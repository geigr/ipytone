.. _release_notes:

.. currentmodule:: ipytone

Release Notes
=============

v0.5.0 (Unreleased)
-------------------

Enhancements
~~~~~~~~~~~~

- Added :py:class:`WaveShaper` signal node operator (:pull:`100`).
- Added :py:class:`PitchShift` effect node (:pull:`101`).
- Added :py:class:`FrequencyShifter` effect node (:pull:`102`).
- Added :py:meth:`Instrument.trigger_note` method that helps conditional
  scheduling of attack or release events within :py:class:`Part` callbacks.
  :py:class:`Note` has also a new ``trigger_type`` attribute (:pull:`105`).
- Added :py:attr:`Transport.state` read-only attribute and use Tonejs' Transport
  Emitter signals for syncing the state and position (:pull:`106`).

Bug fixes
~~~~~~~~~

- Effects: fix ignored initial value for ``wet`` (:issue:`86`, :pull:`103`).
- Add missing ``notes`` argument to :py:meth:`PolySynth.trigger_release()` and
  :py:meth:`Sampler.trigger_release` (:issue:`84`, :pull:`104`).
