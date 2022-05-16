import pytest

from ipytone import transport
from ipytone.core import Param
from ipytone.signal import Signal
from ipytone.source import Oscillator
from ipytone.transport import Transport, schedule, schedule_once, schedule_repeat


def test_transport():
    # singleton
    assert Transport() is transport

    assert isinstance(transport.bpm, Param)
    assert transport.bpm.value == 120
    assert transport.bpm.units == "bpm"

    assert transport.time_signature == 4

    assert transport.loop is False
    assert transport.loop_start == 0
    assert transport.loop_end == "4m"
    t = transport.set_loop_points(0, 2)
    assert t is transport
    assert transport.loop_start == 0
    assert transport.loop_end == 2

    assert repr(transport) == "Transport()"
    transport.loop = True
    assert repr(transport) == "Transport(loop=True, loop_start=0.0, loop_end=2.0)"

    assert transport.swing == 0
    assert transport.swing_subdivision == "8n"

    assert transport.position == 0
    assert transport.seconds == 0
    assert transport.progress == 0
    assert transport.ticks == 0

    transport.dispose()
    assert transport.bpm.disposed is True
    assert len(transport._all_event_id) == 0


@pytest.mark.parametrize(
    "op,func,expected_id,args,kwargs",
    [
        ("", transport.schedule, 0, {"time": "1m"}, {}),
        (
            "repeat",
            transport.schedule_repeat,
            1,
            {"interval": "2"},
            {"start_time": 0, "duration": None},
        ),
        ("once", transport.schedule_once, 2, {"time": "1m"}, {}),
    ],
)
def test_transport_schedule(mocker, op, func, expected_id, args, kwargs):
    mocker.patch.object(transport, "send")

    osc = Oscillator()

    def clb(time):
        osc.start(time).stop(time + 1)

    eid = func(clb, *args.values(), **kwargs)
    assert eid == expected_id

    expected = {
        "event": "schedule",
        "op": op,
        "id": expected_id,
        "items": [
            {
                "method": "start",
                "callee": osc.model_id,
                "args": {
                    "time": {"value": "time", "eval": True},
                    "offset": {"value": None, "eval": False},
                    "duration": {"value": None, "eval": False},
                },
                "arg_keys": ["time", "offset", "duration"],
            },
            {
                "method": "stop",
                "callee": osc.model_id,
                "args": {"time": {"value": "time + this.toSeconds(1)", "eval": True}},
                "arg_keys": ["time"],
            },
        ],
    }
    expected.update(args)
    expected.update(kwargs)

    transport.send.assert_called_with(expected)

    if op != "once":
        t = transport.clear(eid)
        assert t is transport
        transport.send.assert_called_with({"event": "clear", "id": eid})

    with pytest.raises(ValueError, match=".*event ID not found.*"):
        transport.clear(eid)


def test_transport_cancel(mocker):
    mocker.patch.object(transport, "send")
    t = transport.cancel()
    assert t is transport
    transport.send.assert_called_once_with({"event": "cancel", "after": 0})


@pytest.mark.parametrize(
    "method,args",
    [
        ("start", {"time": None, "offset": None}),
        ("stop", {"time": None}),
        ("pause", {"time": None}),
        ("toggle", {"time": None}),
    ],
)
def test_transport_play(mocker, method, args):
    mocker.patch.object(transport, "send")

    expected_args = {k: {"value": v, "eval": False} for k, v in args.items()}
    expected = {"event": "play", "method": method, "args": expected_args, "arg_keys": list(args)}

    t = getattr(transport, method)(*args.values())
    assert t is transport
    transport.send.assert_called_once_with(expected)


def test_transport_sync_signal(mocker):
    mocker.patch.object(transport, "send")

    sig = Signal()

    transport.sync_signal(sig)
    expected = {"event": "sync_signal", "op": "sync", "signal": sig.model_id, "ratio": None}
    transport.send.assert_called_with(expected)

    transport.unsync_signal(sig)
    expected = {"event": "sync_signal", "op": "unsync", "signal": sig.model_id}
    transport.send.assert_called_with(expected)

    with pytest.raises(KeyError, match=r".*not synced with transport"):
        transport.unsync_signal(sig)

    with pytest.raises(TypeError, match="signal must be an ipytone.Signal object"):
        transport.sync_signal("not a signal")

    with pytest.raises(TypeError, match="signal must be an ipytone.Signal object"):
        transport.unsync_signal("not a signal")


@pytest.mark.parametrize(
    "func,cm_func,args,kwargs",
    [
        (transport.schedule, schedule, ("1m",), {}),
        (transport.schedule_repeat, schedule_repeat, (2,), {"start_time": 0, "duration": None}),
        (transport.schedule_once, schedule_once, ("1m",), {}),
    ],
)
def test_schedule_context_manager(mocker, func, cm_func, args, kwargs):
    mocker.patch.object(transport, "send")

    osc = Oscillator()

    def clb(time):
        osc.start(time).stop(time + 1)

    eid = func(clb, *args, **kwargs)
    (expected,) = transport.send.call_args[0]

    with cm_func(*args, **kwargs) as (time, cm_eid):
        osc.start(time).stop(time + 1)

    (actual,) = transport.send.call_args[0]
    assert eid != cm_eid
    actual["id"] = expected["id"]

    assert actual == expected

    with pytest.raises(RuntimeError, match=r".*used outside of its context."):
        time.items
