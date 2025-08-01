---
published: true
title: Learning Regular Languages with L* Algorithm
layout: post
comments: true
tags: regular-grammars induction
categories: post
---

TLDR; This tutorial is a complete implementation of Angluin's L-star algorithm
with PAC learning for inferring input grammars of blackbox programs in Python
(i.e. without using equivalence queries). Such grammars are typically useful
for fuzzing such programs.
The Python interpreter is embedded so that you
can work through the implementation steps.
 
In many previous posts, I have discussed how to
[parse with](/post/2023/11/03/matching-regular-expressions/),
[fuzz with](/post/2021/10/22/fuzzing-with-regular-expressions/), and
manipulate regular and context-free grammars. However, in many cases, such
grammars may be unavailable. If you are given a blackbox program, where the
program indicates in some way that the input was accepted or not, what can
we do to learn the actual input specification of the blackbox? In such cases,
the best option is to try and learn the input specification.

This particular research field which investigates how to learn the input
specification of blackbox programs is called blackbox *grammar inference* or
*grammatical inference* (see the **Note** at the end for a discussion on other
names). In this post, I will discuss one of the classic algorithms for
learning the input specification called L\*. The L\* algorithm was invented by
Dana Angluin in 1987 [^angluin1987]. While the initial algorithm used what is
called an equivalence query, which assumes that you can check the correctness
of the learned grammar separate from yes/no oracle, Angluin in the same paper
also talks about how to update this algorithm to make use of the PAC
(*Probably Approximately Correct*) framework from Valiant [^valiant1984].
Angluin expands on this further in 1988 [^angluin1988].


# Definitions

* Input symbol: A single symbol that is consumed by the machine which can move
  it from one state to another. The set of such symbols is called an alphabet,
  and is represented by $$ A $$.
* Membership query: A string that is passed to the blackbox. The blackbox
  answers yes or no.
* Equivalence query: A grammar that is passed to the teacher as a hypothesis
  of what the target language is. The teacher answers yes or a counter
  example that behaves differently on the blackbox and the hypothesis grammar.
* Prefix closed: a set is prefix closed if all prefixes of any of its elements
  are also in the same set.
* Suffix closed: a set is suffix closed if all suffixes of any of its elements
  are also in the same set.
* Observation table: A table whose rows correspond to the *candidate states*.
  The rows are made up of prefix strings that can reach given states ---
  commonly represented as $$ S $$, but here we will denote these by $$ P $$
  for prefixes --- and the columns are made up of suffix strings that serves
  to distinguish these states --- commonly expressed as $$ E $$ for
  extensions, but we will use $$ S $$ to denote suffixes here. The table
  contains auxiliary rows that extends each item $$ p \in P $$ with each
  alphabet $$ a \in A $$ as we discuss later in *closedness*.
  This table defines the language inferred by the algorithm. The contents of
  the table are the answers from the oracle on a string composed of the row
  and column labels --- prefix + suffix. That is  $$ T[s,e] = O(s.e) $$.
  The table has two properties: *closedness* and *consistency*.
  If these are not met at any time, we take to resolve it.
* The state: A state in the DFA is represented by a prefix in the observation
  table, and is named by the pattern of 1s and 0s in the cell contents.
  We represent a state corresponding the prefix $$ p $$ as $$ [p] $$.
* Closedness of the observation table means that for each $$ p \in P $$ and
  each $$ a \in A $$, the state represented by the auxiliary row $$ [p.a] $$
  (i.e., its contents) exists in $$ P $$. That is, there is some
  $$ p' \in P $$ such that $$ [p.a] == [p'] $$. The idea is that, the state
  corresponding to $$ [p] $$ accepts alphabet $$ a $$ and transitions to the
  state $$ [p'] $$, and $$ p' $$ must be in the main set of rows $$ P $$.
* Consistency of the observation table means that if two prefixes represents
  the same state (i.e. the contents of two rows are equal), that is
  $$ [p1] = [p2] $$ then $$ [p1 . a] = [p2 . a] $$ for all alphabets.
  The idea is that if two prefixes reach the state, then when fed any
  alphabet, both prefixes should transition to the same next state
  (represented by the pattern produced by the suffixes).
* The candidate states `P` is prefix closed, while the set of suffixes `S`
  is suffix closed.


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
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">Fuzzing With Regular Expressions</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl">cfgrandomsample-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/07/27/random-sampling-from-context-free-grammar/">Uniform Random Sampling of Strings from Context-Free Grammar</a>".</li>
<li><a href="https://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl">cfgremoveepsilon-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/29/remove-epsilons/">Remove Empty (Epsilon) Rules From a Context-Free Grammar.</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
#### Prerequisites

We need the fuzzer to generate inputs to parse and also to provide some
utilities such as conversion of regular expression to grammars, random
sampling from grammars etc. Hence, we import all that.

<!--
############
import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import cfgrandomsample
import cfgremoveepsilon
import math
import random

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import cfgrandomsample
import cfgremoveepsilon
import math
import random
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Grammar Inference

Let us start with the assumption that the blackbox program
accepts a [regular language](https://en.wikipedia.org/wiki/Regular_language).
By *accept* I mean that the program does some processing with input given
rather than error out. For example, if the blackbox actually contained a URL
parser, it will *accept* a string that look like a URL, and *reject* strings
that are not in the URL format.
 
So, given such a program, and you are not allowed to peek inside the program
source code, how do you find what the program accepts? assuming that the
program accepts a regular language, we can start by constructing a
[DFA](https://en.wikipedia.org/wiki/Deterministic_finite_automaton) (A
deterministic finite state machine).
 
Finite state machines are of course the bread and butter of
computer science. The idea is that the given program can be represented as a
set of discrete states, and transitions between them. The DFA is
initialized to the start state. A state transitions to another when it is
fed an input symbol. Some states are marked as *accepting*. That is, starting
from the start state, and after consuming all the symbols in the input, the
state reached is one of the accept states, then we say that the input was
*accepted* by the machine.
 
Given this information, how would we go about reconstructing the machine?
An intuitive approach is to recognize that a state is represented by exactly
two sets of strings. The first set of strings (the prefixes) is how the state
can be reached from the start state. The second set of strings are
continuations of input from the current state that distinguishes
this state from every other state. That is, two states can be distinguished
by the DFA if and only if there is at least one suffix string, which when fed
into the pair of states, produces different answers -- i.e. for one, the
machine accepts (or reaches one of the accept states), while for the other
is rejected (or the end state is not an accept).

Given this information, a data structure for keeping track of our experiments
presents itself -- the *observation table* where we keep our prefix strings
as rows, and suffix strings as columns. The cell content simply marks
whether program accepted the prefix + suffix string or not. So, here
is our data structure.

## ObservationTable

We initialize the observation table with the alphabet. We keep the table
itself as an internal dict `_T`. We also keep the prefixes in `P` and
suffixes in `S`.
We initialize the set of prefixes `P` to be $${\epsilon}$$
and the set of suffixes `S` also to be $$ {\epsilon} $$. We also add
a few utility functions.

<!--
############
class ObservationTable:
    def __init__(self, alphabet):
        self._T, self.P, self.S, self.A = {}, [''], [''], alphabet

    def cell(self, v, e): return self._T[v][e]

    def state(self, p):
        return '<%s>' % ''.join([str(self.cell(p,s)) for s in self.S])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable:
    def __init__(self, alphabet):
        self._T, self.P, self.S, self.A = {}, [&#x27;&#x27;], [&#x27;&#x27;], alphabet

    def cell(self, v, e): return self._T[v][e]

    def state(self, p):
        return &#x27;&lt;%s&gt;&#x27; % &#x27;&#x27;.join([str(self.cell(p,s)) for s in self.S])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using the observation table with some pre-cooked data.

<!--
############
alphabet = list('abcdefgh')
o = ObservationTable(alphabet)
o._T = {p:{'':1, 'a':0, 'ba':1, 'cba':0} for p in alphabet}
print(o.cell('a', 'ba'))
print(o.state('a'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
alphabet = list(&#x27;abcdefgh&#x27;)
o = ObservationTable(alphabet)
o._T = {p:{&#x27;&#x27;:1, &#x27;a&#x27;:0, &#x27;ba&#x27;:1, &#x27;cba&#x27;:0} for p in alphabet}
print(o.cell(&#x27;a&#x27;, &#x27;ba&#x27;))
print(o.state(&#x27;a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Convert Table to Grammar

Given the observation table, we can recover the grammar from this table
(corresponding to the DFA). The
unique cell contents of rows are states. In many cases, multiple rows may
correspond to the same state (as the cell contents are the same). 
The *start state* is given by the state that correspond to the $$\epsilon$$
row.
A state is accepting if it on query of $$ \epsilon $$ i.e. `''`,
it returns 1.

The formal
notations are as follows. The notation $$ [p] $$ means the state
corresponding to the prefix $$ p $$. The notation $$ [[p,s]] $$ means the
result of oracle for the prefix $$ p $$ and the suffix $$ s $$.
The notation $$ [p](a) $$ means the state obtained by feeding the input
symbol $$ a $$ to the state $$ [p] $$. We take
the first prefix that resulted in a particular state as its *access prefix*,
and we denote the access prefix of a state $$ s $$ by
$$ \lfloor{}s\rfloor $$ (this is not used in this post). The following
is the DFA from our table.
 
* states: $$ Q = {[p] : p \in P} $$
* start state: $$ q0 = [\epsilon] $$
* transition function: $$ [p](a) \rightarrow [p.a] $$
* accepting state: $$ F = {[p] : p \in P : [[p,\epsilon]] = 1} $$

For constructing the grammar from the table, we first identify all
distinguished states. Next, we identify the start state, followed by
accepting states. Finally, we connect states together with transitions
between them.

<!--
############
class ObservationTable(ObservationTable):
    def table_to_grammar(self):
        # Step 1: identify all distinguished states.
        prefix_to_state = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for p in self.P:
            stateid = self.state(p)
            if stateid not in states: states[stateid] = []
            states[stateid].append(p)
            prefix_to_state[p] = stateid

        for stateid in states: grammar[stateid] = []

        # Step 2: Identify the start state, which corresponds to epsilon row
        start_nt = prefix_to_state['']

        # Step 3: Identify the accepting states
        accepting = [prefix_to_state[p] for p in self.P if self.cell(p,'') == 1]
        if not accepting: return {'<start>': []}, '<start>'
        for s in accepting: grammar[s] = [['<_>']]
        grammar['<_>'] = [[]]

        # Step 4: Create the transition function
        for sid1 in states:
            first_such_row = states[sid1][0]
            for a in self.A:
                sid2 = self.state(first_such_row + a)
                grammar[sid1].append([a, sid2])

        return grammar, start_nt

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def table_to_grammar(self):
        # Step 1: identify all distinguished states.
        prefix_to_state = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for p in self.P:
            stateid = self.state(p)
            if stateid not in states: states[stateid] = []
            states[stateid].append(p)
            prefix_to_state[p] = stateid

        for stateid in states: grammar[stateid] = []

        # Step 2: Identify the start state, which corresponds to epsilon row
        start_nt = prefix_to_state[&#x27;&#x27;]

        # Step 3: Identify the accepting states
        accepting = [prefix_to_state[p] for p in self.P if self.cell(p,&#x27;&#x27;) == 1]
        if not accepting: return {&#x27;&lt;start&gt;&#x27;: []}, &#x27;&lt;start&gt;&#x27;
        for s in accepting: grammar[s] = [[&#x27;&lt;_&gt;&#x27;]]
        grammar[&#x27;&lt;_&gt;&#x27;] = [[]]

        # Step 4: Create the transition function
        for sid1 in states:
            first_such_row = states[sid1][0]
            for a in self.A:
                sid2 = self.state(first_such_row + a)
                grammar[sid1].append([a, sid2])

        return grammar, start_nt
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try the observation to grammar conversion for an observation table 
that corresponds to recognition of the string `a`. We will use the alphabet
`a`, `b`.

<!--
############
alphabet = list('ab')
o = ObservationTable(alphabet)
o._T = {'':    {'': 0, 'a': 1},
        'a':   {'': 1, 'a': 0},
        'b':   {'': 0, 'a': 0},
        'aa':  {'': 0, 'a': 0},
        'ab':  {'': 0, 'a': 0},
        'ba':  {'': 0, 'a': 0},
        'bb':  {'': 0, 'a': 0},
        'baa': {'': 0, 'a': 0},
        'bab': {'': 0, 'a': 0}}
P = [k for k in o._T]
S = [k for k in o._T['']]
o.P, o.S = P, S
g, s = o.table_to_grammar()
print('start: ', s)
for k in g:
    print(k)
    for r in g[k]:
        print(" | ", r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
alphabet = list(&#x27;ab&#x27;)
o = ObservationTable(alphabet)
o._T = {&#x27;&#x27;:    {&#x27;&#x27;: 0, &#x27;a&#x27;: 1},
        &#x27;a&#x27;:   {&#x27;&#x27;: 1, &#x27;a&#x27;: 0},
        &#x27;b&#x27;:   {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;aa&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;ab&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;ba&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;bb&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;baa&#x27;: {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;bab&#x27;: {&#x27;&#x27;: 0, &#x27;a&#x27;: 0}}
P = [k for k in o._T]
S = [k for k in o._T[&#x27;&#x27;]]
o.P, o.S = P, S
g, s = o.table_to_grammar()
print(&#x27;start: &#x27;, s)
for k in g:
    print(k)
    for r in g[k]:
        print(&quot; | &quot;, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Cleanup Grammar
This gets us a grammar that can accept the string `a`, but it also has a
problem. The issue is that the key `<00>` has no rule that does not include
`<00>` in its expansion. That is, `<00>` is an infinite loop that once the
machine goes in, is impossible to exit. We need to remove such rules. We do
that using the `compute_cost()` function of LimitFuzzer. The idea is that
if all rules of a nonterminal have `inf` as the cost, then that nonterminal
produces an infinite loop and hence both the nonterminal, as well as any rule
that references that nonterminal have to be removed recursively.

<!--
############
class ObservationTable(ObservationTable):
    def remove_infinite_loops(self, g, start):
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            if k == start: continue
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                if k in remove_keys: continue
                new_g[k] = []
                for r in g[k]:
                    if [t for t in r if t in remove_keys]: continue
                    new_g[k].append(r)
                if not new_g[k]:
                    if k == start: continue
                    remove_keys.append(k)
                    cont = True
        return new_g, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def remove_infinite_loops(self, g, start):
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            if k == start: continue
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                if k in remove_keys: continue
                new_g[k] = []
                for r in g[k]:
                    if [t for t in r if t in remove_keys]: continue
                    new_g[k].append(r)
                if not new_g[k]:
                    if k == start: continue
                    remove_keys.append(k)
                    cont = True
        return new_g, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can wrap up everything in one method.

<!--
############
class ObservationTable(ObservationTable):
    def grammar(self):
        g, s = self.table_to_grammar()
        return self.remove_infinite_loops(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def grammar(self):
        g, s = self.table_to_grammar()
        return self.remove_infinite_loops(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
once again

<!--
############
o = ObservationTable(alphabet)
o._T = {'':    {'': 0, 'a': 1},
        'a':   {'': 1, 'a': 0},
        'b':   {'': 0, 'a': 0},
        'aa':  {'': 0, 'a': 0},
        'ab':  {'': 0, 'a': 0},
        'ba':  {'': 0, 'a': 0},
        'bb':  {'': 0, 'a': 0},
        'baa': {'': 0, 'a': 0},
        'bab': {'': 0, 'a': 0}}
o.P, o.S = P, S
g, s = o.grammar()
print('start: ', s)
for k in g:
    print(k)
    for r in g[k]:
        print(" | ", r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
o = ObservationTable(alphabet)
o._T = {&#x27;&#x27;:    {&#x27;&#x27;: 0, &#x27;a&#x27;: 1},
        &#x27;a&#x27;:   {&#x27;&#x27;: 1, &#x27;a&#x27;: 0},
        &#x27;b&#x27;:   {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;aa&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;ab&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;ba&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;bb&#x27;:  {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;baa&#x27;: {&#x27;&#x27;: 0, &#x27;a&#x27;: 0},
        &#x27;bab&#x27;: {&#x27;&#x27;: 0, &#x27;a&#x27;: 0}}
o.P, o.S = P, S
g, s = o.grammar()
print(&#x27;start: &#x27;, s)
for k in g:
    print(k)
    for r in g[k]:
        print(&quot; | &quot;, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now that we are convinced that we can produce a DFA or a grammar out of the
table let us proceed to examining how to produce this table.
 
We start with the start state in the table, because we know for sure
that it exists, and is represented by the empty string in row and column,
which together (prefix + suffix) is the empty string `''` or $$ \epsilon $$.
We ask the program if it accepts the empty string, and if it accepts, we mark
the corresponding cell in the table as *accept* (or `1`).
 
For any given state in the DFA, we should be able to say what happens when
an input symbol is fed into the machine in that state. So, we can extend the
table with what happens when each input symbol is fed into the start state.
This means that we extend the table with rows corresponding to each symbol
in the input alphabet. 

So, we can initialize the table as follows. First, we check whether the
empty string is in the language. Then, we extend the table `T`
to `(P u P.A).S` using membership queries. This is given in `update_table()`

<!--
############
class ObservationTable(ObservationTable):
    def init_table(self, oracle):
        self._T[''] = {'': oracle.is_member('') }
        self.update_table(oracle)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def init_table(self, oracle):
        self._T[&#x27;&#x27;] = {&#x27;&#x27;: oracle.is_member(&#x27;&#x27;) }
        self.update_table(oracle)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The update table has two parts. First, it takes the current set of prefixes
(`rows`) and determines the auxiliary rows to compute based on extensions of
the current rows with the symbols in the alphabet (`auxrows`). This gives the
complete set of rows for the table. Then, for each suffix in `S`, ensure that
the table has a cell, and it is updated with the oracle result.

<!--
############
class ObservationTable(ObservationTable):
    def update_table(self, oracle):
        def unique(l): return list({s:None for s in l}.keys())
        rows = self.P
        auxrows = [p + a for p in self.P for a in self.A]
        PuPxA = unique(rows + auxrows)
        for p in PuPxA:
            if p not in self._T: self._T[p] = {}
            for s in self.S:
                if p in self._T and s in self._T[p]: continue
                self._T[p][s] = oracle.is_member(p + s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def update_table(self, oracle):
        def unique(l): return list({s:None for s in l}.keys())
        rows = self.P
        auxrows = [p + a for p in self.P for a in self.A]
        PuPxA = unique(rows + auxrows)
        for p in PuPxA:
            if p not in self._T: self._T[p] = {}
            for s in self.S:
                if p in self._T and s in self._T[p]: continue
                self._T[p][s] = oracle.is_member(p + s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using init_table and update_table

<!--
############
o = ObservationTable(alphabet)
def orcl(): pass
orcl.is_member = lambda x: 1
o.init_table(orcl)
for p in o._T: print(p, o._T[p])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
o = ObservationTable(alphabet)
def orcl(): pass
orcl.is_member = lambda x: 1
o.init_table(orcl)
for p in o._T: print(p, o._T[p])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Since we want to know what state we reached when we
fed the input symbol to the start state, we add a set of cleverly chosen
suffixes (columns) to the table, determine the machine response to these
suffixes (by feeding the machine prefix+suffix for each combination), and
check whether any new state other than the start state was identified. A
new state reached by a prefix can be distinguished from the start state using
some suffix, if, after consuming that particular prefix, followed by the
particular suffix, the machine moved to say *accept*, but when the machine
at the start state was fed the same suffix, the end state was not *accept*.
(i.e. the machine accepted prefix + suffix but not suffix on its own).
Symmetrically, if the machine did not accept the string prefix + suffix
but did accept the string suffix, that also distinguishes the state from
the start state. Once we have identified a new state, we can then extend
the DFA with transitions from this new state, and check whether more
states can be identified.
 
While doing this, there is one requirement we need to ensure. The result
of transition from every state for every alphabet needs to be defined.
The property that ensures this for the observation table is called
*closedness* or equivalently, the observation table is *closed* if the
table has the following property.
 
### Closed
The idea is that for every prefix we have, in set $$ P $$, we need to find
the state that is reached for every $$ a \in A $$. Then, we need to make sure
that the *state* represented by that prefix exists in $$ P $$. (If such a
state does not exist in P, then it means that we have found a new state).
 
Formally:
An observation table $$ P \times S $$ is closed if for each $$ t \in P·A $$
there exists a $$ p \in P $$ such that $$ [t] = [p] $$

<!--
############
class ObservationTable(ObservationTable):
    def closed(self):
        states_in_P = {self.state(p) for p in self.P}
        P_A = [p+a for p in self.P for a in self.A]
        for t in P_A:
            if self.state(t) not in states_in_P: return False, t
        return True, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def closed(self):
        states_in_P = {self.state(p) for p in self.P}
        P_A = [p+a for p in self.P for a in self.A]
        for t in P_A:
            if self.state(t) not in states_in_P: return False, t
        return True, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using closed.

<!--
############
def orcl(): pass
orcl.is_member = lambda x: 1 if x in ['a'] else 0

ot = ObservationTable(list('ab'))
ot.init_table(orcl)
for p in ot._T: print(p, ot._T[p])

res, counter = ot.closed()
assert not res
print(counter)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def orcl(): pass
orcl.is_member = lambda x: 1 if x in [&#x27;a&#x27;] else 0

ot = ObservationTable(list(&#x27;ab&#x27;))
ot.init_table(orcl)
for p in ot._T: print(p, ot._T[p])

res, counter = ot.closed()
assert not res
print(counter)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Add prefix

<!--
############
class ObservationTable(ObservationTable):
    def add_prefix(self, p, oracle):
        if p in self.P: return
        self.P.append(p)
        self.update_table(oracle)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def add_prefix(self, p, oracle):
        if p in self.P: return
        self.P.append(p)
        self.update_table(oracle)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using add_prefix

<!--
############
def orcl(): pass
orcl.is_member = lambda x: 1 if x in ['a'] else 0

ot = ObservationTable(list('ab'))
ot.init_table(orcl)
res, counter = ot.closed()
assert not res

ot.add_prefix('a', orcl)
for p in ot._T: print(p, ot._T[p])
res, counter = ot.closed()
assert res

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def orcl(): pass
orcl.is_member = lambda x: 1 if x in [&#x27;a&#x27;] else 0

ot = ObservationTable(list(&#x27;ab&#x27;))
ot.init_table(orcl)
res, counter = ot.closed()
assert not res

ot.add_prefix(&#x27;a&#x27;, orcl)
for p in ot._T: print(p, ot._T[p])
res, counter = ot.closed()
assert res
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is essentially the intuition behind most
of the grammar inference algorithms, and the cleverness lies in how the
suffixes are chosen. In the case of L\*, when we find that one of the
transitions from the current states result in a new state, we add the
alphabet that caused the transition from the current state and the suffix
that distinguished the new state to the suffixes (i.e, a + suffix is
added to the columns).

This particular aspect is governed by the *consistence* property of the
observation table.

### Consistent

An observation table $$ P \times S $$ is consistent if, whenever $$ p1 $$
and $$ p2 $$
are elements of P such that $$ [p1] = [p2] $$, for each $$ a \in A $$,
$$ [p1.a] = [p2.a] $$.
*If* there are two rows in the top part of the table repeated, then the
corresponding suffix results should be the same.
If not, we have found a counter example. So we report the alphabet and
the suffix that distinguished the rows. We will then add the new
string (a + suffix) as a new suffix to the table.

<!--
############
class ObservationTable(ObservationTable):
    def consistent(self):
        matchingpairs = [(p1, p2) for p1 in self.P for p2 in self.P
                         if p1 != p2 and self.state(p1) == self.state(p2)]
        suffixext = [(a, s) for a in self.A for s in self.S]
        for p1,p2 in matchingpairs:
            for a, s in suffixext:
                if self.cell(p1+a,s) != self.cell(p2+a,s):
                        return False, (p1, p2), (a + s)
        return True, None, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def consistent(self):
        matchingpairs = [(p1, p2) for p1 in self.P for p2 in self.P
                         if p1 != p2 and self.state(p1) == self.state(p2)]
        suffixext = [(a, s) for a in self.A for s in self.S]
        for p1,p2 in matchingpairs:
            for a, s in suffixext:
                if self.cell(p1+a,s) != self.cell(p2+a,s):
                        return False, (p1, p2), (a + s)
        return True, None, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Add suffix

<!--
############
class ObservationTable(ObservationTable):
    def add_suffix(self, a_s, oracle):
        if a_s in self.S: return
        self.S.append(a_s)
        self.update_table(oracle)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def add_suffix(self, a_s, oracle):
        if a_s in self.S: return
        self.S.append(a_s)
        self.update_table(oracle)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using add_suffix

<!--
############
def orcl(): pass
orcl.is_member = lambda x: 1 if x in ['a'] else 0

ot = ObservationTable(list('ab'))
ot.init_table(orcl)
is_closed, counter = ot.closed()
assert not is_closed
ot.add_prefix('a', orcl)
ot.add_prefix('b', orcl)
ot.add_prefix('ba', orcl)
for p in ot._T: print(p, ot._T[p])

is_closed, unknown_P = ot.closed()
print(is_closed)

is_consistent,_, unknown_A = ot.consistent()
assert not is_consistent

ot.add_suffix('a', orcl)
for p in ot._T: print(p, ot._T[p])

is_consistent,_, unknown_A = ot.consistent()
assert is_consistent

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def orcl(): pass
orcl.is_member = lambda x: 1 if x in [&#x27;a&#x27;] else 0

ot = ObservationTable(list(&#x27;ab&#x27;))
ot.init_table(orcl)
is_closed, counter = ot.closed()
assert not is_closed
ot.add_prefix(&#x27;a&#x27;, orcl)
ot.add_prefix(&#x27;b&#x27;, orcl)
ot.add_prefix(&#x27;ba&#x27;, orcl)
for p in ot._T: print(p, ot._T[p])

is_closed, unknown_P = ot.closed()
print(is_closed)

is_consistent,_, unknown_A = ot.consistent()
assert not is_consistent

ot.add_suffix(&#x27;a&#x27;, orcl)
for p in ot._T: print(p, ot._T[p])

is_consistent,_, unknown_A = ot.consistent()
assert is_consistent
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
(Of course readers will quickly note that the table is not the best data
structure here, and just because a suffix distinguished two particular
states does not mean that it is a good idea to evaluate the same suffix
on all other states. These are ideas that will be explored in later
algorithms).


Finally, L\* also relies on a *Teacher* for it to suggest new suffixes that
can distinguish unrecognized states from current ones.

## Teacher
We now construct our teacher. We have two requirements for the teacher.
The first is that it should fulfil the requirement for Oracle. That is,
it should answer `is_member()` queries. Secondly, it should also answer
`is_equivalent()` queries.
First, we define the oracle interface.

<!--
############
class Oracle:
    def is_member(self, q): pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Oracle:
    def is_member(self, q): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As I promised, we will be using the PAC framework rather than the equivalence
oracles. 

We define a simple teacher based on regular expressions. That is, if you
give it a regular expression, will convert it to an acceptor based on a
[parser](/post/2021/02/06/earley-parsing/) and a generator based on a
[random sampler](/post/2021/07/27/random-sampling-from-context-free-grammar/),
and will then use it for verification of hypothesis grammars.
### PAC Learning
PAC learning was introduced by Valiant in 1984 [^valiant1984] as a way to
think about inferred models in computational linguistics and machine learning.
The basic idea is that given a blackbox model, we need to be able to produce
samples that can then be tested against the model to construct an inferred
model (i.e, to train the model). For sampling during training, we have to
assume some sampling procedure, and hence a distribution for training.
Per PAC learning, we can only guarantee the performance of the
learned model when tested using samples from the same distribution. Given
that we are sampling from a distribution, there is a possibility that due
to non-determinism, the data is not as spread out as we may like, and hence
the training data is not optimal by a certain probability. This reflects on
the quality of the model learned. This is indicated by the concept of
confidence intervals, and indicated by the $$ \delta $$ parameter. That is,
$$ 1 - \delta $$ quantifies the confidence we have in our model. Next,
given any training data, due to the fact that the training data is finite,
our grammar learned is an approximation of the real grammar, and there will
always be an error term. This error is quantified by the $$ \epsilon $$
parameter. Given the desired $$ \delta $$ and $$ \epsilon $$ Angluin provides
a formula to compute the number of calls to make to the membership oracle
at the $$ i^{th} $$ equivalence query.

$$ n=\lceil\frac{1}{\epsilon}\times log(\frac{1}{\delta}+i\times log(2))\rceil $$
 
In essence the PAC framework says that there is $$ 1 - \delta  $$ probability
that the model learned will be approximately correct. That is, it will
classify samples with an error rate less than $$ \epsilon $$.

<!--
############
class Teacher(Oracle):
    def is_equivalent(self, grammar, start): assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Oracle):
    def is_equivalent(self, grammar, start): assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We input the PAC parameters delta for confidence and epsilon for accuracy

<!--
############
class Teacher(Teacher):
    def __init__(self, rex, delta=0.1, epsilon=0.1):
        self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)
        self.parser = earleyparser.EarleyParser(self.g)
        self.sampler = cfgrandomsample.RandomSampleCFG(self.g)
        self.equivalence_query_counter = 0
        self.delta, self.epsilon = delta, epsilon

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def __init__(self, rex, delta=0.1, epsilon=0.1):
        self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)
        self.parser = earleyparser.EarleyParser(self.g)
        self.sampler = cfgrandomsample.RandomSampleCFG(self.g)
        self.equivalence_query_counter = 0
        self.delta, self.epsilon = delta, epsilon
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can define the membership query `is_member()` as follows:

<!--
############
class Teacher(Teacher):
    def is_member(self, q):
        try: list(self.parser.recognize_on(q, self.s))
        except: return 0
        return 1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def is_member(self, q):
        try: list(self.parser.recognize_on(q, self.s))
        except: return 0
        return 1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given a grammar, check whether it is equivalent to the given grammar.
The PAC guarantee is that we only need `num_calls` for the `i`th equivalence
query. For equivalence check here, we check for strings of length 1, then
length 2 etc, whose sum should be `num_calls`. We take the easy way out here,
and just use `num_calls` as the number of calls for each string length.
We have what is called a *cooperative teacher*, that tries to respond with
a shortest possible counter example. We # also take the easy way out and only
check for a maximum length of 10.
(I will revisit this if there is interest on expanding this).

<!--
############
class Teacher(Teacher):
    def is_equivalent(self, grammar, start, max_length_limit=10):
        self.equivalence_query_counter += 1
        num_calls = math.ceil(1.0/self.epsilon *
                  (math.log(1.0/self.delta +
                              self.equivalence_query_counter * math.log(2))))

        for limit in range(1, max_length_limit):
            is_eq, counterex, c = self.is_equivalent_for(self.g, self.s,
                                                    grammar, start,
                                                    limit, num_calls)
            if counterex is None: # no members of length limit
                continue
            if not is_eq:
                c = [a for a in counterex if a is not None][0]
                return False, c
        return True, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def is_equivalent(self, grammar, start, max_length_limit=10):
        self.equivalence_query_counter += 1
        num_calls = math.ceil(1.0/self.epsilon *
                  (math.log(1.0/self.delta +
                              self.equivalence_query_counter * math.log(2))))

        for limit in range(1, max_length_limit):
            is_eq, counterex, c = self.is_equivalent_for(self.g, self.s,
                                                    grammar, start,
                                                    limit, num_calls)
            if counterex is None: # no members of length limit
                continue
            if not is_eq:
                c = [a for a in counterex if a is not None][0]
                return False, c
        return True, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Due to the limitations of our utilities for random
sampling, we need to remove epsilon tokens from places other than
the start rule.

<!--
############
class Teacher(Teacher):
    def fix_epsilon(self, grammar_, start):
        # clone
        grammar = {k:[[t for t in r] for r in grammar_[k]] for k in grammar_}
        gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
        gs.remove_epsilon_rules()
        return gs.grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def fix_epsilon(self, grammar_, start):
        # clone
        grammar = {k:[[t for t in r] for r in grammar_[k]] for k in grammar_}
        gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
        gs.remove_epsilon_rules()
        return gs.grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we have a helper for producing the random sampler, and the
parser for easy comparison.

<!--
############
class Teacher(Teacher):
    def digest_grammar(self, g, s, l, n):
        if not g[s]: return 0, None, None
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return cnt, key_node, ep

    def gen_random(self, key_node, cnt):
        if cnt == 0: return None
        at = random.randint(0, cnt-1)
        # sampler does not store state.
        st_ = self.sampler.key_get_string_at(key_node, at)
        return fuzzer.tree_to_string(st_)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def digest_grammar(self, g, s, l, n):
        if not g[s]: return 0, None, None
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return cnt, key_node, ep

    def gen_random(self, key_node, cnt):
        if cnt == 0: return None
        at = random.randint(0, cnt-1)
        # sampler does not store state.
        st_ = self.sampler.key_get_string_at(key_node, at)
        return fuzzer.tree_to_string(st_)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Check Grammar Equivalence
Checking if two grammars are equivalent to a length of string for n count.

<!--
############
class Teacher(Teacher):
    def is_equivalent_for(self, g1, s1, g2, s2, l, n):
        cnt1, key_node1, ep1 = self.digest_grammar(g1, s1, l, n)
        cnt2, key_node2, ep2 = self.digest_grammar(g2, s2, l, n)
        count = 0

        str1 = {self.gen_random(key_node1, cnt1) for _ in range(n)}
        str2 = {self.gen_random(key_node2, cnt2) for _ in range(n)}

        for st1 in str1:
            if st1 is None: continue
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
            if st2 is None: continue
            count += 1
            try: list(ep1.recognize_on(st2, s1))
            except: return False, (None, st2), count

        return True, None, count

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def is_equivalent_for(self, g1, s1, g2, s2, l, n):
        cnt1, key_node1, ep1 = self.digest_grammar(g1, s1, l, n)
        cnt2, key_node2, ep2 = self.digest_grammar(g2, s2, l, n)
        count = 0

        str1 = {self.gen_random(key_node1, cnt1) for _ in range(n)}
        str2 = {self.gen_random(key_node2, cnt2) for _ in range(n)}

        for st1 in str1:
            if st1 is None: continue
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
            if st2 is None: continue
            count += 1
            try: list(ep1.recognize_on(st2, s1))
            except: return False, (None, st2), count

        return True, None, count
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this out.

<!--
############
g1 = { # should end with one.
        '<0>': [
            ['1', '<1>'],
            ['0', '<0>']
            ],
        '<1>':[
            ['1', '<1>'],
            []
            ]
}
g2 = { # should end with one.
        '<0>': [
            ['1', '<1>'],
            ['0', '<1>']
            ],
        '<1>':[
            ['1', '<1>'],
            []
            ]
}
t = Teacher('a')
v = t.is_equivalent_for(g1, '<0>', g2, '<0>', 2, 10)
print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = { # should end with one.
        &#x27;&lt;0&gt;&#x27;: [
            [&#x27;1&#x27;, &#x27;&lt;1&gt;&#x27;],
            [&#x27;0&#x27;, &#x27;&lt;0&gt;&#x27;]
            ],
        &#x27;&lt;1&gt;&#x27;:[
            [&#x27;1&#x27;, &#x27;&lt;1&gt;&#x27;],
            []
            ]
}
g2 = { # should end with one.
        &#x27;&lt;0&gt;&#x27;: [
            [&#x27;1&#x27;, &#x27;&lt;1&gt;&#x27;],
            [&#x27;0&#x27;, &#x27;&lt;1&gt;&#x27;]
            ],
        &#x27;&lt;1&gt;&#x27;:[
            [&#x27;1&#x27;, &#x27;&lt;1&gt;&#x27;],
            []
            ]
}
t = Teacher(&#x27;a&#x27;)
v = t.is_equivalent_for(g1, &#x27;&lt;0&gt;&#x27;, g2, &#x27;&lt;0&gt;&#x27;, 2, 10)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 
## L star main loop
Given the observation table and the teacher, the algorithm itself is simple.
The L* algorithm loops, doing the following operations in sequence. (1) keep
the table closed, (2) keep the table consistent, and if it is closed and
consistent (3) ask the teacher if the corresponding hypothesis grammar is
correct.

<!--
############
def l_star(T, teacher):
    T.init_table(teacher)

    while True:
        while True:
            is_closed, unknown_P = T.closed()
            is_consistent, _, unknown_AS = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.add_prefix(unknown_P, teacher)
            if not is_consistent: T.add_suffix(unknown_AS, teacher)

        grammar, start = T.grammar()
        eq, counterX = teacher.is_equivalent(grammar, start)
        if eq: return grammar, start
        for i,_ in enumerate(counterX): T.add_prefix(counterX[0:i+1], teacher)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def l_star(T, teacher):
    T.init_table(teacher)

    while True:
        while True:
            is_closed, unknown_P = T.closed()
            is_consistent, _, unknown_AS = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.add_prefix(unknown_P, teacher)
            if not is_consistent: T.add_suffix(unknown_AS, teacher)

        grammar, start = T.grammar()
        eq, counterX = teacher.is_equivalent(grammar, start)
        if eq: return grammar, start
        for i,_ in enumerate(counterX): T.add_prefix(counterX[0:i+1], teacher)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
import string
e = '(ab|cd|ef)*'
teacher = Teacher(e)
tbl = ObservationTable(list(string.ascii_letters))
g, s = l_star(tbl, teacher)
print(s, g)

gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    res = gf.iter_fuzz(key=s, max_depth=100)
    print(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
e = &#x27;(ab|cd|ef)*&#x27;
teacher = Teacher(e)
tbl = ObservationTable(list(string.ascii_letters))
g, s = l_star(tbl, teacher)
print(s, g)

gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    res = gf.iter_fuzz(key=s, max_depth=100)
    print(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
we define a match function for converting syntax error to boolean

<!--
############
def match(p, start, text):
    try: p.recognize_on(text, start)
    except SyntaxError as e: return False
    return True

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(p, start, text):
    try: p.recognize_on(text, start)
    except SyntaxError as e: return False
    return True
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Evaluating the model accuracy.
In the PAC model, we infer a grammar with parameters $$ \epsilon $$ and $$ \delta $$.
Here, from a software engineering perspective, the interpretation is that if
we use the same input distribution for inference as the sampling distribution,
then we can expect an accuracy of $$ 1 - \epsilon $$ in classification. That
is, we can expect $$ n \times \epsilon $$ misclassified strings out of $$ n $$
strings, and we have a confidence level of $$ 1 - \delta $$ in this statement.
## The F1 score.

There is of course an additional question here. From the perspective of
language learning for software engineering, the error rate is too coarse.
We need more detail as to the rate of false positives and false negatives.
This is because most of our languages are very sparse compared to the universe
of all strings, and it is easy to get a very small error rate when almost any
input generated randomly is unlikely to be in the language.
That is, the precision and recall of the model that
we learned is important. I have discussed how to compute the precision and
recall, and the F1 score [previously](/post/2021/01/28/grammar-inference/).
So, we can compute the precision and recall as follows.


<!--
############
import re
exprs = ['a', 'ab', 'a*b*', 'a*b', 'ab*', 'a|b', '(ab|cd|ef)*']
for e in exprs:
    teacher = Teacher(e)
    t_g, t_s = teacher.g, teacher.s
    t_p, t_f = teacher.parser, fuzzer.LimitFuzzer(t_g)

    tbl = ObservationTable(list(string.ascii_letters))
    i_g, i_s = l_star(tbl, teacher)
    i_p = earleyparser.EarleyParser(i_g)
    i_f = fuzzer.LimitFuzzer(i_g)

    lgi = 0
    lgi_lgb = 0

    lgb = 0
    lgb_lgi = 0

    for i in range(100):
        val = i_f.iter_fuzz(key=i_s, max_depth=100)
        v = match(t_p, t_s, val)
        lgi += 1
        if v: lgi_lgb += 1

        val = t_f.iter_fuzz(key=t_s, max_depth=100)
        v = match(i_p, i_s, val)
        lgb += 1
        if v: lgb_lgi += 1
    print('expr:', e)
    precision = lgi_lgb / lgi
    print('precision: ', precision)
    recall = lgb_lgi / lgb
    print('recall: ', recall)
    print('F1:', 2 * precision*recall/(precision + recall))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import re
exprs = [&#x27;a&#x27;, &#x27;ab&#x27;, &#x27;a*b*&#x27;, &#x27;a*b&#x27;, &#x27;ab*&#x27;, &#x27;a|b&#x27;, &#x27;(ab|cd|ef)*&#x27;]
for e in exprs:
    teacher = Teacher(e)
    t_g, t_s = teacher.g, teacher.s
    t_p, t_f = teacher.parser, fuzzer.LimitFuzzer(t_g)

    tbl = ObservationTable(list(string.ascii_letters))
    i_g, i_s = l_star(tbl, teacher)
    i_p = earleyparser.EarleyParser(i_g)
    i_f = fuzzer.LimitFuzzer(i_g)

    lgi = 0
    lgi_lgb = 0

    lgb = 0
    lgb_lgi = 0

    for i in range(100):
        val = i_f.iter_fuzz(key=i_s, max_depth=100)
        v = match(t_p, t_s, val)
        lgi += 1
        if v: lgi_lgb += 1

        val = t_f.iter_fuzz(key=t_s, max_depth=100)
        v = match(i_p, i_s, val)
        lgb += 1
        if v: lgb_lgi += 1
    print(&#x27;expr:&#x27;, e)
    precision = lgi_lgb / lgi
    print(&#x27;precision: &#x27;, precision)
    recall = lgb_lgi / lgb
    print(&#x27;recall: &#x27;, recall)
    print(&#x27;F1:&#x27;, 2 * precision*recall/(precision + recall))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 
# Notes

While there is no strict specifications as to what grammar induction,
inference, identification, and learning is, according to [Higuera](http://videolectures.net/mlcs07_higuera_giv/),
Grammar inference is about learning **the** grammar (i.e. the representation)
when given information about a language, and focuses on the target, the
grammar. That is, you start with the assumption that a target grammar exists.
Then, try to guess that grammar based on your observations.
If on the other hand, you do not believe that a particular target grammar
exists, but want to do the best to learn the underlying principles, or find
*a* grammar that explain the data, then it is grammar induction.
(This is also mentioned in the preface of the book "Grammatical Inference"
by Higuera)
That is, it focuses on the best possible grammar for the
given data. Closely related fields are grammar mining, grammar recovery,
and grammar extraction which are all whitebox approaches based on program
or related artifact analysis. Language acquisition is another related term.
Another is Model Learning [^vaandrager2017model].

## Context Free Languages
Here, we discussed how to infer a regular grammar. In many cases the blackbox
may accept a language that is beyond regular, for example, it could be
context-free. The nice thing about L\* is that it can provide us a close
approximation of such context-free language in terms of a regular grammar.
One can then take the regular grammar thus produced, and try and identify
context-free structure in that DFA based on recognition of repeating
structures. It is still an open question on how to recover the context-free
structure from such a DFA.

[^angluin1987]: Learning Regular Sets from Queries and Counterexamples, 1987 
[^angluin1988]: Queries and Concept Learning, 1988
[^valiant1984]: A theory of the learnable, 1984
[^vaandrager2017model]: Model learning, Frits Vaandrager, 2017

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-01-04-lstar-learning-regular-languages.py).


