from traitlets import Bool, Enum, Float, Int, List, Unicode, Union
from traittypes import Array

from .base import AudioNode
from .serialization import data_array_serialization
from .signal import Signal

BASIC_CURVES = ["linear", "exponential"]
CURVES = BASIC_CURVES + ["sine", "cosine", "bounce", "ripple", "step"]


class Envelope(AudioNode):
    """ADSR envelope generator.

    Envelope outputs a signal which can be connected to a :class:`Signal`.

    """

    _model_name = Unicode("EnvelopeModel").tag(sync=True)

    attack = Float(0.01, help="Envelope attack").tag(sync=True)
    decay = Float(0.1, help="Envelope decay").tag(sync=True)
    sustain = Float(1.0, help="Envelope sustain").tag(sync=True)
    release = Float(0.5, help="Envelope release").tag(sync=True)

    attack_curve = Union([Enum(CURVES), List(Float)], default_value="linear").tag(sync=True)
    decay_curve = Enum(BASIC_CURVES, default_value="exponential").tag(sync=True)
    release_curve = Union([Enum(CURVES), List(Float)], default_value="exponential").tag(sync=True)

    array = Array(allow_none=True, default_value=None, read_only=True, help="Envelope data").tag(
        sync=True, **data_array_serialization
    )
    array_length = Int(1024, help="Envelope data resolution (array length)").tag(sync=True)
    sync_array = Bool(False, help="If True, synchronize envelope data").tag(sync=True)

    def __init__(self, *args, **kwargs):
        out_node = Signal(units="normalRange", _create_node=False)
        kwargs.update({"_output": out_node})
        super().__init__(*args, **kwargs)

    def trigger_attack(self, time=""):
        self.send({"event": "triggerAttack"})
        return self

    def trigger_release(self, time=""):
        self.send({"event": "triggerRelease"})
        return self

    def trigger_attack_release(self, duration, time=""):
        self.send({"event": "triggerAttackRelease", "duration": duration})
        return self
