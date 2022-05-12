import pytest

from ipytone.event import Event, _no_callback
from ipytone.source import Oscillator


def test_event():
    event = Event()

    assert event.value is None
    assert event.callback is _no_callback
    assert event.humanize == 0
    assert event.probability == 1
    assert event.mute is False
    assert event.start_offset == 0
    assert event.loop is False
    assert event.loop_start == 0
    assert event.loop_end == "1m"

    event.mute = True
    assert "mute=" in repr(event)
    event.loop = True
    assert "loop=" in repr(event)
    assert "loop_start=" in repr(event)
    assert "loop_end=" in repr(event)


def test_event_callback(mocker):
    osc = Oscillator()

    def clb(time, value):
        osc.frequency.exp_ramp_to(value, 0.2, start_time=time)

    event = Event(value="C4")
    mocker.patch.object(event, "send")
    event.callback = clb

    expected = {
        "event": "set_callback",
        "op": "",
        "items": [
            {
                "method": "exponentialRampTo",
                "callee": osc.frequency.model_id,
                "args": {
                    "value": {"value": "value", "eval": True},
                    "ramp_time": {"value": 0.2, "eval": False},
                    "start_time": {"value": "time", "eval": True},
                },
                "arg_keys": ["value", "ramp_time", "start_time"],
            }
        ]
    }

    event.send.assert_called_with(expected)

    assert event.value == "C4"


@pytest.mark.parametrize(
    "method,args",
    [
        ("start", {"time": None}),
        ("stop", {"time": None}),
    ],
)
def test_event_play(mocker, method, args):
    event = Event()
    mocker.patch.object(event, "send")

    expected_args = {k: {"value": v, "eval": False} for k, v in args.items()}
    expected = {"event": "play", "method": method, "args": expected_args, "arg_keys": list(args)}

    e = getattr(event, method)(*args.values())
    assert e is event
    event.send.assert_called_once_with(expected)


@pytest.mark.parametrize("method", ["cancel", "dispose"])
def test_even_cancel(mocker, method):
    event = Event()
    mocker.patch.object(event, "send")

    e = getattr(event, method)()
    assert e is event
    event.send.assert_called_once_with({"event": "cancel", "time": None})
