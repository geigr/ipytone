import ipywidgets
import pytest
from traitlets import Float, Int, Unicode, Union

from ipytone.analysis import FFT, Analyser, DCMeter, Meter, Waveform
from ipytone.core import Param
from ipytone.envelope import Envelope
from ipytone.event import Event
from ipytone.observe import VALID_OBSERVED_TRAITS, ScheduleObserver
from ipytone.signal import Signal
from ipytone.source import Source
from ipytone.transport import Transport

OBSERVABLE_CLASSES = [
    Param,
    Signal,
    Envelope,
    Event,
    Source,
    Transport,
    Analyser,
    Meter,
    DCMeter,
    FFT,
    Waveform,
]


@pytest.fixture(params=OBSERVABLE_CLASSES)
def widget(request):
    widget_cls = request.param
    yield widget_cls()


@pytest.fixture(scope="module", params=VALID_OBSERVED_TRAITS)
def trait_name(request):
    yield request.param


@pytest.fixture(scope="module")
def handler():
    def func(change):
        print(change)

    yield func


@pytest.fixture(scope="module")
def target_widget():
    class Widget(ipywidgets.Widget):
        value = Union((Int(), Float(), Unicode())).tag(sync=True)

    yield Widget()


def test_schedule_observe(widget, trait_name, handler):
    key = hash(handler)

    if trait_name not in widget._observable_traits and trait_name != "time":
        with pytest.raises(ValueError, match="invalid observable trait name"):
            widget.schedule_observe(handler, name=trait_name)
    else:
        # test observe
        widget.schedule_observe(handler, name=trait_name)
        assert key in widget._observers

        observer = widget._observers[key]
        assert observer.observed_widget is widget
        assert observer.observed_trait == trait_name

        # test observe already observed with same handler
        with pytest.raises(ValueError, match="this handler is already used"):
            widget.schedule_observe(handler, name=trait_name)

        # test unobserve
        widget.schedule_unobserve(handler)
        assert key not in widget._observers


def test_schedule_observe_default_trait(widget, handler):
    key = hash(handler)
    widget.schedule_observe(handler)
    assert widget._observers[key].observed_trait == widget._default_observed_trait


def test_schedule_dlink(widget, trait_name, target_widget, mocker):
    if trait_name not in widget._observable_traits and trait_name != "time":
        with pytest.raises(ValueError, match="invalid observable trait name"):
            widget.schedule_dlink((target_widget, "value"), name=trait_name)
    elif trait_name == "array":
        # TODO: not sure it make 100% to link array values
        pass
    else:
        for method in (widget.schedule_dlink, widget.schedule_jsdlink):
            link = method((target_widget, "value"), name=trait_name)

            assert link.observer.observed_widget is widget
            assert link.observer.observed_trait == trait_name

            # test unlink
            mocker.patch.object(link.link, "unlink")
            mocker.patch.object(link.observer, "schedule_cancel")
            link.unlink()
            link.link.unlink.assert_called_once()
            link.observer.schedule_cancel.assert_called_once()


def test_schedule_observer():
    sig = Signal()
    observer = ScheduleObserver(observed_widget=sig)

    assert observer.observed_widget is sig
    assert observer.observe_time is False
    assert observer.time == 0.0
    assert observer.value == 0
    assert observer.state == "stopped"
    assert observer.progress == 0.0
    assert observer.position == "0:0:0"
    assert observer.ticks == 0
    assert observer.seconds == 0.0
    assert observer.time_value is None


def test_schedule_observer_schedule_observe(mocker, handler):
    sig = Signal()
    observer = ScheduleObserver(observed_widget=sig)

    mocker.patch.object(observer, "observe")
    mocker.patch.object(observer, "unobserve")
    mocker.patch.object(observer, "send")

    observer.schedule_observe(handler, 1, True)
    observer.observe.assert_called_with(handler, names="value")
    observer.send.assert_called_with(
        {"event": "scheduleRepeat", "update_interval": 1, "transport": True, "draw": False}
    )

    observer.schedule_unobserve(handler)
    observer.unobserve.assert_called_with(handler, names="value")
    observer.send.assert_called_with({"event": "scheduleCancel"})

    # test observe time
    observer.observe_time = True
    observer.schedule_observe(handler, 1, True)
    observer.observe.assert_called_with(handler, names="time_value")
    observer.schedule_unobserve(handler)
    observer.unobserve.assert_called_with(handler, names="time_value")


def test_schedule_observer_schedule_link(mocker, target_widget):
    dlink_patch = mocker.patch("ipywidgets.dlink")
    jsdlink_patch = mocker.patch("ipywidgets.jsdlink")

    sig = Signal()
    observer = ScheduleObserver(observed_widget=sig)

    mocker.patch.object(observer, "send")

    # dlink
    observer.schedule_dlink((target_widget, "value"), 1, True)
    observer.send.assert_called_with(
        {"event": "scheduleRepeat", "update_interval": 1, "transport": True, "draw": False}
    )
    dlink_patch.assert_called_with((observer, "value"), (target_widget, "value"))

    # jsdlink
    observer.schedule_dlink((target_widget, "value"), 1, True, js=True)
    observer.send.assert_called_with(
        {"event": "scheduleRepeat", "update_interval": 1, "transport": True, "draw": True}
    )
    jsdlink_patch.assert_called_with((observer, "value"), (target_widget, "value"))
