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

# Audio Samples

```{admonition} Summary
:class: note

In this tutorial, we'll see how to load audio samples (either from file
urls or numpy arrays) in the front-end and play them with a player or
a sampler.

Note: you can download this tutorial as a
{nb-download}`Jupyter notebook <audio_samples.ipynb>`.
```

```{code-cell} ipython3
import ipytone
import numpy as np
import matplotlib.pyplot as plt
```

## Audio buffers

{class}`~ipytone.AudioBuffer` and {class}`~ipytone.AudioBuffers` can be used to
create one or more audio buffers in the front-end from either files or a numpy
arrays.

+++

### Example 1: load one sample from a numpy array

Let's first create a custom waveform with numpy:

```{code-cell} ipython3
# sine + noise waveform

sample_rate = 44100
duration = 1
frequency = 440

size = int(sample_rate * duration)

factor = frequency * np.pi * 2 / sample_rate
waveform = np.sin(np.arange(size) * factor)
waveform += np.random.uniform(-0.1, 0.1, size=size)
```

Let's have a look at the waveform: 

```{code-cell} ipython3
plt.plot(waveform[0:1000]);
```

We can then directly pass the numpy array to the {class}`~ipytone.AudioBuffer`
constructor:

```{code-cell} ipython3
sine_noise_buffer = ipytone.AudioBuffer(url_or_array=waveform)
```

```{important}
Create a buffer from a numpy array is currently limited to samples
of a duration less or equal to 10 seconds.
```

### Example 2: load multiple samples from files (urls)

Let's create new buffers from wav or mp3 file urls.

```{important}
Depending on the given urls, creating the buffers may be blocked due to the
server [CORS](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing)
policy.

If you want to load local files from within JupyterLab, you can get a valid url
by going in the file browser, right-click on the file and "Copy Download Link".
```

```{code-cell} ipython3
# These urls are likely wrong if you've downloaded this notebook and run it locally
base_url = "http://localhost:8888/files/docs/"
kick_url = "kick.wav?_xsrf=2%7C1ced6df3%7C0514fa79e3ccfbcffefe3f864a0d4032%7C1654092692"
snare_url = "snare.wav?_xsrf=2%7C1ced6df3%7C0514fa79e3ccfbcffefe3f864a0d4032%7C1654092692"
```

```{code-cell} ipython3
drum_buffers = ipytone.AudioBuffers(
    base_url=base_url,
    urls={"kick": kick_url, "snare": snare_url},
)
```

Single buffers may be accessed via the `buffers` property, e.g.,

```{code-cell} ipython3
drum_buffers.buffers["kick"]
```

### Buffer attributes

Audio buffers have a few read-only attributes like `loaded`, `duration`,
`length`, `sample_rate`, etc.

```{code-cell} ipython3
# whether all drum buffers are loaded in the front-end
drum_buffers.loaded
```

```{code-cell} ipython3
# clip duration (in seconds)
drum_buffers.buffers["kick"].duration
```

```{code-cell} ipython3
# clip length in number of samples
drum_buffers.buffers["kick"].length
```

And a `reverse` property that can be read or written:

```{code-cell} ipython3
drum_buffers.buffers["kick"].reverse
```

## Player

{class}`~ipytone.Player` is a source audio node for playing samples.

Let's create a new player from the custom sine/noise buffer created above:

```{code-cell} ipython3
player = ipytone.Player(sine_noise_buffer).to_destination()
```

```{note}
We can also directly pass an url to {class}`~ipytone.Player`,
which will automatically create an audio buffer.
```

+++

Like any other source, it has `start()` ant `stop()` methods: 

```{code-cell} ipython3
player.start().stop("+3")
```

It also has some additional properties, e.g., to add fade-in/out, play it
looped, change its playback rate, etc.

```{code-cell} ipython3
player.loop = True
player.fade_in = 0.2
player.playback_rate = 0.5
```

```{code-cell} ipython3
player.start().stop("+3")
```

For convenience, {class}`~ipytone.Players` can be used to create multiple
{class}`~ipytone.Player` instances at once.

Let's create players from the drum buffers created above:

```{code-cell} ipython3
drums = ipytone.Players(drum_buffers.buffers).to_destination()
```

We can get the individual players with {func}`~ipytone.Players.get_player()`:

```{code-cell} ipython3
drums.get_player("kick").start().stop("+1")
drums.get_player("snare").start("+0.5").stop("+1.5")
```

(sampler)=
## Sampler

As an alternative to {class}`~ipytone.Player`, {class}`~ipytone.Sampler` is an
instrument based on samples.

For example, let's create a sampler with the sine/noise buffer created above.
The name of the buffers must correspond to something that can be interpreted
like a musical note.

```{code-cell} ipython3
sampler = ipytone.Sampler({"A4": sine_noise_buffer}, volume=-10).to_destination()
```

Being an instrument, {class}`~ipytone.Sampler` provides the same interface than
any other instrument (see the [instruments](built-in-instruments) tutorial).
When playing a note, the sampler selects the closest sample and adapts the pitch
to generate the corresponding note.

```{code-cell} ipython3
sampler.trigger_attack_release("C2", 0.2)
sampler.trigger_attack_release("A2", 0.2, time="+0.2")
sampler.trigger_attack_release("C3", 0.2, time="+0.4")
sampler.trigger_attack_release("C4", 0.2, time="+0.6")
```

{class}`~ipytone.Sampler` is a polyphonic instrument:

```{code-cell} ipython3
# trigger a chord
sampler.trigger_attack_release(["C4", "E4", "G4"], 0.5)
```

## Dispose buffers

Like for other audio nodes, audio buffers should be disposed if they are not
used anymore.

```{code-cell} ipython3
sine_noise_buffer.dispose()
drum_buffers.dispose()

# note: dispose the player(s) or the sampler
# would also dispose the buffers
player.dispose()
drums.dispose()
sampler.dispose()
```
