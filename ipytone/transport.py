from traitlets import Enum, Unicode

from .base import ToneObject


class BaseCallbackArg:
    """Base class internally used as a placeholder for any tone event or
    scheduling callback argument.

    """

    def __init__(self, caller, value=None, parent=None):
        self.caller = caller
        self.value = value
        self.parent = parent
        self._items = []

    @property
    def items(self):
        items = self._items

        parent = self.parent
        while parent is not None:
            items = parent._items
            parent = parent.parent

        return items


class ScheduleCallbackArg(BaseCallbackArg):
    def __init__(self, *args, value="time", **kwargs):
        super().__init__(*args, value=value, **kwargs)

    def __add__(self, other):
        return ScheduleCallbackArg(self.caller, value=f"{self.value} + {other}", parent=self)


def add_or_send_event(name, callee, args):
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
        data["event"] = "trigger"
        data.update(args)
        callee.send(data)


class Transport(ToneObject):
    """Transport for timing musical events."""

    _singleton = None

    _model_name = Unicode("TransportModel").tag(sync=True)

    state = Enum(["started", "stopped"], allow_none=False, default_value="stopped").tag(sync=True)

    def __new__(cls):
        if Transport._singleton is None:
            Transport._singleton = super(Transport, cls).__new__(cls)
        return Transport._singleton

    def __init__(self, **kwargs):
        self._py_event_id = 0
        self._all_event_id = []
        super(Transport, self).__init__(**kwargs)

    def _get_callback_items(self, callback):
        callback_arg = ScheduleCallbackArg(self)
        callback(callback_arg)
        return callback_arg.items

    def _get_event_id_and_inc(self, append=True):
        event_id = self._py_event_id
        if append:
            self._all_event_id.append(event_id)
        self._py_event_id += 1
        return event_id

    def schedule(self, callback, time):
        items = self._get_callback_items(callback)
        event_id = self._get_event_id_and_inc()
        self.send({"event": "schedule", "op": "", "id": event_id, "items": items, "time": time})
        return event_id

    def schedule_repeat(self, callback, interval, start_time=0, duration=None):
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
        items = self._get_callback_items(callback)
        event_id = self._get_event_id_and_inc(append=False)
        self.send({"event": "schedule", "op": "once", "id": event_id, "items": items, "time": time})
        return event_id

    def clear(self, event_id):
        if event_id not in self._all_event_id:
            raise ValueError(f"Scheduled event ID not found: {event_id}")
        self.send({"event": "clear", "id": event_id})
        id_idx = self._all_event_id.index(event_id)
        del self._all_event_id[id_idx]
        return self

    def start(self):
        self.state = "started"

    def stop(self):
        if self.state == "started":
            self.state = "stopped"


transport = Transport()


def start_node(node, time=""):
    """Start an audio node.

    The node will either start immediately or as specified by ``time`` if this
    function is called within a transport scheduling context.

    """
    # if transport._is_scheduling:
    #    transport._audio_nodes = transport._audio_nodes + [node]
    #    transport._methods = transport._methods + ["start"]
    #    transport._packed_args = transport._packed_args + [time + " *** "]
    # else:
    node.state = "started"

    return node


def stop_node(node, time=""):
    """Stop an audio node.

    The node will either stop immediately or as specified by ``time`` if this
    function is called within a transport scheduling context.

    """
    # if transport._is_scheduling:
    #    transport._audio_nodes = transport._audio_nodes + [node]
    #    transport._methods = transport._methods + ["stop"]
    #    transport._packed_args = transport._packed_args + [time + " *** "]
    # else:
    if node.state == "started":
        node.state = "stopped"

    return node
