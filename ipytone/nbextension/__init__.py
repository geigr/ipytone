#!/usr/bin/env python

# Copyright (c) Benoit Bovy
# Distributed under the terms of the Modified BSD License.


def _jupyter_nbextension_paths():
    return [
        {
            "section": "notebook",
            "src": "nbextension",
            "dest": "ipytone",
            "require": "ipytone/extension",
        }
    ]
