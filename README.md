# haussim

A small house with an air/water heat pump, a buffer tank and floor heating, run by a PLC program. Python 3.10+, no dependencies.

Work in progress. Stage 1 covers the heating: heating curve, night setback with preheat, compressor timers (Taktsperre), EVU lock, defrost, heating rod backup, frost protection and ISA-18.2 alarms. A browser HMI, Modbus, the electrical distribution board and an ESP32 sensor node follow.

```
pip install -e .
haussim simulate --days 2 --outside -5 --evu 11:00-13:00
```

---

Ein kleines Haus mit Luft/Wasser-Wärmepumpe, Pufferspeicher und Fußbodenheizung, gesteuert von einem SPS-Programm. Python 3.10+, keine Abhängigkeiten.

In Arbeit. Stufe 1 ist die Heizung: Heizkurve, Nachtabsenkung mit Aufheizvorlauf, Taktsperre, EVU-Sperre, Abtauung, Heizstab als Reserve, Frostschutz und Alarme nach ISA-18.2. Danach folgen Browser-HMI, Modbus, Unterverteilung und ein ESP32-Sensorknoten.
