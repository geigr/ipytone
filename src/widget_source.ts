import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { AudioBufferModel, AudioBuffersModel, ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

import {
  ArrayProperty,
  dataarray_serialization,
  getArrayProp,
} from './serializers';

interface SourceInterface extends tone.ToneAudioNode {
  mute: boolean;
  volume: tone.Param<'decibels'>;
}

abstract class SourceModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SourceModel.model_name,
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
    this.on('msg:custom', this.handleMsg, this);
  }

  private handleMsg(command: any, buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _volume: { deserialize: unpack_models as any },
  };

  node: SourceInterface;

  static model_name = 'SourceModel';
}

interface BaseOscillatorInterface extends SourceInterface {
  frequency: tone.Signal<'frequency'>;
  detune: tone.Signal<'cents'>;
  type: string;
  partials: number[];
  phase: number;
  asArray(length: number): Promise<Float32Array>;
}

abstract class BaseOscillatorModel extends SourceModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: BaseOscillatorModel.model_name,
      type: 'sine',
      _partials: [],
      _frequency: null,
      _detune: null,
      phase: 0,
      array: null,
      array_length: 1024,
      sync_array: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.maybeSetArray();
    }
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get detune(): SignalModel<'cents'> {
    return this.get('_detune');
  }

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  setSubNodes(): void {
    this.frequency.setNode(this.node.frequency);
    this.detune.setNode(this.node.detune);
  }

  maybeSetArray(): void {
    if (this.get('sync_array')) {
      this.node.asArray(this.get('array_length')).then((arr: Float32Array) => {
        this.array = arr;
        this.save_changes();
      });
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      // prevent calling twice (partials changed -> type = custom)
      if (this.node.type !== this.get('type')) {
        this.node.type = this.get('type');
        this.maybeSetArray();
      }
    });
    this.on('change:_partials', () => {
      this.node.partials = this.get('_partials');
      this.maybeSetArray();
    });
    this.on('change:phase', () => {
      this.node.phase = this.get('phase');
      this.maybeSetArray();
    });
  }

  static serializers: ISerializers = {
    ...SourceModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
    array: dataarray_serialization,
  };

  node: BaseOscillatorInterface;

  static model_name = 'BaseOscillatorModel';
}

export class OscillatorModel extends BaseOscillatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: OscillatorModel.model_name,
    };
  }

  createNode(): tone.Oscillator {
    return new tone.Oscillator({
      type: this.get('type'),
      frequency: this.get('_frequency').get('value'),
      detune: this.get('_detune').get('value'),
      volume: this.get('volume'),
      phase: this.get('phase'),
      partials: this.get('_partials'),
    });
  }

  node: tone.Oscillator;

  static model_name = 'OscillatorModel';
}

export class PulseOscillatorModel extends BaseOscillatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PulseOscillatorModel.model_name,
      _width: null,
    };
  }

  get width(): SignalModel<'audioRange'> {
    return this.get('_width');
  }

  createNode(): tone.PulseOscillator {
    return new tone.PulseOscillator({
      type: this.get('type'),
      frequency: this.get('_frequency').get('value'),
      detune: this.get('_detune').get('value'),
      width: this.get('_width').get('value'),
      volume: this.get('volume'),
      phase: this.get('phase'),
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.width.setNode(this.node.width);
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.width.on('change:value', () => {
      this.maybeSetArray();
    });
  }

  static serializers: ISerializers = {
    ...BaseOscillatorModel.serializers,
    _width: { deserialize: unpack_models as any },
  };

  node: tone.PulseOscillator;

  static model_name = 'PulseOscillatorModel';
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

export class PlayerModel extends SourceModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PlayerModel.model_name,
      buffer: null,
      autostart: false,
      loop: false,
      loop_start: 0,
      loop_end: 0,
      fade_in: 0,
      fade_out: 0,
      reverse: false,
      playback_rate: 1,
    };
  }

  createNode(): tone.Player {
    return new tone.Player({
      url: this.buffer.node,
      autostart: this.get('autostart'),
      loop: this.get('loop'),
      loopEnd: this.get('loop_end'),
      loopStart: this.get('loop_start'),
      fadeIn: this.get('fade_in'),
      fadeOut: this.get('fade_out'),
      reverse: this.get('reverse'),
      playbackRate: this.get('playback_rate'),
      volume: this.get('volume'),
    });
  }

  get buffer(): AudioBufferModel {
    return this.get('buffer');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:buffer', () => {
      this.node.buffer = this.buffer.node;
    });
    this.on('change:loop', () => {
      this.node.loop = this.get('loop');
    });
    this.on('change:loop_end', () => {
      this.node.loopEnd = this.get('loop_end');
    });
    this.on('change:loop_start', () => {
      this.node.loopStart = this.get('loop_start');
    });
    this.on('change:fade_in', () => {
      this.node.fadeIn = this.get('fade_in');
    });
    this.on('change:fade_out', () => {
      this.node.fadeOut = this.get('fade_out');
    });
    this.on('change:playback_rate', () => {
      this.node.playbackRate = this.get('playback_rate');
    });
    this.on('change:reverse', () => {
      this.node.reverse = this.get('reverse');
      this.buffer.set('reverse', this.buffer.node.reverse, { silent: true });
      this.buffer.save_changes();
    });
  }

  node: tone.Player;

  static serializers: ISerializers = {
    ...SourceModel.serializers,
    buffer: { deserialize: unpack_models as any },
  };

  static model_name = 'PlayerModel';
}

export class PlayersModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PlayersModel.model_name,
      _buffers: null,
      _volume: undefined,
      mute: false,
    };
  }

  createNode(): tone.Players {
    const players = new tone.Players({
      urls: this.buffers.buffer_nodes,
      fadeIn: this.get('fade_in'),
      fadeOut: this.get('fade_out'),
      volume: this.get('volume'),
      mute: this.mute,
    });

    // Hack: allows reusing AudioBuffers widget from the Python side
    this.buffers.setNode((players as any)._buffers);

    return players;
  }

  get mute(): boolean {
    return this.get('mute');
  }

  get volume(): ParamModel<'decibels'> {
    return this.get('_volume');
  }

  get buffers(): AudioBuffersModel {
    return this.get('_buffers');
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

  node: tone.Players;

  static serializers: ISerializers = {
    ...SourceModel.serializers,
    _buffers: { deserialize: unpack_models as any },
  };

  static model_name = 'PlayersModel';
}
