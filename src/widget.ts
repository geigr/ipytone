// Copyright (c) Benoit Bovy
// Distributed under the terms of the Modified BSD License.

import {
  WidgetModel
} from '@jupyter-widgets/base';

import {
  Oscillator, ToneAudioNode, Destination, getDestination
} from 'tone';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';

// Import the CSS
// import '../css/widget.css'


abstract class _ToneWidgetModel extends WidgetModel {

  defaults () {
    return {...super.defaults(),
      _model_module: _ToneWidgetModel.model_module,
      _model_module_version: _ToneWidgetModel.model_module_version,
    };
  }

  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;

}


abstract class AudioNodeModel extends _ToneWidgetModel {

  defaults() {
    return {...super.defaults(),
      _model_name: AudioNodeModel.model_name,
      inputs: [],
      outputs: [],
    };
  }

  initialize (attributes: any, options: any) {
    super.initialize(attributes, options);

    this.node = this.createNode();

    // TODO: remove this
    this.node.toDestination();

    this.initEventListeners();
  }

  initEventListeners() : void {
  }

  node: ToneAudioNode;

  abstract createNode() : ToneAudioNode;

  static model_name = 'AudioNodeModel';
}


export
class DestinationModel extends AudioNodeModel {
  defaults() {
    return {...super.defaults(),
      _model_name: DestinationModel.model_name,
      mute: false,
      volume: -16
    };
  }

  createNode () {
    return getDestination();
  }

  get mute () {
    return this.get('mute');
  }

  get volume () {
    return this.get('volume');
  }

  initEventListeners () : void {
    super.initEventListeners();

    this.on('change:mute', () => { this.node.mute = this.mute; });
    this.on('change:volume', () => { this.node.volume.value = this.volume; });
  }

  node: typeof Destination;

  static model_name = 'DestinationModel';
}


export
class OscillatorModel extends AudioNodeModel {
  defaults() {
    return {...super.defaults(),
      _model_name: OscillatorModel.model_name,
      type: 'sine',
      frequency: 440,
      detune: 0,
      volume: -16,
      started: false
    };
  }

  createNode () {
    return new Oscillator({
      "type" : this.type,
      "frequency" : this.frequency,
      "volume" : this.volume
    });
  }

  get type () {
    return this.get('type');
  }

  get frequency () {
    return this.get('frequency');
  }

  get detune () {
    return this.get('detune');
  }

  get volume () {
    return this.get('volume');
  }

  initEventListeners () : void {
    super.initEventListeners();

    this.on('change:frequency', () => { this.node.frequency.value = this.frequency; });
    this.on('change:detune', () => { this.node.detune.value = this.detune; });
    this.on('change:volume', () => { this.node.volume.value = this.volume; });
    this.on('change:type', () => { this.node.type = this.type; });
    this.on('change:started', this.togglePlay, this);
  }

  node: Oscillator;

  private togglePlay () {
    console.log(this.node.state);
    if (this.get('started')) {
      this.node.start(0);
    }
    else {
      this.node.stop(0);
    }
    console.log(this.node.state);
  }

  static model_name = 'OscillatorModel';
}
