import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { ParamModel, VolumeModel } from './widget_core';
import { Signal } from 'tone';

interface InternalNodeModels {
  [name: string]: AudioNodeModel;
}

interface InternalNodes {
  [name: string]: tone.ToneAudioNode;
}

/*
 *  Get instrument's internal Tone.js nodes from their corresponding widget
 *  models.
 *
 *  If createNodes is true, it will create new Tone.js node instances from the
 *  corresponding models. This is used by PolySynthModel so that Tone.js PolySynth can
 *  create new instruments only in the front-end.
 */
function getInternalNodes(
  models: InternalNodeModels,
  createNodes?: boolean
): InternalNodes {
  const nodes: InternalNodes = {};

  Object.entries(models).forEach(([key, model]) => {
    if (createNodes) {
      nodes[key] = model.createNode();
    } else {
      nodes[key] = model.node;
    }
  });

  return nodes;
}

interface IpytoneInstrumentOptions {
  volume: tone.Unit.Decibels;
  triggerAttack: string;
  triggerRelease: string;
  afterInit: string;
  internalNodeModels: InternalNodeModels;
  createInternalNodes?: boolean;
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

    this._internalNodes = getInternalNodes(
      options.internalNodeModels,
      options.createInternalNodes
    );

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

    const afterInit = new Function(options.afterInit).bind(this);
    afterInit();

    // Super hacky: dispose PluckSynth internal nodes that we won't use here.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this._noise.dispose();
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this._lfcf.dispose();
  }

  dispose(): this {
    super.dispose();

    Object.values(this._internalNodes).forEach((node) => {
      node.dispose();
    });

    return this;
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

    this._internalNodes = getInternalNodes(
      options.internalNodeModels,
      options.createInternalNodes
    );

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

    // Hack for re-setting readonly frequency and detune attributes
    // on a Tone.js Synth subclass
    Object.defineProperty(this, 'frequency', {
      writable: true,
    });
    Object.defineProperty(this, 'detune', {
      writable: true,
    });
    if ('frequency' in this._internalNodes) {
      this.frequency = this.getNode('frequency') as Signal<'frequency'>;
    } else {
      this.frequency = (
        this.getNode('oscillator') as tone.Oscillator
      ).frequency;
    }
    if ('detune' in this._internalNodes) {
      this.detune = this.getNode('detune') as Signal<'cents'>;
    } else {
      this.detune = (this.getNode('oscillator') as tone.Oscillator).detune;
    }
    Object.defineProperty(this, 'frequency', {
      writable: false,
    });
    Object.defineProperty(this, 'detune', {
      writable: false,
    });

    const afterInit = new Function(options.afterInit).bind(this);
    afterInit();

    // Super hacky: dispose Synth internal nodes that we won't use here.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this.oscillator.dispose();
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-ignore
    this.envelope.dispose();
  }

  dispose(): this {
    super.dispose();

    Object.values(this._internalNodes).forEach((node) => {
      node.dispose();
    });

    return this;
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
      _after_init: '',
      _trigger_attack: '',
      _trigger_release: '',
    };
  }

  get volume(): ParamModel<'decibels'> {
    return (this.output as VolumeModel).volume;
  }

  abstract createNode(): T;

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

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
      afterInit: this.get('_after_init'),
      internalNodeModels: this.get('_internal_nodes'),
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
      afterInit: this.get('_after_init'),
      setNote: this.get('_set_note'),
      getLevelAtTime: this.get('_get_level_at_time'),
      internalNodeModels: this.get('_internal_nodes'),
      portamento: this.get('portamento'),
    };
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:portamento', () => {
      this.node.portamento = this.get('portamento');
    });
  }

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
    options.createInternalNodes = true;

    return new tone.PolySynth({
      voice: IpytoneMonophonic,
      options: options as any,
    });
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
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