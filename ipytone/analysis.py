from traitlets import Bool, Enum, Float, Int, List, Unicode, validate

from .core import AudioNode, Gain
from .observe import ScheduleObserveMixin


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
        pow2 = (size & (size - 1) == 0) and size != 0
        if not pow2:
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

    def _get_analyser_options(self):
        return {"size": 256, "type": "waveform", "channels": self._channels}

    @property
    def channels(self):
        """Number of channels of the meter."""
        return self._analyser.channels


class DCMeter(BaseMeter):
    """A node to get the raw value of an input audio signal."""

    _model_name = Unicode("DCMeterModel").tag(sync=True)
