import { WidgetModel, ISerializers } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { ToneObjectModel } from './widget_base';

type transportCallback = { (time: number): void };

export class TransportModel extends ToneObjectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: TransportModel.model_name,
    };
  }

  static serializers: ISerializers = {
    ...ToneObjectModel.serializers,
  };

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);
    this.py2jsEventID = {};
  }

  initEventListeners(): void {
    this.on('msg:custom', this.handleMsg, this);
  }

  private getToneCallback(items: any): Promise<transportCallback> {
    const itemsModel = items.map((data: any) => {
      return Promise.resolve(this.widget_manager.get_model(data.callee)).then(
        (model: WidgetModel | undefined) => {
          const item = { ...data };
          item.model = model;
          return item;
        }
      );
    });

    return Promise.all(itemsModel).then((items) => {
      const callback = (time: number) => {
        items.forEach((item: any) => {
          const args = { ...item.args };
          args.time = eval(args.time);
          const argsArray = normalizeArguments(args, item.arg_keys);
          item.model.node[item.method](...argsArray);
        });
      };

      return callback;
    });
  }

  private schedule(command: any): void {
    const callback = Promise.resolve(this.getToneCallback(command.items));

    if (command.op === '') {
      callback.then((clb) => {
        this.py2jsEventID[command.id] = tone.Transport.schedule(
          clb,
          command.time
        );
      });
    } else if (command.op === 'repeat') {
      let duration = Infinity;
      if (command.duration) {
        duration = command.duration;
      }
      callback.then((clb) => {
        this.py2jsEventID[command.id] = tone.Transport.scheduleRepeat(
          clb,
          command.interval,
          command.start_time,
          duration
        );
      });
    } else if (command.op === 'once') {
      callback.then((clb) => {
        this.py2jsEventID[command.id] = tone.Transport.scheduleOnce(
          clb,
          command.time
        );
      });
    }
  }

  private play(command: any): void {
    const argsArray = normalizeArguments(command.args, command.arg_keys);
    (tone.Transport as any)[command.method](...argsArray);
  }

  private handleMsg(command: any, buffers: any): void {
    if (command.event === 'schedule') {
      this.schedule(command);
    } else if (command.event === 'play') {
      this.play(command);
    } else if (command.event === 'clear') {
      this.clearEvent(command.id);
    }
  }

  private clearEvent(pyEventID: number): void {
    tone.Transport.clear(this.py2jsEventID[pyEventID]);
    delete this.py2jsEventID[pyEventID];
  }

  py2jsEventID: { [id: number]: number };

  static model_name = 'TransportModel';
}
