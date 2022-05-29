import ipywidgets
from ipywidgets import widget_serialization
from traitlets import Bool, Dict, Enum, Float, HasTraits, Instance, Int, List, Tuple, Unicode, Union
from traittypes import Array

from .base import ToneObject, ToneWidgetBase
from .serialization import data_array_serialization


class ToneDirectionalLink:
    def __init__(self, observer, link):
        self.observer = observer
        self.link = link

    def unlink(self):
        self.link.unlink()
        self.observer.schedule_cancel()


VALID_OBSERVED_TRAITS = [
    "time",
    "value",
    "state",
    "progress",
    "position",
    "ticks",
    "seconds",
    "array",
]


class ScheduleObserver(ToneWidgetBase):
    """Used internally to observe or link the curent value of an
    attribute of a Tone.js instance at a given, regular interval.

    Implementing this in a separate widget is more composable. It allows setting
    multiple handlers on the same observed instance, possibly with different
    update intervals. It also prevents any interference with the observed
    Param / Signal ``value`` trait, which can be set from within Python.

    """

    _model_name = Unicode("ScheduleObserverModel").tag(sync=True)

    observed_widget = Instance(
        ToneObject,
        help="observed ipytone widget instance",
    ).tag(sync=True, **widget_serialization)

    observed_trait = Enum(VALID_OBSERVED_TRAITS, default_value="value").tag(sync=True)
    observe_time = Bool(False, help="if True, observe time along with the observed trait").tag(
        sync=True
    )

    time = Float(0.0, help="current observed time", read_only=True).tag(sync=True)

    value = Union(
        (Float(), Int(), Unicode(), List(Float())),
        help="Param / Signal / Meter current observed value",
        default_value=0,
        read_only=True,
    ).tag(sync=True)

    state = Enum(
        ["started", "stopped", "paused"],
        default_value="stopped",
        help="current playback state",
        read_only=True,
    ).tag(sync=True)

    progress = Float(0.0, help="current progress (loop intervals)", read_only=True).tag(sync=True)

    position = Unicode(
        "0:0:0", help="current transport position in Bars:Beats:Sixteenths", read_only=True
    ).tag(sync=True)

    ticks = Int(0, help="current transport tick position", read_only=True).tag(sync=True)

    seconds = Float(0.0, help="current transport position in seconds", read_only=True).tag(
        sync=True
    )

    array = Union(
        (Array(), List(Array())),
        allow_none=True,
        default_value=None,
        help="current value as array or list of arrays",
        read_only=True,
    ).tag(sync=True, **data_array_serialization)

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
            link = ipywidgets.jsdlink((self, self.observed_trait), target)
        else:
            link = ipywidgets.dlink((self, self.observed_trait), target)

        return ToneDirectionalLink(self, link)


class ScheduleObserveMixin(HasTraits):
    """Adds the ability to observe from within Python the current value of an
    attribute of an ipytone widget (e.g., Param, Signal, Envelope, Meter, etc.)
    or link it with another widget attribute.

    It is similar to ipywidgets's ``observe``, ``dlink`` and ``jsdlink``, with
    the extra ability here to observe or link ipytone widget attributes that may
    be updated continuously in the front-end (e.g., value of an audio signal or
    an envelope, position of the transport timeline, etc.).

    The values of those ipytone widget attributes are sampled at given, regular
    intervals, either along Tone.js' main transport timeline or with respect to
    the active audio context.

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
            A callable that is called when the trait value is updated at
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
        name : str, optional
            The name of the Tone.js attribute to observe. Note that it doesn't
            necessarily correspond to a trait of this ipytone widget. Instead, it
            may accept one of the following names (depending the observed ipytone
            widget, only a few may be supported):

            - "time": the current time (either transport time or audio context time).
            - "value": the current value of the Tone.js corresponding instance.
            - "state": current playback state
            - "progress": current progress (of an event or transport loop)
            - "position": current transport position in Bars:Beats:Sixteenths
            - "ticks": current transport tick position
            - "seconds": current transport time in seconds

            The default name also depends on the observed ipytone widget.
        observe_time : bool, optional
            If True, both the (current audio context or transport) time and trait value
            are passed to the handler as a ``(time, trait_value)`` tuple when the trait
            value is updated (default: False).

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
        name = self._validate_trait_name(name)

        observer = ScheduleObserver(observed_widget=self, observed_trait=name)
        return observer.schedule_dlink(target, update_interval, transport, js=js)

    def schedule_dlink(self, target, update_interval=1, transport=False, name=None):
        """Link a source attribute of this ipytone widget with a target widget
        attribute.

        As the source attribute may have a continuously updated value
        (e.g., the gain of an audio signal, the current value of a parameter, etc.),
        The target widget attribute is synchronized at a given, finite resolution.

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
        name : str, optional
            The name of the (source) Tone.js attribute to link. See ``schedule_observe``
            for more details and for a list of available names.

        Returns
        -------
        link : ToneDirectionalLink
            A link object that can be used to unlink the widget attributes (using the
            ``.unlink()`` method).

        """
        return self._schedule_dlink(target, update_interval, transport, name, js=False)

    def schedule_jsdlink(self, target, update_interval=0.08, transport=False, name=None):
        """Link a source attribute of this ipytone widget with a target widget
        attribute.

        The link is created in the front-end and does not rely on a roundtrip
        to the backend.

        As the source attribute may have a continuously updated value
        (e.g., the gain of an audio signal, the current value of a parameter, etc.),
        The target widget attribute is synchronized at a given, finite resolution.

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
        name : str, optional
            The name of the (source) Tone.js attribute to link. See ``schedule_observe``
            for more details and for a list of available names.

        Returns
        -------
        link : ToneDirectionalLink
            A link object that can be used to unlink the widget attributes (using the
            ``.unlink()`` method).

        """
        return self._schedule_dlink(target, update_interval, transport, name, js=True)
