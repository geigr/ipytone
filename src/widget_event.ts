import { WidgetModel } from '@jupyter-widgets/base';

import * as tone from 'tone';

import type { callbackArgs, callbackItem } from './utils';

import { normalizeArguments } from './utils';

import { NodeWithContextModel } from './widget_base';

type eventCallback = { (time: number, value: any): void };

export class EventModel extends NodeWithContextModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: EventModel.model_name,
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

    this.event = new tone.ToneEvent({
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

  private getToneCallback(items: any): Promise<eventCallback> {
    const itemsModel: callbackItem[] = items.map((data: any) => {
      return Promise.resolve(this.widget_manager.get_model(data.callee)).then(
        (model: WidgetModel | undefined) => {
          const item = { ...data };
          item.model = model as NodeWithContextModel;
          return item;
        }
      );
    });

    return Promise.all(itemsModel).then((items) => {
      const callback = (time: number, value: any) => {
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
    });
  }

  private setCallback(command: any): void {
    Promise.resolve(this.getToneCallback(command.items)).then((clb) => {
      this.event.callback = clb;
    });
  }

  private play(command: any): void {
    const argsArray = normalizeArguments(command.args, command.arg_keys);
    (this.event as any)[command.method](...argsArray);
  }

  private handleMsg(command: any, buffers: any): void {
    if (command.event === 'set_callback') {
      this.setCallback(command);
    } else if (command.event === 'play') {
      this.play(command);
    } else if (command.event === 'cancel') {
      this.event.cancel(command.time);
    }
  }

  initEventListeners(): void {
    this.on('change:value', () => {
      this.event.value = this.get('value');
    });
    this.on('change:humanize', () => {
      this.event.humanize = this.get('humanize');
    });
    this.on('change:probability', () => {
      this.event.probability = this.get('probability');
    });
    this.on('change:mute', () => {
      this.event.mute = this.get('mute');
    });
    this.on('change:start_offset', () => {
      this.event.startOffset = this.get('start_offset');
    });
    this.on('change:playback_rate', () => {
      this.event.playbackRate = this.get('playback_rate');
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
    this.on('msg:custom', this.handleMsg, this);
  }

  event: tone.ToneEvent;

  static model_name = 'EventModel';
}
