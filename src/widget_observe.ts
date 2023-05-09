import {
  ISerializers,
  unpack_models,
  WidgetModel,
} from '@jupyter-widgets/base';

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
      target_widget: null,
      target_trait: 'value',
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
  private _observedWidget: ObservableModel;
  private _targetWidget: WidgetModel;

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any },
  ): void {
    super.initialize(attributes, options);

    this.event = { id: 0, transport: false };

    // cache unserialized widget models for fast access in schedule loop
    this._observedWidget = this.get('observed_widget');
    this._targetWidget = this.get('target_widget');
    if (this._targetWidget === null) {
      this._targetWidget = this;
    }
  }

  /*
   * Returns the observed ipytone widget model (e.g., audio node, signal, param
   * or transport)
   */
  get observedWidget(): ObservableModel {
    return this._observedWidget;
  }

  get observedTrait(): string {
    return this.get('observed_trait');
  }

  get observeTime(): boolean {
    return this.get('observe_time');
  }

  /*
   * Returns either this observer model instance (observe or dlink) or another
   * widget model instance (jsdlink)
   */
  get targetWidget(): WidgetModel {
    return this._targetWidget;
  }

  get targetTrait(): string {
    return this.get('target_trait');
  }

  private setTargetTrait(time: tone.Unit.Seconds, transport: boolean): void {
    const observedWidget = this.observedWidget;
    const observedTrait = this.observedTrait;
    const targetWidget = this.targetWidget;
    const targetTrait = this.targetTrait;
    let value: TraitValue = 0;

    if (observedTrait === 'array') {
      // bug when array elements aren't changing, then it's never
      // synced again even if it gets updated again later?
      // -> reset array value silently
      targetWidget.set('array', new Float32Array([0]), { silent: true });
    }

    if (observedTrait === 'time') {
      value = time;
    } else {
      if (transport) {
        value = observedWidget.getValueAtTime(observedTrait, time);
      } else {
        value = observedWidget.getValue(observedTrait);
      }
    }

    if (this.observeTime) {
      targetWidget.set('time_value', [time, value]);
    } else {
      targetWidget.set(targetTrait, value);
    }

    if (targetWidget === this) {
      // sync with backend unless target is another widget (jsdlink).
      targetWidget.save_changes();
    }
  }

  private scheduleRepeat(
    transport: boolean,
    updateInterval: number | string,
    draw: boolean,
  ): void {
    let eid: number | ReturnType<typeof setInterval>;

    if (transport) {
      eid = tone.Transport.scheduleRepeat((time) => {
        if (draw) {
          tone.Draw.schedule(() => {
            this.setTargetTrait(time, transport);
          }, time);
        } else {
          this.setTargetTrait(time, transport);
        }
      }, updateInterval);
    } else {
      eid = setInterval(
        () => {
          this.setTargetTrait(tone.now(), transport);
        },
        (updateInterval as number) * 1000,
      );
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
        command.draw,
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
    target_widget: { deserialize: unpack_models as any },
    array: dataarray_serialization,
  };

  static model_name = 'ScheduleObserverModel';
}
