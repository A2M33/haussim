# haussim

A small house with an air/water heat pump, a 300 L buffer tank and floor heating, and the PLC program that heats it. It comes with a browser HMI in German and English.

**[Try the live demo ↗](https://a2m33.github.io/haussim/)** Your browser runs the same Python code through Pyodide. Set a grid lock or block the compressor and watch the PLC react, with nothing to install.

[Deutsche Fassung weiter unten](#deutsch)

![The HMI in its dark theme. The heat pump runs and charges the buffer tank. The grid operator lock turns its lamp amber and stops the compressor while the buffer cools. Then the compressor is blocked: the unit turns red, the header shows one alarm not acknowledged and the faceplate reads "Störung, bitte zurücksetzen". After a reset the heat pump runs again.](docs/demo.gif)

I built haussim to learn how a heat pump system is controlled before I start an apprenticeship in Germany. It needs Python 3.10 or newer and no other packages.

## Run it

```
pip install git+https://github.com/A2M33/haussim
haussim run
```

Your browser opens the HMI at http://localhost:8080. Time runs 120 times faster than real time. A house reacts over hours, so pick `--speed 600` to watch a whole day in under three minutes, or `--speed 1` for real time. `--outside -10` starts a colder day.

To print a day without the HMI:

```
$ haussim simulate --days 1 --outside -5 --evu 11:00-13:00
time   outside  room   buffer target  HP     rod  COP   kWh el  starts
07:00    -9.4   19.9   31.2   35.3   RUN    off   2.7     1.8      1
08:00    -8.6   20.0   31.8   35.3   RUN    off   2.7     3.6      1
...
Heat 87.0 kWh, electricity 31.0 kWh, seasonal COP 2.81
```

## Things to try

- **Set the grid lock** (EVU-Sperre). German grid operators may switch heat pumps off for a few hours a day in return for a cheaper tariff. The PLC stops the compressor and the heating rod at once, and the buffer and the house's thermal mass carry the room through.
- **Block the compressor.** The PLC expects the running feedback within 90 seconds. Without it, the PLC latches a fault, raises a high priority alarm and lets the 6 kW heating rod take over.
- **Seize the circulation pump.** After 10 seconds without feedback the PLC latches a pump fault and keeps both heat sources off, because the heat has nowhere to go.
- **Disconnect the outside sensor.** The reading drops to -60 °C, the PLC calls the sensor broken and carries on with a fixed 0 °C.
- **Open a window.** The room loses about 250 W per kelvin more. The PLC raises the flow target by 2 K for every kelvin the room falls below its setpoint.
- **Change the heating curve** (Steilheit, Parallelverschiebung) and watch the line in the chart move with it.

## How the PLC decides

The program in [`plc.py`](src/haussim/plc.py) runs once per scan, like the main cycle of a real PLC. It sees what a real controller sees: three temperature sensors, the compressor and pump feedback, the high-pressure switch, the defrost signal and the grid operator's lock.

| Situation | What the PLC does |
| --- | --- |
| Damped outside temperature changes | Sets the flow target from the heating curve, 25 to 50 °C |
| Buffer 2 K below the flow target | Starts the compressor |
| Buffer 2 K above the flow target | Stops it, after at least 6 minutes of running |
| Compressor stopped less than 10 minutes ago | Holds off the next start (Taktsperre) |
| 22:00 to 06:00 | Night setpoint 19 °C, back to 21 °C two hours early because floor heating reacts slowly |
| Damped outside temperature above 17 °C | Summer: heating off |
| Grid operator lock | Compressor and heating rod off at once |
| Below -12 °C, or the heat pump has a fault | Heating rod helps |
| Room below 7 °C or buffer below 8 °C | Frost protection, even in standby |
| Feedback missing, sensor out of range | Latches a fault and raises an alarm |

Alarms follow ISA-18.2: an alarm arrives unacknowledged and flashes, and it leaves the list once it has cleared and you have acknowledged it. The HMI follows ISA-101 like my [tanksim](https://github.com/A2M33/tanksim) project. Colour marks state only: cyan for running equipment, amber for the grid lock and medium alarms, red for faults. The buffer tank is the one exception. It fills from grey towards amber as it heats, because its temperature is the first thing you read.

![The full HMI in English after the circulation pump seized: the pump symbol is red, one high priority alarm sits above the event log, and the 24 hour trend shows room, buffer, flow target and outside temperature.](docs/hmi-fault.png)

## The model

| Part | Numbers |
| --- | --- |
| House | 120 m², heat loss 150 W/K (5 kW at -12 °C), time constant about 37 h |
| Heat pump | 7 kW at A2/W35, COP from 45 % of Carnot, defrost after 45 min of running below 6 °C |
| Buffer tank | 300 L, high-pressure switch trips at 62 °C |
| Floor heating | 360 W/K between buffer and room |
| Heating rod | 6 kW |

On a day with a mean of -2 °C the room stays between 20.5 and 21 °C and the seasonal COP comes out at about 3, in line with real air/water heat pumps on floor heating. The [wiki notes](wiki/README.md) explain each number.

## Tests

```
pip install -e ".[dev]"
pytest
```

The 44 tests run a winter day, a summer day, the grid lock, a broken compressor, a seized pump, a broken outside sensor, the high-pressure switch, an open window and frost. They also check every HMI command and the HTTP server's guard against commands from other websites.

---

<a id="deutsch"></a>

# haussim (Deutsch)

Ein kleines Haus mit Luft/Wasser-Wärmepumpe, 300-L-Pufferspeicher und Fußbodenheizung, dazu das SPS-Programm, das es heizt. Mit Browser-HMI auf Deutsch und Englisch.

**[Live-Demo öffnen ↗](https://a2m33.github.io/haussim/)** Ihr Browser führt denselben Python-Code mit Pyodide aus. Setzen Sie eine EVU-Sperre oder blockieren Sie den Verdichter und sehen Sie zu, wie die SPS reagiert.

Ich habe haussim gebaut, um vor meiner Ausbildung in Deutschland zu lernen, wie man eine Wärmepumpenanlage regelt.

## Starten

```
pip install git+https://github.com/A2M33/haussim
haussim run
```

Der Browser öffnet die HMI unter http://localhost:8080. Mit `--speed 600` läuft ein ganzer Tag in knapp drei Minuten ab.

## Was die SPS macht

- **Heizkurve:** Soll-Vorlauf aus der gedämpften Außentemperatur, mit Steilheit, Parallelverschiebung und Raumeinfluss
- **Nachtabsenkung** auf 19 °C, mit zwei Stunden Aufheizvorlauf, weil die Fußbodenheizung träge ist
- **Verdichter:** Zweipunktregelung auf den Puffer, Mindestlaufzeit 6 min, Taktsperre 10 min
- **EVU-Sperre:** Verdichter und Heizstab sofort aus
- **Heizstab** unter dem Bivalenzpunkt (-12 °C) und als Reserve bei einer Störung der Wärmepumpe
- **Abtauung** und **Hochdruckstörung** der Wärmepumpe
- **Frostschutz** auch in Bereitschaft, mit Hysterese
- **Überwachung:** Rückmeldung von Verdichter und Heizkreispumpe, Fühlerbruch mit Ersatzwert
- **Alarme nach ISA-18.2**, HMI nach ISA-101

## Lizenz

MIT
