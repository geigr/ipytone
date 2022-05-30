import * as tone from 'tone';

import { assert } from './utils';

import { AudioNodeModel } from './widget_base';

import { ObservableModel } from './widget_observe';

export class AnalyserModel extends AudioNodeModel implements ObservableModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AnalyserModel.model_name,
      _channels: 1,
      type: 'fft',
      size: 1024,
      smoothing: 0.8,
    };
  }

  createNode(): tone.Analyser {
    return new tone.Analyser({
      channels: this.get('_channels'),
      type: this.get('type'),
      size: this.get('size'),
      smoothing: this.get('smoothing'),
    });
  }

  getValueAtTime(
    traitName: string,
    _time: tone.Unit.Seconds
  ): Float32Array | Float32Array[] {
    return this.getValue(traitName);
  }

  getValue(traitName: string): Float32Array | Float32Array[] {
    assert(traitName === 'array', 'envelope only supports "array" trait');
    return this.node.getValue();
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.get('type');
    });
    this.on('change:size', () => {
      this.node.size = this.get('size');
    });
    this.on('change:smoothing', () => {
      this.node.smoothing = this.get('smoothing');
    });
  }

  node: tone.Analyser;

  static model_name = 'AnalyserModel';
}

abstract class BaseMeterModel
  extends AudioNodeModel
  implements ObservableModel
{
  getValueAtTime(
    traitName: string,
    _time: tone.Unit.Seconds
  ): Float32Array | Float32Array[] | number | number[] {
    return this.getValue(traitName);
  }

  getValue(
    traitName: string
  ): Float32Array | Float32Array[] | number | number[] {
    assert(
      traitName === 'value' || traitName === 'array',
      'Meters only supports "value" or "array" trait'
    );
    let value = this.node.getValue();

    // Issue with -Infinity (inactive signal in dB) converted to None in Python
    // https://github.com/jupyter-widgets/ipywidgets/issues/3321
    // https://github.com/jupyter-widgets/ipywidgets/issues/1531
    if (value === -Infinity) {
      value = -1e20;
    } else if (Array.isArray(value) && value.length == 2) {
      value[0] = value[0] === -Infinity ? -1e20 : value[0];
      value[1] = value[1] === -Infinity ? -1e20 : value[1];
    }

    return value;
  }

  node: tone.Meter | tone.DCMeter | tone.Waveform | tone.FFT;
}

export class MeterModel extends BaseMeterModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MeterModel.model_name,
      _channels: 1,
      normal_range: false,
      smoothing: 0.8,
    };
  }

  createNode(): tone.Meter {
    return new tone.Meter({
      channels: this.get('_channels'),
      normalRange: this.get('normal_range'),
      smoothing: this.get('smoothing'),
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:normal_range', () => {
      this.node.normalRange = this.get('normal_range');
    });
    this.on('change:smoothing', () => {
      this.node.smoothing = this.get('smoothing');
    });
  }

  node: tone.Meter;

  static model_name = 'MeterModel';
}

export class DCMeterModel extends BaseMeterModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: DCMeterModel.model_name,
    };
  }

  createNode(): tone.DCMeter {
    return new tone.DCMeter();
  }

  node: tone.DCMeter;

  static model_name = 'DCMeterModel';
}

export class WaveformModel extends BaseMeterModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: WaveformModel.model_name,
      size: 1024,
    };
  }

  createNode(): tone.Waveform {
    return new tone.Waveform({
      size: this.get('size'),
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:size', () => {
      this.node.size = this.get('size');
    });
  }

  node: tone.Waveform;

  static model_name = 'WaveformModel';
}

export class FFTModel extends BaseMeterModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: FFTModel.model_name,
      size: 1024,
      normal_range: false,
      smoothing: 0.8,
    };
  }

  createNode(): tone.FFT {
    return new tone.FFT({
      size: this.get('size'),
      normalRange: this.get('normal_range'),
      smoothing: this.get('smoothing'),
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:size', () => {
      this.node.size = this.get('size');
    });
    this.on('change:normal_range', () => {
      this.node.normalRange = this.get('normal_range');
    });
    this.on('change:smoothing', () => {
      this.node.smoothing = this.get('smoothing');
    });
  }

  node: tone.FFT;

  static model_name = 'FFTModel';
}
