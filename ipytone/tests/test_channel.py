from ipytone import CrossFade, Gain, Panner, Param, Signal


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
