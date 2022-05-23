import pytest

from ipytone.core import Gain, Volume
from ipytone.envelope import AmplitudeEnvelope, FrequencyEnvelope
from ipytone.filter import Filter, LowpassCombFilter
from ipytone.instrument import (
    AMSynth,
    DuoSynth,
    FMSynth,
    Instrument,
    MembraneSynth,
    ModulationSynth,
    Monophonic,
    MonoSynth,
    NoiseSynth,
    PluckSynth,
    PolySynth,
    Sampler,
    Synth,
)
from ipytone.source import Noise, OmniOscillator, Oscillator


class DummyInstrument(Instrument):
    def __init__(self):
        self.gain = Gain()
        super().__init__()

    def _get_internal_nodes(self):
        return {"gain": self.gain}

    def _attack_func(self):
        return """
        // test
        this.getNode('gain').gain = 0; // test
        """

    def _release_func(self):
        return """
        this.getNode('gain').gain = -20;
        """


def test_instrument():

    inst = DummyInstrument()

    assert isinstance(inst.output, Volume)
    assert inst.input is None

    assert inst.output.volume.value == 0

    assert inst._trigger_attack == "this.getNode('gain').gain = 0;"
    assert inst._trigger_release == "this.getNode('gain').gain = -20;"

    assert inst._internal_nodes["gain"] is inst.gain

    i = inst.dispose()
    assert i is inst
    assert inst.disposed is True
    assert inst.gain.disposed is True


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
def test_instrument_trigger(mocker, method, js_method, kwargs):
    inst = DummyInstrument()
    mocker.patch.object(inst, "send")

    args = {k: {"value": v, "eval": False} for k, v in kwargs.items()}
    expected = {"event": "trigger", "method": js_method, "args": args, "arg_keys": list(kwargs)}

    i = getattr(inst, method)(**kwargs)
    assert i is inst
    inst.send.assert_called_once_with(expected)


class DummyMonophonic(Monophonic):
    def __init__(self):
        self.oscillator = Oscillator()
        self.envelope = AmplitudeEnvelope()
        super().__init__()

    def _get_internal_nodes(self):
        return {"oscillator": self.oscillator, "envelope": self.envelope}

    def _attack_func(self):
        return """
        // test
        this.getNode('gain').gain = 0; // test
        """

    def _release_func(self):
        return """
        this.getNode('gain').gain = -20;
        """

    def _get_level_at_time_func(self):
        return """
        return this.getNode('envelope').getValueAtTime(time);
        """


def test_monophonic():
    mono = DummyMonophonic()

    assert mono.frequency is mono.oscillator.frequency
    assert mono.detune is mono.oscillator.detune
    assert mono.portamento == 0

    assert mono._get_level_at_time == "return this.getNode('envelope').getValueAtTime(time);"


def test_synth():
    synth = Synth()

    assert isinstance(synth.oscillator, OmniOscillator)
    assert synth.oscillator.type == "triangle"

    assert isinstance(synth.envelope, AmplitudeEnvelope)
    assert synth.envelope.attack == 0.005
    assert synth.envelope.decay == 0.1
    assert synth.envelope.sustain == 0.3
    assert synth.envelope.release == 1


def test_monosynth():
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


def test_noisesynth():
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


def test_duosynth():
    synth = DuoSynth()

    assert isinstance(synth.voice0, MonoSynth)
    assert isinstance(synth.voice1, MonoSynth)
    for voice in (synth.voice0, synth.voice1):
        for env in (voice.envelope, voice.filter_envelope):
            assert env.attack == 0.01
            assert env.decay == 0
            assert env.sustain == 1
            assert env.release == 0.5

    assert synth.harmonicity.factor.value == 1.5
    assert synth.vibrato_rate.value == 5
    assert synth.vibrato_amount.value == 0.5
    assert synth.frequency.value == 440
    assert synth.detune.value == 0

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


def test_modulationsynth():
    synth = ModulationSynth()

    assert isinstance(synth._carrier, Synth)
    assert isinstance(synth._modulator, Synth)

    assert synth.oscillator is synth._carrier.oscillator
    assert synth.envelope is synth._carrier.envelope
    assert synth.oscillator.type == "sine"
    assert synth.envelope.attack == 0.01
    assert synth.envelope.decay == 0.01
    assert synth.envelope.sustain == 1
    assert synth.envelope.release == 0.5

    assert synth.modulation is synth._modulator.oscillator
    assert synth.modulation_envelope is synth._modulator.envelope
    assert synth.modulation.type == "square"
    assert synth.modulation_envelope.attack == 0.5
    assert synth.modulation_envelope.decay == 0
    assert synth.modulation_envelope.sustain == 1
    assert synth.modulation_envelope.release == 0.5

    assert synth.harmonicity.factor.value == 3
    assert synth.harmonicity.factor.min_value == 0

    assert synth.frequency.value == 440
    assert synth.detune.value == 0

    assert synth._modulation_node.gain.value == 0

    s = synth.dispose()
    assert s is synth
    assert synth._carrier.disposed is True
    assert synth._modulator.disposed is True
    assert synth.frequency.disposed is True
    assert synth.detune.disposed is True
    assert synth._harmonicity.disposed is True
    assert synth._modulation_node.disposed is True


def test_fmsynth():
    synth = FMSynth()

    assert synth.modulation_index.factor.value == 10

    s = synth.dispose()
    assert s is synth
    assert synth.modulation_index.disposed is True


def test_amsynth():
    synth = AMSynth()

    s = synth.dispose()
    assert s is synth
    assert synth._modulation_scale.disposed is True


def test_polysynth():
    synth = PolySynth()

    assert synth.max_polyphony == 32

    assert isinstance(synth.voice, Synth)
    assert synth.voice is synth._dummy_voice
    # dummy_voice should be already disposed (not used directly)
    assert synth.voice.disposed is True

    assert isinstance(synth.output, Volume)
    assert synth.input is None

    assert synth.output.volume.value == 0


@pytest.mark.parametrize(
    "method,js_method,kwargs",
    [
        ("trigger_attack", "triggerAttack", {"notes": ["C3", "C4"], "time": None, "velocity": 1}),
        ("trigger_release", "triggerRelease", {"time": None}),
        (
            "trigger_attack_release",
            "triggerAttackRelease",
            {"notes": ["C3", "C4"], "duration": [1, 2], "time": None, "velocity": 1},
        ),
        ("release_all", "releaseAll", {"time": None}),
    ],
)
def test_polysynth_trigger(mocker, method, js_method, kwargs):
    inst = PolySynth()
    mocker.patch.object(inst, "send")

    args = {k: {"value": v, "eval": False} for k, v in kwargs.items()}
    expected = {"event": "trigger", "method": js_method, "args": args, "arg_keys": list(kwargs)}

    i = getattr(inst, method)(**kwargs)
    assert i is inst
    inst.send.assert_called_once_with(expected)


def test_sampler():
    sampler = Sampler({"A1": "a1.wav", "A2": "a2.wav"})

    assert isinstance(sampler.output, Volume)
    assert sampler.volume.value == 0
    assert sampler.loaded is False
    assert sampler.attack == 0
    assert sampler.release == 1
    assert sampler.curve == "exponential"

    assert "A1" in sampler._buffers.buffers
    assert "A2" in sampler._buffers.buffers

    s = sampler.add("A3", "a3.mp3")
    assert s is sampler
    assert "A3" in sampler._buffers.buffers

    with pytest.raises(ValueError, match=r"A buffer with name.*"):
        sampler.add("A3", "a3_alt.mp3")

    s = sampler.dispose()
    assert s is sampler
    assert sampler._buffers.disposed is True


@pytest.mark.parametrize(
    "method,js_method,kwargs",
    [
        ("trigger_attack", "triggerAttack", {"notes": ["C3", "C4"], "time": None, "velocity": 1}),
        ("trigger_release", "triggerRelease", {"time": None}),
        (
            "trigger_attack_release",
            "triggerAttackRelease",
            {"notes": ["C3", "C4"], "duration": [1, 2], "time": None, "velocity": 1},
        ),
        ("release_all", "releaseAll", {"time": None}),
    ],
)
def test_sampler_trigger(mocker, method, js_method, kwargs):
    sampler = Sampler({})
    mocker.patch.object(sampler, "send")

    args = {k: {"value": v, "eval": False} for k, v in kwargs.items()}
    expected = {"event": "trigger", "method": js_method, "args": args, "arg_keys": list(kwargs)}

    i = getattr(sampler, method)(**kwargs)
    assert i is sampler
    sampler.send.assert_called_once_with(expected)
