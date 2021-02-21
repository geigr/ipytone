import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

import { MODULE_NAME, MODULE_VERSION } from './version';

export abstract class ToneWidgetModel extends WidgetModel {
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

export abstract class NodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NodeModel.model_name,
    };
  }

  setNode(node: any): void {
    this.node = node;
  }

  node: any;

  static model_name = 'NodeModel';
}

export abstract class AudioNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      name: '',
      _create_node: true,
      _input: null,
      _output: null,
      _in_nodes: [],
      _out_nodes: [],
    };
  }

  initialize(attributes: Backbone.ObjectHash, options: any): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = this.createNode();
      this.setInputOutputNodes();
      this.setSubNodes();
    }

    this.initEventListeners();
  }

  get input(): NodeModel {
    return this.get('_input');
  }

  get output(): NodeModel {
    return this.get('_output');
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

  setNode(node: tone.ToneAudioNode): void {
    this.node = node;
    this.setInputOutputNodes();
    this.setSubNodes();
  }

  private setInputOutputNodes(): void {
    if (this.input !== null) {
      this.input.node = this.node.input;
    }
    if (this.output !== null) {
      this.output.node = this.node.output;
    }
  }

  setSubNodes(): void {
    /**/
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _input: { deserialize: unpack_models as any },
    _output: { deserialize: unpack_models as any },
    _in_nodes: { deserialize: unpack_models as any },
    _out_nodes: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}
