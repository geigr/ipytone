import pytest

from ipytone.base import AudioNode
from ipytone.core import get_destination
from ipytone.source import Source


def test_audio_node_creation():
    node = AudioNode(name="test")

    assert node.input == []
    assert node.output == []
    assert repr(node) == "AudioNode(name='test')"


def test_audio_node_connect():
    node1 = AudioNode()
    node2 = AudioNode()

    n = node1.connect(node2)

    assert node1.output == [node2]
    assert node2.input == [node1]
    assert n is node1

    n = node1.disconnect(node2)

    assert node1.output == []
    assert node2.input == []
    assert n is node1


@pytest.mark.parametrize("func", [AudioNode.connect, AudioNode.fan])
def test_audio_node_connect_error(func):
    node1 = AudioNode()
    src = Source()

    with pytest.raises(ValueError, match="cannot connect an audio node to itself"):
        func(node1, node1)

    with pytest.raises(ValueError, match="cannot connect to source.*"):
        func(node1, src)

    with pytest.raises(ValueError, match=".*must be AudioNode.*"):
        func(node1, "not an audio node")


def test_audio_node_to_destination():
    node = AudioNode()

    n = node.to_destination()

    assert node.output == [get_destination()]
    assert get_destination().input == [node]
    assert n is node


def test_audio_node_fan():
    node1 = AudioNode()
    node2 = AudioNode()
    node3 = AudioNode()

    n = node1.fan(node2, node3)

    assert set(node1.output) == set([node2, node3])
    assert node2.input == [node1]
    assert node3.input == [node1]
    assert n is node1


def test_audio_node_chain():
    node1 = AudioNode()
    node2 = AudioNode()
    node3 = AudioNode()

    n = node1.chain(node2, node3)

    assert node1.output == [node2]
    assert node2.output == [node3]
    assert node2.input == [node1]
    assert node3.input == [node2]
    assert n is node1
