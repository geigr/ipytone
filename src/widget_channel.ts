import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { GainModel, ParamModel } from './widget_core';

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

export class PannerModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PannerModel.model_name,
      _pan: undefined,
    };
  }

  createNode(): tone.Panner {
    return new tone.Panner({ pan: this.pan.value });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.pan.setNode(this.node.pan);
  }

  get pan(): ParamModel<'audioRange'> {
    return this.get('_pan');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _pan: { deserialize: unpack_models as any },
  };

  node: tone.Panner;

  static model_name = 'PannerModel';
}

export class SoloModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SoloModel.model_name,
      solo: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    // keep track of all instances for syncing models
    SoloModel._allSoloModels.add(this);
  }

  createNode(): tone.Solo {
    return new tone.Solo({ solo: this.solo });
  }

  get solo(): boolean {
    return this.get('solo');
  }

  set solo(solo: boolean) {
    this.node.solo = solo;

    // synchronize all solo models (their gain param)
    SoloModel._allSoloModels.forEach((instance) => {
      const gainParam = (instance.input as GainModel).gain;
      gainParam.set('value', gainParam.node.value);
      gainParam.save_changes();
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:solo', () => {
      this.solo = this.get('solo');
    });
  }

  node: tone.Solo;

  private static _allSoloModels: Set<SoloModel> = new Set();

  static model_name = 'SoloModel';
}

export class MergeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MergeModel.model_name,
      _channels: 2,
    };
  }

  createNode(): tone.Merge {
    return new tone.Merge({ channels: this.get('_channels') });
  }

  node: tone.Merge;

  static model_name = 'MergeModel';
}

export class SplitModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SplitModel.model_name,
      _channels: 2,
    };
  }

  createNode(): tone.Split {
    return new tone.Split({ channels: this.get('_channels') });
  }

  node: tone.Split;

  static model_name = 'SplitModel';
}
