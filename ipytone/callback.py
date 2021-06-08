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


def add_or_send_event(method, callee, args, event="trigger"):
    """Add a specific event (i.e., Tone object method call + args) for scheduling or
    send it directly to the front-end.

    """
    arg_values = {}
    callback_args = []
    for name, value in args.items():
        if isinstance(value, BaseCallbackArg):
            callback_args.append(value)
            arg_values[name] = {"value": value.value, "eval": True}
        else:
            arg_values[name] = {"value": value, "eval": False}

    data = {"method": method, "args": arg_values, "arg_keys": list(args.keys())}

    if len(callback_args):
        data["callee"] = callee.model_id
        for ca in callback_args:
            ca.items.append(data)
    else:
        data["event"] = event
        callee.send(data)
