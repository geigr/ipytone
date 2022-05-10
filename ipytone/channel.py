from ipywidgets import widget_serialization
from traitlets import Bool, Instance, Int, Unicode

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
            **kwargs,
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
    def muted(self) -> bool:
        """If the current instance is muted, i.e., another instance is soloed"""
        return self.input.gain.value == 0


class Channel(PyAudioNode):
    """An audio node that provides a channel strip interface with volume, pan,
    solo and mute controls.

    This node may also be used to create channel buses that may receive audio
    from one or more other channels.

    """

    # all channel buses that may be accessed by their name
    _buses = {}

    def __init__(self, pan=0, volume=0, solo=False, mute=False, channel_count=1, **kwargs):
        self._solo = Solo(solo=solo)
        self._panvol = PanVol(pan=pan, volume=volume, mute=mute, channel_count=channel_count)
        self._solo.connect(self._panvol)
        super().__init__(
            self._solo,
            self._panvol,
            channel_count=channel_count,
            channel_count_mode="explicit",
            **kwargs,
        )

    @property
    def pan(self) -> Param:
        return self._panvol.pan

    @property
    def volume(self) -> Param:
        return self._panvol.volume

    @property
    def solo(self):
        return self._solo.solo

    @solo.setter
    def solo(self, value):
        self._solo.solo = value

    @property
    def muted(self) -> bool:
        """If the current instance is muted, i.e., another instance is soloed"""
        return self._solo.muted or self.mute

    @property
    def mute(self) -> bool:
        return self._panvol.mute

    @mute.setter
    def mute(self, value):
        self._panvol.mute = value

    def _get_bus(self, name) -> Gain:
        """Get access to the bus channel referenced by ``name`` via a Gain
        node (create the node if it doesn't exists yet)."""
        if name not in self._buses:
            self._buses[name] = Gain()
        return self._buses[name]

    def send(self, name, volume=0) -> Gain:
        """Send audio from this channel (post-fader) to the channel bus.

        Parameters
        ----------
        name : str
            Name of the bus channel.
        volume : float
            Amount of the signal to send in decibels (default: 0, full signal).

        Returns
        -------
        gain : :class:`ipytone.Gain`
            The (new) gain node through which the audio signal is sent to the bus channel.

        """
        bus_gain = self._get_bus(name)
        send_gain = Gain(gain=volume, units="decibels")
        self.connect(send_gain)
        send_gain.connect(bus_gain)
        return send_gain

    def receive(self, name):
        """Receive audio from a bus channel referenced by ``name``."""
        bus_gain = self._get_bus(name)
        bus_gain.connect(self)
        return self


class Merge(AudioNode):
    """An audio node for merging multiple mono input channels into a single
    multichannel output channel.

    """

    _model_name = Unicode("MergeModel").tag(sync=True)

    channels = Int(2, help="number of channels to merge", read_only=True).tag(sync=True)

    def __init__(self, **kwargs):
        merger = NativeAudioNode(type="ChannelMergerNode")
        super().__init__(_input=merger, _output=merger, _set_node_channels=False, **kwargs)

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "channels"
