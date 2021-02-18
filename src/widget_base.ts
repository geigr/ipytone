import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

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

export abstract class AudioNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      name: '',
      _in_nodes: [],
      _out_nodes: [],
      number_of_inputs: 1,
      number_of_outputs: 1,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    this.node = this.createNode();

    this.set('number_of_inputs', this.node.numberOfInputs);
    this.set('number_of_outputs', this.node.numberOfOutputs);
    this.save_changes();

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

    // callbacks of updated destination nodes
    nodesAdded.concat(nodesRemoved).forEach((model: AudioNodeModel) => {
      model.connectInputCallback();
    });
  }

  protected connectInputCallback(): void {
    /**/
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
