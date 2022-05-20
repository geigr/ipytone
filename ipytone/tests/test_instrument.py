import pytest

from ipytone.core import Gain, Volume
from ipytone.envelope import AmplitudeEnvelope, FrequencyEnvelope
from ipytone.filter import Filter
from ipytone.instrument import Instrument, Monophonic, MonoSynth, NoiseSynth, Synth
from ipytone.source import Noise, OmniOscillator, Oscillator


def test_instrument():
    gain = Gain()
    attack_func = """
    // test
    this.getNode('gain').gain = 0; // test
    """
    release_func = """
    this.getNode('gain').gain = -20;
    """

    inst = Instrument(
        _internal_nodes={"gain": gain}, _trigger_attack=attack_func, _trigger_release=release_func
    )

    assert isinstance(inst.output, Volume)
    assert inst.input is None

    assert inst.output.volume.value == 0

    assert inst._trigger_attack == "this.getNode('gain').gain = 0;"
    assert inst._trigger_release == "this.getNode('gain').gain = -20;"

    assert inst._internal_nodes["gain"] is gain

    i = inst.dispose()
    assert i is inst
    assert inst.disposed is True
    assert gain.disposed is True


@pytest.mark.parametrize(
    "method,js_method,kwargs",
    [
        ("trigger_attack", "triggerAttack", {"note": "C3", "time": None, "velocity": 1}),
        ("trigger_release", "triggerRelease", {"time": None}),
        (
            "trigger_attack_release",
            "triggerAttackRelease",
            {"note": "C3", "duration": 1, "time": None, "velocity": 1},
        ),
    ],
)
def test_enveloppe_trigger(mocker, method, js_method, kwargs):
    inst = Instrument()
    mocker.patch.object(inst, "send")

    args = {k: {"value": v, "eval": False} for k, v in kwargs.items()}
    expected = {"event": "trigger", "method": js_method, "args": args, "arg_keys": list(kwargs)}

    i = getattr(inst, method)(**kwargs)
    assert i is inst
    inst.send.assert_called_once_with(expected)


def test_monophonic():
    oscillator = Oscillator()
    envelope = AmplitudeEnvelope()
    get_level_func = """
    return this.getNode('envelope').getValueAtTime(time);
    """

    mono = Monophonic(
        _internal_nodes={"oscillator": oscillator, "envelope": envelope},
        _get_level_at_time=get_level_func,
        _frequency=oscillator.frequency,
        _detune=oscillator.detune,
    )

    assert mono.frequency is oscillator.frequency
    assert mono.detune is oscillator.detune
    assert mono.portamento == 0

    assert mono._get_level_at_time == "return this.getNode('envelope').getValueAtTime(time);"


def test_synth(audio_graph):
    synth = Synth()

    assert isinstance(synth.oscillator, OmniOscillator)
    assert synth.oscillator.type == "triangle"

    assert isinstance(synth.envelope, AmplitudeEnvelope)
    assert synth.envelope.attack == 0.005
    assert synth.envelope.decay == 0.1
    assert synth.envelope.sustain == 0.3
    assert synth.envelope.release == 1

    assert (synth.oscillator, synth.envelope, 0, 0) in audio_graph.connections
    assert (synth.envelope, synth.output, 0, 0) in audio_graph.connections


def test_monosynth(audio_graph):
    synth = MonoSynth()

    assert isinstance(synth.oscillator, OmniOscillator)
    assert synth.oscillator.type == "sawtooth"

    assert isinstance(synth.envelope, AmplitudeEnvelope)
    assert synth.envelope.attack == 0.005
    assert synth.envelope.decay == 0.1
    assert synth.envelope.sustain == 0.9
    assert synth.envelope.release == 1

    assert isinstance(synth.filter, Filter)
    assert synth.filter.type == "lowpass"
    assert synth.filter.rolloff == -12
    assert synth.filter.q.value == 1

    assert isinstance(synth.filter_envelope, FrequencyEnvelope)
    assert synth.filter_envelope.attack == 0.6
    assert synth.filter_envelope.decay == 0.2
    assert synth.filter_envelope.sustain == 0.5
    assert synth.filter_envelope.release == 2
    assert synth.filter_envelope.base_frequency == 200
    assert synth.filter_envelope.octaves == 3
    assert synth.filter_envelope.exponent == 2

    assert (synth.oscillator, synth.filter, 0, 0) in audio_graph.connections
    assert (synth.filter, synth.envelope, 0, 0) in audio_graph.connections
    assert (synth.envelope, synth.output, 0, 0) in audio_graph.connections
    assert (synth.filter_envelope, synth.filter.frequency, 0, 0) in audio_graph.connections


def test_noisesynth(audio_graph):
    synth = NoiseSynth()

    assert isinstance(synth.noise, Noise)
    assert synth.noise.type == "white"

    assert isinstance(synth.envelope, AmplitudeEnvelope)
    assert synth.envelope.decay == 0.1
    assert synth.envelope.sustain == 0
