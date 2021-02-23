import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import { UnitMap, UnitName } from 'tone/Tone/core/type/Units';

import {
  AudioNodeModel,
  ToneWidgetModel,
  NodeModel,
  NodeWithContextModel,
} from './widget_base';

export class InternalNodeModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: InternalNodeModel.model_name,
      _n_inputs: 1,
      _n_outputs: 1,
      _tone_class: 'ToneWithContext',
    };
  }

  static model_name = 'InternalNodeModel';
}

export class InternalAudioNodeModel extends AudioNodeModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: InternalAudioNodeModel.model_name,
      _n_inputs: 1,
      _n_outputs: 1,
      _tone_class: 'ToneAudioNode',
      _create_node: false,
    };
  }

  createNode(): tone.ToneAudioNode {
    throw new Error('Not implemented');
  }

  static model_name = 'InternalAudioNodeModel';
}

interface ParamProperties<T extends UnitName> {
  value: UnitMap[T],
  units: T,
  convert: boolean,
  minValue?: number,
  maxValue?: number,
}

export class ParamModel<T extends UnitName> extends NodeWithContextModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ParamModel.model_name,
      _create_node: true,
      _input: null,
      value: 0,
      convert: true,
      _units: 'number',
      _min_value: undefined,
      _max_value: undefined,
      overridden: false,
    };
  }

  initialize(
    attributes: Backbone.ObjectHash,
    options: { model_id: string; comm: any; widget_manager: any }
  ): void {
    super.initialize(attributes, options);

    if (this.get('_create_node')) {
      this.node = new tone.Param<T>({
        convert: this.convert,
        value: this.value,
        units: this.units,
        minValue: this.normalizeMinMax(this.get('_min_value')),
        maxValue: this.normalizeMinMax(this.get('_max_value')),
      });
      this.input.node = this.node.input;
    }
  }

  get input(): NodeModel {
    return this.get('_input');
  }

  get value(): UnitMap[T] {
    return this.get('value');
  }

  get units(): T {
    return this.get('_units');
  }

  get convert(): boolean {
    return this.get('convert');
  }

  get minValue(): number | undefined {
    return this.normalizeMinMax(this.get('_min_value'));
  }

  get maxValue(): number | undefined {
    return this.normalizeMinMax(this.get('_max_value'));
  }

  get properties(): ParamProperties<T> {
    let opts: any = { value: this.value, units: this.units, convert: this.convert };

    if(this.minValue !== undefined) {
      opts.minValue = this.minValue;
    }

    if(this.maxValue !== undefined) {
      opts.maxValue = this.maxValue;
    }

    return opts;
  }

  private normalizeMinMax(value: number | null): number | undefined {
    return value === null ? undefined : value;
  }

  setNode(node: tone.Param<T>): void {
    this.node = node;
  }

  connectInputCallback(): void {
    /**/
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:value', () => {
      this.node.value = this.get('value');
    });
    this.on('change:convert', () => {
      this.node.convert = this.get('convert');
    });
  }

  node: tone.Param<T>;

  static model_name = 'ParamModel';
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

type Connection = [AudioNodeModel, AudioNodeModel | ParamModel<any>];
type ConnectionNode = [
  tone.ToneAudioNode,
  tone.ToneAudioNode | tone.Param<any>
];

function getConnectionNodes(connections: Connection[]): ConnectionNode[] {
  return connections.map((conn: Connection) => {
    return [conn[0].node, conn[1].node];
  });
}

function getConnectionId(conn: Connection): string {
  return conn[0].model_id + '::' + conn[1].model_id;
}

function getConnectionIds(connections: Connection[]): string[] {
  return connections.map((conn: Connection) => {
    return getConnectionId(conn);
  });
}

export class AudioGraphModel extends ToneWidgetModel {
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: AudioGraphModel.model_name,
      _connections: [],
    };
  }

  get connections(): Connection[] {
    return this.get('_connections');
  }

  get connections_prev(): Connection[] {
    return this.previous('_connections');
  }

  private updateConnections(): void {
    // connect nodes for new connections
    const connAdded = this.connections.filter((other: Connection) => {
      const other_id: string = getConnectionId(other);
      const prev_ids = getConnectionIds(this.connections_prev);
      return !prev_ids.includes(other_id);
    });

    getConnectionNodes(connAdded).forEach((conn_node) => {
      conn_node[0].connect(conn_node[1]);
    });

    // disconnect nodes for removed connections
    const connRemoved = this.connections_prev.filter((other: Connection) => {
      const other_id: string = getConnectionId(other);
      const current_ids = getConnectionIds(this.connections_prev);
      return !current_ids.includes(other_id);
    });

    getConnectionNodes(connRemoved).forEach((conn_node) => {
      conn_node[0].disconnect(conn_node[1]);
    });

    // callbacks of updated destination nodes
    connAdded.concat(connRemoved).forEach((conn: Connection) => {
      conn[1].connectInputCallback();
    });
  }

  initEventListeners(): void {
    super.initEventListeners();

    this.on('change:_connections', this.updateConnections, this);
  }

  static serializers: ISerializers = {
    ...ToneWidgetModel.serializers,
    _connections: { deserialize: unpack_models as any },
  };

  static model_name = 'AudioGraphModel';
}
