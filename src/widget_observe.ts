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
  update_interval: string | number;
  draw: boolean;
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

  private scheduleRepeat(
    transport: boolean,
    updateInterval: number | string,
    draw: boolean
  ): void {
    const model = this.observedWidget;
    let eid: number | ReturnType<typeof setInterval>;

    if (transport) {
      eid = tone.Transport.scheduleRepeat((time) => {
        if (draw) {
          tone.Draw.schedule(() => {
            this.setObservedTrait(time, model.getValueAtTime(time));
          }, time);
        } else {
          this.setObservedTrait(time, model.getValueAtTime(time));
        }
      }, updateInterval);
    } else {
      eid = setInterval(() => {
        this.setObservedTrait(tone.now(), model.getValue());
      }, (updateInterval as number) * 1000);
    }

    this.event = { id: eid, transport: transport };
  }

  private scheduleCancel(): void {
    if (this.event.transport) {
      tone.Transport.cancel(this.event.id as number);
    } else {
      clearInterval(this.event.id as ReturnType<typeof setInterval>);
    }
  }

  private handleMsg(command: ScheduleObserverCommand, _buffers: any): void {
    if (command.event === 'scheduleRepeat') {
      this.scheduleRepeat(
        command.transport,
        command.update_interval,
        command.draw
      );
    } else if (command.event === 'scheduleCancel') {
      this.scheduleCancel();
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
