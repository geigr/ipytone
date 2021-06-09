from ipywidgets import widget_serialization
from traitlets import Enum, Float, Instance, TraitError, Unicode, validate

from .base import AudioNode
from .callback import add_or_send_event
from .channel import CrossFade
from .core import Gain, Param
from .signal import Signal
from .utils import parse_osc_type


class Effect(AudioNode):
    """Effect base class."""

    _model_name = Unicode("EffectModel").tag(sync=True)

    def __init__(self, wet=1, **kwargs):
        in_node = Gain(_create_node=False)
        out_node = CrossFade(fade=wet, _create_node=False)

        kwargs.update({"_input": in_node, "_output": out_node})
        super().__init__(**kwargs)

    @property
    def wet(self):
        """The wet signal.

        Controls how much of the effected will pass through to the output
        (1 = 100% effected signal, 0 = 100% dry signal)

        """
        return self.output.fade


class StereoEffect(Effect):
    """Stereo effect base class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # input source forced to stereo
        self.input.channel_count = 2
        self.input.channel_count_mode = "explicit"


class Distortion(Effect):
    """Simple distortion effect."""

    _model_name = Unicode("DistortionModel").tag(sync=True)

    distortion = Float(0.4, help="Distortion amount ([0, 1])").tag(sync=True)
    oversample = Enum(["none", "2x", "4x"], default_value="none").tag(sync=True)

    @validate("distortion")
    def _validate_distorition(self, proposal):
        if proposal["value"] < 0 or proposal["value"] > 1:
            raise TraitError("Distortion value must be in range [0, 1]")
        return proposal["value"]


class FeedbackDelay(Effect):
    """Feedback delay effect."""

    _model_name = Unicode("FeedbackDelayModel").tag(sync=True)

    _max_delay = Float().tag(sync=True)
    _feedback = Instance(Param).tag(sync=True, **widget_serialization)
    _delay_time = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, delay_time=0.25, feedback=0.125, max_delay=1, **kwargs):
        feedback_node = Param(value=feedback, units="normalRange", _create_node=False)
        delay_time_node = Param(value=delay_time, units="time", _create_node=False)

        kwargs.update(
            {"_max_delay": max_delay, "_feedback": feedback_node, "_delay_time": delay_time_node}
        )
        super().__init__(**kwargs)

    @property
    def delay_time(self) -> Param:
        """The delay time parameter."""
        return self._delay_time

    @property
    def feedback(self) -> Param:
        """The feedback parameter."""
        return self._feedback

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._delay_time.dispose()
            self._feedback.dispose()

        return self


class PingPongDelay(StereoEffect):
    """Ping-pong delay effect."""

    _model_name = Unicode("PingPongDelayModel").tag(sync=True)

    _max_delay = Float().tag(sync=True)
    _feedback = Instance(Signal).tag(sync=True, **widget_serialization)
    _delay_time = Instance(Signal).tag(sync=True, **widget_serialization)

    def __init__(self, delay_time=0.25, feedback=0.125, max_delay=1, **kwargs):
        feedback_node = Signal(value=feedback, units="normalRange", _create_node=False)
        delay_time_node = Signal(value=delay_time, units="time", _create_node=False)

        kwargs.update(
            {"_max_delay": max_delay, "_feedback": feedback_node, "_delay_time": delay_time_node}
        )
        super().__init__(**kwargs)

    @property
    def delay_time(self) -> Signal:
        """The delay time parameter."""
        return self._delay_time

    @property
    def feedback(self) -> Signal:
        """The feedback parameter."""
        return self._feedback

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._delay_time.dispose()
            self._feedback.dispose()

        return self


class Reverb(Effect):
    """Simple convolution reverb.

    The impulse response is generated from a simple noise pulse.

    """

    _model_name = Unicode("ReverbModel").tag(sync=True)

    decay = Float(1.5, help="decay time (seconds)").tag(sync=True)
    pre_delay = Float(0.01, help="pre-delay time (seconds)").tag(sync=True)

    @validate("decay")
    def _validate_decay(self, proposal):
        if proposal["value"] < 0.001:
            raise TraitError("Decay must be greater than 0.001 seconds")
        return proposal["value"]

    @validate("pre_delay")
    def _validate_pre_delay(self, proposal):
        if proposal["value"] < 0:
            raise TraitError("Pre-delay value must be positive")
        return proposal["value"]


class Tremolo(StereoEffect):
    """Tremolo effect."""

    _model_name = Unicode("TremoloModel").tag(sync=True)

    type = Unicode("sine", help="Tremolo LFO type").tag(sync=True)
    spread = Float(180, help="Tremolo stereo spread (degrees)").tag(sync=True)
    _frequency = Instance(Signal).tag(sync=True, **widget_serialization)
    _depth = Instance(Signal).tag(sync=True, **widget_serialization)

    def __init__(self, frequency=10, depth=0.5, type="sine", spread=180, **kwargs):
        freq_node = Signal(value=frequency, units="frequency", _create_node=False)
        depth_node = Signal(value=depth, units="normalRange", _create_node=False)

        kwargs.update(
            {"_frequency": freq_node, "_depth": depth_node, "type": type, "spread": spread}
        )
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        return "".join(parse_osc_type(proposal["value"]))

    @property
    def frequency(self) -> Signal:
        """Tremolo frequency."""
        return self._frequency

    @property
    def depth(self) -> Param:
        """Tremolo depth."""
        return self._depth

    def start(self, time=None):
        """Start the tremolo effect.

        If it's already started, this will stop and restart the source.
        """
        add_or_send_event("start", self, {"time": time})
        return self

    def stop(self, time=None):
        """Stop the tremolo effect."""

        add_or_send_event("stop", self, {"time": time})
        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._depth.dispose()

        return self


class Vibrato(Effect):
    """Vibrato effect."""

    _model_name = Unicode("VibratoModel").tag(sync=True)

    type = Unicode("sine", help="Vibrato LFO type").tag(sync=True)
    _max_delay = Float().tag(sync=True)
    _frequency = Instance(Signal).tag(sync=True, **widget_serialization)
    _depth = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, frequency=5, depth=0.1, type="sine", max_delay=0.005, **kwargs):
        freq_node = Signal(value=frequency, units="frequency", _create_node=False)
        depth_node = Param(value=depth, units="normalRange", _create_node=False)

        kwargs.update(
            {"_max_delay": max_delay, "_frequency": freq_node, "_depth": depth_node, "type": type}
        )
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        return "".join(parse_osc_type(proposal["value"]))

    @property
    def frequency(self) -> Signal:
        """Vibrato frequency."""
        return self._frequency

    @property
    def depth(self) -> Param:
        """Vibrato depth."""
        return self._depth

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._depth.dispose()

        return self
