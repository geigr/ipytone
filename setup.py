#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
from setuptools import setup, find_packages
import os
from os.path import join as pjoin

from jupyter_packaging import (
    create_cmdclass,
    install_npm,
    ensure_targets,
    combine_commands,
    get_version,
    skip_if_exists,
)


HERE = os.path.dirname(os.path.abspath(__file__))

# The name of the project
name = "ipytone"

# Get our version
version = get_version(pjoin(name, "_version.py"))

nb_path = pjoin(HERE, name, "nbextension", "static")
lab_path = pjoin(HERE, name, "labextension")

# Representative files that should exist after a successful build
jstargets = [
    pjoin(nb_path, "index.js"),
    pjoin(lab_path, "package.json"),
]

package_data_spec = {name: ["nbextension/static/*.*js*", "labextension/**"]}

data_files_spec = [
    ("share/jupyter/nbextensions/ipytone", nb_path, "*.js*"),
    ("share/jupyter/labextensions/ipytone", lab_path, "**"),
    ("etc/jupyter/nbconfig/notebook.d", HERE, "ipytone.json"),
]


cmdclass = create_cmdclass(
    "jsdeps", package_data_spec=package_data_spec, data_files_spec=data_files_spec
)

js_command = combine_commands(
    install_npm(HERE, npm=["yarn"], build_cmd="build:extensions"),
    ensure_targets(jstargets),
)

is_repo = os.path.exists(os.path.join(HERE, ".git"))
if is_repo:
    cmdclass["jsdeps"] = js_command
else:
    cmdclass["jsdeps"] = skip_if_exists(jstargets, js_command)


setup_args = dict(
    name=name,
    description="Interactive audio in Jupyter",
    version=version,
    cmdclass=cmdclass,
    packages=find_packages(),
    zip_safe=False,
    author="Benoit Bovy",
    author_email="benbovy@gmail.com",
    url="https://github.com/benbovy/ipytone",
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "Widgets", "IPython"],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Framework :: Jupyter",
    ],
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "ipywidgets>=7.6.0",
        "numpy",
        "traittypes",
    ],
    extras_require={
        "test": [
            "pytest>=4.6",
            "pytest-cov",
            "pytest-mock",
        ],
    },
    entry_points={},
)

setup(**setup_args)
