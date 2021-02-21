from traitlets import Bool, Float, Int, Unicode

from .base import AudioNode, ToneWidgetBase


class InternalNode(ToneWidgetBase):
    """Ipytone Widget that wraps a Tone.js object with no exposed functionality."""

    _model_name = Unicode("InternalNodeModel").tag(sync=True)

    _is_internal = True
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    tone_class = Unicode().tag(sync=True)

    @property
    def number_of_inputs(self):
        return self._n_inputs

    @property
    def number_of_outputs(self):
        return self._n_outputs

    def _repr_keys(self):
        if self.tone_class:
            yield "tone_class"


class InternalAudioNode(AudioNode):
    """Ipytone Widget that wraps a Tone.js audio node instance with no exposed functionality."""

    _model_name = Unicode("InternalAudioNodeModel").tag(sync=True)

    _is_internal = True
    _n_inputs = Int(1, allow_none=True).tag(sync=True)
    _n_outputs = Int(1, allow_none=True).tag(sync=True)
    tone_class = Unicode().tag(sync=True)
    _create_node = Bool(False).tag(sync=True)

    def _repr_keys(self):
        if self.tone_class:
            yield "tone_class"


class Destination(AudioNode):
    """Audio master node."""

    _singleton = None

    _model_name = Unicode("DestinationModel").tag(sync=True)

    name = Unicode("main output").tag(sync=True)

    mute = Bool(False).tag(sync=True)
    volume = Float(-16).tag(sync=True)

    def __new__(cls):
        if Destination._singleton is None:
            Destination._singleton = super(Destination, cls).__new__(cls)
        return Destination._singleton

    def __init__(self, *args, **kwargs):
        in_node = InternalAudioNode(tone_class="Gain")
        out_node = InternalAudioNode(tone_class="Volume")

        kwargs.update({"_input": in_node, "_output": out_node})
        super().__init__(*args, **kwargs)


_DESTINATION = Destination()


def get_destination():
    """Returns ipytone's audio master node."""
    return _DESTINATION
