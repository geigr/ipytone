import pytest
from traitlets import TraitError

from ipytone import Noise, Oscillator


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
