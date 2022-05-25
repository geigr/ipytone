import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitMap, UnitName } from 'tone/Tone/core/type/Units';

import { assert, normalizeArguments } from './utils';

import { ObservableModel } from './widget_observe';

import {
  AudioNodeModel,
  NativeAudioNodeModel,
  NativeAudioParamModel,
  NodeWithContextModel,
  ToneObjectModel,
} from './widget_base';

import {
  ArrayProperty,
  dataarray_serialization,
  getArrayProp,
} from './serializers';

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
  // so that we could reuse it with Gain
  gain?: UnitMap[T];
}

export class ParamModel<T extends UnitName>
  extends NodeWithContextModel
  implements ObservableModel
{
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

  getValueAtTime(traitName: string, time: tone.Unit.Seconds): UnitMap[T] {
    assert(traitName === 'value', 'param only supports "value" trait');
    return this.node.getValueAtTime(time);
  }

  getValue(traitName: string): UnitMap[T] {
    assert(traitName === 'value', 'param only supports "value" trait');
    return this.node.value;
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

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
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

    this.on('msg:custom', this.handleMsg, this);
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
    const gain_opts = this.gain.properties;
    gain_opts.gain = gain_opts.value;
    return new tone.Gain(gain_opts);
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

export class AudioBufferModel extends ToneObjectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioBufferModel.model_name,
      buffer_url: null,
      array: null,
      _sync_array: false,
      duration: 0,
      length: 0,
      n_channels: 0,
      sample_rate: 0,
      loaded: false,
      reverse: false,
      _create_node: true,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = new tone.ToneAudioBuffer({ reverse: this.get('reverse') });

      if (this.array !== null) {
        this.fromArray(this.array);
      } else if (this.buffer_url !== null) {
        this.fromUrl(this.buffer_url);
      }
    }
  }

  get buffer_url(): null | string {
    return this.get('buffer_url');
  }

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  fromArray(array: Float32Array | Float32Array[]): void {
    this.set('buffer_url', null);
    this.node.fromArray(array);
    this.setBufferProperties();
  }

  fromUrl(url: string): void {
    this.resetBufferProperties();

    this.node.load(url).then(() => {
      this.setBufferProperties();
    });
  }

  setNode(node: tone.ToneAudioBuffer): void {
    this.node = node;
    if (node.loaded) {
      this.setBufferProperties();
    } else {
      node.onload = () => {
        this.setBufferProperties();
      };
    }
  }

  resetBufferProperties(): void {
    this.set('duration', 0);
    this.set('length', 0);
    this.set('n_channels', 0);
    this.set('sample_rate', 0);
    this.set('loaded', false);

    this.array = null;

    this.save_changes();
  }

  setBufferProperties(): void {
    this.set('duration', this.node.duration);
    this.set('length', this.node.length);
    this.set('n_channels', this.node.numberOfChannels);
    this.set('sample_rate', this.node.sampleRate);
    this.set('loaded', this.node.loaded);
    this.set('reverse', this.node.reverse);

    if (this.get('_sync_array') && this.node.duration < 10) {
      this.array = this.node.toArray();
    }

    this.save_changes();
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:array', () => {
      if (this.array !== null) {
        this.fromArray(this.array);
      }
    });
    this.on('change:buffer_url', () => {
      if (this.buffer_url !== null) {
        this.fromUrl(this.buffer_url);
      }
    });
    this.on('change:reverse', () => {
      this.node.reverse = this.get('reverse');
    });
  }

  node: tone.ToneAudioBuffer;

  static serializers: ISerializers = {
    ...ToneObjectModel.serializers,
    array: dataarray_serialization,
  };

  static model_name = 'AudioBufferModel';
}

export class AudioBuffersModel extends ToneObjectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioBuffersModel.model_name,
      _base_url: '',
      _buffers: null,
      _create_node: true,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = new tone.ToneAudioBuffers({
        urls: this.buffer_nodes,
        baseUrl: this.get('_base_url'),
      });
    }
  }

  get buffers(): Map<string, AudioBufferModel> {
    return new Map(Object.entries(this.get('_buffers')));
  }

  get buffer_nodes(): tone.ToneAudioBuffersUrlMap {
    const nodes: tone.ToneAudioBuffersUrlMap = {};

    this.buffers.forEach((buf: AudioBufferModel, key: string) => {
      if (buf.node === undefined) {
        nodes[key] = buf.buffer_url as string;
      } else {
        nodes[key] = buf.node;
      }
    });
    return nodes;
  }

  setNode(node: tone.ToneAudioBuffers): void {
    this.node = node;

    this.buffers.forEach((buf: AudioBufferModel, key: string | number) => {
      let bufferNode: tone.ToneAudioBuffer;

      if (node.has(key)) {
        bufferNode = node.get(key);
      } else {
        // try with key converted to Midi (case of tone.Sampler)
        const keyMidi = new tone.FrequencyClass(tone.context, key).toMidi();
        bufferNode = node.get(keyMidi);
      }

      buf.setNode(bufferNode);
    });
  }

  private updateBufferNodes(): void {
    this.buffers.forEach((buf: AudioBufferModel, key: string) => {
      this.node.add(key, buf.node);
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_buffers', () => {
      this.updateBufferNodes();
    });
  }

  node: tone.ToneAudioBuffers;

  static serializers: ISerializers = {
    ...ToneObjectModel.serializers,
    _buffers: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioBuffersModel';
}
