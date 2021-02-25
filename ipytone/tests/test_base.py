from ipytone.base import AudioNode
from ipytone.core import InternalAudioNode, get_destination


def test_audio_node_creation():
    node = AudioNode(name="test")

    assert node.input is None
    assert node.output is None
    assert node.number_of_inputs == 0
    assert node.number_of_outputs == 0
    assert repr(node) == "AudioNode(name='test')"


def test_audio_node_connect(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()

    n = node1.connect(node2)

    assert (node1, node2) in audio_graph.connections
    assert n is node1

    n = node1.disconnect(node2)

    assert (node1, node2) not in audio_graph.connections
    assert n is node1


def test_audio_node_disconnect(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()

    n = node1.connect(node2).disconnect(node2)

    assert (node1, node2) not in audio_graph.connections
    assert n is node1


def test_audio_node_dispose(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()

    n = node1.connect(node2)


def test_audio_node_to_destination(audio_graph):
    node = InternalAudioNode()

    n = node.to_destination()

    assert (node, get_destination()) in audio_graph.connections
    assert n is node


def test_audio_node_fan(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()
    node3 = InternalAudioNode()

    n = node1.fan(node2, node3)

    assert (node1, node2) in audio_graph.connections
    assert (node1, node3) in audio_graph.connections
    assert n is node1


def test_audio_node_chain(audio_graph):
    node1 = InternalAudioNode()
    node2 = InternalAudioNode()
    node3 = InternalAudioNode()

    n = node1.chain(node2, node3)

    assert (node1, node2) in audio_graph.connections
    assert (node2, node3) in audio_graph.connections
    assert n is node1
