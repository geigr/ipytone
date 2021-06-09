import re

from traitlets import TraitError


def validate_osc_type(value):
    value_re = r"(sine|square|sawtooth|triangle)[\d]*"

    if re.fullmatch(value_re, value) is None:
        raise TraitError(f"Invalid oscillator type: {value}")

    return value


def parse_osc_type(value, types=("sine", "square", "sawtooth", "triangle")):
    types_str = "|".join(types)
    input_re = f"^(?P<basic_type>{types_str})(?P<partial_count>[0-9]*)$"

    pattern = re.compile(input_re)
    res = pattern.search(value)

    if res is None:
        raise ValueError(f"Invalid oscillator type {value!r}")

    return res.group("basic_type"), res.group("partial_count")
