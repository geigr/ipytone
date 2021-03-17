import re

from traitlets import TraitError


def validate_osc_type(value):
    value_re = r"(sine|square|sawtooth|triangle)[\d]*"

    if re.fullmatch(value_re, value) is None:
        raise TraitError(f"Invalid oscillator type: {value}")

    return value
