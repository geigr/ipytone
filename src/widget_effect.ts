import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { AudioNodeModel } from './widget_base';

import { ParamModel } from './widget_core';

import { SignalModel } from './widget_signal';

export class FeedbackDelayModel extends AudioNodeModel {
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

export class PingPongDelayModel extends AudioNodeModel {
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

export class VibratoModel extends AudioNodeModel {
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

  static serializers: ISerializers = {
    ...AudioNodeModel.serializers,
    _frequency: { deserialize: unpack_models as any },
    _depth: { deserialize: unpack_models as any },
  };

  node: tone.Vibrato;

  static model_name = 'VibratoModel';
}
