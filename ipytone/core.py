import math

from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, List, Tuple, Unicode, Union

from .base import AudioNode, Node, NodeWithContext, ToneWidgetBase

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


class InternalNode(Node):
    """Ipytone Widget that wraps a Tone.js or Web API audio object with
    no exposed functionality.

    """

    _model_name = Unicode("InternalNodeModel").tag(sync=True)

    _is_internal = True
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    tone_class = Unicode().tag(sync=True)

    @property
    def number_of_inputs(self):
        return self._n_inputs

    @property
    def number_of_outputs(self):
        return self._n_outputs

    def _repr_keys(self):
        if self.tone_class:
            yield "tone_class"


class InternalAudioNode(AudioNode):
    """Ipytone Widget that wraps a Tone.js audio node instance with no exposed functionality."""

    _model_name = Unicode("InternalAudioNodeModel").tag(sync=True)

    _is_internal = True
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    tone_class = Unicode().tag(sync=True)
    _create_node = Bool(False).tag(sync=True)

    def _repr_keys(self):
        if self.tone_class:
            yield "tone_class"


class Param(NodeWithContext):
    """Single, automatable parameter with units."""

    _model_name = Unicode("ParamModel").tag(sync=True)

    _create_node = Bool(True).tag(sync=True)
    _input = Instance(Node, allow_none=True).tag(sync=True, **widget_serialization)
    _units = Enum(UNITS, default_value="number", allow_none=False).tag(sync=True)
    value = Union((Float(), Int(), Unicode()), help="Parameter value").tag(sync=True)
    _min_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    _max_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    overridden = Bool(False).tag(sync=True)
    convert = Bool(help="If True, convert the value into the specified units").tag(sync=True)

    def __init__(
        self, value=1, units="number", convert=True, min_value=None, max_value=None, **kwargs
    ):
        in_node = InternalNode(tone_class="Gain", _n_outputs=0)

        kw = {
            "_input": in_node,
            "value": value,
            "_units": units,
            "convert": convert,
            "_min_value": min_value,
            "_max_value": max_value,
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

        node = InternalNode(tone_class="GainNode")
        _gain = Param(value=gain, units=units, _create_node=False, **kwargs)

        super().__init__(
            _gain=_gain, _input=node, _output=node, name=name, _create_node=create_node
        )

    @property
    def gain(self):
        """The gain parameter."""
        return self._gain

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "gain"


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

    def __init__(self, *args, **kwargs):
        in_node = Gain(_create_node=False)
        out_node = InternalAudioNode(tone_class="Volume")

        kwargs.update({"_input": in_node, "_output": out_node})
        super().__init__(*args, **kwargs)


_DESTINATION = Destination()


def get_destination():
    """Returns ipytone's audio master node."""
    return _DESTINATION


_Connection = List(Tuple(Instance(AudioNode), Union((Instance(AudioNode), Instance(Param)))))


class AudioGraph(ToneWidgetBase):
    """An audio graph representing all nodes and their connections in the main audio context."""

    _model_name = Unicode("AudioGraphModel").tag(sync=True)
    _connections = _Connection.tag(sync=True, **widget_serialization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._updated_connections = list(self._connections)

    def connect(self, src_node, dest_node, sync=True):
        """Connect a source node output to a destination node input."""

        if not isinstance(src_node, AudioNode):
            raise ValueError("src_node must be an AudioNode object")
        if not isinstance(dest_node, (AudioNode, Param)):
            raise ValueError("dest_node must be an AudioNode or Param object")
        if isinstance(dest_node, AudioNode) and not dest_node.number_of_inputs:
            raise ValueError(f"Cannot connect to audio source {dest_node}")
        if not src_node.number_of_outputs:
            raise ValueError(f"Cannot connect from audio sink {src_node}")

        conn = (src_node, dest_node)

        if conn not in self._connections:
            self._updated_connections.append(conn)

        if sync:
            self.sync_connections()

    def disconnect(self, src_node, dest_node, sync=True):
        """Disconnect a source node output from a destination node input."""

        conn = (src_node, dest_node)

        if conn not in self._connections:
            raise ValueError(f"Node {src_node} is not connected to node {dest_node}")

        self._updated_connections.remove(conn)

        if sync:
            self.sync_connections()

    def sync_connections(self):
        """Synchronize connections with the front-end (internal use)."""

        self._connections = self._updated_connections
        self._updated_connections = self._connections.copy()

    @property
    def connections(self):
        """Returns the audio graph edges as a list of (src_node, dest_node) tuples."""

        return list(self._connections)

    @property
    def nodes(self):
        """Returns a list of all nodes in the audio graph."""

        return list({node for conn in self._connections for node in conn})


_AUDIO_GRAPH = AudioGraph()


def get_audio_graph():
    """Returns the audio graph of ipytone's main audio context."""
    return _AUDIO_GRAPH
