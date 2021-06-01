import { ISerializers } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import {
  ArrayProperty,
  dataarray_serialization,
  getArrayProp,
} from './serializers';

export class EnvelopeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: EnvelopeModel.model_name,
      attack: 0.01,
      decay: 0.1,
      sustain: 1,
      release: 0.5,
      attack_curve: 'linear',
      decay_curve: 'exponential',
      release_curve: 'exponential',
      array: null,
      array_length: 1024,
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

  get array(): ArrayProperty {
    return getArrayProp(this.get('array'));
  }

  set array(value: ArrayProperty) {
    // avoid infinite event listener loop
    this.set('array', value, { silent: true });
  }

  createNode(): tone.Envelope {
    return new tone.Envelope({
      attack: this.get('attack'),
      decay: this.get('decay'),
      sustain: this.get('sustain'),
      release: this.get('release'),
      attackCurve: this.get('attack_curve'),
      decayCurve: this.get('decay_curve'),
      releaseCurve: this.get('release_curve'),
    });
  }

  setNode(node: tone.Envelope): void {
    super.setNode(node);
    this.maybeSetArray();
  }

  maybeSetArray(): void {
    if (this.get('sync_array')) {
      this.node.asArray(this.get('array_length')).then((arr) => {
        this.array = arr;
        this.save_changes();
      });
    }
  }

  updateEnvelope(trait_name: string, node_property: string): void {
    (this.node as any)[node_property] = this.get(trait_name);
    this.maybeSetArray();
  }

  handleMsg(command: any, buffers: any): void {
    switch (command.event) {
      case 'triggerAttack':
        this.node.triggerAttack();
        break;
      case 'triggerRelease':
        this.node.triggerRelease();
        break;
      case 'triggerAttackRelease':
        this.node.triggerAttackRelease(command.duration);
        break;
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:attack', () => this.updateEnvelope('attack', 'attack'));
    this.on('change:decay', () => this.updateEnvelope('decay', 'decay'));
    this.on('change:sustain', () => this.updateEnvelope('sustain', 'sustain'));
    this.on('change:release', () => this.updateEnvelope('release', 'release'));
    this.on('change:attack_curve', () =>
      this.updateEnvelope('attack_curve', 'attackCurve')
    );
    this.on('change:decay_curve', () =>
      this.updateEnvelope('decay_curve', 'decayCurve')
    );
    this.on('change:release_curve', () =>
      this.updateEnvelope('release_curve', 'releaseCurve')
    );

    this.on('msg:custom', this.handleMsg.bind(this));
  }

  node: tone.Envelope;

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    array: dataarray_serialization,
  };

  static model_name = 'EnvelopeModel';
}
