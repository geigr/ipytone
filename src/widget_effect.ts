import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { normalizeArguments } from './utils';

import { AudioNodeModel } from './widget_base';

import { CrossFadeModel } from './widget_channel';

import { ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

abstract class EffectModel extends AudioNodeModel {
  // Returns the wet value from the output node model.
  // This allows to pass it to the constructor of the
  // Tone.Effect subclasses.
  get wetFromModel(): number {
    return (this.output as CrossFadeModel).fade.value;
  }

  static model_name = 'EffectModel';
}

export class DistortionModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: DistortionModel.model_name,
      distortion: 0.4,
      oversample: 'none',
    };
  }

  createNode(): tone.Distortion {
    return new tone.Distortion({
      distortion: this.get('distortion'),
      oversample: this.get('oversample'),
      wet: this.wetFromModel,
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:distortion', () => {
      this.node.distortion = this.get('distortion');
    });
    this.on('change:oversample', () => {
      this.node.oversample = this.get('oversample');
    });
  }

  node: tone.Distortion;

  static model_name = 'DistortionModel';
}

export class FeedbackDelayModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: FeedbackDelayModel.model_name,
      _max_delay: 1,
      _delay_time: undefined,
      _feedback: undefined,
    };
  }

  createNode(): tone.FeedbackDelay {
    return new tone.FeedbackDelay({
      delayTime: this.delayTime.value,
      feedback: this.feedback.value,
      maxDelay: this.get('_max_delay'),
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.delayTime.setNode(this.node.delayTime);
    this.feedback.setNode(this.node.feedback);
  }

  get delayTime(): ParamModel<'time'> {
    return this.get('_delay_time');
  }

  get feedback(): ParamModel<'normalRange'> {
    return this.get('_feedback');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _delay_time: { deserialize: unpack_models as any },
    _feedback: { deserialize: unpack_models as any },
  };

  node: tone.FeedbackDelay;

  static model_name = 'FeedbackDelayModel';
}

export class FrequencyShifterModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: FrequencyShifterModel.model_name,
      _frequency: undefined,
    };
  }

  createNode(): tone.FrequencyShifter {
    return new tone.FrequencyShifter({
      frequency: this.frequency.value,
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
  };

  node: tone.FrequencyShifter;

  static model_name = 'FrequencyShifterModel';
}

export class PingPongDelayModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PingPongDelayModel.model_name,
      _max_delay: 1,
      _delay_time: undefined,
      _feedback: undefined,
    };
  }

  createNode(): tone.PingPongDelay {
    return new tone.PingPongDelay({
      delayTime: this.delayTime.value,
      feedback: this.feedback.value,
      maxDelay: this.get('_max_delay'),
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.delayTime.setNode(this.node.delayTime);
    this.feedback.setNode(this.node.feedback);
  }

  get delayTime(): SignalModel<'time'> {
    return this.get('_delay_time');
  }

  get feedback(): SignalModel<'normalRange'> {
    return this.get('_feedback');
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _delay_time: { deserialize: unpack_models as any },
    _feedback: { deserialize: unpack_models as any },
  };

  node: tone.PingPongDelay;

  static model_name = 'PingPongDelayModel';
}

export class PitchShiftModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PitchShiftModel.model_name,
      pitch: 0,
      window_size: 0.1,
      _delay_time: undefined,
      _feedback: undefined,
    };
  }

  createNode(): tone.PitchShift {
    return new tone.PitchShift({
      pitch: this.get('pitch'),
      windowSize: this.get('window_size'),
      delayTime: this.delayTime.value,
      feedback: this.feedback.value,
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.delayTime.setNode(this.node.delayTime);
    this.feedback.setNode(this.node.feedback);
  }

  get delayTime(): ParamModel<'time'> {
    return this.get('_delay_time');
  }

  get feedback(): ParamModel<'normalRange'> {
    return this.get('_feedback');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:pitch', () => {
      this.node.pitch = this.get('pitch');
    });
    this.on('change:window_size', () => {
      this.node.windowSize = this.get('window_size');
    });
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _delay_time: { deserialize: unpack_models as any },
    _feedback: { deserialize: unpack_models as any },
  };

  node: tone.PitchShift;

  static model_name = 'PitchShiftModel';
}

export class ReverbModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ReverbModel.model_name,
      decay: 1.5,
      pre_delay: 0.01,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any },
  ): void {
    // special case: reverb impulse response is generated asynchronuously
    if (this.get('_create_node')) {
      this.node = this.createNode();
      this.node.ready.then(() => {
        this.input.setNode(this.node.input);
        this.output.setNode(this.node.output as any);
      });
      this.set('_create_node', false);
      this.save_changes();
    }

    super.initialize(attributes, options);
  }

  createNode(): tone.Reverb {
    return new tone.Reverb({
      decay: this.get('decay'),
      preDelay: this.get('pre_delay'),
      wet: this.wetFromModel,
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:decay', () => {
      this.node.decay = this.get('decay');
    });
    this.on('change:pre_delay', () => {
      this.node.preDelay = this.get('pre_delay');
    });
  }

  node: tone.Reverb;

  static model_name = 'ReverbModel';
}

export class TremoloModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: TremoloModel.model_name,
      _frequency: undefined,
      _depth: undefined,
      type: 'sine',
      spread: 180,
    };
  }

  createNode(): tone.Tremolo {
    return new tone.Tremolo({
      frequency: this.frequency.value,
      depth: this.depth.value,
      type: this.get('type'),
      spread: this.get('spread'),
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
    this.depth.setNode(this.node.depth);
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get depth(): SignalModel<'normalRange'> {
    return this.get('_depth');
  }

  get type(): tone.ToneOscillatorType {
    return this.get('type');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:spread', () => {
      this.node.spread = this.get('spread');
    });
    this.on('change:type', () => {
      this.node.type = this.type;
    });
    this.on('msg:custom', this.handleMsg, this);
  }

  private handleMsg(command: any, buffers: any): void {
    if (command.event === 'trigger') {
      const argsArray = normalizeArguments(command.args, command.arg_keys);
      (this.node as any)[command.method](...argsArray);
    }
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _depth: { deserialize: unpack_models as any },
  };

  node: tone.Tremolo;

  static model_name = 'TremoloModel';
}

export class VibratoModel extends EffectModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: VibratoModel.model_name,
      _max_delay: 0.005,
      _frequency: undefined,
      _depth: undefined,
      type: 'sine',
    };
  }

  createNode(): tone.Vibrato {
    return new tone.Vibrato({
      frequency: this.frequency.value,
      depth: this.depth.value,
      type: this.get('type'),
      maxDelay: this.get('_max_delay'),
      wet: this.wetFromModel,
    });
  }

  setSubNodes(): void {
    super.setSubNodes();
    this.frequency.setNode(this.node.frequency);
    this.depth.setNode(this.node.depth);
  }

  get frequency(): SignalModel<'frequency'> {
    return this.get('_frequency');
  }

  get depth(): ParamModel<'normalRange'> {
    return this.get('_depth');
  }

  get type(): tone.ToneOscillatorType {
    return this.get('type');
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:type', () => {
      this.node.type = this.type;
    });
  }

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _depth: { deserialize: unpack_models as any },
  };

  node: tone.Vibrato;

  static model_name = 'VibratoModel';
}
