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

# Instruments

+++


```{admonition} Summary
:class: note

In this tutorial, we'll see how to create a (very) basic synthesizer from
stratch using oscillators and envelopes. We'll also give an overview of the
instruments built in ipytone (copied from Tone.js).

Note: you can download this tutorial as a
{nb-download}`Jupyter notebook <instrument.ipynb>`.
```

```{code-cell} ipython3
import ipytone
import matplotlib.pyplot as plt
```

## Building a synth from scratch

The most basic elements of a synthesizer are oscillators and envelopes. Let's
build a very simple synth using one oscillator and one amplitude envelope.

+++

### Oscillator

Ipytone provides different oscillators (see Section [Source](api_source) of API
reference) that can generate sound from basic waveforms modulated at a given
frequency.

Let's here use an {class}`~ipytone.Oscillator` that we connect to the
destination (speakers) so we can hear it.

```{code-cell} ipython3
osc = ipytone.Oscillator().to_destination()
```

By default, the type (shape) of the waveform is a `sine`. Ipytone Oscillators
generally support other waveform types such as `sawtooth`, `triangle`, `square`,
etc.

```{code-cell} ipython3
osc.type
```

The frequency of the oscillator gives the note. It is possible to set it with a
number (Hertz) or a string (note + octave), e.g.,

```{code-cell} ipython3
osc.frequency.value = "C4"
```

With the `start()` and `stop()` methods, this already gives a very basic synth
that can trigger notes (beware of the volume of your speakers):

```{code-cell} ipython3
osc.start().stop("+0.5")
```

That's not very fancy, though. The audio signal changes abruptly when starting /
stopping the oscillator, causing unpleasant "clicks".

+++

### Envelope

An envelope allows to smoothly modulate a signal over time with a curve that is
generally characterized by 4 segments: attack, decay, sustain and release.

Ipytone provides the such an {class}`~ipytone.Envelope` as well as subclasses
for the two most common envelopes:

- {class}`~ipytone.AmplitudeEnvelope` to modulate the gain of a signal
- {class}`~ipytone.FrequencyEnvelope` to modulate the frequency of a signal

To prevent clicks when starting / stopping the oscillator, let's connect it to
an {class}`~ipytone.AmplitudeEnvelope`:

```{code-cell} ipython3
# first disconnect the oscillator from the destination
osc.disconnect(ipytone.destination)

env = ipytone.AmplitudeEnvelope(sync_array=True)
osc.chain(env, ipytone.destination)
```

It is possible to get or set the overall shape of the envelope using its
`attack`, `decay`, `sustain` and `release` attributes, each synchronized with
the front-end (more attribute allows to set the shape of the curve - linear,
exponential, etc. - of each segment):

```{code-cell} ipython3
[env.attack, env.decay, env.sustain, env.release]
```

Because we've set `sync_array=True` above when creating the envelope, we can get
the whole envelope curve data in Python via its `array` attribute. It is useful
for visualizing the envelope:

```{code-cell} ipython3
---
tags: [remove-output, raises-exception]
---
plt.plot(env.array);
```

```{code-cell} ipyton3
---
tags: [remove-input]
---
# envelope data pre-computed as no front-end in
# jupyter-execute
import numpy as np
data = np.load("envelope_data1.npy")
plt.plot(data);
```

Let's change the envelope shape a bit and see the result:

```{code-cell} ipython3
env.attack = 0.1
env.sustain = 0.5
```

```{code-cell} ipython3
---
tags: [remove-output, raises-exception]
---
plt.plot(env.array);
```

```{code-cell} ipyton3
---
tags: [remove-input]
---
# envelope data pre-computed as no front-end in
# jupyter-execute
data = np.load("envelope_data2.npy")
plt.plot(data);
```

Now that the oscillator is connected to the envelope, we shouldn't hear any sound
when starting the oscillator:

```{code-cell} ipython3
# no sound!
osc.start()
```

We need to explicitly trigger the attack part of the envelope with
{func}`~ipytone.Envelope.trigger_attack`:

```{code-cell} ipython3
env.trigger_attack()
```

The oscillator signal will then modulate over the attack and decay part of the
envelope until it reaches the sustain level.

To trigger the release part of the envelope, we need to call
{func}`~ipytone.Envelope.trigger_release`:

```{code-cell} ipython3
env.trigger_release()
```

Sometimes we want to trigger the release some specific time after having the
triggered the attack. This can be done with the
{func}`~ipytone.Envelope.trigger_attack_release` method:

```{code-cell} ipython3
# trigger attack and trigger release after 1/2 second
env.trigger_attack_release(0.5)
```

We won't need the oscillator and the envelope below. Before moving on, let's
dispose them

```{code-cell} ipython3
osc.dispose()
env.dispose()
```

## Built-in instruments

Ipytone provides a few built-in instruments (see Section
[Instrument](api_instrument) of API reference) that perform basic or more
advanced sound synthesis from a combination of connected nodes (oscillators,
envelopes, etc.).

Let's use the {class}`~ipytone.Synth` here:

```{code-cell} ipython3
synth = ipytone.Synth()
```

Instruments behave like audio nodes, i.e., we can connect them to other nodes:

```{code-cell} ipython3
# connect synth to the speakers
synth.connect(ipytone.destination)
```

All instruments can be played via a common interface including
{func}`~ipytone.Instrument.trigger_attack`,
{func}`~ipytone.Instrument.trigger_release` and
{func}`~ipytone.Instrument.trigger_attack_release` methods, e.g,

```{code-cell} ipython3
# trigger a "C4" note for 1/2 second
synth.trigger_attack_release("C4", 0.5)
```

Each instrument may expose its own components. The {class}`~ipytone.Synth` used
here combines an oscillator and an amplitude envelope just like we did above.

```{code-cell} ipython3
synth.oscillator
```

```{code-cell} ipython3
synth.envelope
```

```{code-cell} ipython3
# finished now with synth
synth.dispose()
```

### Monophonic synths

portamento, etc.

```{code-cell} ipython3

```

### Polyphonic synths

```{code-cell} ipython3

```

```{code-cell} ipython3

```
