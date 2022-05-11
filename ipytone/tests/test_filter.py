import pytest
from traitlets import TraitError

from ipytone.base import NativeAudioNode
from ipytone.core import Gain
from ipytone.filter import BiquadFilter, Filter


def test_biquad_filter():
    bq_filter = BiquadFilter()

    assert isinstance(bq_filter.input, NativeAudioNode)
    assert bq_filter.input is bq_filter.output

    assert bq_filter.array_length == 128
    assert bq_filter.sync_array is False

    assert bq_filter.type == "lowpass"
    assert bq_filter.frequency.value == 350
    assert bq_filter.frequency.units == "frequency"
    assert bq_filter.q.value == 1
    assert bq_filter.q.units == "number"
    assert bq_filter.detune.value == 0
    assert bq_filter.detune.units == "cents"
    assert bq_filter.gain.value == 0
    assert bq_filter.gain.units == "decibels"

    with pytest.raises(TraitError):
        bq_filter.type = "invalid"

    assert "frequency=" in repr(bq_filter)
    assert "q=" in repr(bq_filter)

    bq_filter.dispose()
    assert bq_filter.frequency.disposed is True
    assert bq_filter.q.disposed is True
    assert bq_filter.detune.disposed is True
    assert bq_filter.gain.disposed is True


def test_filter():
    filtr = Filter()

    assert isinstance(filtr.input, Gain)
    assert isinstance(filtr.output, Gain)
    assert filtr.input is not filtr.output

    assert filtr.array_length == 128
    assert filtr.sync_array is False

    assert filtr.type == "lowpass"
    assert filtr.frequency.value == 350
    assert filtr.frequency.units == "frequency"
    assert filtr.q.value == 1
    assert filtr.q.units == "positive"
    assert filtr.detune.value == 0
    assert filtr.detune.units == "cents"
    assert filtr.gain.value == 0
    assert filtr.gain.units == "decibels"
    assert filtr.rolloff == -12

    with pytest.raises(TraitError):
        filtr.type = "invalid"
    with pytest.raises(TraitError):
        filtr.rolloff = -999

    assert "frequency=" in repr(filtr)
    assert "q=" in repr(filtr)

    filtr.dispose()
    assert filtr.frequency.disposed is True
    assert filtr.q.disposed is True
    assert filtr.detune.disposed is True
    assert filtr.gain.disposed is True
