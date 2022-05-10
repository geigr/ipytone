from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Instance, Int, Unicode
from traittypes import Array

from .base import AudioNode
from .core import NativeAudioNode, Param
from .serialization import data_array_serialization

BIQUAD_FILTER_TYPES = [
    "lowpass",
    "highpass",
    "bandpass",
    "lowshelf",
    "highshelf",
    "notch",
    "allpass",
    "peaking",
]


class BiquadFilter(AudioNode):
    """Simple filter."""

    _model_name = Unicode("BiquadFilterModel").tag(sync=True)

    type = Enum(
        BIQUAD_FILTER_TYPES, allow_none=False, default_value="lowpass", help="filter type"
    ).tag(sync=True)
    _frequency = Instance(Param).tag(sync=True, **widget_serialization)
    _q = Instance(Param).tag(sync=True, **widget_serialization)
    _detune = Instance(Param).tag(sync=True, **widget_serialization)
    _gain = Instance(Param).tag(sync=True, **widget_serialization)

    curve = Array(
        allow_none=True,
        default_value=None,
        read_only=True,
        help="frequency response curve data (20hz-20kh)",
    ).tag(sync=True, **data_array_serialization)
    curve_length = Int(128, help="Curve data resolution (array length)").tag(sync=True)
    sync_curve = Bool(False, help="If True, synchronize curve data").tag(sync=True)

    def __init__(self, type="lowpass", frequency=350, q=1, detune=0, gain=0, **kwargs):
        bq_filter = NativeAudioNode(type="BiquadFilterNode")

        p_frequency = Param(units="frequency", value=frequency, _create_node=False)
        p_q = Param(units="number", value=q, _create_node=False)
        p_detune = Param(units="cents", value=detune, _create_node=False)
        p_gain = Param(units="decibels", value=gain, _create_node=False)

        kwargs.update(
            {
                "type": type,
                "_input": bq_filter,
                "_output": bq_filter,
                "_q": p_q,
                "_frequency": p_frequency,
                "_detune": p_detune,
                "_gain": p_gain,
            }
        )

        super().__init__(**kwargs)

    @property
    def frequency(self) -> Param:
        """Filter frequency."""
        return self._frequency

    @property
    def q(self) -> Param:
        """Filter Q factor."""
        return self._q

    @property
    def detune(self) -> Param:
        """Filter frequency detune."""
        return self._detune

    @property
    def gain(self) -> Param:
        """Filter gain (value in decibels).

        Only used for lowshelf, highshelf, and peaking filters.
        """
        return self._gain

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["frequency", "q"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._q.dispose()
            self._detune.dispose()
            self._gain.dispose()
        return self
