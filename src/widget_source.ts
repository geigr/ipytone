import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

// import * as source from 'tone/Tone/source/Source';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

abstract class SourceModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SourceModel.model_name,
      state: 'stopped',
      _volume: undefined,
      mute: false,
    };
  }

  get mute(): boolean {
    return this.get('mute');
  }

  get volume(): ParamModel<'decibels'> {
    return this.get('_volume');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:mute', () => {
      this.node.mute = this.mute;
      // update volume param model value
      this.volume.value = this.node.volume.value;
      this.volume.save_changes();
    });
    this.on('change:state', this.startStopNode, this);
  }

  private startStopNode(): void {
    if (this.get('state') === 'started') {
      this.node.start(0);
    } else {
      this.node.stop(0);
    }
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _volume: { deserialize: unpack_models as any },
  };

  // FIXME: typescript error: property not assignable to the same property in base type
  // node: source.Source<source.SourceOptions>;
  node: any;

  static model_name = 'SourceModel';
}
export class OscillatorModel extends SourceModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: OscillatorModel.model_name,
      type: 'sine',
      _frequency: null,
      _detune: null,
    };
  }

  createNode(): tone.Oscillator {
    return new tone.Oscillator({
      type: this.get('type'),
      frequency: this.get('_frequency').get('value'),
      detune: this.get('_detune').get('value'),
      volume: this.get('volume'),
    });
  }

  setSubNodes(): void {
    this.frequency.setNode(this.node.frequency);
    this.detune.setNode(this.node.detune);
  }

  get type(): tone.ToneOscillatorType {
    return this.get('type');
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get detune(): SignalModel<'cents'> {
    return this.get('_detune');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.type;
    });
  }

  static serializers: ISerializers = {
    ...SourceModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
  };

  node: tone.Oscillator;

  static model_name = 'OscillatorModel';
}

export class NoiseModel extends SourceModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NoiseModel.model_name,
      type: 'white',
      fade_in: 0,
      fade_out: 0,
    };
  }

  createNode(): tone.Noise {
    return new tone.Noise({
      type: this.get('type'),
      volume: this.get('volume'),
      fadeIn: this.get('fade_in'),
      fadeOut: this.get('fade_out'),
    });
  }

  get type(): tone.NoiseType {
    return this.get('type');
  }

  get fadeIn(): number {
    return this.get('fade_in');
  }

  get fadeOut(): number {
    return this.get('fade_out');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.type;
    });
    this.on('change:fade_in', () => {
      this.node.fadeIn = this.fadeIn;
    });
    this.on('change:fade_out', () => {
      this.node.fadeOut = this.fadeOut;
    });
  }

  node: tone.Noise;

  static model_name = 'NoiseModel';
}
