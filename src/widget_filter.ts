import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

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
      curve: null,
      curve_length: 128,
      sync_curve: false,
    };
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

  maybeSetCurve(): void {
    if (this.get('sync_curve')) {
      this.curve = this.node.getFrequencyResponse(this.get('curve_length'));
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

  get curve(): ArrayProperty {
    return getArrayProp(this.get('curve'));
  }

  set curve(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('curve', value, { silent: true });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.get('type');
      this.maybeSetCurve();
    });
    this.frequency.on('change:value', () => this.maybeSetCurve());
    this.q.on('change:value', () => this.maybeSetCurve());
    this.detune.on('change:value', () => this.maybeSetCurve());
    this.gain.on('change:value', () => this.maybeSetCurve());
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _q: { deserialize: unpack_models as any },
    _detune: { deserialize: unpack_models as any },
    _gain: { deserialize: unpack_models as any },
    curve: dataarray_serialization,
  };

  node: tone.BiquadFilter;

  static model_name = 'BiquadFilterModel';
}
