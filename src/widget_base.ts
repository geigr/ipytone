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
      _create_node: false,
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

    // By default, create a Tone node for widgets constructed on the Python side
    // and do not create a Tone node for widgets constructed on the JS side
    // (in the latter case, we want to assign an existing Tone node to the new widget).
    if (this.get('_create_node')) {
      this.node = this.createNode();
      this.setModelAttributesFromNode();
    } else {
      (this.node as any) = null;
    }

    // create new models for Tone sub-nodes and save this model
    Promise.all(this.createModels()).then(() => {
      this.save_changes();
    });

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

  connectInputCallback(): void {
    /**/
  }

  node: tone.ToneAudioNode;

  abstract createNode(): tone.ToneAudioNode;

  setModelAttributesFromNode(): void {
    this.set('number_of_inputs', this.node.numberOfInputs);
    this.set('number_of_outputs', this.node.numberOfOutputs);
    this.save_changes();
  }

  createModels(): Promise<AudioNodeModel>[] {
    return [];
  }

  // Create a new instance of a given model class from a given Tone audio node
  // and assign it to an attribute of this model instance.
  newModel(
    model_name: string,
    attribute_name: string,
    node: tone.ToneAudioNode
  ): Promise<AudioNodeModel> {
    const model: any = this.widget_manager.new_widget({
      model_name: model_name,
      model_module: this.get('_model_module'),
      model_module_version: this.get('_model_module_version'),
      view_name: '',
      view_module: '',
      view_module_version: '',
    });

    model.then((m: any) => {
      m.node = node;
      m.setModelAttributesFromNode();
      this.set(attribute_name, m);
      return m;
    });

    return model;
  }

  replaceNodeBy(node: tone.ToneAudioNode): void {
    this.node.dispose();
    this.node = node;
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _in_nodes: { deserialize: unpack_models as any },
    _out_nodes: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}
