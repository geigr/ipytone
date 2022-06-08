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

(built-in-instruments)=
## Built-in instruments

Ipytone provides a few built-in instruments (see Section
[Instrument](api_instrument) of API reference) that perform basic or more
advanced sound synthesis from a combination of connected nodes (oscillators,
envelopes, etc.). Ipytone also provides a [Sampler](sampler).

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

{class}`~ipytone.Monophonic` synthesizers can only play one note at a time. They
all have a `portamento` attribute, which allows smoothly sliding the frequency
between two triggered notes.

Let's create a {class}`~ipytone.MonoSynth`:

```{code-cell} ipython3
msynth = ipytone.MonoSynth().to_destination()
```

```{code-cell} ipython3
# without portamento
msynth.trigger_attack_release("C3", 0.5)
msynth.trigger_attack_release("C5", 0.5, time="+0.25")
```

```{code-cell} ipython3
msynth.portamento = 0.3
```

```{code-cell} ipython3
# with portamento
msynth.trigger_attack_release("C3", 0.5)
msynth.trigger_attack_release("C5", 0.5, time="+0.25")
```

```{code-cell} ipython3
msynth.dispose()
```

### Polyphonic synths

+++

{class}`~ipytone.PolySynth` allows turning any monophonic synthesizer into a
polyphonic synthesizer, i.e., an instrument that can play multiple notes at the
same time.

Let's create a polyphonic synth from a {class}`~ipytone.Synth`:

```{code-cell} ipython3
psynth = ipytone.PolySynth(voice=ipytone.Synth, volume=-8).to_destination()
```

A list of notes can be passed to the trigger methods to play a chord:

```{code-cell} ipython3
psynth.trigger_attack_release(["C3", "C4", "E4", "G4"], 0.5)
psynth.trigger_attack_release(["G2", "G4", "B4", "D4"], 0.5, time="+0.5")
psynth.trigger_attack_release(["C3", "C5", "E5", "G5"], 0.5, time="+1")
```

We can also pass a list of duration times to play the chord with some "expression":

```{code-cell} ipython3
psynth.trigger_attack_release(["C3", "C4", "E4", "G4"], [0.5, 0.7, 0.9, 1])
```

It is possible to change the parameters of the polyphonic synth via its `voice`
property, which returns a single instance of the mono synth. This instance is
deactivated (it doesn't make any sound), but changing the value of an attribute
of one of its components will apply to all voices of the polyphonic synth.

```{code-cell} ipython3
psynth.voice.envelope.attack = 0.4
```

```{code-cell} ipython3
# play each chord with a slow attack 
psynth.trigger_attack_release(["C3", "C4", "E4", "G4"], 0.5)
psynth.trigger_attack_release(["G2", "G4", "B4", "D4"], 0.5, time="+0.5")
psynth.trigger_attack_release(["C3", "C5", "E5", "G5"], 0.5, time="+1")
```

```{note}
Changing the settings of some components of the `PolySynth.voice` may have
no effect. This generally works with common components like the oscillator
and the amplitude envelope. 
```

In addition to `trigger_attack()`, `trigger_release()` and
`trigger_attack_release()`, {class}`~ipytone.PolySynth` provides a
`release_all()` method that will trigger release for all the active voices

```{code-cell} ipython3
psynth.trigger_attack(["C3", "C4", "E4", "G4"])
psynth.trigger_attack(["G2", "G4", "B4", "D4"], time="+0.5")
psynth.trigger_attack(["C3", "C5", "E5", "G5"], time="+1")
```

```{code-cell} ipython3
# release all chords triggered above
psynth.release_all()
```

The maximum number of active voices is controlled by `max_polyphony`. When
this number is reached, additional notes won't be played.

```{code-cell} ipython3
psynth.max_polyphony = 3
```

```{code-cell} ipython3
# this will play only 3 notes!
psynth.trigger_attack_release(["C3", "C4", "E4", "G4"], 0.5)
```

End of this tutorial!

```{code-cell} ipython3
psynth.dispose()
```
