from unittest.mock import call

import pytest

from ipytone.envelope import AmplitudeEnvelope
from ipytone.event import Event, Loop, Note, Part, Pattern, Sequence, _no_callback
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
        ],
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
def test_event_cancel(mocker, method):
    event = Event()
    mocker.patch.object(event, "send")

    e = getattr(event, method)()
    assert e is event
    event.send.assert_called_once_with({"event": "cancel", "time": None})


def test_part():
    part = Part()
    assert part.length == 0
    assert part.value is None


def test_part_callback(mocker):
    osc = Oscillator()

    def clb(time, value):
        osc.frequency.exp_ramp_to(value.note, 0.2, start_time=time)

    part = Part(
        events=[
            {"time": "0:0", "note": "C3"},
            Note(time="0:2", note="D3", velocity=0.5),
        ]
    )
    mocker.patch.object(part, "send")
    part.callback = clb

    expected = {
        "event": "set_callback",
        "op": "",
        "items": [
            {
                "method": "exponentialRampTo",
                "callee": osc.frequency.model_id,
                "args": {
                    "value": {"value": "value.note", "eval": True},
                    "ramp_time": {"value": 0.2, "eval": False},
                    "start_time": {"value": "time", "eval": True},
                },
                "arg_keys": ["value", "ramp_time", "start_time"],
            }
        ],
    }

    part.send.assert_called_with(expected)

    assert part._events == [
        {"time": "0:0", "note": "C3", "velocity": 1, "duration": 0.1},
        {"time": "0:2", "note": "D3", "velocity": 0.5, "duration": 0.1},
    ]

    with pytest.raises(ValueError, match="cannot interpret this value as a Note"):
        Part(callback=clb, events=["invalid"])


@pytest.mark.parametrize("note", [{"time": "0:0", "note": "C3"}, Note(time="0:0", note="C3")])
def test_part_add(mocker, note):
    part = Part()
    mocker.patch.object(part, "send")

    p = part.add(note)
    assert p is part

    expected = {
        "event": "add",
        "arg": {"time": "0:0", "note": "C3", "velocity": 1, "duration": 0.1},
    }
    part.send.assert_called_once_with(expected)


@pytest.mark.parametrize("note", [{"time": "0:0", "note": "C3"}, Note(time="0:0", note="C3")])
def test_part_at(mocker, note):
    part = Part()
    mocker.patch.object(part, "send")

    part.at("0:0", note)

    expected = {
        "event": "at",
        "time": "0:0",
        "value": {"time": "0:0", "note": "C3", "velocity": 1, "duration": 0.1},
    }
    part.send.assert_called_once_with(expected)


@pytest.mark.parametrize("note", [{"time": "0:0", "note": "C3"}, Note(time="0:0", note="C3")])
def test_part_remove(mocker, note):
    part = Part()
    mocker.patch.object(part, "send")

    part.remove(time="0:0", note=note)

    expected = {
        "event": "remove",
        "time": "0:0",
        "value": {"time": "0:0", "note": "C3", "velocity": 1, "duration": 0.1},
    }
    part.send.assert_called_once_with(expected)

    with pytest.raises(ValueError, match="Please provide at least one value"):
        part.remove()


@pytest.mark.parametrize("method", ["clear", "dispose"])
def test_part_clear(mocker, method):
    part = Part()
    mocker.patch.object(part, "send")

    p = getattr(part, method)()
    assert p is part

    if method == "clear":
        part.send.assert_called_once_with({"event": "clear"})
    elif method == "dispose":
        part.send.assert_has_calls(
            [call({"event": "clear"}), call({"event": "cancel", "time": None})],
            any_order=True,
        )


def test_sequence():
    seq = Sequence()
    assert seq.length == 0
    assert seq.value is None
    assert seq.events == []
    assert seq.subdivision == "8n"
    assert seq.loop is True
    assert seq.loop_start == 0
    assert seq.loop_end == 0


def test_sequence_callback(mocker):
    osc = Oscillator()

    def clb(time, value):
        osc.frequency.exp_ramp_to(value.note, 0.2, start_time=time)

    seq = Sequence(events=["C4", ["E4", "D4", "E4"], "G4", ["A4", "G4"]])
    mocker.patch.object(seq, "send")
    seq.callback = clb

    expected = {
        "event": "set_callback",
        "op": "",
        "items": [
            {
                "method": "exponentialRampTo",
                "callee": osc.frequency.model_id,
                "args": {
                    "value": {"value": "value.note", "eval": True},
                    "ramp_time": {"value": 0.2, "eval": False},
                    "start_time": {"value": "time", "eval": True},
                },
                "arg_keys": ["value", "ramp_time", "start_time"],
            }
        ],
    }

    seq.send.assert_called_with(expected)

    assert seq.events == ["C4", ["E4", "D4", "E4"], "G4", ["A4", "G4"]]


@pytest.mark.parametrize("method", ["clear", "dispose"])
def test_sequence_clear(mocker, method):
    seq = Sequence()
    mocker.patch.object(seq, "send")

    s = getattr(seq, method)()
    assert s is seq

    if method == "clear":
        seq.send.assert_called_once_with({"event": "clear"})
    elif method == "dispose":
        seq.send.assert_has_calls(
            [call({"event": "clear"}), call({"event": "cancel", "time": None})],
            any_order=True,
        )


def test_loop():
    loop = Loop()
    assert loop.interval == "8n"
    assert loop.iterations is None

    for key in ["loop=", "loop_start=", "loop_end="]:
        assert key not in repr(loop)
    assert "interval=" in repr(loop)

    loop.iterations = 5
    assert "iterations=" in repr(loop)


def test_loop_callback(mocker):
    env = AmplitudeEnvelope()

    def clb(time):
        env.trigger_attack_release(0.1, time)

    loop = Loop()
    mocker.patch.object(loop, "send")
    loop.callback = clb

    expected = {
        "event": "set_callback",
        "op": "",
        "items": [
            {
                "method": "triggerAttackRelease",
                "callee": env.model_id,
                "args": {
                    "duration": {"value": 0.1, "eval": False},
                    "time": {"value": "time", "eval": True},
                    "velocity": {"value": 1, "eval": False},
                },
                "arg_keys": ["duration", "time", "velocity"],
            }
        ],
    }

    loop.send.assert_called_with(expected)


def test_pattern():
    pattern = Pattern()
    assert pattern.interval == "8n"
    assert pattern.iterations is None
    assert pattern.pattern == "up"
    assert pattern.values == []

    assert "pattern=" in repr(pattern)


def test_pattern_callback(mocker):
    osc = Oscillator()

    def clb(time, value):
        osc.frequency.exp_ramp_to(value.note, 0.2, start_time=time)

    pattern = Pattern(values=["C2", "D4", "E5", "A6"])
    mocker.patch.object(pattern, "send")
    pattern.callback = clb

    expected = {
        "event": "set_callback",
        "op": "",
        "items": [
            {
                "method": "exponentialRampTo",
                "callee": osc.frequency.model_id,
                "args": {
                    "value": {"value": "value.note", "eval": True},
                    "ramp_time": {"value": 0.2, "eval": False},
                    "start_time": {"value": "time", "eval": True},
                },
                "arg_keys": ["value", "ramp_time", "start_time"],
            }
        ],
    }

    pattern.send.assert_called_with(expected)

    assert pattern.values == ["C2", "D4", "E5", "A6"]
