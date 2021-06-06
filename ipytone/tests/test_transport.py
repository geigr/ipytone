import pytest

from ipytone import transport
from ipytone.source import Oscillator
from ipytone.transport import Transport


def test_transport():
    # signleton
    assert Transport() is transport


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
                "args": {"time": "time", "offset": None, "duration": None},
                "arg_keys": ["time", "offset", "duration"],
            },
            {
                "method": "stop",
                "callee": osc.model_id,
                "args": {"time": "time + 1"},
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

    expected = {"event": "play", "method": method, "args": args, "arg_keys": list(args)}

    t = getattr(transport, method)(*args.values())
    assert t is transport
    transport.send.assert_called_once_with(expected)
