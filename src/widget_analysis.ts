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
      this.node.size = this.get('size')
    });
    this.on('change:smoothing', () => {
      this.node.smoothing = this.get('smoothing');
    });
  }

  node: tone.Analyser;

  static model_name = 'AnalyserModel';
}
