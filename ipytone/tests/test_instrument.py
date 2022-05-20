import pytest

from ipytone.core import Gain, Volume
from ipytone.envelope import AmplitudeEnvelope, FrequencyEnvelope
from ipytone.filter import Filter, LowpassCombFilter
from ipytone.instrument import (
    DuoSynth,
    Instrument,
    MembraneSynth,
    Monophonic,
    MonoSynth,
    NoiseSynth,
    PluckSynth,
    Synth,
)
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


def test_plucksynth(audio_graph):
    synth = PluckSynth()

    assert synth.attack_noise == 1
    assert synth.dampening == 4000
    assert synth.resonance == 0.7
    assert synth.release == 1

    assert isinstance(synth._noise, Noise)
    assert synth._noise.type == "pink"
    assert isinstance(synth._lfcf, LowpassCombFilter)
    assert synth._lfcf.dampening == synth.dampening
    assert synth._lfcf.resonance.value == synth.resonance

    assert (synth._noise, synth._lfcf.widget, 0, 0) in audio_graph.connections
    assert (synth._lfcf.widget, synth.output, 0, 0) in audio_graph.connections

    s = synth.dispose()
    assert s is synth
    assert synth._lfcf.disposed is True


def test_duosynth(audio_graph):
    synth = DuoSynth()

    assert isinstance(synth.voice0, MonoSynth)
    assert isinstance(synth.voice1, MonoSynth)
    for voice in (synth.voice0, synth.voice1):
        for env in (voice.envelope, voice.filter_envelope):
            assert env.attack == 0.01
            assert env.decay == 0
            assert env.sustain == 1
            assert env.release == 0.5

    assert synth.harmonicity.value == 1.5
    assert synth.vibrato_rate.value == 5
    assert synth.vibrato_amount.value == 0.5
    assert synth.frequency.value == 440
    assert synth.detune.value == 0

    assert (synth.frequency, synth.voice0.frequency, 0, 0) in audio_graph.connections
    assert (synth.frequency, synth._harmonicity, 0, 0) in audio_graph.connections
    assert (synth._harmonicity, synth.voice1.frequency, 0, 0) in audio_graph.connections

    assert (synth._vibrato, synth._vibrato_gain, 0, 0) in audio_graph.connections
    assert (synth._vibrato_gain, synth.voice0.detune, 0, 0) in audio_graph.connections
    assert (synth._vibrato_gain, synth.voice1.detune, 0, 0) in audio_graph.connections

    assert (synth.detune, synth.voice0.detune, 0, 0) in audio_graph.connections
    assert (synth.detune, synth.voice1.detune, 0, 0) in audio_graph.connections

    assert (synth.voice0, synth.output, 0, 0) in audio_graph.connections
    assert (synth.voice1, synth.output, 0, 0) in audio_graph.connections

    s = synth.dispose()
    assert s is synth
    assert synth.voice0.disposed is True
    assert synth.voice1.disposed is True
    assert synth._harmonicity.disposed is True
    assert synth._vibrato.disposed is True
    assert synth._vibrato_gain.disposed is True
    assert synth.frequency.disposed is True
    assert synth.detune.disposed is True


def test_membranesynth():
    synth = MembraneSynth()

    assert synth.oscillator.type == "sine"
    assert synth.envelope.attack == 0.001
    assert synth.envelope.attack_curve == "exponential"
    assert synth.envelope.decay == 0.4
    assert synth.envelope.sustain == 0.01
    assert synth.envelope.release == 1.4

    assert synth.pitch_decay == 0.05
    assert synth.octaves == 8

    s = synth.dispose()
    assert s is synth
    assert synth._pitch_decay.disposed is True
    assert synth._octaves.disposed is True
