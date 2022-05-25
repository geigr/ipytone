import re

from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, List, TraitError, Unicode, validate
from traittypes import Array

from .base import AudioNode
from .callback import add_or_send_event
from .core import AudioBuffer, AudioBuffers, Param, Volume
from .observe import ScheduleObserveMixin
from .serialization import data_array_serialization
from .signal import Multiply, Scale, Signal
from .utils import OSC_TYPES, parse_osc_type


class Source(AudioNode, ScheduleObserveMixin):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

    mute = Bool(False, help="Mute source").tag(sync=True)
    _volume = Instance(Param).tag(sync=True, **widget_serialization)

    _observable_traits = List(["state"])
    _default_observed_trait = "state"

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

    def sync(self):
        """Sync the source to the transport.

        All subsequent calls to `start` and `stop` are synced to the
        transport time instead of the audio context time.

        """
        add_or_send_event("sync", self, {})
        return self

    def unsync(self):
        """Unsync the source to the transport."""
        add_or_send_event("unsync", self, {})
        return self


class LFO(AudioNode):
    """LFO (Low Frequency Oscillator).

    A LFO produces an output signal which can be attached to an audio parameter
    or signal in order to modulate that parameter with an oscillator.

    It may be synced to the transport to start/stop and change when the tempo
    changes.

    """

    _model_name = Unicode("LFOModel").tag(sync=True)

    _frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _amplitude = Instance(Param, allow_none=True).tag(sync=True, **widget_serialization)

    _valid_types = OSC_TYPES
    type = Unicode("sine", help="LFO oscillator type").tag(sync=True)
    phase = Float(0.0, help="Starting position of the LFO's cycle").tag(sync=True)
    partials = List(trait=Float(), help="See Oscillator.partials").tag(sync=True)

    units = Unicode("number", help="LFO output units").tag(sync=True)
    convert = Bool(True, help="If True, convert input value in units").tag(sync=True)

    def __init__(self, frequency="4n", amplitude=1, min=0, max=1, **kwargs):
        amplitude = Param(value=amplitude, units="normalRange", _create_node=False)
        frequency = Signal(value=frequency, units="frequency", _create_node=False)

        out_node = Scale(min_out=min, max_out=max, _create_node=False)

        kwargs.update({"_output": out_node, "_frequency": frequency, "_amplitude": amplitude})
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        value = proposal["value"]

        if value == "custom":
            if not len(self._partials):
                raise TraitError("Cannot set 'custom' type, use the ``partials`` attribute instead")
            return value
        else:
            base_type, partial_count = parse_osc_type(value, types=self._valid_types)
            return base_type + partial_count

    @property
    def frequency(self) -> Signal:
        """LFO frequency."""
        return self._frequency

    @property
    def amplitude(self) -> Param:
        """LFO amplitude."""
        return self._amplitude

    @property
    def min_out(self):
        return self.output.min_out

    @min_out.setter
    def min_out(self, value):
        self.output.min_out = value

    @property
    def max_out(self):
        print(self.output.max_out)
        return self.output.max_out

    @max_out.setter
    def max_out(self, value):
        self.output.max_out = value

    def start(self, time=None):
        """Start the LFO."""
        add_or_send_event("start", self, {"time": time})
        return self

    def stop(self, time=None):
        """Stop the LFO."""
        add_or_send_event("stop", self, {"time": time})
        return self

    def sync(self):
        """Sync the LFO playback state and frequency to the transport."""
        add_or_send_event("sync", self, {})
        return self

    def unsync(self):
        """Unsync the LFO from the transport."""
        add_or_send_event("unsync", self, {})
        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._amplitude.dispose()

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

    _valid_types = OSC_TYPES
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
            _, partial_count_ = parse_osc_type(type, types=self._valid_types)

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

    def _parse_osc_type(self, value, validate=False):
        if value == "custom":
            if validate and not len(self._partials):
                raise TraitError("Cannot set 'custom' type, use the ``partial`` property instead")
            return value, ""
        else:
            base_type, partial_count = parse_osc_type(value, types=self._valid_types)
            return base_type, partial_count

    @validate("type")
    def _validate_type(self, proposal):
        value = proposal["value"]

        return "".join(self._parse_osc_type(value, validate=True))

    @property
    def base_type(self):
        """Oscillator wave type without partials."""
        if self.type == "custom":
            return self.type
        else:
            base_type, _ = self._parse_osc_type(self.type)
            return base_type

    @base_type.setter
    def base_type(self, value):
        _, partial_count = self._parse_osc_type(self.type)
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
            _, partial_count = self._parse_osc_type(self.type)
            if not len(partial_count):
                return 0
            else:
                return int(partial_count)

    @partial_count.setter
    def partial_count(self, value):
        if self.type == "custom":
            self._partials = self._partials[0:value]
        else:
            if value == 0:
                value = ""
            base_type, _ = self._parse_osc_type(self.type)
            self.type = base_type + str(value)

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._detune.dispose()

        return self


class AMOscillator(Oscillator):
    """An amplitude modulated oscillator.

    It is implemented with two oscillators, one which modulates
    the other's amplitude through a gain node.

    Parameters
    ----------
    harmonicity : float, optional
       Frequency ratio between the carrier and the modulator oscillators. A
       value of 1 (default) gives both oscillators the same frequency. A value of 2
       means a change of an octave. Must be > 0.

    """

    _model_name = Unicode("AMOscillatorModel").tag(sync=True)

    _harmonicity = Instance(Multiply, allow_none=True).tag(sync=True, **widget_serialization)
    modulation_type = Unicode("square", help="The type of the modulator oscillator").tag(sync=True)

    def __init__(self, harmonicity=1, **kwargs):
        harmonicity = Multiply(value=harmonicity, _create_node=False)
        super().__init__(_harmonicity=harmonicity, **kwargs)

    @validate("modulation_type")
    def _validate_modulation_type(self, proposal):
        value = proposal["value"]
        base_type, partial_count = parse_osc_type(value, types=self._valid_types)
        return base_type + partial_count

    @property
    def harmonicity(self) -> Multiply:
        """Frequency ratio between the carrier and the modulator oscillators."""
        return self._harmonicity

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._harmonicity.dispose()

        return self


class FMOscillator(Oscillator):
    """Frequency modulation synthesis

    Parameters
    ----------
    harmonicity : float, optional
       Frequency ratio between the carrier and the modulator oscillators. A
       value of 1 (default) gives both oscillators the same frequency. A value of 2
       means a change of an octave. Must be > 0.
    modulation_index : float, optional
       Depth (amount) of the modulation (default: 2). Must be > 0.

    """

    _model_name = Unicode("FMOscillatorModel").tag(sync=True)

    _harmonicity = Instance(Multiply, allow_none=True).tag(sync=True, **widget_serialization)
    _modulation_index = Instance(Multiply, allow_none=True).tag(sync=True, **widget_serialization)
    modulation_type = Unicode("square", help="The type of the modulator oscillator").tag(sync=True)

    def __init__(self, harmonicity=1, modulation_index=2, **kwargs):
        harmonicity = Multiply(value=harmonicity, _create_node=False)
        modulation_index = Multiply(value=modulation_index, _create_node=False)
        super().__init__(_harmonicity=harmonicity, _modulation_index=modulation_index, **kwargs)

    @validate("modulation_type")
    def _validate_modulation_type(self, proposal):
        value = proposal["value"]
        base_type, partial_count = parse_osc_type(value, types=self._valid_types)
        return base_type + partial_count

    @property
    def harmonicity(self) -> Multiply:
        """Frequency ratio between the carrier and the modulator oscillators."""
        return self._harmonicity

    @property
    def modulation_index(self) -> Multiply:
        """Depth (amount) of the modulation."""
        return self._modulation_index

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._harmonicity.dispose()
            self._modulation_index.dispose()

        return self


class FatOscillator(Oscillator):
    """A 'fat" oscillator is made of multiple oscillators with detune spread between them."""

    _model_name = Unicode("FatOscillatorModel").tag(sync=True)

    spread = Int(20, help="Control the detune amount between the oscillators").tag(sync=True)
    count = Int(3, help="Number of oscillators").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(type="sawtooth", **kwargs)


class PulseOscillator(Oscillator):
    """A pulse oscillator.

    Parameters
    ----------
    width : float, optional
        Pulse width. A value of zero corresponds to a square wave.

    """

    _model_name = Unicode("PulseOscillatorModel").tag(sync=True)

    _valid_types = ("pulse",)
    _width = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)

    def __init__(self, width=0.2, **kwargs):
        width = Signal(value=width, units="audioRange", _create_node=False)
        super().__init__(_width=width, type="pulse", **kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        if proposal["value"] != "pulse":
            raise TraitError("PulseOscillator only supports the 'pulse' oscillator type")
        return "pulse"

    @property
    def partial_count(self):
        return 0

    @property
    def partials(self):
        return []

    @property
    def width(self) -> Signal:
        """The width of the pulse."""
        return self._width

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._width.dispose()

        return self


class PWMOscillator(Oscillator):
    """A pulse oscillator for which the pulse width is modulated at a given frequency.

    Parameters
    ----------
    modulation_frequency : float, optional
        Modulation frequency of the pulse width.

    """

    _model_name = Unicode("PWMOscillatorModel").tag(sync=True)

    _valid_types = ("pwm",)
    _modulation_frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)

    def __init__(self, modulation_frequency=0.4, **kwargs):
        modulation_frequency = Signal(
            value=modulation_frequency, units="frequency", _create_node=False
        )
        super().__init__(_modulation_frequency=modulation_frequency, type="pwm", **kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        if proposal["value"] != "pwm":
            raise TraitError("PWMOscillator only supports the 'pwm' oscillator type")
        return "pwm"

    @property
    def partial_count(self):
        return 0

    @property
    def partials(self):
        return []

    @property
    def modulation_frequency(self) -> Signal:
        """Modulation frequency of the pulse width."""
        return self._modulation_frequency

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._modulation_frequency.dispose()

        return self


class OmniOscillator(Oscillator):
    """Full options oscillator.

    See other oscillators for documentation.
    """

    _model_name = Unicode("OmniOscillatorModel").tag(sync=True)

    _valid_types = OSC_TYPES + ["pulse", "pwm"]
    _modulation_frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _width = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _harmonicity = Instance(Multiply, allow_none=True).tag(sync=True, **widget_serialization)
    _modulation_index = Instance(Multiply, allow_none=True).tag(sync=True, **widget_serialization)
    modulation_type = Unicode("square", help="The type of the modulator oscillator").tag(sync=True)

    spread = Int(20, help="Control the detune amount between the oscillators").tag(sync=True)
    count = Int(3, help="Number of oscillators").tag(sync=True)

    def __init__(
        self,
        type="sine",
        harmonicity=1,
        modulation_index=2,
        width=0.2,
        modulation_frequency=0.4,
        **kwargs,
    ):
        harmonicity = Multiply(value=harmonicity, _create_node=False)
        modulation_index = Multiply(value=modulation_index, _create_node=False)
        width = Signal(value=width, units="audioRange", _create_node=False)
        modulation_frequency = Signal(
            value=modulation_frequency, units="frequency", _create_node=False
        )
        super().__init__(
            type="sine",
            _harmonicity=harmonicity,
            _modulation_index=modulation_index,
            _width=width,
            _modulation_frequency=modulation_frequency,
            **kwargs,
        )

        # pick up the right validator (this class, not the base class)
        self.type = type

    def _parse_osc_type(self, value, validate=False):
        match = re.match(r"^(?P<prefix>am|fm|fat){0,1}(?P<type>.*)$", value)

        if match is None:
            raise TraitError(f"Invalid oscillator type {value!r}")

        prefix, type_partial = match.groups()
        if prefix is None:
            prefix = ""

        base_type, partial_count = super()._parse_osc_type(type_partial, validate=validate)

        return prefix, base_type, partial_count

    def _is_pulse(self, value=None):
        if value is None:
            value = self.type
        return value in ["pulse", "pwm"]

    @validate("type")
    def _validate_type(self, proposal):
        value = proposal["value"]

        if self._is_pulse(value):
            return value
        else:
            prefix, base_type, partial_count = self._parse_osc_type(value, validate=True)
            return "".join([prefix, base_type, partial_count])

    @property
    def source_type(self):
        if self._is_pulse():
            return self.type

        prefix, _, _ = self._parse_osc_type(self.type)
        if not prefix:
            return "oscillator"
        else:
            return prefix

    @source_type.setter
    def source_type(self, value):
        if self._is_pulse(value):
            self.type = value
        else:
            _, base_type, partial_count = self._parse_osc_type(self.type)
            if self._is_pulse(base_type):
                base_type = "sine"
            if value == "oscillator":
                self.type = base_type + partial_count
            else:
                self.type = value + base_type + partial_count

    @property
    def base_type(self):
        if self._is_pulse():
            return self.type
        else:
            _, base_type, _ = self._parse_osc_type(self.type)
            return base_type

    @base_type.setter
    def base_type(self, value):
        if self._is_pulse(value):
            raise ValueError("Use ``source_type`` instead to set pulse oscillator")

        prefix, _, partial_count = self._parse_osc_type(self.type)
        self.type = prefix + value + partial_count

    @validate("modulation_type")
    def _validate_modulation_type(self, proposal):
        value = proposal["value"]
        base_type, partial_count = parse_osc_type(value, types=self._valid_types)
        return base_type + partial_count

    @property
    def harmonicity(self):
        """Frequency ratio between the carrier and the modulator oscillators."""
        if self.type[0:2] in ["am", "fm"]:
            return self._harmonicity
        else:
            return None

    @property
    def modulation_index(self):
        """Depth (amount) of the modulation."""
        if self.type.startswith("fm"):
            return self._modulation_index
        else:
            return None

    @property
    def modulation_frequency(self):
        """Modulation frequency of the pulse width."""
        if self.type == "pwm":
            return self._modulation_frequency
        else:
            return None

    @property
    def width(self):
        """The width of the pulse."""
        if self.type == "pulse":
            return self._width
        else:
            return None

    @property
    def partial_count(self):
        if self._is_pulse():
            return 0

        _, base_type, partial_count = self._parse_osc_type(self.type)

        if base_type == "custom":
            return len(self._partials)
        else:
            if not len(partial_count):
                return 0
            else:
                return int(partial_count)

    @partial_count.setter
    def partial_count(self, value):
        if self._is_pulse():
            raise NotImplementedError("Cannot set partial count for pulse oscillators")

        prefix, base_type, _ = self._parse_osc_type(self.type)

        if base_type == "custom":
            self._partials = self._partials[0:value]
        else:
            if value == 0:
                value = ""
            self.type = prefix + base_type + str(value)

    @property
    def partials(self):
        if self._is_pulse():
            return []
        else:
            return self._partials

    @partials.setter
    def partials(self, value):
        if self._is_pulse():
            raise NotImplementedError("Cannot set partials for pulse oscillators")

        if value is None:
            value = []

        self._partials = value

        if len(value):
            prefix, _, _ = self._parse_osc_type(self.type)
            self.type = prefix + "custom"

    def dispose(self):
        src_type = self.source_type

        with self._graph.hold_state():
            super().dispose()
            if src_type in ["am", "fm"]:
                self._harmonicity.dispose()
                if src_type == "fm":
                    self._modulation_index.dispose()
            elif src_type == "pulse":
                self._width.dispose()
            elif src_type == "pwm":
                self._modulation_frequency.dispose()

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
