import * as tone from 'tone';

import type { callbackArgs, callbackItem } from './utils';

import { normalizeArguments } from './utils';

import { NodeWithContextModel } from './widget_base';
import { ObservableModel } from './widget_observe';

type eventCallback = { (time: number, value: any): void };

// Interface common to all Tone.js Events
// This is needed as Loop and Pattern don't inherit from ToneEvent
interface Event {
  callback: tone.ToneEventCallback<any>;
  humanize: boolean | tone.Unit.Time;
  mute: boolean;
  probability: tone.Unit.NormalRange;
  playbackRate: tone.Unit.Positive;
  cancel: (time?: tone.Unit.TransportTime) => void;
  dispose: () => void;
  toSeconds: (time: tone.Unit.Time) => tone.Unit.Seconds;
  toFrequency: (frequency: tone.Unit.Frequency) => tone.Unit.Hertz;
}

abstract class BaseEventModel<T extends Event>
  extends NodeWithContextModel
  implements ObservableModel
{
  defaults(): any {
    return {
      ...super.defaults(),
      value: null,
      humanize: false,
      probability: 1,
      mute: false,
      start_offset: 0,
      playback_rate: 1,
      loop_start: 0,
      loop_end: '1m',
      loop: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    this.event = this.createEvent();
  }

  protected abstract createEvent(): T;

  protected toSeconds(time: tone.Unit.Time): tone.Unit.Seconds {
    return this.event.toSeconds(time);
  }

  protected toFrequency(frequency: tone.Unit.Frequency): tone.Unit.Hertz {
    return this.event.toFrequency(frequency);
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

  private getToneCallback(items: callbackItem[]): eventCallback {
    const callback = (time: number, value?: any) => {
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

  private async setCallback(command: any): Promise<void> {
    const items = await this.getCallbackItems(command.items);
    this.event.callback = this.getToneCallback(items);
  }

  getValueAtTime(
    traitName: string,
    _time: tone.Unit.Seconds
  ): tone.BasicPlaybackState | tone.Unit.NormalRange {
    return this.getValue(traitName);
  }

  getValue(traitName: string): tone.BasicPlaybackState | tone.Unit.NormalRange {
    if (traitName === 'state') {
      return (this.event as unknown as tone.ToneEvent).state;
    } else if (traitName === 'progress') {
      return (this.event as unknown as tone.ToneEvent).progress;
    } else {
      throw new Error('unsupported trait name ' + traitName);
    }
  }

  private play(command: any): void {
    const argsArray = normalizeArguments(command.args, command.arg_keys);
    (this.event as any)[command.method](...argsArray);
  }

  protected handleMsg(command: any, _buffers: any): void {
    if (command.event === 'set_callback') {
      this.setCallback(command);
    } else if (command.event === 'play') {
      this.play(command);
    } else if (command.event === 'cancel') {
      this.event.cancel(command.time);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:humanize', () => {
      this.event.humanize = this.get('humanize');
    });
    this.on('change:probability', () => {
      this.event.probability = this.get('probability');
    });
    this.on('change:mute', () => {
      this.event.mute = this.get('mute');
    });
    this.on('change:playback_rate', () => {
      this.event.playbackRate = this.get('playback_rate');
    });
    this.on('msg:custom', this.handleMsg, this);
  }

  dispose(): void {
    this.event.dispose();
  }

  event: T;
}

export class EventModel extends BaseEventModel<tone.ToneEvent> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: EventModel.model_name,
      value: null,
      loop_start: 0,
      loop_end: '1m',
      loop: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    this.event = this.createEvent();
  }

  protected createEvent(): tone.ToneEvent {
    return new tone.ToneEvent({
      value: this.get('value'),
      humanize: this.get('humanize'),
      probability: this.get('probability'),
      mute: this.get('mute'),
      playbackRate: this.get('playback_rate'),
      loopStart: this.get('loop_start'),
      loopEnd: this.get('loop_end'),
      loop: this.get('loop'),
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.event.value = this.get('value');
    });
    this.on('change:loop_start', () => {
      this.event.loopStart = this.get('loop_start');
    });
    this.on('change:loop_end', () => {
      this.event.loopEnd = this.get('loop_end');
    });
    this.on('change:loop', () => {
      this.event.loop = this.get('loop');
    });
  }

  dispose(): void {
    this.event.dispose();
  }

  static model_name = 'EventModel';
}

export class PartModel extends BaseEventModel<tone.Part> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PartModel.model_name,
      _events: [],
      length: 0,
      loop_start: 0,
      loop_end: '1m',
      loop: false,
    };
  }

  protected createEvent(): tone.Part {
    return new tone.Part({
      events: this.get('_events'),
      humanize: this.get('humanize'),
      probability: this.get('probability'),
      mute: this.get('mute'),
      playbackRate: this.get('playback_rate'),
      loopStart: this.get('loop_start'),
      loopEnd: this.get('loop_end'),
      loop: this.get('loop'),
    });
  }

  protected handleMsg(command: any, buffers: any): void {
    super.handleMsg(command, buffers);

    if (command.event === 'add') {
      this.event.add(command.arg);
    } else if (command.event === 'at') {
      this.event.at(command.time, command.value);
    } else if (command.event === 'remove') {
      // TODO: not working in Tone.js?
      if (command.time === null) {
        console.log(command.value);
        console.log(this.event.at(command.value.time));
        this.event.remove(command.value);
      } else {
        console.log(command);
        console.log(this.event.at(command.time));
        this.event.remove(command.time, command.value);
      }
    } else if (command.event === 'clear') {
      this.event.clear();
    }

    // sync number of events
    this.set('length', this.event.length);
    this.save_changes();
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:loop_start', () => {
      this.event.loopStart = this.get('loop_start');
    });
    this.on('change:loop_end', () => {
      this.event.loopEnd = this.get('loop_end');
    });
    this.on('change:loop', () => {
      this.event.loop = this.get('loop');
    });
  }

  static model_name = 'PartModel';
}

export class SequenceModel extends BaseEventModel<tone.Sequence> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SequenceModel.model_name,
      events: [],
      _subdivision: '8n',
      length: 0,
      loop_start: 0,
      loop_end: 0,
      loop: true,
    };
  }

  protected createEvent(): tone.Sequence {
    return new tone.Sequence({
      events: this.get('events'),
      subdivision: this.get('_subdivision'),
      humanize: this.get('humanize'),
      probability: this.get('probability'),
      mute: this.get('mute'),
      playbackRate: this.get('playback_rate'),
      loopStart: this.get('loop_start'),
      loopEnd: this.get('loop_end'),
      loop: this.get('loop'),
    });
  }

  protected handleMsg(command: any, buffers: any): void {
    super.handleMsg(command, buffers);

    if (command.event === 'clear') {
      this.event.clear();
    }

    // sync number of events
    this.set('length', this.event.length);
    this.save_changes();
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:loop_start', () => {
      this.event.loopStart = this.get('loop_start');
    });
    this.on('change:loop_end', () => {
      this.event.loopEnd = this.get('loop_end');
    });
    this.on('change:loop', () => {
      this.event.loop = this.get('loop');
    });

    this.on('change:events', () => {
      this.event.events = this.get('events');
    });
  }

  static model_name = 'SequenceModel';
}

interface Loop extends Event {
  interval: tone.Unit.Time;
  iterations: number | null;
}

abstract class BaseLoopModel<T extends Loop> extends BaseEventModel<T> {
  defaults(): any {
    return {
      ...super.defaults(),
      interval: '8n',
      iterations: null,
    };
  }

  get iterations(): number {
    if (this.get('iterations') === null) {
      return Infinity;
    } else {
      return this.get('iterations');
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:interval', () => {
      this.event.interval = this.get('interval');
    });
    this.on('change:iterations', () => {
      this.event.iterations = this.iterations;
    });
  }
}

export class LoopModel extends BaseLoopModel<tone.Loop> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: LoopModel.model_name,
    };
  }

  protected createEvent(): tone.Loop {
    return new tone.Loop({
      interval: this.get('interval'),
      iterations: this.iterations,
      humanize: this.get('humanize'),
      probability: this.get('probability'),
      mute: this.get('mute'),
      playbackRate: this.get('playback_rate'),
    });
  }

  static model_name = 'LoopModel';
}

export class PatternModel extends BaseLoopModel<tone.Pattern<any>> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PatternModel.model_name,
      pattern: 'up',
      values: [],
    };
  }

  protected createEvent(): tone.Pattern<any> {
    return new tone.Pattern({
      pattern: this.get('pattern'),
      values: this.get('values'),
      interval: this.get('interval'),
      iterations: this.iterations,
      humanize: this.get('humanize'),
      probability: this.get('probability'),
      mute: this.get('mute'),
      playbackRate: this.get('playback_rate'),
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:pattern', () => {
      this.event.pattern = this.get('pattern');
    });
    this.on('change:values', () => {
      this.event.values = this.get('values');
    });
  }

  static model_name = 'PatternModel';
}
