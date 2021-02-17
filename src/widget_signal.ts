import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitName } from 'tone/Tone/core/type/Units';

import { AudioNodeModel } from './widget_base';

export class SignalModel<T extends UnitName> extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SignalModel.model_name,
      value: null,
      _units: 'number',
      _min_value: undefined,
      _max_value: undefined,
      overridden: false,
    };
  }

  initialize(attributes: Backbone.ObjectHash, options: any): void {
    super.initialize(attributes, options);

    this.updateOverridden();
  }

  createNode(): tone.Signal {
    return new tone.Signal({
      value: this.get('value'),
      units: this.get('_units'),
      minValue: this.normalizeMinMax(this.get('_min_value')),
      maxValue: this.normalizeMinMax(this.get('_max_value')),
    });
  }

  private updateOverridden(): void {
    this.set('overridden', this.node.overridden);
    // if overridden, value is reset to 0
    this.set('value', this.node.value);
    this.save_changes();
  }

  protected connectInputCallback(): void {
    // new connected incoming signal overrides this signal value
    this.updateOverridden();
  }

  private normalizeMinMax(value: number | null): number | undefined {
    return value === null ? undefined : value;
  }

  get value(): any {
    return this.node.value;
  }

  get minValue(): number {
    return this.node.minValue;
  }

  get maxValue(): number {
    return this.node.maxValue;
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });
  }

  node: tone.Signal<T>;

  static model_name = 'SignalModel';
}

export class MultiplyModel extends SignalModel<'number'> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MultiplyModel.model_name,
      _factor: undefined,
    };
  }

  createNode(): tone.Multiply {
    const mult = new tone.Multiply();
    this.factor.node.connect(mult.factor);
    return mult;
  }

  get factor(): SignalModel<'number'> {
    return this.get('_factor');
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _factor: { deserialize: unpack_models as any },
  };

  node: tone.Multiply;

  static model_name = 'MultiplyModel';
}

export class AddModel extends SignalModel<'number'> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AddModel.model_name,
      _addend: undefined,
    };
  }

  createNode(): tone.Add {
    const add = new tone.Add();
    this.addend.node.connect(add.addend);
    return add;
  }

  get addend(): SignalModel<'number'> {
    return this.get('_addend');
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _addend: { deserialize: unpack_models as any },
  };

  node: tone.Add;

  static model_name = 'AddModel';
}

export class SubtractModel extends SignalModel<'number'> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SubtractModel.model_name,
      _subtrahend: undefined,
    };
  }

  createNode(): tone.Subtract {
    const sub = new tone.Subtract();
    this.subtrahend.node.connect(sub.subtrahend);
    return sub;
  }

  get subtrahend(): SignalModel<'number'> {
    return this.get('_subtrahend');
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _subtrahend: { deserialize: unpack_models as any },
  };

  node: tone.Subtract;

  static model_name = 'SubtractModel';
}
