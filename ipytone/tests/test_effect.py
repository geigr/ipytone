import pytest
from traitlets import TraitError

from ipytone import CrossFade, Gain, Vibrato
from ipytone.effect import Effect, FeedbackDelay


def test_effect():
    fx = Effect()

    assert isinstance(fx.input, Gain)
    assert isinstance(fx.output, CrossFade)
    assert fx.wet is fx.output.fade


def test_feedback_delay():
    dly = FeedbackDelay()

    assert dly.delay_time.value == 0.25
    assert dly.delay_time.units == "time"
    assert dly.feedback.value == 0.125
    assert dly.feedback.units == "normalRange"

    s = dly.dispose()
    assert s is dly
    assert dly.delay_time.disposed is True
    assert dly.feedback.disposed is True


def test_vibrato():
    vib = Vibrato()

    assert vib.type == "sine"
    assert vib.frequency.value == 5
    assert vib.frequency.units == "frequency"
    assert vib.depth.value == 0.1
    assert vib.depth.units == "normalRange"

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        vib.type = "not a good oscillator wave"

    s = vib.dispose()
    assert s is vib
    assert vib.frequency.disposed is True
    assert vib.depth.disposed is True
