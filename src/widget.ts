// Copyright (c) Benoit Bovy
// Distributed under the terms of the Modified BSD License.

import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitName } from 'tone/Tone/core/type/Units';

// import * as source from 'tone/Tone/source/Source';

import { MODULE_NAME, MODULE_VERSION } from './version';

abstract class ToneWidgetModel extends WidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_module: ToneWidgetModel.model_module,
      _model_module_version: ToneWidgetModel.model_module_version,
    };
  }

  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}

abstract class AudioNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      name: '',
      _in_nodes: [],
      _out_nodes: [],
    };
  }

  initialize(attributes: Backbone.ObjectHash, options: any): void {
    super.initialize(attributes, options);

    this.node = this.createNode();

    this.initEventListeners();
  }

  initEventListeners(): void {
    this.on('change:_out_nodes', this.updateConnections, this);
  }

  private getToneAudioNodes(models: AudioNodeModel[]): tone.ToneAudioNode[] {
    return models.map((model: AudioNodeModel) => {
      return model.node;
    });
  }

  private updateConnections(): void {
    // connect new nodes (if any)
    const nodesAdded = this.get('_out_nodes').filter(
      (other: AudioNodeModel) => {
        return !this.previous('_out_nodes').includes(other);
      }
    );

    this.node.fan(...this.getToneAudioNodes(nodesAdded));

    // disconnect nodes that have been removed (if any)
    const nodesRemoved = this.previous('_out_nodes').filter(
      (other: AudioNodeModel) => {
        return !this.get('_out_nodes').includes(other);
      }
    );

    this.getToneAudioNodes(nodesRemoved).forEach((node) => {
      this.node.disconnect(node);
    });
  }

  node: tone.ToneAudioNode;

  abstract createNode(): tone.ToneAudioNode;

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _in_nodes: { deserialize: unpack_models as any },
    _out_nodes: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}

export class SignalModel<T extends UnitName> extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SignalModel.model_name,
      value: null,
      _units: 'number',
      _min_value: undefined,
      _max_value: undefined,
    };
  }

  createNode(): tone.Signal {
    return new tone.Signal({
      value: this.get('value'),
      units: this.get('_units'),
      minValue: this.normalizeMinMax(this.get('_min_value')),
      maxValue: this.normalizeMinMax(this.get('_max_value')),
    });
  }

  private normalizeMinMax(value: number | null): number | undefined {
    return value === null ? undefined : value;
  }

  get value(): any {
    return this.node.value;
  }

  get minValue(): number {
    return this.node.minValue;
  }

  get maxValue(): number {
    return this.node.maxValue;
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });
  }

  node: tone.Signal<T>;

  static model_name = 'SignalModel';
}

export class MultiplyModel extends SignalModel<'number'> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MultiplyModel.model_name,
      _factor: undefined,
    };
  }

  createNode(): tone.Multiply {
    const mult = new tone.Multiply();
    this.factor.node.connect(mult.factor);
    return mult;
  }

  get factor(): SignalModel<'number'> {
    return this.get('_factor');
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _factor: { deserialize: unpack_models as any },
  };

  node: tone.Multiply;

  static model_name = 'MultiplyModel';
}

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

export class DestinationModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: DestinationModel.model_name,
      mute: false,
      volume: -16,
    };
  }

  createNode(): tone.ToneAudioNode {
    return tone.getDestination();
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
    this.on('change:volume', () => {
      this.node.volume.value = this.volume;
    });
  }

  node: typeof tone.Destination;

  static model_name = 'DestinationModel';
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
    const osc = new tone.Oscillator({
      type: this.get('type'),
      volume: this.get('volume'),
    });

    // need to bind signals explicitly
    this.frequency.node.connect(osc.frequency);
    this.detune.node.connect(osc.detune);

    return osc;
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
