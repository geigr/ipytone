import { ManagerBase, unpack_models, WidgetModel } from '@jupyter-widgets/base';

interface ReceivedSerializedArray {
  shape: number[];
  dtype: string;
  buffer: DataView | DataView[];
}

type SerializedDataArray = null | string | ReceivedSerializedArray;
type DeserializedDataArray =
  | null
  | Promise<any>
  | WidgetModel
  | Float32Array
  | Float32Array[];
export type ArrayProperty = null | Float32Array | Float32Array[];

export function getArrayProp(obj: DeserializedDataArray): ArrayProperty {
  if (obj === null) {
    return null;
  } else if (obj instanceof WidgetModel) {
    // we assume it is a NDArrayModel
    // TODO: handle Promise?
    const ndArray = (obj as any).getNDArray();
    if (ndArray.shape.length == 1) {
      return new Float32Array(ndArray.data);
    } else {
      const arrays: Float32Array[] = [];

      return arrays;
    }
  } else {
    return obj as ArrayProperty;
  }
}

function concat(arrays: Float32Array[], size: number): Float32Array {
  const array = new Float32Array(arrays.length * size);
  let offset = 0;

  for (const arr of arrays) {
    array.set(arr, offset);
    offset += size;
  }

  return array;
}

function split(array: Float32Array, shape: number[]): Float32Array[] {
  const arrays: Float32Array[] = [];
  let offset = 0;
  const size = shape[1];
  const end = size;

  for (let i = 0; i < shape[0]; i++) {
    arrays.push(array.subarray(offset, end));
    offset = end;
  }

  return arrays;
}

function deserializeArray(
  value: any,
  manager?: ManagerBase<any>
): Float32Array | Float32Array[] {
  const arr = new Float32Array(value.buffer.buffer);

  if (value.shape.length == 1) {
    return arr;
  } else {
    return split(arr, value.shape);
  }
}

function deserializeDataArray(
  value: SerializedDataArray,
  manager?: ManagerBase<any>
): DeserializedDataArray {
  if (value === null) {
    return null;
  } else if (typeof value === 'string') {
    return unpack_models(value, manager as ManagerBase<any>);
  } else {
    return deserializeArray(value, manager);
  }
}

function serializeDataArray(
  obj: DeserializedDataArray,
  _widget?: WidgetModel
): any {
  if (obj === null) {
    return null;
  } else if (obj instanceof WidgetModel) {
    return 'IPY_MODEL_' + obj.model_id;
  } else if (obj instanceof Float32Array) {
    return { shape: obj.length, dtype: 'float32', buffer: obj };
  } else {
    const arrays = obj as Float32Array[];
    const size = arrays[0].length;
    const array = concat(arrays, size);
    const shape = [arrays.length, size];
    return { shape: shape, dtype: 'float32', buffer: array };
  }
}

export const dataarray_serialization = {
  deserialize: deserializeDataArray,
  serialize: serializeDataArray,
};
