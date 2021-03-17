import pytest
from traitlets import TraitError

from ipytone.utils import validate_osc_type


def test_validate_osc_type():

    # just test that the following types are valid
    for wave in ["sine", "square", "sawtooth", "triangle"]:
        for pcount in range(2):
            validate_osc_type(wave + str(pcount))

    with pytest.raises(TraitError, match="Invalid oscillator type"):
        validate_osc_type("not a good oscillator wave")
