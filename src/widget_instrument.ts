import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

interface InternalNodes {
  [name: string]: AudioNodeModel | ParamModel<any>;
}

// Hack: Tone.js abstract class ``Instrument`` is not exported
// So we have to inherit here from a subclass.
class IpytoneInstrument extends tone.PluckSynth {
  //@ts-ignore
  readonly name: string = 'IpytoneInstrument';

  private _triggerAttackFunc: Function;

  private _triggerReleaseFunc: Function;

  private _internalNodes: InternalNodes;

  constructor(
    volume: tone.Unit.Decibels,
    triggerAttack: string,
    triggerRelease: string,
    internalNodes: InternalNodes
  ) {
    super({ volume: volume });

    this._internalNodes = internalNodes;
    this._triggerAttackFunc = new Function(
      'note',
      'time',
      'velocity',
      triggerAttack
    ).bind(this);
    this._triggerReleaseFunc = new Function('time', triggerRelease).bind(this);

    // Super hacky: dispose PluckSynth internal nodes that we won't use here.
    //@ts-ignore
    this._noise.dispose();
    //@ts-ignore
    this._lfcf.dispose();
  }

  getNode(name: string): tone.ToneAudioNode | tone.Param {
    return this._internalNodes[name].node;
  }

  triggerAttack(
    note: tone.Unit.Frequency,
    time?: tone.Unit.Time,
    velocity?: tone.Unit.NormalRange
  ): this {
    this._triggerAttackFunc(note, time, velocity);
    return this;
  }

  triggerRelease(...args: any[]): this {
    this._triggerReleaseFunc(args);
    return this;
  }
}

export class InstrumentModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: InstrumentModel.model_name,
      _internal_nodes: {},
      _trigger_attack: '',
      _trigger_release: '',
    };
  }

  createNode(): IpytoneInstrument {
    return new IpytoneInstrument(
      -5, // move this to elsewhere when output node is created: this.output.node.volume,
      this.get('_trigger_attack'),
      this.get('_trigger_release'),
      this.get('_internal_nodes')
    );
  }

  replaceNode(): void {
    this.node.dispose();
    this.node = this.createNode();
  }

  get internalNodes(): Map<string, AudioNodeModel | ParamModel<any>> {
    return this.get('_internal_nodes');
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_trigger_attack', () => this.replaceNode());
    this.on('change:_trigger_release', () => this.replaceNode());

    this.on('msg:custom', this.handleMsg, this);
  }

  node: IpytoneInstrument;

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _internal_nodes: { deserialize: unpack_models as any },
  };

  static model_name = 'InstrumentModel';
}
