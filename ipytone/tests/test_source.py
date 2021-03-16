import pytest
from traitlets import TraitError

from ipytone import Noise, Oscillator, Volume
from ipytone.source import Source


def test_source():
    node = Source()

    assert node.mute is False
    assert node.state == "stopped"
    assert isinstance(node.output, Volume)
    assert node.volume is node.output.volume

    n = node.start()
    assert node.state == "started"
    assert n is node

    n = node.stop()
    assert node.state == "stopped"
    assert n is node


def test_oscillator():
    osc = Oscillator()

    assert osc.type == "sine"
    assert osc.frequency.value == 440
    assert osc.frequency.units == "frequency"
    assert osc.detune.value == 0
    assert osc.detune.units == "cents"

    # just test that the following types are valid
    for wave in ["sine", "square", "sawtooth", "triangle"]:
        for pcount in range(2):
            osc.type = wave + str(pcount)

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        osc.type = "not a good oscillator wave"

    # test dispose
    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.frequency.disposed is True
    assert osc.detune.disposed is True


def test_noise():
    noise = Noise()

    assert noise.type == "white"
    assert noise.fade_in == 0
    assert noise.fade_out == 0

    # just test that the following types are valid
    for typ in ["pink", "white", "brown"]:
        noise.type = typ

    with pytest.raises(TraitError):
        noise.type = "not a valid noise type"
