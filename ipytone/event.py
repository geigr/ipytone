from collections.abc import Mapping
from typing import Callable

from traitlets import Any, Bool, Enum, Float, Int, List, Unicode, Union

from .base import NodeWithContext
from .callback import (
    EventValueCallbackArg,
    TimeCallbackArg,
    add_or_send_event,
    collect_and_merge_items,
)
from .observe import ScheduleObserveMixin


def _no_callback(time, value=None):
    pass


class Event(NodeWithContext, ScheduleObserveMixin):
    """Represents a single or repeatable event along the transport timeline.

    It abstracts away :func:`ipytone.transport.schedule`.
    """

    _model_name = Unicode("EventModel").tag(sync=True)

    value = Any(allow_none=True).tag(sync=True)

    # TODO: create a Time traitlet => Union((Int(), Float(), Unicode()))?
    humanize = Union(
        (Bool(), Float(), Unicode()),
        default_value=False,
        help="if True, apply small or user-defined random variations to callback time",
    ).tag(sync=True)
    probability = Float(1, help="probability of the event being triggered").tag(sync=True)
    mute = Bool(False, help="if True, the callback is deactivated").tag(sync=True)

    start_offset = Int(0, help="start from scheduled start time (ticks)").tag(sync=True)
    playback_rate = Float(1, help="Playback rate of the event (normal speed is 1)").tag(sync=True)

    loop = Union(
        (Bool(), Int()),
        default_value=False,
        help="Loop the event indefinitely (True) or a given number of times",
    ).tag(sync=True)
    loop_start = Union(
        (Float(), Unicode()), default_value=0, help="loop starting (transport) time"
    ).tag(sync=True)
    loop_end = Union(
        (Float(), Unicode()), default_value="1m", help="loop ending (transport) time"
    ).tag(sync=True)

    _observable_traits = List(["state", "progress"])
    _default_observed_trait = "state"

    def __init__(self, callback=None, value=None, **kwargs):
        if callback is None:
            callback = _no_callback

        kwargs.update({"value": value})
        super().__init__(**kwargs)

        self.callback = callback

    @property
    def callback(self) -> Callable:
        return self._callback

    @callback.setter
    def callback(self, func: Callable):
        self._callback = func
        self._set_js_callback()

    def _set_js_callback(self):
        time_arg = TimeCallbackArg(self)
        value_arg = EventValueCallbackArg(self)
        self._callback(time_arg, value_arg)

        items = collect_and_merge_items(time_arg, value_arg)

        time_arg._disposed = True
        value_arg._disposed = True

        data = {
            "event": "set_callback",
            "op": "",
            "items": items,
        }
        self.send(data)

    def start(self, time=None):
        """Start the event at the given (transport) time."""
        add_or_send_event("start", self, {"time": time}, event="play")
        return self

    def stop(self, time=None):
        """Stop the event at the given (transport) time."""
        add_or_send_event("stop", self, {"time": time}, event="play")
        return self

    def cancel(self, time=None):
        """Clear all scheduled events of this ``Event`` greater or equal
        to the given (transport) time.

        """
        self.send({"event": "cancel", "time": time})
        return self

    def dispose(self):
        self.cancel()
        super().dispose()
        return self

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        if self.mute:
            yield "mute"
        if self.loop:
            yield "loop"
            yield "loop_start"
            yield "loop_end"


class Note:
    """A single note with time, note (frequency) and velocity values.

    This is useful for directly calling a :class:`ipytone.Part` callback
    with multiple notes (unlike Tone.js, every note passed as value to the
    callback must have a defined structure, i.e., no arbitrary attributes).

    Note: duration units is seconds.

    """

    def __init__(self, time, note, velocity=1, duration=0.1):
        self.time = time
        self.note = note
        self.velocity = velocity
        self.duration = duration

    def to_dict(self):
        return {
            "time": self.time,
            "note": self.note,
            "velocity": self.velocity,
            "duration": self.duration,
        }


def _normalize_note(value):
    if isinstance(value, Note):
        return value
    elif isinstance(value, Mapping):
        return Note(**value)
    else:
        raise ValueError(f"cannot interpret this value as a Note: {value}")


class Part(Event):
    """A collection of events (notes) that can be handled as a single unit.

    Currently doesn't support access to the underlying Event instances from
    within Python.

    """

    _model_name = Unicode("PartModel").tag(sync=True)

    # note: this is currently used only at object creation, it is not updated afterwards
    _events = List(Any()).tag(sync=True)

    length = Int(0, read_only=True, help="number of scheduled notes in the part").tag(sync=True)

    def __init__(self, callback=None, events=None, **kwargs):
        """

        Parameters
        ----------
        callback : callable, optional
             Scheduling callback, which must accept two arguments (time, value).
        events : list, optional
             A list of note events, i.e., each item being a :class:`Note` instance
             or a dictionnary with "time", "note" (and optionally "velocity") keys.

        """
        if events is None:
            events = []
        events = [_normalize_note(e).to_dict() for e in events]

        kwargs.update({"callback": callback, "_events": events})
        super().__init__(**kwargs)

    def add(self, note):
        """Add an event (note) to the part.

        Parameters
        ----------
        note : dict-like or :class:`Note`
            The note event to add. If a dictionary is passed, it must
            contain at least the "time" and "note" keys, and optionally a
            "velocity" key.

        """
        note = _normalize_note(note)

        self.send({"event": "add", "arg": note.to_dict()})
        return self

    def at(self, time, note):
        """Add or set a note at a given time.

        Unlike in Tone.js, it doesn't return any Event.

        """
        note = _normalize_note(note)

        self.send({"event": "at", "time": time, "value": note.to_dict()})

    def remove(self, time=None, note=None):
        """Remove one or more events (notes) from the part.

        Parameters
        ----------
        time : float or str, optional
            If provided, remove all events scheduled at that time.
        note : dict-like or :class:`Note`
            Remove a specific note event.

        """
        if time is None and note is None:
            raise ValueError("Please provide at least one value for either 'time' or 'note'")
        if note is not None:
            note = _normalize_note(note).to_dict()

        self.send({"event": "remove", "time": time, "value": note})
        return self

    def clear(self):
        """Remove all note events from the part."""
        self.send({"event": "clear"})
        return self

    def dispose(self):
        self.clear()
        super().dispose()
        return self


class Sequence(Event):
    """Alternate version of a Part where note events are spaced at a
    given subdivision.

    """

    _model_name = Unicode("SequenceModel").tag(sync=True)

    events = List(Any()).tag(sync=True)
    _subdivision = Union((Float(), Unicode())).tag(sync=True)

    length = Int(0, read_only=True, help="number of scheduled notes in the part").tag(sync=True)

    def __init__(
        self,
        callback=None,
        events=None,
        subdivision="8n",
        loop=True,
        loop_start=0,
        loop_end=0,
        **kwargs,
    ):
        """

        Parameters
        ----------
        callback : callable, optional
             Scheduling callback, which must accept two arguments (time, value).
        events : list, optional
             A list of note events or a list of lists of note events. The notes in a
             sub-list will be spaced by evenly sub-dividing the the step interval.
        subdivision : str or float, optional
            Subdivision of the sequence, i.e., interval between steps (default: eigth-note).

        """
        if events is None:
            events = []

        kw = {
            "callback": callback,
            "events": events,
            "_subdivision": subdivision,
            # sequence is looped by default
            "loop": loop,
            "loop_start": loop_start,
            "loop_end": loop_end,
        }
        kwargs.update(kw)
        super().__init__(**kwargs)

    @property
    def subdivision(self):
        """Subdivision of the sequence."""
        return self._subdivision

    def clear(self):
        """Remove all note events from the part."""
        self.send({"event": "clear"})
        return self

    def dispose(self):
        self.clear()
        super().dispose()
        return self


class Loop(Event):
    """Looped callback at a specified interval."""

    _model_name = Unicode("LoopModel").tag(sync=True)

    interval = Union((Float(), Unicode()), help="loop interval", default_value="8n").tag(sync=True)
    iterations = Int(
        allow_none=True,
        default_value=None,
        help="number of iterations of the loop (default: infinity)",
    ).tag(sync=True)

    loop = Union((Bool(), Int()), default_value=True, read_only=True).tag(sync=True)
    loop_start = Union((Float(), Unicode()), read_only=True).tag(sync=True)
    loop_end = Union((Float(), Unicode()), read_only=True).tag(sync=True)

    def __init__(self, callback=None, interval="8n", **kwargs):
        kwargs.update({"callback": callback, "interval": interval})
        super().__init__(**kwargs)

    def _set_js_callback(self):
        time_arg = TimeCallbackArg(self)
        self._callback(time_arg)

        data = {
            "event": "set_callback",
            "op": "",
            "items": time_arg.items,
        }

        time_arg._disposed = True

        self.send(data)

    def _repr_keys(self):
        for key in super()._repr_keys():
            if key not in ["loop", "loop_start", "loop_end"]:
                yield key
        yield "interval"
        if self.iterations is not None:
            yield "iterations"


PATTERN_TYPES = [
    "up",
    "down",
    "upDown",
    "downUp",
    "alternateUp",
    "alternateDown",
    "random",
    "randomOnce",
    "randomWalk",
]


class Pattern(Loop):
    """A loop that arpeggiates between the given notes in a given
    pattern.

    """

    _model_name = Unicode("PatternModel").tag(sync=True)

    pattern = Enum(PATTERN_TYPES, default_value="up", help="pattern type").tag(sync=True)
    values = List(Any(), allow_none=True, default_value=None, help="pattern notes").tag(sync=True)

    def __init__(self, callback=None, values=None, pattern="up", **kwargs):
        if values is None:
            values = []
        kwargs.update({"callback": callback, "values": values, "pattern": pattern})
        super().__init__(**kwargs)

    def _set_js_callback(self):
        time_arg = TimeCallbackArg(self)
        value_arg = EventValueCallbackArg(self)
        self._callback(time_arg, value_arg)

        items = collect_and_merge_items(time_arg, value_arg)

        time_arg._disposed = True
        value_arg._disposed = True

        data = {
            "event": "set_callback",
            "op": "",
            "items": items,
        }
        self.send(data)

    def _repr_keys(self):
        for key in super()._repr_keys():
            yield key
        yield "pattern"
