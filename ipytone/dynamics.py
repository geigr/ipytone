from ipywidgets import widget_serialization
from traitlets import Instance, Unicode

from .base import AudioNode, NativeAudioNode, PyAudioNode
from .core import Param


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
