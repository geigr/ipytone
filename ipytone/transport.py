import contextlib

from ipywidgets import Widget, widget_serialization
from traitlets import Bool, Enum, Instance, Int, List, Unicode

from .base import ToneWidgetBase


class Transport(ToneWidgetBase):
    """Transport for timing musical events."""

    _singleton = None

    _model_name = Unicode("TransportModel").tag(sync=True)

    _schedule_op = Unicode().tag(sync=True)
    _audio_nodes = List(Instance(Widget)).tag(sync=True, **widget_serialization)
    _methods = List(Unicode()).tag(sync=True)
    _packed_args = List(Unicode()).tag(sync=True)
    _toggle_schedule = Bool().tag(sync=True)
    _toggle_clear = Bool().tag(sync=True)

    _interval = Unicode().tag(sync=True)
    _start_time = Unicode().tag(sync=True)
    _duration = Unicode(allow_none=True).tag(sync=True)
    _py_event_id = Int().tag(sync=True).tag(sync=True)
    _clear_event_id = Int().tag(sync=True)

    state = Enum(["started", "stopped"], allow_none=False, default_value="stopped").tag(sync=True)

    def __new__(cls):
        if Transport._singleton is None:
            Transport._singleton = super(Transport, cls).__new__(cls)
        return Transport._singleton

    def __init__(self, **kwargs):
        self._is_scheduling = False
        self._all_event_id = []
        super(Transport, self).__init__(**kwargs)

    @contextlib.contextmanager
    def schedule_repeat(self, interval, start_time, duration=None):
        self._is_scheduling = True
        self._audio_nodes = []
        self._methods = []
        self._packed_args = []
        yield self._py_event_id
        self._schedule_op = "scheduleRepeat"
        self._interval = interval
        self._start_time = start_time
        self._duration = duration
        self._toggle_schedule = not self._toggle_schedule
        self._is_scheduling = False
        self._all_event_id.append(self._py_event_id)
        self._py_event_id = self._py_event_id + 1

    def clear(self, event_id):
        if event_id not in self._all_event_id:
            raise RuntimeError(f"Scheduled event ID not found: {event_id}")
        self._clear_event_id = event_id
        self._toggle_clear = not self._toggle_clear
        id_idx = self._all_event_id.index(event_id)
        del self._all_event_id[id_idx]

    def start(self):
        self.state = "started"

    def stop(self):
        if self.state == "started":
            self.state = "stopped"


transport = Transport()
