from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, TraitError, Unicode, validate

from .base import AudioNode
from .core import AudioBuffer, Param, Volume
from .signal import Signal
from .transport import start_node, stop_node
from .utils import validate_osc_type


class Source(AudioNode):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

    mute = Bool(False, help="Mute source").tag(sync=True)
    state = Enum(["started", "stopped"], allow_none=False, default_value="stopped").tag(sync=True)
    _volume = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, volume=0, mute=False, **kwargs):
        out_node = Volume(volume=volume, mute=mute, _create_node=False)
        kwargs.update({"_output": out_node, "_volume": out_node.volume})
        super().__init__(**kwargs)

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._volume

    def start(self, time=""):
        """Start the audio source.

        If it's already started, this will stop and restart the source.
        """
        return start_node(self, time=time)

    def stop(self, time=""):
        """Stop the audio source."""

        return stop_node(self, time=time)


class Oscillator(Source):
    """A simple Oscillator.

    Parameters
    ----------
    type : str, optional
        Oscillator wave type, i.e., either 'sine', 'square', 'sawtooth' or 'triangle'
        (default: 'sine'). Harmonic partials may be added, e.g., 'sine2', 'square8', etc.
    frequency : int or float or str, optional
        Oscillator frequency, either in Hertz or as a note (e.g., 'A4')
        (default, 440 Hertz).
    detune : int or float, optional
        Oscillator frequency detune, in cents (default: 0).

    """

    _model_name = Unicode("OscillatorModel").tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    _frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _detune = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)

    def __init__(self, type="sine", frequency=440, detune=0, **kwargs):
        frequency = Signal(value=frequency, units="frequency", _create_node=False)
        detune = Signal(value=detune, units="cents", _create_node=False)

        kwargs.update({"type": type, "_frequency": frequency, "_detune": detune})
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        return validate_osc_type(proposal["value"])

    @property
    def frequency(self) -> Signal:
        """Oscillator frequency."""
        return self._frequency

    @property
    def detune(self) -> Signal:
        """Oscillator detune."""
        return self._detune

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._detune.dispose()

        return self


class Noise(Source):
    """A noise source."""

    _model_name = Unicode("NoiseModel").tag(sync=True)

    type = Enum(
        ["pink", "white", "brown"], allow_none=False, default_value="white", help="Noise type"
    ).tag(sync=True)
    fade_in = Float(0, help="Fade in time").tag(sync=True)
    fade_out = Float(0, help="Fade out time").tag(sync=True)


class Player(Source):
    """Audio file or buffer player with start, loop, and stop functions.

    Parameters
    ----------
    url_or_buffer : str or :class:`AudioBuffer`
        Audio file (URL) to load or an audio buffer instance.
    **kwargs
        Other options.

    """

    _model_name = Unicode("PlayerModel").tag(sync=True)

    buffer = Instance(AudioBuffer, help="The audio buffer").tag(sync=True, **widget_serialization)
    autostart = Bool(False, help="Play as soon as the audio buffer is loaded").tag(sync=True)
    loop = Bool(False, help="Play the audio buffer in loop").tag(sync=True)
    loop_start = Float(0, help="Loop start position (in seconds)").tag(sync=True)
    loop_end = Float(0, help="Loop end position (in seconds)").tag(sync=True)
    fade_in = Float(0, help="Fade in time").tag(sync=True)
    fade_out = Float(0, help="Fade out time").tag(sync=True)
    reverse = Bool(False, help="True if the buffer is reversed").tag(sync=True)
    playback_rate = Float(1, help="Playback speed (normal speed is 1)").tag(sync=True)

    def __init__(self, url_or_buffer, **kwargs):
        if isinstance(url_or_buffer, str):
            buffer = AudioBuffer(url_or_buffer)
        else:
            buffer = url_or_buffer

        kwargs.update({"buffer": buffer})
        super().__init__(**kwargs)

    def _validate_loop_bound(self, value):
        if value < 0 or self.buffer.loaded and value > self.buffer.duration:
            raise TraitError("Loop time out of audio buffer bounds")
        return value

    @validate("loop_start")
    def _validate_loop_start(self, proposal):
        return self._validate_loop_bound(proposal["value"])

    @validate("loop_end")
    def _validate_loop_end(self, proposal):
        return self._validate_loop_bound(proposal["value"])

    def set_loop_points(self, loop_start, loop_end):
        """Set the loop start and end. Will only loop if loop is set to true."""

        self.loop_start = loop_start
        self.loop_end = loop_end
        return self

    @property
    def loaded(self):
        """Returns True if the audio buffer is loaded."""
        return self.buffer.loaded

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self.buffer.dispose()

        return self
