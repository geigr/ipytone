import pytest

from ipytone import transport
from ipytone.source import Source


def test_transport():
    assert transport.state == "stopped"

    node = Source()
    interval = "8n"
    start_time = "1m"
    with transport.schedule_repeat(interval, start_time) as event_id:
        assert transport._is_scheduling is True
        assert transport._py_event_id == 0
        assert transport._audio_nodes == []
        assert transport._methods == []
        assert transport._packed_args == []
        assert transport._toggle_schedule is False
        node.start("time").stop("time + 0.1")
        assert transport._audio_nodes == [node, node]
        assert transport._methods == ["start", "stop"]
        assert transport._packed_args == ["time *** ", "time + 0.1 *** "]
    assert transport._schedule_op == "scheduleRepeat"
    assert transport._interval == interval
    assert transport._start_time == start_time
    assert transport._duration is None
    assert transport._toggle_schedule is True
    assert transport._is_scheduling is False
    assert transport._py_event_id == 1

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
