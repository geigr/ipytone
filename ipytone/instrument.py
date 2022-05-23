import re
from textwrap import dedent

from ipywidgets import widget_serialization
from traitlets import Dict, Enum, Float, Instance, Int, List, Unicode, validate

from .base import NodeWithContext
from .callback import add_or_send_event
from .core import AudioBuffers, AudioNode, Gain, Param, Volume
from .envelope import AmplitudeEnvelope, FrequencyEnvelope
from .filter import Filter, LowpassCombFilter
from .signal import AudioToGain, Multiply, Signal
from .source import LFO, Noise, OmniOscillator


def minify_js_func(func_str):
    # We could use https://github.com/rspivak/slimit but it's probably overkill.
    # remove indent
    func_str = dedent(func_str)
    # remove comments
    func_str = re.sub(r"//.*\n", "", func_str)
    # remove tabs, end-of-line
    func_str = re.sub(r"[\t\n]*", "", func_str)
    # remove leading / trailing spaces
    func_str = func_str.strip()

    return func_str


class Instrument(AudioNode):

    _model_name = Unicode("InstrumentModel").tag(sync=True)

    _internal_nodes = Dict(key_trait=Unicode(), value_trait=Instance(NodeWithContext)).tag(
        sync=True, **widget_serialization
    )
    _after_init = Unicode(help="constructor JS callback").tag(sync=True)
    _trigger_attack = Unicode(help="trigger attack JS callback").tag(sync=True)
    _trigger_release = Unicode(help="trigger release JS callback").tag(sync=True)

    def __init__(self, volume=0, **kwargs):
        output = Volume(volume=volume, _create_node=False)

        kw = {
            "_input": None,
            "_output": output,
            "_internal_nodes": self._get_internal_nodes(),
            "_trigger_attack": self._attack_func(),
            "_trigger_release": self._release_func(),
            "_after_init": self._after_init_func(),
        }
        kwargs.update(kw)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {}

    def _attack_func(self):
        raise NotImplementedError()

    def _release_func(self):
        raise NotImplementedError()

    def _after_init_func(self):
        return ""

    @validate("_trigger_attack")
    def _minify_trigger_attack(self, proposal):
        return minify_js_func(proposal["value"])

    @validate("_trigger_release")
    def _minify_trigger_release(self, proposal):
        return minify_js_func(proposal["value"])

    @validate("_after_init")
    def _minify_after_init(self, proposal):
        return minify_js_func(proposal["value"])

    @property
    def volume(self) -> Param:
        return self._output.volume

    def trigger_attack(self, note, time=None, velocity=1):
        args = {"note": note, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttack", self, args)
        return self

    def trigger_release(self, time=None):
        add_or_send_event("triggerRelease", self, {"time": time})
        return self

    def trigger_attack_release(self, note, duration, time=None, velocity=1):
        args = {"note": note, "duration": duration, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttackRelease", self, args)
        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            for node in self._internal_nodes.values():
                node.dispose()

        return self


class Monophonic(Instrument):

    _model_name = Unicode("MonophonicModel").tag(sync=True)

    _set_note = Unicode(help="set note JS callback").tag(sync=True)
    _get_level_at_time = Unicode(help="get level at time JS callback").tag(sync=True)

    _settings = Dict(key_trait=Unicode(), value_trait=List(Unicode())).tag(
        sync=True, **widget_serialization
    )

    portamento = Float(0, help="glide time between notes").tag(sync=True)

    def __init__(self, **kwargs):
        kw = {
            "_set_note": self._set_note_func(),
            "_get_level_at_time": self._get_level_at_time_func(),
            "_settings": self._get_settings(),
        }
        kwargs.update(kw)

        super().__init__(**kwargs)

    def _set_note_func(self):
        return ""

    def _get_level_at_time_func(self):
        raise NotImplementedError()

    def _get_settings(self):
        return {}

    @validate("_set_note")
    def _minify_set_note(self, proposal):
        return minify_js_func(proposal["value"])

    @validate("_get_level_at_time")
    def _minify_get_level_at_time(self, proposal):
        return minify_js_func(proposal["value"])

    @property
    def frequency(self) -> Signal:
        if "frequency" in self._internal_nodes:
            return self._internal_nodes["frequency"]
        else:
            return self._internal_nodes["oscillator"].frequency

    @property
    def detune(self) -> Signal:
        if "detune" in self._internal_nodes:
            return self._internal_nodes["detune"]
        else:
            return self._internal_nodes["oscillator"].detune


class Synth(Monophonic):
    """Simple synth build with an :class:`ipytone.OmniOscillator` routed through
    an :class:`ipytone.AmplitudeEnvelope`.

    """

    def __init__(self, **kwargs):
        self.oscillator = OmniOscillator(type="triangle")
        self.envelope = AmplitudeEnvelope(attack=0.005, decay=0.1, sustain=0.3, release=1)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {"oscillator": self.oscillator, "envelope": self.envelope}

    def _get_settings(self):
        return {
            "oscillator": ["type"],
            "envelope": ["attack", "decay", "sustain", "release"],
        }

    def _after_init_func(self):
        return """
        // make sure polyphonic voices get released
        this.getNode('oscillator').onstop = () => this.onsilence(this);
        // connections
        this.getNode('oscillator').chain(this.getNode('envelope'), this.output);
        """

    def _attack_func(self):
        return """
        const envelope = this.getNode('envelope');
        const oscillator = this.getNode('oscillator');
        // the envelopes
        envelope.triggerAttack(time, velocity);
        oscillator.start(time);
        // if there is no release portion, stop the oscillator
        if (envelope.sustain === 0) {
            const computedAttack = this.toSeconds(envelope.attack);
            const computedDecay = this.toSeconds(envelope.decay);
            oscillator.stop(time + computedAttack + computedDecay);
        }
        """

    def _release_func(self):
        return """
        const envelope = this.getNode('envelope');
        const oscillator = this.getNode('oscillator');
        envelope.triggerRelease(time);
        oscillator.stop(time + this.toSeconds(envelope.release));
        """

    def _get_level_at_time_func(self):
        return """
        time = this.toSeconds(time);
        return this.getNode('envelope').getValueAtTime(time);
        """


class MonoSynth(Monophonic):
    """Simple monophonic synth built with one :class:`~ipytone.OmniOscillator`,
    one :class:`~ipytone.Filter` and two envelopes (:class:`~ipytone.AmplitudeEnvelope`
    and :class:`~ipytone.FrequencyEnvelope`).

    """

    def __init__(self, **kwargs):
        self.oscillator = OmniOscillator(type="sawtooth")
        self.envelope = AmplitudeEnvelope(attack=0.005, decay=0.1, sustain=0.9, release=1)
        self.filter = Filter(type="lowpass", rolloff=-12, q=1)
        self.filter_envelope = FrequencyEnvelope(
            attack=0.6, decay=0.2, sustain=0.5, release=2, base_frequency=200, octaves=3, exponent=2
        )

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {
            "envelope": self.envelope,
            "filter_envelope": self.filter_envelope,
            "oscillator": self.oscillator,
            "filter": self.filter,
        }

    def _get_settings(self):
        return {
            "oscillator": ["type"],
            "envelope": ["attack", "decay", "sustain", "release"],
            "filter": ["type", "rolloff", "q"],
            "filter_envelope": ["attack", "decay", "sustain", "release"],
        }

    def _after_init_func(self):
        return """
        // make sure polyphonic voices get released
        this.getNode('oscillator').onstop = () => this.onsilence(this);
        // connections
        this.getNode('oscillator').chain(
          this.getNode('filter'), this.getNode('envelope'), this.output
        );
        this.getNode('filter_envelope').connect(this.getNode('filter').frequency);
        """

    def _attack_func(self):
        return """
        const envelope = this.getNode('envelope');
        const filterEnvelope = this.getNode('filter_envelope');
        const oscillator = this.getNode('oscillator');
        // the envelopes
        envelope.triggerAttack(time, velocity);
        filterEnvelope.triggerAttack(time);
        oscillator.start(time);
        // if there is no release portion, stop the oscillator
        if (envelope.sustain === 0) {
            const computedAttack = this.toSeconds(envelope.attack);
            const computedDecay = this.toSeconds(envelope.decay);
            oscillator.stop(time + computedAttack + computedDecay);
        }
        """

    def _release_func(self):
        return """
        const envelope = this.getNode('envelope');
        const filterEnvelope = this.getNode('filter_envelope');
        const oscillator = this.getNode('oscillator');
        envelope.triggerRelease(time);
        filterEnvelope.triggerRelease(time);
        oscillator.stop(time + this.toSeconds(envelope.release));
        """

    def _get_level_at_time_func(self):
        return """
        time = this.toSeconds(time);
        return this.getNode('envelope').getValueAtTime(time);
        """


class NoiseSynth(Instrument):
    """Simple noise synth build with a :class:`ipytone.Noise` instance
    routed through an :class:`ipytone.AmplitudeEnvelope`.

    """

    def __init__(self, **kwargs):
        self.noise = Noise(type="white")
        self.envelope = AmplitudeEnvelope(decay=0.1, sustain=0)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {"noise": self.noise, "envelope": self.envelope}

    def _after_init_func(self):
        return """
        this.getNode('noise').chain(this.getNode('envelope'), this.output);
        """

    def _attack_func(self):
        return """
        const envelope = this.getNode('envelope');
        const noise = this.getNode('noise');
        // the envelopes
        envelope.triggerAttack(time, velocity);
        noise.start(time);
        // if there is no release portion, stop noise
        if (envelope.sustain === 0) {
            const computedAttack = this.toSeconds(envelope.attack);
            const computedDecay = this.toSeconds(envelope.decay);
            noise.stop(time + computedAttack + computedDecay);
        }
        """

    def _release_func(self):
        return """
        time = this.toSeconds(time);
        const envelope = this.getNode('envelope');
        const noise = this.getNode('noise');
        envelope.triggerRelease(time);
        noise.stop(time + this.toSeconds(envelope.release));
        """


class PluckSynth(Instrument):
    """Karplus-Strong string synthesis."""

    def __init__(self, attack_noise=1, dampening=4000, resonance=0.7, release=1, **kwargs):
        self._attack_noise = Signal(
            value=attack_noise, units="positive", min_value=0.1, max_value=20
        )
        self._resonance = Signal(value=resonance, units="normalRange")
        self._release = Signal(value=release, units="positive")

        self._noise = Noise(type="pink")
        self._lfcf = LowpassCombFilter(dampening=dampening, resonance=resonance)

        super().__init__(**kwargs)

        self._noise.connect(self._lfcf)
        self._lfcf.connect(self._output)

    def _get_internal_nodes(self):
        return {
            "_attack_noise": self._attack_noise,
            "_resonance": self._resonance,
            "_release": self._release,
            "noise": self._noise,
            "lfcf_delay_time": self._lfcf.delay_time,
            "lfcf_resonance": self._lfcf.resonance,
        }

    def _attack_func(self):
        return """
        // convert
        const freq = this.toFrequency(note);
        time = this.toSeconds(time);
        // get nodes
        const noise = this.getNode('noise');
        const lfcfDelayTime = this.getNode('lfcf_delay_time');
        const lfcfResonance = this.getNode('lfcf_resonance');
        const delayAmount = 1 / freq;
        //
        lfcfDelayTime.setValueAtTime(delayAmount, time);
        noise.start(time);
        noise.stop(time + delayAmount * this.getNode('_attack_noise').value);
        lfcfResonance.cancelScheduledValues(time);
        lfcfResonance.setValueAtTime(this.getNode('_resonance').value, time);
        """

    def _release_func(self):
        return """
        time = this.toSeconds(time);
        const lfcfResonance = this.getNode('lfcf_resonance');
        const release = this.getNode('_release').value;
        lfcfResonance.linearRampTo(0, release, time);
        """

    @property
    def attack_noise(self):
        """Amount of noise at the attack.

        (range: 0.1-20)
        """
        return self._attack_noise.value

    @attack_noise.setter
    def attack_noise(self, value):
        self._attack_noise.value = value

    @property
    def dampening(self):
        """Dampening control, i.e. the lowpass filter frequency of the comb filter.

        (range: 0-7000)
        """
        return self._lfcf.dampening

    @dampening.setter
    def dampening(self, value):
        self._lfcf.dampening = value

    @property
    def resonance(self):
        """amount of resonance of the pluck."""
        return self._resonance.value

    @resonance.setter
    def resonance(self, value):
        self._resonance.value = value

    @property
    def release(self):
        """Release time which corresponds to a resonance ramp down to 0."""
        return self._release.value

    @release.setter
    def release(self, value):
        self._release.value = value

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._lfcf.dispose()

        return self


class DuoSynth(Monophonic):
    """Monophonic synth composed of two :class:`~ipytone.MonoSynth` instances
    run in parallel.

    Also provides a control over the frequency ratio between the two voices
    and a vibrato effect.

    """

    def __init__(self, harmonicity=1.5, vibrato_rate=5, vibrato_amount=0.5, **kwargs):
        self.voice0 = MonoSynth()
        self.voice1 = MonoSynth()

        envelope_settings = {"attack": 0.01, "decay": 0.0, "sustain": 1, "release": 0.5}
        for k, v in envelope_settings.items():
            setattr(self.voice0.envelope, k, v)
            setattr(self.voice0.filter_envelope, k, v)
            setattr(self.voice1.envelope, k, v)
            setattr(self.voice1.filter_envelope, k, v)

        self._harmonicity = Multiply(units="positive", factor=harmonicity)
        self._vibrato = LFO(frequency=vibrato_rate, min=-50, max=50)
        self._vibrato_gain = Gain(units="normalRange", gain=vibrato_amount)

        self._frequency = Signal(units="frequency", value=440)
        self._detune = Signal(units="cents", value=0)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {
            "voice0": self.voice0,
            "voice1": self.voice1,
            "harmonicity": self._harmonicity,
            "vibrato": self._vibrato,
            "vibrato_gain": self._vibrato_gain,
            "frequency": self._frequency,
            "detune": self._detune,
        }

    def _get_settings(self):
        return {
            # TODO: voice0 / voice1 nested settings (reuse self.voice0._get_settings(), etc.)
            # also nested settings via Signal value.
            # Note: Tone.js may have different names for the option to set and its corresponding property
            # (e.g., Multiply.factor initialized with option.value)
            # "harmonicity": ["factor"],
            # Note: different names between the widget model trait name (e.g., LFO._frequency) and the
            # Tone.js property or option to set.
            # "vibrato": ["frequency"],
            # "vibrato_gain": ["gain"],
        }

    def _after_init_func(self):
        return """
        const voice0 = this.getNode('voice0');
        const voice1 = this.getNode('voice1');
        // make sure polyphonic voices get released
        voice0.getNode('oscillator').onstop = () => this.onsilence(this);
        // start vibrato right away
        this.getNode('vibrato').start();
        // connections
        this.frequency.connect(voice0.frequency);
        this.frequency.chain(this.getNode('harmonicity'), voice1.frequency);
        this.getNode('vibrato').connect(this.getNode('vibrato_gain'));
        this.getNode('vibrato_gain').fan(voice0.detune, voice1.detune);
        this.detune.fan(voice0.detune, voice1.detune);
        voice0.connect(this.output);
        voice1.connect(this.output);
        """

    def _attack_func(self):
        return """
        this.getNode('voice0')._triggerEnvelopeAttack(time, velocity);
        this.getNode('voice1')._triggerEnvelopeAttack(time, velocity);
        """

    def _release_func(self):
        return """
        this.getNode('voice0')._triggerEnvelopeRelease(time);
        this.getNode('voice1')._triggerEnvelopeRelease(time);
        """

    def _get_level_at_time_func(self):
        return """
        time = this.toSeconds(time);
        const voice0 = this.getNode('voice0');
        const voice1 = this.getNode('voice1');
        return voice0.envelope.getValueAtTime(time) + voice1.envelope.getValueAtTime(time);
        """

    @property
    def harmonicity(self) -> Multiply:
        """Ratio between the two voices.

        A harmonicity of 1 is no change. Harmonicity = 2 means a change
        of an octave.

        """
        return self._harmonicity

    @property
    def vibrato_rate(self) -> Signal:
        """Vibrato frequency."""
        return self._vibrato.frequency

    @property
    def vibrato_amount(self) -> Param:
        """Vibrato amount."""
        return self._vibrato_gain.gain


class MembraneSynth(Synth):
    """A synth that makes kick and tom sounds."""

    def __init__(self, pitch_decay=0.05, octaves=8, **kwargs):
        self._pitch_decay = Signal(value=pitch_decay, units="positive", min_value=0, max_value=0.5)
        self._octaves = Signal(value=octaves, units="positive", min_value=0.5, max_value=8)

        super().__init__(**kwargs)

        self.oscillator.type = "sine"
        self.envelope.attack = 0.001
        self.envelope.attack_curve = "exponential"
        self.envelope.decay = 0.4
        self.envelope.sustain = 0.01
        self.envelope.release = 1.4

    def _get_internal_nodes(self):
        nodes = super()._get_internal_nodes()
        nodes.update({"pitch_decay": self._pitch_decay, "octaves": self._octaves})
        return nodes

    def _set_note_func(self):
        return """
        // conversions
        const seconds = this.toSeconds(time);
        const hertz = this.toFrequency(note);
        // get nodes
        const oscillator = this.getNode('oscillator');
        const octaves = this.getNode('octaves');
        const pitchDecay = this.getNode('pitch_decay');
        //
        const maxNote = hertz * octaves.value;
        oscillator.frequency.setValueAtTime(maxNote, seconds);
        oscillator.frequency.exponentialRampToValueAtTime(
            hertz, seconds + this.toSeconds(pitchDecay.value)
        );
        """

    @property
    def pitch_decay(self):
        """Amount of time the frequency envelope takes."""
        return self._pitch_decay.value

    @pitch_decay.setter
    def pitch_decay(self, value):
        self._pitch_decay.value = value

    @property
    def octaves(self):
        """The number of octaves the pitch envelope ramps."""
        return self._octaves.value

    @octaves.setter
    def octaves(self, value):
        self._octaves.value = value


class ModulationSynth(Monophonic):
    """Base class used for FM/AM synthesis."""

    def __init__(self, harmonicity=3, **kwargs):
        self._carrier = Synth(volume=-10)
        self._modulator = Synth(volume=-10)

        self.oscillator = self._carrier.oscillator
        self.envelope = self._carrier.envelope

        self.oscillator.type = "sine"
        self.envelope.attack = 0.01
        self.envelope.decay = 0.01
        self.envelope.sustain = 1
        self.envelope.release = 0.5

        self.modulation = self._modulator.oscillator
        self.modulation_envelope = self._modulator.envelope

        self.modulation.type = "square"
        self.modulation_envelope.attack = 0.5
        self.modulation_envelope.decay = 0
        self.modulation_envelope.sustain = 1
        self.modulation_envelope.release = 0.5

        self._harmonicity = Multiply(units="positive", factor=harmonicity, min_value=0)
        self._frequency = Signal(units="frequency", value=440)
        self._detune = Signal(units="cents", value=0)
        self._modulation_node = Gain(gain=0)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        return {
            "carrier": self._carrier,
            "modulator": self._modulator,
            "harmonicity": self._harmonicity,
            "frequency": self._frequency,
            "detune": self._detune,
            "modulation_node": self._modulation_node,
        }

    def _after_init_func(self):
        return """
        // make sure polyphonic voices get released
        this.getNode('carrier').onsilence = () => this.onsilence(this);
        """

    def _attack_func(self):
        return """
        this.getNode('carrier')._triggerEnvelopeAttack(time, velocity);
        this.getNode('modulator')._triggerEnvelopeAttack(time, velocity);
        """

    def _release_func(self):
        return """
        this.getNode('carrier')._triggerEnvelopeRelease(time);
        this.getNode('modulator')._triggerEnvelopeRelease(time);
        """

    def _get_level_at_time_func(self):
        return """
        time = this.toSeconds(time);
        this.getNode('envelope').getValueAtTime(time);
        """

    @property
    def harmonicity(self) -> Multiply:
        """Ratio between the two voices.

        A harmonicity of 1 is no change. Harmonicity = 2 means a change
        of an octave.

        """
        return self._harmonicity


class FMSynth(ModulationSynth):
    """A synth for FM synthesis that is built with two :class:`~ipytone.Synth`
    instances, where one synth modulates the frequency of the second.

    """

    def __init__(self, modulation_index=10, **kwargs):
        self._modulation_index = Multiply(factor=modulation_index)

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        nodes = super()._get_internal_nodes()
        nodes.update({"modulation_index": self._modulation_index})
        return nodes

    def _after_init_func(self):
        return (
            super()._after_init_func()
            + """
        const carrier = this.getNode('carrier');
        const modulator = this.getNode('modulator');
        const modulationNode = this.getNode('modulation_node');
        // connections
        this.frequency.connect(carrier.frequency);
        this.frequency.chain(this.getNode('harmonicity'), modulator.frequency);
        this.frequency.chain(this.getNode('modulation_index'), modulationNode);
        this.detune.fan(carrier.detune, modulator.detune);
        modulator.connect(modulationNode.gain);
        modulationNode.connect(carrier.frequency);
        carrier.connect(this.output);
        """
        )

    @property
    def modulation_index(self) -> Multiply:
        """Roughly corresponds to the depth or amount of the modulation.

        Ratio of the frequency of the modulating signal (mf) to the amplitude of the
        modulating signal (ma) -- as in ma/mf.

        """
        return self._modulation_index


class AMSynth(ModulationSynth):
    """A synth for FM synthesis that is built with two :class:`~ipytone.Synth`
    instances, where one synth modulates the amplitude of the second.

    """

    def __init__(self, **kwargs):
        self._modulation_scale = AudioToGain()

        super().__init__(**kwargs)

    def _get_internal_nodes(self):
        nodes = super()._get_internal_nodes()
        nodes.update({"modulation_scale": self._modulation_scale})
        return nodes

    def _after_init_func(self):
        return (
            super()._after_init_func()
            + """
        const carrier = this.getNode('carrier');
        const modulator = this.getNode('modulator');
        const modulationNode = this.getNode('modulation_node');
        // connections
        this.frequency.connect(carrier.frequency);
        this.frequency.chain(this.getNode('harmonicity'), modulator.frequency);
        this.detune.fan(carrier.detune, modulator.detune);
        modulator.chain(this.getNode('modulation_scale'), modulationNode.gain);
        carrier.chain(modulationNode, this.output);
        """
        )


class PolySynth(AudioNode):
    """A PolySynth allows any given monophonic synthesizer to be polyphonic."""

    _model_name = Unicode("PolySynthModel").tag(sync=True)

    _dummy_voice = Instance(Monophonic).tag(sync=True, **widget_serialization)
    max_polyphony = Int(32, help="Max. number of polyphonic voices alloweed").tag(sync=True)

    def __init__(self, voice=Synth, volume=0, **kwargs):
        """

        Parameters
        ----------
        voice : subclass of :class:`~ipytone.Monophonic`
            Any monophonic type used to create each voice of the poly-synth.
        volume : int
            Output volume (in decibels).

        """
        output = Volume(volume=volume, _create_node=False)

        # only used to retrieve the voice constructor arguments in the front-end and to
        # change synth parameters
        # -> dispose below
        self._dummy_voice = voice(volume=volume)

        kwargs.update({"_input": None, "_output": output, "_dummy_voice": self._dummy_voice})
        super().__init__(**kwargs)

        self._dummy_voice.dispose()

    @property
    def volume(self) -> Param:
        return self._output.volume

    @property
    def voice(self) -> Monophonic:
        """Returns an instance of the :class:`~ipytone.Monophonic` class used to
        create all the voices of this PolySynth.

        Although the individual voices used by the ``PolySynth`` to generate the
        single notes are not accessible, you can use this (deactivated) voice to change
        some parameters of this PolySynth. Changing the value of a trait accessed
        through this property will automatically update all active voices.

        """
        return self._dummy_voice

    def trigger_attack(self, notes, time=None, velocity=1):
        args = {"notes": notes, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttack", self, args)
        return self

    def trigger_release(self, time=None):
        add_or_send_event("triggerRelease", self, {"time": time})
        return self

    def trigger_attack_release(self, notes, duration, time=None, velocity=1):
        args = {"notes": notes, "duration": duration, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttackRelease", self, args)
        return self

    def release_all(self, time=None):
        add_or_send_event("releaseAll", self, {"time": time})
        return self


class Sampler(AudioNode):
    """Plays loaded samples mapped to midi notes."""

    _model_name = Unicode("SamplerModel").tag(sync=True)

    _buffers = Instance(AudioBuffers).tag(sync=True, **widget_serialization)

    attack = Float(0.0, help="Envelope attack").tag(sync=True)
    release = Float(1.0, help="Envelope release").tag(sync=True)
    curve = Enum(["linear", "exponential"], default_value="exponential", help="envelope curve").tag(
        sync=True
    )

    def __init__(self, urls, base_url="", volume=0, **kwargs):
        buffers = AudioBuffers(urls, base_url=base_url, _create_node=False)
        output = Volume(volume=volume, _create_node=False)

        kwargs.update({"_buffers": buffers, "_output": output})
        super().__init__(**kwargs)

    @property
    def volume(self) -> Param:
        """The volume parameter."""
        return self._output.volume

    @property
    def loaded(self):
        """Returns True if all audio buffers are loaded."""
        return self._buffers.loaded

    def add(self, note, url):
        """Add a player.

        Parameters
        ----------
        note : str
            Buffer key (must be a midi note).
        url : str or :class:`AudioBuffer`.
            Buffer file URL (str) or :class:`AudioBuffer` object.

        """
        if note in self._buffers.buffers:
            raise ValueError(f"A buffer with name '{note}' already exists on this object.")

        self._buffers.add(note, url)

        return self

    def trigger_attack(self, notes, time=None, velocity=1):
        args = {"notes": notes, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttack", self, args)
        return self

    def trigger_release(self, time=None):
        add_or_send_event("triggerRelease", self, {"time": time})
        return self

    def trigger_attack_release(self, notes, duration, time=None, velocity=1):
        args = {"notes": notes, "duration": duration, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttackRelease", self, args)
        return self

    def release_all(self, time=None):
        add_or_send_event("releaseAll", self, {"time": time})
        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._buffers.dispose()

        return self
