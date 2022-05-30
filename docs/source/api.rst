
.. _api:

API reference
=============

Apart from a few subtle differences, Ipytone closely follows `Tone.js' API`_.
Some Tone.js features are not yet available in Ipytone.

.. _`Tone.js' API`: https://tonejs.github.io/docs/14.7.77/index.html

Core
----

.. currentmodule:: ipytone
.. autosummary::
   :toctree: _api_generated/

   AudioBuffer
   AudioBuffers
   Gain
   Param
   PyAudioNode
   Volume
   destination
   get_audio_graph

Source
------

.. autosummary::
   :toctree: _api_generated/

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

Instrument
----------

.. autosummary::
   :toctree: _api_generated/

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

   Distortion
   FeedbackDelay
   PingPongDelay
   Reverb
   Tremolo
   Vibrato

Component
---------

Analysis
~~~~~~~~

.. autosummary::
   :toctree: _api_generated/

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

   Compressor
   Limiter
   MultibandCompressor

Envelope
~~~~~~~~

.. autosummary::
   :toctree: _api_generated/

   AmplitudeEnvelope
   Envelope
   FrequencyEnvelope

Filter
~~~~~~

.. autosummary::
   :toctree: _api_generated/

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

   schedule
   schedule_once
   schedule_repeat
   transport

Event
-----

.. autosummary::
   :toctree: _api_generated/

   Event
   Loop
   Note
   Part
   Pattern
   Sequence
