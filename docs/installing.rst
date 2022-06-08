
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

Next, install it with a develop install using pip::

  pip install -e .

To build, install and enable the front-end extension, you need to first install
the `Yarn`_ package manager. Then, to install all dependencies of this project,
run the command::

  yarn install

If you are developing on the classic Jupyter Notebook, run the commands below to
build and install the extension::

  yarn run build:lib
  yarn run build:nbextension

Or if your are developing on JupyterLab::

  yarn run build:lib
  yarn run build:labextension:dev


.. _`Yarn`: https://yarnpkg.com/
