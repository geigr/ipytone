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

export class Panner3DModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: Panner3DModel.model_name,
      _position_x: undefined,
      _position_y: undefined,
      _position_z: undefined,
      _orientation_x: undefined,
      _orientation_y: undefined,
      _orientation_z: undefined,
      panning_model: 'equal_power',
      distance_model: 'linear',
      ref_distance: 1,
      rolloff_factor: 1,
      max_distance: 10000,
      cone_inner_angle: 360,
      cone_outer_angle: 360,
      cone_outer_gain: 0,
    };
  }

  createNode(): tone.Panner3D {
    return new tone.Panner3D({
      positionX: this.get('_position_x').value,
      positionY: this.get('_position_y').value,
      positionZ: this.get('_position_z').value,
      orientationX: this.get('_orientation_x').value,
      orientationY: this.get('_orientation_y').value,
      orientationZ: this.get('_orientation_z').value,
      panningModel: this.get('panning_model'),
      distanceModel: this.get('distance_model'),
      refDistance: this.get('ref_distance'),
      rolloffFactor: this.get('rolloff_factor'),
      maxDistance: this.get('max_distance'),
      coneInnerAngle: this.get('cone_inner_angle'),
      coneOuterAngle: this.get('cone_outer_angle'),
      coneOuterGain: this.get('cone_outer_gain'),
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.get('_position_x').setNode(this.node.positionX);
    this.get('_position_y').setNode(this.node.positionY);
    this.get('_position_z').setNode(this.node.positionZ);
    this.get('_orientation_x').setNode(this.node.orientationX);
    this.get('_orientation_y').setNode(this.node.orientationY);
    this.get('_orientation_z').setNode(this.node.orientationZ);
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _position_x: { deserialize: unpack_models as any },
    _position_y: { deserialize: unpack_models as any },
    _position_z: { deserialize: unpack_models as any },
    _orientation_x: { deserialize: unpack_models as any },
    _orientation_y: { deserialize: unpack_models as any },
    _orientation_z: { deserialize: unpack_models as any },
  };

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:panning_model', () => {
      this.node.panningModel = this.get('panning_model');
    });
    this.on('change:distance_model', () => {
      this.node.distanceModel = this.get('distance_model');
    });
    this.on('change:ref_distance', () => {
      this.node.refDistance = this.get('ref_distance');
    });
    this.on('change:rolloff_factor', () => {
      this.node.rolloffFactor = this.get('rolloff_factor');
    });
    this.on('change:max_distance', () => {
      this.node.maxDistance = this.get('max_distance');
    });
    this.on('change:cone_inner_angle', () => {
      this.node.coneInnerAngle = this.get('cone_inner_angle');
    });
    this.on('change:cone_outer_angle', () => {
      this.node.coneOuterAngle = this.get('cone_outer_angle');
    });
    this.on('change:cone_outer_gain', () => {
      this.node.coneOuterGain = this.get('cone_outer_gain');
    });
  }

  node: tone.Panner3D;

  static model_name = 'Panner3DModel';
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
    options: { model_id: string; comm: any; widget_manager: any },
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
