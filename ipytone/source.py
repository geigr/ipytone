from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, List, TraitError, Unicode, validate
from traittypes import Array

from .base import AudioNode
from .callback import add_or_send_event
from .core import AudioBuffer, AudioBuffers, Param, Volume
from .serialization import data_array_serialization
from .signal import Signal
from .utils import parse_osc_type


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
    partials : list, optional
        Relative amplitude of each of the harmonics of the oscillator. The 1st value
        is the fundamental frequency, the 2nd value is an octave up, etc.
    partial_count : int, optional
        Number of harmonics which are used to generate the waveform.

    """

    _model_name = Unicode("OscillatorModel").tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    _partials = List(trait=Float()).tag(sync=True)

    _frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _detune = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    phase = Float(0.0, help="Starting position within the oscillator's cycle").tag(sync=True)

    array = Array(
        allow_none=True, default_value=None, read_only=True, help="Oscillator waveform"
    ).tag(sync=True, **data_array_serialization)
    array_length = Int(1024, help="Oscillator waveform resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="if True, synchronize waveform").tag(sync=True)

    def __init__(
        self, type="sine", frequency=440, detune=0, partials=None, partial_count=None, **kwargs
    ):
        if type == "custom":
            if partials is None:
                raise ValueError("Partials values must be given for 'custom' oscillator type")

        else:
            partials = []
            _, partial_count_ = parse_osc_type(type)

        if partial_count is not None:
            if type == "custom":
                partials = partials[0:partial_count]
            else:
                if partial_count_:
                    raise ValueError(f"Partial count already set in oscillator type {type!r}")
                if partial_count == 0:
                    partial_count = ""
                type += str(partial_count)

        frequency = Signal(value=frequency, units="frequency", _create_node=False)
        detune = Signal(value=detune, units="cents", _create_node=False)

        kwargs.update(
            {"type": type, "_frequency": frequency, "_detune": detune, "_partials": partials}
        )
        super().__init__(**kwargs)

    @property
    def frequency(self) -> Signal:
        """Oscillator frequency."""
        return self._frequency

    @property
    def detune(self) -> Signal:
        """Oscillator detune."""
        return self._detune

    @validate("type")
    def _validate_type(self, proposal):
        value = proposal["value"]

        if value == "custom":
            if not len(self.partials):
                raise ValueError("Cannot set 'custom' type, use the ``partial`` property instead")
            return value
        else:
            base_type, partial_count = parse_osc_type(value)
            return base_type + partial_count

    @property
    def base_type(self):
        """Oscillator wave type without partials."""
        if self.type == "custom":
            return self.type
        else:
            base_type, _ = parse_osc_type(self.type)
            return base_type

    @base_type.setter
    def base_type(self, value):
        _, partial_count = parse_osc_type(self.type)
        self.type = value + partial_count

    @property
    def partials(self):
        """Relative amplitude of each of the harmonics of the oscillator.

        The 1st value is the fundamental frequency, the 2nd value is an octave
        up, etc.

        """
        return self._partials

    @partials.setter
    def partials(self, value):
        if value is None:
            value = []

        self._partials = value

        if len(value):
            self.type = "custom"

    @property
    def partial_count(self):
        """Number of harmonics which are used to generate the waveform.

        If the value equals zero, the maximum number of partials are used.

        """
        if self.type == "custom":
            return len(self.partials)
        else:
            _, partial_count = parse_osc_type(self.type)
            return partial_count

    @partial_count.setter
    def partial_count(self, value):
        if self.type == "custom":
            self._partials = self._partials[0:value]
        else:
            if value == 0:
                value = ""
            base_type, _ = parse_osc_type(self.type)
            self.type = base_type + str(value)

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
