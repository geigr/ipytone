#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.

import pytest
from traitlets.traitlets import TraitError

from ipytone import get_destination, Oscillator
from ipytone.ipytone import AudioNode, Destination, Source


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


def test_source():
    node = Source()

    assert node.mute is False
    assert node.state == "stopped"
    assert node.volume == -16

    n = node.start()
    assert node.state == "started"
    assert n is node

    n = node.stop()
    assert node.state == "stopped"
    assert n is node


def test_destination():
    dest = get_destination()

    assert dest.mute is False
    assert dest.volume == -16

    # test singleton
    dest1 = Destination()
    dest2 = Destination()

    assert dest1 == dest2 == get_destination()


def test_oscillator():
    osc = Oscillator()

    assert osc.type == "sine"
    assert osc.frequency == 440
    assert osc.detune == 0
    assert osc.volume == -16

    # just test that the following types are valid
    for wave in ["sine", "square", "sawtooth", "triangle"]:
        for pcount in range(2):
            osc.type = wave + str(pcount)

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        osc.type = "not a good oscillator wave"
