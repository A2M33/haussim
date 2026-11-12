"""Physical model: the house, the buffer tank, the heat pump and the weather.

Everything the PLC is not. The PLC only sees what a real heating controller
would see: three temperature sensors, the running feedback of the compressor
and the circulation pump, the heat pump's fault and defrost contacts, and the
grid operator's lock signal.
"""

from __future__ import annotations

import math
import random

WATER_J_PER_LK = 4186.0

# Weather: a winter day. Coldest around 05:00, warmest around 15:00.
COLDEST_MINUTE = 5 * 60

COMPRESSOR_RAMP_S = 60.0  # standstill to full capacity
CIRC_RAMP_S = 2.0
DEFROST_AFTER_S = 45 * 60.0  # running time below the icing limit before a defrost
DEFROST_S = 5 * 60.0
ICING_BELOW_C = 6.0
HIGH_PRESSURE_TRIP_C = 62.0  # buffer temperature at which the HP switch trips
ROD_CUTOUT_C = 75.0  # safety thermostat of the heating rod
SENSOR_NOISE_K = 0.05
OPEN_CIRCUIT_C = -60.0  # what a broken sensor lead reads like


def outside_at(minute_of_day: float, mean_c: float, swing_c: float) -> float:
    """Outside temperature for a clear winter day."""
    phase = (minute_of_day - COLDEST_MINUTE) / 1440 * 2 * math.pi
    return mean_c - swing_c * math.cos(phase)


class Process:
    def __init__(
        self,
        *,
        loss_w_per_k: float = 150.0,
        house_j_per_k: float = 20e6,
        emitter_w_per_k: float = 360.0,
        buffer_l: float = 300.0,
        hp_nominal_w: float = 7000.0,
        rod_w: float = 6000.0,
        internal_gains_w: float = 300.0,
        room_c: float = 20.0,
        buffer_c: float = 30.0,
        outside_mean_c: float = -2.0,
        outside_swing_c: float = 5.0,
        start_minute: float = 6 * 60,
        seed: int | None = None,
    ) -> None:
        self.loss_w_per_k = loss_w_per_k
        self.house_j_per_k = house_j_per_k
        self.emitter_w_per_k = emitter_w_per_k
        self.buffer_j_per_k = buffer_l * WATER_J_PER_LK
        self.hp_nominal_w = hp_nominal_w
        self.rod_w = rod_w
        self.internal_gains_w = internal_gains_w
        self.outside_mean_c = outside_mean_c
        self.outside_swing_c = outside_swing_c

        self.clock_s = start_minute * 60.0
        self.room_c = room_c
        self.buffer_c = buffer_c
        self.outside_c = outside_at(start_minute, outside_mean_c, outside_swing_c)

        # Outputs written by the PLC.
        self.hp_cmd = False
        self.circ_cmd = False
        self.rod_cmd = False

        # Plant state.
        self.compressor = 0.0  # 0..1
        self.circ = 0.0  # 0..1
        self.ice = 0.0  # 0..1, defrost starts at 1
        self.defrost_left_s = 0.0
        self.hp_lockout = False  # high-pressure switch, latched
        self.evu_lock = False  # grid operator signal

        # Power flows in watts, for the HMI and the energy meters.
        self.hp_heat_w = 0.0
        self.hp_elec_w = 0.0
        self.rod_w_now = 0.0
        self.emitter_w = 0.0
        self.loss_w = 0.0
        self.cop = 0.0
        self.heat_kwh = 0.0
        self.elec_kwh = 0.0
        self.rod_kwh = 0.0

        # Faults the user can inject from the simulator panel.
        self.hp_broken = False  # compressor does not start
        self.circ_broken = False  # circulation pump seized
        self.window_open = False  # extra ventilation loss
        self.outside_sensor_broken = False
        # Power from the distribution board; the simulator sets these each step.
        self.hp_supply = True
        self.rod_supply = True
        self.circ_supply = True

        self._rng = random.Random(seed)
        self._wander = 0.0
        self._sensors = {"outside": self.outside_c, "room": room_c, "buffer": buffer_c}

    # What the PLC sees ------------------------------------------------------

    @property
    def minute_of_day(self) -> float:
        return (self.clock_s / 60.0) % 1440

    @property
    def outside_sensor(self) -> float:
        return OPEN_CIRCUIT_C if self.outside_sensor_broken else self._sensors["outside"]

    @property
    def room_sensor(self) -> float:
        return self._sensors["room"]

    @property
    def buffer_sensor(self) -> float:
        return self._sensors["buffer"]

    @property
    def hp_running(self) -> bool:
        """Running feedback from the compressor contactor."""
        return self.compressor > 0.5

    @property
    def circ_running(self) -> bool:
        return self.circ > 0.5

    @property
    def defrosting(self) -> bool:
        return self.defrost_left_s > 0

    def reset_lockout(self) -> bool:
        """Reset the high-pressure switch. It only resets once the water cooled down."""
        if self.hp_lockout and self.buffer_c < HIGH_PRESSURE_TRIP_C - 7:
            self.hp_lockout = False
            return True
        return False

    # Physics ------------------------------------------------------------------

    def capacity_w(self) -> float:
        return max(0.3, 1 + 0.025 * (self.outside_c - 2)) * self.hp_nominal_w

    def carnot_cop(self) -> float:
        hot = self.buffer_c + 5 + 273.15
        cold = self.outside_c - 6 + 273.15
        return max(1.5, min(7.0, 0.45 * hot / max(1.0, hot - cold)))

    def step(self, dt: float) -> None:
        if dt <= 0:
            return
        self._weather(dt)
        self._heat_pump(dt)

        if not self.circ_supply:
            self.circ = 0.0
        target = 1.0 if self.circ_cmd and self.circ_supply and not self.circ_broken else 0.0
        ramp = dt / CIRC_RAMP_S
        self.circ += max(-ramp, min(ramp, target - self.circ))

        rod_on = self.rod_cmd and self.rod_supply and self.buffer_c < ROD_CUTOUT_C
        self.rod_w_now = self.rod_w if rod_on else 0.0

        self.emitter_w = self.circ * self.emitter_w_per_k * max(0.0, self.buffer_c - self.room_c)
        buffer_loss = 2.0 * (self.buffer_c - 20.0)
        loss_k = self.loss_w_per_k + (250.0 if self.window_open else 0.0)
        self.loss_w = loss_k * (self.room_c - self.outside_c)

        self.buffer_c += (self.hp_heat_w + self.rod_w_now - self.emitter_w - buffer_loss) * dt / self.buffer_j_per_k
        self.room_c += (self.emitter_w + self.internal_gains_w - self.loss_w) * dt / self.house_j_per_k

        self.heat_kwh += max(0.0, self.hp_heat_w) * dt / 3.6e6
        self.elec_kwh += (self.hp_elec_w + self.rod_w_now) * dt / 3.6e6
        self.rod_kwh += self.rod_w_now * dt / 3.6e6
        self.clock_s += dt

        for name, true in (("outside", self.outside_c), ("room", self.room_c), ("buffer", self.buffer_c)):
            self._sensors[name] = true + self._rng.gauss(0, SENSOR_NOISE_K)

    def _weather(self, dt: float) -> None:
        # The day drifts around the clear-sky curve so no two days look the same.
        self._wander *= 0.9995 ** dt
        self._wander += self._rng.gauss(0, 0.01) * math.sqrt(dt)
        self._wander = max(-2.0, min(2.0, self._wander))
        base = outside_at(self.minute_of_day, self.outside_mean_c, self.outside_swing_c)
        self.outside_c = base + self._wander

    def _heat_pump(self, dt: float) -> None:
        can_run = self.hp_cmd and self.hp_supply and not self.hp_broken and not self.hp_lockout
        if not self.hp_supply:
            self.compressor = 0.0  # no ramp-down without power
        ramp = dt / COMPRESSOR_RAMP_S
        self.compressor += max(-ramp, min(ramp, (1.0 if can_run else 0.0) - self.compressor))

        if self.defrost_left_s > 0:
            self.defrost_left_s = max(0.0, self.defrost_left_s - dt)
            if self.compressor > 0:
                # Reverse cycle: heat goes from the buffer to the evaporator.
                self.hp_heat_w = -1500.0 * self.compressor
                self.hp_elec_w = 1000.0 * self.compressor
                self.cop = 0.0
                return
        if self.hp_running and self.outside_c < ICING_BELOW_C:
            self.ice += dt / DEFROST_AFTER_S
            if self.ice >= 1:
                self.ice = 0.0
                self.defrost_left_s = DEFROST_S

        self.cop = self.carnot_cop() if self.compressor > 0 else 0.0
        self.hp_heat_w = self.compressor * self.capacity_w()
        self.hp_elec_w = self.hp_heat_w / self.cop if self.cop else 0.0

        if self.hp_running and self.buffer_c >= HIGH_PRESSURE_TRIP_C:
            self.hp_lockout = True
