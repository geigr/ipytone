from traitlets import Bool, Enum, Float, Int, List, Unicode, Union
from traittypes import Array

from .base import AudioNode
from .callback import add_or_send_event
from .core import Gain
from .observe import ScheduleObserveMixin
from .serialization import data_array_serialization
from .signal import Pow, Scale, Signal

BASIC_CURVES = ["linear", "exponential"]
CURVES = BASIC_CURVES + ["sine", "cosine", "bounce", "ripple", "step"]


class Envelope(AudioNode, ScheduleObserveMixin):
    """ADSR envelope generator.

    Envelope outputs a signal which can be connected to a :class:`Signal`.

    """

    _model_name = Unicode("EnvelopeModel").tag(sync=True)

    attack = Float(0.01, help="Envelope attack").tag(sync=True)
    decay = Float(0.1, help="Envelope decay").tag(sync=True)
    sustain = Float(1.0, help="Envelope sustain").tag(sync=True)
    release = Float(0.5, help="Envelope release").tag(sync=True)

    attack_curve = Union([Enum(CURVES), List(Float())], default_value="linear").tag(sync=True)
    decay_curve = Enum(BASIC_CURVES, default_value="exponential").tag(sync=True)
    release_curve = Union([Enum(CURVES), List(Float())], default_value="exponential").tag(sync=True)

    array = Array(allow_none=True, default_value=None, read_only=True, help="Envelope data").tag(
        sync=True, **data_array_serialization
    )
    array_length = Int(1024, help="Envelope data resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="If True, synchronize envelope data").tag(sync=True)

    _observable_traits = List(["value"])

    def __init__(self, **kwargs):
        if "_output" not in kwargs:
            out_node = Signal(units="normalRange", _create_node=False)
            kwargs.update({"_output": out_node})

        super().__init__(**kwargs)

    def trigger_attack(self, time=None, velocity=1):
        add_or_send_event("triggerAttack", self, {"time": time, "velocity": velocity})
        return self

    def trigger_release(self, time=None):
        add_or_send_event("triggerRelease", self, {"time": time})
        return self

    def trigger_attack_release(self, duration, time=None, velocity=1):
        args = {"duration": duration, "time": time, "velocity": velocity}
        add_or_send_event("triggerAttackRelease", self, args)
        return self

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["attack", "decay", "sustain", "release"]:
            yield key


class AmplitudeEnvelope(Envelope):
    """Envelope which, applied to an input audio signal, control the gain
    of the output signal.

    """

    _model_name = Unicode("AmplitudeEnvelopeModel").tag(sync=True)

    def __init__(self, **kwargs):
        gain_node = Gain(gain=0, _create_node=False)
        kwargs.update({"_input": gain_node, "_output": gain_node})
        super().__init__(**kwargs)


class FrequencyEnvelope(Envelope):
    """Envelope which may be used to control a frequency signal."""

    _model_name = Unicode("FrequencyEnvelopeModel").tag(sync=True)

    base_frequency = Float(200.0, help="Envelope min output (start) value").tag(sync=True)
    octaves = Int(4, help="Envelope range in number of octaves").tag(sync=True)
    exponent = Int(1, help="May be used to control the envelope (non)linearity").tag(sync=True)

    def __init__(self, base_frequency=200.0, octaves=4, exponent=1, **kwargs):
        kwargs.update({"base_frequency": base_frequency, "octaves": octaves, "exponent": exponent})

        in_node = Pow(value=exponent)
        out_node = Scale(min_out=base_frequency, max_out=base_frequency * 2**octaves)
        kwargs.update({"_input": in_node, "_output": out_node})

        super().__init__(**kwargs)
