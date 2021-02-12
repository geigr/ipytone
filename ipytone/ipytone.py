#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.
import re

from ipywidgets import widget_serialization, Widget
from traitlets import Enum, Instance, Unicode, List, Float, Int, Bool, validate, TraitError

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


class Source(AudioNode):
    """Audio source node."""

    _model_name = Unicode("SourceModel").tag(sync=True)

    mute = Bool(False).tag(sync=True)
    state = Enum(["started", "stopped"], allow_none=False, default_value="stopped").tag(sync=True)
    volume = Float(-16).tag(sync=True)

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
    """A simple Oscillator."""

    _model_name = Unicode("OscillatorModel").tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    frequency = Float(440, help="Oscillator frequency").tag(sync=True)
    detune = Int(0, help="Oscillator frequency detune").tag(sync=True)
    volume = Float(-16, help="Oscillator gain").tag(sync=True)
    started = Bool(False, help="Start/stop oscillator").tag(sync=True)

    @validate("type")
    def _validate_oscillator_type(self, proposal):
        wave = proposal["value"]
        wave_re = r"(sine|square|sawtooth|triangle)[\d]*"

        if re.fullmatch(wave_re, wave) is None:
            raise TraitError(f"Invalid oscillator type: {wave}")

        return proposal["value"]
