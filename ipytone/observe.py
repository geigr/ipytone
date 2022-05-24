from ipywidgets import widget_serialization
from traitlets import Dict, Enum, Float, HasTraits, Instance, Int, Tuple, Unicode, Union

from .base import NodeWithContext, ToneWidgetBase


class ScheduleObserver(ToneWidgetBase):
    """Used internally to observe the current time and/or value of a Tone.js
    Param / Signal / Meter instance at a given, regular interval.

    Implementing this in a separate widget is more composable. It allows setting
    multiple handlers on the same observed instance, possibly with different
    update intervals. It also prevents any interference with the observed
    Param / Signal ``value`` trait, which can be set from within Python.

    """

    _model_name = Unicode("ScheduleObserverModel").tag(sync=True)

    observed_widget = Instance(
        NodeWithContext,
        help="observed Param / Signal / Meter widget",
    ).tag(sync=True, **widget_serialization)

    observed_trait = Enum(["time", "value", "time_value"], default_value="value").tag(sync=True)

    time = Float(help="current observed time", read_only=True).tag(sync=True)

    value = Union(
        (Float(), Int(), Unicode()),
        help="Param / Signal / Meter current observed value",
        read_only=True,
    ).tag(sync=True)

    time_value = Tuple(
        Float(),
        Union((Float(), Int(), Unicode())),
        help="Both current observed time and value",
        allow_none=True,
        read_only=True,
    ).tag(sync=True)

    def schedule_observe(self, handler, repeat_interval, transport):
        data = {
            "event": "scheduleObserve",
            "repeat_interval": repeat_interval,
            "transport": transport,
        }
        self.send(data)

        self.observe(handler, names=self.observed_trait)

    def schedule_unobserve(self, handler):
        self.send({"event": "scheduleUnobserve"})
        self.unobserve(handler, names=self.observed_trait)


class ScheduleObserveMixin(HasTraits):
    """Adds the ability to observe from within Python the current value
    (and/or current time) of a Parameter / Signal or Meter node.

    """

    _observers = Dict(key_trait=Int(), value_trait=Instance(ScheduleObserver))

    def schedule_observe(self, handler, repeat_interval=1, transport=False, name="value"):
        """Setup a handler to be called at regular intervals with the updated
        time / value of this param / signal / meter node.

        Parameters
        ----------
        handler : callable
            A callable that is called when the time and/or value is updated at
            regular intervals. The signature of the callable is similar
            to the signature expected by :func:`ipywidgets.Widget.observe`.
            Note that the handler will only apply to the trait given by the
            ``name`` argument.
        repeat_interval : float or string, optional
            The interval at which the trait is updated in the front-end,
            in seconds (default: 1). If ``transport=True``, any interval accepted by
            :func:`~ipytone.transport.schedule_repeat` is also valid here.
        transport : bool, optional
            if True, the trait update is scheduled along the :class:`ipytone.Transport`
            timeline, i.e., the handler is not called until the transport starts and
            will stop being called when the transport stops. If False (default),
            the trait update is done in the active context.
        name : { "time", "value", "time_value" }
            The name of the trait to observe.

            - "value" (default): the current value of the param / signal / meter node.
            - "time": the current time (either transport time or context time).
            - "time_value": both time and value returned as a tuple.

        """
        key = hash(handler)

        if key in self._observers:
            raise ValueError(
                "this handler is already used. Call 'schedule_unobserve' first if you "
                "want to apply this handler on another interval."
            )

        observer = ScheduleObserver(observed_widget=self, observed_trait=name)
        observer.schedule_observe(handler, repeat_interval, transport)

        observers = self._observers.copy()
        observers[key] = observer
        self._observers = observers

    def schedule_unobserve(self, handler):
        """Cancel the scheduled updates of the time / value trait associated
        with the given handler.

        """
        key = hash(handler)

        observers = self._observers.copy()
        observer = observers.pop(key)
        observer.schedule_unobserve(handler)
        observer.close()
        self._observers = observers
