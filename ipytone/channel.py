from ipywidgets import widget_serialization
from traitlets import Instance, Unicode

from .base import AudioNode
from .core import Gain, NativeAudioNode, Param
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


class Panner(AudioNode):
    """An audio node that provides equal power left/right panner."""

    _model_name = Unicode("PannerModel").tag(sync=True)

    _pan = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, pan=0, **kwargs):
        panner_node = NativeAudioNode(type="StereoPannerNode")
        pan_node = Param(value=pan, units="audioRange", _create_node=False)

        kwargs.update({"_pan": pan_node, "_input": panner_node, "_output": panner_node})
        super().__init__(**kwargs)

    @property
    def pan(self) -> Param:
        """Pan control parameter.

        value = -1 -> hard left
        value =  1 -> hard right

        """
        return self._pan

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "pan"

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._pan.dispose()

        return self
