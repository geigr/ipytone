export function normalizeArguments(args: any, argsKeys: string[]): any[] {
  return argsKeys.map((name: string) => {
    if (args[name].value === null) {
      return undefined;
    } else {
      return args[name].value;
    }
  });
}
