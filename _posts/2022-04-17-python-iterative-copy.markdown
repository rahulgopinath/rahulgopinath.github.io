---
published: true
title: Iterative deep copy of Python data structures
layout: post
comments: true
tags: deepcopy
categories: post
---

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
One of the problems when working with Python is that, even though many
libraries use data structures making use of recursion, the recursion stack in
Python is limited. Python starts with a recursion budget of 1000 function
calls which is easy to exhaust. Such data structures include
`JSON` and `pickle`. Even simple deep copy of a Python data structure from
`copy.deepcopy()` makes use of recursion. Here is a simple recipe that lets
you serialize and duplicate deep data structures.

The idea is to turn any data structure into a series of instructions in a
[concatenative language](https://en.wikipedia.org/wiki/Concatenative_programming_language)
that recreates the data structure. A concatenative language is defined by a
sequence of instructions that is Turing complete. Hence, it is suitable for
what we want to do.
## To concatenative instructions
### Serialize
Next, we define how to serialize a deep data structure.  Here is our subject.

<!--
############
example = [{'a':10, 'b':20, 'c': 30}, ['c', ('d', 'e', 1)]]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
example = [{&#x27;a&#x27;:10, &#x27;b&#x27;:20, &#x27;c&#x27;: 30}, [&#x27;c&#x27;, (&#x27;d&#x27;, &#x27;e&#x27;, 1)]]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
To turn this to a linear sequence of instructions, we make use of two stacks.
The `to_expand` contains a stack of items that still needs to be processed,
and `expanded` is a stack of concatenative instructions to build the data
structure that was input. The idea is that the following stack

```
'a' 'b' 'c' 'd' 2 <set> 3 <list>
```
represents
```
'a' 'b' {'c', 'd'} 3 <list>
```
which in turn represents the following Python data structure.
```
['a', 'b', {'c', 'd'}]
```

<!--
############
def to_stack(ds):
    expanded = []
    to_expand = [ds]
    while to_expand:
        ds, *to_expand = to_expand
        if type(ds) in {list, set, tuple}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
        elif type(ds) in {dict}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds.items()) + to_expand
        else:
            expanded.append(ds)
    return list(reversed(expanded))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_stack(ds):
    expanded = []
    to_expand = [ds]
    while to_expand:
        ds, *to_expand = to_expand
        if type(ds) in {list, set, tuple}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
        elif type(ds) in {dict}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds.items()) + to_expand
        else:
            expanded.append(ds)
    return list(reversed(expanded))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see how it works

<!--
############
print(my_stk := to_stack(example))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(my_stk := to_stack(example))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Deserialize
To deserialize, we do the opposite.

<!--
############
def get_children(result_stk):
    l = result_stk.pop()
    return [result_stk.pop() for i in range(l)]

def from_stack(stk):
    i = 0
    result_stk = []
    while stk:
        item, *stk = stk
        if item == list:
            ds = get_children(result_stk)
            result_stk.append(ds)
        elif item == set:
            ds = get_children(result_stk)
            result_stk.append(set(ds))
        elif item == tuple:
            ds = get_children(result_stk)
            result_stk.append(tuple(ds))
        elif item == dict:
            ds = get_children(result_stk)
            result_stk.append({i[0]:i[1]for i in ds})
        else:
            result_stk.append(item)
    return result_stk[0]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_children(result_stk):
    l = result_stk.pop()
    return [result_stk.pop() for i in range(l)]

def from_stack(stk):
    i = 0
    result_stk = []
    while stk:
        item, *stk = stk
        if item == list:
            ds = get_children(result_stk)
            result_stk.append(ds)
        elif item == set:
            ds = get_children(result_stk)
            result_stk.append(set(ds))
        elif item == tuple:
            ds = get_children(result_stk)
            result_stk.append(tuple(ds))
        elif item == dict:
            ds = get_children(result_stk)
            result_stk.append({i[0]:i[1]for i in ds})
        else:
            result_stk.append(item)
    return result_stk[0]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see how it works

<!--
############
print(my_ds := from_stack(my_stk))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(my_ds := from_stack(my_stk))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Cyclic data structures
One of the nice things about using a concatenative language for
representing nested structures is that it is easy to modify it to support
linked data structures. Here is such an example.

<!--
############
dex = {'a':10, 'b':20, 'c': 30}
gexample = [dex, 40, 50]
dex['e'] = gexample
print('repr', repr(gexample))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dex = {&#x27;a&#x27;:10, &#x27;b&#x27;:20, &#x27;c&#x27;: 30}
gexample = [dex, 40, 50]
dex[&#x27;e&#x27;] = gexample
print(&#x27;repr&#x27;, repr(gexample))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
To handle this we first need a data structure for references.

<!--
############
class Ref__:
    def __init__(self, ds): self._id = id(ds)
    def __str__(self): return str('$'+ str(self._id))
    def __repr__(self): return str('$'+str(self._id))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Ref__:
    def __init__(self, ds): self._id = id(ds)
    def __str__(self): return str(&#x27;$&#x27;+ str(self._id))
    def __repr__(self): return str(&#x27;$&#x27;+str(self._id))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Serialize
Next we define how to convert a data structure to a concatenative definition.

<!--
############
def to_concatenative(ds):
    expanded = []
    to_expand = [ds]
    seen = set()
    while to_expand:
        ds, *to_expand = to_expand
        if id(ds) in seen:
            expanded.append(Ref__(ds))
        elif type(ds) in {list, set, tuple}:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
            seen.add(id(ds))
        elif type(ds) in {tuple}:
            assert False, 'tuples not supported'
        elif type(ds) in {dict}:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            seen.add(id(ds))
            to_expand = [[i,j] for i,j in ds.items()] + to_expand
        elif hasattr(ds, '__dict__'):
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            # to_expand = children(ds) + to_expand <- we stop at any custom
            seen.add(id(ds))
        else:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(ds)
            seen.add(id(ds))
    return list(reversed(expanded))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_concatenative(ds):
    expanded = []
    to_expand = [ds]
    seen = set()
    while to_expand:
        ds, *to_expand = to_expand
        if id(ds) in seen:
            expanded.append(Ref__(ds))
        elif type(ds) in {list, set, tuple}:
            expanded.append(Ref__(ds))
            expanded.append(&#x27;def&#x27;)
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
            seen.add(id(ds))
        elif type(ds) in {tuple}:
            assert False, &#x27;tuples not supported&#x27;
        elif type(ds) in {dict}:
            expanded.append(Ref__(ds))
            expanded.append(&#x27;def&#x27;)
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            seen.add(id(ds))
            to_expand = [[i,j] for i,j in ds.items()] + to_expand
        elif hasattr(ds, &#x27;__dict__&#x27;):
            expanded.append(Ref__(ds))
            expanded.append(&#x27;def&#x27;)
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            # to_expand = children(ds) + to_expand &lt;- we stop at any custom
            seen.add(id(ds))
        else:
            expanded.append(Ref__(ds))
            expanded.append(&#x27;def&#x27;)
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(ds)
            seen.add(id(ds))
    return list(reversed(expanded))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 So, here is how the concatenative definition looks like. As you can see,
all the nesting is eliminated using naming of data structures.

<!--
############
print('expanded', my_g := to_concatenative(gexample))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(&#x27;expanded&#x27;, my_g := to_concatenative(gexample))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Deserialize
Next, to recreate the structure

<!--
############
def from_concatenative(stk):
    i = 0
    result_stk = []
    defs = {}
    while stk:
        item, *stk = stk
        if item == 'def':
            iid = result_stk.pop()._id
            kind = result_stk.pop()
            if kind == list:
                ds = get_children(result_stk)
                defs[iid] = list(ds)
            elif kind == set:
                ds = get_children(result_stk)
                defs[iid] = set(ds)
            elif kind == tuple:
                ds = get_children(result_stk)
                assert False, 'tuples not supported'
            elif kind == dict:
                ds = get_children(result_stk)
                defs[iid] = {i:None for i in ds}
            else:
                ds = result_stk.pop()
                defs[iid] = ds
        else:
            result_stk.append(item)
    assert len(result_stk) == 1
    return result_stk[0], defs

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def from_concatenative(stk):
    i = 0
    result_stk = []
    defs = {}
    while stk:
        item, *stk = stk
        if item == &#x27;def&#x27;:
            iid = result_stk.pop()._id
            kind = result_stk.pop()
            if kind == list:
                ds = get_children(result_stk)
                defs[iid] = list(ds)
            elif kind == set:
                ds = get_children(result_stk)
                defs[iid] = set(ds)
            elif kind == tuple:
                ds = get_children(result_stk)
                assert False, &#x27;tuples not supported&#x27;
            elif kind == dict:
                ds = get_children(result_stk)
                defs[iid] = {i:None for i in ds}
            else:
                ds = result_stk.pop()
                defs[iid] = ds
        else:
            result_stk.append(item)
    assert len(result_stk) == 1
    return result_stk[0], defs
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
my_gds, defs = from_concatenative(my_g)
print(my_gds)
for k in defs:
    print(k)
    print("   ", defs[k])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_gds, defs = from_concatenative(my_g)
print(my_gds)
for k in defs:
    print(k)
    print(&quot;   &quot;, defs[k])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Reconstruct
This structure still contains references. So, we need to reconstruct the
actual data

<!--
############
def reconstruct(defs, root):
    for k in defs:
        ds = defs[k]
        if type(ds) in {list, set}: # container
            for i,kx in enumerate(ds):
                if type(kx) == Ref__: # Ref
                    ds[i] = defs[kx._id]
                else:
                    ds[i] = kx

        elif type(ds) in {dict}: # container
            keys = list(ds.keys())
            ds.clear()
            for i,kx in enumerate(keys):
                if type(kx) == Ref__: # Ref
                    k,v = defs[kx._id]
                    if type(v) == Ref__:
                        ds[k] = defs[v._id]
                    else:
                        ds[k] = v
                else:
                    assert False
                    ds[kx] = kx
        else:
            #ds = defs[k][1]
            ds = ds
            pass
    return defs[root]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def reconstruct(defs, root):
    for k in defs:
        ds = defs[k]
        if type(ds) in {list, set}: # container
            for i,kx in enumerate(ds):
                if type(kx) == Ref__: # Ref
                    ds[i] = defs[kx._id]
                else:
                    ds[i] = kx

        elif type(ds) in {dict}: # container
            keys = list(ds.keys())
            ds.clear()
            for i,kx in enumerate(keys):
                if type(kx) == Ref__: # Ref
                    k,v = defs[kx._id]
                    if type(v) == Ref__:
                        ds[k] = defs[v._id]
                    else:
                        ds[k] = v
                else:
                    assert False
                    ds[kx] = kx
        else:
            #ds = defs[k][1]
            ds = ds
            pass
    return defs[root]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
v = reconstruct(defs, my_gds._id)
print(v)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = reconstruct(defs, my_gds._id)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-04-17-python-iterative-copy.py).


