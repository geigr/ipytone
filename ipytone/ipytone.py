#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.
import re

from ipywidgets import widget_serialization, Widget
from traitlets import Enum, Instance, Unicode, List, Float, Int, Bool, validate, TraitError, Union

from ._frontend import module_name, module_version


class ToneWidgetBase(Widget):
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


class AudioNode(ToneWidgetBase):
    """An audio node widget."""

    _model_name = Unicode("AudioNodeModel").tag(sync=True)

    name = Unicode("").tag(sync=True)

    _in_nodes = List(Instance(Widget)).tag(sync=True, **widget_serialization)
    _out_nodes = List(Instance(Widget)).tag(sync=True, **widget_serialization)

    def _normalize_destination(self, destination):
        if isinstance(destination, AudioNode):
            destination = [destination]

        if not all([isinstance(d, AudioNode) for d in destination]):
            raise ValueError("destination(s) must be AudioNode object(s)")
        if any([isinstance(d, Source) for d in destination]):
            raise ValueError("cannot connect to source audio node(s)")
        if self in destination:
            raise ValueError("cannot connect an audio node to itself")

        return list(set(self._out_nodes) | set(destination))

    def connect(self, destination):
        """Connect the output of this audio node to another ``destination`` audio node."""

        if destination not in self._out_nodes:
            self._out_nodes = self._normalize_destination(destination)
            destination._in_nodes = destination._in_nodes + [self]

        return self

    def disconnect(self, destination):
        """Disconnect the ouput of this audio node from a connected destination."""

        new_out_nodes = list(self._out_nodes)
        new_out_nodes.remove(destination)
        self._out_nodes = new_out_nodes

        new_in_nodes = list(destination._in_nodes)
        new_in_nodes.remove(self)
        destination._in_nodes = new_in_nodes

        return self

    def fan(self, *destinations):
        """Connect the output of this audio node to the ``destinations`` audio nodes in parallel."""

        self._out_nodes = self._normalize_destination(destinations)

        for node in destinations:
            node._in_nodes = node._in_nodes + [self]

        return self

    def chain(self, *nodes):
        """Connect the output of this audio node to the other audio nodes in series."""

        chain_nodes = [self] + list(nodes)

        for i in range(len(chain_nodes) - 1):
            chain_nodes[i].connect(chain_nodes[i + 1])

        return self

    def to_destination(self):
        """Convenience method to directly connect the output of this audio node
        to the master node.

        """
        self.connect(get_destination())

        return self

    @property
    def output(self):
        """Get all audio nodes connected to the output of this node."""
        return list(self._out_nodes)

    @property
    def input(self):
        """Get all audio nodes connected to the input of this node."""
        return list(self._in_nodes)

    def _repr_keys(self):
        if self.name:
            yield "name"


_UNITS = [
    "bpm",
    "cents",
    "decibels",
    "degrees",
    "frequency",
    "gain",
    "hertz",
    "number",
    "positive",
    "radians",
    "samples",
    "ticks",
    "time",
    "transport_time",
]


class Signal(AudioNode):
    """A node that defines a value that can be modulated or calculated
    at the audio sample-level accuracy.

    Signal objects support basic arithmetic operators such as ``+``, ``-``,
    ``*``, ``**``, ``abs``, ``neg`` as well as the ``>`` comparison operator.

    Like any other node, a signal can be connected to/from other nodes. When a signal
    receives an incoming signal, it's value is ignored (reset to 0) and the incoming
    signal passes through the node (``overridden=True``).

    Parameters
    ----------
    value : integer or float or str, optional
        Initial value of the signal (default: 0)
    units : str
        Signal value units, e.g., 'time', 'number', 'frequency', 'bpm', etc.
    min_value : integer or float, optional
        Signal value lower limit (default: no limit).
    max_value : integer or float, optional
        Signal value upper limit (default: no limit).
    **kwargs
        Arguments passed to :class:`AudioNode`

    """

    _model_name = Unicode("SignalModel").tag(sync=True)

    _units = Enum(_UNITS, default_value="number", allow_none=False).tag(sync=True)
    value = Union((Float(), Int(), Unicode()), help="Signal current value").tag(sync=True)
    _min_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    _max_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    overridden = Bool(
        read_only=True, help="If True, the signal value is overridden by an incoming signal"
    ).tag(sync=True)

    def __init__(self, value=0, units="number", min_value=None, max_value=None, **kwargs):
        kwargs.update(
            {"value": value, "_units": units, "_min_value": min_value, "_max_value": max_value}
        )
        super().__init__(**kwargs)

    @property
    def units(self):
        """Signal value units."""
        return self._units

    @property
    def min_value(self):
        """Signal value lower limit."""
        return self._min_value

    @property
    def max_value(self):
        """Signal value upper limit."""
        return self._max_value

    def __mul__(self, other):
        if not isinstance(other, Signal):
            other = Signal(value=other)

        mult = Multiply(other)
        self.connect(mult)

        return mult


class Multiply(Signal):

    _model_name = Unicode("MultiplyModel").tag(sync=True)

    _factor = Instance(Signal, help="Signal multiply factor", allow_none=True).tag(
        sync=True, **widget_serialization
    )

    def __init__(self, factor, **kwargs):
        if not isinstance(factor, Signal):
            factor = Signal(value=factor, **kwargs)

        kwargs.update({"_factor": factor})
        super().__init__(**kwargs)

    @property
    def factor(self):
        return self._factor


class Source(AudioNode):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

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


class Destination(AudioNode):
    """Audio master node."""

    _singleton = None

    _model_name = Unicode("DestinationModel").tag(sync=True)

    name = Unicode("main output").tag(sync=True)

    mute = Bool(False).tag(sync=True)
    volume = Float(-16).tag(sync=True)

    def __new__(cls):
        if Destination._singleton is None:
            Destination._singleton = super(Destination, cls).__new__(cls)
        return Destination._singleton


_DESTINATION = Destination()


def get_destination():
    """Returns ipytone's audio master node."""
    return _DESTINATION


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
    _frequency = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _detune = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)

    def __init__(self, type="sine", frequency=440, detune=0, **kwargs):

        if not isinstance(frequency, Signal):
            frequency = Signal(value=frequency, units="frequency")

        if not isinstance(detune, Signal):
            detune = Signal(value=detune, units="cents")

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


class Noise(Source):
    """A simple Oscillator."""

    _model_name = Unicode("NoiseModel").tag(sync=True)

    type = Enum(
        ["pink", "white", "brown"], allow_none=False, default_value="white", help="Noise type"
    ).tag(sync=True)
    fade_in = Float(0, help="Fade in time").tag(sync=True)
    fade_out = Float(0, help="Fade out time").tag(sync=True)
