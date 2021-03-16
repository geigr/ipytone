import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

export class VibratoModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: VibratoModel.model_name,
      _max_delay: 0.005,
      _frequency: undefined,
      _depth: undefined,
      type: 'sine',
    };
  }

  createNode(): tone.Vibrato {
    return new tone.Vibrato({
      frequency: this.frequency.value,
      depth: this.depth.value,
      type: this.get('type'),
      maxDelay: this.get('_max_delay'),
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
    this.depth.setNode(this.node.depth);
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get depth(): ParamModel<'normalRange'> {
    return this.get('_depth');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _depth: { deserialize: unpack_models as any },
  };

  node: tone.Vibrato;

  static model_name = 'VibratoModel';
}
