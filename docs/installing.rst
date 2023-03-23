
.. _installation:

Installation
============

Using pip
---------

.. code:: bash

   pip install ipytone

Using conda
-----------
.. code:: bash

   conda install ipytone -c conda-forge

Or using mamba:

.. code:: bash

   mamba install ipytone -c conda-forge

JupyterLab extension (v2 only)
------------------------------

For JupyterLab v2.x, the ipytone extension must also be installed::

  jupyter labextension install ipytone

For JupyterLab v3+, not extra-step is required here.

Development installation
------------------------

To install a developer version of ipytone, you will first need to clone
the repository::

  git clone https://github.com/benbovy/ipytone
  cd ipytone

You can then install all the ipytone dependencies and developer tools using
conda (or mamba)::

  conda env create --file=environment-dev.tml
  conda activate ipytone-dev

Next, you can use pip to install ipytone in editable mode::

  python -m pip install -e .

In order to re-build the front-end extension after editing it you need to first
install its dependencies via the `Yarn`_ package manager::

  yarn install

If you are developing on the classic Jupyter Notebook, run the commands below to
build and install the extension::

  yarn run build:lib
  yarn run build:nbextension

Or if your are developing on JupyterLab::

  yarn run build:lib
  yarn run build:labextension:dev

Run the tests
-------------

To run ipytone's (Python) tests::

  python -m pytest ipytone

Linting and formatting
----------------------

Some pre-configured git hooks are available via `Pre-commit`_ to automatically
check and format the Python code (using `Black`_ and `Ruff`_) and the Typescript
code (using `Prettier`_). To install those hooks, run the following command::

  pre-commit install

.. _`Black`: https://black.readthedocs.io/en/stable/
.. _`Ruff`: https://beta.ruff.rs/docs/
.. _`Prettier`: https://prettier.io/
.. _`Pre-commit`: https://pre-commit.com/
.. _`Yarn`: https://yarnpkg.com/
