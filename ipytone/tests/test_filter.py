import pytest
from traitlets import TraitError

from ipytone.base import NativeAudioNode
from ipytone.filter import BiquadFilter


def test_biquad_filter():
    bq_filter = BiquadFilter()

    assert isinstance(bq_filter.input, NativeAudioNode)
    assert bq_filter.input is bq_filter.output

    assert bq_filter.curve_length == 128
    assert bq_filter.sync_curve is False

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
