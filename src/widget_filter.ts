import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

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
