import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import type { callbackArgs, callbackItem } from './utils';

import { normalizeArguments } from './utils';

import { NodeWithContextModel, ToneObjectModel } from './widget_base';

import { ParamModel } from './widget_core';

import { ObservableModel } from './widget_observe';

import { SignalModel } from './widget_signal';

type transportCallback = { (time: number): void };

export class TransportModel extends ToneObjectModel implements ObservableModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: TransportModel.model_name,
      _bpm: null,
      time_signature: 4,
      loop_start: 0,
      loop_end: '4m',
      loop: false,
      swing: 0,
      swing_subdivision: '8n',
      position: 0,
      seconds: 0,
      progress: 0,
      ticks: 0,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);
    this.py2jsEventID = {};
    this.bpm.setNode(tone.Transport.bpm);
  }

  get bpm(): ParamModel<'bpm'> {
    return this.get('_bpm');
  }

  protected toSeconds(time: tone.Unit.Time): tone.Unit.Seconds {
    return tone.Transport.toSeconds(time);
  }

  protected toFrequency(frequency: tone.Unit.Frequency): tone.Unit.Hertz {
    return tone.Transport.toFrequency(frequency);
  }

  // attach widget models to items
  private async getCallbackItems(items: any): Promise<callbackItem[]> {
    const itemsModel: callbackItem[] = items.map(async (data: any) => {
      const model = await this.widget_manager.get_model(data.callee);
      const item = { ...data };
      item.model = model as NodeWithContextModel;
      return item;
    });

    return Promise.all(itemsModel);
  }

  getValueAtTime(traitName: string, time: tone.Unit.Seconds): tone.Unit.Unit {
    switch (traitName) {
      case 'ticks':
        return tone.Transport.getTicksAtTime(time);
      case 'seconds':
        return tone.Transport.getSecondsAtTime(time);
      default:
        return this.getValue(traitName);
    }
  }

  getValue(traitName: string): tone.Unit.Unit {
    switch (traitName) {
      case 'ticks':
        return tone.Transport.ticks;
      case 'seconds':
        return tone.Transport.seconds;
      case 'progress':
        return tone.Transport.progress;
      case 'position':
        return tone.Transport.position;
      case 'state':
        return tone.Transport.state;
      default:
        throw new Error('unsupported trait name ' + traitName);
    }
  }

  private getToneCallback(items: callbackItem[]): transportCallback {
    const callback = (time: number) => {
      items.forEach((item) => {
        const args: callbackArgs = {};

        for (const [k, v] of Object.entries(item.args)) {
          if (v.eval) {
            args[k] = { value: eval(v.value), eval: true };
          } else {
            args[k] = { value: v.value, eval: false };
          }
        }

        const argsArray = normalizeArguments(args, item.arg_keys);
        item.model.node[item.method](...argsArray);
      });
    };

    return callback;
  }

  private async schedule(command: any): Promise<void> {
    const items = await this.getCallbackItems(command.items);
    const callback = this.getToneCallback(items);

    let event_id = 0;

    if (command.op === '') {
      event_id = tone.Transport.schedule(callback, command.time);
    } else if (command.op === 'repeat') {
      const duration = command.duration ? command.duration : Infinity;
      event_id = tone.Transport.scheduleRepeat(
        callback,
        command.interval,
        command.start_time,
        duration
      );
    } else if (command.op === 'once') {
      event_id = tone.Transport.scheduleOnce(callback, command.time);
    }

    this.py2jsEventID[command.id] = event_id;
  }

  private syncPosition(): void {
    this.set('position', tone.Transport.position, { silent: true });
    this.set('seconds', tone.Transport.seconds, { silent: true });
    this.set('progress', tone.Transport.progress, { silent: true });
    this.set('ticks', tone.Transport.ticks, { silent: true });
    this.save_changes();
  }

  private play(command: any): void {
    const argsArray = normalizeArguments(command.args, command.arg_keys);
    (tone.Transport as any)[command.method](...argsArray);
    this.syncPosition();
  }

  private clearEvent(pyEventID: number): void {
    tone.Transport.clear(this.py2jsEventID[pyEventID]);
    delete this.py2jsEventID[pyEventID];
  }

  private async syncSignal(command: any): Promise<void> {
    const signalModel = (await this.widget_manager.get_model(
      command.signal
    )) as SignalModel<any>;

    if (command.op === 'sync') {
      tone.Transport.syncSignal(signalModel.node, command.ratio);
      signalModel.set('value', 0, { silent: true });
      signalModel.save_changes();
    } else if (command.op === 'unsync') {
      tone.Transport.unsyncSignal(signalModel.node);
    }
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'schedule') {
      this.schedule(command);
    } else if (command.event === 'play') {
      this.play(command);
    } else if (command.event === 'clear') {
      this.clearEvent(command.id);
    } else if (command.event === 'cancel') {
      tone.Transport.cancel(command.after);
    } else if (command.event === 'sync_signal') {
      this.syncSignal(command);
    }
  }

  initEventListeners(): void {
    this.on('change:time_signature', () => {
      tone.Transport.timeSignature = this.get('time_signature');
    });
    this.on('change:loop_start', () => {
      tone.Transport.loopStart = this.get('loop_start');
    });
    this.on('change:loop_end', () => {
      tone.Transport.loopEnd = this.get('loop_end');
    });
    this.on('change:loop', () => {
      tone.Transport.loop = this.get('loop');
    });
    this.on('change:swing', () => {
      tone.Transport.swing = this.get('swing');
    });
    this.on('change:swing_subdivision', () => {
      tone.Transport.swingSubdivision = this.get('swing_subdivision');
    });
    this.on('change:position', () => {
      tone.Transport.position = this.get('position');
      this.syncPosition();
    });
    this.on('change:seconds', () => {
      tone.Transport.seconds = this.get('seconds');
      this.syncPosition();
    });
    this.on('change:ticks', () => {
      tone.Transport.position = this.get('ticks');
      this.syncPosition();
    });
    this.on('msg:custom', this.handleMsg, this);
  }

  static serializers: ISerializers = {
    ...ToneObjectModel.serializers,
    _bpm: { deserialize: unpack_models as any },
  };

  py2jsEventID: { [id: number]: number };

  static model_name = 'TransportModel';
}
