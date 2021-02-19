import * as tone from 'tone';

// import * as source from 'tone/Tone/source/Source';

import { AudioNodeModel } from './widget_base';

import { SignalModel } from './widget_signal';

abstract class SourceModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SourceModel.model_name,
      mute: false,
      state: 'stopped',
      volume: -16,
    };
  }

  get mute(): boolean {
    return this.get('mute');
  }

  get volume(): number {
    return this.get('volume');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:mute', () => {
      this.node.mute = this.mute;
    });
    this.on('change:state', this.startStopNode, this);
    this.on('change:volume', () => {
      this.node.volume.value = this.volume;
    });
  }

  private startStopNode(): void {
    if (this.get('state') === 'started') {
      this.node.start(0);
    } else {
      this.node.stop(0);
    }
  }

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
      _init_frequency_value: 440,
      _init_detune_value: 0,
      frequency: null,
      detune: null,
    };
  }

  createNode(): tone.Oscillator {
    return new tone.Oscillator({
      type: this.get('type'),
      frequency: this.get('_init_frequency_value'),
      detune: this.get('_init_detune_value'),
    });
  }

  createModels(): Promise<AudioNodeModel>[] {
    return [
      ...super.createModels(),
      this.newModel(SignalModel.model_name, 'frequency', this.node.frequency),
      this.newModel(SignalModel.model_name, 'detune', this.node.detune),
    ];
  }

  get type(): tone.ToneOscillatorType {
    return this.get('type');
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('frequency');
  }

  get detune(): SignalModel<'cents'> {
    return this.get('detune');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.type;
    });
  }

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
