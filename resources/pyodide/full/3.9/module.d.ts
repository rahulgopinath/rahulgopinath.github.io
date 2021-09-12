/**
 *
 * @param {undefined|(() => string)} stdin
 * @param {undefined|((text: string) => void)} stdout
 * @param {undefined|((text: string) => void)} stderr
 */
export function setStandardStreams(stdin: undefined | (() => string), stdout: (text: string) => void, stderr: (text: string) => void): void;
/**
 * The Emscripten Module.
 *
 * @private @type {import('emscripten').Module}
 */
export let Module: any;
