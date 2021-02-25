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

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    this.initEventListeners();
  }

  initEventListeners(): void {
    /**/
  }

  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}

export abstract class NodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NodeModel.model_name,
      _disposed: false,
    };
  }

  setNode(node: any): void {
    this.node = node;
  }

  node: any;

  static model_name = 'NodeModel';
}

export class NodeWithContextModel extends NodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NodeWithContextModel.model_name,
      name: '',
    };
  }

  static model_name = 'NodeWithContextModel';
}

export abstract class AudioNodeModel extends NodeWithContextModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      _create_node: true,
      _input: null,
      _output: null,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = this.createNode();
      this.setInputOutputNodes();
      this.setSubNodes();
    }
  }

  get input(): NodeModel {
    return this.get('_input');
  }

  get output(): NodeModel {
    return this.get('_output');
  }

  connectInputCallback(): void {
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

  dispose(): void {
    // Tone.js also calls dispose internally for input and output
    // so we need to check if the node is already disposed
    if (!this.node.disposed) {
      this.node.dispose();
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_disposed', this.dispose, this);
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _input: { deserialize: unpack_models as any },
    _output: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}
