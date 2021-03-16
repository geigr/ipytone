from ipywidgets import widget_serialization
from traitlets import Instance, Unicode

from .base import AudioNode
from .core import Gain
from .signal import Signal


class CrossFade(AudioNode):
    """An audio node that provides equal power fading between two a/b inputs."""

    _model_name = Unicode("CrossFadeModel").tag(sync=True)

    _a = Instance(Gain).tag(sync=True, **widget_serialization)
    _b = Instance(Gain).tag(sync=True, **widget_serialization)
    _fade = Instance(Signal).tag(sync=True, **widget_serialization)

    def __init__(self, fade=0.5, **kwargs):
        a_node = Gain(gain=0, _create_node=False)
        b_node = Gain(gain=0, _create_node=False)
        out_node = Gain(_create_node=False)
        fade_node = Signal(value=fade, units="normalRange", _create_node=False)

        kwargs.update({"_a": a_node, "_b": b_node, "_output": out_node, "_fade": fade_node})
        super().__init__(**kwargs)

    @property
    def a(self) -> Gain:
        """The input which is at full level when fade = 0."""
        return self._a

    @property
    def b(self) -> Gain:
        """The input which is at full level when fade = 1."""
        return self._b

    @property
    def fade(self) -> Signal:
        """A signal node which value sets the mix between the two a/b inputs.

        A fade value of 0 will output 100% of input a and
        a fade value of 1 will output 100% of input b.

        """
        return self._fade

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._a.dispose()
            self._b.dispose()
            self._fade.dispose()

        return self
