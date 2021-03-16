import re

from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, TraitError, Unicode, validate

from .base import AudioNode
from .core import Param, Volume
from .signal import Signal
from .transport import transport


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
        if transport._is_scheduling:
            transport._audio_nodes = transport._audio_nodes + [self]
            transport._methods = transport._methods + ["start"]
            transport._packed_args = transport._packed_args + [time + " *** "]
        else:
            self.state = "started"

        return self

    def stop(self, time=""):
        """Stop the audio source."""

        if transport._is_scheduling:
            transport._audio_nodes = transport._audio_nodes + [self]
            transport._methods = transport._methods + ["stop"]
            transport._packed_args = transport._packed_args + [time + " *** "]
        else:
            if self.state == "started":
                self.state = "stopped"

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
        wave = proposal["value"]
        wave_re = r"(sine|square|sawtooth|triangle)[\d]*"

        if re.fullmatch(wave_re, wave) is None:
            raise TraitError(f"Invalid oscillator type: {wave}")

        return proposal["value"]

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
