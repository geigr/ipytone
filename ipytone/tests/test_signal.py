import math
import operator

import pytest

from ipytone import Abs, Add, GreaterThan, Multiply, Negate, Param, Pow, Scale, Signal, Subtract
from ipytone.core import InternalAudioNode


def test_signal():
    sig = Signal()

    assert sig.value == sig.input.value == 0
    assert sig.units == sig.input.units == "number"
    assert sig.min_value == sig.input.min_value == -math.inf
    assert sig.max_value == sig.input.max_value == math.inf
    assert sig.overridden is sig.input.overridden is False

    assert isinstance(sig.input, Param)
    assert isinstance(sig.output, InternalAudioNode)

    sig.value = 2
    assert sig.value == 2

    sig2 = Signal(value=440, units="frequency", min_value=100, max_value=1e3)
    assert sig2.value == 440
    assert sig2.units == "frequency"
    assert sig2.min_value == 100
    assert sig2.max_value == 1e3
    assert repr(sig2) == "Signal(value=440.0, units='frequency')"


@pytest.mark.parametrize(
    "cls,cls_str,prop_name,default_value",
    [
        (Multiply, "Multiply", "factor", 1),
        (Add, "Add", "addend", 0),
        (Subtract, "Subtract", "subtrahend", 0),
        (GreaterThan, "GreaterThan", "comparator", 0),
    ],
)
def test_signal_subclass(cls, cls_str, prop_name, default_value):
    op_signal = cls(name="op")
    assert getattr(op_signal, prop_name).value == default_value

    op_repr = f"{cls_str}(name='op', {prop_name}=Param(value={default_value:.1f}, units='number'))"
    assert repr(op_signal) == op_repr


@pytest.mark.parametrize(
    "op,op_cls,op_prop_name,value,test_other_signal",
    [
        (operator.mul, Multiply, "factor", 2, True),
        (operator.add, Add, "addend", 1, True),
        (operator.sub, Subtract, "subtrahend", 1, True),
        (operator.gt, GreaterThan, "comparator", 1, True),
        (operator.pow, Pow, "value", 1, False),
    ],
)
def test_signal_operator(op, op_cls, op_prop_name, value, test_other_signal, audio_graph):
    # test operator with number
    sig = Signal(value=1)
    op_sig = op(sig, value)
    assert isinstance(op_sig, op_cls)
    assert (sig, op_sig, 0, 0) in audio_graph.connections

    try:
        assert getattr(op_sig, op_prop_name).value == value
    except AttributeError:
        # attribute is a simple value (not a param)
        assert getattr(op_sig, op_prop_name) == value

    # test operator with another signal
    if test_other_signal:
        sig2 = Signal(value=2)
        op_sig2 = op(sig, sig2)
        assert isinstance(op_sig2, op_cls)
        assert (sig, op_sig2, 0, 0) in audio_graph.connections
        assert (sig2, getattr(op_sig2, op_prop_name), 0, 0) in audio_graph.connections

        # test dispose
        s = op_sig2.dispose()
        assert s is op_sig2
        assert op_sig2.disposed is True
        assert getattr(op_sig2, op_prop_name).disposed is True
        assert (sig, op_sig2) not in audio_graph.connections
        assert (sig2, getattr(op_sig2, op_prop_name), 0, 0) not in audio_graph.connections


@pytest.mark.parametrize("op,op_cls", [(operator.abs, Abs), (operator.neg, Negate)])
def test_simple_signal_operator(op, op_cls, audio_graph):
    sig = Signal(value=1)
    op_sig = op(sig)
    assert isinstance(op_sig, op_cls)
    assert (sig, op_sig, 0, 0) in audio_graph.connections


def test_scale():
    sc = Scale(min_out=0.2, max_out=1.2)
    assert sc.min_out == 0.2
    assert sc.max_out == 1.2
    assert sc.input.value == 1.0
    assert sc.output.value == 0.2


def test_complex_signal_expression(audio_graph):
    sig = Signal(value=400)
    mod = Signal(value=-0.5)

    res = sig + abs(mod) * 100

    assert isinstance(res, Add)
    assert (sig, res, 0, 0) in audio_graph.connections

    mult = None
    for (src, dest, *_) in audio_graph.connections:
        if dest is res.addend:
            mult = src
            break
    assert isinstance(mult, Multiply)
    assert mult.factor.value == 100

    abs_ = None
    for (src, dest, *_) in audio_graph.connections:
        if dest is mult:
            abs_ = src
            break
    assert isinstance(abs_, Abs)
    assert (mod, abs_, 0, 0) in audio_graph.connections
