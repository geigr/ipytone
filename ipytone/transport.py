import contextlib

from traitlets import Unicode

from .base import ToneObject


class BaseCallbackArg:
    """Base class internally used as a placeholder for any tone event or
    scheduling callback argument.

    """

    def __init__(self, caller, value=None):
        self.caller = caller
        self.value = value
        self._parent = None
        self._disposed = False
        self._items = []

    def derive(self, value):
        new_obj = type(self)(self.caller, value=value)
        new_obj._disposed = self._disposed
        new_obj._parent = self
        return new_obj

    @property
    def items(self):
        if self._disposed:
            raise RuntimeError(
                f"Callback argument placeholder {self!r} is used outside of its context."
            )

        items = self._items

        parent = self._parent
        while parent is not None:
            items = parent._items
            parent = parent._parent

        return items

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value!r})"


class ScheduleCallbackArg(BaseCallbackArg):
    def __init__(self, *args, value="time", **kwargs):
        super().__init__(*args, value=value, **kwargs)

    def __add__(self, other):
        return self.derive(f"{self.value} + {other}")


def add_or_send_event(name, callee, args, event="trigger"):
    """Add a specific event (i.e., Tone object method call + args) for scheduling or
    send it directly to the front-end.

    """
    time = args["time"]
    data = {"method": name, "args": args.copy(), "arg_keys": list(args.keys())}

    if isinstance(time, BaseCallbackArg):
        data["args"]["time"] = time.value
        data["callee"] = callee.model_id
        time.items.append(data)
    else:
        data["event"] = event
        callee.send(data)


class Transport(ToneObject):
    """Transport for timing musical events."""

    _singleton = None

    _model_name = Unicode("TransportModel").tag(sync=True)

    def __new__(cls):
        if Transport._singleton is None:
            Transport._singleton = super(Transport, cls).__new__(cls)
        return Transport._singleton

    def __init__(self, **kwargs):
        self._py_event_id = 0
        self._all_event_id = set()
        super(Transport, self).__init__(**kwargs)

    def _get_callback_items(self, callback):
        callback_arg = ScheduleCallbackArg(self)
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

    def start(self, time=None, offset=None):
        add_or_send_event("start", self, {"time": time, "offset": offset}, event="play")
        return self

    def stop(self, time=None):
        add_or_send_event("stop", self, {"time": time}, event="play")
        return self

    def pause(self, time=None):
        add_or_send_event("pause", self, {"time": time}, event="play")
        return self

    def toggle(self, time=None):
        add_or_send_event("toggle", self, {"time": time}, event="play")
        return self

    def dispose(self):
        for eid in list(self._all_event_id):
            self.clear(eid)

        super().dispose()


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
    time_arg = ScheduleCallbackArg(transport)
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
    time_arg = ScheduleCallbackArg(transport)
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
    time_arg = ScheduleCallbackArg(transport)
    event_id = transport._get_event_id_and_inc(append=False)
    yield time_arg, event_id
    transport.send(
        {"event": "schedule", "op": "once", "id": event_id, "items": time_arg.items, "time": time}
    )
    time_arg._disposed = True
