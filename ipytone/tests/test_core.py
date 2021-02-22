import pytest

from ipytone.core import Destination, InternalAudioNode, InternalNode, Param, get_destination


def test_internal_node():
    node = InternalNode(tone_class="test")

    assert node.number_of_inputs == 1
    assert node.number_of_outputs == 1
    assert repr(node) == "InternalNode(tone_class='test')"


def test_internal_audio_node():
    node = InternalAudioNode(tone_class="test")

    assert node.number_of_inputs == 1
    assert node.number_of_outputs == 1
    assert repr(node) == "InternalAudioNode(tone_class='test')"


def test_destination():
    dest = get_destination()

    assert dest.mute is False
    assert dest.volume == -16
    assert isinstance(dest.input, InternalAudioNode)
    assert isinstance(dest.output, InternalAudioNode)

    # test singleton
    dest1 = Destination()
    dest2 = Destination()

    assert dest1 == dest2 == get_destination()


def test_audio_graph(audio_graph):
    src = InternalAudioNode()
    dest = InternalAudioNode()
    param = Param()

    audio_graph.connect(src, dest, sync=False)
    assert (src, dest) not in audio_graph.connections
    audio_graph.sync_connections()
    assert (src, dest) in audio_graph.connections

    audio_graph.connect(src, param)
    assert (src, param) in audio_graph.connections

    assert audio_graph.nodes == list({src, dest, param})
    assert audio_graph.connections == [(src, dest), (src, param)]

    audio_graph.disconnect(src, dest, sync=False)
    assert (src, dest) in audio_graph.connections
    audio_graph.sync_connections()
    assert (src, dest) not in audio_graph.connections

    with pytest.raises(ValueError, match=".*not connected to.*"):
        audio_graph.disconnect(src, dest)

    with pytest.raises(ValueError, match="src_node must be an AudioNode object"):
        audio_graph.connect(param, dest)

    with pytest.raises(ValueError, match=".*dest_node must be.*"):
        audio_graph.connect(src, "not a node")

    src = InternalAudioNode()
    dest = InternalAudioNode(_n_inputs=0)
    with pytest.raises(ValueError, match="Cannot connect to audio source.*"):
        audio_graph.connect(src, dest)

    src = InternalAudioNode(_n_outputs=0)
    dest = InternalAudioNode()
    with pytest.raises(ValueError, match="Cannot connect from audio sink.*"):
        audio_graph.connect(src, dest)
