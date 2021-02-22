from ipywidgets import widget_serialization
from traitlets import Bool, Float, Instance, Int, List, Tuple, Unicode

from .base import AudioNode, ToneWidgetBase


class InternalNode(ToneWidgetBase):
    """Ipytone Widget that wraps a Tone.js object with no exposed functionality."""

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
        in_node = InternalAudioNode(tone_class="Gain")
        out_node = InternalAudioNode(tone_class="Volume")

        kwargs.update({"_input": in_node, "_output": out_node})
        super().__init__(*args, **kwargs)


_DESTINATION = Destination()


def get_destination():
    """Returns ipytone's audio master node."""
    return _DESTINATION


class AudioGraph(ToneWidgetBase):
    """An audio graph representing all nodes and their connections in the main audio context."""

    _model_name = Unicode("AudioGraphModel").tag(sync=True)

    _connections = List(Tuple(Instance(AudioNode), Instance(AudioNode))).tag(
        sync=True, **widget_serialization
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._updated_connections = list(self._connections)

    def connect(self, src_node, dest_node, sync=True):
        """Connect a source node output to a destination node input."""

        if not (isinstance(src_node, AudioNode) and isinstance(dest_node, AudioNode)):
            raise ValueError("Source and destination nodes must be AudioNode objects")
        if not dest_node.number_of_inputs:
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
