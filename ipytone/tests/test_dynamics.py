from ipytone.base import NativeAudioNode
from ipytone.channel import MultibandSplit
from ipytone.core import Gain
from ipytone.dynamics import Compressor, Limiter, MultibandCompressor


def test_compressor():
    comp = Compressor()

    assert isinstance(comp.input, NativeAudioNode)
    assert comp.input.type == "DynamicsCompressorNode"
    assert comp.input is comp.output

    assert comp.threshold.value == -24
    assert comp.threshold.units == "decibels"
    assert comp.ratio.value == 12
    assert comp.ratio.units == "positive"
    assert comp.attack.value == 0.003
    assert comp.attack.units == "time"
    assert comp.release.value == 0.25
    assert comp.release.units == "time"
    assert comp.knee.value == 30
    assert comp.knee.units == "decibels"

    assert "threshold" in repr(comp)
    assert "ratio" in repr(comp)

    comp.dispose()
    assert comp.threshold.disposed is True
    assert comp.ratio.disposed is True
    assert comp.attack.disposed is True
    assert comp.release.disposed is True
    assert comp.knee.disposed is True


def test_limiter():
    lim = Limiter()

    assert isinstance(lim.input, Compressor)
    assert lim.input is lim.output

    assert lim.threshold.value == -12
    assert lim.threshold is lim.output.threshold
    assert lim.output.ratio.value == 20
    assert lim.output.attack.value == 0.003
    assert lim.output.release.value == 0.01


def test_multiband_compressor(audio_graph):
    comp = MultibandCompressor()

    assert isinstance(comp.input, MultibandSplit)
    assert isinstance(comp.output, Gain)

    assert comp.low.threshold.value == -30
    assert comp.low.ratio.value == 6
    assert comp.low.attack.value == 0.03
    assert comp.low.release.value == 0.25
    assert comp.low.knee.value == 10
    assert comp.mid.threshold.value == -24
    assert comp.mid.ratio.value == 3
    assert comp.mid.attack.value == 0.02
    assert comp.mid.release.value == 0.3
    assert comp.mid.knee.value == 16
    assert comp.high.threshold.value == -24
    assert comp.high.ratio.value == 3
    assert comp.high.attack.value == 0.02
    assert comp.high.release.value == 0.3
    assert comp.high.knee.value == 16

    assert comp.low_frequency.value == 250
    assert comp.low_frequency is comp.input.low_frequency
    assert comp.high_frequency.value == 2000
    assert comp.high_frequency is comp.input.high_frequency

    # test connections
    assert (comp.input.low, comp.low, 0, 0) in audio_graph.connections
    assert (comp.low, comp.output, 0, 0) in audio_graph.connections
    assert (comp.input.mid, comp.mid, 0, 0) in audio_graph.connections
    assert (comp.mid, comp.output, 0, 0) in audio_graph.connections
    assert (comp.input.high, comp.high, 0, 0) in audio_graph.connections
    assert (comp.high, comp.output, 0, 0) in audio_graph.connections

    comp.dispose()
    assert comp.low.disposed is True
    assert comp.mid.disposed is True
    assert comp.high.disposed is True
