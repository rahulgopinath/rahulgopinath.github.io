---
published: true
title: A Simple Runtime Invariant Miner
layout: post
comments: true
tags: invariants, dynamic-analysis, mining
categories: post
---
 
TLDR; This tutorial is a complete implementation of a Daikon-like runtime
invariant miner in Python. It implements basic instrumentation,
collection of execution traces, invariant checking, and suppression of
redundandant invariants.
## The Oracle Problem in Software Testing
 
One of the key challenges in software testing is the **Oracle Problem**:
That is, how do we determine if the output of a test is correct?
Manually writing assertions (this is the oracle) is tedious and error prone.
 
Daikon-style mining provides an _approximate oracle_. By observing 
verified runs of the given program, we can treat the resulting invariants
as an approximate specification of how the program should behave.
 
Two things to note:
 
1. The invariants are just _likely_: We derive thes invariants _inductively_
   from observations, and not from a human specification. Hence they are
   just hypotheses, not proven facts.
   For example, if your inputs only contain positive `int`s,
   one of the invariants reported could be `x > 0` even if the function is
   can correctly handle negative ints.
 
2. The invariants are _descriptive_: That is, the mined invariants are an
   approximation of the _current behaviour_. It may not be the correct
   behaviour of the program. If the current version of the program has a
   bug, the invariants mined will capture this bug as the expected behaviour.
 
Eventhough these are approximate, they are useful in practice, for example,
in regression testing, and in ensuring correct behaviour after a refactoring.
 
The concept of _dynamic invariant mining_ is as follows: Starting with the
program, and a set of inputs that it works correctly on, we run the program
under instrumentation. We capture the program state (the value of all
variables in the program) at each key location in the program: For example, at
entry and exit from a function, at entry and exit of loops, entry and exit
of conditionals etc. (We use the line number as the unique identifier for
a location. Such a named location is called a _program point_ in Daikon.)

We then use a library of unary and binary relation templates for evaluating
the relationship of each variable against known constants (unary relationship)
and against other variables at that instance (binary relationship). We then
collect all relationships that evaluated to true at that location for every
input. 
For example, `x >= 0`, `x == y`, `len(a) == n` etc. are all potential
relationships.
Any relation that evaluated to true is reported as a likely invariant.
The idea of mining runtime invariants was introduced by Ernst et al. in the
Daikon system [^ernst2001daikon].
Like our [grammar miner](/post/2019/11/26/simpleminer-01/), we
hook into `sys.settrace`.
 
## Synopsis
 
```python
results = mine_invariants(triangle, triangle_inputs)
for point, invs in results.items():
    print(point)
    for inv in invs:
        print('  ', inv)
```
 
## Definitions
* A _program point_ is a named location in a program's execution at
  which variable values are observed. Typical program points are function
  entry (`ENTER`) and function exit (`EXIT`). By convention the name is
  `function_name:::POINT_TYPE`.
 
* A _trace_ is a sequence of (program point, variable state) pairs
  collected during a single run of the program on one input.
 
* A _variable state_ is a snapshot of all in-scope variable bindings at
  a given program point. For an `EXIT` point this also includes the
  return value bound to the key `'return'`.
 
* A _candidate invariant_ is a predicate over a variable state that we
  wish to check. For example, `x >= 0` or `x == y`.
 
* An invariant _survives_ a state if the predicate holds for that state.
  An invariant is _falsified_ the first time it fails on any observed
  state, and is discarded thereafter.
 
* A _likely invariant_ is a candidate that survived every observed state
  at its program point. It is called "likely" because we have only
  checked a finite set of inputs.
 
* _Suppression_ is the process of removing redundant invariants. If
  `x == y` holds, then `x <= y` and `x >= y` are both implied by it and
  need not be reported separately.
 

## Contents
{:.no_toc}

1. TOC
{:toc}

<script src="/resources/js/graphviz/index.min.js"></script>
<script>
// From https://github.com/hpcc-systems/hpcc-js-wasm
// Hosted for teaching.
var hpccWasm = window["@hpcc-js/wasm"];
function display_dot(dot_txt, div) {
    hpccWasm.graphviz.layout(dot_txt, "svg", "dot").then(svg => {
        div.innerHTML = svg;
    });
}
window.display_dot = display_dot
// from js import display_dot
</script>

<script src="/resources/pyodide/full/3.9/pyodide.js"></script>
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/pyodide/js/env/editor.js" type="text/javascript"></script>

**Important:** [Pyodide](https://pyodide.readthedocs.io/en/latest/) takes time to initialize.
Initialization completion is indicated by a red border around *Run all* button.
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
## Prerequisites
 
We only need the standard library for this post.

<!--
############
import sys
import inspect
import itertools

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
import inspect
import itertools
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We will use the following simple functions as running examples throughout
the post. They are small enough that we can predict their invariants by
inspection, which lets us verify that the miner is working correctly.

<!--
############
def triangle(a, b, c):
    if a == b == c:
        return 'equilateral'
    elif a == b or b == c or a == c:
        return 'isosceles'
    else:
        return 'scalene'

def sum_list(lst):
    total = 0
    for x in lst:
        total += x
    return total

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def triangle(a, b, c):
    if a == b == c:
        return &#x27;equilateral&#x27;
    elif a == b or b == c or a == c:
        return &#x27;isosceles&#x27;
    else:
        return &#x27;scalene&#x27;

def sum_list(lst):
    total = 0
    for x in lst:
        total += x
    return total
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Program Points

Daikon's most important design decision is that invariants are attached
to specific points in the program called _program points_. This means
that `x >= 0` at `foo:::ENTER` and `x >= 0` at `foo:::EXIT` are two
separate invariants. The distinction matters: a variable may satisfy a
property on entry but not on exit, or vice versa.
 
We represent a program point as a small named object. By convention
the name is `function_name:::POINT_TYPE`. We give it `__eq__` and
`__hash__` so it can be used as a dict key.

<!--
############
class ProgramPoint:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'ProgramPoint(%r)' % self.name

    def __eq__(self, other):
        return isinstance(other, ProgramPoint) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ProgramPoint:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return &#x27;ProgramPoint(%r)&#x27; % self.name

    def __eq__(self, other):
        return isinstance(other, ProgramPoint) and self.name == other.name

    def __hash__(self):
        return hash(self.name)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Two `ProgramPoint` objects with the same name must compare equal and
hash identically so that the same point created in different places
refers to the same dict entry.

<!--
############
p1 = ProgramPoint('foo:::ENTER')
p2 = ProgramPoint('foo:::ENTER')
assert p1 == p2
assert hash(p1) == hash(p2)
assert str(p1) == 'foo:::ENTER'
assert repr(p1) == "ProgramPoint('foo:::ENTER')"
print('ProgramPoint ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
p1 = ProgramPoint(&#x27;foo:::ENTER&#x27;)
p2 = ProgramPoint(&#x27;foo:::ENTER&#x27;)
assert p1 == p2
assert hash(p1) == hash(p2)
assert str(p1) == &#x27;foo:::ENTER&#x27;
assert repr(p1) == &quot;ProgramPoint(&#x27;foo:::ENTER&#x27;)&quot;
print(&#x27;ProgramPoint ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## TraceStore
 
The `TraceStore` collects observed variable states keyed by program
point name. Each entry is a list of state dicts, one per observation,
accumulated across all inputs.

<!--
############
class TraceStore:
    def __init__(self):
        self.data = {}

    def add(self, point, state):
        if point is None:
            return
        if point.name not in self.data:
            self.data[point.name] = []
        self.data[point.name].append(dict(state))

    def get(self, point):
        return self.data.get(point.name, [])

    def points(self):
        return list(self.data.keys())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class TraceStore:
    def __init__(self):
        self.data = {}

    def add(self, point, state):
        if point is None:
            return
        if point.name not in self.data:
            self.data[point.name] = []
        self.data[point.name].append(dict(state))

    def get(self, point):
        return self.data.get(point.name, [])

    def points(self):
        return list(self.data.keys())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that observations accumulate correctly and that `get` returns
them in insertion order.

<!--
############
store = TraceStore()
p = ProgramPoint('foo:::ENTER')
store.add(p, {'x': 1, 'y': 2})
store.add(p, {'x': 3, 'y': 4})
assert len(store.get(p)) == 2
assert store.get(p)[0] == {'x': 1, 'y': 2}
assert store.get(p)[1] == {'x': 3, 'y': 4}
assert store.get(ProgramPoint('bar:::ENTER')) == []
print('TraceStore ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
store = TraceStore()
p = ProgramPoint(&#x27;foo:::ENTER&#x27;)
store.add(p, {&#x27;x&#x27;: 1, &#x27;y&#x27;: 2})
store.add(p, {&#x27;x&#x27;: 3, &#x27;y&#x27;: 4})
assert len(store.get(p)) == 2
assert store.get(p)[0] == {&#x27;x&#x27;: 1, &#x27;y&#x27;: 2}
assert store.get(p)[1] == {&#x27;x&#x27;: 3, &#x27;y&#x27;: 4}
assert store.get(ProgramPoint(&#x27;bar:::ENTER&#x27;)) == []
print(&#x27;TraceStore ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Instrumentation
 
To collect traces we hook into Python's `sys.settrace` mechanism.
We need two pieces of infrastructure: a `Context` class that unpacks
the information we need from a raw Python frame, and an `Instrumentor`
class that owns the `sys.settrace` lifecycle and accumulates events.
 
### Context
 
A Python trace callback receives a raw `frame` object. `Context` unpacks
the fields we care about: the method name, its declared parameter names,
the source file, and the current line number.
 
`extract_vars` returns all local bindings visible in the frame.
`parameters` filters those down to just the declared parameters — useful
at `call` time when we want only the arguments the caller passed in, not
any locals that the function body may have already created.

<!--
############
class Context:
    def __init__(self, frame):
        self.method          = inspect.getframeinfo(frame).function
        self.parameter_names = inspect.getargvalues(frame).args
        self.file_name       = inspect.getframeinfo(frame).filename
        self.line_no         = inspect.getframeinfo(frame).lineno

    def __repr__(self):
        return '%s:%d:%s(%s)' % (self.file_name, self.line_no,
                                  self.method, ','.join(self.parameter_names))

    def extract_vars(self, frame):
        return inspect.getargvalues(frame).locals

    def parameters(self, all_vars):
        return {k: v for k, v in all_vars.items()
                if k in self.parameter_names}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Context:
    def __init__(self, frame):
        self.method          = inspect.getframeinfo(frame).function
        self.parameter_names = inspect.getargvalues(frame).args
        self.file_name       = inspect.getframeinfo(frame).filename
        self.line_no         = inspect.getframeinfo(frame).lineno

    def __repr__(self):
        return &#x27;%s:%d:%s(%s)&#x27; % (self.file_name, self.line_no,
                                  self.method, &#x27;,&#x27;.join(self.parameter_names))

    def extract_vars(self, frame):
        return inspect.getargvalues(frame).locals

    def parameters(self, all_vars):
        return {k: v for k, v in all_vars.items()
                if k in self.parameter_names}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We verify `Context` directly here, before moving on to `Instrumentor`,
so a reader can see exactly what a frame looks like when unpacked.
We install a minimal one-shot callback as a closure that captures the
frame on the first `call` event and immediately removes itself. This
keeps all the machinery local to the test block.

<!--
############
_seen = {}

def _capture(frame, event, arg):
    if event == 'call' and frame.f_code.co_name == 'triangle':
        cxt = Context(frame)
        _seen['method']     = cxt.method
        _seen['parameters'] = cxt.parameter_names
        _seen['all_vars']   = cxt.extract_vars(frame)
        _seen['params']     = cxt.parameters(cxt.extract_vars(frame))
        sys.settrace(None)
    return _capture

sys.settrace(_capture)
triangle(3, 4, 5)
sys.settrace(None)

assert _seen['method'] == 'triangle'
assert _seen['parameters'] == ['a', 'b', 'c']
# at call time, all_vars contains exactly the parameters
assert _seen['all_vars'] == {'a': 3, 'b': 4, 'c': 5}
# parameters() selects only declared names from whatever all_vars contains
assert _seen['params'] == {'a': 3, 'b': 4, 'c': 5}
print('Context ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_seen = {}

def _capture(frame, event, arg):
    if event == &#x27;call&#x27; and frame.f_code.co_name == &#x27;triangle&#x27;:
        cxt = Context(frame)
        _seen[&#x27;method&#x27;]     = cxt.method
        _seen[&#x27;parameters&#x27;] = cxt.parameter_names
        _seen[&#x27;all_vars&#x27;]   = cxt.extract_vars(frame)
        _seen[&#x27;params&#x27;]     = cxt.parameters(cxt.extract_vars(frame))
        sys.settrace(None)
    return _capture

sys.settrace(_capture)
triangle(3, 4, 5)
sys.settrace(None)

assert _seen[&#x27;method&#x27;] == &#x27;triangle&#x27;
assert _seen[&#x27;parameters&#x27;] == [&#x27;a&#x27;, &#x27;b&#x27;, &#x27;c&#x27;]
# at call time, all_vars contains exactly the parameters
assert _seen[&#x27;all_vars&#x27;] == {&#x27;a&#x27;: 3, &#x27;b&#x27;: 4, &#x27;c&#x27;: 5}
# parameters() selects only declared names from whatever all_vars contains
assert _seen[&#x27;params&#x27;] == {&#x27;a&#x27;: 3, &#x27;b&#x27;: 4, &#x27;c&#x27;: 5}
print(&#x27;Context ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Instrumentor
 
`Instrumentor` owns the `sys.settrace` callback and drives the whole
observation process.
 
Which variable values are worth recording is a policy decision, not a
fixed part of the instrumentation. The default, `default_interesting`,
takes a variable name and its value and returns `True` if both are
worth recording. By default it excludes names starting with `_` (Python
internals) and values of types our invariant templates cannot reason
about. A library user who wants to include private variables, track
additional types, or exclude specific names can pass their own
`interesting=my_predicate` to any instrumentor or collection function
without subclassing anything.
  
`_tracer` is the raw callback registered with `sys.settrace`. Python
calls it on every `call`, `return`, `line`, and `exception` event; we
respond only to `call` and `return` to keep overhead low. On `call` we
build a `Context`, check that the method name does not start with `_`
(to exclude Python internals), collect the variables accepted by
`interesting`, and store them as an `ENTER` state. On `return` we
collect all accepted locals plus the return value and store them as an
`EXIT` state. The callback always returns itself so Python keeps calling
it for nested frames.
 
`run` installs `_tracer`, calls the function, and always tears the
hook down in a `finally` block so we never leave a stale callback
behind even if the function raises.

<!--
############
def default_interesting(name, val):
    return (not name.startswith('_') and
            isinstance(val, (int, float, str, bool, list, tuple)))

class Instrumentor:
    def __init__(self, store, interesting=default_interesting):
        self.store       = store
        self.interesting = interesting

    def _tracer(self, frame, event, arg):
        if event not in ('call', 'return'):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith('_'):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == 'call':
            point = ProgramPoint('%s:::ENTER' % cxt.method)
            self.store.add(point, cxt.parameters(all_vars))
        else:
            point = ProgramPoint('%s:::EXIT' % cxt.method)
            state = dict(all_vars)
            if self.interesting('return', arg):
                state['return'] = arg
            self.store.add(point, state)
        return self._tracer

    def run(self, fn, *args, **kwargs):
        sys.settrace(self._tracer)
        try:
            fn(*args, **kwargs)
        finally:
            sys.settrace(None)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def default_interesting(name, val):
    return (not name.startswith(&#x27;_&#x27;) and
            isinstance(val, (int, float, str, bool, list, tuple)))

class Instrumentor:
    def __init__(self, store, interesting=default_interesting):
        self.store       = store
        self.interesting = interesting

    def _tracer(self, frame, event, arg):
        if event not in (&#x27;call&#x27;, &#x27;return&#x27;):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith(&#x27;_&#x27;):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == &#x27;call&#x27;:
            point = ProgramPoint(&#x27;%s:::ENTER&#x27; % cxt.method)
            self.store.add(point, cxt.parameters(all_vars))
        else:
            point = ProgramPoint(&#x27;%s:::EXIT&#x27; % cxt.method)
            state = dict(all_vars)
            if self.interesting(&#x27;return&#x27;, arg):
                state[&#x27;return&#x27;] = arg
            self.store.add(point, state)
        return self._tracer

    def run(self, fn, *args, **kwargs):
        sys.settrace(self._tracer)
        try:
            fn(*args, **kwargs)
        finally:
            sys.settrace(None)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that a single `run` call produces both an `ENTER` and an `EXIT`
observation, that `ENTER` contains only the declared parameters, and
that `EXIT` contains the return value.

<!--
############
store = TraceStore()
instr = Instrumentor(store)
instr.run(triangle, 3, 3, 3)
assert 'triangle:::ENTER' in store.points()
assert 'triangle:::EXIT'  in store.points()
enter_state = store.get(ProgramPoint('triangle:::ENTER'))[0]
assert enter_state == {'a': 3, 'b': 3, 'c': 3}
exit_state = store.get(ProgramPoint('triangle:::EXIT'))[0]
assert exit_state['return'] == 'equilateral'
print('Instrumentor ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
store = TraceStore()
instr = Instrumentor(store)
instr.run(triangle, 3, 3, 3)
assert &#x27;triangle:::ENTER&#x27; in store.points()
assert &#x27;triangle:::EXIT&#x27;  in store.points()
enter_state = store.get(ProgramPoint(&#x27;triangle:::ENTER&#x27;))[0]
assert enter_state == {&#x27;a&#x27;: 3, &#x27;b&#x27;: 3, &#x27;c&#x27;: 3}
exit_state = store.get(ProgramPoint(&#x27;triangle:::EXIT&#x27;))[0]
assert exit_state[&#x27;return&#x27;] == &#x27;equilateral&#x27;
print(&#x27;Instrumentor ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A library user can restrict or extend what gets recorded by passing a
custom `interesting` predicate. Here we pass one that accepts only
integers, which means string return values and non-integer locals are
excluded. Note the predicate receives both name and value. A user
could, for example, include private variables by ignoring the name
filter entirely.

<!--
############
_int_store = TraceStore()
Instrumentor(_int_store, interesting=lambda n, v: isinstance(v, int)).run(triangle, 3, 3, 3)
_exit = _int_store.get(ProgramPoint('triangle:::EXIT'))[0]
assert 'return' not in _exit      # 'equilateral' is a string, excluded
assert _exit['a'] == 3            # integers still captured
print('Instrumentor custom interesting ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_int_store = TraceStore()
Instrumentor(_int_store, interesting=lambda n, v: isinstance(v, int)).run(triangle, 3, 3, 3)
_exit = _int_store.get(ProgramPoint(&#x27;triangle:::EXIT&#x27;))[0]
assert &#x27;return&#x27; not in _exit      # &#x27;equilateral&#x27; is a string, excluded
assert _exit[&#x27;a&#x27;] == 3            # integers still captured
print(&#x27;Instrumentor custom interesting ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Collecting traces over multiple inputs
 
We run the function once per input and accumulate all observations in
the same store. Each element of `inputs` is a tuple of arguments.
A single-argument function wraps its argument in a one-tuple:
`([1, 2, 3],)`. The `interesting` predicate is forwarded to
`Instrumentor` so callers can control what gets recorded without
touching the collection loop.

<!--
############
def collect_traces(fn, inputs, store=None, interesting=default_interesting):
    if store is None: store = TraceStore()
    instr = Instrumentor(store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return store

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def collect_traces(fn, inputs, store=None, interesting=default_interesting):
    if store is None: store = TraceStore()
    instr = Instrumentor(store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return store
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Collect traces for a range of triangle inputs.

<!--
############
triangle_inputs = [
    (3, 3, 3),
    (3, 3, 4),
    (3, 4, 5),
    (5, 5, 5),
    (1, 2, 3),
]
store = collect_traces(triangle, triangle_inputs)
print('program points:', store.points())
print('ENTER observations:', len(store.get(ProgramPoint('triangle:::ENTER'))))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
triangle_inputs = [
    (3, 3, 3),
    (3, 3, 4),
    (3, 4, 5),
    (5, 5, 5),
    (1, 2, 3),
]
store = collect_traces(triangle, triangle_inputs)
print(&#x27;program points:&#x27;, store.points())
print(&#x27;ENTER observations:&#x27;, len(store.get(ProgramPoint(&#x27;triangle:::ENTER&#x27;))))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
All five inputs share the same two program points `triangle:::ENTER` and
`triangle:::EXIT`. Their observations are pooled, so the surviving
invariants will be those that hold across every input.
## Candidate Invariants
 
An `Invariant` object wraps a predicate and tracks whether it has been
falsified. Once falsified it stays dead — we never resurrect it.
The predicate receives a state dict and should return a bool. Any
exception during evaluation counts as a falsification, which handles
type mismatches (e.g. comparing a string to a number) without special
casing.

<!--
############
class Invariant:
    def __init__(self, name, check):
        self.name  = name
        self.check = check
        self.alive = True

    def test(self, state):
        if not self.alive: return
        try:
            if not self.check(state):
                self.alive = False
        except Exception:
            self.alive = False

    def __repr__(self):
        return self.name

    def status(self):
        return "%s: %s" % (self.name, self.alive)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Invariant:
    def __init__(self, name, check):
        self.name  = name
        self.check = check
        self.alive = True

    def test(self, state):
        if not self.alive: return
        try:
            if not self.check(state):
                self.alive = False
        except Exception:
            self.alive = False

    def __repr__(self):
        return self.name

    def status(self):
        return &quot;%s: %s&quot; % (self.name, self.alive)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Unary templates
 
Unary invariants involve a single variable. We generate a small fixed
set of templates for every variable we observe. Templates that do not
apply to the variable's type (e.g. `>= 0` on a string) will be
falsified on the first observation and quietly drop out.

<!--
############
def unary_invariants(var):
    return [
        Invariant('%s is not None' % var,
                  lambda s, v=var: s.get(v) is not None),
        Invariant('%s >= 0' % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] >= 0),
        Invariant('%s > 0' % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] > 0),
        Invariant('type(%s) is int' % var,
                  lambda s, v=var: isinstance(s.get(v), int)),
        Invariant('type(%s) is str' % var,
                  lambda s, v=var: isinstance(s.get(v), str)),
    ]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unary_invariants(var):
    return [
        Invariant(&#x27;%s is not None&#x27; % var,
                  lambda s, v=var: s.get(v) is not None),
        Invariant(&#x27;%s &gt;= 0&#x27; % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] &gt;= 0),
        Invariant(&#x27;%s &gt; 0&#x27; % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] &gt; 0),
        Invariant(&#x27;type(%s) is int&#x27; % var,
                  lambda s, v=var: isinstance(s.get(v), int)),
        Invariant(&#x27;type(%s) is str&#x27; % var,
                  lambda s, v=var: isinstance(s.get(v), str)),
    ]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that a numeric state kills the string template but preserves
the numeric ones, and that a negative value kills `>= 0`.

<!--
############
invs = unary_invariants('x')
for inv in invs: inv.test({'x': 5})
assert invs[0].alive      # x is not None
assert invs[1].alive      # x >= 0
assert invs[2].alive      # x > 0
assert invs[3].alive      # type(x) is int
assert not invs[4].alive  # type(x) is str — correctly killed on int
invs[1].test({'x': -1})
assert not invs[1].alive  # x >= 0 now dead
assert invs[0].alive      # x is not None still alive
print('unary invariants ok')
for inv in invs:
    print(inv.status())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
invs = unary_invariants(&#x27;x&#x27;)
for inv in invs: inv.test({&#x27;x&#x27;: 5})
assert invs[0].alive      # x is not None
assert invs[1].alive      # x &gt;= 0
assert invs[2].alive      # x &gt; 0
assert invs[3].alive      # type(x) is int
assert not invs[4].alive  # type(x) is str — correctly killed on int
invs[1].test({&#x27;x&#x27;: -1})
assert not invs[1].alive  # x &gt;= 0 now dead
assert invs[0].alive      # x is not None still alive
print(&#x27;unary invariants ok&#x27;)
for inv in invs:
    print(inv.status())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Binary templates
 
Binary invariants involve two variables. We generate templates for
every pair of variables that appear together in at least one state.

<!--
############
def binary_invariants(x, y):
    return [
        Invariant('%s == %s' % (x, y),
                  lambda s, a=x, b=y: s.get(a) == s.get(b)),
        Invariant('%s <= %s' % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] <= s[b]),
        Invariant('%s >= %s' % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] >= s[b]),
    ]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def binary_invariants(x, y):
    return [
        Invariant(&#x27;%s == %s&#x27; % (x, y),
                  lambda s, a=x, b=y: s.get(a) == s.get(b)),
        Invariant(&#x27;%s &lt;= %s&#x27; % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] &lt;= s[b]),
        Invariant(&#x27;%s &gt;= %s&#x27; % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] &gt;= s[b]),
    ]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that equal states keep `==` alive and a differing state kills it
while leaving `<=` alive.

<!--
############
invs = binary_invariants('x', 'y')
for state in [{'x': 2, 'y': 2}, {'x': 2, 'y': 2}]:
    for inv in invs: inv.test(state)
assert invs[0].alive             # x == y survived
for inv in invs: inv.test({'x': 1, 'y': 2})
assert not invs[0].alive         # x == y falsified
assert invs[1].alive             # x <= y survived
print('binary invariants ok')
for inv in invs:
    print(inv.status())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
invs = binary_invariants(&#x27;x&#x27;, &#x27;y&#x27;)
for state in [{&#x27;x&#x27;: 2, &#x27;y&#x27;: 2}, {&#x27;x&#x27;: 2, &#x27;y&#x27;: 2}]:
    for inv in invs: inv.test(state)
assert invs[0].alive             # x == y survived
for inv in invs: inv.test({&#x27;x&#x27;: 1, &#x27;y&#x27;: 2})
assert not invs[0].alive         # x == y falsified
assert invs[1].alive             # x &lt;= y survived
print(&#x27;binary invariants ok&#x27;)
for inv in invs:
    print(inv.status())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Invariant Engine
 
The engine takes a `TraceStore`, generates candidate invariants for each
program point, and checks them against all observations at that point.
A candidate that survives every observation is a likely invariant.
 
### Generating candidates for a point
 
We collect all variable names that appear in any state at the point,
then generate all unary and binary candidates over those names. The
number of candidates grows quadratically with the number of variables,
but for typical program points the variable count is small.

<!--
############
class InvariantEngine:
    def candidates_for(self, observations):
        all_vars = set()
        for state in observations:
            all_vars.update(state.keys())
        all_vars = sorted(all_vars)
        candidates = []
        for v in all_vars:
            candidates.extend(unary_invariants(v))
        for x, y in itertools.combinations(all_vars, 2):
            candidates.extend(binary_invariants(x, y))
        return candidates

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class InvariantEngine:
    def candidates_for(self, observations):
        all_vars = set()
        for state in observations:
            all_vars.update(state.keys())
        all_vars = sorted(all_vars)
        candidates = []
        for v in all_vars:
            candidates.extend(unary_invariants(v))
        for x, y in itertools.combinations(all_vars, 2):
            candidates.extend(binary_invariants(x, y))
        return candidates
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify candidate generation produces the templates we expect.

<!--
############
engine = InvariantEngine()
obs    = [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]
cands  = engine.candidates_for(obs)
names  = [c.name for c in cands]
assert 'x >= 0' in names
assert 'x == y' in names
print('candidate generation ok, %d candidates' % len(cands))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
engine = InvariantEngine()
obs    = [{&#x27;x&#x27;: 1, &#x27;y&#x27;: 2}, {&#x27;x&#x27;: 3, &#x27;y&#x27;: 4}]
cands  = engine.candidates_for(obs)
names  = [c.name for c in cands]
assert &#x27;x &gt;= 0&#x27; in names
assert &#x27;x == y&#x27; in names
print(&#x27;candidate generation ok, %d candidates&#x27; % len(cands))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Checking candidates against observations
 
We test every candidate against every observed state. Candidates that
remain alive after all observations are the likely invariants. The order
of iteration does not matter because falsification is monotone: once
dead, always dead.

<!--
############
class InvariantEngine(InvariantEngine):
    def check(self, candidates, observations):
        for state in observations:
            for inv in candidates:
                inv.test(state)
        return [inv for inv in candidates if inv.alive]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class InvariantEngine(InvariantEngine):
    def check(self, candidates, observations):
        for state in observations:
            for inv in candidates:
                inv.test(state)
        return [inv for inv in candidates if inv.alive]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Running the full analysis
 
`analyze` iterates over every program point in the store, generates
fresh candidates for each one, checks them against that point's
observations, and collects the survivors into a results dict keyed by
point name. Candidates are generated fresh for each point so that
falsification at one point does not affect another.

<!--
############
class InvariantEngine(InvariantEngine):
    def analyze(self, store):
        results = {}
        for point_name in store.points():
            observations = store.data[point_name]
            if not observations:
                continue
            candidates = self.candidates_for(observations)
            results[point_name] = self.check(candidates, observations)
        return results

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class InvariantEngine(InvariantEngine):
    def analyze(self, store):
        results = {}
        for point_name in store.points():
            observations = store.data[point_name]
            if not observations:
                continue
            candidates = self.candidates_for(observations)
            results[point_name] = self.check(candidates, observations)
        return results
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the engine on our triangle traces.

<!--
############
engine  = InvariantEngine()
results = engine.analyze(store)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
engine  = InvariantEngine()
results = engine.analyze(store)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At `triangle:::ENTER` we see `a >= 0`, `b >= 0`, `c >= 0`, and
`type(a) is int` because all our inputs used positive integers.
At `triangle:::EXIT` we see `type(return) is str`. Notice that
pooling all five inputs means `a == b` does not survive — it holds
for `(3,3,3)` and `(5,5,5)` but not for `(3,4,5)`. We will address
this in the scoped program points section below.
  
## Suppression
 
The engine produces many redundant invariants. If `x == y` holds then
both `x <= y` and `x >= y` add no information. The suppression step
removes weaker invariants that are implied by stronger ones.
 
We maintain a simple implication table: if an invariant matching the
_strong_ pattern is alive, we remove any co-surviving invariant
matching the _weak_ pattern that involves the same variables.
`_vars` extracts variable names from an invariant's name string by
tokenising and keeping only identifiers that are not keywords used by
our templates.

<!--
############
class SuppressionLattice:
    IMPLIES = [
        ('==', '<='),
        ('==', '>='),
    ]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SuppressionLattice:
    IMPLIES = [
        (&#x27;==&#x27;, &#x27;&lt;=&#x27;),
        (&#x27;==&#x27;, &#x27;&gt;=&#x27;),
    ]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`suppress` walks the implication table and removes any invariant that
is dominated by a stronger co-surviving invariant over the same
variables.

<!--
############
class SuppressionLattice(SuppressionLattice):
    def _vars(self, inv_name):
        tokens = inv_name.replace('(', ' ').replace(')', ' ').split()
        return frozenset(t for t in tokens
                         if t.isidentifier() and t not in
                         ('type', 'is', 'not', 'None', 'int', 'str', 'float'))

    def suppress(self, invariants):
        alive     = list(invariants)
        to_remove = set()
        for strong, weak in self.IMPLIES:
            strong_invs = [i for i in alive if strong in i.name]
            weak_invs   = [i for i in alive if weak in i.name
                           and strong not in i.name]
            for s_inv in strong_invs:
                s_vars = self._vars(s_inv.name)
                for w_inv in weak_invs:
                    if self._vars(w_inv.name) == s_vars:
                        to_remove.add(id(w_inv))
        return [i for i in alive if id(i) not in to_remove]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SuppressionLattice(SuppressionLattice):
    def _vars(self, inv_name):
        tokens = inv_name.replace(&#x27;(&#x27;, &#x27; &#x27;).replace(&#x27;)&#x27;, &#x27; &#x27;).split()
        return frozenset(t for t in tokens
                         if t.isidentifier() and t not in
                         (&#x27;type&#x27;, &#x27;is&#x27;, &#x27;not&#x27;, &#x27;None&#x27;, &#x27;int&#x27;, &#x27;str&#x27;, &#x27;float&#x27;))

    def suppress(self, invariants):
        alive     = list(invariants)
        to_remove = set()
        for strong, weak in self.IMPLIES:
            strong_invs = [i for i in alive if strong in i.name]
            weak_invs   = [i for i in alive if weak in i.name
                           and strong not in i.name]
            for s_inv in strong_invs:
                s_vars = self._vars(s_inv.name)
                for w_inv in weak_invs:
                    if self._vars(w_inv.name) == s_vars:
                        to_remove.add(id(w_inv))
        return [i for i in alive if id(i) not in to_remove]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that `==` suppresses the redundant `<=` and `>=`.

<!--
############
lattice = SuppressionLattice()
eq_inv  = Invariant('x == y', lambda s: s['x'] == s['y'])
le_inv  = Invariant('x <= y', lambda s: s['x'] <= s['y'])
ge_inv  = Invariant('x >= y', lambda s: s['x'] >= s['y'])
result  = lattice.suppress([eq_inv, le_inv, ge_inv])
assert len(result) == 1
assert result[0].name == 'x == y'
print('suppression ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
lattice = SuppressionLattice()
eq_inv  = Invariant(&#x27;x == y&#x27;, lambda s: s[&#x27;x&#x27;] == s[&#x27;y&#x27;])
le_inv  = Invariant(&#x27;x &lt;= y&#x27;, lambda s: s[&#x27;x&#x27;] &lt;= s[&#x27;y&#x27;])
ge_inv  = Invariant(&#x27;x &gt;= y&#x27;, lambda s: s[&#x27;x&#x27;] &gt;= s[&#x27;y&#x27;])
result  = lattice.suppress([eq_inv, le_inv, ge_inv])
assert len(result) == 1
assert result[0].name == &#x27;x == y&#x27;
print(&#x27;suppression ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Full Pipeline
 
We now combine all the pieces into a single `mine_invariants` function.

<!--
############
def mine_invariants(fn, inputs):
    store   = collect_traces(fn, inputs)
    engine  = InvariantEngine()
    raw     = engine.analyze(store)
    lattice = SuppressionLattice()
    return {point: lattice.suppress(invs) for point, invs in raw.items()}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def mine_invariants(fn, inputs):
    store   = collect_traces(fn, inputs)
    engine  = InvariantEngine()
    raw     = engine.analyze(store)
    lattice = SuppressionLattice()
    return {point: lattice.suppress(invs) for point, invs in raw.items()}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the full pipeline on `triangle`.

<!--
############
results = mine_invariants(triangle, triangle_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
results = mine_invariants(triangle, triangle_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the full pipeline on `sum_list`.

<!--
############
sum_inputs = [([1, 2, 3],), ([0],), ([10, 20],), ([1, 1, 1, 1],)]
results = mine_invariants(sum_list, sum_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
sum_inputs = [([1, 2, 3],), ([0],), ([10, 20],), ([1, 1, 1, 1],)]
results = mine_invariants(sum_list, sum_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At `sum_list:::EXIT` the miner correctly discovers `return == total`,
which captures the loop invariant: the return value equals the running
total at the point the function exits.
 
## Scoped Program Points
 
The flat naming above pools all calls to `triangle` into one program
point. This means the invariants we report are those that hold across
every input — an equilateral triangle and a scalene triangle share one
observation bucket, and properties specific to either are lost.
 
The fix is to give each invocation a unique identity. We introduce a
`CallStack` that assigns a monotonically increasing integer to each
call. The program point name becomes `function[call_id]:::TAG`, so
`triangle[1]:::ENTER` and `triangle[2]:::ENTER` are distinct points
whose observations never mix.
 
This is the same scoping idea used in our grammar miner to distinguish
separate calls to the same parsing helper. It also turns out to be the
key we need to link an `ENTER` observation to its corresponding `EXIT`
observation — something we will use in the next section.

<!--
############
START_SYMBOL = '<start>'
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
START_SYMBOL = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The root sentinel (seq == 0) marks the bottom of the stack
before any function has been entered.

<!--
############
class CallStack:
    def __init__(self, start_symbol=START_SYMBOL):
        self.method_id       = (START_SYMBOL, 0)
        self.method_register = 0
        self.mstack          = [self.method_id]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallStack:
    def __init__(self, start_symbol=START_SYMBOL):
        self.method_id       = (START_SYMBOL, 0)
        self.method_register = 0
        self.mstack          = [self.method_id]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Assign the next id, push onto the stack, and return the new
method_id so the caller can use it to name the ENTER point.

<!--
############
class CallStack(CallStack):
    def enter(self, method):
        self.method_register += 1
        self.method_id = (method, self.method_register)
        self.mstack.append(self.method_id)
        return self.method_id

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallStack(CallStack):
    def enter(self, method):
        self.method_register += 1
        self.method_id = (method, self.method_register)
        self.mstack.append(self.method_id)
        return self.method_id
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Pop the current frame and restore the caller's method_id.

<!--
############
class CallStack(CallStack):
    def leave(self):
        self.mstack.pop()
        self.method_id = self.mstack[-1]

    def current(self):
        return self.method_id

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallStack(CallStack):
    def leave(self):
        self.mstack.pop()
        self.method_id = self.mstack[-1]

    def current(self):
        return self.method_id
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that `enter` and `leave` maintain the stack correctly and that
ids are unique and monotonically increasing across calls.

<!--
############
cs = CallStack()
assert cs.current() == (START_SYMBOL, 0)
mid1 = cs.enter('foo')
assert mid1 == ('foo', 1)
mid2 = cs.enter('bar')
assert mid2 == ('bar', 2)
cs.leave()
assert cs.current() == mid1
mid3 = cs.enter('bar')   # second call to bar gets a new id
assert mid3 == ('bar', 3)
cs.leave()
cs.leave()
assert cs.current() == (START_SYMBOL, 0)
print('CallStack ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cs = CallStack()
assert cs.current() == (START_SYMBOL, 0)
mid1 = cs.enter(&#x27;foo&#x27;)
assert mid1 == (&#x27;foo&#x27;, 1)
mid2 = cs.enter(&#x27;bar&#x27;)
assert mid2 == (&#x27;bar&#x27;, 2)
cs.leave()
assert cs.current() == mid1
mid3 = cs.enter(&#x27;bar&#x27;)   # second call to bar gets a new id
assert mid3 == (&#x27;bar&#x27;, 3)
cs.leave()
cs.leave()
assert cs.current() == (START_SYMBOL, 0)
print(&#x27;CallStack ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`make_scoped_point` produces the `function[id]:::TAG` name. The root
sentinel (seq == 0) is not a real call so we return `None`, which
`TraceStore.add` will silently ignore.

<!--
############
def make_scoped_point(method_id, tag):
    method, seq = method_id
    if seq == 0:
        return None
    return ProgramPoint('%s[%d]:::%s' % (method, seq, tag))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def make_scoped_point(method_id, tag):
    method, seq = method_id
    if seq == 0:
        return None
    return ProgramPoint(&#x27;%s[%d]:::%s&#x27; % (method, seq, tag))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`ScopedInstrumentor` extends `Instrumentor` by maintaining a
`CallStack` and using `make_scoped_point` instead of bare
`function:::TAG` names. On `call` it pushes the method onto the stack
and tags the ENTER point with the resulting id. On `return` it reads
the current id for the EXIT point, then pops the stack. The `run`
method is inherited unchanged from `Instrumentor`.

<!--
############
class ScopedInstrumentor(Instrumentor):
    def __init__(self, store, interesting=default_interesting):
        super().__init__(store, interesting)
        self.call_stack = CallStack()

    def _tracer(self, frame, event, arg):
        if event not in ('call', 'return'):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith('_'):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == 'call':
            mid   = self.call_stack.enter(cxt.method)
            point = make_scoped_point(mid, 'ENTER')
            self.store.add(point, cxt.parameters(all_vars))
        else:
            mid   = self.call_stack.current()
            point = make_scoped_point(mid, 'EXIT')
            state = dict(all_vars)
            if self.interesting('return', arg):
                state['return'] = arg
            self.store.add(point, state)
            self.call_stack.leave()
        return self._tracer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ScopedInstrumentor(Instrumentor):
    def __init__(self, store, interesting=default_interesting):
        super().__init__(store, interesting)
        self.call_stack = CallStack()

    def _tracer(self, frame, event, arg):
        if event not in (&#x27;call&#x27;, &#x27;return&#x27;):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith(&#x27;_&#x27;):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == &#x27;call&#x27;:
            mid   = self.call_stack.enter(cxt.method)
            point = make_scoped_point(mid, &#x27;ENTER&#x27;)
            self.store.add(point, cxt.parameters(all_vars))
        else:
            mid   = self.call_stack.current()
            point = make_scoped_point(mid, &#x27;EXIT&#x27;)
            state = dict(all_vars)
            if self.interesting(&#x27;return&#x27;, arg):
                state[&#x27;return&#x27;] = arg
            self.store.add(point, state)
            self.call_stack.leave()
        return self._tracer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify that two calls to the same function produce distinct program
points and that their observations do not mix.

<!--
############
scoped_store = TraceStore()
instr = ScopedInstrumentor(scoped_store)
instr.run(triangle, 3, 3, 3)   # equilateral
instr.run(triangle, 3, 4, 5)   # scalene
pts = scoped_store.points()
assert 'triangle[1]:::ENTER' in pts
assert 'triangle[2]:::ENTER' in pts
obs1 = scoped_store.get(ProgramPoint('triangle[1]:::ENTER'))[0]
obs2 = scoped_store.get(ProgramPoint('triangle[2]:::ENTER'))[0]
assert obs1 == {'a': 3, 'b': 3, 'c': 3}
assert obs2 == {'a': 3, 'b': 4, 'c': 5}
print('ScopedInstrumentor ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
scoped_store = TraceStore()
instr = ScopedInstrumentor(scoped_store)
instr.run(triangle, 3, 3, 3)   # equilateral
instr.run(triangle, 3, 4, 5)   # scalene
pts = scoped_store.points()
assert &#x27;triangle[1]:::ENTER&#x27; in pts
assert &#x27;triangle[2]:::ENTER&#x27; in pts
obs1 = scoped_store.get(ProgramPoint(&#x27;triangle[1]:::ENTER&#x27;))[0]
obs2 = scoped_store.get(ProgramPoint(&#x27;triangle[2]:::ENTER&#x27;))[0]
assert obs1 == {&#x27;a&#x27;: 3, &#x27;b&#x27;: 3, &#x27;c&#x27;: 3}
assert obs2 == {&#x27;a&#x27;: 3, &#x27;b&#x27;: 4, &#x27;c&#x27;: 5}
print(&#x27;ScopedInstrumentor ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`collect_traces_scoped` mirrors `collect_traces` but uses
`ScopedInstrumentor`. The `interesting` predicate is forwarded so
callers have the same control over what gets recorded as they do with
the flat version.

<!--
############
def collect_traces_scoped(fn, inputs, store=None, interesting=default_interesting):
    if store is None:
        store = TraceStore()
    instr = ScopedInstrumentor(store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return store

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def collect_traces_scoped(fn, inputs, store=None, interesting=default_interesting):
    if store is None:
        store = TraceStore()
    instr = ScopedInstrumentor(store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return store
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
With scoped points each call to `triangle` gets its own pair, so the
five inputs produce `triangle[1]` through `triangle[5]`.

<!--
############
scoped_store = collect_traces_scoped(triangle, triangle_inputs)
print('scoped program points:', scoped_store.points())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
scoped_store = collect_traces_scoped(triangle, triangle_inputs)
print(&#x27;scoped program points:&#x27;, scoped_store.points())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The rest of the pipeline — `InvariantEngine`, `SuppressionLattice`,
`mine_invariants` — is unchanged. We just pass `collect_traces_scoped`
instead of `collect_traces`.

<!--
############
def mine_invariants_scoped(fn, inputs):
    store   = collect_traces_scoped(fn, inputs)
    engine  = InvariantEngine()
    raw     = engine.analyze(store)
    lattice = SuppressionLattice()
    return {point: lattice.suppress(invs) for point, invs in raw.items()}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def mine_invariants_scoped(fn, inputs):
    store   = collect_traces_scoped(fn, inputs)
    engine  = InvariantEngine()
    raw     = engine.analyze(store)
    lattice = SuppressionLattice()
    return {point: lattice.suppress(invs) for point, invs in raw.items()}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the scoped pipeline on `triangle`.

<!--
############
results = mine_invariants_scoped(triangle, triangle_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
results = mine_invariants_scoped(triangle, triangle_inputs)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now `triangle[1]:::ENTER` (the equilateral case `(3,3,3)`) reports
`a == b`, `a == c`, and `b == c`, while `triangle[3]:::ENTER` (the
scalene case `(3,4,5)`) reports only `a <= b`, `a <= c`, and
`b <= c`. The scoped points give us per-call precision that the flat
version cannot.
 
## Pre/Post Relations
 
The invariants we have mined so far are _single-point_ invariants:
each one says something about the program state at either `ENTER` or
`EXIT`, but never both at once. This misses the most interesting class
of invariant: _relational_ invariants that relate the state a function
was called with to the state it left behind. For example:
 
* `a_exit == a_entry` — the argument `a` was not modified.
* `return_exit >= a_entry` — the return value is at least as large as
  the first argument on entry.
 
These are pre/post invariants in the sense of Hoare logic: they
relate the precondition (values at `ENTER`) to the postcondition
(values at `EXIT`).
 
To express them we need to pair each `ENTER` observation with its
corresponding `EXIT` observation from the same call. The call id
produced by `CallStack` is the join key: the `ENTER` and `EXIT`
observations for `triangle[3]` came from the same invocation and can
be safely merged into one combined state where every entry variable
carries an `_entry` suffix and every exit variable carries an `_exit`
suffix.
 
### PairedTraceStore
 
`PairedTraceStore` accumulates `ENTER` and `EXIT` observations
separately, keyed by call id, then joins them on demand. Variables
that appear at both points get two entries — `x_entry` and `x_exit`
— which lets us ask directly whether the value changed.

<!--
############
class PairedTraceStore:
    def __init__(self):
        self.enters = {}
        self.exits  = {}

    def add_enter(self, call_id, state):
        self.enters[call_id] = dict(state)

    def add_exit(self, call_id, state):
        self.exits[call_id] = dict(state)

    def pairs(self):
        combined = []
        for call_id in self.enters:
            if call_id not in self.exits:
                continue
            entry  = {'%s_entry' % k: v for k, v in self.enters[call_id].items()}
            exit_  = {'%s_exit'  % k: v for k, v in self.exits[call_id].items()}
            merged = {}
            merged.update(entry)
            merged.update(exit_)
            combined.append(merged)
        return combined

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PairedTraceStore:
    def __init__(self):
        self.enters = {}
        self.exits  = {}

    def add_enter(self, call_id, state):
        self.enters[call_id] = dict(state)

    def add_exit(self, call_id, state):
        self.exits[call_id] = dict(state)

    def pairs(self):
        combined = []
        for call_id in self.enters:
            if call_id not in self.exits:
                continue
            entry  = {&#x27;%s_entry&#x27; % k: v for k, v in self.enters[call_id].items()}
            exit_  = {&#x27;%s_exit&#x27;  % k: v for k, v in self.exits[call_id].items()}
            merged = {}
            merged.update(entry)
            merged.update(exit_)
            combined.append(merged)
        return combined
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify pairing with a simple example.

<!--
############
pts = PairedTraceStore()
pts.add_enter(1, {'a': 3, 'b': 3, 'c': 3})
pts.add_exit (1, {'a': 3, 'b': 3, 'c': 3, 'return': 'equilateral'})
pairs = pts.pairs()
assert len(pairs) == 1
assert pairs[0]['a_entry'] == 3
assert pairs[0]['a_exit']  == 3
assert pairs[0]['return_exit'] == 'equilateral'
assert 'return_entry' not in pairs[0]
print('PairedTraceStore ok')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
pts = PairedTraceStore()
pts.add_enter(1, {&#x27;a&#x27;: 3, &#x27;b&#x27;: 3, &#x27;c&#x27;: 3})
pts.add_exit (1, {&#x27;a&#x27;: 3, &#x27;b&#x27;: 3, &#x27;c&#x27;: 3, &#x27;return&#x27;: &#x27;equilateral&#x27;})
pairs = pts.pairs()
assert len(pairs) == 1
assert pairs[0][&#x27;a_entry&#x27;] == 3
assert pairs[0][&#x27;a_exit&#x27;]  == 3
assert pairs[0][&#x27;return_exit&#x27;] == &#x27;equilateral&#x27;
assert &#x27;return_entry&#x27; not in pairs[0]
print(&#x27;PairedTraceStore ok&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### PairedInstrumentor
 
`PairedInstrumentor` extends `ScopedInstrumentor`. Instead of writing
to a flat `TraceStore` it routes `ENTER` observations to
`paired_store.add_enter` and `EXIT` observations to
`paired_store.add_exit`, keyed by the integer call id from `CallStack`.
The `run` method is inherited unchanged from `Instrumentor`.

<!--
############
class PairedInstrumentor(ScopedInstrumentor):
    def __init__(self, paired_store, interesting=default_interesting):
        self.paired_store = paired_store
        self.store        = TraceStore()  # unused but satisfies super().__init__
        self.interesting  = interesting
        self.call_stack   = CallStack()

    def _tracer(self, frame, event, arg):
        if event not in ('call', 'return'):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith('_'):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == 'call':
            mid = self.call_stack.enter(cxt.method)
            _, call_id = mid
            self.paired_store.add_enter(call_id, cxt.parameters(all_vars))
        else:
            mid = self.call_stack.current()
            _, call_id = mid
            state = dict(all_vars)
            if self.interesting('return', arg):
                state['return'] = arg
            self.paired_store.add_exit(call_id, state)
            self.call_stack.leave()
        return self._tracer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PairedInstrumentor(ScopedInstrumentor):
    def __init__(self, paired_store, interesting=default_interesting):
        self.paired_store = paired_store
        self.store        = TraceStore()  # unused but satisfies super().__init__
        self.interesting  = interesting
        self.call_stack   = CallStack()

    def _tracer(self, frame, event, arg):
        if event not in (&#x27;call&#x27;, &#x27;return&#x27;):
            return self._tracer
        cxt = Context(frame)
        if cxt.method.startswith(&#x27;_&#x27;):
            return self._tracer
        all_vars = {k: v for k, v in cxt.extract_vars(frame).items()
                    if self.interesting(k, v)}
        if event == &#x27;call&#x27;:
            mid = self.call_stack.enter(cxt.method)
            _, call_id = mid
            self.paired_store.add_enter(call_id, cxt.parameters(all_vars))
        else:
            mid = self.call_stack.current()
            _, call_id = mid
            state = dict(all_vars)
            if self.interesting(&#x27;return&#x27;, arg):
                state[&#x27;return&#x27;] = arg
            self.paired_store.add_exit(call_id, state)
            self.call_stack.leave()
        return self._tracer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### collect_pairs
 
`collect_pairs` mirrors `collect_traces` but populates a
`PairedTraceStore` using `PairedInstrumentor`. The `interesting`
predicate is forwarded as with the other collection functions.

<!--
############
def collect_pairs(fn, inputs, interesting=default_interesting):
    paired_store = PairedTraceStore()
    instr = PairedInstrumentor(paired_store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return paired_store

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def collect_pairs(fn, inputs, interesting=default_interesting):
    paired_store = PairedTraceStore()
    instr = PairedInstrumentor(paired_store, interesting)
    for args in inputs:
        instr.run(fn, *args)
    return paired_store
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Verify collection on triangle.

<!--
############
ps = collect_pairs(triangle, triangle_inputs)
pairs = ps.pairs()
assert len(pairs) == len(triangle_inputs)
assert 'a_entry' in pairs[0]
assert 'return_exit' in pairs[0]
print('collect_pairs ok, %d pairs' % len(pairs))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ps = collect_pairs(triangle, triangle_inputs)
pairs = ps.pairs()
assert len(pairs) == len(triangle_inputs)
assert &#x27;a_entry&#x27; in pairs[0]
assert &#x27;return_exit&#x27; in pairs[0]
print(&#x27;collect_pairs ok, %d pairs&#x27; % len(pairs))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Relational invariant templates
 
With entry and exit variables in the same state dict we can write
invariant templates that span both. We generate two kinds:
 
* _Change invariants_ — `x_exit OP x_entry` for every variable that
  appears at both points. These detect whether a variable was
  preserved, increased, or decreased.
* _Return invariants_ — `return_exit OP x_entry` for every entry
  variable. These detect postconditions on the return value.
 
We reuse `binary_invariants` directly: the renamed variables
`a_entry` and `a_exit` are just variable names as far as it is
concerned.

<!--
############
def relational_invariants(entry_vars, exit_vars):
    candidates = []
    for v in entry_vars:
        ev = '%s_entry' % v
        xv = '%s_exit'  % v
        if xv in exit_vars:
            candidates.extend(binary_invariants(xv, ev))
    if 'return_exit' in exit_vars:
        for v in entry_vars:
            ev = '%s_entry' % v
            candidates.extend(binary_invariants('return_exit', ev))
    return candidates

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def relational_invariants(entry_vars, exit_vars):
    candidates = []
    for v in entry_vars:
        ev = &#x27;%s_entry&#x27; % v
        xv = &#x27;%s_exit&#x27;  % v
        if xv in exit_vars:
            candidates.extend(binary_invariants(xv, ev))
    if &#x27;return_exit&#x27; in exit_vars:
        for v in entry_vars:
            ev = &#x27;%s_entry&#x27; % v
            candidates.extend(binary_invariants(&#x27;return_exit&#x27;, ev))
    return candidates
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### RelationalEngine
 
`RelationalEngine` operates on the paired states from
`PairedTraceStore.pairs()`. It infers entry and exit variable names
from the suffix of each key in the first pair, generates relational
candidates, checks them against every pair, and returns the survivors.

<!--
############
class RelationalEngine:
    def analyze(self, paired_store):
        pairs = paired_store.pairs()
        if not pairs:
            return []
        entry_vars = sorted({k[:-6] for k in pairs[0] if k.endswith('_entry')})
        exit_vars  = sorted({k      for k in pairs[0] if k.endswith('_exit')})
        candidates = relational_invariants(entry_vars, exit_vars)
        for state in pairs:
            for inv in candidates:
                inv.test(state)
        return [inv for inv in candidates if inv.alive]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RelationalEngine:
    def analyze(self, paired_store):
        pairs = paired_store.pairs()
        if not pairs:
            return []
        entry_vars = sorted({k[:-6] for k in pairs[0] if k.endswith(&#x27;_entry&#x27;)})
        exit_vars  = sorted({k      for k in pairs[0] if k.endswith(&#x27;_exit&#x27;)})
        candidates = relational_invariants(entry_vars, exit_vars)
        for state in pairs:
            for inv in candidates:
                inv.test(state)
        return [inv for inv in candidates if inv.alive]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the relational engine on triangle.

<!--
############
ps      = collect_pairs(triangle, triangle_inputs)
rengine = RelationalEngine()
rinvs   = rengine.analyze(ps)
print('triangle relational invariants:')
for inv in rinvs:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ps      = collect_pairs(triangle, triangle_inputs)
rengine = RelationalEngine()
rinvs   = rengine.analyze(ps)
print(&#x27;triangle relational invariants:&#x27;)
for inv in rinvs:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`a_exit == a_entry`, `b_exit == b_entry`, and `c_exit == c_entry` all
survive — `triangle` does not modify its arguments, which is correct.
`return_exit` relations to the numeric entry variables do not survive
because `return` is a string, so the numeric templates are falsified
immediately.
 
Run the relational engine on sum_list.

<!--
############
ps      = collect_pairs(sum_list, sum_inputs)
rengine = RelationalEngine()
rinvs   = rengine.analyze(ps)
print('sum_list relational invariants:')
for inv in rinvs:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ps      = collect_pairs(sum_list, sum_inputs)
rengine = RelationalEngine()
rinvs   = rengine.analyze(ps)
print(&#x27;sum_list relational invariants:&#x27;)
for inv in rinvs:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`lst_exit == lst_entry` survives — `sum_list` does not modify its
input list. The return-value relations to `lst_entry` do not survive
because `lst` is a list and our numeric templates do not apply to it.
The `return_exit == total_exit` relation found earlier by the
single-point engine is a same-point binary invariant at `EXIT`, not a
pre/post relation, so it does not appear here. The two engines are
complementary.
 
### Full relational pipeline

<!--
############
def mine_relational_invariants(fn, inputs):
    paired_store = collect_pairs(fn, inputs)
    engine       = RelationalEngine()
    raw          = engine.analyze(paired_store)
    lattice      = SuppressionLattice()
    return lattice.suppress(raw)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def mine_relational_invariants(fn, inputs):
    paired_store = collect_pairs(fn, inputs)
    engine       = RelationalEngine()
    raw          = engine.analyze(paired_store)
    lattice      = SuppressionLattice()
    return lattice.suppress(raw)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the full relational pipeline on triangle.

<!--
############
rinvs = mine_relational_invariants(triangle, triangle_inputs)
print('triangle relational (suppressed):')
for inv in rinvs:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rinvs = mine_relational_invariants(triangle, triangle_inputs)
print(&#x27;triangle relational (suppressed):&#x27;)
for inv in rinvs:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Run the full relational pipeline on sum_list.

<!--
############
rinvs = mine_relational_invariants(sum_list, sum_inputs)
print('sum_list relational (suppressed):')
for inv in rinvs:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rinvs = mine_relational_invariants(sum_list, sum_inputs)
print(&#x27;sum_list relational (suppressed):&#x27;)
for inv in rinvs:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Extended Example: Newton's Method
 
Newton's method for finding square roots is a good stress test for the
miner because it has a non-trivial loop, a convergence condition, and
a clear mathematical postcondition: the return value squared should
equal the input (to within floating-point tolerance).
 
The algorithm maintains a running estimate `x` and refines it by
averaging `x` and `n/x` until consecutive estimates differ by less
than a small epsilon.

<!--
############
EPSILON = 1e-10

def newton_sqrt(n):
    x    = float(n)
    prev = 0.0
    while abs(x - prev) > EPSILON:
        prev = x
        x    = (x + n / x) / 2.0
    return x

def newton_step(x, n):
    return (x + n / x) / 2.0

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EPSILON = 1e-10

def newton_sqrt(n):
    x    = float(n)
    prev = 0.0
    while abs(x - prev) &gt; EPSILON:
        prev = x
        x    = (x + n / x) / 2.0
    return x

def newton_step(x, n):
    return (x + n / x) / 2.0
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We run the miner on a range of positive inputs. Newton's method
converges for any positive `n`, so all inputs should produce a valid
return value.

<!--
############
newton_inputs = [
    (2.0,),
    (4.0,),
    (9.0,),
    (16.0,),
    (0.25,),
    (100.0,),
]
results = mine_invariants(newton_sqrt, newton_inputs)
print('newton_sqrt single-point invariants:')
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
newton_inputs = [
    (2.0,),
    (4.0,),
    (9.0,),
    (16.0,),
    (0.25,),
    (100.0,),
]
results = mine_invariants(newton_sqrt, newton_inputs)
print(&#x27;newton_sqrt single-point invariants:&#x27;)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At `newton_sqrt:::ENTER` we expect `n >= 0` and `n > 0` to survive
since all our inputs were positive. At `newton_sqrt:::EXIT` we expect
`return >= 0` and `return > 0`.
 
Now the relational analysis, which is where the interesting postcondition
lives.

<!--
############
rinvs = mine_relational_invariants(newton_sqrt, newton_inputs)
print('newton_sqrt relational (suppressed):')
for inv in rinvs:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rinvs = mine_relational_invariants(newton_sqrt, newton_inputs)
print(&#x27;newton_sqrt relational (suppressed):&#x27;)
for inv in rinvs:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`return_exit >= n_entry` should not survive in general — `sqrt(0.25)`
returns `0.5` which is less than `0.25` — and indeed it does not.
`return_exit == n_entry` also does not survive. What survives is
`return_exit > 0` — the square root of a positive number is positive —
and the variable preservation invariants for intermediate locals.
 
The miner cannot discover `return_exit ** 2 == n_entry` because our
template set does not include quadratic relations. That is an
intentional limitation: Daikon itself uses a richer template language
including polynomial invariants. Adding a template is straightforward:

<!--
############
def quadratic_invariants(ret_var, input_var):
    return [
        Invariant('%s * %s == %s' % (ret_var, ret_var, input_var),
                  lambda s, r=ret_var, n=input_var:
                      isinstance(s.get(r), float) and
                      isinstance(s.get(n), float) and
                      abs(s[r] * s[r] - s[n]) < 1e-6),
    ]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def quadratic_invariants(ret_var, input_var):
    return [
        Invariant(&#x27;%s * %s == %s&#x27; % (ret_var, ret_var, input_var),
                  lambda s, r=ret_var, n=input_var:
                      isinstance(s.get(r), float) and
                      isinstance(s.get(n), float) and
                      abs(s[r] * s[r] - s[n]) &lt; 1e-6),
    ]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Re-run the relational engine with the quadratic template added.

<!--
############
ps         = collect_pairs(newton_sqrt, newton_inputs)
pairs      = ps.pairs()
entry_vars = sorted({k[:-6] for k in pairs[0] if k.endswith('_entry')})
exit_vars  = sorted({k      for k in pairs[0] if k.endswith('_exit')})
candidates = relational_invariants(entry_vars, exit_vars)
candidates += quadratic_invariants('return_exit', 'n_entry')
for state in pairs:
    for inv in candidates:
        inv.test(state)
survivors = [inv for inv in candidates if inv.alive]
lattice   = SuppressionLattice()
survivors = lattice.suppress(survivors)
print('newton_sqrt with quadratic template:')
for inv in survivors:
    print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ps         = collect_pairs(newton_sqrt, newton_inputs)
pairs      = ps.pairs()
entry_vars = sorted({k[:-6] for k in pairs[0] if k.endswith(&#x27;_entry&#x27;)})
exit_vars  = sorted({k      for k in pairs[0] if k.endswith(&#x27;_exit&#x27;)})
candidates = relational_invariants(entry_vars, exit_vars)
candidates += quadratic_invariants(&#x27;return_exit&#x27;, &#x27;n_entry&#x27;)
for state in pairs:
    for inv in candidates:
        inv.test(state)
survivors = [inv for inv in candidates if inv.alive]
lattice   = SuppressionLattice()
survivors = lattice.suppress(survivors)
print(&#x27;newton_sqrt with quadratic template:&#x27;)
for inv in survivors:
    print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`return_exit * return_exit == n_entry` now survives, which is the
mathematical specification of the square root function. This shows how
the template set determines what the miner can discover: the
infrastructure is general, and extending coverage is a matter of
adding more `Invariant` objects to the candidate list.
 
Also run the step function to observe its internal invariants.

<!--
############
step_inputs = [(x, n) for n in [4.0, 9.0, 16.0]
                       for x in [float(n), float(n)/2, 1.0]]
results = mine_invariants(newton_step, step_inputs)
print('newton_step single-point invariants:')
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print('  ', inv)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
step_inputs = [(x, n) for n in [4.0, 9.0, 16.0]
                       for x in [float(n), float(n)/2, 1.0]]
results = mine_invariants(newton_step, step_inputs)
print(&#x27;newton_step single-point invariants:&#x27;)
for point, invs in sorted(results.items()):
    print(point)
    for inv in invs:
        print(&#x27;  &#x27;, inv)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`newton_step:::ENTER` shows `x > 0` and `n > 0` (all our inputs were
positive). `newton_step:::EXIT` shows `return > 0` — the refined
estimate is always positive when both `x` and `n` are positive, which
is a genuine loop invariant of Newton's method.
 
## Utilities

<!--
############
def format_results(results):
    lines = []
    for point in sorted(results.keys()):
        lines.append(point)
        for inv in results[point]:
            lines.append('    ' + str(inv))
    return '\n'.join(lines)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def format_results(results):
    lines = []
    for point in sorted(results.keys()):
        lines.append(point)
        for inv in results[point]:
            lines.append(&#x27;    &#x27; + str(inv))
    return &#x27;\n&#x27;.join(lines)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Format and print the scoped triangle results.

<!--
############
results = mine_invariants_scoped(triangle, triangle_inputs)
print(format_results(results))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
results = mine_invariants_scoped(triangle, triangle_inputs)
print(format_results(results))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Performance
The performance of this miner is dominated by the candidate checking phase,
which scales at approximately $$O(T \times V^2)$$, where $$T$$ is the number
of observed traces and $$V$$ is the number of variables in scope, making it
reasonably fast for typical functions but computationally expensive as the
variable count grows.
 
## Conclusion
 
Our implementation is a simplified version of the full Daikon system,
but it contains the core ideas of dynamic invariant mining:
 
1. **The specification gap**: Most software has no formal 
   specification. By mining invariants, we create a "de facto" spec 
   that describes how the code actually behaves.
 
2. **Templates are the limit**: As seen with `newton_sqrt`, the miner 
   can only *see* what we give it templates for. The trade-off is 
   between computational cost (more templates = more checks) and 
   expressiveness.
 
3. **Automated assertions**: These mined invariants can be
   turned into `assert` statements, giving you an approximate
   oracle that flags when future changes break previously observed
   behavior.
 
Dynamic analysis doesn't replace formal proof or manual testing, but 
provides an automated, and hence low-effort way to document behavior and
catch regressions.
 
**Note:** Dynamic invariant mining is the dual of Static analysis for
invariant (we can also call these oracles in testing parlance) inference.
The main difference is that the invariants being inferred is **approximate**
but **precise**, while static analysis invariants are **sound** but
**imprecise**. Bridging the gap is impossible if arbitrary programs are the
subjects.

Dynamic invariant mining is also a whitebox dual of blackbox specification
inference similar to how (code) path coverage is a whitebox dual of input
coverage using k-paths.
 
## References
 
[^ernst2001daikon]: Michael D. Ernst, Jake Cockrell, William G. Griswold, David Notkin. "Dynamically Discovering Likely Program Invariants to Support Program Evolution." IEEE Transactions on Software Engineering, 27(2):99–123, 2001.
 
[^ernst2007daikon]: Michael D. Ernst et al. "The Daikon system for dynamic detection of likely invariants." Science of Computer Programming, 69(1–3):35–45, 2007.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2026-05-09-simple-invariant-miner.py).


The installable python wheel `simpleinvariantminer` is available [here](/py/simpleinvariantminer-0.0.1-py2.py3-none-any.whl).

