import math

import numpy as np
import pytest

from ipytone.base import NativeAudioNode, NativeAudioParam
from ipytone.core import (
    AudioBuffer,
    AudioBuffers,
    Destination,
    Gain,
    InternalAudioNode,
    Param,
    Volume,
    destination,
)
from ipytone.signal import Signal


def test_internal_audio_node():
    node = InternalAudioNode(type="test")

    assert node.number_of_inputs == 1
    assert node.number_of_outputs == 1
    assert repr(node) == "InternalAudioNode(type='test')"


@pytest.fixture(params=["param", "signal"])
def param_or_signal(request):
    if request.param == "param":
        obj = Param()
    else:
        obj = Signal(units="frequency")
    yield obj
    obj.dispose()


@pytest.mark.parametrize(
    "method,js_method,args",
    [
        ("set_value_at_time", "setValueAtTime", {"value": 1, "time": 0}),
        ("set_ramp_point", "setRampPoint", {"time": 0}),
        ("linear_ramp_to_value_at_time", "linearRampToValueAtTime", {"value": 1, "time": 1}),
        ("exp_ramp_to_value_at_time", "exponentialRampToValueAtTime", {"value": 1, "time": 1}),
        ("linear_ramp_to", "linearRampTo", {"value": 1, "ramp_time": 2, "start_time": 3}),
        ("exp_ramp_to", "exponentialRampTo", {"value": 1, "ramp_time": 2, "start_time": 3}),
        ("target_ramp_to", "targetRampTo", {"value": 1, "ramp_time": 2, "start_time": 3}),
        ("ramp_to", "linearRampTo", {"value": 1, "ramp_time": 2, "start_time": 3}),
        (
            "exp_approach_value_at_time",
            "exponentialApproachValueAtTime",
            {
                "value": 1,
                "time": 1,
                "ramp_time": 2,
            },
        ),
        ("set_target_at_time", "setTargetAtTime", {"value": 1, "start_time": 3, "time_const": 2}),
        (
            "set_value_curve_at_time",
            "setValueCurveAtTime",
            {"values": [0, 1, 2], "start_time": 0, "duration": 2, "scaling": None},
        ),
        ("cancel_scheduled_values", "cancelScheduledValues", {"time": 0}),
        ("cancel_and_hold_at_time", "cancelAndHoldAtTime", {"time": 0}),
    ],
)
def test_param_schedule_mixin(mocker, param_or_signal, method, js_method, args):
    mocker.patch.object(param_or_signal, "send")

    if param_or_signal.units == "frequency" and method == "ramp_to":
        js_method = "exponentialRampTo"

    expected_args = {k: {"value": v, "eval": False} for k, v in args.items()}
    expected = {
        "event": "trigger",
        "method": js_method,
        "args": expected_args,
        "arg_keys": list(args),
    }

    obj = getattr(param_or_signal, method)(*args.values())
    assert obj is param_or_signal
    param_or_signal.send.assert_called_once_with(expected)


def test_param():
    param = Param()

    assert param.value == 1
    assert param.units == "number"
    assert param.convert is True
    assert param.min_value == -math.inf
    assert param.max_value == math.inf
    assert param.overridden is False
    assert repr(param) == "Param(value=1.0, units='number')"
    assert isinstance(param.input, NativeAudioParam)

    param2 = Param(min_value=-0.2, max_value=0.2, swappable=True)

    assert param2.min_value == -0.2
    assert param2.max_value == 0.2
    assert isinstance(param2.input, NativeAudioNode)


@pytest.mark.parametrize(
    "units,expected_range",
    [
        ("audioRange", (-1, 1)),
        ("normalRange", (0, 1)),
        ("time", (0, math.inf)),
        ("decibels", (-math.inf, math.inf)),
    ],
)
def test_param_min_max_value(units, expected_range):
    param = Param(units=units)
    actual_range = (param.min_value, param.max_value)
    assert actual_range == expected_range


def test_gain():
    gain = Gain()

    assert gain.gain.value == 1
    assert gain.gain.units == "gain"
    assert isinstance(gain.input, NativeAudioNode)
    assert gain.input is gain.output
    assert repr(gain) == "Gain(gain=Param(value=1.0, units='gain'))"

    s = gain.dispose()
    assert s is gain
    assert gain.disposed is True
    assert gain.gain.disposed is True


def test_volume():
    volume = Volume()

    assert volume.volume.value == 0
    assert volume.volume.units == "decibels"
    assert volume.mute is False
    assert isinstance(volume.input, Gain)
    assert volume.input is volume.output
    assert repr(volume) == "Volume(volume=Param(value=0.0, units='decibels'), mute=False)"


def test_destination():
    assert destination.mute is False
    assert isinstance(destination.input, Volume)
    assert isinstance(destination.output, Gain)
    assert destination.volume is destination.input.volume
    expected = (
        "Destination(name='main output', volume=Param(value=0.0, units='decibels'), mute=False)"
    )
    assert repr(destination) == expected

    # test singleton
    dest1 = Destination()
    dest2 = Destination()

    assert dest1 == dest2 == destination


def test_audio_buffer():
    buffer = AudioBuffer("some_url")

    assert buffer.buffer_url == "some_url"
    assert buffer.array is None
    assert buffer.duration == 0
    assert buffer.length == 0
    assert buffer.n_channels == 0
    assert buffer.sample_rate == 0
    assert buffer.loaded is False
    assert buffer.reverse is False
    assert repr(buffer) == "AudioBuffer(loaded=False)"

    arr = np.random.uniform(low=-1, high=1, size=10)
    buffer2 = AudioBuffer(arr, reverse=True)

    assert buffer2.buffer_url is None
    assert buffer2.array is arr
    assert buffer2.reverse is True


def test_audio_buffers():
    bbuf = AudioBuffer("another_url")
    buffers = AudioBuffers({"A": "some_url", "B": bbuf}, base_url="base/")

    assert buffers.base_url == "base/"
    assert isinstance(buffers.buffers["A"], AudioBuffer)
    assert buffers.buffers["A"].buffer_url == "base/some_url"
    assert buffers.buffers["B"] is bbuf
    assert buffers.loaded is False
    assert repr(buffers) == "AudioBuffers(loaded=False)"

    buffers.add("C", "a_3rd_url")
    assert isinstance(buffers.buffers["C"], AudioBuffer)
    assert buffers.buffers["C"].buffer_url == "base/a_3rd_url"

    with pytest.raises(TypeError, match=r"Invalid buffer.*"):
        buffers.add("D", ["not", "a", "buffer"])

    b = buffers.dispose()
    assert b is buffers
    assert buffers.disposed is True
    assert bbuf.disposed is True
    assert buffers.buffers == {}
