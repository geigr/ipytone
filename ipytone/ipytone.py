#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget
from traitlets import Unicode, Float, Int, Bool, validate, observe, TraitError
from ._frontend import module_name, module_version


class Oscillator(Widget):
    """A simple Oscillator."""
   
    _model_name = Unicode('OscillatorModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    type = Unicode("sine", help="Oscillator type").tag(sync=True)
    frequency = Float(440, help="Oscillator frequency").tag(sync=True)
    detune = Int(0, help="Oscillator frequency detune").tag(sync=True)
    volume = Float(-16, help="Oscillator gain").tag(sync=True)
    started = Bool(False, help="Start/stop oscillator").tag(sync=True)

    @validate('type')
    def _valid_value(self, proposal):
        if proposal['value'] not in ["sine", "square", "sawtooth", "triangle"]:
            raise TraitError("Invalid oscillator type")
        return proposal['value']


class Time(Widget):
    """The time in the browser."""
   
    _model_name = Unicode('TimeModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    time = Float(0, help="The time in the browser").tag(sync=True)

    def __init__(self, output=None, **kwargs):
        self.output = output
        super().__init__(**kwargs)

    @observe('time')
    def _observe_time(self, change):
        if self.output is not None:
            with self.output:
                print(change['new'])
