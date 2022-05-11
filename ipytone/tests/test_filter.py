import pytest
from traitlets import TraitError

from ipytone.base import NativeAudioNode
from ipytone.channel import MultibandSplit
from ipytone.core import Gain
from ipytone.filter import (
    EQ3,
    BiquadFilter,
    FeedbackCombFilter,
    Filter,
    LowpassCombFilter,
    OnePoleFilter,
)


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

    assert "type" in repr(bq_filter)
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

    assert "type" in repr(filtr)
    assert "frequency=" in repr(filtr)
    assert "q=" in repr(filtr)

    filtr.dispose()
    assert filtr.frequency.disposed is True
    assert filtr.q.disposed is True
    assert filtr.detune.disposed is True
    assert filtr.gain.disposed is True


def test_one_pole_filter():
    op_filter = OnePoleFilter()

    assert isinstance(op_filter.input, Gain)
    assert isinstance(op_filter.output, Gain)
    assert op_filter.input is not op_filter.output

    assert op_filter.array_length == 128
    assert op_filter.sync_array is False

    assert op_filter.type == "lowpass"
    assert op_filter.frequency == 880

    with pytest.raises(TraitError):
        op_filter.type = "highshelf"

    assert "type" in repr(op_filter)
    assert "frequency=" in repr(op_filter)


def test_feedback_comb_filter():
    fc_filter = FeedbackCombFilter()

    assert isinstance(fc_filter.input, Gain)
    assert isinstance(fc_filter.output, Gain)
    assert fc_filter.input is not fc_filter.output

    assert fc_filter.delay_time.value == 0.1
    assert fc_filter.delay_time.units == "time"
    assert fc_filter.resonance.value == 0.5
    assert fc_filter.resonance.units == "normalRange"

    assert "delay_time" in repr(fc_filter)
    assert "resonance" in repr(fc_filter)

    fc_filter.dispose()
    assert fc_filter.delay_time.disposed is True
    assert fc_filter.resonance.disposed is True


def test_lowpass_comb_filter():
    lc_filter = LowpassCombFilter()

    assert isinstance(lc_filter.input, OnePoleFilter)
    assert isinstance(lc_filter.output, FeedbackCombFilter)

    assert lc_filter.delay_time.value == 0.1
    assert lc_filter.delay_time.units == "time"
    assert lc_filter.delay_time is lc_filter.output.delay_time
    assert lc_filter.resonance.value == 0.5
    assert lc_filter.resonance.units == "normalRange"
    assert lc_filter.resonance is lc_filter.output.resonance
    assert lc_filter.dampening == 3000
    assert lc_filter.dampening == lc_filter.input.frequency

    assert "delay_time" in repr(lc_filter)
    assert "resonance" in repr(lc_filter)
    assert "dampening" in repr(lc_filter)


def test_eq3(audio_graph):
    eq = EQ3()

    assert isinstance(eq.input, MultibandSplit)
    assert isinstance(eq.output, Gain)

    assert eq.low.value == 0
    assert eq.mid.value == 0
    assert eq.high.value == 0
    assert eq.low_frequency.value == 400
    assert eq.low_frequency is eq.input.low_frequency
    assert eq.high_frequency.value == 2500
    assert eq.high_frequency is eq.input.high_frequency
    assert eq.q is eq.input.q

    # test connections
    assert (eq.input.low, eq._low_gain, 0, 0) in audio_graph.connections
    assert (eq._low_gain, eq.output, 0, 0) in audio_graph.connections
    assert (eq.input.mid, eq._mid_gain, 0, 0) in audio_graph.connections
    assert (eq._mid_gain, eq.output, 0, 0) in audio_graph.connections
    assert (eq.input.high, eq._high_gain, 0, 0) in audio_graph.connections
    assert (eq._high_gain, eq.output, 0, 0) in audio_graph.connections

    eq.dispose()
    assert eq._low_gain.disposed is True
    assert eq._mid_gain.disposed is True
    assert eq._high_gain.disposed is True
