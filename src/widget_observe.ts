import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { ToneWidgetModel } from './widget_base';

type ObserveEvent = {
  id: number | ReturnType<typeof setInterval>;
  transport: boolean;
};

type ScheduleObserverCommand = {
  event: string;
  transport: boolean;
  repeat_interval: string | number;
};

export interface ObservableModel {
  getValueAtTime: (time: tone.Unit.Seconds) => tone.Unit.Unit;
  getValue: () => tone.Unit.Unit;
}

export class ScheduleObserverModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ScheduleObserverModel.model_name,
      observed_widget: null,
      observed_trait: 'value',
      time: 0.0,
      value: 0.0,
      time_value: [],
    };
  }

  private event: ObserveEvent;

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    this.event = { id: 0, transport: false };
  }

  get observedWidget(): ObservableModel {
    return this.get('observed_widget');
  }

  get observedTrait(): string {
    return this.get('observed_trait');
  }

  private setObservedTrait(
    time: tone.Unit.Seconds,
    value: tone.Unit.Unit
  ): void {
    if (this.observedTrait === 'value') {
      this.set('value', value);
    } else if (this.observedTrait === 'time') {
      this.set('time', time);
    } else if (this.observedTrait === 'time_value') {
      this.set('time_value', [time, value]);
    }

    this.save_changes();
  }

  private scheduleObserve(
    transport: boolean,
    repeatInterval: number | string
  ): void {
    const obj = this.observedWidget;
    let eid: number | ReturnType<typeof setInterval>;

    if (transport) {
      eid = tone.Transport.scheduleRepeat((time) => {
        this.setObservedTrait(time, obj.getValueAtTime(time));
      }, repeatInterval);
    } else {
      eid = setInterval(() => {
        this.setObservedTrait(tone.now(), obj.getValue());
      }, (repeatInterval as number) * 1000);
    }

    this.event = { id: eid, transport: transport };
  }

  private scheduleUnobserve(): void {
    if (this.event.transport) {
      tone.Transport.cancel(this.event.id as number);
    } else {
      clearInterval(this.event.id as ReturnType<typeof setInterval>);
    }
  }

  private handleMsg(command: ScheduleObserverCommand, _buffers: any): void {
    if (command.event === 'scheduleObserve') {
      this.scheduleObserve(command.transport, command.repeat_interval);
    } else if (command.event === 'scheduleUnobserve') {
      this.scheduleUnobserve();
    }
  }

  initEventListeners(): void {
    this.on('msg:custom', this.handleMsg, this);
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    observed_widget: { deserialize: unpack_models as any },
  };

  static model_name = 'ScheduleObserverModel';
}
