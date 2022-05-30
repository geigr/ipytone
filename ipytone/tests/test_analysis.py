import pytest
from traitlets.traitlets import TraitError

from ipytone.analysis import FFT, Analyser, DCMeter, Follower, Meter, Waveform
from ipytone.core import Gain
from ipytone.filter import OnePoleFilter
from ipytone.signal import Abs


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


def test_meter():
    meter = Meter()

    assert meter.input is meter.output
    assert isinstance(meter.output, Analyser)

    assert meter.normal_range is False
    assert meter.smoothing == 0.8
    assert meter.channels == 1

    # analyser settings
    assert meter.output.channels == 1
    assert meter.output.size == 256
    assert meter.output.type == "waveform"


def test_dcmeter():
    meter = DCMeter()

    assert meter.output.size == 256
    assert meter.output.type == "waveform"


def test_waveform():
    waveform = Waveform()

    assert waveform.size == waveform.output.size == 1024
    assert waveform.output.type == "waveform"

    with pytest.raises(ValueError, match="size must be a power of two"):
        waveform.size = 10


def test_fft():
    fft = FFT()

    assert fft.size == fft.output.size == 1024
    assert fft.smoothing == fft.output.smoothing == 0.8
    assert fft.normal_range is False
    assert fft.output.type == "fft"

    with pytest.raises(ValueError, match="size must be a power of two"):
        fft.size = 10

    assert fft.frequency_labels.size == fft.size


def test_follower(audio_graph):
    follower = Follower()

    assert isinstance(follower.input, Abs)
    assert isinstance(follower.output, OnePoleFilter)

    assert follower.output.type == "lowpass"
    assert follower.output.frequency == 1 / follower.smoothing
    assert follower.smoothing == 0.05

    follower.smoothing = 5
    assert follower.smoothing == 5
    assert follower.output.frequency == 1 / 5

    assert (follower.input, follower.output, 0, 0) in audio_graph.connections
