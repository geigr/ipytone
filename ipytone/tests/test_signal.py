import operator

import pytest

from ipytone import Add, GreaterThan, Multiply, Signal, Subtract


def test_signal():
    sig = Signal()

    assert sig.units == "number"
    assert sig.min_value is sig.max_value is None

    sig.value = 2
    assert sig.value == 2

    sig2 = Signal(value=440, units="frequency", min_value=100, max_value=1e3)
    assert sig2.value == 440
    assert sig2.units == "frequency"
    assert sig2.min_value == 100
    assert sig2.max_value == 1e3
    assert sig2.overridden is False
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

    op_repr = f"{cls_str}(name='op', {prop_name}=Signal(value={default_value:.1f}, units='number'))"
    assert repr(op_signal) == op_repr


@pytest.mark.parametrize(
    "op,op_cls,op_prop_name,value",
    [
        (operator.mul, Multiply, "factor", 2),
        (operator.add, Add, "addend", 1),
        (operator.sub, Subtract, "subtrahend", 1),
        (operator.gt, GreaterThan, "comparator", 1),
    ],
)
def test_signal_operator(op, op_cls, op_prop_name, value):
    # test operator with number
    sig = Signal(value=1)
    op_sig = op(sig, value)
    assert isinstance(op_sig, op_cls)
    assert sig in op_sig.input
    assert getattr(op_sig, op_prop_name).value == value

    # test operator with another signal
    sig2 = Signal(value=2)
    op_sig2 = op(sig, sig2)
    assert isinstance(op_sig2, op_cls)
    assert sig in op_sig2.input
    assert sig2 in getattr(op_sig2, op_prop_name).input
