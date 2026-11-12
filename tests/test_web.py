import http.client
import json
import urllib.error
import urllib.request

import pytest

from haussim import web
from haussim.cli import build_parser
from haussim.commands import CommandError, apply_command
from haussim.process import Process
from haussim.sim import Simulator
from haussim.web import HmiServer


@pytest.fixture
def sim():
    return Simulator(Process(seed=1))


@pytest.fixture
def server(sim):
    srv = HmiServer(sim, port=0)
    srv.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def url(srv, path):
    return f"http://127.0.0.1:{srv.server_address[1]}{path}"


def get(srv, path):
    with urllib.request.urlopen(url(srv, path), timeout=3) as r:
        return r.status, r.read()


def post(srv, body, headers=None):
    req = urllib.request.Request(
        url(srv, "/api/command"),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


# ---- commands without a server ---------------------------------------


def test_standby_and_back(sim):
    apply_command(sim, {"cmd": "auto", "value": False})
    assert sim.plc.auto is False
    apply_command(sim, {"cmd": "auto", "value": True})
    assert sim.plc.auto is True


def test_setpoints_all_or_nothing(sim):
    apply_command(sim, {"cmd": "setpoints", "value": {"room_day": 22, "curve_slope": 0.6}})
    assert sim.plc.setpoints["room_day"] == 22 and sim.plc.setpoints["curve_slope"] == 0.6
    with pytest.raises(CommandError):
        apply_command(sim, {"cmd": "setpoints", "value": {"room_day": 23, "flow_min": 55}})
    assert sim.plc.setpoints["room_day"] == 22  # the valid half was not applied


@pytest.mark.parametrize(
    "body",
    [
        {"cmd": "auto", "value": "false"},
        {"cmd": "speed", "value": True},
        {"cmd": "speed", "value": 7},
        {"cmd": "outside", "value": 40},
        {"cmd": "outside", "value": float("nan")},
        {"cmd": "setpoints", "value": {"room_day": True}},
        {"cmd": "setpoints", "value": {"nope": 1}},
        {"cmd": "setpoints", "value": {}},
        {"cmd": "setpoints", "value": {"room_night": 25}},
        {"cmd": "fault", "name": "roof", "value": True},
        {"cmd": "evu"},
        {"cmd": "explode"},
    ],
)
def test_bad_commands_are_refused(sim, body):
    with pytest.raises(CommandError):
        apply_command(sim, body)


def test_simulator_controls(sim):
    apply_command(sim, {"cmd": "speed", "value": 600})
    apply_command(sim, {"cmd": "pause", "value": True})
    apply_command(sim, {"cmd": "outside", "value": -10})
    apply_command(sim, {"cmd": "evu", "value": True})
    for name in ("hp", "circ", "window", "outside_sensor"):
        apply_command(sim, {"cmd": "fault", "name": name, "value": True})
    s = sim.snapshot()
    assert s["sim"]["speed"] == 600 and s["sim"]["paused"] and s["sim"]["outside_mean"] == -10
    assert s["evu_lock"]
    assert all(s["sim"][k] for k in ("hp_broken", "circ_broken", "window_open", "outside_sensor_broken"))


def test_evu_lock_stops_the_heat_pump(sim):
    sim.step(3 * 3600)
    apply_command(sim, {"cmd": "evu", "value": True})
    sim.step(120)
    s = sim.snapshot()
    assert not s["hp_cmd"] and not s["rod_on"]
    assert any(e[1] == "EVU" for e in s["events"])


def test_history_grows_one_sample_a_minute(sim):
    sim.step(30 * 60)
    rows = sim.history_list()
    assert 29 <= len(rows) <= 31 and len(rows[0]) == 7


# ---- HTTP ------------------------------------------------------------


def test_serves_hmi_files(server):
    for path in web.STATIC:
        status, body = get(server, path)
        assert status == 200 and body


def test_page_only_references_served_files(server):
    _, html = get(server, "/")
    for ref in ("tokens.css", "hmi.css", "hmi.js", "icons/haussim-32.png"):
        assert ref.encode() in html and "/" + ref in web.STATIC


def test_state_and_history(server):
    _, body = get(server, "/api/state")
    state = json.loads(body)
    assert state["auto"] is True and state["setpoints"]["room_day"] == 21.0
    _, body = get(server, "/api/history")
    assert isinstance(json.loads(body), list)


def test_command_round_trip(server):
    assert post(server, {"cmd": "auto", "value": False}) == (200, {"ok": True})
    _, body = get(server, "/api/state")
    assert json.loads(body)["auto"] is False
    status, body = post(server, {"cmd": "speed", "value": 3})
    assert status == 400 and "Speed" in body["error"]


def test_refuses_foreign_origin(server):
    status, _ = post(server, {"cmd": "ack"}, {"Origin": "http://evil.example"})
    assert status == 403


def test_refuses_rebound_host(server):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
    conn.request("POST", "/api/command", body=b'{"cmd":"ack"}', headers={"Host": "evil.example"})
    assert conn.getresponse().status == 403
    conn.close()


def test_unknown_path(server):
    with pytest.raises(urllib.error.HTTPError) as err:
        get(server, "/nope")
    assert err.value.code == 404


def test_run_parser_defaults():
    args = build_parser().parse_args(["run", "--no-browser"])
    assert args.speed == 120 and args.http_port == 8080 and args.no_browser
