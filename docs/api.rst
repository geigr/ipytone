
.. _api:

API reference
=============

.. note::

   Apart from a few subtle differences, ipytone closely follows the
   `Tone.js API`_. Some of the Tone.js features are not yet available in
   ipytone.

.. note::

   The majority of iyptone classes listed here derive from ``ipywidgets.Widget``.
   To keep the documentation clear and succinct, the Widget-specific API is
   not shown here. Please refer to the `ipywidgets`_ documentation.

.. _`Tone.js API`: https://tonejs.github.io/docs/14.7.77/index.html
.. _`ipywidgets`: https://ipywidgets.readthedocs.io_

Core
----

.. currentmodule:: ipytone
.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   AudioBuffer
   AudioBuffers
   Gain
   Param
   PyAudioNode
   Volume

.. autosummary::
   :toctree: _api_generated/

   destination
   get_audio_graph

.. _api_source:

Source
------

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   LFO
   AMOscillator
   FatOscillator
   FMOscillator
   Noise
   OmniOscillator
   Oscillator
   Player
   Players
   PulseOscillator
   PWMOscillator

.. _api_instrument:

Instrument
----------

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   AMSynth
   DuoSynth
   FMSynth
   Instrument
   MembraneSynth
   Monophonic
   MonoSynth
   NoiseSynth
   PluckSynth
   PolySynth
   Sampler
   Synth

Effect
------

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Distortion
   FeedbackDelay
   PingPongDelay
   Reverb
   Tremolo
   Vibrato

Component
---------

.. _api_analysis:

Analysis
~~~~~~~~

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Analyser
   FFT
   DCMeter
   Follower
   Meter
   Waveform

Channel
~~~~~~~

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Channel
   CrossFade
   Merge
   Mono
   MultibandSplit
   Panner
   PanVol
   Solo
   Split

Dynamics
~~~~~~~~

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Compressor
   Limiter
   MultibandCompressor

Envelope
~~~~~~~~

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   AmplitudeEnvelope
   Envelope
   FrequencyEnvelope

Filter
~~~~~~

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   EQ3
   BiquadFilter
   FeedbackCombFilter
   Filter
   LowpassCombFilter
   OnePoleFilter

Signal
------

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Abs
   Add
   AudioToGain
   GreaterThan
   Multiply
   Negate
   Pow
   Scale
   Signal
   Subtract

Transport
---------

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   transport.Transport

.. autosummary::
   :toctree: _api_generated/

   schedule
   schedule_once
   schedule_repeat
   transport

Event
-----

.. autosummary::
   :toctree: _api_generated/
   :template: ipytone-class-template.rst

   Event
   Loop
   Note
   Part
   Pattern
   Sequence
