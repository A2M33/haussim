"use strict";
// Report view: months, days and one day from the plant log (history.py).
// Loaded before hmi.js; uses its helpers ($, t, num, lang, demo) at call time.

const REPORT_I18N = {
  de: {
    viewPlant: "Anlage", viewReport: "Auswertung",
    reportTitle: "Auswertung", refresh: "Aktualisieren",
    reportEmpty: "Noch keine Aufzeichnung. Lassen Sie die Anlage einen Tag laufen oder starten Sie haussim mit --db.",
    sourceLive: (from) => `Aufzeichnung dieser Anlage seit ${from}. Die Energie kommt aus den Zählerständen, nicht aus Mittelwerten.`,
    sourceDemo: "Beispieljahr 2026, vorab simuliert mit Außentemperaturen wie im deutschen Mittel und wechselndem Wetter. Die Live-Anlage zeichnet in der Demo nicht auf.",
    monthsTitle: "Wärme und Strom je Monat",
    daysTitle: (m) => `Tage im ${m}`,
    seriesHeat: "Wärme", seriesElec: "Strom Wärmepumpe und Heizstab",
    clickMonth: "Klicken Sie auf einen Monat für seine Tage.",
    clickDay: "Klicken Sie auf einen Tag für seinen Verlauf.",
    tileJaz: "Jahresarbeitszahl", tileAz: "Arbeitszahl", tileHeat: "Wärme", tileElec: "Strom Wärmepumpe",
    tileRod: "davon Heizstab", tileHouse: "Strom Haushalt", tileRun: "Laufzeit Verdichter", tileStarts: "Starts",
    tileDays: "Tage aufgezeichnet",
    colMonth: "Monat", colDay: "Tag", colOutside: "Ø außen °C", colRoomMin: "Raum min. °C", colHeat: "Wärme kWh",
    colElec: "Strom kWh", colRod: "Heizstab kWh", colJaz: "JAZ", colAz: "AZ", colHouse: "Haushalt kWh",
    colRun: "Laufzeit h", colStarts: "Starts", total: "Summe",
    tipOutside: "Ø außen", tipJaz: "Arbeitszahl", tipRoom: "Raum", tipBuffer: "Puffer", tipTarget: "Soll Vorlauf",
    tipOutsideNow: "Außen", tipHeatW: "Wärmeleistung",
  },
  en: {
    viewPlant: "Plant", viewReport: "Report",
    reportTitle: "Report", refresh: "Refresh",
    reportEmpty: "Nothing logged yet. Let the plant run for a day, or start haussim with --db.",
    sourceLive: (from) => `Log of this plant since ${from}. Energy comes from meter readings, not from averages.`,
    sourceDemo: "Sample year 2026, simulated in advance with German average outside temperatures and changing weather. The live plant does not log in the demo.",
    monthsTitle: "Heat and electricity per month",
    daysTitle: (m) => `Days in ${m}`,
    seriesHeat: "Heat", seriesElec: "Electricity, heat pump and rod",
    clickMonth: "Click a month to see its days.",
    clickDay: "Click a day to see its course.",
    tileJaz: "Seasonal performance factor", tileAz: "Performance factor", tileHeat: "Heat", tileElec: "Heat pump electricity",
    tileRod: "of which heating rod", tileHouse: "Household electricity", tileRun: "Compressor run time", tileStarts: "Starts",
    tileDays: "Days logged",
    colMonth: "Month", colDay: "Day", colOutside: "Mean outside °C", colRoomMin: "Room min °C", colHeat: "Heat kWh",
    colElec: "Electricity kWh", colRod: "Rod kWh", colJaz: "SPF", colAz: "PF", colHouse: "Household kWh",
    colRun: "Run h", colStarts: "Starts", total: "Total",
    tipOutside: "Mean outside", tipJaz: "Performance factor", tipRoom: "Room", tipBuffer: "Buffer", tipTarget: "Flow target",
    tipOutsideNow: "Outside", tipHeatW: "Heat output",
  },
};

const report = { view: "plant", months: [], days: [], day: null, month: null, date: null, firstDay: null };

async function fetchReport(what, arg) {
  if (demo) {
    if (!demo.report) throw new Error("no log");
    return JSON.parse(demo.report(what, arg || ""));
  }
  const q = new URLSearchParams({ what, ...(arg ? { arg } : {}) });
  const res = await fetch("api/report?" + q);
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || res.statusText);
  return res.json();
}

const monthName = (m, style = "long") =>
  new Date(m + "-15T12:00:00").toLocaleDateString(lang, { month: style, ...(style === "long" ? { year: "numeric" } : {}) });
const dayName = (d, style = "long") =>
  new Date(d + "T12:00:00").toLocaleDateString(lang, style === "long"
    ? { weekday: "long", day: "numeric", month: "long", year: "numeric" } : { day: "numeric" });
const kwh = (v) => num(v, 0);
const hours = (s) => num(s / 3600, 0);
const ratio = (v) => (v == null ? "–" : num(v, 2));

function setView(view) {
  report.view = view;
  document.body.classList.toggle("view-report", view === "report");
  $("report").hidden = view !== "report";
  for (const b of document.querySelectorAll("[data-view]")) b.setAttribute("aria-pressed", b.dataset.view === view);
  if (view === "report") loadReport();
}

async function loadReport() {
  try {
    report.months = await fetchReport("months");
  } catch {
    report.months = [];
  }
  const empty = !report.months.length;
  $("report-empty").hidden = !empty;
  for (const el of document.querySelectorAll(".report > .panel, #tiles")) el.hidden = empty;
  if (empty) {
    setText("report-source", "");
    return;
  }
  if (!report.month || !report.months.some((m) => m.month === report.month)) {
    report.month = report.months[report.months.length - 1].month;
    report.date = null;
  }
  await loadDays();
}

async function loadDays() {
  report.days = await fetchReport("days", report.month);
  if (!report.firstDay || demo) {
    const first = report.months[0].month;
    const days = first === report.month ? report.days : await fetchReport("days", first);
    report.firstDay = days.length ? days[0].day : null;
  }
  if (!report.date || !report.days.some((d) => d.day === report.date)) {
    // The newest complete day: the live plant's today has only just begun.
    const done = report.days.filter((d) => demo || !state || d.day !== state.date);
    const pick = done.length ? done : report.days;
    report.date = pick.length ? pick[pick.length - 1].day : null;
  }
  report.day = report.date ? await fetchReport("day", report.date) : null;
  renderReport();
}

function renderReport() {
  if (!report.months.length) return;
  setText("report-source", demo ? t("sourceDemo") : t("sourceLive", report.firstDay ? dayName(report.firstDay) : "–"));
  renderTiles();
  renderMonthTable();
  setText("days-title", t("daysTitle", monthName(report.month)));
  renderDayTable();
  setText("day-title", report.date ? dayName(report.date) : "–");
  drawReportCharts();
  renderDayEvents();
}

function renderTiles() {
  const sum = (k) => report.months.reduce((a, m) => a + m[k], 0);
  const days = sum("days");
  const heat = sum("heat_kwh"), elec = sum("elec_kwh");
  const tiles = [
    [days >= 300 ? t("tileJaz") : t("tileAz"), elec > 0.05 ? num(heat / elec, 2) : "–", ""],
    [t("tileHeat"), kwh(heat), "kWh"],
    [t("tileElec"), kwh(elec), "kWh"],
    [t("tileRod"), kwh(sum("rod_kwh")), "kWh"],
    [t("tileHouse"), kwh(sum("house_kwh")), "kWh"],
    [t("tileRun"), hours(sum("run_s")), "h"],
    [t("tileStarts"), num(sum("starts"), 0), ""],
    [t("tileDays"), num(days, 0), ""],
  ];
  const box = $("tiles");
  box.replaceChildren();
  for (const [label, value, unit] of tiles) {
    const div = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    if (unit) {
      const small = document.createElement("small");
      small.textContent = unit;
      dd.append(small);
    }
    div.append(dt, dd);
    box.append(div);
  }
}

function fillTable(table, head, rows, foot, selectedKey, onPick) {
  table.replaceChildren();
  const thead = table.createTHead().insertRow();
  for (const h of head) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = h;
    thead.append(th);
  }
  const body = table.createTBody();
  for (const { key, cells } of rows) {
    const tr = body.insertRow();
    tr.tabIndex = 0;
    tr.setAttribute("aria-selected", key === selectedKey);
    for (const c of cells) tr.insertCell().textContent = c;
    tr.addEventListener("click", () => onPick(key));
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onPick(key); } });
  }
  if (foot) {
    const tr = table.createTFoot().insertRow();
    for (const c of foot) tr.insertCell().textContent = c;
  }
}

function pickMonth(month) {
  report.month = month;
  report.date = null;
  loadDays();
}

function pickDay(day) {
  report.date = day;
  fetchReport("day", day).then((d) => { report.day = d; renderReport(); });
}

function renderMonthTable() {
  const ms = report.months;
  const sum = (k) => ms.reduce((a, m) => a + m[k], 0);
  const heat = sum("heat_kwh"), elec = sum("elec_kwh");
  fillTable(
    $("months-table"),
    [t("colMonth"), t("colOutside"), t("colHeat"), t("colElec"), t("colRod"), t("colAz"), t("colHouse"), t("colRun"), t("colStarts")],
    ms.map((m) => ({
      key: m.month,
      cells: [monthName(m.month), num(m.outside), kwh(m.heat_kwh), kwh(m.elec_kwh), kwh(m.rod_kwh), ratio(m.jaz),
        kwh(m.house_kwh), hours(m.run_s), num(m.starts, 0)],
    })),
    [t("total"), "", kwh(heat), kwh(elec), kwh(sum("rod_kwh")), ratio(elec > 0.05 ? heat / elec : null),
      kwh(sum("house_kwh")), hours(sum("run_s")), num(sum("starts"), 0)],
    report.month,
    pickMonth,
  );
}

function renderDayTable() {
  fillTable(
    $("days-table"),
    [t("colDay"), t("colOutside"), t("colRoomMin"), t("colHeat"), t("colElec"), t("colAz"), t("colHouse"), t("colRun"), t("colStarts")],
    report.days.map((d) => ({
      key: d.day,
      cells: [dayName(d.day, "short") + ". " + monthName(report.month, "short"), num(d.outside), num(d.room_min),
        kwh(d.heat_kwh), kwh(d.elec_kwh), ratio(d.jaz), num(d.house_kwh, 1), num(d.run_s / 3600, 1), num(d.starts, 0)],
    })),
    null,
    report.date,
    pickDay,
  );
}

function renderDayEvents() {
  const list = $("day-events");
  list.replaceChildren();
  const events = report.day ? report.day.events : [];
  for (const [minute, kind, text] of events.slice(-40).reverse()) {
    const li = document.createElement("li");
    li.className = kind;
    for (const [txt, cls] of [[hhmm(minute), "time"], [kind, "kind"], [text, "text"]]) {
      const span = document.createElement("span");
      span.className = cls;
      span.textContent = txt;
      li.append(span);
    }
    list.append(li);
  }
}

// ---- charts ----------------------------------------------------------

// A round tick step for about four gridlines: 1, 2 or 5 times a power of ten.
function niceStep(max) {
  const raw = Math.max(max, 1e-9) / 4;
  const p = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 5, 10].map((m) => m * p).find((m) => m >= raw);
}

function showTip(tip, canvas, px, rows, title) {
  tip.replaceChildren();
  const strong = document.createElement("strong");
  strong.textContent = title;
  tip.append(strong);
  for (const [label, value, colour] of rows) {
    const row = document.createElement("div");
    row.className = "row";
    const name = document.createElement("span");
    if (colour) {
      const sw = document.createElement("span");
      sw.className = "sw";
      sw.style.background = colour;
      name.append(sw);
    }
    name.append(label);
    const val = document.createElement("span");
    val.textContent = value;
    row.append(name, val);
    tip.append(row);
  }
  tip.hidden = false;
  const w = tip.offsetWidth;
  const left = px + 16 + w > canvas.clientWidth ? px - 16 - w : px + 16;
  tip.style.left = Math.max(0, left) + "px";
}

// Grouped bars: heat and electricity per item, one kWh axis from zero.
function drawBars(canvas, items, label, selected, hover) {
  const [ctx, w, h] = canvasContext(canvas);
  const c = colours();
  const css = getComputedStyle(document.documentElement);
  const heatC = css.getPropertyValue("--c-heat").trim();
  const elecC = css.getPropertyValue("--c-elec").trim();
  const left = 52, right = w - 10, top = 12, bottom = h - 24;
  const peak = Math.max(1, ...items.map((i) => Math.max(i.heat_kwh, i.elec_kwh)));
  const tick = niceStep(peak);
  const max = Math.ceil(peak / tick) * tick;
  const y = (v) => bottom - (bottom - top) * v / max;
  const group = (right - left) / Math.max(1, items.length);
  const bar = Math.max(2, Math.min(26, (group * 0.72 - 2) / 2));

  ctx.save();
  ctx.font = "12px " + c.font;
  ctx.lineWidth = 1;
  for (let v = 0; v <= max + 1e-9; v += tick) {
    ctx.strokeStyle = c.grid;
    line(ctx, [[left, y(v)], [right, y(v)]]);
    ctx.fillStyle = c.muted;
    ctx.textAlign = "right";
    ctx.fillText(num(v, tick < 1 ? 1 : 0), left - 6, y(v) + 4);
  }
  ctx.textAlign = "center";
  const every = Math.ceil(items.length / Math.max(1, Math.floor((right - left) / 44)));
  items.forEach((it, i) => {
    const cx = left + group * (i + 0.5);
    if (it.key === selected || i === hover) {
      ctx.fillStyle = c.grid;
      ctx.fillRect(left + group * i, top, group, bottom - top);
    }
    const marks = [[it.heat_kwh, heatC, cx - bar - 1], [it.elec_kwh, elecC, cx + 1]];
    for (const [v, colour, x0] of marks) {
      if (v <= 0) continue;
      const y0 = y(v);
      ctx.fillStyle = colour;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(x0, y0, bar, bottom - y0, [Math.min(4, bar / 2), Math.min(4, bar / 2), 0, 0]);
      else ctx.rect(x0, y0, bar, bottom - y0);
      ctx.fill();
    }
    if (i % every === 0) {
      ctx.fillStyle = it.key === selected ? c.ink : c.muted;
      ctx.fillText(label(it), cx, h - 7);
    }
  });
  ctx.strokeStyle = c.muted;
  line(ctx, [[left, bottom + 0.5], [right, bottom + 0.5]]);
  ctx.restore();
  return { left, group, heatC, elecC };
}

function bindBars(canvas, tip, getItems, label, title, getSelected, onPick) {
  let layout = null;
  const index = (e) => {
    const items = getItems();
    if (!layout || !items.length) return -1;
    const i = Math.floor((e.offsetX - layout.left) / layout.group);
    return i >= 0 && i < items.length ? i : -1;
  };
  const draw = (hover = -1) => { layout = drawBars(canvas, getItems(), label, getSelected(), hover); };
  canvas.addEventListener("mousemove", (e) => {
    const i = index(e);
    draw(i);
    if (i < 0) { tip.hidden = true; return; }
    const it = getItems()[i];
    showTip(tip, canvas, e.offsetX, [
      [t("seriesHeat"), kwh(it.heat_kwh) + " kWh", layout.heatC],
      [t("seriesElec"), kwh(it.elec_kwh) + " kWh", layout.elecC],
      [t("tipJaz"), ratio(it.jaz)],
      [t("tipOutside"), num(it.outside) + " °C"],
    ], title(it));
  });
  canvas.addEventListener("mouseleave", () => { tip.hidden = true; draw(); });
  canvas.addEventListener("click", (e) => {
    const i = index(e);
    if (i >= 0) onPick(getItems()[i].key);
  });
  return draw;
}

function drawDay(canvas, hoverX) {
  const [ctx, w, h] = canvasContext(canvas);
  const samples = report.day ? report.day.samples : [];
  const c = colours();
  const left = 34, right = w - 8, top = 8, bottom = h - 22;
  const x = (m) => left + (right - left) * m / 1440;
  const y = (v) => bottom - (bottom - top) * (v - T_MIN) / (T_MAX - T_MIN);
  ctx.save();
  ctx.font = "12px " + c.font;
  ctx.lineWidth = 1;
  for (let v = T_MIN; v <= T_MAX; v += 20) {
    ctx.strokeStyle = c.grid;
    line(ctx, [[left, y(v)], [right, y(v)]]);
    ctx.fillStyle = c.muted;
    ctx.fillText(String(v), 4, y(v) + 4);
  }
  for (let m = 0; m <= 1440; m += w < 500 ? 360 : 180) {
    ctx.strokeStyle = c.grid;
    line(ctx, [[x(m), top], [x(m), bottom]]);
    ctx.fillStyle = c.muted;
    ctx.fillText(hhmm(m % 1440), Math.min(x(m) - 14, w - 34), h - 6);
  }
  const step = samples.length > 1 ? samples[1][0] - samples[0][0] : 15;
  for (const s of samples) {
    if (Math.abs(s[5]) < 1) continue;
    ctx.fillStyle = s[5] > 0 ? c.trace : c.signal;
    ctx.fillRect(x(s[0]), bottom - 8, Math.max(1, x(s[0] + step) - x(s[0])), 8);
  }
  const series = (col, colour, width, dash) => {
    ctx.strokeStyle = colour;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    line(ctx, samples.map((s) => [x(s[0]), y(s[col])]));
  };
  series(1, c.muted, 1.5, [2, 3]);
  series(4, c.muted, 1.5, [5, 4]);
  series(3, c.warn, 2, []);
  series(2, c.ink, 2.5, []);
  ctx.setLineDash([]);
  let nearest = null;
  if (hoverX != null && samples.length) {
    const minute = ((hoverX - left) / (right - left)) * 1440;
    nearest = samples.reduce((a, s) => (Math.abs(s[0] - minute) < Math.abs(a[0] - minute) ? s : a));
    ctx.strokeStyle = c.muted;
    ctx.lineWidth = 1;
    line(ctx, [[x(nearest[0]), top], [x(nearest[0]), bottom]]);
    for (const [col, colour] of [[2, c.ink], [3, c.warn]]) {
      ctx.fillStyle = colour;
      ctx.beginPath();
      ctx.arc(x(nearest[0]), y(nearest[col]), 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.restore();
  return nearest;
}

let drawMonthBars = null;
let drawDayBars = null;

function drawReportCharts() {
  if (report.view !== "report" || !report.months.length) return;
  const monthItems = report.months.map((m) => ({ ...m, key: m.month }));
  report.monthItems = monthItems;
  report.dayItems = report.days.map((d) => ({ ...d, key: d.day }));
  drawMonthBars();
  drawDayBars();
  drawDay($("chart-day"));
}

function initReport() {
  for (const b of document.querySelectorAll("[data-view]")) b.addEventListener("click", () => setView(b.dataset.view));
  $("report-refresh").addEventListener("click", loadReport);
  drawMonthBars = bindBars($("chart-months"), $("tip-months"), () => report.monthItems || [],
    (it) => monthName(it.key, "short"), (it) => monthName(it.key), () => report.month, pickMonth);
  drawDayBars = bindBars($("chart-days"), $("tip-days"), () => report.dayItems || [],
    (it) => dayName(it.key, "short"), (it) => dayName(it.key), () => report.date, pickDay);
  const dayCanvas = $("chart-day");
  const tip = $("tip-day");
  dayCanvas.addEventListener("mousemove", (e) => {
    const s = drawDay(dayCanvas, e.offsetX);
    if (!s) { tip.hidden = true; return; }
    const c = colours();
    showTip(tip, dayCanvas, e.offsetX, [
      [t("tipRoom"), num(s[2]) + " °C", c.ink],
      [t("tipBuffer"), num(s[3]) + " °C", c.warn],
      [t("tipTarget"), num(s[4]) + " °C"],
      [t("tipOutsideNow"), num(s[1]) + " °C"],
      [t("tipHeatW"), num(s[5] / 1000) + " kW"],
    ], hhmm(s[0]));
  });
  dayCanvas.addEventListener("mouseleave", () => { tip.hidden = true; drawDay(dayCanvas); });
  window.addEventListener("resize", drawReportCharts);
}
