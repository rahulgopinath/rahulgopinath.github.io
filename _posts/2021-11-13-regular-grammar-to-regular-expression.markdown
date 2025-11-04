---
published: true
title: Converting a Regular Grammar to a Regular Expression
layout: post
comments: true
tags: parsing
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
This post shows you how to convert a regular grammar to a regular expression
using the state elimination algorithm. The intuition in this algorithm is to
note that every nonterminal is just a way point between two sets of states
A and B. So, Eliminating one nonterminal can be achieved by linking all pairs
between A and B with the equivalent regular expression transmissions.
We start with importing the prerequisites

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">Fuzzing With Regular Expressions</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl">rxregular-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/23/regular-expression-to-regular-grammar/">Regular Expression to Regular Grammar</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl">rxcanonical-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/24/canonical-regular-grammar/">Converting a Regular Expression to DFA using Regular Grammar</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxcanonical

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxcanonical
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us define a grammar that we want to extract the regular expression for.

<!--
############
G_1 = {"<S>": [["a", "<A>"]],
    "<A>" : [
        [rxcanonical.NT_EMPTY],
        ["b","<S>"],
        ["b","<A>"],
        ["a","<B>"],
    ],
    "<B>" : [
        ["b",rxcanonical.NT_EMPTY],
        ["a","<S>"]
    ],
    rxcanonical.NT_EMPTY : [[]]}
S_1 = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G_1 = {&quot;&lt;S&gt;&quot;: [[&quot;a&quot;, &quot;&lt;A&gt;&quot;]],
    &quot;&lt;A&gt;&quot; : [
        [rxcanonical.NT_EMPTY],
        [&quot;b&quot;,&quot;&lt;S&gt;&quot;],
        [&quot;b&quot;,&quot;&lt;A&gt;&quot;],
        [&quot;a&quot;,&quot;&lt;B&gt;&quot;],
    ],
    &quot;&lt;B&gt;&quot; : [
        [&quot;b&quot;,rxcanonical.NT_EMPTY],
        [&quot;a&quot;,&quot;&lt;S&gt;&quot;]
    ],
    rxcanonical.NT_EMPTY : [[]]}
S_1 = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us first define a few helpr functions for regular expression conversion.
we represent individual regular expressions by lists. So, concatenation is
just list addition. An empty list represents epsilon. We justneed to take
care of two meta symbols, kleene star and alternative, which is represented
as below.

<!--
############
def star(r):
    if not r: return []
    return [('star', r)]

def union(r1, r2):
    if not r1: return r2
    if not r2: return r1
    return [('or', r1, r2)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def star(r):
    if not r: return []
    return [(&#x27;star&#x27;, r)]

def union(r1, r2):
    if not r1: return r2
    if not r2: return r1
    return [(&#x27;or&#x27;, r1, r2)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define how to convert a regular expression to its string form.

<!--
############
def convert_rex(rex):
    if rex[0] == 'or':
        return '(%s|%s)' % (convert_rexs(rex[1]), convert_rexs(rex[2]))
    elif rex[0] == 'star':
        v = convert_rexs(rex[1])
        if len(v) > 1: # | or concat
            return "(%s)*" % v
        else:
            return "%s*" % v
    else:
        return rex

def convert_rexs(rexs):
    r = ''
    for rex in rexs:
        r += convert_rex(rex)
    return r

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def convert_rex(rex):
    if rex[0] == &#x27;or&#x27;:
        return &#x27;(%s|%s)&#x27; % (convert_rexs(rex[1]), convert_rexs(rex[2]))
    elif rex[0] == &#x27;star&#x27;:
        v = convert_rexs(rex[1])
        if len(v) &gt; 1: # | or concat
            return &quot;(%s)*&quot; % v
        else:
            return &quot;%s*&quot; % v
    else:
        return rex

def convert_rexs(rexs):
    r = &#x27;&#x27;
    for rex in rexs:
        r += convert_rex(rex)
    return r
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Adjuscency Matrix

Using the regular grammar directly is too unwieldy.
Let us first extract the states, and transitions to build an adjuscency
matrix. We do not want any incoming transitions to the start state, and we do
not want any outgoing transitions from the accept. So, let us also define
two phony states for these.

<!--
############
def adjuscency_matrix(grammar, start, stop):
    my_states = {k:i for i,k in enumerate(sorted(grammar.keys()))}
    new_start, new_stop = len(my_states) + 1, len(my_states) + 2
    states = set(my_states.values()) | {new_start, new_stop}
    regex = {(i, j): None for i in states for j in states}

    for k in grammar:
        for r in grammar[k]:
            if not r:
                assert k == rxcanonical.NT_EMPTY
            elif len(r) == 1:
                assert r[0] == rxcanonical.NT_EMPTY
                src, dst, trans  = my_states[k], my_states[r[0]], []
                regex[(src, dst)] = union(regex[(src, dst)], [])
            else:
                src, dst, trans  = my_states[k], my_states[r[1]], r[0]
                regex[(src, dst)] = union(regex[(src, dst)], [trans])
    regex[(new_start, my_states[start])] = [] # empty transition
    regex[(my_states[stop], new_stop)] = [] # empty transition
    return regex, states, new_start, new_stop

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def adjuscency_matrix(grammar, start, stop):
    my_states = {k:i for i,k in enumerate(sorted(grammar.keys()))}
    new_start, new_stop = len(my_states) + 1, len(my_states) + 2
    states = set(my_states.values()) | {new_start, new_stop}
    regex = {(i, j): None for i in states for j in states}

    for k in grammar:
        for r in grammar[k]:
            if not r:
                assert k == rxcanonical.NT_EMPTY
            elif len(r) == 1:
                assert r[0] == rxcanonical.NT_EMPTY
                src, dst, trans  = my_states[k], my_states[r[0]], []
                regex[(src, dst)] = union(regex[(src, dst)], [])
            else:
                src, dst, trans  = my_states[k], my_states[r[1]], r[0]
                regex[(src, dst)] = union(regex[(src, dst)], [trans])
    regex[(new_start, my_states[start])] = [] # empty transition
    regex[(my_states[stop], new_stop)] = [] # empty transition
    return regex, states, new_start, new_stop
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
regex,states, start, stop = adjuscency_matrix(G_1, S_1, rxcanonical.NT_EMPTY)
for i in states:
    print(' '.join(['%s,%s: %s' % (i, j, regex[(i,j)]) for j in states]))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
regex,states, start, stop = adjuscency_matrix(G_1, S_1, rxcanonical.NT_EMPTY)
for i in states:
    print(&#x27; &#x27;.join([&#x27;%s,%s: %s&#x27; % (i, j, regex[(i,j)]) for j in states]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now define our conversion routine. The idea is very simple,
remove one state at a time. For any pair of states such that
`<src> -> (a) -> <q> -> (b) -> <dst>`, replace it with 
`<src> -> (ab) -> <dst>

<!--
############
def rg_to_regex(grammar, start, stop=rxcanonical.NT_EMPTY):
    regex, states, new_start, new_stop = adjuscency_matrix(grammar, start, stop)

    for q in sorted(states - {new_start, new_stop}):
        for i in states - {q}:
            for j in states - {q}:
                r_iq, r_qq, r_qj, r_ij = regex[(i, q)], regex[(q, q)], \
                        regex[(q, j)], regex[(i, j)]
                if r_iq is None or r_qj is None: continue
                new_part = r_iq + star(r_qq) + r_qj
                regex[(i, j)] = union(r_ij, new_part)

    return regex[(new_start, new_stop)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def rg_to_regex(grammar, start, stop=rxcanonical.NT_EMPTY):
    regex, states, new_start, new_stop = adjuscency_matrix(grammar, start, stop)

    for q in sorted(states - {new_start, new_stop}):
        for i in states - {q}:
            for j in states - {q}:
                r_iq, r_qq, r_qj, r_ij = regex[(i, q)], regex[(q, q)], \
                        regex[(q, j)], regex[(i, j)]
                if r_iq is None or r_qj is None: continue
                new_part = r_iq + star(r_qq) + r_qj
                regex[(i, j)] = union(r_ij, new_part)

    return regex[(new_start, new_stop)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
rxg = rg_to_regex(G_1, S_1)
print(rxg)
rx = convert_rexs(rxg)
print(rx)
import re
rf = fuzzer.LimitFuzzer(G_1)
for i in range(100):
    v = rf.fuzz(S_1)
    print(v)
    assert re.match(rx, v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rxg = rg_to_regex(G_1, S_1)
print(rxg)
rx = convert_rexs(rxg)
print(rx)
import re
rf = fuzzer.LimitFuzzer(G_1)
for i in range(100):
    v = rf.fuzz(S_1)
    print(v)
    assert re.match(rx, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-11-13-regular-grammar-to-regular-expression.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-11-13-regular-grammar-to-regular-expression.py).


The installable python wheel `rgtorx` is available [here](/py/rgtorx-0.0.1-py2.py3-none-any.whl).

