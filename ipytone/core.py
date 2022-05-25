import math

import numpy as np
from ipywidgets import Widget, widget_serialization
from traitlets import Bool, Dict, Enum, Float, Instance, Int, List, Unicode, Union
from traittypes import Array

from .base import AudioNode, NativeAudioNode, NativeAudioParam, NodeWithContext, ToneObject
from .callback import add_or_send_event
from .observe import ScheduleObserveMixin
from .serialization import data_array_serialization

UNITS = [
    "audioRange",
    "bpm",
    "cents",
    "decibels",
    "degrees",
    "frequency",
    "gain",
    "hertz",
    "number",
    "normalRange",
    "positive",
    "radians",
    "samples",
    "ticks",
    "time",
    "transportTime",
]


class InternalAudioNode(AudioNode):
    """Widget that wraps a Tone.js audio node instance with no exposed functionality.

    It wraps an instance of a Tone.js ``ToneAudioNode`` class that is either not
    yet implemented in ipytone or that does already expose its functionality in its
    parent widget.

    """

    _model_name = Unicode("InternalAudioNodeModel").tag(sync=True)

    _create_node = Bool(False).tag(sync=True)
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    type = Unicode().tag(sync=True)

    @property
    def number_of_inputs(self):
        return self._n_inputs

    @property
    def number_of_outputs(self):
        return self._n_outputs

    def _repr_keys(self):
        if self.type:
            yield "type"


class ParamScheduleMixin:
    def set_value_at_time(self, value, time):
        """Schedules a parameter value change at the given time."""
        add_or_send_event("setValueAtTime", self, {"value": value, "time": time})
        return self

    def set_ramp_point(self, time):
        """Creates a schedule point with the value computed at the given time.

        Use this method to create an automation starting point when you don't
        know what will be the value at this time. Otherwise use
        :meth:`Param.set_value_at_time`.

        An automation starting point is needed when calling
        :meth:`Param.linear_ramp_to_value_at_time` or
        :meth:`Param.exp_ramp_to_value_at_time`.

        """
        add_or_send_event("setRampPoint", self, {"time": time})
        return self

    def linear_ramp_to_value_at_time(self, value, time):
        """Schedules a linear continuous change from the previous scheduled parameter
        value to the given value at the given time.

        """
        add_or_send_event("linearRampToValueAtTime", self, {"value": value, "time": time})
        return self

    def exp_ramp_to_value_at_time(self, value, time):
        """Schedules an exponential continuous change from the previous scheduled parameter
        value to the given value at the given time.

        """
        add_or_send_event("exponentialRampToValueAtTime", self, {"value": value, "time": time})
        return self

    def linear_ramp_to(self, value, ramp_time, start_time=None):
        """Schedules a linear continuous change from the current time and current
        value to the given value over the duration of ``ramp_time``.

        """
        add_or_send_event(
            "linearRampTo", self, {"value": value, "ramp_time": ramp_time, "start_time": start_time}
        )
        return self

    def exp_ramp_to(self, value, ramp_time, start_time=None):
        """Schedules an exponential continuous change from the current time and current
        value to the given value over the duration of ``ramp_time``.

        """
        add_or_send_event(
            "exponentialRampTo",
            self,
            {"value": value, "ramp_time": ramp_time, "start_time": start_time},
        )
        return self

    def target_ramp_to(self, value, ramp_time, start_time=None):
        """Start exponentially approaching the target value at the given time.

        Since it is an exponential approach it will continue approaching after
        the ramp duration. ``ramp_time`` is the time that it takes to reach over 99% of
        the way towards the value.

        """
        add_or_send_event(
            "targetRampTo",
            self,
            {"value": value, "ramp_time": ramp_time, "start_time": start_time},
        )
        return self

    def ramp_to(self, value, ramp_time, start_time=None):
        """Ramps to the given value over the duration of the ``ramp_time``.

        Automatically selects the best ramp type (exponential or linear)
        depending on the `units` of the signal

        """
        if self.units in ["frequency", "bpm", "decibels"]:
            return self.exp_ramp_to(value, ramp_time, start_time)
        else:
            return self.linear_ramp_to(value, ramp_time, start_time)

    def exp_approach_value_at_time(self, value, time, ramp_time):
        """Start exponentially approaching the target value at the given time.

        Since it is an exponential approach it will continue approaching after
        the ramp duration. ``ramp_time`` is the time that it takes to reach
        over 99% of the way towards the value.

        """
        add_or_send_event(
            "exponentialApproachValueAtTime",
            self,
            {"value": value, "time": time, "ramp_time": ramp_time},
        )
        return self

    def set_target_at_time(self, value, start_time, time_const):
        """Start exponentially approaching the target value at the given time."""
        add_or_send_event(
            "setTargetAtTime",
            self,
            {"value": value, "start_time": start_time, "time_const": time_const},
        )
        return self

    def set_value_curve_at_time(self, values, start_time, duration, scaling=None):
        """Sets an array of arbitrary parameter values starting at the given time
        for the given duration.

        Optionally scale values with a ``scaling`` factor.

        """
        add_or_send_event(
            "setValueCurveAtTime",
            self,
            {
                "values": list(values),
                "start_time": start_time,
                "duration": duration,
                "scaling": scaling,
            },
        )
        return self

    def cancel_scheduled_values(self, time):
        """Cancels all scheduled parameter changes with times greater than or equal to
        a given time.

        """
        add_or_send_event("cancelScheduledValues", self, {"time": time})
        return self

    def cancel_and_hold_at_time(self, time):
        """Like :meth:`Param.cancel_scheduled_values` but also holds the automated value
        at time until the next automated event.

        """
        add_or_send_event("cancelAndHoldAtTime", self, {"time": time})
        return self


class Param(NodeWithContext, ParamScheduleMixin, ScheduleObserveMixin):
    """Single, automatable parameter with units."""

    _model_name = Unicode("ParamModel").tag(sync=True)

    _is_param = True
    _create_node = Bool(False).tag(sync=True)
    _input = Union((Instance(NativeAudioParam), Instance(NativeAudioNode))).tag(
        sync=True, **widget_serialization
    )
    _units = Enum(UNITS, default_value="number", allow_none=False).tag(sync=True)
    value = Union((Float(), Int(), Unicode()), help="Parameter value").tag(sync=True)
    _min_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    _max_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    _swappable = Bool(False).tag(sync=True)
    overridden = Bool(False).tag(sync=True)
    convert = Bool(help="If True, convert the value into the specified units").tag(sync=True)

    _observable_traits = List(["value"])

    def __init__(
        self,
        value=1,
        units="number",
        convert=True,
        min_value=None,
        max_value=None,
        swappable=False,
        **kwargs
    ):
        if "_input" not in kwargs:
            if swappable:
                input = NativeAudioNode(type="GainNode")
            else:
                input = NativeAudioParam()

            kwargs["_input"] = input

        kw = {
            "value": value,
            "_units": units,
            "convert": convert,
            "_min_value": min_value,
            "_max_value": max_value,
            "_swappable": swappable,
        }

        kwargs.update(kw)
        super().__init__(**kwargs)

    @property
    def units(self):
        """Parameter value units."""
        return self._units

    @property
    def min_value(self):
        """Parameter value lower limit."""
        if self._min_value is not None:
            return self._min_value
        elif self._units == "audioRange":
            return -1
        elif self._units in ["number", "decibels"]:
            # min value for web audio API GainNode
            return -math.inf
        else:
            # all other units
            return 0

    @property
    def max_value(self):
        """Parameter value upper limit."""
        if self._max_value is not None:
            return self._max_value
        elif self._units in ["audioRange", "normalRange"]:
            return 1
        else:
            return math.inf

    @property
    def input(self):
        """Returns the input node."""
        return self._input

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if self.overridden:
            yield "overridden"
        else:
            yield "value"
            yield "units"


class Gain(AudioNode):
    """A simple node for adjusting audio gain."""

    _model_name = Unicode("GainModel").tag(sync=True)

    _gain = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, gain=1, units="gain", **kwargs):
        name = kwargs.pop("name", "")
        create_node = kwargs.pop("_create_node", True)

        node = NativeAudioNode(type="GainNode")
        _gain = Param(value=gain, units=units, **kwargs)

        super().__init__(
            _gain=_gain, _input=node, _output=node, name=name, _create_node=create_node
        )

    @property
    def gain(self) -> Param:
        """The gain parameter."""
        return self._gain

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "gain"

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self.gain.dispose()

        return self


class Volume(AudioNode):
    """Simple volume node."""

    _model_name = Unicode("VolumeModel").tag(sync=True)

    _volume = Instance(Param).tag(sync=True, **widget_serialization)
    mute = Bool(False).tag(sync=True)

    def __init__(self, volume=0, mute=False, **kwargs):

        node = Gain(gain=volume, units="decibels", _create_node=False)
        _volume = node._gain

        super().__init__(_volume=_volume, _input=node, _output=node, mute=mute, **kwargs)

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._volume

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "volume"
        yield "mute"


class Destination(AudioNode):
    """Audio master node."""

    _singleton = None

    _model_name = Unicode("DestinationModel").tag(sync=True)

    name = Unicode("main output").tag(sync=True)

    _volume = Instance(Param).tag(sync=True, **widget_serialization)
    mute = Bool(False).tag(sync=True)

    def __new__(cls):
        if Destination._singleton is None:
            Destination._singleton = super(Destination, cls).__new__(cls)
        return Destination._singleton

    def __init__(self, **kwargs):
        in_node = Volume(_create_node=False)
        out_node = Gain(_create_node=False)

        kwargs.update({"_input": in_node, "_output": out_node, "_volume": in_node.volume})
        super().__init__(**kwargs)

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._volume

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "volume"
        yield "mute"


destination = Destination()
"""Ipytone's audio main output node."""


class AudioBuffer(ToneObject):
    """Audio buffer loaded from an URL or an array.

    Parameters
    ----------
    url_or_array : str or array-like or array widget
        Buffer file (URL) or data.
    sync_array : bool, optional
        If True, the array trait will be synchronized as soon as the
        audio buffer is loaded in the front-end (default: False). It is
        ignored if an array is already given as buffer data or if the
        duration of the buffer exceeds 10 seconds.
    reverse : bool, optional
        If True, the audio buffer is reversed (default: False).

    """

    _model_name = Unicode("AudioBufferModel").tag(sync=True)

    buffer_url = Unicode(
        help="Buffer loaded from this URL (None if an array is used)",
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    array = Union((Instance(Widget), Array()), allow_none=True, default_value=None).tag(
        sync=True, **data_array_serialization
    )
    _sync_array = Bool(False).tag(sync=True)
    _create_node = Bool(True).tag(sync=True)

    duration = Float(0, help="Buffer duration in seconds (0 if not loaded)", read_only=True).tag(
        sync=True
    )
    length = Int(0, help="Buffer size in samples (0 if not loaded)", read_only=True).tag(sync=True)
    n_channels = Int(
        0, help="Number of discrete audio channels (0 if not loaded)", read_only=True
    ).tag(sync=True)
    sample_rate = Int(0, help="Buffer sample rate (0 if not loaded)", read_only=True).tag(sync=True)
    loaded = Bool(False, help="True if the audio buffer is loaded", read_only=True).tag(sync=True)
    reverse = Bool(False, help="True if the buffer is reversed").tag(sync=True)

    def __init__(self, url_or_array, sync_array=False, reverse=False, **kwargs):
        kwargs.update({"reverse": reverse})
        if isinstance(url_or_array, str):
            kwargs.update({"buffer_url": url_or_array, "_sync_array": sync_array})
        elif isinstance(url_or_array, (np.ndarray, Widget)):
            # _sync_array=False: no need to get array from the front-end
            kwargs.update({"array": url_or_array, "_sync_array": False})
        super().__init__(**kwargs)

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if not self.disposed:
            yield "loaded"
            if self.loaded:
                yield "duration"


def add_buf_to_collection(buffers, key, url, base_url="", create_node=False):
    if isinstance(url, str):
        buf = AudioBuffer(base_url + url, _create_node=create_node)
    elif isinstance(url, AudioBuffer):
        buf = url
    else:
        raise TypeError("Invalid buffer: must be a string (url) or AudioBuffer")

    buffers[key] = buf


class AudioBuffers(ToneObject):
    """A collection (dict-like) of audio buffers.

    Parameters
    ----------
    urls : dict-like
        A mapping of buffer names (str) and buffer file URLs (str) or
        :class:`AudioBuffer` objects
    base_url : str, optional
        Prefix to add before all the URLs.

    """

    _model_name = Unicode("AudioBuffersModel").tag(sync=True)

    _base_url = Unicode("").tag(sync=True)
    _buffers = Dict(value_trait=Instance(AudioBuffer), allow_none=True).tag(
        sync=True, **widget_serialization
    )
    _create_node = Bool(True).tag(sync=True)

    def __init__(self, urls, base_url="", **kwargs):
        create_buffer = kwargs.get("_create_node", True)
        buffers = {}

        for key, url in urls.items():
            add_buf_to_collection(
                buffers, str(key), url, base_url=base_url, create_node=create_buffer
            )

        kwargs.update({"_base_url": base_url, "_buffers": buffers})
        super().__init__(**kwargs)

    @property
    def base_url(self):
        return self._base_url

    @property
    def buffers(self):
        """Returns a dictionary with all buffers."""
        return self._buffers.copy()

    @property
    def loaded(self):
        """Return True if all buffers are loaded."""
        return all(buf.loaded for buf in self._buffers.values())

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            for buf in self._buffers.values():
                buf.dispose()
        self._buffers = {}

        return self

    def add(self, key, url, create_node=True):
        """Add or replace a buffer.

        Parameters
        ----------
        key : str
            Buffer name.
        url : str or :class:`AudioBuffer`.
            Buffer file URL (str) or :class:`AudioBuffer` object.
        create_node : bool, optional
            Internal use only.

        """
        buffers = self._buffers.copy()
        add_buf_to_collection(buffers, key, url, base_url=self._base_url, create_node=create_node)
        self._buffers = buffers

        return self

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if not self.disposed:
            yield "loaded"
