#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Benoit Bovy.
# Distributed under the terms of the Modified BSD License.

from ._version import __version__, version_info
from .analysis import FFT, Analyser, DCMeter, Follower, Meter, Waveform
from .base import PyAudioNode
from .channel import Channel, CrossFade, Merge, Mono, MultibandSplit, Panner, PanVol, Solo, Split
from .core import AudioBuffer, AudioBuffers, Gain, Param, Volume, destination
from .dynamics import Compressor, Limiter, MultibandCompressor
from .effect import Distortion, FeedbackDelay, PingPongDelay, Reverb, Tremolo, Vibrato
from .envelope import AmplitudeEnvelope, Envelope, FrequencyEnvelope
from .event import Event, Loop, Note, Part, Pattern, Sequence
from .filter import (  # PhaseShiftAllpass,
    EQ3,
    BiquadFilter,
    FeedbackCombFilter,
    Filter,
    LowpassCombFilter,
    OnePoleFilter,
)
from .graph import get_audio_graph
from .instrument import (
    AMSynth,
    DuoSynth,
    FMSynth,
    Instrument,
    MembraneSynth,
    Monophonic,
    MonoSynth,
    NoiseSynth,
    PluckSynth,
    PolySynth,
    Sampler,
    Synth,
)
from .signal import (
    Abs,
    Add,
    AudioToGain,
    GreaterThan,
    Multiply,
    Negate,
    Pow,
    Scale,
    Signal,
    Subtract,
)
from .source import (
    LFO,
    AMOscillator,
    FatOscillator,
    FMOscillator,
    Noise,
    OmniOscillator,
    Oscillator,
    Player,
    Players,
    PulseOscillator,
    PWMOscillator,
)
from .transport import schedule, schedule_once, schedule_repeat, transport


def _jupyter_labextension_paths():
    """Called by Jupyter Lab Server to detect if it is a valid labextension and
    to install the widget

    Returns
    =======
    src: Source directory name to copy files from. Webpack outputs generated files
        into this directory and Jupyter Lab copies from this directory during
        widget installation
    dest: Destination directory name to install widget files to. Jupyter Lab copies
        from `src` directory into <jupyter path>/labextensions/<dest> directory
        during widget installation
    """
    return [
        {
            "src": "labextension",
            "dest": "ipytone",
        }
    ]


def _jupyter_nbextension_paths():
    """Called by Jupyter Notebook Server to detect if it is a valid nbextension and
    to install the widget

    Returns
    =======
    section: The section of the Jupyter Notebook Server to change.
        Must be 'notebook' for widget extensions
    src: Source directory name to copy files from. Webpack outputs generated files
        into this directory and Jupyter Notebook copies from this directory during
        widget installation
    dest: Destination directory name to install widget files to. Jupyter Notebook copies
        from `src` directory into <jupyter path>/nbextensions/<dest> directory
        during widget installation
    require: Path to importable AMD Javascript module inside the
        <jupyter path>/nbextensions/<dest> directory
    """
    return [
        {
            "section": "notebook",
            "src": "nbextension",
            "dest": "ipytone",
            "require": "ipytone/extension",
        }
    ]
