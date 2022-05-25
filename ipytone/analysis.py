from traitlets import Enum, Int, Float, List, Unicode, validate

from .core import AudioNode, Gain
from .observe import ScheduleObserveMixin


class Analyser(AudioNode, ScheduleObserveMixin):

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
