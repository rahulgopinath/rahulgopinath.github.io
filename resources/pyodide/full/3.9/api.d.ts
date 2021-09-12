/**
 * Runs a string of Python code from Javascript.
 *
 * The last part of the string may be an expression, in which case, its value
 * is returned.
 *
 * @param {string} code Python code to evaluate
 * @param {PyProxy} globals An optional Python dictionary to use as the globals.
 *        Defaults to :any:`pyodide.globals`. Uses the Python API
 *        :any:`pyodide.eval_code` to evaluate the code.
 * @returns {Py2JsResult} The result of the Python code translated to Javascript. See the
 *          documentation for :any:`pyodide.eval_code` for more info.
 */
export function runPython(code: string, globals?: PyProxy): Py2JsResult;
/**
 * @callback LogFn
 * @param {string} msg
 * @returns {void}
 * @private
 */
/**
 * Inspect a Python code chunk and use :js:func:`pyodide.loadPackage` to install
 * any known packages that the code chunk imports. Uses the Python API
 * :func:`pyodide.find\_imports` to inspect the code.
 *
 * For example, given the following code as input
 *
 * .. code-block:: python
 *
 *    import numpy as np x = np.array([1, 2, 3])
 *
 * :js:func:`loadPackagesFromImports` will call
 * ``pyodide.loadPackage(['numpy'])``.
 *
 * @param {string} code The code to inspect.
 * @param {LogFn=} messageCallback The ``messageCallback`` argument of
 * :any:`pyodide.loadPackage` (optional).
 * @param {LogFn=} errorCallback The ``errorCallback`` argument of
 * :any:`pyodide.loadPackage` (optional).
 * @async
 */
export function loadPackagesFromImports(code: string, messageCallback?: LogFn | undefined, errorCallback?: LogFn | undefined): Promise<void>;
/**
 * Access a Python object in the global namespace from Javascript.
 *
 * @deprecated This function will be removed in version 0.18.0. Use
 *    :any:`pyodide.globals.get('key') <pyodide.globals>` instead.
 *
 * @param {string} name Python variable name
 * @returns {Py2JsResult} The Python object translated to Javascript.
 */
export function pyimport(name: string): Py2JsResult;
/**
 * Runs Python code using `PyCF_ALLOW_TOP_LEVEL_AWAIT
 * <https://docs.python.org/3/library/ast.html?highlight=pycf_allow_top_level_await#ast.PyCF_ALLOW_TOP_LEVEL_AWAIT>`_.
 *
 * .. admonition:: Python imports
 *    :class: warning
 *
 *    Since pyodide 0.18.0, you must call :js:func:`loadPackagesFromImports` to
 *    import any python packages referenced via `import` statements in your code.
 *    This function will no longer do it for you.
 *
 * For example:
 *
 * .. code-block:: pyodide
 *
 *    let result = await pyodide.runPythonAsync(`
 *        from js import fetch
 *        response = await fetch("./packages.json")
 *        packages = await response.json()
 *        # If final statement is an expression, its value is returned to Javascript
 *        len(packages.packages.object_keys())
 *    `);
 *    console.log(result); // 79
 *
 * @param {string} code Python code to evaluate
 * @returns {Py2JsResult} The result of the Python code translated to Javascript.
 * @async
 */
export function runPythonAsync(code: string): Py2JsResult;
/**
 * Registers the Javascript object ``module`` as a Javascript module named
 * ``name``. This module can then be imported from Python using the standard
 * Python import system. If another module by the same name has already been
 * imported, this won't have much effect unless you also delete the imported
 * module from ``sys.modules``. This calls the ``pyodide_py`` API
 * :func:`pyodide.register_js_module`.
 *
 * @param {string} name Name of the Javascript module to add
 * @param {object} module Javascript object backing the module
 */
export function registerJsModule(name: string, module: object): void;
/**
 * Tell Pyodide about Comlink.
 * Necessary to enable importing Comlink proxies into Python.
 */
export function registerComlink(Comlink: any): void;
/**
 * Unregisters a Javascript module with given name that has been previously
 * registered with :js:func:`pyodide.registerJsModule` or
 * :func:`pyodide.register_js_module`. If a Javascript module with that name
 * does not already exist, will throw an error. Note that if the module has
 * already been imported, this won't have much effect unless you also delete
 * the imported module from ``sys.modules``. This calls the ``pyodide_py`` API
 * :func:`pyodide.unregister_js_module`.
 *
 * @param {string} name Name of the Javascript module to remove
 */
export function unregisterJsModule(name: string): void;
/**
 * Convert the Javascript object to a Python object as best as possible.
 *
 * This is similar to :any:`JsProxy.to_py` but for use from Javascript. If the
 * object is immutable or a :any:`PyProxy`, it will be returned unchanged. If
 * the object cannot be converted into Python, it will be returned unchanged.
 *
 * See :ref:`type-translations-jsproxy-to-py` for more information.
 *
 * @param {*} obj
 * @param {object} options
 * @param {number} options.depth Optional argument to limit the depth of the
 * conversion.
 * @returns {PyProxy} The object converted to Python.
 */
export function toPy(obj: any, { depth }?: {
    depth: number;
}): PyProxy;
export function makePublicAPI(): {
    globals: import("./pyproxy.gen.js").PyProxy;
    FS: any;
    pyodide_py: import("./pyproxy.gen.js").PyProxy;
    version: string;
    loadPackage: typeof loadPackage;
    loadPackagesFromImports: typeof loadPackagesFromImports;
    loadedPackages: any;
    isPyProxy: typeof isPyProxy;
    pyimport: typeof pyimport;
    runPython: typeof runPython;
    runPythonAsync: typeof runPythonAsync;
    registerJsModule: typeof registerJsModule;
    unregisterJsModule: typeof unregisterJsModule;
    setInterruptBuffer: typeof setInterruptBuffer;
    toPy: typeof toPy;
    registerComlink: typeof registerComlink;
    PythonError: typeof PythonError;
    PyBuffer: typeof PyBuffer;
};
/**
 * A Javascript error caused by a Python exception.
 *
 * In order to reduce the risk of large memory leaks, the ``PythonError``
 * contains no reference to the Python exception that caused it. You can find
 * the actual Python exception that caused this error as `sys.last_value
 * <https://docs.python.org/3/library/sys.html#sys.last_value>`_.
 *
 * See :ref:`type-translations-errors` for more information.
 *
 * .. admonition:: Avoid Stack Frames
 *    :class: warning
 *
 *    If you make a :any:`PyProxy` of ``sys.last_value``, you should be
 *    especially careful to :any:`destroy() <PyProxy.destroy>` it when you are
 *    done. You may leak a large amount of memory including the local
 *    variables of all the stack frames in the traceback if you don't. The
 *    easiest way is to only handle the exception in Python.
 *
 * @class
 */
export class PythonError {
    /**
     * The Python traceback.
     * @type {string}
     */
    message: string;
}
/**
 *
 * The Pyodide version.
 *
 * It can be either the exact release version (e.g. ``0.1.0``), or
 * the latest release version followed by the number of commits since, and
 * the git hash of the current commit (e.g. ``0.1.0-1-bd84646``).
 *
 * @type {string}
 */
export let version: string;
export type LogFn = (msg: string) => void;
export type Py2JsResult = import('./pyproxy.gen').Py2JsResult;
export type PyProxy = import('./pyproxy.gen').PyProxy;
export type TypedArray = import('./pyproxy.gen').TypedArray;
export type Emscripten = any;
import { loadPackage } from "./load-pyodide.js";
import { isPyProxy } from "./pyproxy.gen.js";
/**
 * @param {TypedArray} interrupt_buffer
 */
export function setInterruptBuffer(interrupt_buffer: TypedArray): void;
import { PyBuffer } from "./pyproxy.gen.js";
import { loadedPackages } from "./load-pyodide.js";
export { loadPackage, loadedPackages, isPyProxy };
