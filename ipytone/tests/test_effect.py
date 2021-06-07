import pytest
from traitlets import TraitError

from ipytone import (
    CrossFade,
    Distortion,
    FeedbackDelay,
    Gain,
    PingPongDelay,
    Reverb,
    Tremolo,
    Vibrato,
)
from ipytone.effect import Effect, StereoEffect


def test_effect():
    fx = Effect()

    assert isinstance(fx.input, Gain)
    assert isinstance(fx.output, CrossFade)
    assert fx.wet is fx.output.fade


def test_stereo_effect():
    fx = StereoEffect()

    assert fx.input.channel_count == 2
    assert fx.input.channel_count_mode == "explicit"


def test_distortion():
    dist = Distortion()

    assert dist.distortion == 0.4
    assert dist.oversample == "none"

    for value in [-1.2, 1.2]:
        with pytest.raises(TraitError, match="Distortion value must be in range.*"):
            dist.distortion = value

    # just test enum values
    dist.oversample = "2x"
    dist.oversample = "4x"


def test_feedback_delay():
    dly = FeedbackDelay()

    assert dly.delay_time.value == 0.25
    assert dly.delay_time.units == "time"
    assert dly.feedback.value == 0.125
    assert dly.feedback.units == "normalRange"

    e = dly.dispose()
    assert e is dly
    assert dly.delay_time.disposed is True
    assert dly.feedback.disposed is True


def test_pingpong_delay():
    dly = PingPongDelay()

    assert dly.delay_time.value == 0.25
    assert dly.delay_time.units == "time"
    assert dly.feedback.value == 0.125
    assert dly.feedback.units == "normalRange"

    e = dly.dispose()
    assert e is dly
    assert dly.delay_time.disposed is True
    assert dly.feedback.disposed is True


def test_reverb():
    rv = Reverb()

    assert rv.decay == 1.5
    assert rv.pre_delay == 0.01

    with pytest.raises(TraitError, match="Decay must be greater than 0.001 seconds"):
        rv.decay = 0

    with pytest.raises(TraitError, match="Pre-delay value must be positive"):
        rv.pre_delay = -1


def test_tremolo(mocker):
    tre = Tremolo()
    mocker.patch.object(tre, "send")

    assert tre.type == "sine"
    assert tre.frequency.value == 10
    assert tre.frequency.units == "frequency"
    assert tre.depth.value == 0.5
    assert tre.depth.units == "normalRange"
    assert tre.spread == 180

    e = tre.start()
    tre.send.assert_called_with(
        {
            "event": "trigger",
            "method": "start",
            "args": {"time": {"value": None, "eval": False}},
            "arg_keys": ["time"],
        }
    )
    assert e is tre

    e = tre.stop()
    tre.send.assert_called_with(
        {
            "event": "trigger",
            "method": "stop",
            "args": {"time": {"value": None, "eval": False}},
            "arg_keys": ["time"],
        }
    )
    assert e is tre

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        tre.type = "not a good oscillator wave"

    e = tre.dispose()
    assert e is tre
    assert tre.frequency.disposed is True
    assert tre.depth.disposed is True


def test_vibrato():
    vib = Vibrato()

    assert vib.type == "sine"
    assert vib.frequency.value == 5
    assert vib.frequency.units == "frequency"
    assert vib.depth.value == 0.1
    assert vib.depth.units == "normalRange"

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        vib.type = "not a good oscillator wave"

    e = vib.dispose()
    assert e is vib
    assert vib.frequency.disposed is True
    assert vib.depth.disposed is True
