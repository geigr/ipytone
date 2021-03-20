# code taken from ipygany (https://github.com/QuantStack/ipygany)
# Copyright (c) 2019-2021 Martin Renou
# BSD 3-Clause "New" or "Revised" License
import numpy as np

from ipywidgets import Widget, widget_serialization


def array_to_binary(ar, obj=None, force_contiguous=True):
    if ar is None:
        return None
    if ar.dtype.kind not in ['f']:
        raise ValueError(f"Only float dtype is supported, got {ar.dtype}")
    if ar.dtype == np.float64:  # ToneAudioBuffer does not support float64
        ar = ar.astype(np.float32)
    if force_contiguous and not ar.flags["C_CONTIGUOUS"]:  # make sure it's contiguous
        ar = np.ascontiguousarray(ar)
    return {'data': memoryview(ar), 'dtype': str(ar.dtype), 'shape': ar.shape}


def json_to_array(json, obj=None):
    return np.array(json)


def data_array_to_json(value, obj=None, force_contiguous=True):
    if isinstance(value, Widget):
        return widget_serialization['to_json'](value, obj)
    else:
        return array_to_binary(value, obj, force_contiguous)


def json_to_data_array(json, obj=None):
    if isinstance(json, str) and json.startswith('IPY_MODEL_'):
        # Array widget
        return widget_serialization['from_json'](json, obj)
    else:
        return json_to_array(json, obj)


array_serialization = dict(
    to_json=array_to_binary,
    from_json=json_to_array
)

data_array_serialization = dict(
    to_json=data_array_to_json,
    from_json=json_to_data_array
)
