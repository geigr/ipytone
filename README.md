
# ipytone

[![Build Status](https://travis-ci.org/benbovy/ipytone.svg?branch=master)](https://travis-ci.org/benbovy/ipytone)
[![codecov](https://codecov.io/gh/benbovy/ipytone/branch/master/graph/badge.svg)](https://codecov.io/gh/benbovy/ipytone)


Interactive audio in Jupyter

## Installation

You can install using `pip`:

```bash
pip install ipytone
```

Or if you use jupyterlab:

```bash
pip install ipytone
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

If you are using Jupyter Notebook 5.2 or earlier, you may also need to enable
the nbextension:
```bash
jupyter nbextension enable --py [--sys-prefix|--user|--system] ipytone
```
