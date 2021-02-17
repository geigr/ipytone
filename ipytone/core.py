from traitlets import Unicode, Float, Bool

from .base import AudioNode


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


_DESTINATION = Destination()


def get_destination():
    """Returns ipytone's audio master node."""
    return _DESTINATION
