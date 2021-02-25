from ipywidgets import widget_serialization
from traitlets import Instance, List, Tuple, Unicode, Union

from .base import AudioNode, NativeAudioNode, NativeAudioParam, ToneWidgetBase
from .core import Param

_Connection = List(
    Tuple(
        Union((Instance(AudioNode), Instance(NativeAudioNode))),
        Union(
            (
                Instance(AudioNode),
                Instance(NativeAudioNode),
                Instance(Param),
                Instance(NativeAudioParam),
            )
        ),
    )
)


class AudioGraph(ToneWidgetBase):
    """An audio graph representing all nodes and their connections in the main audio context."""

    _model_name = Unicode("AudioGraphModel").tag(sync=True)
    _connections = _Connection.tag(sync=True, **widget_serialization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._updated_connections = list(self._connections)

    def connect(self, src_node, dest_node, sync=True):
        """Connect a source node output to a destination node input."""

        if not isinstance(src_node, (AudioNode, NativeAudioNode)):
            raise ValueError("src_node must be a (native) AudioNode object")
        if not isinstance(dest_node, (AudioNode, NativeAudioNode, Param, NativeAudioParam)):
            raise ValueError("dest_node must be a (native) AudioNode or Param object")
        if isinstance(dest_node, AudioNode):
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

    def clean(self, sync=True):
        """Remove all connections from/to disposed nodes."""

        for src, dest in self._connections:
            if src.disposed or dest.disposed:
                self.disconnect(src, dest, sync=False)

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
