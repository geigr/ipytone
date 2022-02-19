import pytest
from traitlets import TraitError

from ipytone.core import Gain
from ipytone.envelope import AmplitudeEnvelope, Envelope, FrequencyEnvelope
from ipytone.signal import Pow, Scale, Signal


def test_envelope():
    env = Envelope()

    assert isinstance(env.output, Signal)
    assert env.output.units == "normalRange"
    assert env.input is None

    assert env.array is None
    assert env.array_length == 1024
    assert env.sync_array is False

    assert env.attack == 0.01
    assert env.decay == 0.1
    assert env.sustain == 1.0
    assert env.release == 0.5
    assert env.attack_curve == "linear"
    assert env.decay_curve == "exponential"
    assert env.release_curve == "exponential"

    assert repr(env) == "Envelope(attack=0.01, decay=0.1, sustain=1.0, release=0.5)"

    assert env.trigger_attack() is env
    assert env.trigger_release() is env
    assert env.trigger_attack_release(1) is env

    env.attack_curve = [0.0, 0.2, 0.8, 1.0]
    assert isinstance(env.attack_curve, list)
    env.release_curve = [1.0, 0.8, 0.2, 0.0]
    assert isinstance(env.release_curve, list)

    with pytest.raises(TraitError):
        env.decay_curve = "sine"


@pytest.mark.parametrize(
    "method,js_method,kwargs",
    [
        ("trigger_attack", "triggerAttack", {"time": None, "velocity": 1}),
        ("trigger_release", "triggerRelease", {"time": None}),
        (
            "trigger_attack_release",
            "triggerAttackRelease",
            {"duration": 1, "time": None, "velocity": 1},
        ),
    ],
)
def test_enveloppe_trigger(mocker, method, js_method, kwargs):
    env = Envelope()
    mocker.patch.object(env, "send")

    args = {k: {"value": v, "eval": False} for k, v in kwargs.items()}
    expected = {"event": "trigger", "method": js_method, "args": args, "arg_keys": list(kwargs)}

    e = getattr(env, method)(**kwargs)
    assert e is env
    env.send.assert_called_once_with(expected)


def test_amplitude_envelope():
    env = AmplitudeEnvelope()

    assert isinstance(env.input, Gain)
    assert env.input is env.output
    assert env.input.gain.value == 0


def test_frequency_envelope():
    env = FrequencyEnvelope()

    assert isinstance(env.input, Pow)
    assert env.input.value == env.exponent == 1
    assert isinstance(env.output, Scale)
    assert env.output.min_out == env.base_frequency == 200.0
    assert env.output.max_out == 200.0 * 2**4
    assert env.octaves == 4
