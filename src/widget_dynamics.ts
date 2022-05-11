import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

export class CompressorModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CompressorModel.model_name,
      _threshold: undefined,
      _ratio: undefined,
      _attack: undefined,
      _release: undefined,
      _knee: undefined,
    };
  }

  createNode(): tone.Compressor {
    return new tone.Compressor({
      threshold: this.threshold.value,
      ratio: this.ratio.value,
      attack: this.attack.value,
      release: this.release.value,
      knee: this.knee.value,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.threshold.setNode(this.node.threshold);
    this.ratio.setNode(this.node.ratio);
    this.attack.setNode(this.node.attack);
    this.release.setNode(this.node.release);
    this.knee.setNode(this.node.knee);
  }

  get threshold(): ParamModel<'decibels'> {
    return this.get('_threshold');
  }

  get ratio(): ParamModel<'positive'> {
    return this.get('_ratio');
  }

  get attack(): ParamModel<'time'> {
    return this.get('_attack');
  }

  get release(): ParamModel<'time'> {
    return this.get('_release');
  }

  get knee(): ParamModel<'decibels'> {
    return this.get('_knee');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _threshold: { deserialize: unpack_models as any },
    _ratio: { deserialize: unpack_models as any },
    _attack: { deserialize: unpack_models as any },
    _release: { deserialize: unpack_models as any },
    _knee: { deserialize: unpack_models as any },
  };

  node: tone.Compressor;

  static model_name = 'CompressorModel';
}
