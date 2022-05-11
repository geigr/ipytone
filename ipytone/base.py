from ipywidgets import Widget, widget_serialization
from traitlets import Bool, Enum, HasTraits, Instance, Int, Unicode, Union

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

    def dispose(self):
        """Dispose and disconnect this node."""

        with self._graph.hold_state():
            self._disposed = True

        return self

    def close(self):
        self.dispose()
        super().close()

    def _repr_keys(self):
        if self.disposed:
            yield "disposed"


def is_disposed(node):
    return not is_native(node) and node.disposed


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
    _set_node_channels = Bool(True).tag(sync=True)
    channel_count = Int(2).tag(sync=True)
    channel_count_mode = Enum(["max", "clamped-max", "explicit"], default_value="max").tag(
        sync=True
    )
    channel_interpretation = Enum(["speakers", "discrete"], default_value="speakers").tag(sync=True)

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

    def connect(self, destination, output_number=0, input_number=0):
        """Connect the output of this audio node to the input of another node.

        Parameters
        ----------
        destination : :class:`AudioNode` or ``NativeAudioNode`` or :class:`Param` or ``NativeAudioParam``
            The destination node.
        output_number : int
            The channel number of the output of this node (default: 0).
        input_number : int
            The channel number of the input of the destination node (default: 0).

        """
        self._graph.connect(
            self, destination, output_number=output_number, input_number=input_number
        )
        return self

    def disconnect(self, destination, output_number=0, input_number=0):
        """Disconnect the ouput of this audio node from a connected node.

        Parameters
        ----------
        destination : :class:`AudioNode` or ``NativeAudioNode`` or :class:`Param` or ``NativeAudioParam``
            The connected destination node.
        output_number : int
            The channel number of the output of this node (default: 0).
        input_number : int
            The channel number of the input of the destination node (default: 0).

        """
        self._graph.disconnect(
            self, destination, output_number=output_number, input_number=input_number
        )
        return self

    def fan(self, *destinations):
        """Connect the output of this audio node to the ``destinations`` audio nodes in parallel."""

        with self._graph.hold_state():
            for node in destinations:
                self._graph.connect(self, node)

        return self

    def chain(self, *nodes):
        """Connect the output of this audio node to the other audio nodes in series."""

        chain_nodes = [self] + list(nodes)

        with self._graph.hold_state():
            for i in range(len(chain_nodes) - 1):
                self._graph.connect(chain_nodes[i], chain_nodes[i + 1])

        return self

    def to_destination(self):
        """Convenience method to directly connect the output of this audio node
        to the master node.

        """
        from .core import destination

        self.connect(destination)
        return self

    @property
    def input(self):
        """Returns the input node, or None if this node is a source."""

        return self._input

    @property
    def output(self):
        """Returns the output node, or None if this node is a sink."""

        return self._output

    def dispose(self):
        """Dispose and disconnect this audio node (as well as its input/output)."""

        with self._graph.hold_state():
            super().dispose()

            # also dispose input/output
            # TODO: will not clean the audio graph if native node are connected directly.
            if self.input is not None and not is_native(self.input):
                self.input.dispose()
            if self.output is not None and not is_native(self.output):
                self.output.dispose()

        return self


class PyInternalAudioNode(AudioNode):
    """An audio node widget wrapped by a :class:`PyAudioNode` object."""

    _model_name = Unicode("PyInternalAudioNodeModel").tag(sync=True)


class PyAudioNode(HasTraits):
    """A Pure-Python audio node.

    Although it provides the same interface than :class:`AudioNode`, it is not a
    :class:`ipywidget.Widget`. It is materialized in the front-end through its
    input and/or output nodes, which must correspond to :class:`AudioNode`
    objects (maybe via some other :class:`PyAudioNode` nested objects).

    This class may be used as a base class to create custom nodes that don't
    exist in Tone.js or high-level nodes that are straightforward to
    implement on top of audio nodes types already available in ipytone.

    """

    name = Unicode("").tag(sync=True)

    _input = Union(
        (
            Instance(ToneWidgetBase, allow_none=True),
            Instance("ipytone.PyAudioNode", allow_none=True),
        )
    )
    _output = Union(
        (
            Instance(ToneWidgetBase, allow_none=True),
            Instance("ipytone.PyAudioNode", allow_none=True),
        )
    )

    _set_node_channels = Bool(True)
    channel_count = Int(2)
    channel_count_mode = Enum(["max", "clamped-max", "explicit"], default_value="max")
    channel_interpretation = Enum(["speakers", "discrete"], default_value="speakers")

    def __init__(self, input_node, output_node, **kwargs):
        from .graph import _AUDIO_GRAPH

        # ignore _input / _output kwargs -> must be passed as args
        kwargs.pop("_input", None)
        kwargs.pop("_output", None)
        super().__init__(**kwargs)

        self._input = input_node
        self._output = output_node

        # the internal node must have two widgets (or None) as input/output
        max_iter = 50
        err_msg = "could not find input/output audio node widget"
        i = 0
        while isinstance(input_node, PyAudioNode):
            input_node = input_node.input
            if i >= max_iter:
                raise StopIteration(err_msg)
        i = 0
        while isinstance(output_node, PyAudioNode):
            output_node = output_node.output
            if i >= max_iter:
                raise StopIteration(err_msg)

        self._graph = _AUDIO_GRAPH

        self._node = PyInternalAudioNode(_input=input_node, _output=output_node, **kwargs)

    @property
    def widget(self):
        """Returns the wrapped audio node widget."""
        return self._node

    @property
    def number_of_inputs(self):
        return self._node.number_of_inputs

    @property
    def number_of_outputs(self):
        return self._node.number_of_outputs

    def connect(self, destination, output_number=0, input_number=0):
        self._node.connect(destination, output_number, input_number)
        return self

    def disconnect(self, destination, output_number=0, input_number=0):
        self._node.disconnect(destination, output_number, input_number)
        return self

    def fan(self, *destinations):
        self._node.fan(*destinations)
        return self

    def chain(self, *destinations):
        self._node.chain(*destinations)
        return self

    def to_destination(self):
        self._node.to_destination()
        return self

    @property
    def input(self):
        return self._input

    @property
    def output(self):
        return self._output

    def dispose(self):
        self._node.dispose()
        return self

    @property
    def disposed(self):
        return self._node.disposed

    def close(self):
        self._node.close()

    def _repr_keys(self):
        if self.name:
            yield "name"
        if self.disposed:
            yield "disposed"

    def _gen_repr_from_keys(self, keys):
        class_name = self.__class__.__name__
        signature = ", ".join("{}={!r}".format(key, getattr(self, key)) for key in keys)
        return f"{class_name}({signature})"

    def __repr__(self):
        # emulate repr of ipywidgets.Widget (no DOM)
        return self._gen_repr_from_keys(self._repr_keys())
