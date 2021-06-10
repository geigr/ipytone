import numpy as np
import pytest
from traitlets import TraitError

from ipytone import AudioBuffer, Noise, Player, Players, Volume
from ipytone.source import (
    LFO,
    AMOscillator,
    FatOscillator,
    FMOscillator,
    OmniOscillator,
    Oscillator,
    PulseOscillator,
    PWMOscillator,
    Source,
)


def test_source(mocker):
    node = Source()
    mocker.patch.object(node, "send")

    assert node.mute is False
    assert isinstance(node.output, Volume)
    assert node.volume is node.output.volume

    n = node.start()
    assert n is node
    node.send.assert_called_with(
        {
            "event": "trigger",
            "method": "start",
            "args": {
                "time": {"value": None, "eval": False},
                "offset": {"value": None, "eval": False},
                "duration": {"value": None, "eval": False},
            },
            "arg_keys": ["time", "offset", "duration"],
        }
    )

    n = node.stop()
    node.send.assert_called_with(
        {
            "event": "trigger",
            "method": "stop",
            "args": {"time": {"value": None, "eval": False}},
            "arg_keys": ["time"],
        }
    )
    assert n is node

    n = node.sync()
    node.send.assert_called_with({"event": "trigger", "method": "sync", "args": {}, "arg_keys": []})
    assert n is node

    n = node.unsync()
    node.send.assert_called_with(
        {"event": "trigger", "method": "unsync", "args": {}, "arg_keys": []}
    )
    assert n is node


def test_lfo(mocker):
    lfo = LFO()
    mocker.patch.object(lfo, "send")

    assert lfo.frequency.value == "4n"
    assert lfo.amplitude.value == 1
    assert lfo.min_out == lfo.output.min_out == 0
    assert lfo.max_out == lfo.output.max_out == 1
    assert lfo.type == "sine"
    assert lfo.phase == 0
    assert lfo.partials == []
    assert lfo.units == "number"
    assert lfo.convert is True

    lfo.min_out = 0.5
    assert lfo.output.min_out == 0.5
    lfo.min_out = 0.9
    assert lfo.output.min_out == 0.9

    n = lfo.start()
    assert n is lfo
    lfo.send.assert_called_with(
        {
            "event": "trigger",
            "method": "start",
            "args": {
                "time": {"value": None, "eval": False},
            },
            "arg_keys": ["time"],
        }
    )

    n = lfo.stop()
    lfo.send.assert_called_with(
        {
            "event": "trigger",
            "method": "stop",
            "args": {"time": {"value": None, "eval": False}},
            "arg_keys": ["time"],
        }
    )
    assert n is lfo

    n = lfo.sync()
    lfo.send.assert_called_with({"event": "trigger", "method": "sync", "args": {}, "arg_keys": []})
    assert n is lfo

    n = lfo.unsync()
    lfo.send.assert_called_with(
        {"event": "trigger", "method": "unsync", "args": {}, "arg_keys": []}
    )
    assert n is lfo

    n = lfo.dispose()
    assert n is lfo
    assert lfo.frequency.disposed is True
    assert lfo.amplitude.disposed is True


def test_oscillator():
    osc = Oscillator()

    assert osc.type == "sine"
    assert osc.base_type == "sine"
    assert osc.partial_count == 0
    assert osc.partials == []
    assert osc.frequency.value == 440
    assert osc.frequency.units == "frequency"
    assert osc.detune.value == 0
    assert osc.detune.units == "cents"
    assert osc.phase == 0
    assert osc.sync_array is False
    assert osc.array_length == 1024

    osc.type = "square2"
    assert osc.base_type == "square"
    assert osc.partial_count == 2

    osc.base_type = "triangle"
    assert osc.type == "triangle2"

    osc.partial_count = 3
    assert osc.type == "triangle3"
    osc.partial_count = 0
    assert osc.type == "triangle"

    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        osc.type = "not a good oscillator wave"

    osc.partials = [1.0, 0.5, 0.3]
    assert osc.partials == [1.0, 0.5, 0.3]
    assert osc.type == "custom"
    assert osc.partial_count == 3

    osc.partial_count = 2
    assert osc.partials == [1.0, 0.5]

    # test dispose
    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.frequency.disposed is True
    assert osc.detune.disposed is True

    with pytest.raises(ValueError, match="Partials values must be given.*"):
        Oscillator(type="custom", partials=None)

    with pytest.raises(ValueError, match="Partial count already set.*"):
        Oscillator(type="sine8", partial_count=2)

    osc2 = Oscillator(type="custom", partials=[1.0, 0.5, 0.3], partial_count=2)
    assert osc2.partials == [1.0, 0.5]

    osc3 = Oscillator(type="sine", partial_count=2)
    assert osc3.type == "sine2"

    osc4 = Oscillator(type="sine", partial_count=0)
    assert osc4.type == "sine"


def test_am_oscillator():
    osc = AMOscillator()

    assert osc.modulation_type == "square"
    assert osc.harmonicity.value == 1

    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        osc.modulation_type = "not a valid oscillator type"

    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.harmonicity.disposed is True


def test_fm_oscillator():
    osc = FMOscillator()

    assert osc.modulation_type == "square"
    assert osc.harmonicity.value == 1
    assert osc.modulation_index.value == 2

    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        osc.modulation_type = "not a valid oscillator type"

    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.harmonicity.disposed is True
    assert osc.modulation_index.disposed is True


def test_fat_oscillator():
    osc = FatOscillator()

    assert osc.spread == 20
    assert osc.count == 3


def test_pulse_oscillator():
    osc = PulseOscillator()

    assert osc.type == "pulse"
    assert osc.partial_count == 0
    assert osc.partials == []
    assert osc.width.units == "audioRange"
    assert osc.width.value == 0.2

    with pytest.raises(TraitError, match=".*only supports the 'pulse'.*"):
        osc.type = "sine"

    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.width.disposed is True


def test_pwm_oscillator():
    osc = PWMOscillator()

    assert osc.type == "pwm"
    assert osc.partial_count == 0
    assert osc.partials == []
    assert osc.modulation_frequency.units == "frequency"
    assert osc.modulation_frequency.value == 0.4

    with pytest.raises(TraitError, match=".*only supports the 'pwm'.*"):
        osc.type = "sine"

    n = osc.dispose()
    assert n is osc
    assert osc.disposed is True
    assert osc.modulation_frequency.disposed is True


def test_omni_oscillator():
    osc = OmniOscillator()

    assert osc.type == "sine"
    assert osc.partial_count == 0
    assert osc.partials == []

    osc.type = "amsine"
    assert osc.modulation_type == "square"
    assert osc.harmonicity.value == 1
    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        osc.modulation_type = "not a valid oscillator type"

    osc.type = "fmsine"
    assert osc.harmonicity.value == 1

    osc.type = "pulse"
    assert osc.source_type == "pulse"
    assert osc.base_type == "pulse"
    assert osc.partial_count == 0
    with pytest.raises(NotImplementedError):
        osc.partial_count = 1
    assert osc.partials == []
    with pytest.raises(NotImplementedError):
        osc.partials = [1, 0.5, 0.2]
    assert osc.width.units == "audioRange"
    assert osc.width.value == 0.2

    osc.type = "pwm"
    assert osc.source_type == "pwm"
    assert osc.base_type == "pwm"
    assert osc.partial_count == 0
    with pytest.raises(NotImplementedError):
        osc.partial_count = 1
    assert osc.partials == []
    with pytest.raises(NotImplementedError):
        osc.partials = [1, 0.5, 0.2]
    assert osc.modulation_frequency.units == "frequency"
    assert osc.modulation_frequency.value == 0.4

    osc.source_type = "oscillator"
    # from pulse/pwm: back to sine by default
    assert osc.type == "sine"
    osc.source_type = "am"
    assert osc.type == "amsine"
    osc.source_type = "fm"
    assert osc.type == "fmsine"
    osc.source_type = "fat"
    assert osc.type == "fatsine"
    osc.type = "sine"
    assert osc.source_type == "oscillator"
    osc.source_type = "pulse"
    assert osc.type == "pulse"

    assert osc.base_type == "pulse"
    osc.base_type = "sine"
    assert osc.type == "sine"
    osc.type = "amsine"
    assert osc.base_type == "sine"
    osc.base_type = "square"
    assert osc.type == "amsquare"

    osc.partial_count = 3
    assert osc.type == "amsquare3"
    osc.partial_count = 0
    assert osc.type == "amsquare"

    osc.partials = [1.0, 0.5, 0.4]
    assert osc.type == "amcustom"
    assert osc.partial_count == 3
    osc.partial_count = 2
    assert osc.partials == [1.0, 0.5]


@pytest.mark.parametrize(
    "type,active_props",
    [
        ("sine", []),
        ("fatsine", []),
        ("amsine", ["harmonicity"]),
        ("fmsine", ["harmonicity", "modulation_index"]),
        ("pulse", ["width"]),
        ("pwm", ["modulation_frequency"]),
    ],
)
def test_omni_oscillator_properties(type, active_props):
    all_props = {"harmonicity", "modulation_index", "width", "modulation_frequency"}
    active_props = set(active_props)

    osc = OmniOscillator(type=type)

    for prop in all_props.intersection(active_props):
        assert getattr(osc, prop) is not None

    for prop in all_props.difference(active_props):
        assert getattr(osc, prop) is None

    osc.dispose()

    for prop in active_props:
        assert getattr(osc, prop).disposed is True


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


def test_players():
    players = Players({"A": "some_url", "B": "another_url"})

    assert isinstance(players.output, Volume)
    assert players.volume is players.output.volume
    assert players.mute is False
    assert players.loaded is False
    assert players.fade_in == 0
    assert players.fade_out == 0

    a = players.get_player("A")
    assert isinstance(a, Player)
    # test cache
    a = players.get_player("A")
    assert isinstance(a, Player)
    assert a.buffer.buffer_url == "some_url"

    b = players.get_player("B")
    assert b.buffer.buffer_url == "another_url"

    a.start()
    b.start()
    p = players.stop_all()
    assert p is players

    players.fade_in = 1
    assert a.fade_in == b.fade_in == players.fade_in == 1
    players.fade_out = 2
    assert a.fade_out == b.fade_out == players.fade_out == 2

    p = players.add("C", "a_3rd_url")
    assert p is players
    c = players.get_player("C")
    assert c.buffer.buffer_url == "a_3rd_url"

    with pytest.raises(ValueError, match=r"A buffer with name.*"):
        players.add("C", "whatever")

    p = players.dispose()
    assert p is players
    assert a.disposed is b.disposed is c.disposed is True
    assert players._buffers.disposed is True
