import { NodeWithContextModel } from './widget_base';

export type callbackArgs = { [key: string]: { eval: boolean; value: any } };

export type callbackItem = {
  method: string;
  callee: string;
  model: NodeWithContextModel;
  args: callbackArgs;
  arg_keys: string[];
};

/*
 * Replace null argument values by undefined so that it works well
 * with Tone.js optional arguments.
 */
export function normalizeArguments(args: any, argsKeys: string[]): any[] {
  return argsKeys.map((name: string) => {
    if (args[name].value === null) {
      return undefined;
    } else {
      return args[name].value;
    }
  });
}
