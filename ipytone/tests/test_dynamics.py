from ipytone.base import NativeAudioNode
from ipytone.dynamics import Compressor, Limiter


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
