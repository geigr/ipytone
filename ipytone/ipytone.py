#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import widget_serialization, Widget
from traitlets import Instance, Union, Unicode, List, Float, Int, Bool, validate, TraitError

from ._frontend import module_name, module_version


class _ToneWidgetBase(Widget):
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


class AudioNode(_ToneWidgetBase):
    """An audio node widget."""

    _model_name = Unicode('AudioNodeModel').tag(sync=True)

    inputs = List(Instance(Widget)).tag(sync=True, **widget_serialization)
    outputs = List(Instance(Widget)).tag(sync=True, **widget_serialization)


class Destination(AudioNode):
    """Audio master output node."""

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
    """Returns ipytone's audio master output node."""
    return _DESTINATION


class Oscillator(AudioNode):
    """A simple Oscillator."""
   
    _model_name = Unicode('OscillatorModel').tag(sync=True)

    type = Unicode("sine").tag(sync=True)
    frequency = Float(440).tag(sync=True)
    detune = Int(0).tag(sync=True)
    volume = Float(-16).tag(sync=True)
    started = Bool(False).tag(sync=True)

    def __init__(self, type='sine', frequency=440, detune=0, volume=-16, started=False, **kwargs):
        super(Oscillator, self).__init__(
            type=type,
            frequency=frequency,
            detune=detune,
            volume=volume,
            started=started,
            **kwargs
        )

    @validate('type')
    def _validate_oscillator_type(self, proposal):
        if proposal['value'] not in ["sine", "square", "sawtooth", "triangle"]:
            raise TraitError("Invalid oscillator type")
        return proposal['value']
