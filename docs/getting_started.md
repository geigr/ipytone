---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Getting Started

```{admonition} Summary
:class: note

In this tutorial, we'll see how to:

- generate and shape sounds by creating audio nodes and connecting them together
- control audio node attributes or parameters with Python code
- link audio node attributes or parameters with other widgets

Note: you can download this tutorial as a
{nb-download}`Jupyter notebook <getting_started.ipynb>`.
```

```{code-cell} ipython3
import ipytone
```

First, let's create a simple oscillator (i.e., a source audio node that
generates an audio signal using a basic waveform).

```{code-cell} ipython3
osc = ipytone.Oscillator(volume=-5)
```

Like every other ipytone widget, an {class}`~ipytone.Oscillator` has no visible output.

```{code-cell} ipython3
osc
```

+++ {"tags": []}

## Audio nodes

Like many other audio processing software, Tone.js and ipytone are built around
the concept of audio nodes. These consist of logical audio processing units that
can be connected to each other via their input / output anchors, letting the
audio signal flow from source nodes to the destination node (i.e., the
"speakers").

Ipytone audio nodes input / output may be accessed via their `input` / `output`
properties, which each either return another audio node object or `None`. For
example, an {class}`~ipytone.Oscillator` has no input (source node) and has a
{class}`~ipytone.Volume` node as output:

```{code-cell} ipython3
osc.input is None
```

```{code-cell} ipython3
osc.output
```

### Connecting audio nodes

The {class}`~ipytone.Oscillator` object created above won't make any sound until
it is connected to the destination. To connect it directly to the destination,
you can use the `connect` method like below or the more convenient
`to_destination` method.

```{code-cell} ipython3
# connects the oscillator (output) to the destination (input)
osc.connect(ipytone.destination)
```

Note that the oscillator still won't make any sound. You need to start / stop it
explicitly (all source nodes have `start` and `stop` methods):

```{code-cell} ipython3
osc.start()
```

```{code-cell} ipython3
osc.stop()
```

To disconnect the oscillator from the destination, you can use `disconnect`:

```{code-cell} ipython3
osc.disconnect(ipytone.destination)
```

More advanced connections are possible. In addition to `connect`, the `chain`
and `fan` convenience methods can be used to make multiple connections at once
(resp. in serial and in parallel).

An example with a {class}`~ipytone.Filter` node inserted between the oscillator
and the destination:

```{code-cell} ipython3
filtr = ipytone.Filter(type="highpass", frequency=1000)
```

```{code-cell} ipython3
# connects in chain oscillator -> filter -> destination
osc.chain(filtr, ipytone.destination)
```

### Method chaining

Most audio node methods return the node object itself, which allows chaining
them for convenience, e.g.,

```{code-cell} ipython3
# start the oscillator now and stop it after 1 second
osc.start().stop("+1")
```

## Audio node controls

An ipytone audio node may have several properties that are synchronized with the
front-end and that can be used for a fine-grained control on the generated or
processed audio.

The value of those properties generally corresponds to either:

- a "simple" value of `int`, `float` or `str`, etc. basic type

- an instance of {class}`~ipytone.Param` or {class}`~ipytone.Signal`, which
  holds some metadata in addition to the actual value (e.g., units) and provides
  convenient methods that can be used to schedule value changes (see below).

+++

### Basic node properties

Basic audio node property values can be read/written directly with Python.

An example with the oscillator `type` (i.e., its waveform shape):

```{code-cell} ipython3
osc.type
```

```{code-cell} ipython3
osc.type = "triangle"

osc.start().stop("+1")
```

### Param and Signal

When an audio node property is a {class}`~ipytone.Param` or
{class}`~ipytone.Signal` instance, the actual value can be read / written via
the `value` property of that instance.

An example with the oscillator `frequency`:

```{code-cell} ipython3
osc.frequency
```

```{code-cell} ipython3
osc.frequency.value
```

```{code-cell} ipython3
osc.frequency.value = 800

osc.start().stop("+1")
```

### Controlling audio nodes with Python

#### "Pure-Python" example

In the example below the frequency of the oscillator is gradually increased by
directly setting the frequency value within a Python function.

```{code-cell} ipython3
import time

def linear_ramp_to(value, ramp_time):
    n = 100
    time_step = ramp_time / n
    freq_step = (value - osc.frequency.value) / n
    for i in range(n):
        time.sleep(time_step)
        osc.frequency.value += freq_step
```

```{code-cell} ipython3
osc.frequency.value = 440

osc.start()
linear_ramp_to(800, 3)
osc.stop()
```

Although it is working, this solution is not optimal:

- the Python interpreter is blocked while the frequency of the oscillator is
  updated (although there might be ways to make it non-blocking)

- the actual frequency update steps in the front-end may not happen at an
  "audio-friendly" accuracy (slow data transfer between the Python kernel and
  the front-end can make things even worse)

+++

#### Using ipytone (Tone.js) scheduling

The same effect than in the example above can be achieved with ipytone method calls. 

Those calls send a few messages in the front-end, which are then processed
right-away to schedule a few events at specific times (via Tone.js and
utlimately via the Web Audio API). This approach overcomes the limitations of
the "pure-Python" solution above (i.e., non-blocking and more accurate
scheduling).

```{code-cell} ipython3
osc.frequency.value = 440
osc.start().stop("+3")
osc.frequency.linear_ramp_to(800, 3)
osc.frequency.set_value_at_time(440, "+3")
```

```{important}
When triggered in the front-end, scheduled events will not update and/or
synchronize the `value` property of a {class}`~ipytone.Param` or
{class}`~ipytone.Signal` in Python. This property thus won't always
return the current, actual value.

Ipytone provides other ways to track value updates from Python. See the
[Synchronizing Audio State](synchronizing) tutorial.
```

### Controling audio nodes with (ipy)widgets

Ipytone audio nodes are widgets and can thus be integrated with other widgets
for more interactive control, e.g., via widget events (i.e., `observe`, `link`,
`jslink`).

Here is a basic example with a few UI widgets to control the oscillator type,
frequency and playback state.

```{code-cell} ipython3
import ipywidgets

freq_slider = ipywidgets.FloatSlider(
    value=440,
    min=100,
    max=1000,
    step=1,
)

type_dropdown = ipywidgets.Dropdown(
    options=['sine', 'square', 'sawtooth', 'triangle'],
    value='sine',
)

toggle_play_button = ipywidgets.ToggleButton(
    value=False,
    description="Start/Stop"
)

ipywidgets.jslink((freq_slider, 'value'), (osc.frequency, 'value'))
ipywidgets.link((type_dropdown, 'value'), (osc, 'type'))

def start_stop_osc(change):
    if change['new']:
        osc.start()
    else:
        osc.stop()

toggle_play_button.observe(start_stop_osc, names='value')

ipywidgets.VBox([freq_slider, type_dropdown, toggle_play_button])
```

## Dispose audio nodes

If audio nodes are not used anymore, it is recommended to dispose it. Disposing a
node instance means that all of its underlying Web Audio nodes are disconnected
and freed for garbage collection in the front-end.

```{code-cell} ipython3
osc.dispose()
```

```{code-cell} ipython3
osc.disposed
```

```{code-cell} ipython3
filtr.dispose()
```

```{note}
When the `close()` method of an ipytone node widget is called, the node is
automatically disposed.
```
