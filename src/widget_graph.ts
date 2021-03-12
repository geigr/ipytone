import { ISerializers, unpack_models } from '@jupyter-widgets/base';

import * as tone from 'tone';

import {
  AudioNodeModel,
  ToneWidgetModel,
  NativeAudioNodeModel,
  NativeAudioParamModel,
} from './widget_base';

import { ParamModel } from './widget_core';

function isNative(obj: any): boolean {
  return obj instanceof AudioNode || obj instanceof AudioParam;
}

function isDisposed(obj: any): boolean {
  return !isNative(obj) && obj.disposed;
}

type Connection = [
  AudioNodeModel | NativeAudioNodeModel,
  (
    | AudioNodeModel
    | NativeAudioNodeModel
    | ParamModel<any>
    | NativeAudioParamModel
  ),
  number,
  number
];

type ConnectionNode = [
  tone.ToneAudioNode | AudioNode,
  tone.ToneAudioNode | AudioNode | tone.Param<any> | AudioParam,
  number,
  number
];

function getConnectionNodes(connections: Connection[]): ConnectionNode[] {
  return connections.map((conn: Connection) => {
    return [conn[0].node, conn[1].node, conn[2], conn[3]];
  });
}

function getConnectionId(conn: Connection): string {
  return (
    conn[0].model_id + '::' + conn[1].model_id + '::' + conn[2] + '::' + conn[3]
  );
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
      conn_node[0].connect(conn_node[1] as any, conn_node[2], conn_node[3]);
    });

    // disconnect nodes for removed connections
    const connRemoved = this.connections_prev.filter((other: Connection) => {
      const other_id: string = getConnectionId(other);
      const current_ids = getConnectionIds(this.connections_prev);
      return !current_ids.includes(other_id);
    });

    getConnectionNodes(connRemoved).forEach((conn_node) => {
      const src = conn_node[0];
      const dest = conn_node[1];

      // Disposed nodes should have been already disconnected by Tone.js
      if (!isDisposed(src) || !isDisposed(dest)) {
        const outputNum = conn_node[2];
        const inputNum = conn_node[3];
        src.disconnect(dest, outputNum, inputNum);
      }
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
