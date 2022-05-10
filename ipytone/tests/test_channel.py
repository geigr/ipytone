from ipytone.base import NativeAudioNode
from ipytone.channel import Channel, CrossFade, Merge, Mono, Panner, PanVol, Solo, Split
from ipytone.core import Gain, Param, Volume
from ipytone.signal import Signal


def test_cross_fade():
    cross_fade = CrossFade()

    assert isinstance(cross_fade.a, Gain)
    assert cross_fade.a.gain.value == 0
    assert isinstance(cross_fade.b, Gain)
    assert cross_fade.b.gain.value == 0
    assert isinstance(cross_fade.output, Gain)
    assert isinstance(cross_fade.fade, Signal)
    assert cross_fade.fade.units == "normalRange"
    assert cross_fade.fade.value == 0.5

    s = cross_fade.dispose()
    assert s is cross_fade
    assert cross_fade.disposed is True
    assert cross_fade.a.disposed is True
    assert cross_fade.b.disposed is True
    assert cross_fade.fade.disposed is True


def test_panner():
    panner = Panner()

    assert isinstance(panner.pan, Param)
    assert panner.pan.value == 0
    assert panner.pan.units == "audioRange"
    assert panner.channel_count == 1
    assert panner.channel_count_mode == "explicit"

    p = panner.dispose()
    assert p is panner
    assert panner.disposed is True
    assert panner.pan.disposed is True


def test_panvol():
    panvol = PanVol()

    assert isinstance(panvol.input, Panner)
    assert isinstance(panvol.output, Volume)

    assert panvol.channel_count == 1
    assert panvol.channel_count_mode == "explicit"

    assert panvol.pan.value == 0
    assert panvol.pan is panvol.input.pan

    assert panvol.volume.value == 0
    assert panvol.volume is panvol.output.volume

    assert panvol.mute is False
    panvol.mute = True
    assert panvol.output.mute is True


def test_solo():
    solo = Solo()

    assert solo.solo is False
    assert solo.muted is False
    assert isinstance(solo.input, Gain)
    assert isinstance(solo.output, Gain)
    assert solo.input is solo.output


def test_channel():
    chan = Channel()

    assert chan.pan.value == 0
    assert chan.volume.value == 0
    assert chan.muted is False
    assert chan.channel_count == 1
    assert chan.channel_count_mode == "explicit"

    assert chan.pan is chan.output.pan
    assert chan.volume is chan.output.volume
    assert chan.solo is chan.input.solo

    # can't test solo -> muted without JS.
    chan.mute = True
    assert chan.muted is True


def test_channel_buses(audio_graph):
    chan1 = Channel()
    chan2 = Channel()

    sender = chan1.send("test", volume=-10)
    assert isinstance(sender, Gain)
    assert sender.gain.value == -10
    assert sender.gain.units == "decibels"

    chan2.receive("test")

    # check connections
    assert (sender, Channel._buses["test"], 0, 0) in audio_graph.connections
    assert (Channel._buses["test"], chan2.widget, 0, 0) in audio_graph.connections


def test_merge():
    merge = Merge()

    assert merge.channels == 2
    assert merge.input is merge.output
    assert isinstance(merge.output, NativeAudioNode)
    assert merge.output.type == "ChannelMergerNode"

    assert repr(merge) == "Merge(channels=2)"


def test_split():
    split = Split()

    assert split.channels == 2
    assert split.input is split.output
    assert isinstance(split.output, NativeAudioNode)
    assert split.output.type == "ChannelSplitterNode"

    assert repr(split) == "Split(channels=2)"


def test_mono(audio_graph):
    mono = Mono()

    assert isinstance(mono.input, Gain)
    assert isinstance(mono.output, Merge)

    assert (mono.input, mono.output, 0, 0) in audio_graph.connections
    assert (mono.input, mono.output, 0, 1) in audio_graph.connections
