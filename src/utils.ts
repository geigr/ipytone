import { NodeWithContextModel } from './widget_base';

import * as tone from 'tone';

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

export type ObserveEvent = {
  id: number | ReturnType<typeof setInterval>;
  transport: boolean;
};

export type ObserveEventMap = { [hash: number]: ObserveEvent };

/*
 * Used by ParamModel / SignalModel / (TODO: MeterModel) to
 * schedule sync of `current_value` trait on regular intervals,
 * either along tone.Transport's timeline or on the current context
 * time.
 */
export function scheduleObserve(
  obj: NodeWithContextModel,
  transport: boolean,
  repeatInterval: number | string
): ObserveEvent {
  let eid: number | ReturnType<typeof setInterval>;

  if (transport) {
    eid = tone.Transport.scheduleRepeat((time) => {
      obj.set('current_value', obj.node.getValueAtTime(time));
      obj.save_changes();
    }, repeatInterval);
  } else {
    eid = setInterval(() => {
      obj.set('current_value', obj.node.value);
      obj.save_changes();
    }, (repeatInterval as number) * 1000);
  }

  return { id: eid, transport: transport };
}

/*
 * Cancel scheduled syncs created by `scheduleObserve`.
 */
export function scheduleUnobserve(
  hashHandler: number,
  eventMap: ObserveEventMap
): void {
  const event = eventMap[hashHandler];

  if (event.transport) {
    tone.Transport.cancel(event.id as number);
  } else {
    clearInterval(event.id as ReturnType<typeof setInterval>);
  }
}
