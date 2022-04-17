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
(my_stk := to_stack(example))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
(my_stk := to_stack(example))
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
(my_ds := from_stack(my_stk))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
(my_ds := from_stack(my_stk))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-04-17-python-iterative-copy.py).


