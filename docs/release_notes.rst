.. _release_notes:

.. currentmodule:: ipytone

Release Notes
=============

v0.6.0 (unreleased)
-------------------

Bug fixes
~~~~~~~~~

- Fixed ``schedule_jsdlink`` so it doesn't synchronize state with the backend
  and fix ``unlink`` / ``unobserve`` with ``transport=True`` (:issue:`116`,
  :pull:`118`).

Maintenance
~~~~~~~~~~~

- CI: update minimum Python version to 3.9 (:pull:`112`).

v0.5.1
------

Bug fixes
~~~~~~~~~

- Fixed installation issue with notebook "classic" version <7 (:issue:`109`,
  :pull:`110`).

v0.5.0
------

Deprecated features
~~~~~~~~~~~~~~~~~~~

- ``ipytone.destination`` is deprecated, use :py:func:`get_destination`
  instead. Likewise, ``ipytone.transport`` is deprecated in favor of
  :py:func:`get_transport` (:pull:`108`).

Enhancements
~~~~~~~~~~~~

- Added :py:class:`WaveShaper` signal node operator (:pull:`100`).
- Added :py:class:`PitchShift` effect node (:pull:`101`).
- Added :py:class:`FrequencyShifter` effect node (:pull:`102`).
- Added :py:meth:`Instrument.trigger_note` method that helps conditional
  scheduling of attack or release events within :py:class:`Part` callbacks.
  :py:class:`Note` has also a new ``trigger_type`` attribute (:pull:`105`).
- Added ``Transport.state`` read-only attribute and use Tonejs' Transport
  Emitter signals for syncing the state and position (:pull:`106`).
- Added :py:class:`~core.Listener` and :py:class:`Panner3D` audio spatialization
  components (:pull:`107`).

Bug fixes
~~~~~~~~~

- Effects: fix ignored initial value for ``wet`` (:issue:`86`, :pull:`103`).
- Add missing ``notes`` argument to :py:meth:`PolySynth.trigger_release()` and
  :py:meth:`Sampler.trigger_release` (:issue:`84`, :pull:`104`).

Maintenance
~~~~~~~~~~~

- Ipywidgets 8 compatibility, use ruff for linting (Python), switch to Hatch
  build backend and pyproject.toml, enable pre-commit, etc. (:pull:`94`).
