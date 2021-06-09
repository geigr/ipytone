import pytest
from traitlets import TraitError

from ipytone.utils import parse_osc_type


def test_parse_osc_type():

    # just test that the following types are valid
    for wave in ["sine", "square", "sawtooth", "triangle"]:
        for pcount in ["", "2", "22"]:
            basic_type, partial_count = parse_osc_type(wave + pcount)
            assert basic_type == wave
            assert partial_count == pcount

    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        parse_osc_type("sines2")

    with pytest.raises(TraitError, match="Invalid oscillator type.*"):
        parse_osc_type("sine", types="pulse")
