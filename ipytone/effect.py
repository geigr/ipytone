from ipywidgets import widget_serialization
from traitlets import Float, Instance, Unicode, validate

from .base import AudioNode
from .channel import CrossFade
from .core import Gain, Param
from .signal import Signal
from .utils import validate_osc_type


class Effect(AudioNode):
    """Effect base class."""

    _model_name = Unicode("EffectModel").tag(sync=True)

    def __init__(self, wet=1, **kwargs):
        in_node = Gain(_create_node=False)
        out_node = CrossFade(fade=wet, _create_node=False)

        kwargs.update({"_input": in_node, "_output": out_node})
        super().__init__(**kwargs)

    @property
    def wet(self):
        """The wet signal.

        Controls how much of the effected will pass through to the output
        (1 = 100% effected signal, 0 = 100% dry signal)

        """
        return self.output.fade


class Vibrato(Effect):
    """Vibrato effect."""

    _model_name = Unicode("VibratoModel").tag(sync=True)

    type = Unicode("sine", help="Vibrato LFO type").tag(sync=True)
    _max_delay = Float().tag(sync=True)
    _frequency = Instance(Signal).tag(sync=True, **widget_serialization)
    _depth = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, frequency=5, depth=0.1, type="sine", max_delay=0.005, **kwargs):
        freq_node = Signal(value=frequency, units="frequency", _create_node=False)
        depth_node = Param(value=depth, units="normalRange", _create_node=False)

        kwargs.update(
            {"_max_delay": max_delay, "_frequency": freq_node, "_depth": depth_node, "type": type}
        )
        super().__init__(**kwargs)

    @validate("type")
    def _validate_type(self, proposal):
        return validate_osc_type(proposal["value"])

    @property
    def frequency(self) -> Signal:
        """Vibrato frequency."""
        return self._frequency

    @property
    def depth(self) -> Param:
        """Vibrato depth."""
        return self._depth

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._frequency.dispose()
            self._depth.dispose()

        return self
