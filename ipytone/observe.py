from ipywidgets import Widget, dlink, jsdlink, widget_serialization
from traitlets import Bool, Dict, Enum, Float, HasTraits, Instance, Int, List, Tuple, Unicode, Union

from .base import NodeWithContext, ToneWidgetBase


class ToneDirectionalLink:
    def __init__(self, observer, link):
        self.observer = observer
        self.link = link

    def unlink(self):
        self.link.unlink()
        self.observer.schedule_cancel()


VALID_OBSERVED_TRAITS = ["time", "value", "state"]


class ScheduleObserver(ToneWidgetBase):
    """Used internally to observe from Python the curent value of an
    attribute of a Tone.js instance at a given, regular interval.

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

    observed_trait = Enum(VALID_OBSERVED_TRAITS, default_value="value").tag(sync=True)
    observe_time = Bool(False, help="if True, observe time along with the observed trait").tag(
        sync=True
    )

    time = Float(help="current observed time", read_only=True).tag(sync=True)

    value = Union(
        (Float(), Int(), Unicode()),
        help="Param / Signal / Meter current observed value",
        read_only=True,
    ).tag(sync=True)

    state = Enum(
        ["started", "stopped", "paused"],
        default_value="stopped",
        help="current playback state",
        read_only=True,
    ).tag(sync=True)

    time_value = Tuple(
        Float(),
        Union((Float(), Int(), Unicode())),
        help="Both current observed time and trait value",
        allow_none=True,
        read_only=True,
    ).tag(sync=True)

    def schedule_repeat(self, update_interval, transport, draw=False):
        data = {
            "event": "scheduleRepeat",
            "update_interval": update_interval,
            "transport": transport,
            "draw": draw,
        }
        self.send(data)

    def schedule_cancel(self):
        self.send({"event": "scheduleCancel"})

    def _get_trait_name(self):
        if self.observe_time:
            return "time_value"
        else:
            return self.observed_trait

    def schedule_observe(self, handler, update_interval, transport):
        self.schedule_repeat(update_interval, transport)
        self.observe(handler, names=self._get_trait_name())

    def schedule_unobserve(self, handler):
        self.schedule_cancel()
        self.unobserve(handler, names=self._get_trait_name())

    def schedule_dlink(self, target, update_interval, transport, js=False):
        if js and transport:
            # use Tone.js Draw for better synchronization
            # of sound and visuals
            draw = True
        else:
            draw = False

        self.schedule_repeat(update_interval, transport, draw=draw)

        if js:
            link = jsdlink((self, "value"), target)
        else:
            link = dlink((self, "value"), target)

        return ToneDirectionalLink(self, link)


class ScheduleObserveMixin(HasTraits):
    """Adds the ability to observe from within Python the current value
    of an ipytone widget (e.g., Param, Signal, Envelope, Meter, etc.).

    """

    _observers = Dict(key_trait=Int(), value_trait=Instance(ScheduleObserver))

    # redefine those properties in subclass to restrict the list of valid observable traits.
    _observable_traits = List(VALID_OBSERVED_TRAITS)
    _default_observed_trait = "value"

    def _validate_trait_name(self, proposal):
        if proposal is None:
            proposal = self._default_observed_trait

        if proposal not in self._observable_traits + ["time"]:
            raise ValueError(
                f"invalid observable trait name, should be one of {self._observable_traits}, "
                f"found {proposal}"
            )

        return proposal

    def _add_observer(self, key, observer):
        observers = self._observers.copy()
        observers[key] = observer
        self._observers = observers

    def _remove_observer(self, key):
        observers = self._observers.copy()
        observers.pop(key)
        # TODO: it this the cause of "no comm in channel included" error?
        # observer.close()
        self._observers = observers

    def schedule_observe(
        self, handler, update_interval=1, transport=False, name=None, observe_time=False
    ):
        """Setup a handler to be called at regular intervals with the updated
        time / value of this ipytone widget.

        Parameters
        ----------
        handler : callable
            A callable that is called when the time and/or value is updated at
            regular intervals. The signature of the callable is similar
            to the signature expected by :func:`ipywidgets.Widget.observe`.
            Note that the handler will only apply to the trait given by the
            ``name`` argument here.
        update_interval : float or string, optional
            The interval at which the trait is updated in the front-end,
            in seconds (default: 1). If ``transport=True``, any interval accepted by
            :func:`~ipytone.transport.schedule_repeat` is also valid here.
        transport : bool, optional
            if True, the trait update is scheduled along the :class:`ipytone.Transport`
            timeline, i.e., the handler is not called until the transport starts and
            will stop being called when the transport stops. If False (default),
            the trait update is done with respect to the active audio context.
        name : { "time", "value" }, optional
            The name of the trait to observe. It accepts one of the following:

            - "value" (default): the current value of the Tone.js corresponding instance.
            - "time": the current time (either transport time or audio context time).

        """
        key = hash(handler)

        name = self._validate_trait_name(name)

        if key in self._observers:
            raise ValueError(
                "this handler is already used. Call 'schedule_unobserve' first if you "
                "want to apply this handler on another interval."
            )

        observer = ScheduleObserver(
            observed_widget=self, observed_trait=name, observe_time=observe_time
        )
        observer.schedule_observe(handler, update_interval, transport)

        self._add_observer(key, observer)

    def schedule_unobserve(self, handler):
        """Cancel the scheduled updates of the time / value trait associated
        with the given handler.

        """
        key = hash(handler)

        observer = self._observers[key]
        observer.schedule_unobserve(handler)

        self._remove_observer(key)

    def _schedule_dlink(self, target, update_interval, transport, name, js=False):
        widget, trait = target

        if not isinstance(widget, Widget):
            raise ValueError("the first item of target must be a Widget instance")
        if not hasattr(widget, trait):
            raise ValueError(f"{trait!r} is not a trait of widget {widget!r}")

        name = self._validate_trait_name(name)

        observer = ScheduleObserver(observed_widget=self, observed_trait=name)
        return observer.schedule_dlink(target, update_interval, transport, js=js)

    def schedule_dlink(self, target, update_interval=1, transport=False, name=None):
        """Link this ipytone widget value with a target widget attribute.

        As the value of this widget may refer to a continuously updated value
        (e.g., the gain of an audio signal, the current value of a parameter, etc.),
        The target widget attribute is synchronized on a given, finite resolution.

        Parameters
        ----------
        target : (object, str) tuple
            The target widget attribute to link, given as a
            ``(widget, attr_name)`` tuple.
        update_interval : float or string, optional
            The interval at which the target attribute is updated in the front-end,
            in seconds (default: 0.04). If ``transport=True``, any interval accepted by
            :func:`~ipytone.transport.schedule_repeat` is also valid here.
        transport : bool, optional
            if True, the target attribute is synced along the :class:`ipytone.Transport`
            timeline, i.e., no update happens until the transport starts and
            updates stop when the transport stops. If False (default),
            the target attribute update is done with respect to the active audio context.

        """
        return self._schedule_dlink(target, update_interval, transport, name, js=False)

    def schedule_jsdlink(self, target, update_interval=0.08, transport=False, name=None):
        """Link this ipytone widget value with a target widget attribute.

        The link is created in the front-end and does not rely on a roundtrip
        to the backend.

        As the value of this widget may refer to a continuously updated value
        (e.g., the gain of an audio signal, the current value of a parameter, etc.),
        The target widget attribute is synchronized on a given, finite resolution.

        Parameters
        ----------
        target : (object, str) tuple
            The target widget attribute to link, given as a
            ``(widget, attr_name)`` tuple.
        update_interval : float or string, optional
            The interval at which the target attribute is updated in the front-end,
            in seconds (default: 0.04). If ``transport=True``, any interval accepted by
            :func:`~ipytone.transport.schedule_repeat` is also valid here.
        transport : bool, optional
            if True, the target attribute is synced along the :class:`ipytone.Transport`
            timeline, i.e., no update happens until the transport starts and
            updates stop when the transport stops. If False (default),
            the target attribute update is done with respect to the active audio context.

        """
        return self._schedule_dlink(target, update_interval, transport, name, js=True)
