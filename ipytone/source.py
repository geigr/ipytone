import re

from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, TraitError, Unicode, validate, Union

from .base import AudioNode
from .signal import Signal


class Source(AudioNode):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

    number_of_inputs = Int(
        read_only=True,
        default_value=0,
        help="An audio source node has no input"
    ).tag(sync=True)

    mute = Bool(False, help="Mute source").tag(sync=True)
    state = Enum(["started", "stopped"], allow_none=False, default_value="stopped").tag(sync=True)
    volume = Float(-16, help="Source gain").tag(sync=True)

    def start(self):
        """Start the audio source.

        If it's already started, this will stop and restart the source.
        """
        self.state = "started"

        return self

    def stop(self):
        """Stop the audio source."""

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
    frequency : int or str or :class:`Signal`, optional
        Oscillator frequency, either in Hertz, as a note (e.g., 'A4') or as a Signal object
        (default, 440 Hertz).
    detune : int or :class:`Signal`, optional
        Oscillator frequency detune, in cents (or as a Signal object). Default: 0.

    """

    _model_name = Unicode("OscillatorModel").tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    _init_frequency_value = Union([Int(), Float(), Unicode()]).tag(sync=True)
    _init_detune_value = Float().tag(sync=True)
    frequency = Instance(Signal, read_only=True, allow_none=True).tag(sync=True, **widget_serialization);
    detune = Instance(Signal, read_only=True, allow_none=True).tag(sync=True, **widget_serialization);

    def __init__(self, type="sine", frequency=440, detune=0, **kwargs):

        kwargs.update({"type": type, "_init_frequency_value": frequency, "_init_detune_value": detune})
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        wave = proposal["value"]
        wave_re = r"(sine|square|sawtooth|triangle)[\d]*"

        if re.fullmatch(wave_re, wave) is None:
            raise TraitError(f"Invalid oscillator type: {wave}")

        return proposal["value"]


class Noise(Source):
    """A noise source."""

    _model_name = Unicode("NoiseModel").tag(sync=True)

    type = Enum(
        ["pink", "white", "brown"], allow_none=False, default_value="white", help="Noise type"
    ).tag(sync=True)
    fade_in = Float(0, help="Fade in time").tag(sync=True)
    fade_out = Float(0, help="Fade out time").tag(sync=True)
