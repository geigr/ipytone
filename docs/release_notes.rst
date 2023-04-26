.. _release_notes:

.. currentmodule:: ipytone

Release Notes
=============

v0.5.0 (Unreleased)
===================

Enhancements
~~~~~~~~~~~~

- Added :py:class:`WaveShaper` signal node operator (:pull:`100`).
- Added :py:class:`PitchShift` effect node (:pull:`101`).
- Added :py:class:`FrequencyFilter` effect node (:pull:`102`).

Bug fixes
~~~~~~~~~

- Effects: fix ignored initial value for ``wet`` (:issue:`86`, :pull:`103`).
- Add missing ``notes`` argument to :py:meth:`PolySynth.trigger_release()` and
  :py:meth:`Sampler.trigger_release` (:issue:`84`, :pull:`104`).
