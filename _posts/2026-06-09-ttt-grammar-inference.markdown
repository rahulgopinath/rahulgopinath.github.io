---
published: true
title: Learning Regular Languages with the TTT Algorithm
layout: post
comments: true
tags: regular-grammars induction
categories: post
---

TLDR; This tutorial is a complete implementation of the TTT algorithm
for active automata learning in Python. TTT combines the discrimination
tree of Kearns and Vazirani with binary search counterexample analysis
from Rivest and Schapire, and adds prefix transformation and discriminator
finalization to eliminate all redundant membership queries. The Python
interpreter is embedded so that you can work through the implementation
steps.

Why learn an input language?

Suppose you are given a piece of software. For example,  a network protocol
implementation, a parser, or a security filter. You want to understand what
inputs it accepts. You have no access to the source code, and can only run it
and observe whether it accepts or rejects a given input.
This is the blackbox setting.

A naive answer is to try to test it exhaustively. But the set of all strings
accepted by even simple grammars is infinite.
A better approach is to infer a finite model, that is a DFA, that captures the
input behaviour exactly. Such a model is useful on its own. You can inspect
it, verify properties, generate tests from it, or compare it against a
specification to find discrepancies.
Active automata learning is the discipline of constructing this model
efficiently, using as few queries as possible.
 
In my [previous post](/post/2024/01/04/lstar-learning-regular-languages/),
I implemented Angluin's L* algorithm for learning regular languages from
a blackbox oracle. L* uses a flat observation table to track state
distinctions, which leads to redundant membership queries: when a
counterexample arrives, all its suffixes are added as columns even though
most distinguish no new states.

TTT is the state-of-the art algorithm for regular language inference. Using
this algorithm, you can infer the input language of any blackbox program
up to its regular approximation. It is much more faster than L*, and the
number of membership queries it generates (that is, the number of inputs
it needs to test the blackbox with) is provably non-redundant.
 
Several independent contributions are incorporated in the TTT algorithm.
Rivest and Schapire[^rivest1993] contributed the binary search
counterexample analysis, which finds the single relevant suffix in a
counterexample in $$ O(\log k) $$ queries (rather than $$ k $$ queries).
The introduction of discrimination tree as a replacement for the observation
table is due Kearns and Vazirani[^kearns1994].

TTT by Isberner, Howar and Steffen[^isberner2014]
adds two further refinements: *prefix transformation*,
which keeps access sequences minimal, and *discriminator finalization*,
which keeps the discrimination tree shallow.
TTT is provably redundancy-free. That is, it never makes a membership query
whose answer could have been derived from earlier queries.

Language inference can also be applied to hardware. There are however,
other considerations in such settings. For example, it may not be possible
or even expensive to restart a system.
ADT[^adt] is a notable extension of TTT, which uses adaptive
distinguishing sequences, and can reduce resets in hardware settings.

## Definitions

* _Alphabet_ $$ A $$: the set of input symbols the DFA reads.
* _Membership query_: a string passed to the blackbox oracle. The oracle
  answers yes (accepted) or no (rejected).
* _Equivalence query_: a hypothesis grammar passed to the teacher. The
  teacher answers yes, or returns a counterexample string where the
  hypothesis and the target disagree.
* _PAC oracle_: a probabilistic approximation to the equivalence oracle.
  After $$ N $$ random tests without finding a counterexample, we declare
  the hypothesis probably approximately correct.
* _Discrimination tree (DT)_: a binary tree whose inner nodes are
  discriminator suffixes and whose leaves are states. Sifting a string
  $$ w $$ through the tree classifies it to a state using one membership
  query per level.
* _Access sequence_ $$ reach(q) $$: the shortest known string that reaches
  state $$ q $$ in the target. This is called $$ acc(q) $$ in TTT literature,
  but using $$ reach(q) $$ to avoid conflation with $$ accept $$ in DFA.
* _Spanning tree_: a mapping from each known state to its access sequence.
  In this implementation we use a dict (called State Table) rather than
  a tree.
* _Open transition_: a transition from state $$ q $$ on symbol $$ a $$ that
  has not yet been sifted to determine its target state.
* _Counterexample decomposition_: the process of finding the split point
  in a counterexample, extracting a new discriminator, and splitting a
  leaf in the DT.

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

We use the `Teacher` and `Oracle` from the L* post unchanged.
The rest of the algorithm is independent of L*.

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
<li><a href="https://rahul.gopinath.org/py/lstar-0.0.1-py2.py3-none-any.whl">lstar-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2024/01/04/lstar-learning-regular-languages/">L* Algorithm</a>".</li>
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
https://rahul.gopinath.org/py/lstar-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import math
import random
import lstar

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import math
import random
import lstar
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Since this notebook serves both as a web notebook as well as a script
that can be run on the command line, we redefine canvas if it is not
defined already. The `__canvas__` function is defined externally when
it is used as a web notebook.

<!--
############
if '__canvas__' not in globals(): __canvas__ = print

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
if &#x27;__canvas__&#x27; not in globals(): __canvas__ = print
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## From L* to TTT

In L*, when the equivalence oracle returns a counterexample $$ ce $$ of
length $$ k $$, the algorithm adds all $$ k $$ suffixes of $$ ce $$ as
new columns (i.e. discriminators for states).
For each new column, it must re-query every existing row.
However, many of these new columns are redundant because they do not
distinguish any new pair of states.

The key insight that distinguishes TTT from L* is that
**a counterexample identifies only one pair of states** that was wrongly
merged. Hence, exactly **one** new discriminator is sufficient, not $$ k $$.
TTT incorporates the following independent contributions:

* **Kearns and Vazirani (1994)**[^kearns1994] replaced the observation
  table with a *discrimination tree*. A binary tree of discriminator
  suffixes where each leaf is a state.
  Sifting a string down the tree classifies it in $$ O(depth) $$ queries
  rather than $$ O(|suffixes|) $$.
* **Rivest and Schapire (1993)**[^rivest1993] showed that binary search
  over the counterexample finds the single relevant split point in
  $$ O(\log k) $$ queries, rather than adding all $$ k $$ suffixes.
* **Isberner, Howar and Steffen (2014)**[^isberner2014] combined these
  with *prefix transformation* (keeping access sequences minimal) and
  *discriminator finalization* (keeping the DT shallow), producing TTT.

The combination of a discrimination tree with a spanning tree of access
sequences is known as an *observation pack* [^howar2012]. This post does
not use that abstraction directly; we manage the two structures separately.

## The DFA Representation

The `DFA` class is similar to the one from the
[RPNI post](/post/2025/10/24/rpni-learning-regular-languages/).

<!--
############
class DFA:
    def __init__(self, start_symbol='<start>', key_counter=0):
        self.grammar = {}
        self.start_symbol = start_symbol
        self.grammar[self.start_symbol] = []
        self.key_counter = key_counter

    def transition(self, key, char):
        rules = self.grammar[key]
        for rule in rules:
            if not rule: continue
            if char == rule[0]: return rule
        return None

    def add_transition(self, from_key, token, to_key):
        self.grammar[from_key].append([token, to_key])

    def set_accepting(self, key):
        if [] not in self.grammar[key]:
            self.grammar[key].append([])

    def ensure_state(self, key):
        if key not in self.grammar:
            self.grammar[key] = []

    def new_state(self):
        key = '<%s>' % self.key_counter
        self.grammar[key] = []
        self.key_counter += 1
        return key


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA:
    def __init__(self, start_symbol=&#x27;&lt;start&gt;&#x27;, key_counter=0):
        self.grammar = {}
        self.start_symbol = start_symbol
        self.grammar[self.start_symbol] = []
        self.key_counter = key_counter

    def transition(self, key, char):
        rules = self.grammar[key]
        for rule in rules:
            if not rule: continue
            if char == rule[0]: return rule
        return None

    def add_transition(self, from_key, token, to_key):
        self.grammar[from_key].append([token, to_key])

    def set_accepting(self, key):
        if [] not in self.grammar[key]:
            self.grammar[key].append([])

    def ensure_state(self, key):
        if key not in self.grammar:
            self.grammar[key] = []

    def new_state(self):
        key = &#x27;&lt;%s&gt;&#x27; % self.key_counter
        self.grammar[key] = []
        self.key_counter += 1
        return key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also add `run()`, which returns the state reached after consuming a string,
and `accepts()`, which checks whether that state is an accepting state.

<!--
############
class DFA(DFA):
    def run(self, string):
        state = self.start_symbol
        for char in string:
            rule = self.transition(state, char)
            if rule is None: return None
            state = rule[1]
        return state

    def accepts(self, string):
        state = self.run(string)
        if state is None: return False
        return [] in self.grammar[state]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA(DFA):
    def run(self, string):
        state = self.start_symbol
        for char in string:
            rule = self.transition(state, char)
            if rule is None: return None
            state = rule[1]
        return state

    def accepts(self, string):
        state = self.run(string)
        if state is None: return False
        return [] in self.grammar[state]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The DFA class can now model a deterministic finite state machine.
We also add a helper to render any DFA as a Graphviz dot diagram.

<!--
############
def dfa_to_dot(dfa, name='DFA'):
    lines = ['digraph %s {' % name,
             '  rankdir=LR;',
             '  node [shape = circle];',
             '  __start__ [shape = point, label = ""];',
             '  __start__ -> "%s";' % dfa.start_symbol]
    for state, rules in dfa.grammar.items():
        accepting = [] in rules
        shape = 'doublecircle' if accepting else 'circle'
        lines.append('  "%s" [shape = %s];' % (state, shape))
        for rule in rules:
            if not rule: continue
            char, target = rule[0], rule[1]
            lines.append('  "%s" -> "%s" [label = "%s"];' % (state, target, char))
    lines.append('}')
    return '\n'.join(lines)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def dfa_to_dot(dfa, name=&#x27;DFA&#x27;):
    lines = [&#x27;digraph %s {&#x27; % name,
             &#x27;  rankdir=LR;&#x27;,
             &#x27;  node [shape = circle];&#x27;,
             &#x27;  __start__ [shape = point, label = &quot;&quot;];&#x27;,
             &#x27;  __start__ -&gt; &quot;%s&quot;;&#x27; % dfa.start_symbol]
    for state, rules in dfa.grammar.items():
        accepting = [] in rules
        shape = &#x27;doublecircle&#x27; if accepting else &#x27;circle&#x27;
        lines.append(&#x27;  &quot;%s&quot; [shape = %s];&#x27; % (state, shape))
        for rule in rules:
            if not rule: continue
            char, target = rule[0], rule[1]
            lines.append(&#x27;  &quot;%s&quot; -&gt; &quot;%s&quot; [label = &quot;%s&quot;];&#x27; % (state, target, char))
    lines.append(&#x27;}&#x27;)
    return &#x27;\n&#x27;.join(lines)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test it thoroughly.

<!--
############
dfa = DFA()
s1 = dfa.new_state()
dfa.add_transition('<start>', 'a', s1)
dfa.add_transition(s1, 'a', '<start>')
dfa.add_transition('<start>', 'b', '<start>')
dfa.add_transition(s1, 'b', s1)
dfa.set_accepting('<start>')
assert dfa.run('') == '<start>'
assert dfa.run('a') == s1
assert dfa.run('aa') == '<start>'
assert dfa.run('x') is None
assert dfa.accepts('')
assert dfa.accepts('aa')
assert not dfa.accepts('a')
__canvas__(dfa_to_dot(dfa, 'DFA_even_a'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dfa = DFA()
s1 = dfa.new_state()
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;, s1)
dfa.add_transition(s1, &#x27;a&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa.add_transition(s1, &#x27;b&#x27;, s1)
dfa.set_accepting(&#x27;&lt;start&gt;&#x27;)
assert dfa.run(&#x27;&#x27;) == &#x27;&lt;start&gt;&#x27;
assert dfa.run(&#x27;a&#x27;) == s1
assert dfa.run(&#x27;aa&#x27;) == &#x27;&lt;start&gt;&#x27;
assert dfa.run(&#x27;x&#x27;) is None
assert dfa.accepts(&#x27;&#x27;)
assert dfa.accepts(&#x27;aa&#x27;)
assert not dfa.accepts(&#x27;a&#x27;)
__canvas__(dfa_to_dot(dfa, &#x27;DFA_even_a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The Oracle

Let us define a simple mock oracle for testing the components in isolation.
The `Teacher` imported from L* is the full oracle, and will be used in the
main loop.

<!--
############
class MockOracle(lstar.Oracle):
    def __init__(self, fn):
        self.fn = fn
    def is_member(self, q):
        return self.fn(q)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class MockOracle(lstar.Oracle):
    def __init__(self, fn):
        self.fn = fn
    def is_member(self, q):
        return self.fn(q)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The Discrimination Tree

The discrimination tree (DT) replaces L*'s flat observation table.
Think of it as a game of 20 questions: each inner node asks:
**if I append suffix $$ d $$ to this string, does the target accept it?**
and routes left (no) or right (yes). Each leaf is a known state.

The discriminator suffixes at different nodes are **independent strings**
with no relationship to each other; they play the same role as the suffix
columns in L*, but each counterexample adds exactly one, rather than all
$$ k $$ suffixes of the counterexample at once.
 
The tree structure is not a trie; a parent's suffix is not a prefix of its
children's suffixes, and there is no requirement that sibling suffixes share
anything in common. The tree is purely a *decision structure*: each node's
suffix is the question that splits the states reachable at that point, chosen
only because it distinguishes some pair of states that would otherwise be
merged. Two nodes at different depths may share a suffix, or their suffixes
may be completely unrelated; what matters is only the binary answer at each
step.

Both children of an inner node can themselves be inner nodes, and the tree
can be arbitrarily deep. A leaf represents a known state; it has no
discriminator. Early in learning the tree is shallow; each counterexample
adds exactly one new inner node, splitting one existing leaf into two children.

A node starts life as a leaf holding a state name. When the equivalence
oracle returns a counterexample, it means the blackbox and the hypothesis DFA
disagree on some string: two strings that reach different blackbox states are
being routed to the same hypothesis state. `decompose` identifies which leaf
is responsible and splits it.

Splitting a leaf means it becomes an inner node: it forgets its state name,
gains a discriminator suffix, and sprouts two child leaves, one for each of
the two now-distinct states. Which child goes right and which goes left is
determined by querying the oracle on `reach(old_state) + discriminator`. A
right child means that query returned True; a left child means it returned
False. Note that right does not mean "accepted": later, when sifting an
arbitrary string $$ w $$, the same node asks whether $$ w + discriminator $$
is accepted, and routes right on True, left on False. The direction encodes
agreement with the oracle, not acceptance of $$ w $$ itself.

We mutate in place because other nodes in the tree already
hold references to this object; replacing it with a new object would leave
those references stale. The `split` method (called `split_leaf` in TTT
literature) encapsulates this mutation.

<!--
############
class DTNode:
    _counter = 0

    def __init__(self, state):
        DTNode._counter += 1
        self.node_id = DTNode._counter
        self.state, self.discriminator = state, None
        # self.right is the branch taken when oracle returns True
        self.left, self.right = None, None

    def is_leaf(self):
        return self.state is not None

    def split(self, discriminator, new_state, oracle, st):
        old_child, new_child = DTNode(self.state), DTNode(new_state)

        if oracle.is_member(st.reach(self.state) + discriminator):
            self.left, self.right = new_child, old_child
        else:
            self.left, self.right  = old_child, new_child

        self.state, self.discriminator = None, discriminator
        return old_child, new_child

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DTNode:
    _counter = 0

    def __init__(self, state):
        DTNode._counter += 1
        self.node_id = DTNode._counter
        self.state, self.discriminator = state, None
        # self.right is the branch taken when oracle returns True
        self.left, self.right = None, None

    def is_leaf(self):
        return self.state is not None

    def split(self, discriminator, new_state, oracle, st):
        old_child, new_child = DTNode(self.state), DTNode(new_state)

        if oracle.is_member(st.reach(self.state) + discriminator):
            self.left, self.right = new_child, old_child
        else:
            self.left, self.right  = old_child, new_child

        self.state, self.discriminator = None, discriminator
        return old_child, new_child
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The State Table

Each state in the hypothesis has an *access sequence*: the shortest known
string that reaches it from `<start>`. The TTT paper calls this structure
a *spanning tree* because, conceptually, the states form a tree: `<start>`
is the root, each state is a child of the state whose access sequence is one
character shorter, and walking from root to any node spells out that node's
access sequence. In the original Kearns-Vazirani algorithm this tree was
traversed explicitly: to find a state's access sequence you'd walk up to the
root collecting edge labels. TTT's prefix transformation makes traversal
unnecessary by storing the full access string directly against each state.
The tree structure is therefore implicit, and the implementation reduces to
a plain dict. We call the class `StateTable` to reflect what it actually is.

<!--
############
class StateTable:
    def __init__(self, start_symbol='<start>'):
        self._reach = { start_symbol: '' }

    def add_state(self, state, parent, char):
        self._reach[state] = self._reach[parent] + char

    def reach(self, state):
        return self._reach[state]

    def is_reachable(self, state):
        return state in self._reach

    def states(self):
        return list(self._reach.keys())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class StateTable:
    def __init__(self, start_symbol=&#x27;&lt;start&gt;&#x27;):
        self._reach = { start_symbol: &#x27;&#x27; }

    def add_state(self, state, parent, char):
        self._reach[state] = self._reach[parent] + char

    def reach(self, state):
        return self._reach[state]

    def is_reachable(self, state):
        return state in self._reach

    def states(self):
        return list(self._reach.keys())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test the node types before proceeding.

<!--
############
leaf = DTNode('<start>')
assert leaf.is_leaf() == True
st_t = StateTable()
st_t.add_state('<1>', '<start>', 'a')
oracle_t = MockOracle(lambda w: w.count('a') % 2 == 0)
leaf.split('', '<1>', oracle_t, st_t)
assert leaf.is_leaf() == False
assert leaf.discriminator == ''

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
leaf = DTNode(&#x27;&lt;start&gt;&#x27;)
assert leaf.is_leaf() == True
st_t = StateTable()
st_t.add_state(&#x27;&lt;1&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
oracle_t = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
leaf.split(&#x27;&#x27;, &#x27;&lt;1&gt;&#x27;, oracle_t, st_t)
assert leaf.is_leaf() == False
assert leaf.discriminator == &#x27;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Sifting

To classify any string $$ w $$ to a state, we walk the DT from root to
leaf. At each inner node labeled $$ d $$, we query $$ member(w \cdot d) $$
and go right (yes) or left (no). The leaf we land on is the state $$ w $$
belongs to. Each step is one membership query, so sifting costs at most
$$ depth(DT) $$ queries, far fewer than L*'s $$ O(|suffixes|) $$.

At any inner node, either child may itself be another inner node. This is
not like a trie where deeper nodes share a common prefix with their parent;
the suffix at a deeper node is simply a different, independent question
that separates states the shallower question could not. The tree gets deeper
only when a pair of states survive all questions asked so far and a new
discriminator must be introduced to tell them apart. Keeping the tree
shallow therefore reduces the query cost of every future sift, which is why
TTT's discriminator finalization step aggressively replaces long, incidental
discriminators with shorter, permanent ones.

<!--
############
def sift(node, w, oracle):
    while not node.is_leaf():
        if oracle.is_member(w + node.discriminator):
            node = node.right
        else:
            node = node.left
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def sift(node, w, oracle):
    while not node.is_leaf():
        if oracle.is_member(w + node.discriminator):
            node = node.right
        else:
            node = node.left
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also add a helper to render a DT as a Graphviz dot diagram.
Inner nodes show their discriminator suffix; leaves show the state name.
Left edges (membership query returned False) are labelled "no";
right edges (True) are labelled "yes".
An empty discriminator is shown as $$\varepsilon$$ (epsilon), meaning the string itself
is queried with nothing appended.
An optional `tracer` argument (a `DTTracer`, defined below) colours the
recorded sift path blue.

<!--
############
def dt_to_dot(root, name='DT', tracer=None):
    path_nodes = tracer.path_nodes if tracer else set()
    path_edges = tracer.path_edges if tracer else set()
    lines = ['digraph %s {' % name, '  rankdir=TB;', '  node [shape = rectangle];']
    counter = [0]
    def node_id():
        counter[0] += 1
        return 'n%d' % counter[0]
    def blue(attrs):
        return attrs + ', color=blue, fontcolor=blue'
    def walk(node, nid):
        on_path = id(node) in path_nodes
        if node.is_leaf():
            attrs = 'shape = ellipse, label = "%s"' % node.state
            if on_path: attrs = blue(attrs)
            lines.append('  %s [%s];' % (nid, attrs))
        else:
            disc = node.discriminator if node.discriminator != '' else 'ε'
            attrs = 'label = "d: %s"' % disc
            if on_path: attrs = blue(attrs)
            lines.append('  %s [%s];' % (nid, attrs))
            left_id  = node_id()
            right_id = node_id()
            walk(node.left,  left_id)
            walk(node.right, right_id)
            no_attrs  = 'label = "no"'
            yes_attrs = 'label = "yes"'
            if (id(node), id(node.left))  in path_edges:
                no_attrs  += ', color=blue, fontcolor=blue, penwidth=2'
            if (id(node), id(node.right)) in path_edges:
                yes_attrs += ', color=blue, fontcolor=blue, penwidth=2'
            lines.append('  %s -> %s [%s];' % (nid, left_id,  no_attrs))
            lines.append('  %s -> %s [%s];' % (nid, right_id, yes_attrs))
    walk(root, node_id())
    lines.append('}')
    return '\n'.join(lines)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def dt_to_dot(root, name=&#x27;DT&#x27;, tracer=None):
    path_nodes = tracer.path_nodes if tracer else set()
    path_edges = tracer.path_edges if tracer else set()
    lines = [&#x27;digraph %s {&#x27; % name, &#x27;  rankdir=TB;&#x27;, &#x27;  node [shape = rectangle];&#x27;]
    counter = [0]
    def node_id():
        counter[0] += 1
        return &#x27;n%d&#x27; % counter[0]
    def blue(attrs):
        return attrs + &#x27;, color=blue, fontcolor=blue&#x27;
    def walk(node, nid):
        on_path = id(node) in path_nodes
        if node.is_leaf():
            attrs = &#x27;shape = ellipse, label = &quot;%s&quot;&#x27; % node.state
            if on_path: attrs = blue(attrs)
            lines.append(&#x27;  %s [%s];&#x27; % (nid, attrs))
        else:
            disc = node.discriminator if node.discriminator != &#x27;&#x27; else &#x27;ε&#x27;
            attrs = &#x27;label = &quot;d: %s&quot;&#x27; % disc
            if on_path: attrs = blue(attrs)
            lines.append(&#x27;  %s [%s];&#x27; % (nid, attrs))
            left_id  = node_id()
            right_id = node_id()
            walk(node.left,  left_id)
            walk(node.right, right_id)
            no_attrs  = &#x27;label = &quot;no&quot;&#x27;
            yes_attrs = &#x27;label = &quot;yes&quot;&#x27;
            if (id(node), id(node.left))  in path_edges:
                no_attrs  += &#x27;, color=blue, fontcolor=blue, penwidth=2&#x27;
            if (id(node), id(node.right)) in path_edges:
                yes_attrs += &#x27;, color=blue, fontcolor=blue, penwidth=2&#x27;
            lines.append(&#x27;  %s -&gt; %s [%s];&#x27; % (nid, left_id,  no_attrs))
            lines.append(&#x27;  %s -&gt; %s [%s];&#x27; % (nid, right_id, yes_attrs))
    walk(root, node_id())
    lines.append(&#x27;}&#x27;)
    return &#x27;\n&#x27;.join(lines)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`DTTracer` wraps a real DT node and records every step taken during a sift.
It proxies `is_leaf`, `discriminator`, `left`, `right`, and `state` to the
wrapped node, but intercepts the `left`/`right` accesses to record which
edge was taken. After `sift(DTTracer(root), w, oracle)` returns, the tracer
holds `path_nodes` and `path_edges` as sets of `id()`s referencing the
*unwrapped* nodes, so they match what `dt_to_dot` sees.

<!--
############
class DTTracer:
    def __init__(self, node):
        self._node = node
        self.path_nodes = set()
        self.path_edges = set()

    def is_leaf(self):
        self.path_nodes.add(id(self._node))
        return self._node.is_leaf()

    @property
    def discriminator(self):
        return self._node.discriminator

    @property
    def state(self):
        return self._node.state

    @property
    def left(self):
        child = self._node.left
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @property
    def right(self):
        child = self._node.right
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @staticmethod
    def _transfer(tracer, node):
        # Return a new DTTracer for the child that shares the same recording sets.
        t = DTTracer(node)
        t.path_nodes = tracer.path_nodes
        t.path_edges = tracer.path_edges
        return t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DTTracer:
    def __init__(self, node):
        self._node = node
        self.path_nodes = set()
        self.path_edges = set()

    def is_leaf(self):
        self.path_nodes.add(id(self._node))
        return self._node.is_leaf()

    @property
    def discriminator(self):
        return self._node.discriminator

    @property
    def state(self):
        return self._node.state

    @property
    def left(self):
        child = self._node.left
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @property
    def right(self):
        child = self._node.right
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @staticmethod
    def _transfer(tracer, node):
        # Return a new DTTracer for the child that shares the same recording sets.
        t = DTTracer(node)
        t.path_nodes = tracer.path_nodes
        t.path_edges = tracer.path_edges
        return t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test sifting on the even-a's example: the DT has one discriminator
(the empty string) that separates even-a states from odd-a states.

**Single leaf:** every string sifts to `<start>`.

<!--
############
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
dt = DTNode('<start>')
assert sift(dt, 'aa', oracle).state == '<start>'
assert sift(dt, '', oracle).state == '<start>'
__canvas__(dt_to_dot(dt, 'DT_single'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
dt = DTNode(&#x27;&lt;start&gt;&#x27;)
assert sift(dt, &#x27;aa&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
assert sift(dt, &#x27;&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
__canvas__(dt_to_dot(dt, &#x27;DT_single&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Two-level tree:** a single split on discriminator $$\varepsilon$$ separates `<odd>`
(rejects $$\varepsilon$$) from `<start>` (accepts $$\varepsilon$$, since `''` has zero a's).
We start from a single-leaf DT rooted at `<start>` and split it,
recording that `<odd>` is reached via `'a'`.

<!--
############
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
st_ea = StateTable()
st_ea.add_state('<odd>', '<start>', 'a')
dt = DTNode('<start>')
dt.split('', '<odd>', oracle, st_ea)
assert sift(dt, 'aa', oracle).state == '<start>'
assert sift(dt, 'a', oracle).state == '<odd>'
assert sift(dt, '', oracle).state == '<start>'
assert sift(dt, 'b', oracle).state == '<start>'
__canvas__(dt_to_dot(dt, 'DT_even_a'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
st_ea = StateTable()
st_ea.add_state(&#x27;&lt;odd&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
dt = DTNode(&#x27;&lt;start&gt;&#x27;)
dt.split(&#x27;&#x27;, &#x27;&lt;odd&gt;&#x27;, oracle, st_ea)
assert sift(dt, &#x27;aa&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
assert sift(dt, &#x27;a&#x27;, oracle).state == &#x27;&lt;odd&gt;&#x27;
assert sift(dt, &#x27;&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
assert sift(dt, &#x27;b&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
__canvas__(dt_to_dot(dt, &#x27;DT_even_a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Sifting `'a'` (odd a's) goes left to `<odd>`; sifting `'aa'` (even a's) goes right to `<start>`.

<!--
############
_tr = DTTracer(dt)
sift(_tr, 'a', oracle)
__canvas__(dt_to_dot(dt, 'DT_sift_a', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_tr = DTTracer(dt)
sift(_tr, &#x27;a&#x27;, oracle)
__canvas__(dt_to_dot(dt, &#x27;DT_sift_a&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Sifting `'aa'` goes right.

<!--
############
_tr = DTTracer(dt)
sift(_tr, 'aa', oracle)
__canvas__(dt_to_dot(dt, 'DT_sift_aa', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_tr = DTTracer(dt)
sift(_tr, &#x27;aa&#x27;, oracle)
__canvas__(dt_to_dot(dt, &#x27;DT_sift_aa&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The two examples above only ever have one inner node at the root. To see
both children being inner nodes, consider what happens after a second split.
We split the `<start>` leaf again: discriminator `'aa'` separates `<start>`
(accepts `'aa'`) from a new state `<even2>` (rejects `'aa'`, e.g. reached
via `'aaa'`). The right child of the root is now itself an inner node, and
sifting takes two steps before reaching a leaf.

<!--
############
st_ea.add_state('<even2>', '<start>', 'aaa')
dt3 = DTNode('<start>')
dt3.split('', '<odd>', oracle, st_ea)
# dt3.right is now the <start> leaf; split it on 'aa'
dt3.right.split('aa', '<even2>', oracle, st_ea)
__canvas__(dt_to_dot(dt3, 'DT_three_state'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
st_ea.add_state(&#x27;&lt;even2&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;aaa&#x27;)
dt3 = DTNode(&#x27;&lt;start&gt;&#x27;)
dt3.split(&#x27;&#x27;, &#x27;&lt;odd&gt;&#x27;, oracle, st_ea)
# dt3.right is now the &lt;start&gt; leaf; split it on &#x27;aa&#x27;
dt3.right.split(&#x27;aa&#x27;, &#x27;&lt;even2&gt;&#x27;, oracle, st_ea)
__canvas__(dt_to_dot(dt3, &#x27;DT_three_state&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Sifting `'aa'` through the three-state DT:

    node d=''  : member('aa' + '') = member('aa') = True  -> go right
    node d='aa': member('aa' + 'aa') = member('aaaa') = True -> go right
    leaf <start>: done.

<!--
############
_tr = DTTracer(dt3)
sift(_tr, 'aa', oracle)
__canvas__(dt_to_dot(dt3, 'DT_sift_three_aa', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_tr = DTTracer(dt3)
sift(_tr, &#x27;aa&#x27;, oracle)
__canvas__(dt_to_dot(dt3, &#x27;DT_sift_three_aa&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Sifting `'aaa'`: goes right at root, then `member('aaa'+'aa')` = False,
go left to leaf `<even2>`.

<!--
############
_tr = DTTracer(dt3)
sift(_tr, 'aaa', oracle)
__canvas__(dt_to_dot(dt3, 'DT_sift_three_aaa', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_tr = DTTracer(dt3)
sift(_tr, &#x27;aaa&#x27;, oracle)
__canvas__(dt_to_dot(dt3, &#x27;DT_sift_three_aaa&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The even-a's DT uses $$ \varepsilon $$ as its discriminator because membership of the
access sequence alone distinguishes all states. Most targets produce
non-empty discriminators; we will see this concretely in the
Counterexample Decomposition section and in the full worklist walkthrough.

## Hypothesis Construction

At any point during learning, we have a DT and a state table. Together
they are enough to construct a complete hypothesis DFA. The states of the
DFA are exactly the states recorded in the state table. The transitions
are derived by sifting: for each state $$ q $$ and each alphabet symbol
$$ a $$, form $$ reach(q) \cdot a $$ and sift it through the DT. The leaf
it lands on identifies the target state. Repeat for every $$ (q, a) $$ pair
and the full transition table is filled.

Concretely, for the even-a's example with a two-leaf DT (discriminator `''`,
left = `<odd>`, right = `<start>`), and state table
`{<start>: '', <odd>: 'a'}`:

    sift('a') : node d='': member('a' +'') = False -> left  => <start> -a-> <odd>
    sift('b') : node d='': member('b' +'') = True  -> right => <start> -b-> <start>
    sift('aa'): node d='': member('aa'+'') = True  -> right => <odd>   -a-> <start>
    sift('ab'): node d='': member('ab'+'') = False -> left  => <odd>   -b-> <odd>

A transition is *open* if it is absent from the DFA entirely, meaning it has
not yet been sifted to determine its target state.

<!--
############
def is_open(dfa, state, char):
    return dfa.transition(state, char) is None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_open(dfa, state, char):
    return dfa.transition(state, char) is None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
`close_transitions` works through all known states, sifting each open
transition. When sifting discovers a state not yet in the state table,
that state is added and appended to the work list so its own transitions
are processed in the same pass. This means the loop may grow as it runs:
starting with one state, it may end with the full set.

`leaf_index` maps `leaf.node_id` to the list of `(state, char)` transitions
that sifted to that leaf. It is passed in explicitly so its contents are
visible to callers; `update_hypothesis` reads it to find stale transitions.

<!--
############
def close_transitions(dfa, dt, st, oracle, alphabet, leaf_index):
    states = st.states()
    while states:
        state, *states = states
        dfa.ensure_state(state)
        for char in alphabet:
            if not is_open(dfa, state, char): continue
            target_leaf = sift(dt, st.reach(state) + char, oracle)
            target_state = target_leaf.state
            if not st.is_reachable(target_state):
                # new state discovered: register and queue for processing
                st.add_state(target_state, state, char)
                states.append(target_state)
            dfa.add_transition(state, char, target_state)
            # record which leaf this transition landed on, for stale detection
            leaf_index.setdefault(target_leaf.node_id, []).append((state, char))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def close_transitions(dfa, dt, st, oracle, alphabet, leaf_index):
    states = st.states()
    while states:
        state, *states = states
        dfa.ensure_state(state)
        for char in alphabet:
            if not is_open(dfa, state, char): continue
            target_leaf = sift(dt, st.reach(state) + char, oracle)
            target_state = target_leaf.state
            if not st.is_reachable(target_state):
                # new state discovered: register and queue for processing
                st.add_state(target_state, state, char)
                states.append(target_state)
            dfa.add_transition(state, char, target_state)
            # record which leaf this transition landed on, for stale detection
            leaf_index.setdefault(target_leaf.node_id, []).append((state, char))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Accepting states are determined by querying the oracle directly on each
access sequence. If $$ reach(q) $$ is accepted by the target, then $$ q $$
is an accepting state.

<!--
############
def build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index):
    for state in st.states():
        dfa.ensure_state(state)
        if oracle.is_member(st.reach(state)):
            dfa.set_accepting(state)
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index):
    for state in st.states():
        dfa.ensure_state(state)
        if oracle.is_member(st.reach(state)):
            dfa.set_accepting(state)
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
To see what closing looks like step by step, consider the even-a's target
with alphabet {a, b}. We start with one state `<start>` and a single-leaf
DT. Every transition is open because no target state has been determined yet.
Closing sifts `reach(<start>) + 'a'` = `'a'` and `reach(<start>) + 'b'` = `'b'`
through the single-leaf DT. Both land on `<start>`, so both transitions
point back to `<start>` -- the hypothesis says everything loops.
We visualise the DT and the resulting DFA at this stage.
 
DFA before the split.

<!--
############
oracle_ea = MockOracle(lambda w: w.count('a') % 2 == 0)
dfa_pre = DFA()
__canvas__(dfa_to_dot(dfa_pre, 'DFA_before_split'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle_ea = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
dfa_pre = DFA()
__canvas__(dfa_to_dot(dfa_pre, &#x27;DFA_before_split&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
DT before the split

<!--
############
dt_pre = DTNode('<start>')
__canvas__(dt_to_dot(dt_pre, 'DT_before_split'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dt_pre = DTNode(&#x27;&lt;start&gt;&#x27;)
__canvas__(dt_to_dot(dt_pre, &#x27;DT_before_split&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Build the hypothesis.

<!--
############
leaf_index_pre = {}
st_pre = StateTable()
build_hypothesis(dfa_pre, dt_pre, st_pre, oracle_ea, ['a', 'b'], leaf_index_pre)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
leaf_index_pre = {}
st_pre = StateTable()
build_hypothesis(dfa_pre, dt_pre, st_pre, oracle_ea, [&#x27;a&#x27;, &#x27;b&#x27;], leaf_index_pre)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
After the first counterexample (say `'a'`) is processed, `decompose` splits
the DT: a new inner node with discriminator `''` separates `<start>` (goes
right: accepts `''`) from new state `<odd>` (goes left: rejects `''`).
Re-sifting now correctly routes `'a'` to `<odd>` and `'b'` back to `<start>`.

<!--
############
st_post = StateTable()
st_post.add_state('<odd>', '<start>', 'a')
dt_post = DTNode('<start>')
dt_post.split('', '<odd>', oracle_ea, st_post)
__canvas__(dt_to_dot(dt_post, 'DT_after_split'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
st_post = StateTable()
st_post.add_state(&#x27;&lt;odd&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
dt_post = DTNode(&#x27;&lt;start&gt;&#x27;)
dt_post.split(&#x27;&#x27;, &#x27;&lt;odd&gt;&#x27;, oracle_ea, st_post)
__canvas__(dt_to_dot(dt_post, &#x27;DT_after_split&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
DFA built from the two-leaf DT above.

<!--
############
dfa_post = DFA()
build_hypothesis(dfa_post, dt_post, st_post, oracle_ea, ['a', 'b'], {})
__canvas__(dfa_to_dot(dfa_post, 'DFA_after_split'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dfa_post = DFA()
build_hypothesis(dfa_post, dt_post, st_post, oracle_ea, [&#x27;a&#x27;, &#x27;b&#x27;], {})
__canvas__(dfa_to_dot(dfa_post, &#x27;DFA_after_split&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Incremental Hypothesis Update
 
When `decompose` splits a leaf $$ \ell $$ into an inner node, every
transition that was previously routed to $$ \ell $$ is now stale: it
pointed to a single state, but the DT now says some of those strings
belong to the left child and some to the right.
 
We could re-sift every transition in the hypothesis from scratch, but that
is wasteful. Instead, `leaf_index` records exactly which `(state, char)`
pairs were routed to each leaf. We remove only those transitions from the
DFA and re-sift only them. Every other transition remains correct.
 
In the even-a's example, the initial DT has a single leaf `<start>`. Every
transition sifted during `build_hypothesis` therefore landed on that leaf,
so every transition is stale after the first split. After splitting on `''`
and registering `<1>` (the odd-a's state, called `<odd>` in earlier examples),
all transitions are removed and re-sifted through the two-node DT.
`<start> -a-> <start>` becomes `<start> -a-> <1>`; the rest route to the
same state as before.
`update_hypothesis` is called after a leaf split. It pops the stale
transitions from `leaf_index`, removes them from the DFA, then re-closes
to re-sift only those transitions plus the new state's open transitions.
This corresponds to TTT's incremental hypothesis update step.

<!--
############
def update_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index, split_id, new_state):
    # record the new state's accepting status and ensure it exists in the DFA
    dfa.ensure_state(new_state)
    if oracle.is_member(st.reach(new_state)):
        dfa.set_accepting(new_state)

    # collect transitions that pointed to the now-split leaf, then clear them
    stale = leaf_index.pop(split_id, [])

    # remove the stale transitions from the DFA grammar
    for (from_state, char) in stale:
        rules = dfa.grammar[from_state]
        dfa.grammar[from_state] = [r for r in rules if not (r and r[0] == char)]

    # re-close: re-sift the stale transitions and close new_state's transitions
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def update_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index, split_id, new_state):
    # record the new state&#x27;s accepting status and ensure it exists in the DFA
    dfa.ensure_state(new_state)
    if oracle.is_member(st.reach(new_state)):
        dfa.set_accepting(new_state)

    # collect transitions that pointed to the now-split leaf, then clear them
    stale = leaf_index.pop(split_id, [])

    # remove the stale transitions from the DFA grammar
    for (from_state, char) in stale:
        rules = dfa.grammar[from_state]
        dfa.grammar[from_state] = [r for r in rules if not (r and r[0] == char)]

    # re-close: re-sift the stale transitions and close new_state&#x27;s transitions
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test hypothesis construction on the even-a's example.

<!--
############
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
alphabet = ['a', 'b']
st = StateTable()
st.add_state('<odd>', '<start>', 'a')
dt = DTNode('<start>')
dt.split('', '<odd>', oracle, st)
leaf_index = {}
dfa = DFA()
build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)
assert dfa.transition('<start>', 'a')[1] == '<odd>'
assert dfa.transition('<start>', 'b')[1] == '<start>'
assert dfa.transition('<odd>', 'a')[1] == '<start>'
assert dfa.transition('<odd>', 'b')[1] == '<odd>'
assert dfa.accepts('')
assert dfa.accepts('aa')
assert not dfa.accepts('a')
assert st.reach('<odd>') == 'a'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
alphabet = [&#x27;a&#x27;, &#x27;b&#x27;]
st = StateTable()
st.add_state(&#x27;&lt;odd&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
dt = DTNode(&#x27;&lt;start&gt;&#x27;)
dt.split(&#x27;&#x27;, &#x27;&lt;odd&gt;&#x27;, oracle, st)
leaf_index = {}
dfa = DFA()
build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)
assert dfa.transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)[1] == &#x27;&lt;odd&gt;&#x27;
assert dfa.transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;)[1] == &#x27;&lt;start&gt;&#x27;
assert dfa.transition(&#x27;&lt;odd&gt;&#x27;, &#x27;a&#x27;)[1] == &#x27;&lt;start&gt;&#x27;
assert dfa.transition(&#x27;&lt;odd&gt;&#x27;, &#x27;b&#x27;)[1] == &#x27;&lt;odd&gt;&#x27;
assert dfa.accepts(&#x27;&#x27;)
assert dfa.accepts(&#x27;aa&#x27;)
assert not dfa.accepts(&#x27;a&#x27;)
assert st.reach(&#x27;&lt;odd&gt;&#x27;) == &#x27;a&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Counterexample Decomposition

When the equivalence oracle returns a counterexample $$ ce $$, we know the
hypothesis is wrong on $$ ce $$. But *where exactly* does it go wrong?

### The Split Point

Walk $$ ce $$ through the hypothesis. At position 0, both hypothesis and
target are in $$ \langle start \rangle $$, so they agree. At position
$$ |ce| $$, they disagree (that is what the counterexample means). So
somewhere in between is the *first point of disagreement*. That is, the
position $$ i $$ where the hypothesis first takes a wrong transition.

We find this by binary search in $$ O(\log|ce|) $$ queries. At each
midpoint $$ m $$, we check whether $$ reach(q_m) \cdot ce[m:] $$ gives the
same answer as the full counterexample. If yes, the split point is to the
right; if no, it is here or to the left.

### Prefix Transformation

After finding the split point $$ i $$, we need the string that reaches
state $$ q_i $$ and then reads $$ ce[i] $$. The raw counterexample prefix
$$ ce[:i+1] $$ would work, but we use $$ reach(q_i) \cdot ce[i] $$ instead.
This is the *prefix transformation*, and it gives two guarantees:

* **Correctness**: $$ reach(q_i) $$ traces a known path through the
  hypothesis, so the sift is guaranteed to work even if the hypothesis
  is partially stale.
* **Minimality**: the new state gets access sequence $$ reach(q_i) \cdot
  ce[i] $$, which is the shortest possible. Using $$ ce[:i+1] $$ could
  produce a much longer access sequence, making future sifts more expensive.

<!--
############
def prefix_transformation(states, st, ce, i):
    # replace the raw prefix ce[:i+1] with reach(q_i) + ce[i]
    # states[i] is the hypothesis state reached after consuming ce[:i]
    q_i = states[i]
    return st.reach(q_i) + ce[i], q_i

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def prefix_transformation(states, st, ce, i):
    # replace the raw prefix ce[:i+1] with reach(q_i) + ce[i]
    # states[i] is the hypothesis state reached after consuming ce[:i]
    q_i = states[i]
    return st.reach(q_i) + ce[i], q_i
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Splitting a Leaf

Once we have the split point, we know:

* A leaf $$ \ell $$ currently represents `old_state`
* `old_state` and `new_state` were treated as identical by the hypothesis,
  but the counterexample proves they are different
* The discriminator $$ ce[i+1:] $$ is the suffix that tells them apart

`DTNode.split` was introduced in the Discrimination Tree section above and
is used directly here. `decompose` calls it with the leaf found by sifting
the transformed prefix, the new discriminator, and the fresh state.

We now show `update_hypothesis` in action. We build the stale hypothesis
(single-leaf DT, everything loops to `<start>`), then split the leaf and
call `update_hypothesis`. The stale transition `<start> -a-> <start>` is
removed and re-sifted to `<1>`.

<!--
############
oracle_ea = MockOracle(lambda w: w.count('a') % 2 == 0)
dt_stale = DTNode('<start>')
st_stale = StateTable()
dfa_stale = DFA()
leaf_index_stale = {}
build_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea, ['a', 'b'],
                 leaf_index_stale)
__canvas__(dfa_to_dot(dfa_stale, 'DFA_stale'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle_ea = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
dt_stale = DTNode(&#x27;&lt;start&gt;&#x27;)
st_stale = StateTable()
dfa_stale = DFA()
leaf_index_stale = {}
build_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea, [&#x27;a&#x27;, &#x27;b&#x27;],
                 leaf_index_stale)
__canvas__(dfa_to_dot(dfa_stale, &#x27;DFA_stale&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Split the DT: add state `<1>` reached via `'a'`, then split the `<start>` leaf.

<!--
############
st_stale.add_state('<1>', '<start>', 'a')
# sift finds the current leaf for <start>; capture its id before mutating
start_leaf = sift(dt_stale, st_stale.reach('<start>'), MockOracle(lambda w: w.count('a') % 2 == 0))
split_id = start_leaf.node_id
start_leaf.split('', '<1>', oracle_ea, st_stale)
__canvas__(dt_to_dot(dt_stale, 'DT_after_split2'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
st_stale.add_state(&#x27;&lt;1&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
# sift finds the current leaf for &lt;start&gt;; capture its id before mutating
start_leaf = sift(dt_stale, st_stale.reach(&#x27;&lt;start&gt;&#x27;), MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0))
split_id = start_leaf.node_id
start_leaf.split(&#x27;&#x27;, &#x27;&lt;1&gt;&#x27;, oracle_ea, st_stale)
__canvas__(dt_to_dot(dt_stale, &#x27;DT_after_split2&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now update: stale transitions are removed and re-sifted.

<!--
############
update_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea, ['a', 'b'],
                  leaf_index_stale, split_id, '<1>')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
update_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea, [&#x27;a&#x27;, &#x27;b&#x27;],
                  leaf_index_stale, split_id, &#x27;&lt;1&gt;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
DFA after update: <start> -a-> <1>, all other transitions unchanged.

<!--
############
assert dfa_stale.transition('<start>', 'a')[1] == '<1>'
assert dfa_stale.transition('<start>', 'b')[1] == '<start>'
assert dfa_stale.transition('<1>', 'a')[1] == '<start>'
assert dfa_stale.transition('<1>', 'b')[1] == '<1>'
__canvas__(dfa_to_dot(dfa_stale, 'DFA_after_update'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
assert dfa_stale.transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)[1] == &#x27;&lt;1&gt;&#x27;
assert dfa_stale.transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;)[1] == &#x27;&lt;start&gt;&#x27;
assert dfa_stale.transition(&#x27;&lt;1&gt;&#x27;, &#x27;a&#x27;)[1] == &#x27;&lt;start&gt;&#x27;
assert dfa_stale.transition(&#x27;&lt;1&gt;&#x27;, &#x27;b&#x27;)[1] == &#x27;&lt;1&gt;&#x27;
__canvas__(dfa_to_dot(dfa_stale, &#x27;DFA_after_update&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Discriminator Finalization

The discriminator $$ ce[i+1:] $$ is correct but may be longer than
necessary. A shorter suffix of $$ ce[i+1:] $$ may distinguish the two
states just as well. Keeping discriminators short keeps the DT shallow,
which reduces sifting costs in all future iterations.

A suffix $$ d $$ *distinguishes* two states when appending it to their
access sequences gives different membership answers:
`oracle(reach(old_state) + d) != oracle(reach(new_state) + d)`.
This means the two states respond differently to $$ d $$, so they cannot
be the same state in the target.

Starting from the full suffix $$ ce[i+1:] $$, we try progressively shorter
suffixes (by advancing the start index). We keep shrinking as long as the
shorter suffix still distinguishes the two states. The moment a candidate
fails to distinguish them, no further shortening can help, so we stop and
return the shortest distinguishing suffix found so far.

<!--
############
def finalize_discriminator(old_state, new_state, ce_suffix, st, oracle):
    best = ce_suffix
    for j in range(len(ce_suffix) - 1, 0, -1):
        candidate = ce_suffix[j:]
        old_answer = oracle.is_member(st.reach(old_state) + candidate)
        new_answer = oracle.is_member(st.reach(new_state) + candidate)
        if old_answer != new_answer:
            best = candidate
        else:
            break   # shorter suffixes won't work either
    return best

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def finalize_discriminator(old_state, new_state, ce_suffix, st, oracle):
    best = ce_suffix
    for j in range(len(ce_suffix) - 1, 0, -1):
        candidate = ce_suffix[j:]
        old_answer = oracle.is_member(st.reach(old_state) + candidate)
        new_answer = oracle.is_member(st.reach(new_state) + candidate)
        if old_answer != new_answer:
            best = candidate
        else:
            break   # shorter suffixes won&#x27;t work either
    return best
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test discriminator finalization.

<!--
############
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
st = StateTable()
st.add_state('<1>', '<start>', 'a')
# '' is already minimal
d = finalize_discriminator('<start>', '<1>', '', st, oracle)
assert d == ''
# 'ba' can be shortened to 'a'
# reach('<start>') + 'a' = 'a'   -> False (odd)
# reach('<1>') + 'a' = 'aa'  -> True  (even), so 'a' distinguishes them
d = finalize_discriminator('<start>', '<1>', 'ba', st, oracle)
assert d == 'a'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
st = StateTable()
st.add_state(&#x27;&lt;1&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
# &#x27;&#x27; is already minimal
d = finalize_discriminator(&#x27;&lt;start&gt;&#x27;, &#x27;&lt;1&gt;&#x27;, &#x27;&#x27;, st, oracle)
assert d == &#x27;&#x27;
# &#x27;ba&#x27; can be shortened to &#x27;a&#x27;
# reach(&#x27;&lt;start&gt;&#x27;) + &#x27;a&#x27; = &#x27;a&#x27;   -&gt; False (odd)
# reach(&#x27;&lt;1&gt;&#x27;) + &#x27;a&#x27; = &#x27;aa&#x27;  -&gt; True  (even), so &#x27;a&#x27; distinguishes them
d = finalize_discriminator(&#x27;&lt;start&gt;&#x27;, &#x27;&lt;1&gt;&#x27;, &#x27;ba&#x27;, st, oracle)
assert d == &#x27;a&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Finding the Split Point

`find_split_point` records the hypothesis states visited while reading
$$ ce $$, then binary-searches for the first position where
$$ reach(q_i) \cdot ce[i:] $$ disagrees with the target answer on $$ ce $$.
That position $$ i $$ is where the hypothesis first takes a wrong transition.
The search costs $$ O(\log|ce|) $$ membership queries.

The function returns both the split index and the full states list, since
`decompose` needs the states list for the prefix transformation.

<!--
############
def find_split_point(dfa, st, oracle, ce):
    # walk the hypothesis along ce
    states = [dfa.start_symbol]
    for char in ce:
        rule = dfa.transition(states[-1], char)
        states.append(rule[1])

    target_answer = oracle.is_member(ce)

    # binary search: find first index where reach(q_i)+ce[i:] disagrees with target
    lo, hi = 0, len(ce)
    while lo < hi:
        mid = (lo + hi) // 2
        q_mid = states[mid]
        if oracle.is_member(st.reach(q_mid) + ce[mid:]) == target_answer:
            lo = mid + 1   # mid agrees: split is to the right
        else:
            hi = mid       # mid disagrees: split is here or to the left

    # lo-1 is the last agreeing position; lo is the first disagreeing position
    return lo - 1, states

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_split_point(dfa, st, oracle, ce):
    # walk the hypothesis along ce
    states = [dfa.start_symbol]
    for char in ce:
        rule = dfa.transition(states[-1], char)
        states.append(rule[1])

    target_answer = oracle.is_member(ce)

    # binary search: find first index where reach(q_i)+ce[i:] disagrees with target
    lo, hi = 0, len(ce)
    while lo &lt; hi:
        mid = (lo + hi) // 2
        q_mid = states[mid]
        if oracle.is_member(st.reach(q_mid) + ce[mid:]) == target_answer:
            lo = mid + 1   # mid agrees: split is to the right
        else:
            hi = mid       # mid disagrees: split is here or to the left

    # lo-1 is the last agreeing position; lo is the first disagreeing position
    return lo - 1, states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test find_split_point on a simple case.

<!--
############
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
# hypothesis: single state <start>, everything loops back, <start> is accepting
dfa_sp = DFA()
dfa_sp.set_accepting('<start>')
dfa_sp.add_transition('<start>', 'a', '<start>')
dfa_sp.add_transition('<start>', 'b', '<start>')
st_sp = StateTable()
# counterexample 'a': hypothesis accepts, target rejects
i, states = find_split_point(dfa_sp, st_sp, oracle, 'a')
assert i == 0, i
# counterexample 'aab': split should be at position 0 (first divergence)
i2, _ = find_split_point(dfa_sp, st_sp, oracle, 'aab')
assert i2 == 0, i2

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
# hypothesis: single state &lt;start&gt;, everything loops back, &lt;start&gt; is accepting
dfa_sp = DFA()
dfa_sp.set_accepting(&#x27;&lt;start&gt;&#x27;)
dfa_sp.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa_sp.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;start&gt;&#x27;)
st_sp = StateTable()
# counterexample &#x27;a&#x27;: hypothesis accepts, target rejects
i, states = find_split_point(dfa_sp, st_sp, oracle, &#x27;a&#x27;)
assert i == 0, i
# counterexample &#x27;aab&#x27;: split should be at position 0 (first divergence)
i2, _ = find_split_point(dfa_sp, st_sp, oracle, &#x27;aab&#x27;)
assert i2 == 0, i2
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Putting Decomposition Together

With `find_split_point`, `prefix_transformation`, `finalize_discriminator`,
and `DTNode.split` all in place, `decompose` is a straightforward
four-step sequence. One counterexample yields exactly one new state and
one new discriminator.

Note: `decompose` uses hypothesis transitions only to find the split point.
The actual split uses $$ reach(q_i) $$ from the state table, which is always
correct with respect to the target, so `decompose` is correct even if the
hypothesis is partially stale.

<!--
############
def decompose(dfa, dt, st, oracle, ce, leaf_index):
    # step 1: find split point by binary search (TTT: findSplitPoint)
    i, states = find_split_point(dfa, st, oracle, ce)
    lo = i + 1

    # step 2: prefix transformation (TTT: prefixTransformation)
    transformed, q_i = prefix_transformation(states, st, ce, i)

    # step 3: sift to find which leaf the transformed prefix lands on,
    # then create the new state (TTT: sift + newState)
    old_leaf = sift(dt, transformed, oracle)
    old_state = old_leaf.state
    new_state = dfa.new_state()
    st.add_state(new_state, q_i, ce[i])

    # step 4: finalize discriminator and split the leaf (TTT: splitLeaf)
    new_discriminator = finalize_discriminator(
            old_state, new_state, ce[lo:], st, oracle)
    split_id = old_leaf.node_id
    old_leaf.split(new_discriminator, new_state, oracle, st)

    return new_state, split_id

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def decompose(dfa, dt, st, oracle, ce, leaf_index):
    # step 1: find split point by binary search (TTT: findSplitPoint)
    i, states = find_split_point(dfa, st, oracle, ce)
    lo = i + 1

    # step 2: prefix transformation (TTT: prefixTransformation)
    transformed, q_i = prefix_transformation(states, st, ce, i)

    # step 3: sift to find which leaf the transformed prefix lands on,
    # then create the new state (TTT: sift + newState)
    old_leaf = sift(dt, transformed, oracle)
    old_state = old_leaf.state
    new_state = dfa.new_state()
    st.add_state(new_state, q_i, ce[i])

    # step 4: finalize discriminator and split the leaf (TTT: splitLeaf)
    new_discriminator = finalize_discriminator(
            old_state, new_state, ce[lo:], st, oracle)
    split_id = old_leaf.node_id
    old_leaf.split(new_discriminator, new_state, oracle, st)

    return new_state, split_id
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We test decompose.

<!--
############
# preparation.
oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
alphabet = ['a', 'b']

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
# preparation.
oracle = MockOracle(lambda w: w.count(&#x27;a&#x27;) % 2 == 0)
alphabet = [&#x27;a&#x27;, &#x27;b&#x27;]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
test 1: single symbol counterexample 'a'

<!--
############
dt = DTNode('<start>')
st = StateTable()
leaf_index = {}
dfa = DFA()
dfa.set_accepting('<start>')
dfa.add_transition('<start>', 'a', '<start>')
dfa.add_transition('<start>', 'b', '<start>')
new_state, _ = decompose(dfa, dt, st, oracle, 'a', leaf_index)
assert not dt.is_leaf()
assert st.reach(new_state) == 'a'
assert sift(dt, '', oracle).state == '<start>'
assert sift(dt, 'a', oracle).state == new_state
__canvas__(dt_to_dot(dt, 'DT_decompose1'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dt = DTNode(&#x27;&lt;start&gt;&#x27;)
st = StateTable()
leaf_index = {}
dfa = DFA()
dfa.set_accepting(&#x27;&lt;start&gt;&#x27;)
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;start&gt;&#x27;)
new_state, _ = decompose(dfa, dt, st, oracle, &#x27;a&#x27;, leaf_index)
assert not dt.is_leaf()
assert st.reach(new_state) == &#x27;a&#x27;
assert sift(dt, &#x27;&#x27;, oracle).state == &#x27;&lt;start&gt;&#x27;
assert sift(dt, &#x27;a&#x27;, oracle).state == new_state
__canvas__(dt_to_dot(dt, &#x27;DT_decompose1&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
test 2: longer counterexample 'aab'; binary search finds split at position 0,
so the new state still gets access sequence 'a' and discriminator is 'b'.

<!--
############
dt = DTNode('<start>')
st = StateTable()
leaf_index = {}
dfa = DFA()
dfa.set_accepting('<start>')
dfa.add_transition('<start>', 'a', '<start>')
dfa.add_transition('<start>', 'b', '<start>')
new_state, _ = decompose(dfa, dt, st, oracle, 'aab', leaf_index)
assert not dt.is_leaf()
assert st.reach(new_state) == 'a'
__canvas__(dt_to_dot(dt, 'DT_decompose2'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dt = DTNode(&#x27;&lt;start&gt;&#x27;)
st = StateTable()
leaf_index = {}
dfa = DFA()
dfa.set_accepting(&#x27;&lt;start&gt;&#x27;)
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;start&gt;&#x27;)
new_state, _ = decompose(dfa, dt, st, oracle, &#x27;aab&#x27;, leaf_index)
assert not dt.is_leaf()
assert st.reach(new_state) == &#x27;a&#x27;
__canvas__(dt_to_dot(dt, &#x27;DT_decompose2&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
test 3: two states, counterexample 'aa' reveals a third state.
The DT gains a second level; the new state gets access sequence 'aa'.

<!--
############
st2 = StateTable()
st2.add_state('<odd>', '<start>', 'a')
dt2 = DTNode('<start>')
dt2.split('', '<odd>', oracle, st2)
dfa2 = DFA()
dfa2.ensure_state('<odd>')
dfa2.set_accepting('<start>')
dfa2.add_transition('<start>', 'a', '<odd>')
dfa2.add_transition('<start>', 'b', '<start>')
dfa2.add_transition('<odd>', 'a', '<odd>')   # wrong
dfa2.add_transition('<odd>', 'b', '<odd>')
new_state2, _ = decompose(dfa2, dt2, st2, oracle, 'aa', {})
assert st2.reach(new_state2) == 'aa'
__canvas__(dt_to_dot(dt2, 'DT_decompose3'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
st2 = StateTable()
st2.add_state(&#x27;&lt;odd&gt;&#x27;, &#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;)
dt2 = DTNode(&#x27;&lt;start&gt;&#x27;)
dt2.split(&#x27;&#x27;, &#x27;&lt;odd&gt;&#x27;, oracle, st2)
dfa2 = DFA()
dfa2.ensure_state(&#x27;&lt;odd&gt;&#x27;)
dfa2.set_accepting(&#x27;&lt;start&gt;&#x27;)
dfa2.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;a&#x27;, &#x27;&lt;odd&gt;&#x27;)
dfa2.add_transition(&#x27;&lt;start&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;start&gt;&#x27;)
dfa2.add_transition(&#x27;&lt;odd&gt;&#x27;, &#x27;a&#x27;, &#x27;&lt;odd&gt;&#x27;)   # wrong
dfa2.add_transition(&#x27;&lt;odd&gt;&#x27;, &#x27;b&#x27;, &#x27;&lt;odd&gt;&#x27;)
new_state2, _ = decompose(dfa2, dt2, st2, oracle, &#x27;aa&#x27;, {})
assert st2.reach(new_state2) == &#x27;aa&#x27;
__canvas__(dt_to_dot(dt2, &#x27;DT_decompose3&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Worklist Growth in `close_transitions`

We now trace the full `(a|b)*ba` learning run to show how state names
emerge from the algorithm and how the worklist grows during
`close_transitions`. No states are pre-declared; they are created by
`dfa.new_state()` inside `decompose` as each counterexample is processed.

**Step 1.** Single-leaf DT, only `<start>` in the state table.
`close_transitions` sifts `'' + 'a'` and `'' + 'b'`. Both land on the
only leaf `<start>`, so no new states are discovered.

<!--
############
oracle_ba = MockOracle(lambda w: w.endswith('ba'))
dt_cl = DTNode('<start>')
st_cl = StateTable()
dfa_cl = DFA()
leaf_index_cl = {}
build_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, ['a', 'b'], leaf_index_cl)
print('step 1 states:', st_cl.states())
__canvas__(dt_to_dot(dt_cl, 'cl_dt_step1'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
oracle_ba = MockOracle(lambda w: w.endswith(&#x27;ba&#x27;))
dt_cl = DTNode(&#x27;&lt;start&gt;&#x27;)
st_cl = StateTable()
dfa_cl = DFA()
leaf_index_cl = {}
build_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, [&#x27;a&#x27;, &#x27;b&#x27;], leaf_index_cl)
print(&#x27;step 1 states:&#x27;, st_cl.states())
__canvas__(dt_to_dot(dt_cl, &#x27;cl_dt_step1&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
DFA after step 1: everything loops back to `<start>`.

<!--
############
__canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step1'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(dfa_to_dot(dfa_cl, &#x27;cl_dfa_step1&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Step 2.** Counterexample `'ba'`: the hypothesis accepts it as `<start>`
(which is accepting) but shouldn't, since `<start>` should only accept `''`.
`decompose` creates a fresh state (call it `s1`) and splits the DT leaf
with discriminator `'a'`. `update_hypothesis` re-sifts stale transitions;
sifting `'' + 'b'` now lands on `s1`, which is new, so it is appended to the
worklist and its transitions are closed immediately. Worklist grows from
`['<start>']` to `['<start>', s1]`.

<!--
############
new_s1, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, 'ba', leaf_index_cl)
update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, ['a', 'b'],
                  leaf_index_cl, split_id, new_s1)
print('step 2 states:', st_cl.states(), '  new state:', new_s1)
__canvas__(dt_to_dot(dt_cl, 'cl_dt_step2'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
new_s1, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, &#x27;ba&#x27;, leaf_index_cl)
update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, [&#x27;a&#x27;, &#x27;b&#x27;],
                  leaf_index_cl, split_id, new_s1)
print(&#x27;step 2 states:&#x27;, st_cl.states(), &#x27;  new state:&#x27;, new_s1)
__canvas__(dt_to_dot(dt_cl, &#x27;cl_dt_step2&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
DFA after step 2.

<!--
############
__canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step2'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(dfa_to_dot(dfa_cl, &#x27;cl_dfa_step2&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Step 3.** Counterexample `'ba'` again; now the hypothesis rejects it
because `s1 -a-> <start>` is wrong (should reach an accepting state).
`decompose` creates `s2` and splits the `<start>` leaf with discriminator
$$ \varepsilon $$. `update_hypothesis` re-sifts; sifting `reach(s1) + 'a'` = `'ba'`
lands on `s2`, which is new and appended. Worklist grows to include `s2`.
Here is that sift path, the one that grows the worklist:

<!--
############
new_s2, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, 'ba', leaf_index_cl)
_tr = DTTracer(dt_cl)
sift(_tr, 'ba', oracle_ba)
__canvas__(dt_to_dot(dt_cl, 'cl_worklist_grow', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
new_s2, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, &#x27;ba&#x27;, leaf_index_cl)
_tr = DTTracer(dt_cl)
sift(_tr, &#x27;ba&#x27;, oracle_ba)
__canvas__(dt_to_dot(dt_cl, &#x27;cl_worklist_grow&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
And sifting `reach(s1) + 'b'` = `'bb'` lands on `<start>`, which is already known; no append.

<!--
############
_tr = DTTracer(dt_cl)
sift(_tr, 'bb', oracle_ba)
__canvas__(dt_to_dot(dt_cl, 'cl_worklist_no_grow', tracer=_tr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
_tr = DTTracer(dt_cl)
sift(_tr, &#x27;bb&#x27;, oracle_ba)
__canvas__(dt_to_dot(dt_cl, &#x27;cl_worklist_no_grow&#x27;, tracer=_tr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
After `update_hypothesis` finishes, all three states are wired up.

<!--
############
update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, ['a', 'b'],
                  leaf_index_cl, split_id, new_s2)
print('step 3 states:', st_cl.states(), '  new state:', new_s2)
__canvas__(dt_to_dot(dt_cl, 'cl_dt_step3'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, [&#x27;a&#x27;, &#x27;b&#x27;],
                  leaf_index_cl, split_id, new_s2)
print(&#x27;step 3 states:&#x27;, st_cl.states(), &#x27;  new state:&#x27;, new_s2)
__canvas__(dt_to_dot(dt_cl, &#x27;cl_dt_step3&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Final DFA, with states named by the algorithm as they were discovered.

<!--
############
__canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step3'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(dfa_to_dot(dfa_cl, &#x27;cl_dfa_step3&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Non-Redundancy

The central claim of the TTT is that it never makes a membership
query whose answer could have been derived from earlier queries. To see
what this means concretely: in L*, if the counterexample is `ba`, the
algorithm adds both `a` and `ba` as new suffix columns and re-queries every
existing state against both. If `a` was already a column, that work is
wasted. TTT avoids this by extracting exactly one new suffix per
counterexample and routing all future classification through the DT. This
holds at every level:

* **Sifting is non-redundant.** Every query is $$ w \cdot d $$ where $$ d $$
  was placed in the DT by a previous split that proved it necessary.
* **Splitting is non-redundant.** Each split adds exactly one discriminator,
  proven necessary by the counterexample.
* **Closing is non-redundant.** Each transition is sifted exactly once per
  iteration. Newly discovered states come with their DT position already
  established by the sift that found them, so no extra queries are needed.

This contrasts with L*, where adding all $$ k $$ suffixes of a counterexample
forces re-querying every existing row against every new column, most of
which add no new information.
## A Note on the Equivalence Oracle

TTT assumes the equivalence oracle is *exact*: if it says the hypothesis is
wrong, it returns a string the hypothesis genuinely misclassifies. The
`Teacher` we use is a PAC oracle: it samples a finite set of strings and
declares equivalence if none expose a mistake. This is an approximation.

In principle, a false counterexample from a PAC oracle could cause TTT to
create a redundant state: one that could have been merged with an existing
state without changing the language the DFA accepts. The DFA would still be
correct, just slightly larger than necessary. Neither TTT nor L* guarantees
a globally minimal DFA under a PAC oracle: both can acquire spurious states
or columns from false counterexamples, and neither performs a global
minimization pass afterward. In practice this is a minor concern: the PAC
oracle is unlikely to produce false counterexamples with reasonable
parameters, and the language accepted by the DFA is unaffected either way.
## The Main Loop

The main loop orchestrates everything:

1. Build the initial hypothesis: one state, all transitions open.
2. Ask the equivalence oracle. If it says yes, we are done.
3. If not, decompose the counterexample to find one new state and one new
   discriminator.
4. Incrementally update the hypothesis: re-sift only the stale transitions.
5. Repeat from step 2.

The loop runs exactly $$ n - 1 $$ times where $$ n $$ is the number of
states in the minimal DFA, one counterexample per new state discovered.

<!--
############
def ttt(oracle, alphabet):
    dt = DTNode('<start>')
    st = StateTable()
    leaf_index = {}

    # initial hypothesis: one state, no transitions yet
    dfa = DFA()
    build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)

    while True:
        # equivalence query via PAC oracle from Teacher
        is_eq, ce = oracle.is_equivalent(dfa.grammar, dfa.start_symbol)
        if is_eq: break   # done: hypothesis matches target

        # one counterexample yields one new state and one new discriminator
        new_state, split_id = decompose(dfa, dt, st, oracle, ce, leaf_index)

        # incremental update: re-sift only the stale transitions
        update_hypothesis(dfa, dt, st, oracle, alphabet,
                          leaf_index, split_id, new_state)

    return dfa

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def ttt(oracle, alphabet):
    dt = DTNode(&#x27;&lt;start&gt;&#x27;)
    st = StateTable()
    leaf_index = {}

    # initial hypothesis: one state, no transitions yet
    dfa = DFA()
    build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)

    while True:
        # equivalence query via PAC oracle from Teacher
        is_eq, ce = oracle.is_equivalent(dfa.grammar, dfa.start_symbol)
        if is_eq: break   # done: hypothesis matches target

        # one counterexample yields one new state and one new discriminator
        new_state, split_id = decompose(dfa, dt, st, oracle, ce, leaf_index)

        # incremental update: re-sift only the stale transitions
        update_hypothesis(dfa, dt, st, oracle, alphabet,
                          leaf_index, split_id, new_state)

    return dfa
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Examples

We test TTT on three targets of increasing complexity.

target 1: strings over {a, b} with an even number of a's

<!--
############
teacher = lstar.Teacher('(b*ab*a)*b*') # even a
result = ttt(teacher, ['a', 'b'])
assert result.accepts('')
assert result.accepts('aa')
assert result.accepts('bb')
assert not result.accepts('a')
assert not result.accepts('aaa')
print("test 1 passed: even a's")
__canvas__(dfa_to_dot(result, 'DFA_even_a_ttt'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
teacher = lstar.Teacher(&#x27;(b*ab*a)*b*&#x27;) # even a
result = ttt(teacher, [&#x27;a&#x27;, &#x27;b&#x27;])
assert result.accepts(&#x27;&#x27;)
assert result.accepts(&#x27;aa&#x27;)
assert result.accepts(&#x27;bb&#x27;)
assert not result.accepts(&#x27;a&#x27;)
assert not result.accepts(&#x27;aaa&#x27;)
print(&quot;test 1 passed: even a&#x27;s&quot;)
__canvas__(dfa_to_dot(result, &#x27;DFA_even_a_ttt&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
target 2: strings over {a, b} that end in 'b'

<!--
############
teacher = lstar.Teacher('(a|b)*b')
result = ttt(teacher, ['a', 'b'])
assert result.accepts('b')
assert result.accepts('ab')
assert result.accepts('aab')
assert not result.accepts('')
assert not result.accepts('a')
assert not result.accepts('ba')
print('test 2 passed: ends in b')
__canvas__(dfa_to_dot(result, 'DFA_ends_b_ttt'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
teacher = lstar.Teacher(&#x27;(a|b)*b&#x27;)
result = ttt(teacher, [&#x27;a&#x27;, &#x27;b&#x27;])
assert result.accepts(&#x27;b&#x27;)
assert result.accepts(&#x27;ab&#x27;)
assert result.accepts(&#x27;aab&#x27;)
assert not result.accepts(&#x27;&#x27;)
assert not result.accepts(&#x27;a&#x27;)
assert not result.accepts(&#x27;ba&#x27;)
print(&#x27;test 2 passed: ends in b&#x27;)
__canvas__(dfa_to_dot(result, &#x27;DFA_ends_b_ttt&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
target 3: binary strings whose value is divisible by 3

This target has no convenient regex, so we write a custom teacher.
It is a good stress test: the minimal DFA has exactly 3 states (one per
remainder mod 3), the alphabet is {0, 1}, and transitions are determined
by how reading a bit updates the current value modulo 3. This exercises
TTT on a target where the states correspond to arithmetic structure rather
than string patterns.

<!--
############
class DivBy3Teacher(lstar.Teacher):
    def __init__(self, delta=0.5, epsilon=0.5):
        super().__init__('0', delta=delta, epsilon=epsilon)

    def is_member(self, w):
        if not w: return True
        return int(w, 2) % 3 == 0

    def is_equivalent(self, grammar, start):
        self.equivalence_query_counter += 1
        num_calls = math.ceil(1.0/self.epsilon *
                  (math.log(1.0/self.delta +
                              self.equivalence_query_counter * math.log(2))))
        dfa = DFA(start_symbol=start)
        dfa.grammar = grammar
        for _ in range(num_calls):
            # sample a random binary string up to length 10
            length = random.randint(0, 10)
            w = ''.join(random.choice(['0', '1']) for _ in range(length))
            if bool(self.is_member(w)) != bool(dfa.accepts(w)):
                return False, w
        return True, None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DivBy3Teacher(lstar.Teacher):
    def __init__(self, delta=0.5, epsilon=0.5):
        super().__init__(&#x27;0&#x27;, delta=delta, epsilon=epsilon)

    def is_member(self, w):
        if not w: return True
        return int(w, 2) % 3 == 0

    def is_equivalent(self, grammar, start):
        self.equivalence_query_counter += 1
        num_calls = math.ceil(1.0/self.epsilon *
                  (math.log(1.0/self.delta +
                              self.equivalence_query_counter * math.log(2))))
        dfa = DFA(start_symbol=start)
        dfa.grammar = grammar
        for _ in range(num_calls):
            # sample a random binary string up to length 10
            length = random.randint(0, 10)
            w = &#x27;&#x27;.join(random.choice([&#x27;0&#x27;, &#x27;1&#x27;]) for _ in range(length))
            if bool(self.is_member(w)) != bool(dfa.accepts(w)):
                return False, w
        return True, None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Test this.

<!--
############
result = ttt(DivBy3Teacher(delta=0.2, epsilon=0.2), ['0', '1'])
assert result.accepts('')
assert result.accepts('0')
assert result.accepts('11')    # 3 in binary
assert result.accepts('110')   # 6 in binary
assert not result.accepts('1')
assert not result.accepts('10') # 2 in binary
print('test 3 passed: divisible by 3 in binary')
__canvas__(dfa_to_dot(result, 'DFA_divby3_ttt'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
result = ttt(DivBy3Teacher(delta=0.2, epsilon=0.2), [&#x27;0&#x27;, &#x27;1&#x27;])
assert result.accepts(&#x27;&#x27;)
assert result.accepts(&#x27;0&#x27;)
assert result.accepts(&#x27;11&#x27;)    # 3 in binary
assert result.accepts(&#x27;110&#x27;)   # 6 in binary
assert not result.accepts(&#x27;1&#x27;)
assert not result.accepts(&#x27;10&#x27;) # 2 in binary
print(&#x27;test 3 passed: divisible by 3 in binary&#x27;)
__canvas__(dfa_to_dot(result, &#x27;DFA_divby3_ttt&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Evaluating Model Accuracy

We measure precision and recall by cross-fuzzing the target grammar and the
inferred grammar. Precision is the fraction of strings generated by the
inferred DFA that the target accepts. Recall is the fraction of strings
generated by the target that the inferred DFA accepts.

The inferred DFA may contain a dead/sink state: a non-accepting state with
no exit, representing strings the target permanently rejects. Such a state
causes `LimitFuzzer` to loop, because the grammar has no finite derivation
from it. We remove dead states before fuzzing using `fuzzer.compute_cost`,
which assigns each nonterminal the minimum number of steps needed to reach
a terminal string. Any nonterminal with infinite cost is a dead state;
we remove it and all rules that reference it.

<!--
############
def remove_infinite_loops(g, start):
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
def remove_infinite_loops(g, start):
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
We define a `match` helper that wraps the Earley parser in a boolean check.

<!--
############
def match(p, start, text):
    try: p.recognize_on(text, start)
    except SyntaxError: return False
    return True

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(p, start, text):
    try: p.recognize_on(text, start)
    except SyntaxError: return False
    return True
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing
Each pair is (regex, alphabet). Cases cover a range of DFA shapes:
two-segment and three-segment chains, prefix-anchored, suffix-anchored,
substring-containment, exact-alternation, and disjoint finite sets.

<!--
############
cases = [
    ('(b*ab*a)*b*',       ['a', 'b']),
    ('(a|b)*b',           ['a', 'b']),
    ('a*b*',              ['a', 'b']),
    ('ab*',               ['a', 'b']),   # must start with a, then any b's
    ('(a|b)*ba',          ['a', 'b']),   # must end with ba
    ('(ab)*',             ['a', 'b']),   # strictly alternating
    ('a*b*c*',            ['a', 'b', 'c']),
    ('a(a|b)*a',          ['a', 'b']),   # must start and end with a
    ('(aab)*',            ['a', 'b']),   # period-3 repetition
    ('(a|b)*aba(a|b)*',   ['a', 'b']),   # must contain substring aba
    ('(a|b)*abb',         ['a', 'b']),   # must end with abb
    ('aa|bb',             ['a', 'b']),   # exactly aa or exactly bb
    ('(ab|ba)*',          ['a', 'b']),   # even-length, alternating pairs
    ('(a|b)*ab(a|b)*',    ['a', 'b']),   # must contain substring ab
]
for e, alphabet in cases:
    teacher = lstar.Teacher(e, delta=0.2, epsilon=0.2)
    t_g, t_s = teacher.g, teacher.s
    t_f = fuzzer.LimitFuzzer(t_g)

    result = ttt(teacher, alphabet)
    i_g, i_s = remove_infinite_loops(result.grammar, result.start_symbol)
    i_p = earleyparser.EarleyParser(i_g)
    i_f = fuzzer.LimitFuzzer(i_g)

    lgi = lgi_lgb = lgb = lgb_lgi = 0
    for _ in range(100):
        val = i_f.iter_fuzz(key=i_s, max_depth=100)
        if match(teacher.parser, t_s, val): lgi_lgb += 1
        lgi += 1

        val = t_f.iter_fuzz(key=t_s, max_depth=100)
        if match(i_p, i_s, val): lgb_lgi += 1
        lgb += 1

    precision = lgi_lgb / lgi if lgi else 1.0
    recall    = lgb_lgi / lgb if lgb else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    print('expr: %-20s  precision: %.2f  recall: %.2f  F1: %.2f'
          % (e, precision, recall, f1))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cases = [
    (&#x27;(b*ab*a)*b*&#x27;,       [&#x27;a&#x27;, &#x27;b&#x27;]),
    (&#x27;(a|b)*b&#x27;,           [&#x27;a&#x27;, &#x27;b&#x27;]),
    (&#x27;a*b*&#x27;,              [&#x27;a&#x27;, &#x27;b&#x27;]),
    (&#x27;ab*&#x27;,               [&#x27;a&#x27;, &#x27;b&#x27;]),   # must start with a, then any b&#x27;s
    (&#x27;(a|b)*ba&#x27;,          [&#x27;a&#x27;, &#x27;b&#x27;]),   # must end with ba
    (&#x27;(ab)*&#x27;,             [&#x27;a&#x27;, &#x27;b&#x27;]),   # strictly alternating
    (&#x27;a*b*c*&#x27;,            [&#x27;a&#x27;, &#x27;b&#x27;, &#x27;c&#x27;]),
    (&#x27;a(a|b)*a&#x27;,          [&#x27;a&#x27;, &#x27;b&#x27;]),   # must start and end with a
    (&#x27;(aab)*&#x27;,            [&#x27;a&#x27;, &#x27;b&#x27;]),   # period-3 repetition
    (&#x27;(a|b)*aba(a|b)*&#x27;,   [&#x27;a&#x27;, &#x27;b&#x27;]),   # must contain substring aba
    (&#x27;(a|b)*abb&#x27;,         [&#x27;a&#x27;, &#x27;b&#x27;]),   # must end with abb
    (&#x27;aa|bb&#x27;,             [&#x27;a&#x27;, &#x27;b&#x27;]),   # exactly aa or exactly bb
    (&#x27;(ab|ba)*&#x27;,          [&#x27;a&#x27;, &#x27;b&#x27;]),   # even-length, alternating pairs
    (&#x27;(a|b)*ab(a|b)*&#x27;,    [&#x27;a&#x27;, &#x27;b&#x27;]),   # must contain substring ab
]
for e, alphabet in cases:
    teacher = lstar.Teacher(e, delta=0.2, epsilon=0.2)
    t_g, t_s = teacher.g, teacher.s
    t_f = fuzzer.LimitFuzzer(t_g)

    result = ttt(teacher, alphabet)
    i_g, i_s = remove_infinite_loops(result.grammar, result.start_symbol)
    i_p = earleyparser.EarleyParser(i_g)
    i_f = fuzzer.LimitFuzzer(i_g)

    lgi = lgi_lgb = lgb = lgb_lgi = 0
    for _ in range(100):
        val = i_f.iter_fuzz(key=i_s, max_depth=100)
        if match(teacher.parser, t_s, val): lgi_lgb += 1
        lgi += 1

        val = t_f.iter_fuzz(key=t_s, max_depth=100)
        if match(i_p, i_s, val): lgb_lgi += 1
        lgb += 1

    precision = lgi_lgb / lgi if lgi else 1.0
    recall    = lgb_lgi / lgb if lgb else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    print(&#x27;expr: %-20s  precision: %.2f  recall: %.2f  F1: %.2f&#x27;
          % (e, precision, recall, f1))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Comparison with L*

| | L* | TTT |
|---|---|---|
| Data structure | Flat observation table | Discrimination tree (Kearns-Vazirani) |
| Counterexample processing | Add all $$ k $$ suffixes | Binary search for 1 suffix (Rivest-Schapire) |
| Prefix transformation | No | Yes (minimal access sequences, TTT) |
| Discriminator finalization | No | Yes (shallow DT, TTT) |
| Redundant queries | Many | None: the DT structure prevents re-querying known distinctions |
| Closedness check | Explicit global scan | Lazy, local (open transitions) |
| Consistency check | Explicit global scan | Structurally prevented by DT |

The DT depth is bounded by $$ n $$ (one split per state), so sifting never
becomes expensive. This makes TTT the preferred algorithm when membership
queries are costly, as is typical when learning protocol implementations
or library APIs through testing.

## References

[^kearns1994]: Michael Kearns and Umesh Vazirani. An Introduction to Computational Learning Theory. MIT Press, 1994. pp. 44-58.

[^rivest1993]: Ronald L. Rivest and Robert E. Schapire. Inference of Finite Automata Using Homing Sequences. Information and Computation, 103(2):51-73, 1993.

[^isberner2014]: Malte Isberner, Falk Howar, and Bernhard Steffen. The TTT Algorithm: A Redundancy-Free Approach to Active Automata Learning. RV 2014.

[^isbernerphd]: Malte Isberner. Foundations of Active Automata Learning: An Algorithmic Perspective. PhD Dissertation, TU Dortmund, 2015. http://129.217.131.68:8080/bitstream/2003/34282/1/Dissertation.pdf

[^isbernerce]: Malte Isberner and Bernhard Steffen. An Abstract Framework for Counterexample Analysis in Active Automata Learning. ICGI 2014. http://proceedings.mlr.press/v34/isberner14a.pdf

[^howar2012]: Falk Howar, Bernhard Steffen, and Maik Merten. Internalization of Observation Packs. ICFEM 2012.

[^learnlib]: Falk Howar and Bernhard Steffen. Active Automata Learning in Practice. Springer, 2022.

[^adt]: Markus Frohme. Active Automata Learning with Adaptive Distinguishing Sequences. Master Thesis, TU Dortmund, 2015. https://arxiv.org/abs/1902.01139

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2026-06-09-ttt-grammar-inference.py).


