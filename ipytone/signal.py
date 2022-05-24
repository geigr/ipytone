from ipywidgets import widget_serialization
from traitlets import Bool, Float, Instance, Int, List, Unicode, Union

from .base import AudioNode, ToneObject
from .core import Gain, InternalAudioNode, Param, ParamScheduleMixin
from .observe import ScheduleObserveMixin


class SignalOperator(AudioNode):

    _model_name = "SignalOperatorModel"

    def _create_op_signal(self, other, signal_cls, signal_attr_name):
        if isinstance(other, SignalOperator):
            op_signal = signal_cls()
            other.connect(getattr(op_signal, signal_attr_name))
        else:
            op_signal = signal_cls(other)

        self.connect(op_signal)

        return op_signal

    def _create_simple_op_signal(self, signal_cls, **kwargs):
        op_signal = signal_cls(**kwargs)
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

    def __abs__(self):
        return self._create_simple_op_signal(Abs)

    def __neg__(self):
        return self._create_simple_op_signal(Negate)

    def __pow__(self, value):
        return self._create_simple_op_signal(Pow, value=value)


class Signal(SignalOperator, ParamScheduleMixin, ScheduleObserveMixin):
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
    _input = Instance(ToneObject).tag(sync=True, **widget_serialization)
    _override = Bool(True).tag(sync=True)
    value = Union((Float(), Int(), Unicode()), help="Signal value").tag(sync=True)

    _side_signal_prop_name = None

    _observable_traits = List(["value"])

    def __init__(self, value=0, units="number", min_value=None, max_value=None, **kwargs):
        if "_input" not in kwargs:
            kwargs["_input"] = Param(
                value=value,
                units=units,
                min_value=min_value,
                max_value=max_value,
                _create_node=False,
            )
        if "_output" not in kwargs:
            kwargs["_output"] = InternalAudioNode(type="ToneConstantSource")

        kwargs["value"] = value

        super().__init__(**kwargs)

    @property
    def units(self):
        """Signal value units."""
        return self.input.units

    @property
    def min_value(self):
        """Signal value lower limit."""
        return self.input.min_value

    @property
    def max_value(self):
        """Signal value upper limit."""
        return self.input.max_value

    @property
    def overridden(self):
        """If True, the signal value is overridden by an incoming signal."""
        if self._override:
            return self.input.overridden
        else:
            return False

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


def _as_signal(value) -> SignalOperator:
    # TODO: this will change when ipytone will support Tone.Param

    if isinstance(value, SignalOperator):
        return value
    else:
        return Signal(value=value)


class Multiply(Signal):
    """A signal that outputs the product of the incoming signal by another signal
    or a constant factor.

    Parameters
    ----------
    factor : integer or float, optional
        Multiplication factor (default: 1).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("MultiplyModel").tag(sync=True)
    _factor = Instance(Param).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "factor"

    def __init__(self, factor=1, **kwargs):
        gain = Gain(
            gain=factor,
            units="number",
            min_value=kwargs.pop("min_value", None),
            max_value=kwargs.pop("max_value", None),
            _create_node=False,
        )
        _factor = gain.gain

        kwargs.update({"_factor": _factor, "_input": gain, "_output": gain, "_override": False})
        super().__init__(**kwargs)

    @property
    def factor(self) -> Param:
        """The multiplication factor."""
        return self._factor


class Add(Signal):
    """A signal that outputs the sum of the incoming signal and another signal
    or a constant value.

    Parameters
    ----------
    addend : integer or float, optional
        The value to be added to the incoming signal (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("AddModel").tag(sync=True)
    _addend = Instance(Param).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "addend"

    def __init__(self, addend=0, **kwargs):
        node = Gain(_create_node=False)
        _addend = Param(value=addend, _create_node=False)

        kwargs.update({"_addend": _addend, "_input": node, "_output": node, "_override": False})
        super().__init__(**kwargs)

    @property
    def addend(self) -> Param:
        """The value which is added to the input signal."""
        return self._addend

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self.addend.dispose()

        return self


class Subtract(Signal):
    """A signal that outputs the difference between the incoming signal and another signal
    or a constant value.

    Parameters
    ----------
    subtrahend : integer or float, optional
        The value to substract to the incoming signal (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("SubtractModel").tag(sync=True)
    _subtrahend = Instance(Param).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "subtrahend"

    def __init__(self, subtrahend=0, **kwargs):
        node = Gain(_create_node=False)
        _subtrahend = Param(value=subtrahend, _create_node=False)

        kwargs.update(
            {"_subtrahend": _subtrahend, "_input": node, "_output": node, "_override": False}
        )
        super().__init__(**kwargs)

    @property
    def subtrahend(self) -> Param:
        """The value which is substracted from the input signal."""
        return self._subtrahend

    def dispose(
        self,
    ):
        with self._graph.hold_state():
            super().dispose()
            self.subtrahend.dispose()

        return self


class GreaterThan(Signal):
    """A signal that outputs 1 the signal is greater than the value (or another signal),
    otherwise outputs 0.

    Parameters
    ----------
    comparator : integer or float, optional
        The value to compare to the incoming signal (default: 0).
    **kwargs
        Arguments passed to :class:`Signal`.

    """

    _model_name = Unicode("GreaterThanModel").tag(sync=True)
    _comparator = Instance(Param).tag(sync=True, **widget_serialization)
    _side_signal_prop_name = "comparator"

    def __init__(self, comparator=0, **kwargs):
        in_node = InternalAudioNode(type="Substract")
        out_node = InternalAudioNode(type="GreaterThanZero")
        _comparator = Param(value=comparator, _create_node=False)

        kw = {
            "_comparator": _comparator,
            "_input": in_node,
            "_output": out_node,
            "_override": False,
        }
        kwargs.update(kw)
        super().__init__(**kwargs)

    @property
    def comparator(self) -> Param:
        """The value that is compared to the incoming signal against."""
        return self._comparator

    def dispose(
        self,
    ):
        with self._graph.hold_state():
            super().dispose()
            self.comparator.dispose()

        return self


class AudioToGain(SignalOperator):
    """A node that converts an input signal in audio range [-1, 1] to an output signal
    in normal range [0, 1].

    """

    _model_name = Unicode("AudioToGainModel").tag(sync=True)

    def __init__(self, *args, **kwargs):
        node = InternalAudioNode(type="WaveShaper")
        kwargs.update({"_input": node, "_output": node})
        super().__init__(*args, **kwargs)


class Abs(SignalOperator):
    """A node that outputs the absolute value of an incoming signal.

    The incoming signal must be audio range [-1, 1].

    """

    _model_name = Unicode("AbsModel").tag(sync=True)

    def __init__(self, *args, **kwargs):
        node = InternalAudioNode(type="WaveShaper")
        kwargs.update({"_input": node, "_output": node})
        super().__init__(*args, **kwargs)


class Negate(SignalOperator):
    """A node that outputs the opposite value of an incoming signal.

    The incoming signal must be audio range [-1, 1].
    """

    _model_name = Unicode("NegateModel").tag(sync=True)

    def __init__(self, *args, **kwargs):
        node = InternalAudioNode(type="Multiply")
        kwargs.update({"_input": node, "_output": node})
        super().__init__(*args, **kwargs)


class Pow(SignalOperator):
    """A node that applies an exponent to the incoming signal.

    The incoming signal must be audio range [-1, 1].
    """

    _model_name = Unicode("PowModel").tag(sync=True)

    value = Union((Float(), Int()), help="exponent value").tag(sync=True)

    def __init__(self, *args, **kwargs):
        node = InternalAudioNode(type="WaveShaper")
        kwargs.update({"_input": node, "_output": node})
        super().__init__(*args, **kwargs)


class Scale(SignalOperator):
    """A node that applies linear scaling on the incoming signal.

    The incoming signal must be normal range [0, 1].
    """

    _model_name = Unicode("ScaleModel").tag(sync=True)

    min_out = Float(0.0, help="min output value").tag(sync=True)
    max_out = Float(1.0, help="max output value").tag(sync=True)

    def __init__(self, min_out=0.0, max_out=1.0, **kwargs):
        kwargs.update({"min_out": min_out, "max_out": max_out})

        in_node = Multiply(value=max_out - min_out, _create_node=False)
        out_node = Add(value=min_out, _create_node=False)
        kwargs.update({"_input": in_node, "_output": out_node})

        super().__init__(**kwargs)
