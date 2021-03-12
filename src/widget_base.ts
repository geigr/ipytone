import {
  WidgetModel,
  ISerializers,
  unpack_models,
} from '@jupyter-widgets/base';

import * as tone from 'tone';

// import * as tone_base from 'tone/Tone/core/Tone';

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

export class NativeAudioNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NativeAudioNodeModel.model_name,
      _n_inputs: 1,
      _n_outputs: 1,
      type: '',
    };
  }

  connectInputCallback(): void {
    /**/
  }

  setNode(node: AudioNode): void {
    this.node = node;
  }

  node: AudioNode;

  static model_name = 'NativeAudioNodeModel';
}

export class NativeAudioParamModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: NativeAudioParamModel.model_name,
      type: '',
    };
  }

  connectInputCallback(): void {
    /**/
  }

  setNode(node: AudioParam): void {
    this.node = node;
  }

  node: AudioParam;

  static model_name = 'NativeAudioParamModel';
}

export abstract class ToneObjectModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ToneObjectModel.model_name,
      _disposed: false,
    };
  }

  setNode(node: any): void {
    this.node = node;
  }

  get disposed(): boolean {
    return this.get('_disposed');
  }

  dispose(): void {
    // Tone.js calls dispose internally for sub-nodes such as input, output, etc.
    // so we need to check if the node is already disposed
    if (!this.node.disposed) {
      this.node.dispose();
    }
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_disposed', this.dispose, this);
  }

  node: any; //tone_base.Tone | tone.ToneAudioNode | tone.Param<any> | AudioNode | AudioParam | undefined;

  static model_name = 'ToneObjectModel';
}

export class NodeWithContextModel extends ToneObjectModel {
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
      channel_count: 2,
      channel_count_mode: 'max',
      channel_interpretation: 'speakers',
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = this.createNode();
      this.setNodeChannels();
      this.setInputOutputNodes();
      this.setSubNodes();
    }
  }

  get input(): ToneObjectModel | NativeAudioNodeModel | NativeAudioParamModel {
    return this.get('_input');
  }

  get output(): ToneObjectModel | NativeAudioNodeModel {
    return this.get('_output');
  }

  connectInputCallback(): void {
    /**/
  }

  node: tone.ToneAudioNode;

  abstract createNode(): tone.ToneAudioNode;

  setNode(node: tone.ToneAudioNode): void {
    this.node = node;
    this.setNodeChannels();
    this.setInputOutputNodes();
    this.setSubNodes();
  }

  setNodeChannels(): void {
    this.node.channelCount = this.get('channel_count');
    this.node.channelCountMode = this.get('channel_count_mode');
    this.node.channelInterpretation = this.get('channel_interpretation');
  }

  private setInputOutputNodes(): void {
    if (this.input !== null) {
      this.input.setNode(this.node.input);
    }
    if (this.output !== null) {
      this.output.setNode(this.node.output as any);
    }
  }

  setSubNodes(): void {
    /**/
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:channel_count', this.setNodeChannels, this);
    this.on('change:channel_count_mode', this.setNodeChannels, this);
    this.on('change:channel_interpretation', this.setNodeChannels, this);
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _input: { deserialize: unpack_models as any },
    _output: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioNodeModel';
}
