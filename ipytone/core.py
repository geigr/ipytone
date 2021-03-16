import math

from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, Unicode, Union

from .base import AudioNode, NativeAudioNode, NativeAudioParam, NodeWithContext

UNITS = [
    "audio_range",
    "bpm",
    "cents",
    "decibels",
    "degrees",
    "frequency",
    "gain",
    "hertz",
    "number",
    "normal_range",
    "positive",
    "radians",
    "samples",
    "ticks",
    "time",
    "transport_time",
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


class Param(NodeWithContext):
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
        elif self._units == "audio_range":
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
        elif self._units in ["audio_range", "normal_range"]:
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
