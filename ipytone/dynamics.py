from ipywidgets import widget_serialization
from traitlets import Instance, Unicode

from .base import AudioNode, NativeAudioNode, PyAudioNode
from .channel import MultibandSplit
from .core import Gain, Param
from .signal import Signal


class Compressor(AudioNode):
    """Simple compressor."""

    _model_name = Unicode("CompressorModel").tag(sync=True)

    _threshold = Instance(Param).tag(sync=True, **widget_serialization)
    _ratio = Instance(Param).tag(sync=True, **widget_serialization)
    _attack = Instance(Param).tag(sync=True, **widget_serialization)
    _release = Instance(Param).tag(sync=True, **widget_serialization)
    _knee = Instance(Param).tag(sync=True, **widget_serialization)

    def __init__(self, threshold=-24, ratio=12, attack=0.003, release=0.25, knee=30, **kwargs):
        _compressor = NativeAudioNode(type="DynamicsCompressorNode")

        kws = {
            "_threshold": Param(
                units="decibels", value=threshold, min_value=-100, max_value=0, _create_node=False
            ),
            "_ratio": Param(
                units="positive", value=ratio, min_value=1, max_value=20, _create_node=False
            ),
            "_attack": Param(
                units="time", value=attack, min_value=0, max_value=1, _create_node=False
            ),
            "_release": Param(
                units="time", value=release, min_value=0, max_value=1, _create_node=False
            ),
            "_knee": Param(
                units="decibels", value=knee, min_value=0, max_value=40, _create_node=False
            ),
            "_input": _compressor,
            "_output": _compressor,
            # TODO: check if this is relevant
            "_set_node_channels": False,
        }
        kwargs.update(kws)

        super().__init__(**kwargs)

    @property
    def threshold(self) -> Param:
        """Threshold parameter."""
        return self._threshold

    @property
    def ratio(self) -> Param:
        """Ratio parameter."""
        return self._ratio

    @property
    def attack(self) -> Param:
        """Attack parameter."""
        return self._attack

    @property
    def release(self) -> Param:
        """Release parameter."""
        return self._release

    @property
    def knee(self) -> Param:
        """Knee parameter."""
        return self._knee

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["threshold", "ratio"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._threshold.dispose()
            self._ratio.dispose()
            self._attack.dispose()
            self._release.dispose()
            self._knee.dispose()
        return self


class Limiter(PyAudioNode):
    """Simple limiter (i.e., compressor with fast attack/release and max compression ratio)."""

    def __init__(self, threshold=-12, **kwargs):
        self._comp = Compressor(threshold=threshold, ratio=20, attack=0.003, release=0.01)
        kwargs.update({"_set_node_channels": False})
        super().__init__(self._comp, self._comp, **kwargs)

    @property
    def threshold(self) -> Param:
        """Threshold parameter."""
        return self._comp.threshold


class MultibandCompressor(PyAudioNode):
    """Three-band (low/mid/high) compressor."""

    def __init__(
        self, low=None, mid=None, high=None, low_frequency=250, high_frequency=2000, **kwargs
    ):
        if low is None:
            low = {"ratio": 6, "threshold": -30, "attack": 0.03, "release": 0.25, "knee": 10}
        if mid is None:
            mid = {"ratio": 3, "threshold": -24, "attack": 0.02, "release": 0.3, "knee": 16}
        if high is None:
            high = {"ratio": 3, "threshold": -24, "attack": 0.02, "release": 0.3, "knee": 16}

        msplit = MultibandSplit(low_frequency=low_frequency, high_frequency=high_frequency)
        out_gain = Gain()

        super().__init__(msplit, out_gain, _set_node_channels=False, **kwargs)

        self._low = Compressor(**low)
        self._mid = Compressor(**mid)
        self._high = Compressor(**high)

        # connections
        msplit.low.chain(self._low, out_gain)
        msplit.mid.chain(self._mid, out_gain)
        msplit.high.chain(self._high, out_gain)

    @property
    def low(self) -> Compressor:
        """Low band compressor."""
        return self._low

    @property
    def mid(self) -> Compressor:
        """Mid band compressor."""
        return self._mid

    @property
    def high(self) -> Compressor:
        """High band compressor."""
        return self._high

    @property
    def low_frequency(self) -> Signal:
        """Low/mid cross-over frequency."""
        return self.input.low_frequency

    @property
    def high_frequency(self) -> Signal:
        """Mid/high cross-over frequency."""
        return self.input.high_frequency

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._low.dispose()
            self._mid.dispose()
            self._high.dispose()
        return self
