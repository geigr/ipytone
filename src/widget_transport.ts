import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

import { ToneWidgetModel } from './widget_base';

export class TransportModel extends WidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: TransportModel.model_name,
      _toggle_schedule: false,
      _toggle_clear: false,
      _schedule_op: '',
      _audio_nodes: [],
      _methods: [],
      _packed_args: [],
      _interval: '',
      _start_time: '',
      _duration: null,
      _py_event_id: 0,
      _clear_event_id: 0,
      state: 'stopped',
    };
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _audio_nodes: { deserialize: unpack_models as any },
  };

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);
    this.py2jsEventID = {};
    this.initEventListeners();
  }

  initEventListeners(): void {
    this.on('change:state', this.startStopTransport, this);
    this.on('change:_toggle_schedule', this.schedule, this);
    this.on('change:_toggle_clear', this.clear_event, this);
  }

  private startStopTransport(): void {
    if (this.get('state') === 'started') {
      tone.Transport.start();
    } else {
      tone.Transport.stop();
    }
  }

  private schedule(): void {
    const schedule_op = this.get('_schedule_op');
    const audioNodes = this.get('_audio_nodes');
    const methods = this.get('_methods');
    const packed_args = this.get('_packed_args');
    const callback = function (time: number) {
      for (let i = 0; i < audioNodes.length; i++) {
        const audioNode = audioNodes[i].node;
        const method = methods[i];
        const args = packed_args[i].split(' *** ');
        args.pop();
        for (let j = 0; j < args.length; j++) {
          args[j] = eval(args[j]);
        }
        if (method === 'start') {
          audioNode.start(...args);
        } else if (method === 'stop') {
          audioNode.stop(...args);
        }
      }
    };
    let eventID;
    if (schedule_op === 'scheduleRepeat') {
      const interval = this.get('_interval');
      const startTime = this.get('_start_time');
      let duration = this.get('_duration');
      if (!duration) {
        duration = Infinity;
      }
      eventID = tone.Transport.scheduleRepeat(
        callback,
        interval,
        startTime,
        duration
      );
    } else {
      return;
    }
    const pyEventID = this.get('_py_event_id');
    this.py2jsEventID[pyEventID] = eventID;
  }

  private clear_event(): void {
    const pyEventID = this.get('_clear_event_id');
    tone.Transport.clear(this.py2jsEventID[pyEventID]);
    delete this.py2jsEventID[pyEventID];
  }

  py2jsEventID: { [id: number]: number };

  static model_name = 'TransportModel';
}
