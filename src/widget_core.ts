import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitMap, UnitName } from 'tone/Tone/core/type/Units';

import {
  AudioNodeModel,
  NativeAudioNodeModel,
  NativeAudioParamModel,
  NodeWithContextModel,
} from './widget_base';

export class InternalAudioNodeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: InternalAudioNodeModel.model_name,
      _n_inputs: 1,
      _n_outputs: 1,
      type: '',
      _create_node: false,
    };
  }

  createNode(): tone.ToneAudioNode {
    throw new Error('Not implemented');
  }

  static model_name = 'InternalAudioNodeModel';
}

interface ParamProperties<T extends UnitName> {
  value: UnitMap[T];
  units: T;
  convert: boolean;
  minValue?: number;
  maxValue?: number;
}

export class ParamModel<T extends UnitName> extends NodeWithContextModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ParamModel.model_name,
      _create_node: true,
      _input: null,
      value: 0,
      convert: true,
      _units: 'number',
      _min_value: undefined,
      _max_value: undefined,
      _swappable: false,
      overridden: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      // TODO: is there any use case of creating a new Tone.Param from Python?
      // Usually a ParamModel wraps an existing Tone.Param object
      this.node = new tone.Param<T>({
        convert: this.convert,
        value: this.value,
        units: this.units,
        minValue: this.normalizeMinMax(this.get('_min_value')),
        maxValue: this.normalizeMinMax(this.get('_max_value')),
      });
      this.input.node = this.node.input;
    }
  }

  get input(): NativeAudioParamModel | NativeAudioNodeModel {
    return this.get('_input');
  }

  get value(): UnitMap[T] {
    return this.get('value');
  }

  set value(val: UnitMap[T]) {
    this.set('value', val);
  }

  get units(): T {
    return this.get('_units');
  }

  get convert(): boolean {
    return this.get('convert');
  }

  get minValue(): number | undefined {
    return this.normalizeMinMax(this.get('_min_value'));
  }

  get maxValue(): number | undefined {
    return this.normalizeMinMax(this.get('_max_value'));
  }

  get properties(): ParamProperties<T> {
    const opts: any = {
      value: this.value,
      units: this.units,
      convert: this.convert,
    };

    if (this.minValue !== undefined) {
      opts.minValue = this.minValue;
    }

    if (this.maxValue !== undefined) {
      opts.maxValue = this.maxValue;
    }

    return opts;
  }

  private normalizeMinMax(value: number | null): number | undefined {
    return value === null ? undefined : value;
  }

  setNode(node: tone.Param<T>): void {
    this.node = node;
    this.input.setNode(node.input as any);
  }

  connectInputCallback(): void {
    this.set('overridden', this.node.overridden);
    // if overridden, value is reset to 0
    this.set('value', this.node.value);
    this.save_changes();
  }

  dispose(): void {
    // Tone.js may have called dispose internally for this Tone instance
    // so we need to check if the instance is already disposed
    if (!this.node.disposed) {
      this.node.dispose();
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });
    this.on('change:convert', () => {
      this.node.convert = this.get('convert');
    });
    this.on('change:_disposed', this.dispose, this);
  }

  static serializers: ISerializers = {
    ...NodeWithContextModel.serializers,
    _input: { deserialize: unpack_models as any },
  };

  node: tone.Param<T>;

  static model_name = 'ParamModel';
}

export class GainModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: GainModel.model_name,
      _gain: undefined,
    };
  }

  createNode(): tone.Gain {
    return new tone.Gain(this.gain.properties);
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.gain.setNode(this.node.gain);
  }

  get gain(): ParamModel<'gain'> {
    return this.get('_gain');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _gain: { deserialize: unpack_models as any },
  };

  node: tone.Gain;

  static model_name = 'GainModel';
}

export class VolumeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: VolumeModel.model_name,
      _volume: undefined,
      mute: false,
    };
  }

  createNode(): tone.Volume {
    return new tone.Volume({ volume: this.volume.value, mute: this.mute });
  }

  get volume(): ParamModel<'decibels'> {
    return this.get('_volume');
  }

  get mute(): boolean {
    return this.get('mute');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:mute', () => {
      this.node.mute = this.mute;
      // update volume param model value
      this.volume.value = this.node.volume.value;
      this.volume.save_changes();
    });
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _volume: { deserialize: unpack_models as any },
  };

  node: tone.Volume;

  static model_name = 'VolumeModel';
}

export class DestinationModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: DestinationModel.model_name,
      _volume: undefined,
      mute: false,
    };
  }

  createNode(): tone.ToneAudioNode {
    return tone.getDestination();
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
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _volume: { deserialize: unpack_models as any },
  };

  node: typeof tone.Destination;

  static model_name = 'DestinationModel';
}
