from ipytone import get_destination
from ipytone.core import Destination


def test_destination():
    dest = get_destination()

    assert dest.mute is False
    assert dest.volume == -16

    # test singleton
    dest1 = Destination()
    dest2 = Destination()

    assert dest1 == dest2 == get_destination()
