from typing import Callable

from traitlets import Any, Bool, Float, Int, Unicode, Union

from .base import NodeWithContext
from .callback import (
    EventValueCallbackArg,
    TimeCallbackArg,
    add_or_send_event,
    collect_and_merge_items,
)


def _no_callback(time, value):
    pass


class Event(NodeWithContext):

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
