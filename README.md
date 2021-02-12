[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/benbovy/ipytone/master?urlpath=lab%2Ftree%2Fexamples)
[![Tests](https://github.com/benbovy/ipytone/workflows/Test/badge.svg)](https://github.com/benbovy/ipytone/actions)

# ipytone

Interactive audio in Jupyter, using [Tone.js](https://tonejs.github.io).

Note: This is still at a proof-of-concept stage.

## Requirements

* JupyterLab >= 3.0

## Contributing

### Development install

Development installation requires NodeJS and [yarn](https://yarnpkg.com/) be
installed. You can easily install it with conda:

``` bash
conda install nodejs yarn -c conda-forge
```

Clone this repository, change directory to the ipytone directory and install the
package in development mode:

```bash
python -m pip install -e .

# if you use jupyterlab, you can also install the pre-built extension
# in development mode and re-build the extension (see below):
jupyter labextension develop . --overwrite
```

### Re-build the extension

After making changes to the typescript source code, you need to rebuild the extension:

``` bash
yarn run build

# or if you use jupyterlab
yarn run build:lib
yarn run build:labextension:dev
```

You can then refresh the notebook or JupyterLab in the browser to test the changes.

If you change the Python source, you need to reload the Python kernel. 
