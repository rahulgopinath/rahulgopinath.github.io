---
published: true
title: Learning Regular Languages with L* Algorithm
layout: post
comments: true
tags: regular-grammars induction
categories: post
---

TLDR; This tutorial is a complete implementation of Angluin's L-star algorithm
with PAC learning in Python (i.e. without using equivalence queries).
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


#### Prerequisites
 
As before, we start with the prerequisite imports.

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
Let us start with the assumption that the blackbox program
accepts a [regular language](https://en.wikipedia.org/wiki/Regular_language).
By *accept* I mean that the program does some processing with input given
rather than error out. For example, if the blackbox actually contained a JSON
parser, it will *accept* a string in the JSON format, and *reject* strings
that are not in the JSON format.
 
So, given such a program, and you are not allowed to peek inside the program
source code, how do you find what the program accepts? Knowing that the
program accepts a regular language, we can start by constructing a
[DFA](https://en.wikipedia.org/wiki/Deterministic_finite_automaton) (A finite
state machine).
 
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
as rows, and suffix strings as columns. The table content simply marks
whether program accepted the prefix + suffix string or not.

Next, we start with the start state in the table, because we know for sure
that it exists, and is represented by the empty string in row and column,
which together (prefix + suffix = '' + '') is the empty string. We ask the
program if it accepts the empty string, and if it accepts, we mark the
corresponding cell in the table as accept (or `1`).

For any given state in the DFA, we should be able to say what happens when
an input symbol is fed into the machine in that state. So, we can extend the
table with what happens when each input symbol is fed into the start state.
This means that we extend the table with rows corresponding to each symbol
in the input alphabet. Since we want to know what state we reached when we
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
states can be identified. This is essentially the intuition behind most
of the grammar inference algorithms, and the cleverness lies in how the
suffixes are chosen. In the case of L\*, the when we find that one of the
transitions from the current states result in a new state, we add the
alphabet that caused the transition from the current state and the suffix
that distinguished the new state to the suffixes (i.e, a + suffix is
added to the columns). Furthermore, L\* also relies on something called
a *Teacher* for it to suggest new suffixes that can distinguish
unrecognized states from current ones.

(Of course readers will quickly note that the table is not the best data
structure here, and just because a suffix distinguished two particular
states does not mean that it is a good idea to evaluate the same suffix
on all other states. These are ideas that will be explored in later
algorithms).
 
# The classical L* algorithm
 
In the classical algorithm from Angluin [^angluin1987], beyond the yes/no
oracle (the program can tell you whether any given string is acceptable or
not, traditionally called the *membership query*), we also require what is
called an *equivalence query*. That is, the algorithm requires what is called
a *Teacher* that is able to accept a guess of the target language in terms of
a grammar, and tell us whether we guessed it right, or if not, provide us with
a string that has different behavior on the blackbox and the guessed grammar
-- a counter example. The idea is to use the counter example to refine the
guess until the guess matches the target grammar. To start with, we require
the following definitions.
 
## Definitions

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

Given the observation table, the algorithm itself is simple

## L star main loop
The L* algorithm loops, doing the following operations in sequence. (1) keep
the table closed, (2) keep the table consistent, and if it is closed and
consistent (3) ask the teacher if the corresponding hypothesis grammar is
correct.

<!--
############
def l_star(T):
    T.init_table()

    while True:
        while True:
            is_closed, unknown_P = T.closed()
            is_consistent, _, unknown_AS = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.append_P(unknown_P)
            if not is_consistent: T.append_S(unknown_AS)

        grammar, start = T.grammar()
        eq, counterX = teacher.is_equivalent(grammar, start)
        if eq: return grammar, start
        for i,_ in enumerate(counterX): T.append_P(counterX[0:i+1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def l_star(T):
    T.init_table()

    while True:
        while True:
            is_closed, unknown_P = T.closed()
            is_consistent, _, unknown_AS = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.append_P(unknown_P)
            if not is_consistent: T.append_S(unknown_AS)

        grammar, start = T.grammar()
        eq, counterX = teacher.is_equivalent(grammar, start)
        if eq: return grammar, start
        for i,_ in enumerate(counterX): T.append_P(counterX[0:i+1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## ObservationTable

Next, we define the state table, also called the observation table.
We initialize the class with an teacher, and the alphabet.
That is, we initialize the set of prefixes `P` to be { $$\epsilon $$ }
and the set of suffixes (experiments) `S` also to be { $$\epsilon $$ }

<!--
############
class ObservationTable:
    def __init__(self, alphabet, teacher):
        self._T, self.P, self.S = {}, [''], ['']
        self.teacher = teacher
        self.A = alphabet

    def row(self, v): return self._T[v]

    def cell(self, v, e): return self._T[v][e]

    def get_sid(self, s):
        return '<%s>' % ''.join([str(self.cell(s,e)) for e in self.S])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable:
    def __init__(self, alphabet, teacher):
        self._T, self.P, self.S = {}, [&#x27;&#x27;], [&#x27;&#x27;]
        self.teacher = teacher
        self.A = alphabet

    def row(self, v): return self._T[v]

    def cell(self, v, e): return self._T[v][e]

    def get_sid(self, s):
        return &#x27;&lt;%s&gt;&#x27; % &#x27;&#x27;.join([str(self.cell(s,e)) for e in self.S])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can initialize the table as follows. First, we check whether the
empty string is in the language. Then, we extend the table `T`
to `(P u P.A).S` using membership queries.

- For each p in P and each a in A, query the teacher for the output of `p.a`
and update table `T` with the rows.
- For each `s` in `S`, query the teacher for the output of `p.s` and update `T`

<!--
############
class ObservationTable(ObservationTable):
    def init_table(self):
        self._T[''] = {'': self.teacher.is_member('') }
        self.update_table()

    def update_table(self):
        def unique(l): return list({s:None for s in l}.keys())
        rows = self.P
        auxrows = [p + a for p in self.P for a in self.A]
        PuPxA = unique(rows + auxrows)
        PuPxA_E = [(s,e) for s in PuPxA for e in self.S]
        for s,e in PuPxA_E:
            if s in self._T and e in self._T[s]: continue
            if s not in self._T: self._T[s] = {}
            self._T[s][e] = self.teacher.is_member(s + e)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def init_table(self):
        self._T[&#x27;&#x27;] = {&#x27;&#x27;: self.teacher.is_member(&#x27;&#x27;) }
        self.update_table()

    def update_table(self):
        def unique(l): return list({s:None for s in l}.keys())
        rows = self.P
        auxrows = [p + a for p in self.P for a in self.A]
        PuPxA = unique(rows + auxrows)
        PuPxA_E = [(s,e) for s in PuPxA for e in self.S]
        for s,e in PuPxA_E:
            if s in self._T and e in self._T[s]: continue
            if s not in self._T: self._T[s] = {}
            self._T[s][e] = self.teacher.is_member(s + e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Closed

A state table $$ P \times S $$ is closed if for each $$ t \in P·A $$
there exists a $$ p \in P $$ such that $$ [t] = [p] $$

<!--
############
class ObservationTable(ObservationTable):
    def closed(self):
        P_A = [p+a for p in self.P for a in self.A]
        for t in P_A:
            res = [p for p in self.P if self.row(t) == self.row(p)]
            if not res: return False, t
        return True, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def closed(self):
        P_A = [p+a for p in self.P for a in self.A]
        for t in P_A:
            res = [p for p in self.P if self.row(t) == self.row(p)]
            if not res: return False, t
        return True, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Consistent

A state table $$ P \times S $$ is consistent if, whenever p1 and p2
are elements of P such that $$ [p1] = [p2] $$, for each $$ a \in A $$,
$$ [p1.a] = [p2.a] $$.
*If* there are two rows in the top part of the table repeated, then the
corresponding extensions should be the same.
If not, we found a counter example, and we report the alphabet + the
suffix that distinguished. We will then add the new string (a + suffix)
as a new suffix to the table.

<!--
############
class ObservationTable(ObservationTable):
    def consistent(self):
        prefixpairs = [(p1,p2) for p1 in self.P for p2 in self.P if p1 != p2]
        for p1,p2 in prefixpairs:
            if self.row(p1) != self.row(p2): continue
            for a in self.A:
                for s in self.S:
                    if self.cell(p1+a,s) != self.cell(p2+a,s):
                        return False, (p1, p2), (a + s)
        return True, None, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def consistent(self):
        prefixpairs = [(p1,p2) for p1 in self.P for p2 in self.P if p1 != p2]
        for p1,p2 in prefixpairs:
            if self.row(p1) != self.row(p2): continue
            for a in self.A:
                for s in self.S:
                    if self.cell(p1+a,s) != self.cell(p2+a,s):
                        return False, (p1, p2), (a + s)
        return True, None, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Table utilities
Next, we define two utilities, one for appending a new S, and another
for appending a new E. We also define a utility for naming a state,
which corresponds to a unique row contents.

<!--
############
class ObservationTable(ObservationTable):
    def append_P(self, p):
        if p in self.P: return
        self.P.append(p)
        self.update_table()

    def append_S(self, a_s):
        if a_s in self.S: return
        self.S.append(a_s)
        self.update_table()


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def append_P(self, p):
        if p in self.P: return
        self.P.append(p)
        self.update_table()

    def append_S(self, a_s):
        if a_s in self.S: return
        self.S.append(a_s)
        self.update_table()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Convert Table to Grammar
Given the observation table, we can recover the grammar from this table
(corresponding to the DFA). The
unique cell contents of rows are states. In many cases, multiple rows may
correspond to the same state (as the cell contents are the same).
The *start state* is given by the state that correspond to the epsilon row.
A state is accepting if it on query of epsilon, it returns 1.
 
* $$ Q = {row(p) : p \in P} $$             -- states
* $$ q0 = [\epsilon] $$                    -- start
* $$ \delta([s], a) = [s.a] $$             -- Transition function
* $$ F = {[p] : p \in P, \delta([p],\epsilon) = 1} $$      -- accepting state

<!--
############
class ObservationTable(ObservationTable):
    def table_to_grammar(self):
        prefix_to_state = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for p in self.P:
            stateid = self.get_sid(p)
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
                sid2 = self.get_sid(first_such_row + a)
                grammar[sid1].append([a, sid2])

        return grammar, start_nt

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def table_to_grammar(self):
        prefix_to_state = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for p in self.P:
            stateid = self.get_sid(p)
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
                sid2 = self.get_sid(first_such_row + a)
                grammar[sid1].append([a, sid2])

        return grammar, start_nt
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Cleanup Grammar
The grammar output by the `grammar()` method is a bit messy. It can contain
keys will always lead to infinite loops. For example,

```
<A> ::= <B> <A>
     |  <C> <A>
```
We need to remove such infinite loops.

<!--
############
class ObservationTable(ObservationTable):
    def remove_infinite_loops(self, g, s):
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            if k == s: continue
            # if all rules in a k cost inf, then it should be removed.
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        new_g = {}
        for k in g:
            if k in remove_keys: continue
            new_g[k] = []
            for r in g[k]:
                if [t for t in r if t in remove_keys]: continue
                new_g[k].append(r)
        return new_g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def remove_infinite_loops(self, g, s):
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            if k == s: continue
            # if all rules in a k cost inf, then it should be removed.
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        new_g = {}
        for k in g:
            if k in remove_keys: continue
            new_g[k] = []
            for r in g[k]:
                if [t for t in r if t in remove_keys]: continue
                new_g[k].append(r)
        return new_g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Infer Grammar
We can now wrap up everything in one method.

<!--
############
class ObservationTable(ObservationTable):
    def grammar(self):
        g, s = self.table_to_grammar()
        g, s = self.remove_infinite_loops(g, s)
        return g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ObservationTable(ObservationTable):
    def grammar(self):
        g, s = self.table_to_grammar()
        g, s = self.remove_infinite_loops(g, s)
        return g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Teacher

Next, we need to construct our teacher. 
As I promised, we will be using the PAC framework rather than the equivalence
oracles. First, due to the limitations of our utilities for random
sampling, we need to remove epsilon tokens from places other than
the start rule.

<!--
############
class Teacher:
    def fix_epsilon(self, grammar, start):
        gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
        gs.remove_epsilon_rules()
        return gs.grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher:
    def fix_epsilon(self, grammar, start):
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
    def prepare_grammar(self, g, s, l, n):
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return rgf, key_node, cnt, ep

    def generate_a_random_string(self, rgf, key_node, cnt):
        at = random.randint(0, cnt-1)
        st_ = rgf.key_get_string_at(key_node, at)
        return fuzzer.tree_to_string(st_)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def prepare_grammar(self, g, s, l, n):
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return rgf, key_node, cnt, ep

    def generate_a_random_string(self, rgf, key_node, cnt):
        at = random.randint(0, cnt-1)
        st_ = rgf.key_get_string_at(key_node, at)
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
        rgf1, key_node1, cnt1, ep1 = self.prepare_grammar(g1, s1, l, n)
        rgf2, key_node2, cnt2, ep2 = self.prepare_grammar(g2, s2, l, n)
        count = 0

        if cnt1 == 0 and cnt2 == 0: return True, (None, None), count


        if cnt1 == 0:
            st2 = self.generate_a_random_string(rgf2, key_node2, cnt2)
            return False, (None, st2), count

        if cnt2 == 0:
            st1 = self.generate_a_random_string(rgf1, key_node1, cnt1)
            return False, (st1, None), count

        str1 = set()
        str2 = set()

        for i in range(n):
            str1.add(self.generate_a_random_string(rgf1, key_node1, cnt1))
            str2.add(self.generate_a_random_string(rgf2, key_node2, cnt2))

        for st1 in str1:
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
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
        rgf1, key_node1, cnt1, ep1 = self.prepare_grammar(g1, s1, l, n)
        rgf2, key_node2, cnt2, ep2 = self.prepare_grammar(g2, s2, l, n)
        count = 0

        if cnt1 == 0 and cnt2 == 0: return True, (None, None), count


        if cnt1 == 0:
            st2 = self.generate_a_random_string(rgf2, key_node2, cnt2)
            return False, (None, st2), count

        if cnt2 == 0:
            st1 = self.generate_a_random_string(rgf1, key_node1, cnt1)
            return False, (st1, None), count

        str1 = set()
        str2 = set()

        for i in range(n):
            str1.add(self.generate_a_random_string(rgf1, key_node1, cnt1))
            str2.add(self.generate_a_random_string(rgf2, key_node2, cnt2))

        for st1 in str1:
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
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
t = Teacher()
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
t = Teacher()
v = t.is_equivalent_for(g1, &#x27;&lt;0&gt;&#x27;, g2, &#x27;&lt;0&gt;&#x27;, 2, 10)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a simple oracle based on regular expressions.

<!--
############
class Teacher(Teacher):
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == ('^', '$'):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)

        g, s = self.fix_epsilon(self.g, self.s)

        self.ep = earleyparser.EarleyParser(g)
        self.rgf = cfgrandomsample.RandomSampleCFG(g)
        self.counter = 0
        # epsilon is the accuracy and delta is the confidence
        self.delta, self.epsilon = 0.1, 0.1

    def generate(self, l):
        cache = {}
        while not cache:
            l += 1
            self.rgf.produce_shared_forest(self.s, l)
            cache = self.rgf.compute_cached_index(l, {})
        cnt = self.rgf.get_total_count(cache)
        at = random.randint(1, cnt) # at least 1 length
        v, tree = self.rgf.random_sample(self.s, at, cache)
        return fuzzer.tree_to_string(tree)

    def is_member(self, q):
        try: list(self.ep.recognize_on(q, self.s))
        except: return 0
        return 1

    # There are two things to consider here. The first is that we need to
    # generate inputs from both our regular expression as well as the given grammar.
    def is_equivalent(self, grammar, start):
        self.counter += 1
        if not grammar[start]:
            s = self.generate(self.counter)
            return False, s

        num_calls = math.ceil(1.0/self.epsilon *
                              (math.log(1.0/self.delta) + self.counter * math.log(2)))

        max_length_limit = 10
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

if __name__ == '__main__':
    teacher = Teacher('a*b*')
    g_T = ObservationTable(['a', 'b'], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher('a*b')
    g_T = ObservationTable(['a', 'b'], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher('ab')
    g_T = ObservationTable(['a', 'b'], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher('ab*')
    g_T = ObservationTable(['a', 'b'], teacher)
    g, s = l_star(g_T)
    print(s, g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Teacher(Teacher):
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == (&#x27;^&#x27;, &#x27;$&#x27;):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)

        g, s = self.fix_epsilon(self.g, self.s)

        self.ep = earleyparser.EarleyParser(g)
        self.rgf = cfgrandomsample.RandomSampleCFG(g)
        self.counter = 0
        # epsilon is the accuracy and delta is the confidence
        self.delta, self.epsilon = 0.1, 0.1

    def generate(self, l):
        cache = {}
        while not cache:
            l += 1
            self.rgf.produce_shared_forest(self.s, l)
            cache = self.rgf.compute_cached_index(l, {})
        cnt = self.rgf.get_total_count(cache)
        at = random.randint(1, cnt) # at least 1 length
        v, tree = self.rgf.random_sample(self.s, at, cache)
        return fuzzer.tree_to_string(tree)

    def is_member(self, q):
        try: list(self.ep.recognize_on(q, self.s))
        except: return 0
        return 1

    # There are two things to consider here. The first is that we need to
    # generate inputs from both our regular expression as well as the given grammar.
    def is_equivalent(self, grammar, start):
        self.counter += 1
        if not grammar[start]:
            s = self.generate(self.counter)
            return False, s

        num_calls = math.ceil(1.0/self.epsilon *
                              (math.log(1.0/self.delta) + self.counter * math.log(2)))

        max_length_limit = 10
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

if __name__ == &#x27;__main__&#x27;:
    teacher = Teacher(&#x27;a*b*&#x27;)
    g_T = ObservationTable([&#x27;a&#x27;, &#x27;b&#x27;], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher(&#x27;a*b&#x27;)
    g_T = ObservationTable([&#x27;a&#x27;, &#x27;b&#x27;], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher(&#x27;ab&#x27;)
    g_T = ObservationTable([&#x27;a&#x27;, &#x27;b&#x27;], teacher)
    g, s = l_star(g_T)
    print(s, g)

    teacher = Teacher(&#x27;ab*&#x27;)
    g_T = ObservationTable([&#x27;a&#x27;, &#x27;b&#x27;], teacher)
    g, s = l_star(g_T)
    print(s, g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Using it

<!--
############
import re
exprs = ['a*b*', 'ab', 'a*b', 'ab*', 'a|b', 'aba']
for e in exprs:
    teacher = Teacher(e)
    tbl = ObservationTable(['a', 'b'], teacher)
    g, s = l_star(tbl)
    print(s, g)

    ep = earleyparser.EarleyParser(g)
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        res = gf.iter_fuzz(key=s, max_depth=100)
        v = re.fullmatch(e, res)
        a, b = v.span()
        assert a == 0, b == len(res)
        print(a,b)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import re
exprs = [&#x27;a*b*&#x27;, &#x27;ab&#x27;, &#x27;a*b&#x27;, &#x27;ab*&#x27;, &#x27;a|b&#x27;, &#x27;aba&#x27;]
for e in exprs:
    teacher = Teacher(e)
    tbl = ObservationTable([&#x27;a&#x27;, &#x27;b&#x27;], teacher)
    g, s = l_star(tbl)
    print(s, g)

    ep = earleyparser.EarleyParser(g)
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        res = gf.iter_fuzz(key=s, max_depth=100)
        v = re.fullmatch(e, res)
        a, b = v.span()
        assert a == 0, b == len(res)
        print(a,b)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Notes
While there is no strict specifications as to what grammar induction,
inference, and learning is, according to [Higuera](http://videolectures.net/mlcs07_higuera_giv/),
Grammar inference is about learning a *grammar* (i.e. the representation) when
given information about a language, and focuses on the target, the grammar.
That is, you start with the assumption that a target grammar exists. Then,
try to guess that grammar based on your observations.
If on the other hand, you do not believe that a particular target grammar
exists, but want to do the best to learn the underlying principles, then it is
grammar induction. That is, it focuses on the best possible grammar for the
given data. Closely related fields are grammar mining, grammar recovery,
and grammar extraction which are all whitebox approaches based on program
or related artifact analysis. Language acquisition is another related term.

[^angluin1987]: Learning Regular Sets from Queries and Counterexamples, 1987 
[^angluin1988]: Queries and Concept Learning, 1988
[^valiant1984]: A theory of the learnable, 1984

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-01-04-lstar-learning-regular-languages.py).


