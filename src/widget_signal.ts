import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitName, UnitMap } from 'tone/Tone/core/type/Units';

import { assert, normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

import { ObservableModel } from './widget_observe';

abstract class SignalOperatorModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SignalOperatorModel.model_name,
    };
  }

  static model_name = 'SignalOperatorModel';
}

export class SignalModel<T extends UnitName>
  extends SignalOperatorModel
  implements ObservableModel
{
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SignalModel.model_name,
      _override: true,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.updateOverridden();
    }
  }

  get input(): ParamModel<T> {
    return this.get('_input');
  }

  get value(): UnitMap[T] {
    return this.get('value');
  }

  createNode(): tone.Signal<T> {
    return new tone.Signal(this.input.properties);
  }

  private updateOverridden(): void {
    this.input.set('overridden', this.node.overridden);
    // if overridden, value is reset to 0
    this.input.set('value', this.node.value);
    this.input.save_changes();
    this.set('value', this.node.value);
    this.save_changes();
  }

  connectInputCallback(): void {
    // new connected incoming signal overrides this signal value
    this.updateOverridden();
  }

  getValueAtTime(traitName: string, time: tone.Unit.Seconds): UnitMap[T] {
    assert(traitName === 'value', 'param only supports "value" trait');
    return this.node.getValueAtTime(time);
  }

  getValue(traitName: string): UnitMap[T] {
    assert(traitName === 'value', 'param only supports "value" trait');
    return this.node.value;
  }

  private handleMsg(command: any, _buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });

    this.on('msg:custom', this.handleMsg, this);
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
    return new tone.Multiply(this.factor.value);
  }

  get factor(): ParamModel<'number'> {
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
    return new tone.Add(this.addend.value);
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.addend.setNode(this.node.addend);
  }

  get addend(): ParamModel<'number'> {
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
    return new tone.Subtract(this.subtrahend.value);
  }

  get subtrahend(): ParamModel<'number'> {
    return this.get('_subtrahend');
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.subtrahend.setNode(this.node.subtrahend);
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _subtrahend: { deserialize: unpack_models as any },
  };

  node: tone.Subtract;

  static model_name = 'SubtractModel';
}

export class GreaterThanModel extends SignalModel<'number'> {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: GreaterThanModel.model_name,
      _comparator: undefined,
    };
  }

  createNode(): tone.GreaterThan {
    return new tone.GreaterThan(this.comparator.value);
  }

  get comparator(): ParamModel<'number'> {
    return this.get('_comparator');
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.comparator.setNode(this.node.comparator);
  }

  static serializers: ISerializers = {
    ...SignalModel.serializers,
    _comparator: { deserialize: unpack_models as any },
  };

  node: tone.GreaterThan;

  static model_name = 'GreaterThanModel';
}

export class AudioToGainModel extends SignalOperatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioToGainModel.model_name,
    };
  }

  createNode(): tone.AudioToGain {
    return new tone.AudioToGain();
  }

  node: tone.AudioToGain;

  static model_name = 'AudioToGainModel';
}

export class AbsModel extends SignalOperatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AbsModel.model_name,
    };
  }

  createNode(): tone.Abs {
    return new tone.Abs();
  }

  node: tone.Abs;

  static model_name = 'AbsModel';
}

export class NegateModel extends SignalOperatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NegateModel.model_name,
    };
  }

  createNode(): tone.Negate {
    return new tone.Negate();
  }

  node: tone.Negate;

  static model_name = 'NegateModel';
}

export class PowModel extends SignalOperatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PowModel.model_name,
      value: 1,
    };
  }

  createNode(): tone.Pow {
    return new tone.Pow(this.get('value'));
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });
  }

  node: tone.Pow;

  static model_name = 'PowModel';
}

export class ScaleModel extends SignalOperatorModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ScaleModel.model_name,
      min_out: 0.0,
      max_out: 1.0,
    };
  }

  createNode(): tone.Scale {
    return new tone.Scale(this.get('min_out'), this.get('max_out'));
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:min_out', () => {
      this.node.min = this.get('min_out');
    });
    this.on('change:max_out', () => {
      this.node.min = this.get('max_out');
    });
  }

  node: tone.Scale;

  static model_name = 'ScaleModel';
}
