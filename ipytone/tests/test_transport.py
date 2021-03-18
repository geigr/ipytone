import pytest

from ipytone import transport
from ipytone.source import Source


def test_transport():
    assert transport.state == "stopped"

    toggle_schedule = False
    py_event_id = 0
    node = Source()

    # schedule_repeat
    interval = "8n"
    start_time = "1m"
    start = "time"
    stop = "time + 0.1"
    with transport.schedule_repeat(interval, start_time) as event_id:
        assert transport._is_scheduling is True
        assert transport._py_event_id == py_event_id
        assert transport._audio_nodes == []
        assert transport._methods == []
        assert transport._packed_args == []
        assert transport._toggle_schedule == toggle_schedule
        node.start(start).stop(stop)
        assert transport._audio_nodes == [node, node]
        assert transport._methods == ["start", "stop"]
        assert transport._packed_args == [f"{start} *** ", f"{stop} *** "]
    toggle_schedule = not toggle_schedule
    py_event_id += 1
    assert transport._schedule_op == "scheduleRepeat"
    assert transport._interval == interval
    assert transport._start_time == start_time
    assert transport._duration is None
    assert transport._toggle_schedule == toggle_schedule
    assert transport._is_scheduling is False
    assert transport._py_event_id == py_event_id

    transport.start()
    assert transport.state == "started"

    assert transport._toggle_clear is False
    transport.clear(event_id)
    assert transport._toggle_clear is True
    assert transport._clear_event_id == event_id
    with pytest.raises(RuntimeError):
        transport.clear(event_id)

    transport.stop()
    assert transport.state == "stopped"

    # schedule
    time = "2m"
    start = "time + 0.2"
    stop = "time + 0.3"
    with transport.schedule(time) as event_id:
        assert transport._is_scheduling is True
        assert transport._py_event_id == py_event_id
        assert transport._audio_nodes == []
        assert transport._methods == []
        assert transport._packed_args == []
        assert transport._toggle_schedule == toggle_schedule
        node.start(start).stop(stop)
        assert transport._audio_nodes == [node, node]
        assert transport._methods == ["start", "stop"]
        assert transport._packed_args == [f"{start} *** ", f"{stop} *** "]
    toggle_schedule = not toggle_schedule
    py_event_id += 1
    assert transport._schedule_op == "schedule"
    assert transport._start_time == time
    assert transport._toggle_schedule == toggle_schedule
    assert transport._is_scheduling is False
    assert transport._py_event_id == py_event_id

    # schedule_once
    time = "3m"
    start = "time + 0.4"
    stop = "time + 0.5"
    with transport.schedule_once(time) as event_id:
        assert transport._is_scheduling is True
        assert transport._audio_nodes == []
        assert transport._methods == []
        assert transport._packed_args == []
        assert transport._toggle_schedule == toggle_schedule
        node.start(start).stop(stop)
        assert transport._audio_nodes == [node, node]
        assert transport._methods == ["start", "stop"]
        assert transport._packed_args == [f"{start} *** ", f"{stop} *** "]
    toggle_schedule = not toggle_schedule
    assert transport._schedule_op == "scheduleOnce"
    assert transport._start_time == time
    assert transport._toggle_schedule == toggle_schedule
    assert transport._is_scheduling is False
