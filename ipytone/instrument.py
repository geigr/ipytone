import re
from textwrap import dedent

from ipywidgets import widget_serialization
from traitlets import Dict, Float, Instance, Unicode, validate

from .base import NodeWithContext
from .callback import add_or_send_event
from .core import AudioNode, Param, Volume
from .envelope import AmplitudeEnvelope, FrequencyEnvelope
from .filter import Filter
from .signal import Signal
from .source import Noise, OmniOscillator


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
    _trigger_attack = Unicode(help="trigger attack JS callback").tag(sync=True)
    _trigger_release = Unicode(help="trigger release JS callback").tag(sync=True)

    def __init__(self, volume=0, **kwargs):
        output = Volume(volume=volume, _create_node=False)
        kwargs.update({"_input": None, "_output": output})
        super().__init__(**kwargs)

    @validate("_trigger_attack")
    def _minify_trigger_attack(self, proposal):
        return minify_js_func(proposal["value"])

    @validate("_trigger_release")
    def _minify_trigger_release(self, proposal):
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

    _get_level_at_time = Unicode(help="get level at time JS callback").tag(sync=True)

    _frequency = Instance(Signal).tag(sync=True, **widget_serialization)
    _detune = Instance(Signal).tag(sync=True, **widget_serialization)

    portamento = Float(0, help="glide time between notes").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @validate("_get_level_at_time")
    def _minify_get_level_at_time(self, proposal):
        return minify_js_func(proposal["value"])

    @property
    def frequency(self) -> Signal:
        return self._frequency

    @property
    def detune(self) -> Signal:
        return self._detune


class Synth(Monophonic):
    """Simple synth build with an :class:`ipytone.OmniOscillator` routed through
    an :class:`ipytone.AmplitudeEnvelope`.

    """

    def __init__(self, **kwargs):
        self.oscillator = OmniOscillator(type="triangle")
        self.envelope = AmplitudeEnvelope(attack=0.005, decay=0.1, sustain=0.3, release=1)

        attack_func = """
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

        release_func = """
        const envelope = this.getNode('envelope');
        const oscillator = this.getNode('oscillator');
        envelope.triggerRelease(time);
        oscillator.stop(time + this.toSeconds(envelope.release));
        """

        get_level_func = """
        time = this.toSeconds(time);
        return this.getNode('envelope').getValueAtTime(time);
        """

        kw = {
            "_internal_nodes": {"envelope": self.envelope, "oscillator": self.oscillator},
            "_trigger_attack": attack_func,
            "_trigger_release": release_func,
            "_get_level_at_time": get_level_func,
            "_frequency": self.oscillator.frequency,
            "_detune": self.oscillator.detune,
        }
        kwargs.update(kw)

        super().__init__(**kwargs)

        self.oscillator.chain(self.envelope, self._output)


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

        attack_func = """
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

        release_func = """
        const envelope = this.getNode('envelope');
        const filterEnvelope = this.getNode('filter_envelope');
        const oscillator = this.getNode('oscillator');
        envelope.triggerRelease(time);
        filterEnvelope.triggerRelease(time);
        oscillator.stop(time + this.toSeconds(envelope.release));
        """

        get_level_func = """
        time = this.toSeconds(time);
        return this.getNode('envelope').getValueAtTime(time);
        """

        kw = {
            "_internal_nodes": {
                "envelope": self.envelope,
                "filter_envelope": self.filter_envelope,
                "oscillator": self.oscillator,
                "filter": self.filter,
            },
            "_trigger_attack": attack_func,
            "_trigger_release": release_func,
            "_get_level_at_time": get_level_func,
            "_frequency": self.oscillator.frequency,
            "_detune": self.oscillator.detune,
        }
        kwargs.update(kw)

        super().__init__(**kwargs)

        self.oscillator.chain(self.filter, self.envelope, self._output)
        self.filter_envelope.connect(self.filter.frequency)


class NoiseSynth(Instrument):
    """Simple noise synth build with a :class:`ipytone.Noise` instance
    routed through an :class:`ipytone.AmplitudeEnvelope`.

    """

    def __init__(self, **kwargs):
        self.noise = Noise(type="white")
        self.envelope = AmplitudeEnvelope(decay=0.1, sustain=0)

        attack_func = """
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

        release_func = """
        time = this.toSeconds(time);
        const envelope = this.getNode('envelope');
        const noise = this.getNode('noise');
        envelope.triggerRelease(time);
        noise.stop(time + this.toSeconds(envelope.release));
        """

        kw = {
            "_internal_nodes": {
                "envelope": self.envelope,
                "noise": self.noise,
            },
            "_trigger_attack": attack_func,
            "_trigger_release": release_func,
        }
        kwargs.update(kw)

        super().__init__(**kwargs)

        self.noise.chain(self.envelope, self._output)
