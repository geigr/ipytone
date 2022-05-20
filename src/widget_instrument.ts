import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { ParamModel, VolumeModel } from './widget_core';

interface InternalNodes {
  [name: string]: tone.ToneAudioNode | tone.Param;
}

interface IpytoneInstrumentOptions {
  volume: tone.Unit.Decibels;
  triggerAttack: string;
  triggerRelease: string;
  internalNodes: InternalNodes;
  context?: tone.Context;
}

// Hack: Tone.js abstract class ``Instrument`` is not exported
// So we have to inherit here from a subclass.
class IpytoneInstrument extends tone.PluckSynth {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  //@ts-ignore
  readonly name: string = 'IpytoneInstrument';

  private _triggerAttackFunc: (
    note: tone.Unit.Frequency,
    time?: tone.Unit.Seconds,
    velocity?: tone.Unit.NormalRange
  ) => void;

  private _triggerReleaseFunc: (...args: any[]) => void;

  private _internalNodes: InternalNodes;

  constructor(options: IpytoneInstrumentOptions) {
    super({ volume: options.volume });

    this._internalNodes = options.internalNodes;

    this._triggerAttackFunc = new Function(
      'note',
      'time',
      'velocity',
      options.triggerAttack
    ).bind(this);
    this._triggerReleaseFunc = new Function(
      'time',
      options.triggerRelease
    ).bind(this);

    // Super hacky: dispose PluckSynth internal nodes that we won't use here.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this._noise.dispose();
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this._lfcf.dispose();
  }

  getNode(name: string): tone.ToneAudioNode | tone.Param {
    return this._internalNodes[name];
  }

  triggerAttack(
    note: tone.Unit.Frequency,
    time?: tone.Unit.Seconds,
    velocity?: tone.Unit.NormalRange
  ): this {
    this._triggerAttackFunc(note, time, velocity);
    return this;
  }

  triggerRelease(...args: any[]): this {
    this._triggerReleaseFunc(...args);
    return this;
  }
}

interface IpytoneMonophonicOptions extends IpytoneInstrumentOptions {
  setNote: string;
  getLevelAtTime: string;
  frequency: tone.Signal<'frequency'>;
  detune: tone.Signal<'cents'>;
  portamento: number;
  onsilence?: (instrument: tone.Synth) => void;
}

// Hack: Tone.js abstract class ``Monophonic`` is not exported
// So we have to inherit here from a subclass.
class IpytoneMonophonic extends tone.Synth {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  //@ts-ignore
  readonly name: string = 'IpytoneMonophonic';

  readonly frequency: tone.Signal<'frequency'>;

  readonly detune: tone.Signal<'cents'>;

  private _triggerAttackFunc: (
    time: tone.Unit.Seconds,
    velocity: tone.Unit.NormalRange
  ) => void;

  private _triggerReleaseFunc: (time: tone.Unit.Seconds) => void;

  private _setNoteFunc: (
    note: tone.Unit.Frequency,
    time?: tone.Unit.Time
  ) => void;

  private _getLevelAtTimeFunc: (time: tone.Unit.Time) => tone.Unit.NormalRange;

  private _internalNodes: InternalNodes;

  constructor(options: IpytoneMonophonicOptions) {
    super({ volume: options.volume, portamento: options.portamento });

    this._internalNodes = options.internalNodes;

    this._triggerAttackFunc = new Function(
      'time',
      'velocity',
      options.triggerAttack
    ).bind(this);

    this._triggerReleaseFunc = new Function(
      'time',
      options.triggerRelease
    ).bind(this);

    if (options.setNote !== '') {
      this._setNoteFunc = new Function('note', 'time', options.setNote).bind(
        this
      );
    } else {
      this._setNoteFunc = (
        note: tone.Unit.Frequency,
        time?: tone.Unit.Time
      ) => {
        super.setNote(note, time);
      };
    }

    this._getLevelAtTimeFunc = new Function(
      'time',
      options.getLevelAtTime
    ).bind(this);

    Object.defineProperty(this, 'frequency', {
      writable: true,
    });
    Object.defineProperty(this, 'detune', {
      writable: true,
    });
    this.frequency = options.frequency;
    this.detune = options.detune;
    Object.defineProperty(this, 'frequency', {
      writable: false,
    });
    Object.defineProperty(this, 'detune', {
      writable: false,
    });

    // Super hacky: dispose Synth internal nodes that we won't use here.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this.oscillator.dispose();
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this.envelope.dispose();
  }

  getNode(name: string): tone.ToneAudioNode | tone.Param {
    return this._internalNodes[name];
  }

  _triggerEnvelopeAttack(
    time: tone.Unit.Seconds,
    velocity: tone.Unit.NormalRange
  ): this {
    this._triggerAttackFunc(time, velocity);
    return this;
  }

  _triggerEnvelopeRelease(time: tone.Unit.Seconds): this {
    this._triggerReleaseFunc(time);
    return this;
  }

  setNote(note: tone.Unit.Frequency, time?: tone.Unit.Time): this {
    this._setNoteFunc(note, time);
    return this;
  }

  getLevelAtTime(time: tone.Unit.Time): tone.Unit.NormalRange {
    return this._getLevelAtTimeFunc(time);
  }
}

abstract class BaseInstrumentModel<
  T extends IpytoneInstrument | IpytoneMonophonic
> extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _internal_nodes: {},
      _trigger_attack: '',
      _trigger_release: '',
    };
  }

  get volume(): ParamModel<'decibels'> {
    return (this.output as VolumeModel).volume;
  }

  abstract createNode(): T;

  replaceNode(): void {
    //FIXME: the new node doesn't seem connected properly (no sound)
    //this.node.dispose();
    this.node = this.createNode();
  }

  get internalNodes(): InternalNodes {
    const models: { [name: string]: AudioNodeModel | ParamModel<any> } =
      this.get('_internal_nodes');
    const nodes: InternalNodes = {};

    Object.entries(models).forEach(([key, model]) => {
      nodes[key] = model.node;
    });

    return nodes;
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_internal_nodes', () => this.replaceNode());
    this.on('change:_trigger_attack', () => this.replaceNode());
    this.on('change:_trigger_release', () => this.replaceNode());

    this.on('msg:custom', this.handleMsg, this);
  }

  node: T;

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _internal_nodes: { deserialize: unpack_models as any },
  };
}

export class InstrumentModel extends BaseInstrumentModel<IpytoneInstrument> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: InstrumentModel.model_name,
    };
  }

  createNode(): IpytoneInstrument {
    return new IpytoneInstrument({
      volume: this.volume.value,
      triggerAttack: this.get('_trigger_attack'),
      triggerRelease: this.get('_trigger_release'),
      internalNodes: this.internalNodes,
    });
  }

  static model_name = 'InstrumentModel';
}

export class MonophonicModel extends BaseInstrumentModel<IpytoneMonophonic> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MonophonicModel.model_name,
      _set_note: '',
      _get_level_at_time: '',
      _frequency: null,
      _detune: null,
      portamento: 0,
    };
  }

  createNode(): IpytoneMonophonic {
    return new IpytoneMonophonic(this.getOptions());
  }

  getOptions(): IpytoneMonophonicOptions {
    return {
      volume: this.volume.value,
      triggerAttack: this.get('_trigger_attack'),
      triggerRelease: this.get('_trigger_release'),
      setNote: this.get('_set_note'),
      getLevelAtTime: this.get('_get_level_at_time'),
      internalNodes: this.internalNodes,
      frequency: this.get('_frequency').node,
      detune: this.get('_detune').node,
      portamento: this.get('portamento'),
    };
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_set_note', () => this.replaceNode());
    this.on('change:_get_level_at_time', () => this.replaceNode());
    this.on('change:portamento', () => {
      this.node.portamento = this.get('portamento');
    });
  }

  static serializers: ISerializers = {
    ...BaseInstrumentModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
  };

  static model_name = 'MonophonicModel';
}

export class PolySynthModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PolySynthModel.model_name,
      _dummy_voice: null,
    };
  }

  get dummyVoice(): MonophonicModel {
    return this.get('_dummy_voice');
  }

  createNode(): tone.PolySynth {
    const options = this.dummyVoice.getOptions();
    return new tone.PolySynth({
      voice: IpytoneMonophonic,
      options: options as any,
    });
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      console.log(this.node);
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('msg:custom', this.handleMsg, this);
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _dummy_voice: { deserialize: unpack_models as any },
  };

  node: tone.PolySynth;

  static model_name = 'PolySynthModel';
}
