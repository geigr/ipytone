from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, Unicode, Union
from traittypes import Array

from .base import AudioNode, PyAudioNode
from .core import Gain, NativeAudioNode, Param
from .serialization import data_array_serialization
from .signal import Signal

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

    array = Array(
        allow_none=True,
        default_value=None,
        read_only=True,
        help="frequency response curve data (20hz-20kh)",
    ).tag(sync=True, **data_array_serialization)
    array_length = Int(128, help="Curve data resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="If True, synchronize curve data").tag(sync=True)

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
        for key in ["type", "frequency", "q"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._q.dispose()
            self._detune.dispose()
            self._gain.dispose()
        return self


FILTER_ROLLOFF = [-12, -24, -48, -96]


class Filter(AudioNode):
    """Simple filter with rolloff (slope) parameter."""

    _model_name = Unicode("FilterModel").tag(sync=True)

    type = Enum(
        BIQUAD_FILTER_TYPES, allow_none=False, default_value="lowpass", help="filter type"
    ).tag(sync=True)
    _frequency = Instance(Signal).tag(sync=True, **widget_serialization)
    _q = Instance(Signal).tag(sync=True, **widget_serialization)
    _detune = Instance(Signal).tag(sync=True, **widget_serialization)
    _gain = Instance(Signal).tag(sync=True, **widget_serialization)
    rolloff = Enum(
        FILTER_ROLLOFF, allow_none=False, default_value=-12, help="filter rolloff (slope)"
    ).tag(sync=True)

    array = Array(
        allow_none=True,
        default_value=None,
        read_only=True,
        help="frequency response curve data (20hz-20kh)",
    ).tag(sync=True, **data_array_serialization)
    array_length = Int(128, help="Curve data resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="If True, synchronize curve data").tag(sync=True)

    def __init__(self, type="lowpass", frequency=350, q=1, detune=0, gain=0, rolloff=-12, **kwargs):
        in_gain = Gain(_create_node=False)
        out_gain = Gain(_create_node=False)

        p_frequency = Signal(units="frequency", value=frequency, _create_node=False)
        p_q = Signal(units="positive", value=q, _create_node=False)
        p_detune = Signal(units="cents", value=detune, _create_node=False)
        p_gain = Signal(units="decibels", value=gain, _create_node=False)

        kwargs.update(
            {
                "type": type,
                "_input": in_gain,
                "_output": out_gain,
                "_q": p_q,
                "_frequency": p_frequency,
                "_detune": p_detune,
                "_gain": p_gain,
                "rolloff": rolloff,
            }
        )

        super().__init__(**kwargs)

    @property
    def frequency(self) -> Signal:
        """Filter frequency."""
        return self._frequency

    @property
    def q(self) -> Signal:
        """Filter Q factor."""
        return self._q

    @property
    def detune(self) -> Signal:
        """Filter frequency detune."""
        return self._detune

    @property
    def gain(self) -> Signal:
        """Filter gain (value in decibels).

        Only used for lowshelf, highshelf, and peaking filters.
        """
        return self._gain

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["type", "frequency", "q"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._q.dispose()
            self._detune.dispose()
            self._gain.dispose()
        return self


ONE_POLE_FILTER_TYPES = ["lowpass", "highpass"]


class OnePoleFilter(AudioNode):
    """A one pole filter with 6db-per-octave rolloff.

    Either 'highpass' or 'lowpass'. Note that changing the type or frequency may
    result in a discontinuity which * can sound like a click or pop.

    """

    _model_name = Unicode("OnePoleFilterModel").tag(sync=True)

    type = Enum(
        ONE_POLE_FILTER_TYPES, allow_none=False, default_value="lowpass", help="filter type"
    ).tag(sync=True)
    frequency = Union((Float(), Unicode()), default_value=880, help="filter frequency").tag(
        sync=True
    )

    def __init__(self, **kwargs):
        in_gain = Gain(_create_node=False)
        out_gain = Gain(_create_node=False)

        kwargs.update({"_input": in_gain, "_output": out_gain})
        super().__init__(**kwargs)

    array = Array(
        allow_none=True,
        default_value=None,
        read_only=True,
        help="frequency response curve data (20hz-20kh)",
    ).tag(sync=True, **data_array_serialization)
    array_length = Int(128, help="Curve data resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="If True, synchronize curve data").tag(sync=True)

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["type", "frequency"]:
            yield key


class FeedbackCombFilter(AudioNode):
    """Feedback comb filter."""

    _model_name = Unicode("FeedbackCombFilterModel").tag(sync=True)

    _delay_time = Instance(Param).tag(sync=True, **widget_serialization)
    _resonance = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, delay_time=0.1, resonance=0.5, **kwargs):
        in_gain = Gain(_create_node=False)
        out_gain = Gain(_create_node=False)

        p_delay_time = Param(units="time", value=delay_time, _create_node=False)
        p_resonance = Param(units="normalRange", value=resonance, _create_node=False)

        kwargs.update(
            {
                "_input": in_gain,
                "_output": out_gain,
                "_delay_time": p_delay_time,
                "_resonance": p_resonance,
            }
        )
        super().__init__(**kwargs)

    @property
    def delay_time(self) -> Param:
        """Amount of delay of the comb filter."""
        return self._delay_time

    @property
    def resonance(self) -> Param:
        """Amount of feedback of the delayed signal."""
        return self._resonance

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["delay_time", "resonance"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._delay_time.dispose()
            self._resonance.dispose()
        return self


class LowpassCombFilter(PyAudioNode):
    """Feedback comb + lowpass filter."""

    def __init__(self, delay_time=0.1, resonance=0.5, dampening=3000, **kwargs):
        self._fc_filter = FeedbackCombFilter(delay_time=delay_time, resonance=resonance)
        self._lowpass_filter = OnePoleFilter(type="lowpass", frequency=dampening)
        self._lowpass_filter.connect(self._fc_filter)
        super().__init__(self._lowpass_filter, self._fc_filter, **kwargs)

    @property
    def delay_time(self) -> Param:
        """Amount of delay of the comb filter."""
        return self._fc_filter.delay_time

    @property
    def resonance(self) -> Param:
        """Amount of feedback of the delayed signal."""
        return self._fc_filter.resonance

    @property
    def dampening(self):
        """Dampening control of the feedback."""
        return self._lowpass_filter.frequency

    @dampening.setter
    def dampening(self, value):
        self._lowpass_filter.frequency = value

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["delay_time", "resonance", "dampening"]:
            yield key


# class PhaseShiftAllpass(AudioNode):
#     """Optimized implementation of Hilbert transform using two all-pass IIR
#     filters whose phase difference is approximately 90 degrees.

#     """

#     _model_name = Unicode("PhaseShiftAllpass").tag(sync=True)

#     _offset90 = Instance(Gain).tag(sync=True, **widget_serialization)

#     def __init__(self, **kwargs):
#         in_gain = Gain(_create_node=False)
#         out_gain = Gain(_create_node=False)
#         offset90 = Gain(_create_node=False)
#         kwargs.update({"_input": in_gain, "_output": out_gain, "_offset_90": offset90})
#         super().__init__(**kwargs)

#     @property
#     def offset90(self) -> Gain:
#         """Returns the PhaseShifted allpass output."""
#         return self._offset90


class EQ3(PyAudioNode):
    """Three-band equalizer."""

    def __init__(self, low=0, mid=0, high=0, low_frequency=400, high_frequency=2500, **kwargs):
        from .channel import MultibandSplit

        in_msplit = MultibandSplit(low_frequency=low_frequency, high_frequency=high_frequency)
        out_gain = Gain()

        self._low_gain = Gain(units="decibels", gain=low)
        self._mid_gain = Gain(units="decibels", gain=mid)
        self._high_gain = Gain(units="decibels", gain=high)

        super().__init__(in_msplit, out_gain, **kwargs)

        # connections
        with self._graph.hold_state():
            in_msplit.low.chain(self._low_gain, out_gain)
            in_msplit.mid.chain(self._mid_gain, out_gain)
            in_msplit.high.chain(self._high_gain, out_gain)

    @property
    def low(self) -> Param:
        """Low band gain (decibels)."""
        return self._low_gain.gain

    @property
    def mid(self) -> Param:
        """Mid band gain (decibels)."""
        return self._mid_gain.gain

    @property
    def high(self) -> Param:
        """High band gain (decibels)."""
        return self._high_gain.gain

    @property
    def low_frequency(self) -> Signal:
        """Low/mid cross-over frequency."""
        return self.input.low_frequency

    @property
    def high_frequency(self) -> Signal:
        """Mid/high cross-over frequency."""
        return self.input.high_frequency

    @property
    def q(self) -> Signal:
        """Q factor of all filters."""
        return self.input.q

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._low_gain.dispose()
            self._mid_gain.dispose()
            self._high_gain.dispose()
        return self
