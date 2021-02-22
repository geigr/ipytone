from ipywidgets import Widget, widget_serialization
from traitlets import Bool, Instance, Unicode

from ._frontend import module_name, module_version


class ToneWidgetBase(Widget):
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


class NodeWithContext(ToneWidgetBase):

    name = Unicode("").tag(sync=True)

    _model_name = Unicode("NodeWithContextModel").tag(sync=True)

    def _repr_keys(self):
        if self.name:
            yield "name"


class AudioNode(NodeWithContext):
    """An audio node widget."""

    _model_name = Unicode("AudioNodeModel").tag(sync=True)

    _is_internal = False
    _input = Instance(ToneWidgetBase, allow_none=True).tag(sync=True, **widget_serialization)
    _output = Instance(ToneWidgetBase, allow_none=True).tag(sync=True, **widget_serialization)
    _create_node = Bool(True).tag(sync=True)

    @property
    def number_of_inputs(self):
        """Returns the number of input slots for the input node (0 for source nodes)."""
        if self._is_internal:
            return self._n_inputs
        elif self._input is None:
            return 0
        elif isinstance(self._input, AudioNode):
            return self._input.number_of_inputs
        else:
            # Param
            return 1

    @property
    def number_of_outputs(self):
        """Returns the number of output slots for the output node (0 for sink nodes)."""
        if self._is_internal:
            return self._n_outputs
        elif self._output is None:
            return 0
        else:
            return self._output.number_of_outputs

    def connect(self, destination):
        """Connect the output of this audio node to the input of a ``destination`` audio node."""

        from .core import _AUDIO_GRAPH

        _AUDIO_GRAPH.connect(self, destination)

        return self

    def disconnect(self, destination):
        """Disconnect the ouput of this audio node from a connected destination."""

        from .core import _AUDIO_GRAPH

        _AUDIO_GRAPH.disconnect(self, destination)

        return self

    def fan(self, *destinations):
        """Connect the output of this audio node to the ``destinations`` audio nodes in parallel."""

        from .core import _AUDIO_GRAPH

        for node in destinations:
            _AUDIO_GRAPH.connect(self, node, sync=False)

        _AUDIO_GRAPH.sync_connections()
        return self

    def chain(self, *nodes):
        """Connect the output of this audio node to the other audio nodes in series."""

        from .core import _AUDIO_GRAPH

        chain_nodes = [self] + list(nodes)

        for i in range(len(chain_nodes) - 1):
            _AUDIO_GRAPH.connect(chain_nodes[i], chain_nodes[i + 1], sync=False)

        _AUDIO_GRAPH.sync_connections()
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
        if not self._is_internal:
            return self._input
        elif self._n_inputs:
            return "internal"
        else:
            return None

    @property
    def output(self):
        """Returns the output node, or None if this node is a sink."""
        if not self._is_internal:
            return self._output
        elif self._n_outputs:
            return "internal"
        else:
            return None
