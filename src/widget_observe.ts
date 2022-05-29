import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { ToneWidgetModel } from './widget_base';

import { dataarray_serialization } from './serializers';

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

type TraitValue =
  | tone.Unit.Unit
  | tone.PlaybackState
  | Float32Array
  | Float32Array[]
  | number
  | number[];

export interface ObservableModel {
  getValueAtTime: (traitName: string, time: tone.Unit.Seconds) => TraitValue;
  getValue: (traitName: string) => TraitValue;
}

export class ScheduleObserverModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ScheduleObserverModel.model_name,
      observed_widget: null,
      observed_trait: 'value',
      observe_time: false,
      time: 0.0,
      value: 0.0,
      state: 'stopped',
      progress: 0.0,
      position: '0:0:0',
      ticks: 0,
      seconds: 0.0,
      array: [],
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

  get observeTime(): boolean {
    return this.get('observe_time');
  }

  private setObservedTrait(time: tone.Unit.Seconds, transport: boolean): void {
    const model = this.observedWidget;
    const traitName = this.observedTrait;
    let traitValue: TraitValue = 0;

    if (traitName === 'array') {
      // bug when array elements aren't changing, then it's never
      // synced again even if it gets updated again later?
      // -> reset array value silently
      this.set('array', new Float32Array([0]), { silent: true });
    }

    if (traitName === 'time') {
      traitValue = time;
    } else {
      if (transport) {
        traitValue = model.getValueAtTime(traitName, time);
      } else {
        traitValue = model.getValue(traitName);
      }
    }

    if (this.observeTime) {
      this.set('time_value', [time, traitValue]);
    } else {
      this.set(traitName, traitValue);
    }

    this.save_changes();
  }

  private scheduleRepeat(
    transport: boolean,
    updateInterval: number | string,
    draw: boolean
  ): void {
    let eid: number | ReturnType<typeof setInterval>;

    if (transport) {
      eid = tone.Transport.scheduleRepeat((time) => {
        if (draw) {
          tone.Draw.schedule(() => {
            this.setObservedTrait(time, transport);
          }, time);
        } else {
          this.setObservedTrait(time, transport);
        }
      }, updateInterval);
    } else {
      eid = setInterval(() => {
        this.setObservedTrait(tone.now(), transport);
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
    array: dataarray_serialization,
  };

  static model_name = 'ScheduleObserverModel';
}
