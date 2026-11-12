"use strict";

// ---- words -----------------------------------------------------------
// German first: the HMI is built the way a German installer would see it.

const I18N = {
  de: {
    title: "Haus 1, Wärmepumpenheizung",
    subtitle: "Luft/Wasser-Wärmepumpe WP-101, Pufferspeicher PS-101, Fußbodenheizung",
    clockLabel: "Uhrzeit der Anlage",
    linkLost: "Verbindung zu haussim verloren. Die Werte sind veraltet. Neuer Versuch…",
    processTitle: "Anlagenbild: Wärmepumpe WP-101 lädt den Pufferspeicher PS-101, Pumpe P-101 versorgt die Fußbodenheizung",
    outside: "Außen", room: "Raum", buffer: "Puffer", flowTarget: "Soll Vorlauf", hpPower: "Wärmepumpe",
    evu: "EVU-Sperre",
    fpTitle: "Heizung", mode: "Betriebsart", auto: "Automatik", standby: "Bereitschaft",
    spf: "JAZ", starts: "Starts", runtime: "Laufzeit", heat: "Wärme", electricity: "Strom",
    ack: "Alarme quittieren", reset: "Störung zurücksetzen",
    curveTitle: "Heizkurve",
    curveCaption: "Soll-Vorlauf über der gedämpften Außentemperatur, für Tag (Linie) und Nacht (gestrichelt). Der Punkt ist der Sollwert jetzt, mit Raumeinfluss.",
    spTitle: "Sollwerte", apply: "Sollwerte übernehmen", discard: "Änderungen verwerfen",
    trendTitle: "Temperaturen, letzte 24 Stunden",
    hpRunning: "Wärmepumpe läuft", defrost: "Abtauen",
    alarmsTitle: "Alarme", priority: "Priorität", since: "Seit", message: "Meldung", state: "Zustand",
    alarmEmpty: "Alles ruhig. Neue Alarme erscheinen hier und bleiben, bis sie gegangen und quittiert sind.",
    eventsTitle: "Ereignisprotokoll",
    simTitle: "Simulator",
    simNote: "Außerhalb der Anlage. Ein Bediener kann das nicht. Damit testen Sie, wie die SPS reagiert.",
    speed: "Zeitraffer", outsideMean: "Außentemperatur, Tagesmittel", gridSignal: "Netzbetreiber",
    evuSwitch: "EVU-Sperre setzen", faults: "Störungen",
    faultHp: "Verdichter blockieren", faultCirc: "Pumpe festsetzen",
    faultSensor: "Außenfühler abklemmen", faultWindow: "Fenster öffnen",
    pause: "Pause", resume: "Weiter", paused: "angehalten",
    high: "Hoch", medium: "Mittel",
    stActiveUnacked: "Kommt, nicht quittiert", stActive: "Aktiv", stCleared: "Gegangen, nicht quittiert",
    noAlarms: "Keine Alarme", noData: "Noch keine Daten",
    alarmCount: (n, u) => `${n} ${n > 1 ? "Alarme" : "Alarm"}` + (u ? `, ${u} nicht quittiert` : ""),
    hpFault: "Störung", hpDefrost: "Abtauen", hpRun: "Läuft", hpEvu: "EVU-Sperre", hpStart: "Startet",
    hpOff: "Aus", hpTakt: (m) => `Taktsperre noch ${m} min`,
    hpPowerText: (kw, cop) => `${kw} kW, COP ${cop}`,
    damped: (v) => `gedämpft ${v} °C`,
    roomTarget: (v, night) => `Soll ${v} °C (${night ? "Nacht" : "Tag"})`,
    flowTargetIn: (v) => `Soll ${v}`,
    rodOn: (kw) => `Heizstab ${kw} kW`,
    season: (cut, heating) => `Heizgrenze ${cut} °C: ${heating ? "Heizbetrieb" : "Sommerbetrieb"}`,
    fpFault: "Störung, bitte zurücksetzen", fpFrost: "Frostschutz", fpHeating: "Heizbetrieb",
    fpSummer: "Sommerbetrieb", fpStandby: "Bereitschaft",
    hintStandby: "In Bereitschaft heizt die SPS nur, wenn Frost droht.",
    hintEvu: "Der Netzbetreiber sperrt Verdichter und Heizstab. Der Puffer und das Haus überbrücken die Sperre.",
    hintFault: "Eine Störung hält den Wärmeerzeuger aus, bis Sie sie zurücksetzen.",
    hintSummer: "Die gedämpfte Außentemperatur liegt über der Heizgrenze, also bleibt die Heizung aus.",
    hintAuto: "In Automatik regelt die SPS den Puffer nach der Heizkurve, mit Mindestlaufzeit und Taktsperre.",
    spPending: "Die SPS behält ihre Sollwerte, bis Sie die Änderungen übernehmen.",
    spNothing: "Es wurde nichts übernommen.",
    spNow: (v) => `jetzt ${v}`,
    spRange: (name, lo, hi) => `${name} muss zwischen ${lo} und ${hi} liegen`,
    spFlowOrder: "Minimaler Vorlauf muss unter dem maximalen Vorlauf liegen",
    spNightOrder: "Der Nacht-Sollwert darf nicht über dem Tag-Sollwert liegen",
    gRoom: "Raum und Zeitprogramm", gCurve: "Heizkurve und Regelung", gLimits: "Grenzen",
    simHintHp: "Der Verdichter ist aus, die SPS merkt es erst beim nächsten Start.",
    simHintSensor: "Die SPS rechnet mit dem Ersatzwert 0 °C weiter.",
    simHintWindow: "Das offene Fenster kostet etwa 250 W pro Kelvin. Der Raumeinfluss hebt den Vorlauf an.",
    demoLoading: "Der Simulator wird in Ihren Browser geladen. Das dauert ein paar Sekunden…",
    demoFailed: (e) => `Die Demo konnte nicht starten: ${e}. Installieren Sie haussim mit pip, um es lokal zu starten.`,
    demoReady: 'Live-Demo: Das SPS-Programm läuft in Ihrem Browser. <a href="https://github.com/A2M33/haussim#starten">So starten Sie haussim lokal.</a>',
    noConnection: "Keine Verbindung zu haussim",
    boardTitle: "Unterverteilung UV-1", phasesLabel: "Hausanschluss, Strom je Außenleiter",
    meterHouse: "Zähler Haushalt", meterHp: "Zähler Wärmepumpe",
    boardHint: "Ein Klick auf einen Schalter schaltet ihn aus oder ein. Ein ausgelöster Schalter bleibt aus, bis Sie ihn wieder einschalten.",
    faultShort: "Kurzschluss Steckdosen Wohnen", faultOverload: "Überlast Küche, 5 kW",
    faultInsulation: "Isolationsfehler Waschmaschine",
    leverOn: "Ein", leverOff: "Aus", testButton: "Prüftaste T",
    tripShort: "Kurzschluss", tripOverload: "Überlast", tripLeak: "Fehlerstrom", tripTest: "Prüfung",
    leak: (ma) => `Fehlerstrom ${ma} mA`,
    switchLabel: (id, name, on) => `${id} ${name}, ${on ? "eingeschaltet" : "ausgeschaltet"}. Klicken zum ${on ? "Ausschalten" : "Einschalten"}`,
    simHintInsulation: "Q1 löst sofort wieder aus, solange der fehlerhafte Stromkreis eingeschaltet ist. Schalten Sie die Leitungsschutzschalter nacheinander aus, um ihn zu finden.",
    simHintOverload: "Der Schalter F3 erwärmt sich und löst nach einigen Minuten aus.",
  },
  en: {
    title: "House 1, heat pump heating",
    subtitle: "Air/water heat pump WP-101, buffer tank PS-101, floor heating",
    clockLabel: "Plant time",
    linkLost: "Connection to haussim lost. Values are out of date. Retrying…",
    processTitle: "Process graphic: heat pump WP-101 charges buffer tank PS-101, pump P-101 supplies the floor heating",
    outside: "Outside", room: "Room", buffer: "Buffer", flowTarget: "Flow target", hpPower: "Heat pump",
    evu: "Grid lock",
    fpTitle: "Heating", mode: "Mode", auto: "Auto", standby: "Standby",
    spf: "SPF", starts: "Starts", runtime: "Run time", heat: "Heat", electricity: "Electricity",
    ack: "Acknowledge alarms", reset: "Reset faults",
    curveTitle: "Heating curve",
    curveCaption: "Flow target over the damped outside temperature, for day (line) and night (dashed). The dot is the target now, including the room influence.",
    spTitle: "Setpoints", apply: "Apply setpoints", discard: "Discard changes",
    trendTitle: "Temperatures, last 24 hours",
    hpRunning: "Heat pump running", defrost: "Defrost",
    alarmsTitle: "Alarms", priority: "Priority", since: "Since", message: "Message", state: "State",
    alarmEmpty: "All quiet. New alarms appear here and stay until they clear and you acknowledge them.",
    eventsTitle: "Event log",
    simTitle: "Simulator",
    simNote: "Outside the plant. A real operator cannot do these things; use them to test how the PLC reacts.",
    speed: "Time speed", outsideMean: "Outside temperature, daily mean", gridSignal: "Grid operator",
    evuSwitch: "Set grid lock", faults: "Faults",
    faultHp: "Block the compressor", faultCirc: "Seize the pump",
    faultSensor: "Disconnect the outside sensor", faultWindow: "Open a window",
    pause: "Pause", resume: "Resume", paused: "paused",
    high: "High", medium: "Medium",
    stActiveUnacked: "Active, not acknowledged", stActive: "Active", stCleared: "Cleared, not acknowledged",
    noAlarms: "No alarms", noData: "No data yet",
    alarmCount: (n, u) => `${n} alarm${n > 1 ? "s" : ""}` + (u ? `, ${u} not acknowledged` : ""),
    hpFault: "Fault", hpDefrost: "Defrosting", hpRun: "Running", hpEvu: "Grid lock", hpStart: "Starting",
    hpOff: "Off", hpTakt: (m) => `Restart lock ${m} min`,
    hpPowerText: (kw, cop) => `${kw} kW, COP ${cop}`,
    damped: (v) => `damped ${v} °C`,
    roomTarget: (v, night) => `Target ${v} °C (${night ? "night" : "day"})`,
    flowTargetIn: (v) => `target ${v}`,
    rodOn: (kw) => `Heating rod ${kw} kW`,
    season: (cut, heating) => `Heating limit ${cut} °C: ${heating ? "heating season" : "summer"}`,
    fpFault: "Fault, reset to restart", fpFrost: "Frost protection", fpHeating: "Heating",
    fpSummer: "Summer, heating off", fpStandby: "Standby",
    hintStandby: "In standby the PLC only heats when frost is near.",
    hintEvu: "The grid operator blocks compressor and rod. The buffer and the house bridge the lock.",
    hintFault: "A fault keeps the heat source off until you reset it.",
    hintSummer: "The damped outside temperature is above the heating limit, so the heating stays off.",
    hintAuto: "In auto the PLC holds the buffer on the heating curve, with minimum run time and restart lock.",
    spPending: "The PLC keeps its setpoints until you apply the changes.",
    spNothing: "Nothing was applied.",
    spNow: (v) => `now ${v}`,
    spRange: (name, lo, hi) => `${name} must lie between ${lo} and ${hi}`,
    spFlowOrder: "Minimum flow must be below maximum flow",
    spNightOrder: "Night setpoint must not be above the day setpoint",
    gRoom: "Room and schedule", gCurve: "Heating curve and control", gLimits: "Limits",
    simHintHp: "The compressor is off, so the PLC only notices at the next start.",
    simHintSensor: "The PLC carries on with the 0 °C fallback value.",
    simHintWindow: "The open window costs about 250 W per kelvin. The room influence raises the flow target.",
    demoLoading: "Loading the simulator into your browser. This takes a few seconds…",
    demoFailed: (e) => `The demo could not start: ${e}. Install haussim with pip to run it locally.`,
    demoReady: 'Live demo: the PLC program runs in your browser. <a href="https://github.com/A2M33/haussim#run-it">Run haussim locally.</a>',
    noConnection: "No connection to haussim",
    boardTitle: "Distribution board UV-1", phasesLabel: "House connection, current per phase",
    meterHouse: "Household meter", meterHp: "Heat pump meter",
    boardHint: "Click a switch to turn it off or on. A tripped device stays off until you switch it on again.",
    faultShort: "Short circuit, living room sockets", faultOverload: "Overload kitchen, 5 kW",
    faultInsulation: "Insulation fault, washing machine",
    leverOn: "On", leverOff: "Off", testButton: "Test button T",
    tripShort: "Short circuit", tripOverload: "Overload", tripLeak: "Earth leakage", tripTest: "Test",
    leak: (ma) => `Leakage ${ma} mA`,
    switchLabel: (id, name, on) => `${id} ${name}, ${on ? "on" : "off"}. Click to switch ${on ? "off" : "on"}`,
    simHintInsulation: "Q1 trips again at once while the faulty circuit is on. Switch the breakers off one by one to find it.",
    simHintOverload: "Breaker F3 warms up and trips after a few minutes.",
  },
};

// key, unit, [de, en], group, kind
const SETPOINTS = [
  ["room_day", "°C", ["Raum Tag", "Room, day"], "gRoom"],
  ["room_night", "°C", ["Raum Nacht", "Room, night"], "gRoom"],
  ["night_from", "", ["Nacht ab", "Night from"], "gRoom", "time"],
  ["night_to", "", ["Nacht bis", "Night until"], "gRoom", "time"],
  ["preheat", "min", ["Vorheizen", "Preheat"], "gRoom"],
  ["curve_slope", "", ["Steilheit", "Slope"], "gCurve"],
  ["curve_shift", "K", ["Parallelverschiebung", "Parallel shift"], "gCurve"],
  ["flow_min", "°C", ["Vorlauf min.", "Flow min"], "gCurve"],
  ["flow_max", "°C", ["Vorlauf max.", "Flow max"], "gCurve"],
  ["hysteresis", "K", ["Schaltdifferenz ±", "Switching band ±"], "gCurve"],
  ["summer_cutoff", "°C", ["Heizgrenze", "Heating limit"], "gLimits"],
  ["bivalent", "°C", ["Bivalenzpunkt", "Bivalent point"], "gLimits"],
  ["buffer_high", "°C", ["Alarm Puffer hoch", "Buffer high alarm"], "gLimits"],
  ["room_low", "°C", ["Alarm Raum tief", "Room low alarm"], "gLimits"],
];
// Same limits as SETPOINT_LIMITS in plc.py, which has the last word.
const LIMITS = {
  room_day: [10, 26], room_night: [10, 26], night_from: [0, 1439], night_to: [0, 1439],
  preheat: [0, 240], curve_slope: [0.1, 2], curve_shift: [-5, 5], flow_min: [20, 40],
  flow_max: [30, 60], hysteresis: [0.5, 5], summer_cutoff: [10, 22], bivalent: [-20, 5],
  buffer_high: [45, 70], room_low: [5, 20],
};
const HIGH_PRIORITY = new Set(["HP_LOCK", "HP_FB", "CIRC_FB", "S_BUF", "FROST", "Q1_TRIP", "Q2_TRIP", "F6_TRIP", "F7_TRIP"]);
const MAIN_FUSE_A = 35;
const TRIP_WORD = { short: "tripShort", overload: "tripOverload", leak: "tripLeak", test: "tripTest" };
const RESETTABLE = new Set(["HP_LOCK", "HP_FB", "CIRC_FB", "S_OUT", "S_ROOM", "S_BUF"]);
const SPEEDS = [1, 60, 120, 600];
const TREND_SPAN_S = 86400;
const T_MIN = -20, T_MAX = 60; // trend scale, °C

const $ = (id) => document.getElementById(id);
let lang = localStorage.getItem("haussim-lang") === "en" ? "en" : "de";
let state = null;
let history = [];
const spEdited = new Set();
let spProblem = null;
let demo = null;

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/";
const DEMO_MODULES = ["__init__", "process", "electrical", "plc", "sim", "commands"];
const DEMO_GLUE = `
import json, sys
sys.path.insert(0, "/home/pyodide")
from haussim.sim import Simulator
from haussim.commands import CommandError, apply_command

sim = Simulator()

def step(real_s):
    if not sim.paused:
        sim.step(min(real_s, 1.0) * sim.speed)

def snapshot():
    return json.dumps(sim.snapshot())

def history():
    return json.dumps(sim.history_list())

def command(body):
    try:
        apply_command(sim, json.loads(body))
    except CommandError as err:
        return str(err)
    return ""
`;

// ---- helpers ---------------------------------------------------------

const t = (key, ...args) => {
  const v = I18N[lang][key];
  return typeof v === "function" ? v(...args) : v;
};

function num(value, digits = 1) {
  const rounded = Number(Number(value).toFixed(digits)) || 0; // -0.04 must not read "-0.0"
  return rounded.toLocaleString(lang, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function hhmm(minute) {
  const m = ((Math.floor(minute) % 1440) + 1440) % 1440;
  return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
}

function hhmmss(clock) {
  const s = Math.floor(clock) % 86400;
  return hhmm(s / 60) + ":" + String(s % 60).padStart(2, "0");
}

const drawn = new Map();
function changed(block, data) {
  const key = JSON.stringify(data);
  if (drawn.get(block) === key) return false;
  drawn.set(block, key);
  return true;
}

function setText(id, text) {
  const el = $(id);
  if (el.textContent !== String(text)) el.textContent = text;
}

function setLamp(id, lampState) {
  const lamp = $(id);
  if (lampState) lamp.dataset.state = lampState;
  else delete lamp.dataset.state;
}

const active = (s, tag) => s.alarms.some((a) => a.tag === tag && a.active);

async function send(cmd, extra = {}) {
  if (demo) {
    const error = demo.command(JSON.stringify({ cmd, ...extra }));
    if (error) throw new Error(error);
    render(JSON.parse(demo.snapshot()));
    return;
  }
  const res = await fetch("api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cmd, ...extra }),
  }).catch(() => { throw new Error(t("noConnection")); });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(body.error);
  }
}

function act(cmd, extra) {
  if (!state) return;
  const notice = $("cmd-error");
  send(cmd, extra).then(
    () => { notice.hidden = true; },
    (err) => { notice.textContent = err.message; notice.hidden = false; },
  );
}

function setLive(live) {
  document.body.classList.toggle("waiting", !live);
  for (const el of document.querySelectorAll("main, .sim")) el.inert = !live;
}

// ---- language --------------------------------------------------------

function applyLanguage() {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  document.title = t("title") + " · haussim";
  $("clock").setAttribute("aria-label", t("clockLabel"));
  $("process-title").textContent = t("processTitle");
  for (const b of document.querySelectorAll("[data-lang]")) b.setAttribute("aria-pressed", b.dataset.lang === lang);
  for (const [key, , names] of SETPOINTS) $("sp-" + key + "-label").textContent = names[lang === "de" ? 0 : 1];
  for (const g of document.querySelectorAll(".sp-group")) g.textContent = t(g.dataset.group);
  if (demo) $("demo-note").innerHTML = t("demoReady");
  drawn.clear();
  if (state) render(state);
}

// ---- static parts ----------------------------------------------------

const isTime = (key) => key === "night_from" || key === "night_to";
const spName = (key) => SETPOINTS.find(([k]) => k === key)[2][lang === "de" ? 0 : 1];

function buildSetpointForm() {
  const grid = $("sp-grid");
  let group = null;
  for (const [key, unit, , g] of SETPOINTS) {
    if (g !== group) {
      group = g;
      const head = document.createElement("div");
      head.className = "sp-group";
      head.dataset.group = g;
      grid.append(head);
    }
    const id = "sp-" + key;
    const label = document.createElement("label");
    label.htmlFor = id;
    label.id = id + "-label";
    const input = document.createElement("input");
    input.id = id;
    input.dataset.key = key;
    // Text, not type="time": that one shows 10:00 PM or 22:00 depending on the
    // browser locale, and the field is too narrow for the first.
    if (isTime(key)) Object.assign(input, { type: "text", inputMode: "numeric", placeholder: "HH:MM", maxLength: 5 });
    else Object.assign(input, { type: "number", min: LIMITS[key][0], max: LIMITS[key][1], step: "any" });
    if (unit) input.setAttribute("aria-description", unit);
    input.addEventListener("input", () => {
      if (spNumber(input) === state.setpoints[key]) spEdited.delete(key);
      else spEdited.add(key);
      if (spProblem) spProblem = setpointProblem(spValues());
      renderSetpointForm(state);
    });
    const live = document.createElement("span");
    live.id = id + "-live";
    live.className = "sp-live";
    input.setAttribute("aria-describedby", live.id);
    grid.append(label, input, live);
  }
}

const spInputs = () => [...$("sp-form").querySelectorAll("input")];

function spNumber(input) {
  if (input.value === "") return NaN;
  if (isTime(input.dataset.key)) {
    const match = /^(\d{1,2}):(\d{2})$/.exec(input.value.trim());
    if (!match || Number(match[1]) > 23 || Number(match[2]) > 59) return NaN;
    return Number(match[1]) * 60 + Number(match[2]);
  }
  return Number(input.value);
}

function spShow(key, value) {
  return isTime(key) ? hhmm(value) : String(value);
}

const spValues = () => Object.fromEntries(spInputs().map((i) => [i.dataset.key, spNumber(i)]));

function setpointProblem(values) {
  for (const [key] of SETPOINTS) {
    const [lo, hi] = LIMITS[key];
    if (!(values[key] >= lo && values[key] <= hi)) {
      return { message: t("spRange", spName(key), spShow(key, lo), spShow(key, hi)), keys: [key] };
    }
  }
  if (values.flow_min >= values.flow_max) return { message: t("spFlowOrder"), keys: ["flow_min", "flow_max"] };
  if (values.room_night > values.room_day) return { message: t("spNightOrder"), keys: ["room_night", "room_day"] };
  return null;
}

function buildSpeeds() {
  const box = $("speeds");
  for (const s of SPEEDS) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = s + "×";
    b.dataset.speed = s;
    b.addEventListener("click", () => act("speed", { value: s }));
    box.append(b);
  }
}

// ---- distribution board ---------------------------------------------

function buildBoard() {
  const phases = $("phases");
  for (const n of [1, 2, 3]) {
    const row = document.createElement("div");
    row.className = "phase";
    row.innerHTML = `<span>L${n}</span><span class="phase-track"><span class="phase-fill" id="ph${n}-fill"></span></span><span class="phase-value" id="ph${n}-value">--</span>`;
    phases.append(row);
  }
}

function moduleFor(dev, isRcd) {
  const m = document.createElement("div");
  m.className = "module" + (isRcd ? " rcd" : dev.phases === 3 ? " wide" : "");
  m.dataset.id = dev.id;
  const parts = [
    ["dev-id", dev.id],
    ["dev-rating", isRcd ? `${dev.rated_ma} mA` : dev.rating + (dev.phases === 3 ? " 3p" : ` L${dev.phase}`)],
    ["dev-name", ""],
  ];
  for (const [cls, text] of parts) {
    const span = document.createElement("span");
    span.className = cls;
    span.textContent = text;
    m.append(span);
  }
  const lever = document.createElement("button");
  lever.type = "button";
  lever.className = "lever";
  lever.dataset.device = dev.id;
  m.append(lever);
  const reading = document.createElement("span");
  reading.className = "dev-reading";
  m.append(reading);
  if (isRcd) {
    const test = document.createElement("button");
    test.type = "button";
    test.className = "test-btn";
    test.dataset.test = dev.id;
    m.append(test);
  } else {
    const track = document.createElement("span");
    track.className = "heat-track";
    track.innerHTML = '<span class="heat-fill"></span>';
    m.append(track);
  }
  return m;
}

function renderBoard(s) {
  const b = s.board;
  const rails = $("rails");
  if (!rails.children.length) {
    for (const rcd of b.rcds) {
      const rail = document.createElement("div");
      rail.className = "rail";
      rail.append(moduleFor(rcd, true));
      for (const br of b.breakers.filter((x) => x.rcd === rcd.id)) rail.append(moduleFor(br, false));
      rails.append(rail);
    }
  }
  const pick = (names) => names[lang === "de" ? 0 : 1];
  const live = new Set(b.rcds.filter((r) => r.closed).map((r) => r.id));
  for (const dev of [...b.rcds, ...b.breakers]) {
    const m = rails.querySelector(`[data-id="${dev.id}"]`);
    const isRcd = "rated_ma" in dev;
    m.classList.toggle("tripped", Boolean(dev.trip));
    m.querySelector(".dev-name").textContent = pick(dev.name);
    const lever = m.querySelector(".lever");
    lever.setAttribute("aria-pressed", dev.closed);
    lever.textContent = dev.closed ? t("leverOn") : t("leverOff");
    lever.setAttribute("aria-label", t("switchLabel", dev.id, pick(dev.name), dev.closed));
    let reading;
    if (dev.trip) reading = t(TRIP_WORD[dev.trip]);
    else if (isRcd) reading = dev.leak_ma > 0 ? t("leak", num(dev.leak_ma, 0)) : "";
    else reading = dev.closed && live.has(dev.rcd) ? num(dev.current_a) + " A" : "–";
    m.querySelector(".dev-reading").textContent = reading;
    if (isRcd) {
      const test = m.querySelector(".test-btn");
      test.textContent = t("testButton");
      test.disabled = !dev.closed;
    } else {
      const fill = m.querySelector(".heat-fill");
      const heat = Math.min(1, dev.heat);
      fill.style.width = (heat * 100).toFixed(0) + "%";
      fill.classList.toggle("hot", heat > 0.75);
    }
  }
  b.phase_a.forEach((a, i) => {
    const fill = $(`ph${i + 1}-fill`);
    fill.style.width = Math.min(100, (a / MAIN_FUSE_A) * 100).toFixed(1) + "%";
    fill.classList.toggle("high", a > 0.8 * MAIN_FUSE_A);
    setText(`ph${i + 1}-value`, num(a) + " A");
  });
  setText("v-house-kwh", num(b.house_kwh) + " kWh");
  setText("v-hp-kwh", num(b.hp_kwh) + " kWh");
}

// ---- rendering -------------------------------------------------------

function hpState(s) {
  if (active(s, "HP_LOCK") || active(s, "HP_FB")) return ["fault", t("hpFault")];
  if (s.defrosting && s.hp_running) return ["live", t("hpDefrost")];
  if (s.hp_running) return ["live", t("hpRun")];
  if (s.evu_lock && s.heating) return ["warn", t("hpEvu")];
  if (s.hp_cmd) return ["", t("hpStart")];
  return ["", t("hpOff")];
}

function renderMimic(s) {
  const sp = s.setpoints;
  setText("v-outside", num(s.outside) + " °C");
  setText("v-damped", s.outside_damped == null ? "" : t("damped", num(s.outside_damped)));
  $("evu").classList.toggle("active", s.evu_lock);
  setLamp("evu-lamp", s.evu_lock ? "warn" : "");

  const [hpLamp, hpText] = hpState(s);
  const hp = $("hp");
  hp.classList.toggle("running", s.hp_running);
  hp.classList.toggle("defrost", s.defrosting);
  hp.classList.toggle("fault", hpLamp === "fault");
  setLamp("hp-lamp", hpLamp);
  setText("v-hp", hpText);
  setText("v-hp-power", s.hp_running && !s.defrosting ? t("hpPowerText", num(s.hp_heat_w / 1000), num(s.cop)) : "");
  setText("v-hp-note", s.taktsperre > 0 && s.heating && !s.hp_cmd ? t("hpTakt", Math.ceil(s.taktsperre / 60)) : "");
  const hpFlow = s.hp_running;
  $("pipe-hp-flow").classList.toggle("flowing", hpFlow);
  $("pipe-hp-return").classList.toggle("flowing", hpFlow);

  setText("v-buffer", num(s.buffer));
  setText("v-flow-target", t("flowTargetIn", num(s.flow_target)));
  const warm = Math.max(0, Math.min(100, ((s.buffer - 20) / 35) * 100));
  $("buffer-fill").style.fill = `color-mix(in srgb, var(--warm) ${warm.toFixed(0)}%, var(--cold))`;
  $("rod").classList.toggle("on", s.rod_on);
  setText("v-rod", s.rod_on ? t("rodOn", num(s.rod_w / 1000)) : "");

  const circFault = active(s, "CIRC_FB");
  const circ = $("circ");
  circ.classList.toggle("running", s.circ_running);
  circ.classList.toggle("fault", circFault);
  setLamp("circ-lamp", circFault ? "fault" : s.circ_running ? "live" : "");
  for (const id of ["pipe-heat-flow", "pipe-heat-return", "floor"]) $(id).classList.toggle("flowing", s.circ_running);
  setText("v-emitter", s.circ_running ? num(s.emitter_w / 1000) + " kW" : "");

  setText("v-room", num(s.room) + " °C");
  const night = s.room_target === sp.room_night && sp.room_night !== sp.room_day;
  setText("v-room-target", t("roomTarget", num(s.room_target), night));
  $("window").classList.toggle("open", s.sim.window_open);
  $("window-sash").setAttribute("d", s.sim.window_open ? "M604 262 L590 270 V304 L604 296" : "M604 262 V296");
  const season = s.outside_damped != null && s.outside_damped < sp.summer_cutoff;
  setText("v-season", t("season", num(sp.summer_cutoff, 0), season));

  const readouts = {
    room: num(s.room) + " °C",
    outside: num(s.outside) + " °C",
    buffer: num(s.buffer) + " °C",
    "flow-target": num(s.flow_target) + " °C",
    "hp-power": s.hp_running ? num(s.hp_heat_w / 1000) + " kW" : hpText,
    cop: s.hp_running && s.cop ? num(s.cop) : "–",
  };
  for (const [name, text] of Object.entries(readouts)) setText("m-" + name, text);
}

function renderFaceplate(s) {
  const fault = [...RESETTABLE].some((tag) => HIGH_PRIORITY.has(tag) && active(s, tag));
  const frost = active(s, "FROST");
  const summer = s.auto && !s.heating;
  const fp = $("fp-state");
  setText("fp-state",
    fault ? t("fpFault") : frost ? t("fpFrost") : !s.auto ? t("fpStandby") : summer ? t("fpSummer") : t("fpHeating"));
  fp.classList.toggle("fault", fault);
  setLamp("fp-lamp", fault ? "fault" : s.evu_lock && s.heating ? "warn" : s.heating ? "live" : "");

  $("btn-auto").setAttribute("aria-pressed", s.auto);
  $("btn-standby").setAttribute("aria-pressed", !s.auto);
  setText("mode-hint",
    fault ? t("hintFault") : !s.auto ? t("hintStandby") : s.evu_lock ? t("hintEvu") : summer ? t("hintSummer") : t("hintAuto"));

  setText("v-cop", s.hp_running && s.cop ? num(s.cop) : "–");
  setText("v-spf", s.spf ? num(s.spf, 2) : "–");
  setText("v-starts", s.starts);
  const min = Math.floor(s.run_s / 60);
  setText("v-runtime", `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")} min`);
  setText("v-heat", num(s.heat_kwh) + " kWh");
  setText("v-elec", num(s.elec_kwh) + " kWh");
  $("btn-ack").disabled = !s.alarms.some((a) => !a.acked);
  $("btn-reset").disabled = !s.alarms.some((a) => RESETTABLE.has(a.tag) && a.active);

  renderSetpointForm(s);
}

function renderSetpointForm(s) {
  for (const input of spInputs()) {
    const key = input.dataset.key;
    const live = s.setpoints[key];
    if (spNumber(input) === live) spEdited.delete(key);
    else if (!spEdited.has(key)) input.value = spShow(key, live);
    const edited = spEdited.has(key);
    input.classList.toggle("pending", edited);
    input.setAttribute("aria-invalid", Boolean(spProblem && spProblem.keys.includes(key)));
    const unit = SETPOINTS.find(([k]) => k === key)[1];
    setText(input.id + "-live", edited ? t("spNow", spShow(key, live)) : unit);
  }
  if (!spEdited.size) spProblem = null;
  $("sp-apply").disabled = $("sp-discard").disabled = !spEdited.size;
  $("sp-message").classList.toggle("error", Boolean(spProblem));
  setText("sp-message", spProblem
    ? `${spProblem.message}. ${t("spNothing")}`
    : spEdited.size ? t("spPending") : "");
}

function renderAlarms(s) {
  const summary = $("alarm-summary");
  const n = s.alarms.length;
  const unacked = s.alarms.filter((a) => !a.acked).length;
  const high = s.alarms.some((a) => HIGH_PRIORITY.has(a.tag));
  setText("alarm-summary", n === 0 ? t("noAlarms") : t("alarmCount", n, unacked));
  summary.className = "alarm-summary" + (n ? (high ? " has-high" : " has-medium") : "") + (unacked ? " unacked" : "");

  if (changed("alarms", [lang, s.alarms])) {
    const rows = $("alarm-rows");
    rows.replaceChildren();
    for (const a of [...s.alarms].sort((x, y) => y.since - x.since)) {
      const tr = document.createElement("tr");
      const isHigh = HIGH_PRIORITY.has(a.tag);
      tr.className = [isHigh ? "high" : "medium", a.acked ? "acked" : "unacked", a.active ? "active" : "cleared"].join(" ");
      const stateText = a.active ? (a.acked ? t("stActive") : t("stActiveUnacked")) : t("stCleared");
      const priority = document.createElement("td");
      const shape = document.createElement("span");
      shape.className = "prio-shape";
      priority.append(shape, isHigh ? t("high") : t("medium"));
      tr.append(priority);
      for (const [text, cls] of [[hhmmss(a.since)], [a.tag], [lang === "de" ? a.text_de : a.text], [stateText, "state-cell"]]) {
        const td = document.createElement("td");
        td.textContent = text;
        if (cls) td.className = cls;
        tr.append(td);
      }
      rows.append(tr);
    }
    $("alarm-empty").hidden = n > 0;
  }

  if (changed("events", s.events)) {
    const list = $("events");
    list.replaceChildren();
    for (const [clock, kind, text] of [...s.events].reverse()) {
      const li = document.createElement("li");
      li.className = kind;
      for (const [txt, cls] of [[hhmmss(clock), "time"], [kind, "kind"], [text, "text"]]) {
        const span = document.createElement("span");
        span.className = cls;
        span.textContent = txt;
        li.append(span);
      }
      list.append(li);
    }
  }
}

function renderSim(s) {
  for (const b of $("speeds").children) b.setAttribute("aria-pressed", Number(b.dataset.speed) === s.sim.speed);
  $("btn-pause").setAttribute("aria-pressed", s.sim.paused);
  setText("btn-pause", s.sim.paused ? t("resume") : t("pause"));
  const slider = $("outside-mean");
  if (document.activeElement !== slider) {
    slider.value = Math.round(s.sim.outside_mean);
    $("outside-out").textContent = slider.value + " °C";
  }
  $("btn-evu").setAttribute("aria-pressed", s.evu_lock);
  const faults = {
    hp: s.sim.hp_broken, circ: s.sim.circ_broken,
    outside_sensor: s.sim.outside_sensor_broken, window: s.sim.window_open,
    short: s.sim.short_circuit, overload: s.sim.overload, insulation: s.sim.insulation_fault,
  };
  for (const b of document.querySelectorAll("[data-fault]")) b.setAttribute("aria-pressed", faults[b.dataset.fault]);
  setText("sim-hint",
    s.sim.hp_broken && !s.hp_cmd && !active(s, "HP_FB") ? t("simHintHp")
      : s.sim.insulation_fault ? t("simHintInsulation")
      : s.sim.overload && s.board.breakers.find((b) => b.id === "F3").closed ? t("simHintOverload")
      : s.sim.outside_sensor_broken && active(s, "S_OUT") ? t("simHintSensor")
        : s.sim.window_open ? t("simHintWindow") : "");
}

function canvasContext(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * dpr)) {
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  return [ctx, w, h];
}

function colours() {
  const css = getComputedStyle(document.documentElement);
  const v = (name) => css.getPropertyValue(name).trim();
  return { ink: v("--ink"), muted: v("--ink-2"), grid: v("--inset"), trace: v("--trace"), signal: v("--signal"), warn: v("--warn"), font: v("--font") };
}

function line(ctx, points) {
  ctx.beginPath();
  points.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
  ctx.stroke();
}

function drawCurve() {
  const [ctx, w, h] = canvasContext($("curve"));
  if (!state) return;
  const c = colours();
  const sp = state.setpoints;
  const left = 34, right = w - 10, top = 10, bottom = h - 22;
  const X0 = -20, X1 = 20, Y0 = 20, Y1 = 60;
  const x = (v) => left + (right - left) * (v - X0) / (X1 - X0);
  const y = (v) => bottom - (bottom - top) * (v - Y0) / (Y1 - Y0);
  const flowAt = (room, out) => Math.max(sp.flow_min, Math.min(sp.flow_max, room + sp.curve_shift + sp.curve_slope * (room - out)));

  ctx.save();
  ctx.font = "12px " + c.font;
  ctx.fillStyle = c.muted;
  ctx.strokeStyle = c.grid;
  ctx.lineWidth = 1;
  for (let v = Y0; v <= Y1; v += 10) {
    line(ctx, [[left, y(v)], [right, y(v)]]);
    ctx.fillText(String(v), 6, y(v) + 4);
  }
  for (let v = X0; v <= X1; v += 10) {
    line(ctx, [[x(v), top], [x(v), bottom]]);
    ctx.fillText(String(v), x(v) - 8, h - 6);
  }
  // heating limit: no heating to the right of it
  ctx.fillStyle = c.grid;
  ctx.fillRect(x(Math.min(X1, sp.summer_cutoff)), top, right - x(Math.min(X1, sp.summer_cutoff)), bottom - top);

  const outs = [];
  for (let v = X0; v <= Math.min(X1, sp.summer_cutoff); v += 0.5) outs.push(v);
  ctx.strokeStyle = c.muted;
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  line(ctx, outs.map((v) => [x(v), y(flowAt(sp.room_night, v))]));
  ctx.setLineDash([]);
  ctx.strokeStyle = c.ink;
  ctx.lineWidth = 2;
  line(ctx, outs.map((v) => [x(v), y(flowAt(sp.room_day, v))]));

  if (state.outside_damped != null) {
    const px = x(Math.max(X0, Math.min(X1, state.outside_damped)));
    const py = y(Math.max(Y0, Math.min(Y1, state.flow_target)));
    ctx.fillStyle = state.heating ? c.signal : c.trace;
    ctx.beginPath();
    ctx.arc(px, py, 5, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawTrend() {
  const [ctx, w, h] = canvasContext($("trend"));
  if (!state) return;
  const c = colours();
  const left = 34, right = w - 8, top = 8, bottom = h - 22;
  const now = state.clock;
  const x = (tt) => left + (right - left) * (1 - (now - tt) / TREND_SPAN_S);
  const y = (v) => bottom - (bottom - top) * (v - T_MIN) / (T_MAX - T_MIN);

  ctx.save();
  ctx.font = "12px " + c.font;
  ctx.fillStyle = c.muted;
  ctx.strokeStyle = c.grid;
  ctx.lineWidth = 1;
  for (let v = T_MIN; v <= T_MAX; v += 20) {
    line(ctx, [[left, y(v)], [right, y(v)]]);
    ctx.fillText(String(v), 4, y(v) + 4);
  }
  const step = w < 500 ? 6 * 3600 : 3 * 3600;
  const firstTick = Math.ceil((now - TREND_SPAN_S) / step) * step;
  for (let tt = firstTick; tt <= now; tt += step) {
    line(ctx, [[x(tt), top], [x(tt), bottom]]);
    ctx.fillText(hhmm(tt / 60), Math.min(x(tt) - 14, w - 34), h - 6);
  }

  ctx.beginPath();
  ctx.rect(left, top, right - left, bottom - top);
  ctx.clip();

  // heat pump band along the bottom: grey while heating, cyan while defrosting
  for (let i = 1; i < history.length; i++) {
    const heat = history[i][5];
    if (Math.abs(heat) < 1) continue;
    ctx.fillStyle = heat > 0 ? c.trace : c.signal;
    ctx.fillRect(x(history[i - 1][0]), bottom - 8, x(history[i][0]) - x(history[i - 1][0]) + 0.5, 8);
  }

  const series = (col, colour, width, dash) => {
    ctx.strokeStyle = colour;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    line(ctx, history.map((r) => [x(r[0]), y(r[col])]));
  };
  series(1, c.muted, 1.5, [2, 3]);
  series(4, c.muted, 1.5, [5, 4]);
  series(3, c.warn, 1.5, []);
  series(2, c.ink, 2.5, []);
  ctx.restore();
}

function setHistory(samples, now) {
  history = samples.filter(([tt]) => now - tt <= TREND_SPAN_S);
}

async function loadHistory() {
  const res = await fetch("api/history");
  if (!res.ok) throw new Error(res.statusText);
  const samples = await res.json();
  setHistory(samples, samples.length ? samples[samples.length - 1][0] : 0);
}

function render(s) {
  if (!state) setLive(true);
  state = s;
  setText("clock", hhmm(s.minute) + (s.sim.paused ? " " + t("paused") : ""));
  let last = history[history.length - 1];
  if (last && s.clock < last[0]) {
    history = [];
    last = null;
  }
  if (!last || s.clock - last[0] >= 60) {
    history.push([s.clock, s.outside, s.room, s.buffer, s.flow_target, s.hp_heat_w, s.hp_elec_w + s.rod_w]);
    setHistory(history, s.clock);
  }
  renderMimic(s);
  renderFaceplate(s);
  renderAlarms(s);
  renderSim(s);
  renderBoard(s);
  drawCurve();
  drawTrend();
}

// ---- wiring ----------------------------------------------------------

function wire() {
  for (const b of document.querySelectorAll("[data-lang]")) {
    b.addEventListener("click", () => {
      lang = b.dataset.lang;
      localStorage.setItem("haussim-lang", lang);
      applyLanguage();
    });
  }
  $("btn-auto").addEventListener("click", () => act("auto", { value: true }));
  $("btn-standby").addEventListener("click", () => act("auto", { value: false }));
  $("btn-ack").addEventListener("click", () => act("ack"));
  $("btn-reset").addEventListener("click", () => act("reset"));
  $("alarm-summary").addEventListener("click", () => $("alarms-title").scrollIntoView({ behavior: "smooth" }));
  $("btn-pause").addEventListener("click", () => act("pause", { value: !state.sim.paused }));
  $("btn-evu").addEventListener("click", () => act("evu", { value: !state.evu_lock }));

  const slider = $("outside-mean");
  slider.addEventListener("input", () => { $("outside-out").textContent = slider.value + " °C"; });
  slider.addEventListener("change", () => act("outside", { value: Number(slider.value) }));

  for (const b of document.querySelectorAll("[data-fault]")) {
    b.addEventListener("click", () => act("fault", { name: b.dataset.fault, value: b.getAttribute("aria-pressed") !== "true" }));
  }

  $("sp-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!spEdited.size) return;
    spProblem = setpointProblem(spValues());
    if (!spProblem) {
      const values = spValues();
      const value = Object.fromEntries([...spEdited].map((key) => [key, values[key]]));
      await send("setpoints", { value }).catch((err) => { spProblem = { message: err.message, keys: [] }; });
    }
    renderSetpointForm(state);
  });
  $("sp-discard").addEventListener("click", () => {
    spEdited.clear();
    spProblem = null;
    renderSetpointForm(state);
  });

  $("rails").addEventListener("click", (e) => {
    const lever = e.target.closest("[data-device]");
    const test = e.target.closest("[data-test]");
    if (lever) act("switch", { device: lever.dataset.device, value: lever.getAttribute("aria-pressed") !== "true" });
    else if (test) act("rcd_test", { device: test.dataset.test });
  });

  window.addEventListener("resize", () => { drawCurve(); drawTrend(); });
}

async function start() {
  buildSetpointForm();
  buildSpeeds();
  buildBoard();
  wire();
  applyLanguage();
  setText("alarm-summary", t("noData"));
  const server = !document.documentElement.hasAttribute("data-demo")
    && await loadHistory().then(() => true, () => false);
  if (server) {
    const stream = new EventSource("api/stream");
    stream.onmessage = (e) => {
      if (!$("link-lost").hidden) {
        $("link-lost").hidden = true;
        setLive(true);
        loadHistory().catch(() => {});
      }
      render(JSON.parse(e.data));
    };
    stream.onerror = () => {
      $("link-lost").hidden = false;
      setLive(false);
    };
  } else {
    await startDemo();
  }
}

// No haussim server behind this page: run the same Python code in the
// browser with Pyodide.
async function startDemo() {
  const note = $("demo-note");
  note.hidden = false;
  note.textContent = t("demoLoading");
  try {
    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = PYODIDE + "pyodide.js";
      script.onload = resolve;
      script.onerror = () => reject(new Error("Could not load Pyodide"));
      document.head.append(script);
    });
    const py = await loadPyodide({ indexURL: PYODIDE });
    py.FS.mkdirTree("/home/pyodide/haussim");
    for (const name of DEMO_MODULES) {
      const res = await fetch(`py/haussim/${name}.py`);
      if (!res.ok) throw new Error(`Could not load ${name}.py`);
      py.FS.writeFile(`/home/pyodide/haussim/${name}.py`, await res.text());
    }
    const ns = py.globals.get("dict")();
    py.runPython(DEMO_GLUE, { globals: ns });
    demo = { step: ns.get("step"), snapshot: ns.get("snapshot"), command: ns.get("command") };
    history = JSON.parse(ns.get("history")());
  } catch (err) {
    note.textContent = t("demoFailed", err.message);
    return;
  }
  note.innerHTML = t("demoReady");

  let last = performance.now();
  setInterval(() => {
    const now = performance.now();
    demo.step((now - last) / 1000);
    last = now;
  }, 100);
  setInterval(() => render(JSON.parse(demo.snapshot())), 250);
}

start();
