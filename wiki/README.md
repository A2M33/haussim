# haussim wiki

- Goal (2026-11-11): flagship CV project for the user's Ausbildung applications. One simulated small house that shows all three target clusters: IT (dashboard, server), electrical/automation (PLC, distribution board, ESP32) and HVAC (heat pump). Decided with the user: simulation only (no hardware yet), German + English UI/README, start with the heat pump stage.
- Stages: 1 heat pump heating + PLC (this) → 2 distribution board (circuits, MCB, RCD) → 3 dashboard + database history → 4 ESP32 sensor node in Wokwi → 5 Docker home server → 6 German README + drawings.
- Architecture copies tanksim on purpose (process / plc / sim split, scan-based PLC, ISA-18.2 alarms, no runtime dependencies, Pyodide demo later), so both projects read as one portfolio.
- No AI mention in README, commits or UI (user decision). Commits carry no Claude co-author line.

## Stage 1 model (numbers and why)

- House: single-zone RC model. Heat loss coefficient H = 150 W/K (about 5 kW at -12 °C outside and 21 °C inside, a typical renovated 120 m² house). Thermal mass C = 20 MJ/K, so the time constant is about 37 h.
- Floor heating emitter: 360 W/K between buffer and room (about 5 kW at 35 °C supply).
- Buffer tank 300 L. Small standing loss to a 20 °C basement.
- Heat pump: air/water, 7 kW at A2/W35, capacity drops 2.5 %/K colder outside. COP = 0.45 × Carnot between (buffer + 5 K) and (outside - 6 K), clamped 1.5..7. Compressor ramps up over 60 s.
- Defrost: below 6 °C outside the evaporator ices up; after about 45 min of running it defrosts for 5 min and pulls heat out of the buffer.
- High-pressure switch: trips and latches if the buffer passes 62 °C while the compressor runs.
- Heating rod (Heizstab) 6 kW as backup and below the bivalent point.
- EVU lock (EVU-Sperre): grid operator signal; the PLC must stop compressor and rod while it is active.

## PLC rules

- Heating curve: flow target = room setpoint + slope × (room setpoint - damped outside temperature), clamped 25..50 °C, plus 2 K per K the room is below setpoint.
- Damped outside temperature (3 h filter) drives summer cut-off at 17 °C.
- Night setback 22:00-06:00.
- Compressor: start at target - 2 K, stop at target + 2 K; minimum run 6 min, minimum off 10 min (Taktsperre); EVU lock stops it at once.
- Feedback check: compressor 90 s, circulation pump 10 s; both latch a fault.
- Sensor faults: outside sensor out of range → fixed fallback 0 °C and alarm; room sensor → ignore room influence; buffer sensor → stop compressor and rod.
- Frost protection: room < 7 °C or buffer < 8 °C forces circulation and heat demand.
