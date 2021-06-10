import re

from traitlets import TraitError

OSC_TYPES = ["sine", "square", "sawtooth", "triangle"]
EXTENDED_OSC_TYPES = OSC_TYPES + ["pwm", "pulse"]


def parse_osc_type(value, types=None):
    if types is None:
        types = OSC_TYPES

    types_str = "|".join(types)
    input_re = f"^(?P<basic_type>{types_str})(?P<partial_count>[0-9]*)$"

    pattern = re.compile(input_re)
    res = pattern.search(value)

    if res is None:
        raise TraitError(f"Invalid oscillator type {value!r}")

    return res.group("basic_type"), res.group("partial_count")
