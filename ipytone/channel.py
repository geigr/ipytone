from ipywidgets import widget_serialization
from traitlets import Bool, Enum, Float, Instance, Int, Unicode

from .base import AudioNode, PyAudioNode
from .core import Gain, NativeAudioNode, Param, Volume
from .filter import Filter
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
        yield from super()._repr_keys()
        yield "pan"

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._pan.dispose()

        return self


class Panner3D(AudioNode):
    """A spatialized panner audio node that provides equal power or HRTF panning.

    For more details about the 3D spatial reference system, see
    :py:class:`Listener`.

    """

    _model_name = Unicode("Panner3DModel").tag(sync=True)

    _position_x = Instance(Param).tag(sync=True, **widget_serialization)
    _position_y = Instance(Param).tag(sync=True, **widget_serialization)
    _position_z = Instance(Param).tag(sync=True, **widget_serialization)

    _orientation_x = Instance(Param).tag(sync=True, **widget_serialization)
    _orientation_y = Instance(Param).tag(sync=True, **widget_serialization)
    _orientation_z = Instance(Param).tag(sync=True, **widget_serialization)

    panning_model = Enum(
        ["equal_power", "HRTF"], default_value="equal_power", help="panning model"
    ).tag(sync=True)

    distance_model = Enum(
        ["linear", "inverse", "exponential"],
        default_value="inverse",
        help="distance model for source volume reduction",
    ).tag(sync=True)

    ref_distance = Float(1.0, help="reference distance for source volume reduction").tag(sync=True)

    rolloff_factor = Float(
        1.0, help="controls the amount of source volume reduction with distance"
    ).tag(sync=True)

    max_distance = Float(
        10000.0, help="max distance between the source and listener (beyond, no volume reduction)"
    ).tag(sync=True)

    cone_inner_angle = Float(
        360.0, help="angle inside of which there is no volume reduction (degrees)"
    ).tag(sync=True)

    cone_outer_angle = Float(
        360.0, help="angle outside of which volume is reduced to a constant (degrees)"
    ).tag(sync=True)

    cone_outer_gain = Float(0.0, help="gain value outside of the cone outer angle").tag(sync=True)

    def __init__(
        self,
        position=(0, 0, 0),
        orientation=(0, 0, 0),
        **kwargs,
    ):
        panner_node = NativeAudioNode(type="PannerNode")

        nodes = {
            "_input": panner_node,
            "_output": panner_node,
            "_position_x": Param(value=position[0], _create_node=False),
            "_position_y": Param(value=position[1], _create_node=False),
            "_position_z": Param(value=position[2], _create_node=False),
            "_orientation_x": Param(value=orientation[0], _create_node=False),
            "_orientation_y": Param(value=orientation[1], _create_node=False),
            "_orientation_z": Param(value=orientation[2], _create_node=False),
        }

        kwargs.update(nodes)
        super().__init__(_set_node_channels=False, **kwargs)

    @property
    def position_x(self) -> Param:
        """source position x-coordinate."""
        return self._position_x

    @property
    def position_y(self) -> Param:
        """source position y-coordinate."""
        return self._position_y

    @property
    def position_z(self) -> Param:
        """source position z-coordinate."""
        return self._position_z

    def set_position(self, x, y, z):
        """Convenient method to set the x-y-z coordinate position of the
        source.

        """
        self._position_x.value = x
        self._position_y.value = y
        self._position_z.value = z
        return self

    @property
    def orientation_x(self) -> Param:
        """source orientation x-coordinate."""
        return self._orientation_x

    @property
    def orientation_y(self) -> Param:
        """source orientation y-coordinate."""
        return self._orientation_y

    @property
    def orientation_z(self) -> Param:
        """source orientation z-coordinate."""
        return self._orientation_z

    def set_orientation(self, x, y, z):
        """Convenient method to set the x-y-z coordinate orientation of the
        source.

        """
        self._orientation_x.value = x
        self._orientation_y.value = y
        self._orientation_z.value = z
        return self

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._position_x.dispose()
            self._position_y.dispose()
            self._position_z.dispose()
            self._orientation_x.dispose()
            self._orientation_y.dispose()
            self._orientation_z.dispose()

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
    """An audio node that merges multiple mono input channels into a single
    multichannel output channel.

    """

    _model_name = Unicode("MergeModel").tag(sync=True)

    _channels = Int(2).tag(sync=True)

    def __init__(self, channels=2, **kwargs):
        merger = NativeAudioNode(type="ChannelMergerNode")
        super().__init__(
            _input=merger, _output=merger, _channels=channels, _set_node_channels=False, **kwargs
        )

    @property
    def channels(self):
        return self._channels

    def _repr_keys(self):
        yield from super()._repr_keys()
        yield "channels"


class Split(AudioNode):
    """An audio node that splits an incoming signal into the number of given channels."""

    _model_name = Unicode("SplitModel").tag(sync=True)

    _channels = Int(2).tag(sync=True)

    def __init__(self, channels=2, **kwargs):
        splitter = NativeAudioNode(type="ChannelSplitterNode")
        super().__init__(
            _input=splitter,
            _output=splitter,
            _channels=channels,
            _set_node_channels=False,
            **kwargs,
        )

    @property
    def channels(self):
        return self._channels

    def _repr_keys(self):
        yield from super()._repr_keys()
        yield "channels"


class MultibandSplit(PyAudioNode):
    """Split the incoming signal into three bands (low, mid, high), with
    cross-over frequency controls.

    """

    def __init__(self, low_frequency=400, high_frequency=2500, q=1, **kwargs):
        in_gain = Gain()

        self._low = Filter(frequency=0, type="lowpass")
        self._low_mid = Filter(frequency=0, type="highpass")
        self._mid = Filter(frequency=0, type="lowpass")
        self._high = Filter(frequency=0, type="highpass")

        self._low_frequency = Signal(units="frequency", value=low_frequency)
        self._high_frequency = Signal(units="frequency", value=high_frequency)
        self._q = Signal(units="positive", value=q)

        super().__init__(in_gain, None, **kwargs)

        # connections
        with self._graph.hold_state():
            in_gain.fan(self._low, self._high)
            in_gain.chain(self._low_mid, self._mid)

            self._low_frequency.fan(self._low.frequency, self._low_mid.frequency)
            self._high_frequency.fan(self._mid.frequency, self._high.frequency)

            self._q.fan(self._low.q, self._low_mid.q, self._mid.q, self._high.q)

    @property
    def low(self) -> Filter:
        """returns the low band filter."""
        return self._low

    @property
    def mid(self) -> Filter:
        """returns the mid band filter."""
        return self._mid

    @property
    def high(self) -> Filter:
        """returns the high band filter."""
        return self._high

    @property
    def low_frequency(self) -> Signal:
        """Low/mid cross-over frequency."""
        return self._low_frequency

    @property
    def high_frequency(self) -> Signal:
        """Mid/high cross-over frequency."""
        return self._high_frequency

    @property
    def q(self) -> Signal:
        """Filter Q factor."""
        return self._q

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        for key in ["low_frequency", "high_frequency", "q"]:
            yield key

    def dispose(self):
        with self._graph.hold_state():
            super().dispose()
            self._low.dispose()
            self._low_mid.dispose()
            self._mid.dispose()
            self._high.dispose()
            self._low_frequency.dispose()
            self._high_frequency.dispose()
            self._q.dispose()
        return self


class Mono(PyAudioNode):
    """An audio node that coerces an incoming audio signal (mono or stereo) into
    a mono signal.

    """

    def __init__(self, **kwargs):
        gain = Gain()
        merge = Merge()
        gain.connect(merge, 0, 0)
        gain.connect(merge, 0, 1)
        kwargs.update({"_set_node_channels": False})
        super().__init__(gain, merge, **kwargs)
