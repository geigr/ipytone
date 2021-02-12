// Copyright (c) Benoit Bovy
// Distributed under the terms of the Modified BSD License.

import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

// import * as source from 'tone/Tone/source/Source';

import { MODULE_NAME, MODULE_VERSION } from './version';

abstract class ToneWidgetModel extends WidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_module: ToneWidgetModel.model_module,
      _model_module_version: ToneWidgetModel.model_module_version,
    };
  }

  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}

abstract class AudioNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      name: '',
      _in_nodes: [],
      _out_nodes: [],
    };
  }

  initialize(attributes: Backbone.ObjectHash, options: any): void {
    super.initialize(attributes, options);

    this.node = this.createNode();

    this.initEventListeners();
  }

  initEventListeners(): void {
    this.on('change:_out_nodes', this.updateConnections, this);
  }

  private getToneAudioNodes(models: AudioNodeModel[]): tone.ToneAudioNode[] {
    return models.map((model: AudioNodeModel) => {
      return model.node;
    });
  }

  private updateConnections(): void {
    // connect new nodes (if any)
    const nodesAdded = this.get('_out_nodes').filter(
      (other: AudioNodeModel) => {
        return !this.previous('_out_nodes').includes(other);
      }
    );

    this.node.fan(...this.getToneAudioNodes(nodesAdded));

    // disconnect nodes that have been removed (if any)
    const nodesRemoved = this.previous('_out_nodes').filter(
      (other: AudioNodeModel) => {
        return !this.get('_out_nodes').includes(other);
      }
    );

    this.getToneAudioNodes(nodesRemoved).forEach((node) => {
      this.node.disconnect(node);
    });
  }

  node: tone.ToneAudioNode;

  abstract createNode(): tone.ToneAudioNode;

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _in_nodes: { deserialize: unpack_models as any },
    _out_nodes: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}

abstract class SourceModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SourceModel.model_name,
      mute: false,
      state: 'stopped',
      volume: -16,
    };
  }

  get mute(): boolean {
    return this.get('mute');
  }

  get volume(): number {
    return this.get('volume');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:mute', () => {
      this.node.mute = this.mute;
    });
    this.on('change:state', this.startStopNode, this);
    this.on('change:volume', () => {
      this.node.volume.value = this.volume;
    });
  }

  private startStopNode(): void {
    if (this.get('state') === 'started') {
      this.node.start(0);
    } else {
      this.node.stop(0);
    }
  }

  // FIXME: typescript error: property not assignable to the same property in base type
  // node: source.Source<source.SourceOptions>;
  node: any;

  static model_name = 'SourceModel';
}

export class DestinationModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: DestinationModel.model_name,
      mute: false,
      volume: -16,
    };
  }

  createNode(): tone.ToneAudioNode {
    return tone.getDestination();
  }

  get mute(): boolean {
    return this.get('mute');
  }

  get volume(): number {
    return this.get('volume');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:mute', () => {
      this.node.mute = this.mute;
    });
    this.on('change:volume', () => {
      this.node.volume.value = this.volume;
    });
  }

  node: typeof tone.Destination;

  static model_name = 'DestinationModel';
}

export class OscillatorModel extends SourceModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: OscillatorModel.model_name,
      type: 'sine',
      frequency: 440,
      detune: 0,
      volume: -16,
    };
  }

  createNode(): tone.Oscillator {
    return new tone.Oscillator({
      type: this.get('type'),
      frequency: this.get('frequency'),
      volume: this.get('volume'),
    });
  }

  get type(): tone.ToneOscillatorType {
    return this.get('type');
  }

  get frequency(): number {
    return this.get('frequency');
  }

  get detune(): number {
    return this.get('detune');
  }

  get volume(): number {
    return this.get('volume');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:frequency', () => {
      this.node.frequency.value = this.frequency;
    });
    this.on('change:detune', () => {
      this.node.detune.value = this.detune;
    });
    this.on('change:volume', () => {
      this.node.volume.value = this.volume;
    });
    this.on('change:type', () => {
      this.node.type = this.type;
    });
  }

  node: tone.Oscillator;

  static model_name = 'OscillatorModel';
}
