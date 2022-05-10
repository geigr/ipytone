from ipywidgets import widget_serialization
from traitlets import Bool, Instance, Unicode

from .base import AudioNode, PyAudioNode
from .core import Gain, NativeAudioNode, Param, Volume
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

    def __init__(self, pan=0, channel_count=1, **kwargs):
        panner_node = NativeAudioNode(type="StereoPannerNode")
        pan_node = Param(value=pan, units="audioRange", _create_node=False)

        kwargs.update({"_pan": pan_node, "_input": panner_node, "_output": panner_node})
        super().__init__(channel_count=channel_count, channel_count_mode="explicit", **kwargs)

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


class PanVol(PyAudioNode):
    """Panner and Volume in one."""

    def __init__(self, pan=0, volume=0, mute=False, channel_count=1, **kwargs):
        self._panner = Panner(pan=pan, channel_count=channel_count)
        self._volume = Volume(volume=volume, mute=mute)
        self._panner.connect(self._volume)
        super().__init__(
            self._panner,
            self._volume,
            channel_count=channel_count,
            channel_count_mode="explicit",
            **kwargs
        )

    @property
    def pan(self) -> Param:
        """Pan control parameter.

        value = -1 -> hard left
        value =  1 -> hard right

        """
        return self._panner.pan

    @property
    def volume(self) -> Param:
        """Volume control in decibels."""
        return self._volume.volume

    @property
    def mute(self) -> bool:
        return self._volume.mute

    @mute.setter
    def mute(self, value):
        self._volume.mute = value


class Solo(AudioNode):
    """An audio node to isolate a specific audio stream from audio streams
    connected to other solo nodes.

    When an instance is set to ``solo = True`` it will mute all other instances
    of ``Solo``.

    """

    _model_name = Unicode("SoloModel").tag(sync=True)

    solo = Bool(False, help="if True, all other Solo instances are muted").tag(sync=True)

    def __init__(self, **kwargs):
        gain = Gain(_create_node=False)
        kwargs.update({"_input": gain, "_output": gain})
        super().__init__(**kwargs)

    @property
    def muted(self):
        """If the current instance is muted, i.e., another instance is soloed"""
        return self.input.gain.value == 0
