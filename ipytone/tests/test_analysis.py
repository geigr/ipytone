import pytest
from traitlets.traitlets import TraitError

from ipytone.analysis import Analyser
from ipytone.core import Gain


def test_analyser():
    analyser = Analyser()

    assert isinstance(analyser.output, Gain)
    assert analyser.input is analyser.output

    assert analyser.channels == 1

    assert analyser.type == "fft"
    analyser.type = "waveform"
    assert analyser.type == "waveform"
    with pytest.raises(TraitError):
        analyser.type = "invalid"

    assert analyser.size == 1024
    analyser.size = 512
    assert analyser.size == 512
    with pytest.raises(ValueError, match="size must be a power of two"):
        analyser.size = 10

    assert analyser.smoothing == 0.8
