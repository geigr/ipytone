# code modified from ipygany (https://github.com/QuantStack/ipygany)
# Copyright (c) 2019-2021 Martin Renou
# BSD 3-Clause "New" or "Revised" License
import numpy as np
from ipywidgets import Widget, widget_serialization


def array_to_binary(value, widget, force_contiguous=True):
    if value is None:
        return None
    # TODO: move checks to trait value validate
    if value.ndim not in [1, 2]:
        raise ValueError(f"Only 1-d or 2-d array is supported, got {value.ndim}")
    if value.dtype.kind not in ["f"]:
        raise ValueError(f"Only float dtype is supported, got {value.dtype}")
    if value.dtype == np.float64:  # ToneAudioBuffer does not support float64
        value = value.astype(np.float32)
    if force_contiguous and not value.flags["C_CONTIGUOUS"]:  # make sure it's contiguous
        value = np.ascontiguousarray(value)
    return {"shape": value.shape, "dtype": str(value.dtype), "buffer": memoryview(value)}


def json_to_array(value, widget):
    if value is None:
        return None
    arr = np.frombuffer(value["buffer"], dtype=value["dtype"])
    arr.shape = value["shape"]
    return arr


def data_array_to_json(value, widget, force_contiguous=True):
    if isinstance(value, Widget):
        return widget_serialization["to_json"](value, widget)
    elif isinstance(value, list):
        return [array_to_binary(element, widget, force_contiguous) for element in value]
    else:
        return array_to_binary(value, widget, force_contiguous)


def json_to_data_array(value, widget):
    if isinstance(value, str) and value.startswith("IPY_MODEL_"):
        # Array widget
        return widget_serialization["from_json"](value, widget)
    elif isinstance(value, list):
        # list of arrays
        return [json_to_array(element, widget) for element in value]
    else:
        return json_to_array(value, widget)


array_serialization = dict(to_json=array_to_binary, from_json=json_to_array)

data_array_serialization = dict(to_json=data_array_to_json, from_json=json_to_data_array)
