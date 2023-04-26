import { NodeWithContextModel } from './widget_base';

export function assert(statement: boolean, error: string): asserts statement {
  if (!statement) {
    throw new Error(error);
  }
}

export type callbackArgs = { [key: string]: { eval: boolean; value: any } };

export type callbackItem = {
  method: string;
  callee: string;
  model: NodeWithContextModel;
  args: callbackArgs;
  arg_keys: string[];
};

/*
 * Return an array of argument values from an object.
 *
 * Sort values according to a given array of argument names.
 * Maybe skip some given elements.
 *
 * Replace null argument values by undefined so that it works well
 * with Tone.js optional arguments.
 */
export function normalizeArguments(
  args: any,
  argsKeys: string[],
  skipArgs: string[] = [],
): any[] {
  return argsKeys
    .filter((name: string) => {
      if (skipArgs.includes(name)) {
        return false;
      }
      return true;
    })
    .map((name: string) => {
      if (args[name].value === null) {
        return undefined;
      } else {
        return args[name].value;
      }
    });
}
