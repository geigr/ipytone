import contextlib

from ipywidgets import widget_serialization
from traitlets import Bool, Float, Instance, Int, List, Unicode, Union

from .base import ToneObject
from .callback import TimeCallbackArg, add_or_send_event
from .core import Param
from .observe import ScheduleObserveMixin
from .signal import Signal


class Transport(ToneObject, ScheduleObserveMixin):
    """Transport for timing musical events.

    Note: the transport position is not updated until changing the playback state
    (play/pause/stop) or explicitly setting a new position.

    """

    _singleton = None

    _model_name = Unicode("TransportModel").tag(sync=True)

    _bpm = Instance(Param).tag(sync=True, **widget_serialization)
    time_signature = Union(
        [Int(), List(trait=Int(), minlen=2, maxlen=2)],
        default_value=4,
        help="transport time signature",
    ).tag(sync=True)

    loop_start = Union(
        [Float(), Unicode()], default_value=0, help="starting position of transport loop"
    ).tag(sync=True)
    loop_end = Union(
        [Float(), Unicode()], default_value="4m", help="ending position of transport loop"
    ).tag(sync=True)
    loop = Bool(False, help="whether the transport loops or not").tag(sync=True)

    swing = Float(0, help="transport swing").tag(sync=True)
    swing_subdivision = Unicode("8n", help="transport swing subdivision").tag(sync=True)

    position = Union([Float(), Unicode()], default_value=0, help="transport position").tag(
        sync=True
    )
    seconds = Float(0, help="transport position in seconds").tag(sync=True)
    progress = Float(0, help="transport loop relative position", read_only=True).tag(sync=True)
    ticks = Int(0, help="transport position in ticks").tag(sync=True)

    _observable_traits = List(["state", "progress", "position", "ticks", "seconds"])
    _default_observed_trait = "state"

    def __new__(cls):
        if Transport._singleton is None:
            Transport._singleton = super(Transport, cls).__new__(cls)
        return Transport._singleton

    def __init__(self, **kwargs):
        bpm_param = Param(value=120, units="bpm", _create_node=False)
        kwargs.update({"_bpm": bpm_param})

        self._py_event_id = 0
        self._all_event_id = set()
        self._synced_signals = {}

        super(Transport, self).__init__(**kwargs)

    @property
    def bpm(self) -> Param:
        """Transport tempo parameter (beats per minute)."""
        return self._bpm

    def set_loop_points(self, start, end):
        """Set the transport loop start and stop positions."""
        self.loop_start = start
        self.loop_end = end
        return self

    def _get_callback_items(self, callback):
        callback_arg = TimeCallbackArg(self)
        callback(callback_arg)
        items = callback_arg.items
        callback_arg._disposed = True
        return items

    def _get_event_id_and_inc(self, append=True):
        event_id = self._py_event_id
        if append:
            self._all_event_id.add(event_id)
        self._py_event_id += 1
        return event_id

    def schedule(self, callback, time):
        """Schedule an event along the transport timeline.

        Parameters
        ----------
        callback : callable
            The callback to be invoked at the scheduled time. It must accept exactly
            one argument that corresponds to the time value (in seconds).
        time : str or float
            The time to invoke the callback at (any value/units supported by
            Tone.js ``Time``).

        Returns
        -------
        event_id : int
            The id of the event which can be used for canceling the event.

        """
        items = self._get_callback_items(callback)
        event_id = self._get_event_id_and_inc()
        self.send({"event": "schedule", "op": "", "id": event_id, "items": items, "time": time})
        return event_id

    def schedule_repeat(self, callback, interval, start_time=0, duration=None):
        """Schedule a repeated event along the transport timeline.

        The event may start at a given time and may be repeated only for a
        specified duration.

        Parameters
        ----------
        callback : callable
            The callback to be invoked at the scheduled time. It must accept exactly
            one argument that corresponds to the time value (in seconds).
        interval : str or float
            The duration between successive callbacks (any value/units supported by
            Tone.js ``Time`` but must be positive).
        start_time : str or float, optional
            When along the timeline the events should start being invoked (default: at the
            beginning of the timeline).
        duration : str or float, optional
            How long the event should repeat (default: indefinitely).

        Returns
        -------
        event_id : int
            The id of the event which can be used for canceling the event.

        """
        items = self._get_callback_items(callback)
        event_id = self._get_event_id_and_inc()
        self.send(
            {
                "event": "schedule",
                "op": "repeat",
                "id": event_id,
                "items": items,
                "interval": interval,
                "start_time": start_time,
                "duration": duration,
            }
        )
        return event_id

    def schedule_once(self, callback, time):
        """Schedule an event along the transport timeline.

        After being invoked, the event is removed.

        Parameters
        ----------
        callback : callable
            The callback to be invoked at the scheduled time. It must accept exactly
            one argument that corresponds to the time value (in seconds).
        time : str or float
            The time to invoke the callback at (any value/units supported by
            Tone.js ``Time``).

        Returns
        -------
        event_id : int
            The id of the event which can be used for canceling the event.

        """
        items = self._get_callback_items(callback)
        event_id = self._get_event_id_and_inc(append=False)
        self.send({"event": "schedule", "op": "once", "id": event_id, "items": items, "time": time})
        return event_id

    def clear(self, event_id):
        """Clear an event from the timeline.

        Parameters
        ----------
        event_id : int
            The id of the event to clear.

        """
        if event_id not in self._all_event_id:
            raise ValueError(f"Scheduled event ID not found: {event_id}")
        self.send({"event": "clear", "id": event_id})
        self._all_event_id.remove(event_id)
        return self

    def cancel(self, after=0):
        """Clear all scheduled events on the timeline that would
        start after a given time.

        Parameters
        ----------
        after : str or float
            The time threshold along the transport timeline.

        """
        self.send({"event": "cancel", "after": after})
        return self

    def start(self, time=None, offset=None):
        """Start the transport and all sources synced to the transport.

        Parameters
        ----------
        time : str or float
            The time time when the transport should start.
        offset : str or float
            The timeline offset (position) to start the transport.

        """
        add_or_send_event("start", self, {"time": time, "offset": offset}, event="play")
        return self

    def stop(self, time=None):
        """Stop the transport and all sources synced to the transport.

        Parameters
        ----------
        time : str or float
            The time time when the transport should stop.

        """
        add_or_send_event("stop", self, {"time": time}, event="play")
        return self

    def pause(self, time=None):
        """Pause the transport and all sources synced to the transport.

        Parameters
        ----------
        time : str or float
            The time time when the transport should pause.

        """
        add_or_send_event("pause", self, {"time": time}, event="play")
        return self

    def toggle(self, time=None):
        """Toggle the current playback state of the transport.

        Parameters
        ----------
        time : str or float
            The time of the event.

        """
        add_or_send_event("toggle", self, {"time": time}, event="play")
        return self

    def sync_signal(self, signal, ratio=None):
        """Attach a signal to the tempo so that any change in the tempo
        will change the signal in the same ratio.

        Parameters
        ----------
        signal : :class:`ipytone.Signal`
            The audio signal object to sync with the tempo.
        ratio : float, optional
            Ratio between the signal value and the tempo BPM value. By default
            computed from their current values.

        """
        if not isinstance(signal, Signal):
            raise TypeError("signal must be an ipytone.Signal object")

        self.send({"event": "sync_signal", "op": "sync", "signal": signal.model_id, "ratio": ratio})
        self._synced_signals[signal.model_id] = ratio

        return self

    def unsync_signal(self, signal):
        """Unsync a previously synced signal.

        Parameters
        ----------
        signal : :class:`ipytone.Signal`
            The audio signal object to unsync with the tempo.

        """
        if not isinstance(signal, Signal):
            raise TypeError("signal must be an ipytone.Signal object")
        if signal.model_id not in self._synced_signals:
            raise KeyError(f"signal {signal!r} is not synced with transport")

        self.send({"event": "sync_signal", "op": "unsync", "signal": signal.model_id})
        del self._synced_signals[signal.model_id]

        return self

    def dispose(self):
        self.cancel()
        self._all_event_id.clear()
        self.bpm.dispose()
        super().dispose()

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if self.loop:
            yield "loop"
            yield "loop_start"
            yield "loop_end"


transport = Transport()


@contextlib.contextmanager
def schedule(time):
    """Like :meth:`ipytone.transport.schedule` but used as a context manager.

    Examples
    --------

    >>> osc = ipytone.Oscillator().to_destination()
    >>> with ipytone.schedule("1m") as (time, event_id):
    ...     osc.start(time).stop(time + 1)
    >>> ipytone.transport.start()

    """
    time_arg = TimeCallbackArg(transport)
    event_id = transport._get_event_id_and_inc()
    yield time_arg, event_id
    transport.send(
        {"event": "schedule", "op": "", "id": event_id, "items": time_arg.items, "time": time}
    )
    time_arg._disposed = True


@contextlib.contextmanager
def schedule_repeat(interval, start_time=0, duration=None):
    """Like :meth:`ipytone.transport.schedule_repeat` but used as a context manager.

    Examples
    --------

    >>> osc = ipytone.Oscillator().to_destination()
    >>> with ipytone.schedule_repeat("1m", "1m") as (time, event_id):
    ...     osc.start(time).stop(time + 1)
    >>> ipytone.transport.start()

    """
    time_arg = TimeCallbackArg(transport)
    event_id = transport._get_event_id_and_inc()
    yield time_arg, event_id
    transport.send(
        {
            "event": "schedule",
            "op": "repeat",
            "id": event_id,
            "items": time_arg.items,
            "interval": interval,
            "start_time": start_time,
            "duration": duration,
        }
    )
    time_arg._disposed = True


@contextlib.contextmanager
def schedule_once(time):
    """Like :meth:`ipytone.transport.schedule_once` but used as a context manager.

    Examples
    --------

    >>> osc = ipytone.Oscillator().to_destination()
    >>> with ipytone.schedule_once("1m") as (time, event_id):
    ...     osc.start(time).stop(time + 1)
    >>> ipytone.transport.start()

    """
    time_arg = TimeCallbackArg(transport)
    event_id = transport._get_event_id_and_inc(append=False)
    yield time_arg, event_id
    transport.send(
        {"event": "schedule", "op": "once", "id": event_id, "items": time_arg.items, "time": time}
    )
    time_arg._disposed = True
