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

# Timeline

```{admonition} Summary
:class: note

In this tutorial, we'll see how to schedule musical events along a global
transport timeline.

Note: you can download this tutorial as a
{nb-download}`Jupyter notebook <timeline.ipynb>`.
```

Tone.js offers the possibility to schedule with precision sound or musical
events along a global timeline. By analogy, this is very similar to how we use
the arrangement view in a classic DAW to position audio or MIDI clips and/or
draw automation curves.

```{code-cell} ipython3
import ipytone
```

## Transport

The Tone.js global timeline is exposed in Python with the
{class}`~ipytone.transport.Transport` singleton class, which may be accessed via
`ipytone.transport`:

```{code-cell} ipython3
t = ipytone.transport
```

```{important}
Like the audio context used by ipytone and Tone.js, the
{class}`~ipytone.transport.Transport` timeline
is exposed globally in the front-end. Consequently, if two or more notebooks
with independent kernels are open in the same JupyterLab tab, they
will all act on the same timeline. 
```

### Playback state, position, bpm, time signature...

+++

The playback state of the timeline is controlled by the
{func}`~ipytone.transport.Transport.start`,
{func}`~ipytone.transport.Transport.pause` and
{func}`~ipytone.transport.Transport.stop` methods.

```{code-cell} ipython3
t.start().stop("+1")
```

The `position` property can be used to move the current "cursor" along the
timeline. It accepts different kinds of values, e.g.,

- a string in the form of `"Bars:Beats:Sixteenths"`
- a string like `"4m"` (four measures from the beginning of the timeline) or "8n" (8-notes)
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

{class}`~ipytone.transport.Transport` has also properties for setting the BPM or
the time signature:

```{code-cell} ipython3
t.bpm
```

```{code-cell} ipython3
t.time_signature
```

## Basic scheduling

Basic event scheduling can be done either using
{class}`~ipytone.transport.Transport` with callbacks or using context managers
provided by ipytone.

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

Then we can pass it to one of the {func}`~ipytone.transport.Transport.schedule`,
{func}`~ipytone.transport.Transport.schedule_repeat` and
{func}`~ipytone.transport.Transport.schedule_once` methods of
{class}`~ipytone.transport.Transport`, e.g.,

```{code-cell} ipython3
# schedule the call repeatedly at every 4th bar note
event_id = t.schedule_repeat(callback, "4n")
```

```{code-cell} ipython3
t.start().stop("+2m")
```

Those schedule methods return an event id that can be used later to remove it
from the transport timeline with the {func}`~ipytone.transport.Transport.clear`,
method, e.g.,

```{code-cell} ipython3
t.clear(event_id)
```

```{code-cell} ipython3
# no scheduled event, no sound
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

Note that unlike the example above, the two note triggers here are scheduled
only once so they won't be re-triggered after stopping and restarting the
transport

```{code-cell} ipython3
# no scheduled event, no sound
t.start().stop("+2m")
```

## Advanced scheduling

Ipytone also exposes Tone.js event classes for more advanced and handy
scheduling.

+++

### Event

{class}`~ipytone.Event` is the base class of all events and accepts a callback
that has two arguments: `time` and a `value` (i.e., a pitch or a note).

```{code-cell} ipython3
def event_clb(time, value):
    synth.trigger_attack_release(value, "16n", time=time)
```

```{code-cell} ipython3
event = ipytone.Event(callback=event_clb, value="A4")
```

It can then be started / stopped anywhere along the transport timeline and can
even be looped:

```{code-cell} ipython3
event.loop = True
event.loop_start = "4:0:0"
event.loop_end = "8:0:0"
```

```{code-cell} ipython3
event.start()
```

```{important}
Events won't fire unless the {class}`~ipytone.transport.Transport` is started.
```

```{code-cell} ipython3
t.start()
```

{class}`~ipytone.Event` also provides some other properties to control its
playback rate and to randomize it.

```{code-cell} ipython3
# play it 4x faster
event.playback_rate = 4
```

```{code-cell} ipython3
# the probability to trigger the event
event.probability = 0.8
```

```{code-cell} ipython3
# apply a small random offset on the trigger time
event.humanize = 0.2
```

Call `cancel` to remove it from the transport timeline:

```{code-cell} ipython3
event.stop()
event.cancel()
```

### Loop

{class}`~ipytone.Loop` is a simplified event that is looped by default at a
user-defined interval. Like in basic scheduling, it accepts a callback with one
`time` argument.

```{code-cell} ipython3
loop = ipytone.Loop(callback=callback, interval="8n")
```

```{code-cell} ipython3
loop.start()
```

```{code-cell} ipython3
loop.stop()
```

```{code-cell} ipython3
loop.cancel()
```

### Part

{class}`~ipytone.Part` is a sequence of events that can be handled just like an
{class}`~ipytone.Event` (i.e., it is a music partition). It accepts a callback
with two `time` and `note` arguments.

```{important}
While Tone.js accepts any arbitrary value type for the second argument, ipytone
only accepts an instance of {class}`~ipytone.Note`. The way ipytone handles
Python callbacks (i.e., not "real" callbacks) imposes this restriction.
```

```{code-cell} ipython3
def part_clb(time, note):
     synth.trigger_attack_release(
         note.note, note.duration, time=time, velocity=note.velocity
     )
```

In the {class}`~ipytone.Part` constructor, events may be specified either with
instances of {class}`~ipytone.Note` (which contain information about the actual
note, time, duration and velocity) or an equivalent dictionary.

```{code-cell} ipython3
part = ipytone.Part(
    callback=part_clb,
    events=[
        ipytone.Note(0, "A4", duration="16n"),
        {"time": "8n", "note": "B4", "duration": "8n", "velocity": 0.5},
        ipytone.Note("2n", "E4", duration="16n"),
    ]
)
```

```{code-cell} ipython3
part.start()
```

Although the single events of a {class}`~ipytone.Part` cannot be accessed
directly, they can be further updated using the {class}`~ipytone.Part.add`,
{class}`~ipytone.Part.at`, {class}`~ipytone.Part.at`,
{class}`~ipytone.Part.remove` and {class}`~ipytone.Part.clear` methods.

```{code-cell} ipython3
part.add(ipytone.Note("16n", "A3", velocity=0.2))
```

```{code-cell} ipython3
part.at("2n", ipytone.Note("2n", "E5", duration="4n"))
```

```{code-cell} ipython3
part.clear()
```

```{code-cell} ipython3
part.stop()
```

### Sequence

{class}`~ipytone.Sequence` is an alternative to {class}`~ipytone.Part` where the
note events are evenly spaced at a given subdivision.

```{code-cell} ipython3
seq = ipytone.Sequence(
    callback=event_clb,
    events=["A4", "C4", "B4", "A5"],
    subdivision="8n",
)
```

A sequence is looped by default.

```{code-cell} ipython3
seq.start()
```

Events may be nested (the interval within a nested array corresponds to the
parent subdivision divided by the length of the nested array).

```{code-cell} ipython3
seq.events = ["A4", ["C4", "E4", "D4"], "B4", "A5"]
```

Blank intervals may be defined by `None` array elements:

```{code-cell} ipython3
seq.events = ["A4", ["C4", "E4", "D4"], "B4", None]
```

```{code-cell} ipython3
seq.stop()
```

### Pattern

{class}`~ipytone.Pattern` is like an arpeggiator, it cycles trough an sequence
of notes with a given pattern.

```{code-cell} ipython3
pat = ipytone.Pattern(
    callback=event_clb,
    values=["C3", "E3", "G3"],
    pattern="upDown",
)
```

```{code-cell} ipython3
pat.start()
```

```{code-cell} ipython3
pat.pattern="up"
```

```{code-cell} ipython3
pat.stop()
```

### Dispose events

Like audio nodes, events may also be disposed.

```{code-cell} ipython3
event.dispose()
loop.dispose()
part.dispose()
seq.dispose()
pat.dispose()
```

We've reached the end of this tutorial. Let's cancel all scheduled events, stop
the transport and dispose the synth.

```{code-cell} ipython3
t.cancel()
t.stop()
synth.dispose()
```
