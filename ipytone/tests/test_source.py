import numpy as np
import pytest
from traitlets import TraitError

from ipytone import AudioBuffer, Noise, Oscillator, Player, Volume
from ipytone.source import Source


def test_source():
    node = Source()

    assert node.mute is False
    assert node.state == "stopped"
    assert isinstance(node.output, Volume)
    assert node.volume is node.output.volume

    n = node.start()
    assert node.state == "started"
    assert n is node

    n = node.stop()
    assert node.state == "stopped"
    assert n is node


def test_oscillator():
    osc = Oscillator()

    assert osc.type == "sine"
    assert osc.frequency.value == 440
    assert osc.frequency.units == "frequency"
    assert osc.detune.value == 0
    assert osc.detune.units == "cents"

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        osc.type = "not a good oscillator wave"

    # test dispose
    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.frequency.disposed is True
    assert osc.detune.disposed is True


def test_noise():
    noise = Noise()

    assert noise.type == "white"
    assert noise.fade_in == 0
    assert noise.fade_out == 0

    # just test that the following types are valid
    for typ in ["pink", "white", "brown"]:
        noise.type = typ

    with pytest.raises(TraitError):
        noise.type = "not a valid noise type"


def test_player():
    player = Player("some_url")

    assert player.buffer.buffer_url == "some_url"
    assert player.autostart is False
    assert player.loop is False
    assert player.loop_start == 0
    assert player.loop_end == 0
    assert player.fade_in == 0
    assert player.fade_out == 0
    assert player.reverse is player.buffer.reverse is False
    assert player.playback_rate == 1
    assert player.loaded is player.buffer.loaded is False

    with pytest.raises(TraitError, match="Loop time out of audio buffer bounds"):
        player.loop_start = -1

    # doesn't raise as buffer is not loaded (no front-end)
    player.set_loop_points(0, 1)
    assert player.loop_end == 1

    player.dispose()
    assert player.disposed is True
    assert player.buffer.disposed is True

    buf = AudioBuffer(np.random.uniform(low=-1, high=1, size=100))
    player2 = Player(buf)

    assert player2.buffer is buf
