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

(synchronizing)=
# Synchronizing Audio State

```{admonition} Summary
:class: note

In this tutorial, we'll see how to synchronize specific properties like
an audio signal value, the transport timeline position, the playback state, etc.
with the back-end (Python) or link them with other Jupyter widgets.
We'll also give an overview of the audio analysis nodes available in ipytone.

Note: you can download this tutorial as a
{nb-download}`Jupyter notebook <observe_link.ipynb>`.
```

```{code-cell} ipython3
import ipytone
import ipywidgets
import matplotlib.pyplot as plt
```

One thing specific to audio signals (and parameters) is that their value may be
updated continuously in the front-end (to be correct: still at discrete steps
but at a very high rate, i.e., the audio sample rate is often set to 44.1 MHz).

This makes challenging the synchronization of those widgets with the back-end
(e.g., for handling specific events in Python) or with other elements in the
front-end (e.g., widget linking). The common ways to handle events with Jupyter
widgets (see Section [Widget
Events](https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20Events.html))
won't help much here.

Fortunately, ipytone provides alternative ways to deal with this issue that are
very similar to the `observe()`, `link()` and `jslink()` functions applied to
"classic" Jupyter widgets.

+++

## Observing state from Python

Very much like the `observe()` method of a Jupyter widget, Ipytone provides a
`schedule_observe()` method that can be used for tracking special attributes
like

- the current value of a {class}`~ipytone.Param`, {class}`~ipytone.Signal`,
  {class}`~ipytone.Envelope` or any [analysis node](api_analysis) (see also
  Section [Analysis audio nodes](analysis) of this tutorial)

- the current progress and playback state of an {class}`~ipytone.Event`, a
  [source](api_source) node or the {class}`~ipytone.transport.Transport`
  timeline.
  
- and more...

+++

Let's create a {class}`~ipytone.Synth`:

```{code-cell} ipython3
synth = ipytone.Synth().to_destination()
```

For example, we would like to track the current frequency of the synth
oscillator, which will depend on the note played.

Let's first create a function that will get this value and print it in an output
widget:

```{code-cell} ipython3
output = ipywidgets.Output()

def print_new_value(change):
    widget = change["owner"].observed_widget

    with output:
        print(widget, " : ", change["new"])

output
```

We can then register this function on the synth oscillator frequency, using
`schedule_observe()`:

```{code-cell} ipython3
synth.oscillator.frequency.schedule_observe(
    print_new_value,
    update_interval=0.5,
    name="value",
    transport=False,
)
```

```{note}
Unlike the Jupyter widget `observe()` method, `schedule_observe()` can track
only one attribute.

The `update_interval` option corresponds to the time
interval between two consecutive synchronizations of the attribute with the
back-end.

The `transport` option controls how to schedule the synchronization
(either using Tone.js `Transport.schedule_repeat` or using Javascript's
`setInterval`). It is recommended to use `transport=True` if you schedule events
along the transport timeline (see the [Timeline](timeline) tutorial).
```

Let's trigger a couple of notes. Just after running this cell, you should see
the oscillator frequency values printed in the output of the cell further above.

```{code-cell} ipython3
synth.trigger_attack_release("C3", 1)
synth.trigger_attack_release("A3", 1, time="+1")
```

Let's also observe the current value of the envelope (with a slightly higher
time resolution):

```{code-cell} ipython3
# set a longer envelope attack
synth.envelope.attack = 1
```

```{code-cell} ipython3
synth.envelope.schedule_observe(print_new_value, update_interval=0.1)
```

You should now also see the envelope values printed above when running the cell
below:

```{code-cell} ipython3
synth.trigger_attack_release("C3", 2)
```

We can stop tracking those attributes with the `schedule_unobserve()` method.
This will stop the repeated synchronizations with the back-end.

```{code-cell} ipython3
synth.oscillator.frequency.schedule_unobserve(print_new_value)
synth.envelope.schedule_unobserve(print_new_value)
```

### Observing both state and time

Because the synchronization with the back-end (Python) happens with some latency
that is is not known with precision, it might be useful to know exactly at which
time the attribute value has been read (either the time of the Tone.js main
audio context or the time along the Tone.js Transport timeline). By setting
`observe_time=True`, we can get both that time and the attribute value in
Python. For example:

```{code-cell} ipython3
synth.oscillator.frequency.schedule_observe(
    print_new_value,
    update_interval=3,
    observe_time=True
)
```

You should see a `(time, value)` tuple printed in the output below. Note that
because the time is never constant, the tuple gets updated and the function is
called at every synchronization, regardless of whether or not the value has
changed.

```{code-cell} ipython3
output.clear_output()
output
```

```{code-cell} ipython3
synth.oscillator.frequency.schedule_unobserve(print_new_value)
```

## Linking audio widgets

Similarly to `observe()` -> `schedule_observe()`, ipytone provides extra methods
for widget linking:

- `dlink()` -> `schedule_dlink()`
- `jsdlink()` -> `schedule_jsdlink()`

```{note}
There's no such `schedule_link()` or `schedule_jslink()` method,
as bi-directional linking doesn't make much sense for audio signals.
```

For example, let's connect the envelope of the synth created above to a
`FloatProgress` widget so that we can have a better view on the evolution of the
envelope through time. The link below is made only in the front-end (by default
synchronizations will happen at a high frequency).

```{code-cell} ipython3
progress = ipywidgets.FloatProgress(value=0, min=0, max=1)

link = synth.envelope.schedule_jsdlink((progress, "value"))

progress
```

Now let's play a long note:

```{code-cell} ipython3
synth.trigger_attack_release("C3", 2)
```

To unlink the two widgets, use `unlink()` like below. This will stop the
repeated attribute synchronizations between the two widgets.

```{code-cell} ipython3
link.unlink()
```

(analysis)=
## Analysis audio nodes

Ipytone's [audio analysis widgets](api_analysis) are useful for synchronizing
audio signals. Any audio node can be connected to those widgets, which can then
be used for observing the signal value from Python or linking it with another
widget.

+++

### Analyser

{class}`~ipytone.Analyser` is a generic analysis node for getting the current
waveform or frequency (FFT) data as a numpy array.

The example below plots at a regular interval the current waveform generated by
the synthesizer created above.

```{code-cell} ipython3
plot_output = ipywidgets.Output(layout=ipywidgets.Layout(height="300px"))

def plot_change(change):
    plot_output.clear_output()
    with plot_output:
        plt.plot(change["new"])
        plt.show()
        
plot_output
```

```{code-cell} ipython3
analyser = ipytone.Analyser(type="waveform")
synth.connect(analyser)
```

```{code-cell} ipython3
analyser.schedule_observe(plot_change, update_interval=1)
```

If you play a note, you should see the waveform drawn in the plot above:

```{code-cell} ipython3
synth.trigger_attack_release("C3", 2)
```

Analyser has a `smoothing` attribute that controls the time window average of
the analyzed waveform or frequency. Let's set a high value and you should see
the waveform evolve more smoothly in the plot.

```{code-cell} ipython3
analyser.smoothing = 5
```

```{code-cell} ipython3
synth.trigger_attack_release("C3", 2)
```

```{code-cell} ipython3
analyser.schedule_unobserve(plot_change)
analyser.dispose()
```

### FFT and Waveform

{class}`~ipytone.FFT` and {class}`~ipytone.Waveform` both work very much like
{class}`~ipytone.Analyser`, with some default options and only for mono audio
signals.

+++

### Meter and DCMeter

{class}`~ipytone.Meter` can be used to get the current (RMS) level of an audio
signal either in decibels (default) or in the [0-1] range.

For example, let's see the output gain of the synthesizer in real time:

```{code-cell} ipython3
progress = ipywidgets.FloatProgress(value=0, min=0, max=1)

progress
```

```{code-cell} ipython3
meter = ipytone.Meter(normal_range=True)
synth.connect(meter)

link = meter.schedule_jsdlink((progress, "value"))
```

```{code-cell} ipython3
synth.trigger_attack_release("C3", 2)
```

```{code-cell} ipython3
link.unlink()
meter.dispose()
```

{class}`~ipytone.DCMeter` is similar to {class}`~ipytone.Meter` except that it
outputs the raw value of the audio signal in the [-1, 1] range.

+++

End of this tutorial!

```{code-cell} ipython3
synth.dispose()
```
