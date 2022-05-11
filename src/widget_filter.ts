import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

// import { PhaseShiftAllpass } from 'tone/Tone/component/filter/PhaseShiftAllpass';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

import {
  ArrayProperty,
  dataarray_serialization,
  getArrayProp,
} from './serializers';

export class BiquadFilterModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: BiquadFilterModel.model_name,
      type: 'lowpass',
      _frequency: undefined,
      _q: undefined,
      _detune: undefined,
      _gain: undefined,
      array: null,
      array_length: 128,
      sync_array: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.maybeSetArray();
    }
  }

  createNode(): tone.BiquadFilter {
    return new tone.BiquadFilter({
      type: this.get('type'),
      frequency: this.frequency.value,
      Q: this.q.value,
      detune: this.detune.value,
      gain: this.gain.value,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
    this.q.setNode(this.node.Q);
    this.detune.setNode(this.node.detune);
    this.gain.setNode(this.node.gain);
  }

  maybeSetArray(): void {
    if (this.get('sync_array')) {
      this.array = this.node.getFrequencyResponse(this.get('array_length'));
      this.save_changes();
    }
  }

  get frequency(): ParamModel<'frequency'> {
    return this.get('_frequency');
  }

  get q(): ParamModel<'number'> {
    return this.get('_q');
  }

  get detune(): ParamModel<'cents'> {
    return this.get('_detune');
  }

  get gain(): ParamModel<'decibels'> {
    return this.get('_gain');
  }

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.get('type');
      this.maybeSetArray();
    });
    this.frequency.on('change:value', () => this.maybeSetArray());
    this.q.on('change:value', () => this.maybeSetArray());
    this.detune.on('change:value', () => this.maybeSetArray());
    this.gain.on('change:value', () => this.maybeSetArray());
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _q: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
    _gain: { deserialize: unpack_models as any },
    array: dataarray_serialization,
  };

  node: tone.BiquadFilter;

  static model_name = 'BiquadFilterModel';
}

export class FilterModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: FilterModel.model_name,
      type: 'lowpass',
      _frequency: undefined,
      _q: undefined,
      _detune: undefined,
      _gain: undefined,
      rolloff: -12,
      array: null,
      array_length: 128,
      sync_array: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.maybeSetArray();
    }
  }

  createNode(): tone.Filter {
    return new tone.Filter({
      type: this.get('type'),
      frequency: this.frequency.value,
      Q: this.q.value,
      detune: this.detune.value,
      gain: this.gain.value,
      rolloff: this.get('rolloff'),
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
    this.q.setNode(this.node.Q);
    this.detune.setNode(this.node.detune);
    this.gain.setNode(this.node.gain);
  }

  maybeSetArray(): void {
    if (this.get('sync_array')) {
      this.array = this.node.getFrequencyResponse(this.get('array_length'));
      this.save_changes();
    }
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get q(): SignalModel<'positive'> {
    return this.get('_q');
  }

  get detune(): SignalModel<'cents'> {
    return this.get('_detune');
  }

  get gain(): SignalModel<'decibels'> {
    return this.get('_gain');
  }

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.get('type');
      this.maybeSetArray();
    });
    this.frequency.on('change:value', () => this.maybeSetArray());
    this.q.on('change:value', () => this.maybeSetArray());
    this.detune.on('change:value', () => this.maybeSetArray());
    this.gain.on('change:value', () => this.maybeSetArray());
    this.on('change:rolloff', () => {
      this.node.rolloff = this.get('rolloff');
      this.maybeSetArray();
    });
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _q: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
    _gain: { deserialize: unpack_models as any },
    array: dataarray_serialization,
  };

  node: tone.Filter;

  static model_name = 'FilterModel';
}

export class OnePoleFilterModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: OnePoleFilterModel.model_name,
      type: 'lowpass',
      frequency: 880,
      array: null,
      array_length: 128,
      sync_array: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.maybeSetArray();
    }
  }

  createNode(): tone.OnePoleFilter {
    return new tone.OnePoleFilter({
      type: this.get('type'),
      frequency: this.get('frequency'),
    });
  }

  maybeSetArray(): void {
    if (this.get('sync_array')) {
      this.array = this.node.getFrequencyResponse(this.get('array_length'));
      this.save_changes();
    }
  }

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.get('type');
      this.maybeSetArray();
    });
    this.on('change:frequency', () => {
      this.node.frequency = this.get('frequency');
      this.maybeSetArray();
    });
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    array: dataarray_serialization,
  };

  node: tone.OnePoleFilter;

  static model_name = 'OnePoleFilterModel';
}

export class FeedbackCombFilterModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: FeedbackCombFilterModel.model_name,
      _delay_time: undefined,
      _resonance: undefined,
    };
  }

  createNode(): tone.FeedbackCombFilter {
    return new tone.FeedbackCombFilter({
      delayTime: this.delayTime.value,
      resonance: this.resonance.value,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.delayTime.setNode(this.node.delayTime);
    this.resonance.setNode(this.node.resonance);
  }

  get delayTime(): ParamModel<'time'> {
    return this.get('_delay_time');
  }

  get resonance(): ParamModel<'normalRange'> {
    return this.get('_resonance');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _delay_time: { deserialize: unpack_models as any },
    _resonance: { deserialize: unpack_models as any },
  };

  node: tone.FeedbackCombFilter;

  static model_name = 'FeedbackCombFilterModel';
}

// TODO: Tone.js PhaseShiftAllpass not (yet?) part of public API
// export class PhaseShiftAllpassModel extends AudioNodeModel {
//   defaults(): any {
//     return {
//       ...super.defaults(),
//       _model_name: PhaseShiftAllpassModel.model_name,
//       _offset90: undefined,
//     };
//   }

//   createNode(): PhaseShiftAllpass {
//     return new PhaseShiftAllpass();
//   }

//   setSubNodes(): void {
//     super.setSubNodes();
//     this.offset90.setNode(this.node.offset90);
//   }

//   get offset90(): GainModel {
//     return this.get('_offset90');
//   }

//   static serializers: ISerializers = {
//     ...AudioNodeModel.serializers,
//     _offset90: { deserialize: unpack_models as any },
//   };

//   node: PhaseShiftAllpass;

//   static model_name = 'PhaseShiftAllpassModel';
// }
