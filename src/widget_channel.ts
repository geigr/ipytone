import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { GainModel } from './widget_core';

import { SignalModel } from './widget_signal';

export class CrossFadeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CrossFadeModel.model_name,
      _a: undefined,
      _b: undefined,
      _fade: undefined,
    };
  }

  createNode(): tone.CrossFade {
    return new tone.CrossFade({ fade: this.fade.value });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.a.setNode(this.node.a);
    this.b.setNode(this.node.b);
    this.fade.setNode(this.node.fade);
  }

  get a(): GainModel {
    return this.get('_a');
  }

  get b(): GainModel {
    return this.get('_b');
  }

  get fade(): SignalModel<'normalRange'> {
    return this.get('_fade');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _a: { deserialize: unpack_models as any },
    _b: { deserialize: unpack_models as any },
    _fade: { deserialize: unpack_models as any },
  };

  node: tone.CrossFade;

  static model_name = 'CrossFadeModel';
}
