import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

// import * as source from 'tone/Tone/source/Source';

import { AudioNodeModel } from './widget_base';

import { AudioBufferModel, AudioBuffersModel, ParamModel } from './widget_core';

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
