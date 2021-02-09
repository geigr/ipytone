// Copyright (c) Benoit Bovy
// Distributed under the terms of the Modified BSD License.

import {
  WidgetModel, ISerializers
} from '@jupyter-widgets/base';

import * as Tone from 'tone';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';

// Import the CSS
// import '../css/widget.css'


export
class OscillatorModel extends WidgetModel {
  defaults() {
    return {...super.defaults(),
      _model_name: OscillatorModel.model_name,
      _model_module: OscillatorModel.model_module,
      _model_module_version: OscillatorModel.model_module_version,
      type: 'sine',
      frequency: 440,
      detune: 0,
      volume: -16,
      started: false
    };
  }

  initialize(attributes: any, options: any) {
    super.initialize(attributes, options);

    this._osc = new Tone.Oscillator({
      "type" : this.get('type'),
      "frequency" : this.get('frequency'),
      "volume" : this.get('volume')
    }).toMaster();

    this.on('change:frequency', this.changeFrequency, this);
    this.on('change:detune', this.changeDetune, this);
    this.on('change:volume', this.changeVolume, this);
    this.on('change:type', this.changeType, this);
    this.on('change:started', this.togglePlay, this);
  }

  static serializers: ISerializers = {
      ...WidgetModel.serializers,
      // Add any extra serializers here
    }

  private changeFrequency() {
    this._osc.frequency.value = this.get('frequency');
  }

  private changeDetune() {
    this._osc.detune.value = this.get('detune');
  }

  private changeVolume() {
    this._osc.volume.value = this.get('volume');
  }

  private changeType() {
    this._osc.type = this.get('type');
  }

  private togglePlay () {
    console.log(this._osc.state);
    if (this.get('started')) {
      this._osc.start(0);
    }
    else {
      this._osc.stop(0);
    }
    console.log(this._osc.state);
  }

  static model_name = 'OscillatorModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = null;
  static view_module = null;
  static view_module_version = MODULE_VERSION;

  private _osc!: Tone.Oscillator;
}



export
class TimeModel extends WidgetModel {
  defaults() {
    return {...super.defaults(),
      _model_name: TimeModel.model_name,
      _model_module: TimeModel.model_module,
      _model_module_version: TimeModel.model_module_version,
      time: 0
    };
  }

  initialize(attributes: any, options: any) {
    super.initialize(attributes, options);

    Tone.Transport.scheduleRepeat((time) => {
        this.set('time', time);
        this.save_changes();
    }, "4n");

    Tone.Transport.start();
  }

  static serializers: ISerializers = {
      ...WidgetModel.serializers,
      // Add any extra serializers here
    }

  static model_name = 'TimeModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = null;
  static view_module = null;
  static view_module_version = MODULE_VERSION;
}
