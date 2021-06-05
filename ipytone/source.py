from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, TraitError, Unicode, validate

from .base import AudioNode
from .core import AudioBuffer, AudioBuffers, Param, Volume
from .signal import Signal
from .transport import add_or_send_event
from .utils import validate_osc_type


class Source(AudioNode):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

    mute = Bool(False, help="Mute source").tag(sync=True)
    _volume = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, volume=0, mute=False, **kwargs):
        out_node = Volume(volume=volume, mute=mute, _create_node=False)
        kwargs.update({"_output": out_node, "_volume": out_node.volume})
        super().__init__(**kwargs)

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._volume

    def start(self, time=None, offset=None, duration=None):
        """Start the audio source.

        If it's already started, this will stop and restart the source.
        """
        add_or_send_event("start", self, {"time": time, "offset": offset, "duration": duration})
        return self

    def stop(self, time=None):
        """Stop the audio source."""
        add_or_send_event("stop", self, {"time": time})
        return self


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


class Players(AudioNode):
    """Multiple players."""

    _model_name = Unicode("PlayersModel").tag(sync=True)

    _buffers = Instance(AudioBuffers).tag(sync=True, **widget_serialization)
    mute = Bool(False, help="Mute source").tag(sync=True)
    _volume = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, urls, base_url="", volume=0, mute=False, fade_in=0, fade_out=0, **kwargs):
        buffers = AudioBuffers(urls, base_url=base_url, _create_node=False)
        out_node = Volume(volume=volume, mute=mute, _create_node=False)

        kwargs.update({"_buffers": buffers, "_output": out_node, "_volume": out_node.volume})
        super().__init__(**kwargs)

        self._fade_in = fade_in
        self._fade_out = fade_out
        self._players = {}

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._volume

    @property
    def loaded(self):
        """Returns True if all audio buffers are loaded."""
        return self._buffers.loaded

    def get_player(self, name):
        """Get the :class:`Player` object that corresponds to ``name``."""
        if name in self._players:
            return self._players[name]
        else:
            player = Player(
                self._buffers.buffers[name], fade_in=self.fade_in, fade_out=self.fade_out
            )
            player.connect(self.output)
            self._players[name] = player
            return player

    @property
    def fade_in(self):
        return self._fade_in

    @fade_in.setter
    def fade_in(self, value):
        for p in self._players.values():
            p.fade_in = value
        self._fade_in = value

    @property
    def fade_out(self):
        return self._fade_out

    @fade_out.setter
    def fade_out(self, value):
        for p in self._players.values():
            p.fade_out = value
        self._fade_out = value

    @property
    def state(self):
        """Returns 'started' if any of the players are playing. Otherwise returns 'stopped'."""
        return (
            "started" if any([p.state == "started" for p in self._players.values()]) else "stopped"
        )

    def add(self, name, url):
        """Add a player.

        Parameters
        ----------
        key : str
            Buffer name.
        url : str or :class:`AudioBuffer`.
            Buffer file URL (str) or :class:`AudioBuffer` object.

        """
        if name in self._buffers.buffers:
            raise ValueError(f"A buffer with name '{name}' already exists on this object.")

        self._buffers.add(name, url)

        return self

    def stop_all(self, time=""):
        """Stop all of the players at the given time."""
        for p in self._players.values():
            p.stop()

        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            for p in self._players.values():
                p.dispose()
            self._buffers.dispose()

        return self
