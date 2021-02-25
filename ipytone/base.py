from ipywidgets import Widget, widget_serialization
from traitlets import Bool, Instance, Int, Unicode

from ._frontend import module_name, module_version


class ToneWidgetBase(Widget):
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


class NativeAudioNode(ToneWidgetBase):
    """A widget that wraps a Web API Audio native AudioNode object."""

    _model_name = Unicode("NativeAudioNodeModel").tag(sync=True)

    _is_param = False
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    type = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        from .graph import _AUDIO_GRAPH

        self._graph = _AUDIO_GRAPH

        super().__init__(*args, **kwargs)

    @property
    def number_of_inputs(self):
        return self._n_inputs

    @property
    def number_of_outputs(self):
        return self._n_outputs

    def connect(self, destination):
        """Connect the output of this audio node to the input of a ``destination`` audio node."""
        self._graph.connect(self, destination)

        return self

    def disconnect(self, destination):
        """Disconnect the ouput of this audio node from a connected destination."""
        self._graph.disconnect(self, destination)

        return self

    def _repr_keys(self):
        if self.type:
            yield "type"


class NativeAudioParam(ToneWidgetBase):
    """A widget that wraps a Web API Audio native AudioParam object."""

    _model_name = Unicode("NativeAudioParamModel").tag(sync=True)

    _is_param = True
    type = Unicode().tag(sync=True)

    def _repr_keys(self):
        if self.type:
            yield "type"


def is_native(widget):
    return isinstance(widget, (NativeAudioNode, NativeAudioParam))


class ToneObject(ToneWidgetBase):

    _model_name = Unicode("ToneObjectModel").tag(sync=True)
    _disposed = Bool(False).tag(sync=True)

    def __init__(self, *args, **kwargs):
        from .graph import _AUDIO_GRAPH

        self._graph = _AUDIO_GRAPH

        super().__init__(*args, **kwargs)

    @property
    def disposed(self):
        """Returns True if the node was disposed (i.e., disconnected and
        web audio node freed for garbage collection).

        """
        return self._disposed

    def dispose(self, clean_graph=True):
        """Dispose and disconnect this node."""

        self._disposed = True

        if clean_graph:
            self._graph.clean()

        return self

    def close(self):
        self.dispose()
        super().close()

    def _repr_keys(self):
        if self.disposed:
            yield "disposed"


class NodeWithContext(ToneObject):

    name = Unicode("").tag(sync=True)

    _model_name = Unicode("NodeWithContextModel").tag(sync=True)

    def _repr_keys(self):
        if self.name:
            yield "name"
        if self.disposed:
            yield "disposed"


class AudioNode(NodeWithContext):
    """An audio node widget."""

    _model_name = Unicode("AudioNodeModel").tag(sync=True)

    _is_param = False
    _input = Instance(ToneWidgetBase, allow_none=True).tag(sync=True, **widget_serialization)
    _output = Instance(ToneWidgetBase, allow_none=True).tag(sync=True, **widget_serialization)
    _create_node = Bool(True).tag(sync=True)

    @property
    def number_of_inputs(self):
        """Returns the number of input slots for the input node (0 for source nodes)."""
        if self._input is None:
            return 0
        elif self._input._is_param:
            return 1
        else:
            return self._input.number_of_inputs

    @property
    def number_of_outputs(self):
        """Returns the number of output slots for the output node (0 for sink nodes)."""
        if self._output is None:
            return 0
        else:
            return self._output.number_of_outputs

    def connect(self, destination):
        """Connect the output of this audio node to the input of a ``destination`` audio node."""

        self._graph.connect(self, destination)
        return self

    def disconnect(self, destination):
        """Disconnect the ouput of this audio node from a connected destination."""

        self._graph.disconnect(self, destination)
        return self

    def fan(self, *destinations):
        """Connect the output of this audio node to the ``destinations`` audio nodes in parallel."""

        for node in destinations:
            self._graph.connect(self, node, sync=False)

        self._graph.sync_connections()
        return self

    def chain(self, *nodes):
        """Connect the output of this audio node to the other audio nodes in series."""

        chain_nodes = [self] + list(nodes)

        for i in range(len(chain_nodes) - 1):
            self._graph.connect(chain_nodes[i], chain_nodes[i + 1], sync=False)

        self._graph.sync_connections()
        return self

    def to_destination(self):
        """Convenience method to directly connect the output of this audio node
        to the master node.

        """
        from .core import get_destination

        self.connect(get_destination())
        return self

    @property
    def input(self):
        """Returns the input node, or None if this node is a source."""

        return self._input

    @property
    def output(self):
        """Returns the output node, or None if this node is a sink."""

        return self._output

    def dispose(self, clean_graph=True):
        """Dispose and disconnect this audio node (as well as its input/output)."""

        super().dispose(clean_graph=False)

        # also dispose input/output
        # TODO: will not clean the audio graph if native node are connected directly.
        if self.input is not None and not is_native(self.input):
            self.input.dispose(clean_graph=False)
        if self.output is not None and not is_native(self.output):
            self.output.dispose(clean_graph=False)

        if clean_graph:
            self._graph.clean()

        return self
