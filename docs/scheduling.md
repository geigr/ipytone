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

# Scheduling

Tone.js offers the possibility to schedule sound or musical events along a
global timeline. By analogy, this is very similar to how we use the arrangement
view in a classic DAW to position audio or MIDI clips and/or draw automation
curves.

```{code-cell} ipython3
import ipytone
```

## Transport

The Tone.js global timeline is exposed in Python with the `ipytone.Transport`
singleton class, which may be accessed via `ipytone.transport`:

```{code-cell} ipython3
t = ipytone.transport
```

```{important}
Like the audio context used by ipytone and Tone.js, the `Transport` timeline
is exposed globally in the front-end. Consequently, if two or more notebooks
with independent kernels are open in the same JupyterLab tab, they
will all act on the same timeline. 
```

### Playback state, position, bpm, time signature...

+++

The playback state of the timeline is controlled by the `start`, `pause` and
`stop` methods.

```{code-cell} ipython3
t.start().stop("+1")
```

The `position` property can be used to move the current "cursor" along the
timeline. It accepts different kinds of values, e.g.,

- a string in the form of `"Bars:Beats:Sixteenths"`
- a string like `"4m"` (four measure from the beginning of the timeline)
- a float (number of seconds from the beginning of the timeline)

See the [Tone.js Wiki](https://github.com/Tonejs/Tone.js/wiki/Time) for more details.

```{code-cell} ipython3
t.position
```

It is possible to define a limited segment along the timeline that will be played in loop:

```{code-cell} ipython3
t.loop = True
t.loop_start = "4:0:0"
t.loop_end = "8:0:0"
```

Transport has also properties for setting the BPM or the time signature:

```{code-cell} ipython3
t.bpm
```

```{code-cell} ipython3
t.time_signature
```

## Basic scheduling

Basic event scheduling can be done either using `Transport` with callbacks or
using context managers provided by ipytone.

Let's first create an instrument

```{code-cell} ipython3
synth = ipytone.Synth(volume=-5).to_destination()
```

### Using callbacks

Callbacks must accept one `time` argument (in seconds) and usually implement in
their body all the events that we want be triggered at that time (e.g.,
instrument note, parameter automation, etc.).

```{code-cell} ipython3
def callback(time):
    synth.trigger_attack_release("C4", "16n", time=time)
```

Then we can pass it to one of the `schedule`, `schedule_repeat` and
`schedule_once` methods of `Transport`, e.g.,

```{code-cell} ipython3
# schedule the call repeatedly at every 4th bar note
event_id = t.schedule_repeat(callback, "4n")
```

```{code-cell} ipython3
t.start().stop("+2m")
```

Those schedule methods return an event id that can be used later to remove it
from the transport timeline, e.g.,

```{code-cell} ipython3
t.clear(event_id)
```

```{code-cell} ipython3
# no scheduled event
t.start().stop("+2m")
```

````{important}
Ipytone doesn't handle those callbacks like you might expect,
i.e., like functions called at each of the scheduled times. Instead, ipytone
uses some tricks internally to reconstruct (more-or-less) equivalent callbacks
in the front-end before passing it to Tone.js scheduling functions.

As a consequence, Python callbacks have some limitations compared to Tone.js /
JS callbacks. More specifically, the Python code inside a callback will be
executed only once. Here is a bad example that won't behave as we'd like:

```python
import random

def callback(time):
    # This will randomly choose one note once for all repeated events!! 
    note = random.choice(["C4", "G4", "A4"]) 
    synth.trigger_attack_release(note, "16n", time=time)
```

There's also very limited support for making operations with the `time` argument
(currently, only addition is supported).
````

+++

### Using contexts

For convenience, the same scheduling operations can be achieved using context
managers. For example:

```{code-cell} ipython3
with ipytone.schedule_once("4n") as (time, event_id):
    synth.trigger_attack_release("A4", "16n", time=time)
    synth.trigger_attack_release("A5", "16n", time=time + "16n")
```

```{code-cell} ipython3
t.start().stop("+2m")
```

Unlike the example above, the two note triggers here are scheduled only once so
they won't be re-triggered after stopping and restarting the transport

```{code-cell} ipython3
# no scheduled event
t.start().stop("+2m")
```

## Advanced scheduling

Ipytone also exposes Tone.js event classes for more advanced and practical
scheduling.

+++

### Event

```{code-cell} ipython3

```

### Loop

```{code-cell} ipython3

```

### Part

```{code-cell} ipython3

```

### Sequence

```{code-cell} ipython3

```

### Pattern

```{code-cell} ipython3

```

```{code-cell} ipython3

```

```{code-cell} ipython3

```

```{code-cell} ipython3

```

```{code-cell} ipython3
t.cancel()
```

```{code-cell} ipython3
synth.dispose()
```

```{code-cell} ipython3

```
