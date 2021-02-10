#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import widget_serialization, Widget
from traitlets import Instance, Unicode, List, Float, Int, Bool, validate, TraitError

from ._frontend import module_name, module_version


class _ToneWidgetBase(Widget):
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


class AudioNode(_ToneWidgetBase):
    """An audio node widget."""

    _model_name = Unicode('AudioNodeModel').tag(sync=True)

    _in_nodes = List(Instance(Widget)).tag(sync=True, **widget_serialization)
    _out_nodes = List(Instance(Widget)).tag(sync=True, **widget_serialization)

    def _normalize_destination(self, destination):
        if not isinstance(destination, list):
            destination = [destination]

        if not all([isinstance(d, AudioNode) for d in destination]):
            raise ValueError(f"destination must be an AudioNode object(s)")
        if self in destination:
            raise ValueError("cannot connect an audio node to itself")

        return list(set(self._out_nodes) | set(destination))

    def connect(self, destination):
        """Connect the output of this audio node to another ``destination`` audio node."""

        if destination not in self._out_nodes:
            self._out_nodes = self._normalize_destination(destination)

    def disconnect(self, destination):
        """Disconnect the ouput of this audio node from a connected destination."""

        if destination not in self._out_nodes:
            raise ValueError("f{cannot disconnect destination {destination} that is not connected}")

        out_nodes = list(self._out_nodes)
        out_nodes.remove(destination)

        self._out_nodes = out_nodes

    def fan(self, *destinations):
        """Connect the output of this audio node to the ``destinations`` audio nodes in parallel."""

        self._out_nodes = self._normalize_destination(destinations)

    def chain(self, *nodes):
        """Connect the output of this audio node to the other audio nodes in series."""

        chain_nodes = [self] + list(nodes)

        for i in range(1, len(chain_nodes) + 1):
            chain_nodes[i].connect(chain_nodes[i + 1])

    def to_destination(self):
        """Convenience method to directly connect the output of this audio node
        to the master node.

        """
        self.connect(get_destination())

    @property
    def output(self):
        """Get all audio nodes connected to the output of this node."""
        return self._out_nodes

    @property
    def input(self):
        """Get all audio nodes connected to the input of this node."""
        return self._in_nodes


class Destination(AudioNode):
    """Audio master node."""

    _singleton = None

    _model_name = Unicode('DestinationModel').tag(sync=True)

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


class Oscillator(AudioNode):
    """A simple Oscillator."""
   
    _model_name = Unicode('OscillatorModel').tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    frequency = Float(440, help="Oscillator frequency").tag(sync=True)
    detune = Int(0, help="Oscillator frequency detune").tag(sync=True)
    volume = Float(-16, help="Oscillator gain").tag(sync=True)
    started = Bool(False, help="Start/stop oscillator").tag(sync=True)

    @validate('type')
    def _validate_oscillator_type(self, proposal):
        if proposal['value'] not in ["sine", "square", "sawtooth", "triangle"]:
            raise TraitError("Invalid oscillator type")
        return proposal['value']
