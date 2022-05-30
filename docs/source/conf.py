# -*- coding: utf-8 -*-
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "jupyterlite_sphinx",
]

jupyterlite_config = "jupyterlite_config.json"

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "ipytone"
copyright = "2022, Benoit Bovy"
author = "Benoit Bovy"

# get version from python package:
import os

here = os.path.dirname(__file__)
repo = os.path.join(here, "..", "..")
_version_py = os.path.join(repo, "ipytone", "_version.py")
version_ns = {}
with open(_version_py) as f:
    exec(f.read(), version_ns)

# The short X.Y version.
version = "%i.%i" % version_ns["version_info"][:2]
# The full version, including alpha/beta/rc tags.
release = version_ns["__version__"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["**.ipynb_checkpoints", ".ipynb"]

highlight_language = "python"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output ----------------------------------------------

html_theme = "pydata_sphinx_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = dict(github_url="https://github.com/benbovy/ipytone")

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "ipytonedoc"

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"https://docs.python.org/": None}
