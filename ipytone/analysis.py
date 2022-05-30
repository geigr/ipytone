import numpy as np
from traitlets import Bool, Enum, Float, Int, List, Unicode, validate

from ipytone.base import PyAudioNode
from ipytone.filter import OnePoleFilter
from ipytone.signal import Abs

from .core import AudioNode, Gain
from .observe import ScheduleObserveMixin


def is_pow2(value):
    return (value & (value - 1) == 0) and value != 0


class Analyser(AudioNode, ScheduleObserveMixin):
    """A node that may be used to extract frequency (FFT) or waveform data
    from an incoming audio signal.

    """

    _model_name = Unicode("AnalyserModel").tag(sync=True)

    _channels = Int(1).tag(sync=True)
    type = Enum(["waveform", "fft"], default_value="fft", help="analysis function").tag(sync=True)
    size = Int(1024, help="array size (must be a power of two)").tag(sync=True)
    smoothing = Float(0.8, help="controls the time averaging window").tag(sync=True)

    _observable_traits = List(["array"])
    _default_observed_trait = "array"

    def __init__(self, channels=1, **kwargs):
        gain = Gain(_create_node=False)

        kwargs.update({"_input": gain, "_output": gain, "_channels": channels})
        super().__init__(**kwargs)

    @validate("size")
    def _is_power_of_two(self, proposal):
        size = proposal["value"]
        if not is_pow2(size):
            raise ValueError(f"size must be a power of two, found {size}")
        return size

    @property
    def channels(self):
        """Number of channels the analyser does the analysis on."""
        return self._channels


class BaseMeter(AudioNode, ScheduleObserveMixin):
    """Base class for metering nodes."""

    _model_name = Unicode("BaseMeterModel").tag(sync=True)

    def __init__(self, **kwargs):
        self._analyser = Analyser(_create_node=False, **self._get_analyser_options())

        kwargs.update({"_input": self._analyser, "_output": self._analyser})
        super().__init__(**kwargs)

    def _get_analyser_options(self):
        return {"size": 256, "type": "waveform"}


class Meter(BaseMeter):
    """A node to get the RMS value of an input audio signal."""

    _model_name = Unicode("MeterModel").tag(sync=True)

    _channels = Int(1).tag(sync=True)

    normal_range = Bool(False, help="value in range [0-1] (True) or decibels (False)").tag(
        sync=True
    )
    smoothing = Float(0.8, help="controls the time averaging window").tag(sync=True)

    def __init__(self, channel_count=1, **kwargs):
        self._channels = channel_count
        super().__init__(**kwargs)
        self._analyser.smoothing = self.smoothing

    def _get_analyser_options(self):
        return {"size": 256, "type": "waveform", "channels": self._channels}

    @property
    def channels(self):
        """Number of channels of the meter."""
        return self._analyser.channels


class DCMeter(BaseMeter):
    """A node to get the raw value of an input audio signal."""

    _model_name = Unicode("DCMeterModel").tag(sync=True)


class Waveform(BaseMeter):
    """A node to get waveform data from an input audio signal."""

    _model_name = Unicode("WaveformModel").tag(sync=True)

    size = Int(1024, help="array size (must be a power of two)").tag(sync=True)

    _observable_traits = List(["array"])
    _default_observed_trait = "array"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._analyser.size = self.size

    def _get_analyser_options(self):
        return {"type": "waveform"}

    @validate("size")
    def _is_power_of_two(self, proposal):
        size = proposal["value"]
        if not is_pow2(size):
            raise ValueError(f"size must be a power of two, found {size}")
        return size


class FFT(BaseMeter):
    """A node to get frequency data from an input audio signal."""

    _model_name = Unicode("FFTModel").tag(sync=True)

    size = Int(1024, help="array size (must be a power of two)").tag(sync=True)
    normal_range = Bool(False, help="value in range [0-1] (True) or decibels (False)").tag(
        sync=True
    )
    smoothing = Float(0.8, help="controls the time averaging window").tag(sync=True)

    _observable_traits = List(["array"])
    _default_observed_trait = "array"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._analyser.size = self.size
        self._analyser.smoothing = self.smoothing

    def _get_analyser_options(self):
        return {"type": "fft"}

    @validate("size")
    def _is_power_of_two(self, proposal):
        size = proposal["value"]
        if not is_pow2(size):
            raise ValueError(f"size must be a power of two, found {size}")
        return size

    @property
    def frequency_labels(self):
        """Frequency label values (in Hertz)."""
        # assume sample rate 44,1 MHz (TODO: get it from Tone context)
        sample_rate = 44100
        return np.arange(self.size) * sample_rate / (self.size * 2)


class Follower(PyAudioNode):
    """Simple envelope follower that consists of a lowpass filter applied to the
    absolute value of an incoming audio signal.

    """

    def __init__(self, smoothing=0.05, **kwargs):
        self._smoothing = smoothing
        self._abs = Abs()
        self._lowpass = OnePoleFilter(type="lowpass", frequency=1 / self._smoothing)

        super().__init__(self._abs, self._lowpass, **kwargs)

        self._abs.connect(self._lowpass)

    @property
    def smoothing(self):
        """Envelope follower smoothing, in seconds."""
        return self._smoothing

    @smoothing.setter
    def smoothing(self, value):
        self._smoothing = value
        self._lowpass.frequency = 1 / self._smoothing
