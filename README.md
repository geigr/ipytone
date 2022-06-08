[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/benbovy/ipytone/master?urlpath=lab%2Ftree%2Fexamples)
[![Tests](https://github.com/benbovy/ipytone/workflows/Test/badge.svg)](https://github.com/benbovy/ipytone/actions)

# Ipytone: Interactive Audio in Jupyter

Ipytone exposes many features of the [Tone.js](https://tonejs.github.io) library
to Python as [Jupyter widgets](https://ipywidgets.readthedocs.io). It allows
turning Jupyter into a versatile DAW (Digital Audio Workstation) for music
creation, sound design, data sonification, and more...

...like this little piece of music entirely composed and played in a Jupyter notebook,
with a custom Earth Globe VU-meter!

https://user-images.githubusercontent.com/4160723/172623510-3423505f-cd27-4770-8553-b2f0dc75384f.mov

## Documentation + Live Demo

https://ipytone.readthedocs.io

## Requirements

* JupyterLab >= 3.0 or Jupyter notebook.
* numpy

## Install

You can install ipytone either with [pip](#with-pip) or [conda](#with-conda).

### With pip

```sh
pip install ipytone
# Skip the next step if using JupyterLab or Classic notebook version 5.3 and above
jupyter nbextension enable --py --sys-prefix ipytone
```

### With conda

```sh
conda install -c conda-forge ipytone
```

or mamba


```sh
mamba install -c conda-forge ipytone
```
