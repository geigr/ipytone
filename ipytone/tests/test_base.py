from ipytone.base import (
    AudioNode,
    NativeAudioNode,
    NativeAudioParam,
    PyAudioNode,
    PyInternalAudioNode,
    ToneObject,
)
from ipytone.core import InternalAudioNode, destination


def test_native_audio_node(audio_graph):
    node = NativeAudioNode(type="GainNode")

    assert node.number_of_inputs == 1
    assert node.number_of_outputs == 1
    assert node.type == "GainNode"
    assert repr(node) == "NativeAudioNode(type='GainNode')"

    node2 = NativeAudioNode()
    node.connect(node2)
    assert (node, node2, 0, 0) in audio_graph.connections

    node.disconnect(node2)
    assert (node, node2, 0, 0) not in audio_graph.connections


def test_native_audio_param():
    param = NativeAudioParam(type="Param")

    assert param.type == "Param"
    assert repr(param) == "NativeAudioParam(type='Param')"


def test_tone_object():
    obj = ToneObject()

    assert obj.disposed is False
    assert repr(obj) == "ToneObject()"
    obj.dispose()
    assert obj.disposed is True
    assert repr(obj) == "ToneObject(disposed=True)"

    obj2 = ToneObject()

    obj2.close()
    assert obj2.disposed is True


def test_audio_node_creation():
    node = AudioNode(name="test")

    assert node.input is None
    assert node.output is None
    assert node.number_of_inputs == 0
    assert node.number_of_outputs == 0
    assert node.channel_count == 2
    assert node.channel_count_mode == "max"
    assert node.channel_interpretation == "speakers"
    assert repr(node) == "AudioNode(name='test')"


def test_audio_node_connect(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()

    n = node1.connect(node2)

    assert (node1, node2, 0, 0) in audio_graph.connections
    assert n is node1

    node1.connect(node2, 1, 2)
    assert (node1, node2, 1, 2) in audio_graph.connections

    n = node1.disconnect(node2)

    assert (node1, node2, 0, 0) not in audio_graph.connections
    assert n is node1

    node1.disconnect(node2, 1, 2)
    assert (node1, node2, 1, 2) not in audio_graph.connections


def test_audio_node_disconnect(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()

    n = node1.connect(node2).disconnect(node2)

    assert (node1, node2, 0, 0) not in audio_graph.connections
    assert n is node1


def test_audio_node_dispose(audio_graph):
    in_node = InternalAudioNode()
    out_node = InternalAudioNode()
    node1 = AudioNode(_input=in_node, _output=out_node)
    node2 = InternalAudioNode()

    node1.connect(node2)

    assert node1.disposed is False
    assert (node1, node2, 0, 0) in audio_graph.connections

    node1.dispose()

    assert node1.disposed is True
    assert in_node.disposed is True
    assert out_node.disposed is True
    assert (node1, node2, 0, 0) not in audio_graph.connections


def test_audio_node_to_destination(audio_graph):
    node = InternalAudioNode()

    n = node.to_destination()

    assert (node, destination, 0, 0) in audio_graph.connections
    assert n is node


def test_audio_node_fan(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()
    node3 = InternalAudioNode()

    n = node1.fan(node2, node3)

    assert (node1, node2, 0, 0) in audio_graph.connections
    assert (node1, node3, 0, 0) in audio_graph.connections
    assert n is node1


def test_audio_node_chain(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()
    node3 = InternalAudioNode()

    n = node1.chain(node2, node3)

    assert (node1, node2, 0, 0) in audio_graph.connections
    assert (node2, node3, 0, 0) in audio_graph.connections
    assert n is node1


def test_pyaudionode(audio_graph):
    in_node_in = InternalAudioNode()
    in_node_out = InternalAudioNode()
    in_node = PyAudioNode(in_node_in, in_node_out)
    out_node = InternalAudioNode()
    node = PyAudioNode(in_node, out_node, name="test")

    assert node.disposed is False
    assert node.number_of_inputs == 1
    assert node.number_of_outputs == 1
    assert node.channel_count == 2
    assert node.channel_count_mode == "max"
    assert node.channel_interpretation == "speakers"
    assert repr(node) == "PyAudioNode(name='test')"

    assert node.input is in_node
    assert node.output is out_node

    assert isinstance(node.widget, PyInternalAudioNode)
    assert node.widget.input is in_node_in
    assert node.widget.output is out_node

    node2 = InternalAudioNode()
    n = node.connect(node2)
    assert (node.widget, node2, 0, 0) in audio_graph.connections
    assert n is node

    node3 = InternalAudioNode()
    node3.connect(node)
    assert (node3, node.widget, 0, 0) in audio_graph.connections

    n = node.disconnect(node2)
    assert (node.widget, node2, 0, 0) not in audio_graph.connections
    assert n is node

    node4 = InternalAudioNode()
    node5 = InternalAudioNode()
    n = node.fan(node4, node5)
    assert (node.widget, node4, 0, 0) in audio_graph.connections
    assert (node.widget, node5, 0, 0) in audio_graph.connections
    assert n is node

    node6 = InternalAudioNode()
    node7 = InternalAudioNode()
    n = node.chain(node6, node7)
    assert (node.widget, node6, 0, 0) in audio_graph.connections
    assert (node6, node7, 0, 0) in audio_graph.connections
    assert n is node

    n = node.to_destination()
    assert (node.widget, destination, 0, 0) in audio_graph.connections
    assert n is node

    n = node.dispose()
    assert node.disposed is True
    assert n is node
