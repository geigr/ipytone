from ipywidgets import widget_serialization
from traitlets import Enum, Instance, Unicode, Float, Int, Bool, Union

from .core import AudioNode


_UNITS = [
    "bpm",
    "cents",
    "decibels",
    "degrees",
    "frequency",
    "gain",
    "hertz",
    "number",
    "positive",
    "radians",
    "samples",
    "ticks",
    "time",
    "transport_time",
]


class Signal(AudioNode):
    """A node that defines a value that can be modulated or calculated
    at the audio sample-level accuracy.

    Signal objects support basic arithmetic operators such as ``+``, ``-``,
    ``*``, ``**``, ``abs``, ``neg`` as well as the ``>`` comparison operator.

    Like any other node, a signal can be connected to/from other nodes. When a signal
    receives an incoming signal, its value is ignored (reset to 0) and the incoming
    signal passes through the node (``overridden=True``).

    Parameters
    ----------
    value : integer or float or str, optional
        Initial value of the signal (default: 0)
    units : str
        Signal value units, e.g., 'time', 'number', 'frequency', 'bpm', etc.
    min_value : integer or float, optional
        Signal value lower limit (default: no limit).
    max_value : integer or float, optional
        Signal value upper limit (default: no limit).
    **kwargs
        Arguments passed to :class:`AudioNode`

    """

    _model_name = Unicode("SignalModel").tag(sync=True)

    _units = Enum(_UNITS, default_value="number", allow_none=False).tag(sync=True)
    value = Union((Float(), Int(), Unicode()), help="Signal current value").tag(sync=True)
    _min_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    _max_value = Union((Float(), Int()), default_value=None, allow_none=True).tag(sync=True)
    overridden = Bool(
        read_only=True, help="If True, the signal value is overridden by an incoming signal"
    ).tag(sync=True)

    _side_signal_prop_name = None

    def __init__(self, value=0, units="number", min_value=None, max_value=None, **kwargs):
        kwargs.update(
            {"value": value, "_units": units, "_min_value": min_value, "_max_value": max_value}
        )
        super().__init__(**kwargs)

    @property
    def units(self):
        """Signal value units."""
        return self._units

    @property
    def min_value(self):
        """Signal value lower limit."""
        return self._min_value

    @property
    def max_value(self):
        """Signal value upper limit."""
        return self._max_value

    def _create_op_signal(self, other, signal_cls, signal_attr_name):
        if not isinstance(other, Signal):
            op_signal = signal_cls(**{signal_attr_name: other})
        else:
            op_signal = signal_cls()
            other.connect(getattr(op_signal, signal_attr_name))

        self.connect(op_signal)

        return op_signal

    def __mul__(self, other):
        return self._create_op_signal(other, Multiply, "factor")

    def __add__(self, other):
        return self._create_op_signal(other, Add, "addend")

    def __sub__(self, other):
        return self._create_op_signal(other, Subtract, "subtrahend")

    def __gt__(self, other):
        return self._create_op_signal(other, GreaterThan, "comparator")

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if self.overridden:
            yield "overridden"
        elif self._side_signal_prop_name is not None:
            yield self._side_signal_prop_name
        else:
            yield "value"
            yield "units"


class Multiply(Signal):
    """A signal that outputs the product of the incoming signal by another signal
    or a constant factor.

    Parameters
    ----------
    factor : integer or float or :class:`Signal`, optional
        Multiplication factor, either a constant value or a signal (default: 1).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("MultiplyModel").tag(sync=True)
    _factor = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "factor"

    def __init__(self, factor=1, **kwargs):
        if not isinstance(factor, Signal):
            factor = Signal(value=factor)

        kwargs.update({"_factor": factor})
        super().__init__(**kwargs)

    @property
    def factor(self) -> Signal:
        """The signal used as multiplication factor."""
        return self._factor


class Add(Signal):
    """A signal that outputs the sum of the incoming signal and another signal
    or a constant value.

    Parameters
    ----------
    addend : integer or float or :class:`Signal`, optional
        Either a constant value or a signal to be added to the incoming signal
        (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("AddModel").tag(sync=True)
    _addend = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "addend"

    def __init__(self, addend=0, **kwargs):
        if not isinstance(addend, Signal):
            addend = Signal(value=addend)

        kwargs.update({"_addend": addend})
        super().__init__(**kwargs)

    @property
    def addend(self):
        """The signal which is added to the input signal."""
        return self._addend


class Subtract(Signal):
    """A signal that outputs the difference between the incoming signal and another signal
    or a constant value.

    Parameters
    ----------
    subtrahend : integer or float or :class:`Signal`, optional
        Either a constant value or a signal to substract to the incoming signal
        (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("SubtractModel").tag(sync=True)
    _subtrahend = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "subtrahend"

    def __init__(self, subtrahend=0, **kwargs):
        if not isinstance(subtrahend, Signal):
            subtrahend = Signal(value=subtrahend)

        kwargs.update({"_subtrahend": subtrahend})
        super().__init__(**kwargs)

    @property
    def subtrahend(self):
        """The signal which is substracted from the input signal."""
        return self._subtrahend


class GreaterThan(Signal):
    """A signal that outputs 1 the signal is greater than the value (or another signal),
    otherwise outputs 0.

    Parameters
    ----------
    comparator : integer or float or :class:`Signal`, optional
        Either a constant value or a signal to compare to the incoming signal
        (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("SubtractModel").tag(sync=True)
    _comparator = Instance(Signal, allow_none=True).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "comparator"

    def __init__(self, comparator=0, **kwargs):
        if not isinstance(comparator, Signal):
            comparator = Signal(value=comparator)

        kwargs.update({"_comparator": comparator})
        super().__init__(**kwargs)

    @property
    def comparator(self):
        """The signal to compare to the incoming signal against."""
        return self._comparator
