from ipytone import Add, Multiply, Signal, Subtract


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


def test_signal_multiply():
    mult = Multiply(name="test mult")
    assert mult.factor.value == 1
    assert repr(mult) == "Multiply(name='test mult', factor=Signal(value=1.0, units='number'))"


def test_signal_multiply_operator():
    # test __mul__ with number
    sig = Signal(value=1)
    mult = sig * 2
    assert isinstance(mult, Multiply)
    assert sig in mult.input
    assert mult.factor.value == 2

    # test __mul__ with signal
    sig2 = Signal(value=2)
    mult2 = sig * sig2
    assert isinstance(mult2, Multiply)
    assert sig in mult2.input
    assert sig2 in mult2.factor.input


def test_signal_add():
    add = Add(name="test add")
    assert add.addend.value == 0
    assert repr(add) == "Add(name='test add', addend=Signal(value=0.0, units='number'))"


def test_signal_add_operator():
    # test __add__ with number
    sig = Signal(value=1)
    add = sig + 1
    assert isinstance(add, Add)
    assert sig in add.input
    assert add.addend.value == 1

    # test __add__ with signal
    sig2 = Signal(value=2)
    add2 = sig + sig2
    assert isinstance(add2, Add)
    assert sig in add2.input
    assert sig2 in add2.addend.input


def test_signal_subtract():
    sub = Subtract(name="test sub")
    assert sub.subtrahend.value == 0
    assert repr(sub) == "Subtract(name='test sub', subtrahend=Signal(value=0.0, units='number'))"


def test_signal_subtract_operator():
    # test __sub__ with number
    sig = Signal(value=1)
    sub = sig - 1
    assert isinstance(sub, Subtract)
    assert sig in sub.input
    assert sub.subtrahend.value == 1

    # test __sub__ with signal
    sig2 = Signal(value=2)
    sub2 = sig - sig2
    assert isinstance(sub2, Subtract)
    assert sig in sub2.input
    assert sig2 in sub2.subtrahend.input
