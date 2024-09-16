---
published: true
title: A Shift-Reduce LR0 Parser
layout: post
comments: true
tags: parsing gll
categories: post
---
TLDR; This tutorial is a complete implementation of a simple shift-reduce
LR(0) Parser in Python. The Python interpreter is embedded so that you can
work through the implementation steps.
An LR parser is a bottom-up parser. The *L* stands for scanning the input
left-to-right, and the *R* stands for constructing a rightmost derivation.
This contrasts with LL parsers which are again left-to-right but construct
the leftmost derivation.

We are implementing LR(0) which means that the decisions on which state to
transition to are determined exclusively on the current parsed prefix. There
is no lookahead.

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

#### Prerequisites
 
As before, we start with the prerequisite imports.

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
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl">pydot-1.4.1-py2.py3-none-any.whl</a></li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
Since this notebook serves both as a web notebook as well as a script
that can be run on the command line, we redefine canvas if it is not
defined already. The `__canvas__` function is defined externally when it is
used as a web notebook.

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
Importing the fuzzer for a few simple utilities. 

<!--
############
import simplefuzzer as fuzzer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We use the `display_tree()` method in earley parser for displaying trees.

<!--
############
import earleyparser as ep

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import earleyparser as ep
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We use the random choice to extract derivation trees from the parse forest.

<!--
############
import random

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Pydot is needed for drawing

<!--
############
import pydot

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pydot
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar
style. That is, given below is a simple grammar for nested parenthesis.

```
<P> := '(' <P> ')'
     | '(' <D> ')'
<D> := 0 | 1
```
Equivalently,

<!--
############
paren_g = {
        '<P>' : [['(', '<P>', ')'],
                 ['(', '<D>', ')']],
        '<D>' : [['0'],['1']]
}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
paren_g = {
        &#x27;&lt;P&gt;&#x27; : [[&#x27;(&#x27;, &#x27;&lt;P&gt;&#x27;, &#x27;)&#x27;],
                 [&#x27;(&#x27;, &#x27;&lt;D&gt;&#x27;, &#x27;)&#x27;]],
        &#x27;&lt;D&gt;&#x27; : [[&#x27;0&#x27;],[&#x27;1&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is another gramamr. Here, we extend the grammar with the augmented
stard sybmol `S``

```
 <S`> := <S>
 <S>  := 'a' <A> 'c'
       | 'b' '<A>' 'd' 'd'
 <A>  := 'b'
```
Again, equivalently, we have

<!--
############
S_g = {'<S`>': [['<S>', '$']],
        '<S>': [ ['a', '<A>', 'c'],
                 ['b', '<A>', 'd', 'd']],
        '<A>': [ ['b']]}
S_s = '<S`>'
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
S_g = {&#x27;&lt;S`&gt;&#x27;: [[&#x27;&lt;S&gt;&#x27;, &#x27;$&#x27;]],
        &#x27;&lt;S&gt;&#x27;: [ [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;],
                 [&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;d&#x27;, &#x27;d&#x27;]],
        &#x27;&lt;A&gt;&#x27;: [ [&#x27;b&#x27;]]}
S_s = &#x27;&lt;S`&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can list the grammar production rules as follows:

<!--
############
i = 1
for k in S_g:
    for r in S_g[k]:
        print(i, k, r)
        i+=1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
i = 1
for k in S_g:
    for r in S_g[k]:
        print(i, k, r)
        i+=1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The main difference between an LR parser and an LL parser is that an LL
parser uses the current nonterminal and the next symbol to determine the
production rule to apply. In contrast, the LR parser uses the current
viable prefix and the next symbol to determine the next action to take.

The viable-prefix is the string prefix that has been currently recognized.
This recognition is accomplished by the LR automata, which we describe next.

But before that, let us start slow. If we are going for a naive translation
of the grammar into an automata, this is what we could do. That is, we start
with the starting production rule
`S' -> S`. Since we are starting to parse, let us indicate the parse point
also, which would be before `S` is parsed. That is, `S' -> .S`. The period
represents the current parse point. If we somehow parsed `S` now, then we
would transition to an accept state. This is represented by `S' -> S.`.
However, since the transition is a nonterminal, it can't happen by reading
the corresponding symbol `S` from the input stream. It has to happen through
another path. Hence, we indicate this by a dashed line. Next, when the parse
is at `S' -> .S`, any of the expansions of `S` can now be parsed. So, we add
each expansion of `S` as $$\epsilon$$ transition away. These are
`S := . a A c` and `S := . b A d d`. Continuing in this fashion, we have: 

<!--
############
__canvas__('''
digraph NFA {
 rankdir=TB;
 node [shape = rectangle];
 start [shape = point];

 // States
 S0 [label = "S' := . S"];
 SF [label = "S' := S .", shape = doublecircle];
 S1 [label = "S := . a A c"];
 S2 [label = "S := . b A d d"];
 S3 [label = "S := a . A c"];
 S4 [label = "S := a A . c"];
 S5 [label = "S := a A c ."];
 S6 [label = "S := b . A d d"];
 S7 [label = "S := b A . d d"];
 S8 [label = "S := b A d . d"];
 S9 [label = "S := b A d d ."];
 A1 [label = "A := . b"];
 A2 [label = "A := b ."];

 // Regular transitions
 start -> S0;
 S0 -> S1 [label = "ε"];
 S0 -> S2 [label = "ε"];
 S1 -> S3 [label = "a"];
 S3 -> A1 [label = "ε"];
 S4 -> S5 [label = "c"];
 S2 -> S6 [label = "b"];
 S6 -> A1 [label = "ε"];
 S7 -> S8 [label = "d"];
 S8 -> S9 [label = "d"];
 A1 -> A2 [label = "b"];

 // Nonterminal transitions (dashed)
 edge [style = dashed];
 S0 -> SF [label = "S"];
 S3 -> S4 [label = "A"];
 S6 -> S7 [label = "A"];
}''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
digraph NFA {
 rankdir=TB;
 node [shape = rectangle];
 start [shape = point];

 // States
 S0 [label = &quot;S&#x27; := . S&quot;];
 SF [label = &quot;S&#x27; := S .&quot;, shape = doublecircle];
 S1 [label = &quot;S := . a A c&quot;];
 S2 [label = &quot;S := . b A d d&quot;];
 S3 [label = &quot;S := a . A c&quot;];
 S4 [label = &quot;S := a A . c&quot;];
 S5 [label = &quot;S := a A c .&quot;];
 S6 [label = &quot;S := b . A d d&quot;];
 S7 [label = &quot;S := b A . d d&quot;];
 S8 [label = &quot;S := b A d . d&quot;];
 S9 [label = &quot;S := b A d d .&quot;];
 A1 [label = &quot;A := . b&quot;];
 A2 [label = &quot;A := b .&quot;];

 // Regular transitions
 start -&gt; S0;
 S0 -&gt; S1 [label = &quot;ε&quot;];
 S0 -&gt; S2 [label = &quot;ε&quot;];
 S1 -&gt; S3 [label = &quot;a&quot;];
 S3 -&gt; A1 [label = &quot;ε&quot;];
 S4 -&gt; S5 [label = &quot;c&quot;];
 S2 -&gt; S6 [label = &quot;b&quot;];
 S6 -&gt; A1 [label = &quot;ε&quot;];
 S7 -&gt; S8 [label = &quot;d&quot;];
 S8 -&gt; S9 [label = &quot;d&quot;];
 A1 -&gt; A2 [label = &quot;b&quot;];

 // Nonterminal transitions (dashed)
 edge [style = dashed];
 S0 -&gt; SF [label = &quot;S&quot;];
 S3 -&gt; S4 [label = &quot;A&quot;];
 S6 -&gt; S7 [label = &quot;A&quot;];
}&#x27;&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Notice that this NFA is not complete. For example, what happens when `A := b .`
is complete? Then, the parse need to transition to a state that has just
completed `A`. For example, `S := a A . c` or `S := b A . d d`. Here is how
it looks like.

<!--
############
__canvas__('''
digraph NFA {
  rankdir=TB;
  node [shape = rectangle];
  start [shape = point];

  // States
  S0 [label = "S' := . S"];
  SF [label = "S' := S .", shape = doublecircle];
  S1 [label = "S := . a A c"];
  S2 [label = "S := . b A d d"];
  S3 [label = "S := a . A c"];
  S4 [label = "S := a A . c"];
  S5 [label = "S := a A c ."];
  S6 [label = "S := b . A d d"];
  S7 [label = "S := b A . d d"];
  S8 [label = "S := b A d . d"];
  S9 [label = "S := b A d d ."];
  A1 [label = "A := . b"];
  A2 [label = "A := b ."];

  // Regular transitions
  start -> S0;
  S0 -> S1 [label = "ε"];
  S0 -> S2 [label = "ε"];
  S1 -> S3 [label = "a"];
  S3 -> A1 [label = "ε"];
  S4 -> S5 [label = "c"];
  S2 -> S6 [label = "b"];
  S6 -> A1 [label = "ε"];
  S7 -> S8 [label = "d"];
  S8 -> S9 [label = "d"];
  A1 -> A2 [label = "b"];

  // Nonterminal transitions (dashed)
  edge [style = dashed];
  S0 -> SF [label = "S"];
  S3 -> S4 [label = "A"];
  S6 -> S7 [label = "A"];

  // Red arrows for completed rules
  edge [color = red, constraint = false, style = solid];
  A2 -> S4 [label = "completion"];
  A2 -> S7 [label = "completion"];
  S5 -> SF [label = "completion"];
  S9 -> SF [label = "completion"];
 }''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
digraph NFA {
  rankdir=TB;
  node [shape = rectangle];
  start [shape = point];

  // States
  S0 [label = &quot;S&#x27; := . S&quot;];
  SF [label = &quot;S&#x27; := S .&quot;, shape = doublecircle];
  S1 [label = &quot;S := . a A c&quot;];
  S2 [label = &quot;S := . b A d d&quot;];
  S3 [label = &quot;S := a . A c&quot;];
  S4 [label = &quot;S := a A . c&quot;];
  S5 [label = &quot;S := a A c .&quot;];
  S6 [label = &quot;S := b . A d d&quot;];
  S7 [label = &quot;S := b A . d d&quot;];
  S8 [label = &quot;S := b A d . d&quot;];
  S9 [label = &quot;S := b A d d .&quot;];
  A1 [label = &quot;A := . b&quot;];
  A2 [label = &quot;A := b .&quot;];

  // Regular transitions
  start -&gt; S0;
  S0 -&gt; S1 [label = &quot;ε&quot;];
  S0 -&gt; S2 [label = &quot;ε&quot;];
  S1 -&gt; S3 [label = &quot;a&quot;];
  S3 -&gt; A1 [label = &quot;ε&quot;];
  S4 -&gt; S5 [label = &quot;c&quot;];
  S2 -&gt; S6 [label = &quot;b&quot;];
  S6 -&gt; A1 [label = &quot;ε&quot;];
  S7 -&gt; S8 [label = &quot;d&quot;];
  S8 -&gt; S9 [label = &quot;d&quot;];
  A1 -&gt; A2 [label = &quot;b&quot;];

  // Nonterminal transitions (dashed)
  edge [style = dashed];
  S0 -&gt; SF [label = &quot;S&quot;];
  S3 -&gt; S4 [label = &quot;A&quot;];
  S6 -&gt; S7 [label = &quot;A&quot;];

  // Red arrows for completed rules
  edge [color = red, constraint = false, style = solid];
  A2 -&gt; S4 [label = &quot;completion&quot;];
  A2 -&gt; S7 [label = &quot;completion&quot;];
  S5 -&gt; SF [label = &quot;completion&quot;];
  S9 -&gt; SF [label = &quot;completion&quot;];
 }&#x27;&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the dashed arrows represent non-terminal transitions that are
actually completed through other paths. The red arrows represent reductions.
You will notice that there can be multiple reductions from the same
item. At this point, this NFA over-approximates our grammar.
The right reduction needs to chosen based on the prefix so far, and we
will see how to do this later.

While this is reasonable, it is not very useful. For one, it is an NFA,
over-approximating the grammar, and secondly, there can be multiple possible
paths for a given prefix.  Hence, it is not very optimal.
Let us next see how to generate a DFA instead.

## LR Automata
 An LR automata is composed of multiple states, and each state represents a set
of items that indicate the parsing progress. The states are connected together
using transitions which are composed of the terminal and nonterminal symbols
in the grammar.

To construct the LR automata, one starts with the initial state containing the
augmented start symbol (if necessary), and we apply closure to expand the
context. For the closure, we simply merge all epsilon transitions to current
item.

### Closure
A closure to represents all possible parse paths at a given
point. The idea is to look at the current parse progress; Identify any
nonterminals that need to be expanded next, and add the production rules of that
nonterminal to the current item, with parse point (dot) at the beginning.

For example, given the first state, where `*` represent the parse progress
 
```
<S`> := * <S>
```
Applying closure, we expand `<S>` further.
 
```
<S`> := * <S>
<S>  := * a <A> c
<S>  := * b <A> d d
```
No more nonterminals to expand. Hence, this is the closure of the first state.

Consider what happens when we apply a transition of `a` to this state.

```
<S> := a * A c
```
Now, we apply closure
```
<S> := a * A c
<A> := * b
```

This gives us the following graph with each closure, and the transitions indicated. Note that
the nonterminal transitions are dashed.

<!--
############
__canvas__('''
digraph ParsingAutomaton {
rankdir=TB;

// Node definitions with labels
node [shape=rectangle];

// State definitions with reduction instructions
0 [label="I0:\nS' → • S\nS → • a A c\nS → • b A d d"];
1 [label="I1:\nS' → S •\n[Accept]"];
2 [label="I2:\nS → a • A c\nA → • b"];
3 [label="I3:\nS → b • A d d\nA → • b"];
4 [label="I4:\nS → a A • c"];
5 [label="I5:\nA → b •"];
6 [label="I6:\nS → b A • d d"];
7 [label="I7:\nS → a A c •"];
8 [label="I8:\nS → b A d • d"];
9 [label="I9:\nS → b A d d •"];

// Edge definitions with labels
0 -> 2 [label="a"];
0 -> 3 [label="b"];
0 -> 1 [label="S", style=dashed];

2 -> 5 [label="b"];
2 -> 4 [label="A", style=dashed];

3 -> 5 [label="b"];
3 -> 6 [label="A", style=dashed];

4 -> 7 [label="c"];

5 -> 4 [label="A", color=red]; // GOTO after reduction in state 5
5 -> 6 [label="A", color=red]; // GOTO after reduction in state 5

6 -> 8 [label="d"];

7 -> 1 [label="S", color=red]; // GOTO after reduction in state 7

8 -> 9 [label="d"];

9 -> 1 [label="S", color=red]; // GOTO after reduction in state 9
}''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
digraph ParsingAutomaton {
rankdir=TB;

// Node definitions with labels
node [shape=rectangle];

// State definitions with reduction instructions
0 [label=&quot;I0:\nS&#x27; → • S\nS → • a A c\nS → • b A d d&quot;];
1 [label=&quot;I1:\nS&#x27; → S •\n[Accept]&quot;];
2 [label=&quot;I2:\nS → a • A c\nA → • b&quot;];
3 [label=&quot;I3:\nS → b • A d d\nA → • b&quot;];
4 [label=&quot;I4:\nS → a A • c&quot;];
5 [label=&quot;I5:\nA → b •&quot;];
6 [label=&quot;I6:\nS → b A • d d&quot;];
7 [label=&quot;I7:\nS → a A c •&quot;];
8 [label=&quot;I8:\nS → b A d • d&quot;];
9 [label=&quot;I9:\nS → b A d d •&quot;];

// Edge definitions with labels
0 -&gt; 2 [label=&quot;a&quot;];
0 -&gt; 3 [label=&quot;b&quot;];
0 -&gt; 1 [label=&quot;S&quot;, style=dashed];

2 -&gt; 5 [label=&quot;b&quot;];
2 -&gt; 4 [label=&quot;A&quot;, style=dashed];

3 -&gt; 5 [label=&quot;b&quot;];
3 -&gt; 6 [label=&quot;A&quot;, style=dashed];

4 -&gt; 7 [label=&quot;c&quot;];

5 -&gt; 4 [label=&quot;A&quot;, color=red]; // GOTO after reduction in state 5
5 -&gt; 6 [label=&quot;A&quot;, color=red]; // GOTO after reduction in state 5

6 -&gt; 8 [label=&quot;d&quot;];

7 -&gt; 1 [label=&quot;S&quot;, color=red]; // GOTO after reduction in state 7

8 -&gt; 9 [label=&quot;d&quot;];

9 -&gt; 1 [label=&quot;S&quot;, color=red]; // GOTO after reduction in state 9
}&#x27;&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is the basic automaton. However, you may notice that there are two types
of nodes in this diagram. The first one represents partial parses which
contain the dot at a position other than the end, and the second one
represents a complete parse of a rule with the dot at the end. You will also
note that the complete parse nodes seem to have red outgoing arrows, and
at least in one, multiple red outgoing arrows. That is, it is not a true
DFA. The next state to transition to is actually chosen based on the path
the input string took through the DFA with the help of a stack.
Let us now represent these states step by step.
State 0
This is the initial state. It transitions into State 2 or State 3 based
on the input symbol. Note that we save the current state in the stack
before transitioning to the next state after consuming one token.

<!--
############
def state_0(stack, input_string):
    rule = ['S`', ['S'], 0]
    stack.append(0)
    symbol = input_string[0]
    if symbol == 'a': return state_2(stack, input_string[1:])
    elif symbol == 'b': return state_3(stack, input_string[1:])
    else: raise Exception("Expected 'a' or 'b'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_0(stack, input_string):
    rule = [&#x27;S`&#x27;, [&#x27;S&#x27;], 0]
    stack.append(0)
    symbol = input_string[0]
    if symbol == &#x27;a&#x27;: return state_2(stack, input_string[1:])
    elif symbol == &#x27;b&#x27;: return state_3(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;a&#x27; or &#x27;b&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 1
This is the acceptor state.

<!--
############
def state_1(stack, input_string):
    rule = ['S`', ['S'], 1]
    stack.append(1)
    symbol = input_string[0]
    if symbol == '$': print("Input accepted.")
    else: raise Exception("Expected end of input")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_1(stack, input_string):
    rule = [&#x27;S`&#x27;, [&#x27;S&#x27;], 1]
    stack.append(1)
    symbol = input_string[0]
    if symbol == &#x27;$&#x27;: print(&quot;Input accepted.&quot;)
    else: raise Exception(&quot;Expected end of input&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 2 which is the production rule `S -> a . A c` just after consuming `a`.
We need `b` to transition to State 5 which represents a production rule of A.

<!--
############
def state_2(stack, input_string):
    rule = ['S', ['a', 'A', 'c'], 1]
    stack.append(2)
    symbol = input_string[0]
    if symbol == 'b': return state_5(stack, input_string[1:])
    else: raise Exception("Expected 'b'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_2(stack, input_string):
    rule = [&#x27;S&#x27;, [&#x27;a&#x27;, &#x27;A&#x27;, &#x27;c&#x27;], 1]
    stack.append(2)
    symbol = input_string[0]
    if symbol == &#x27;b&#x27;: return state_5(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;b&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 3 which is the production rule `S -> b . A d d` just after consuming `b`.

<!--
############
def state_3(stack, input_string):
    rule = ['S', ['b', 'A', 'd', 'd'], 1]
    stack.append(3)
    symbol = input_string[0]
    if symbol == 'b': return state_5(stack, input_string[1:])
    else: raise Exception("Expected 'b'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_3(stack, input_string):
    rule = [&#x27;S&#x27;, [&#x27;b&#x27;, &#x27;A&#x27;, &#x27;d&#x27;, &#x27;d&#x27;], 1]
    stack.append(3)
    symbol = input_string[0]
    if symbol == &#x27;b&#x27;: return state_5(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;b&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 4 which is the production rule `S -> a A.  c` just after consuming `a`.

<!--
############
def state_4(stack, input_string):
    rule = ['S', ['a', 'A', 'c'], 2]
    stack.append(4)
    symbol = input_string[0]
    if symbol == 'c': return state_7(stack, input_string[1:])
    else: raise Exception("Expected 'c'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_4(stack, input_string):
    rule = [&#x27;S&#x27;, [&#x27;a&#x27;, &#x27;A&#x27;, &#x27;c&#x27;], 2]
    stack.append(4)
    symbol = input_string[0]
    if symbol == &#x27;c&#x27;: return state_7(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;c&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 5 which is the production rule `A -> b .`. That is, it has completed
parsing A, and now need to decide which state to transition to. This is
decided by what was in the stack before. We simply pop off as many symbols
as there are tokens in the RHS of the production rule, and check the
remaining top symbol.

<!--
############
def state_5(stack, input_string):
    stack.append(5)
    rule = ['A', ['b']]
    for _ in range(len(rule[1])): stack.pop()  # Pop state 'b', 5
    if stack[-1] == 2: return state_4(stack, input_string)
    elif stack[-1] == 3: return state_6(stack, input_string)
    else: raise Exception(position, "Invalid state during reduction by A → b")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_5(stack, input_string):
    stack.append(5)
    rule = [&#x27;A&#x27;, [&#x27;b&#x27;]]
    for _ in range(len(rule[1])): stack.pop()  # Pop state &#x27;b&#x27;, 5
    if stack[-1] == 2: return state_4(stack, input_string)
    elif stack[-1] == 3: return state_6(stack, input_string)
    else: raise Exception(position, &quot;Invalid state during reduction by A → b&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 6 `S -> b A . d d`

<!--
############
def state_6(stack, input_string):
    stack.append(6)
    rule = ['S', ['b', 'A', 'd', 'd'], 2]
    symbol = input_string[0]
    if symbol == 'd': return state_8(stack, input_string[1:])
    else: raise Exception("Expected 'd'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_6(stack, input_string):
    stack.append(6)
    rule = [&#x27;S&#x27;, [&#x27;b&#x27;, &#x27;A&#x27;, &#x27;d&#x27;, &#x27;d&#x27;], 2]
    symbol = input_string[0]
    if symbol == &#x27;d&#x27;: return state_8(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;d&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 7 is a reduction rule `S -> a A c .`

<!--
############
def state_7(stack, input_string):
    stack.append(7)
    rule = ['S', ['a', 'A', 'c'], 3]
    for _ in range(len(rule[1])): stack.pop() # Pop 'c', 7; 'A', 4; 'a', 2

    if stack[-1] == 0: return state_1(stack, input_string)
    else: raise Exception("Invalid state during reduction by S → a A c")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_7(stack, input_string):
    stack.append(7)
    rule = [&#x27;S&#x27;, [&#x27;a&#x27;, &#x27;A&#x27;, &#x27;c&#x27;], 3]
    for _ in range(len(rule[1])): stack.pop() # Pop &#x27;c&#x27;, 7; &#x27;A&#x27;, 4; &#x27;a&#x27;, 2

    if stack[-1] == 0: return state_1(stack, input_string)
    else: raise Exception(&quot;Invalid state during reduction by S → a A c&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 8 `S -> b A d . d`

<!--
############
def state_8(stack, input_string):
    rule = ['S', ['b', 'A', 'd', 'd'], 3]
    stack.append(8)
    symbol = input_string[0]
    if symbol == 'd': return state_9(stack, input_string[1:])
    else: raise Exception("Expected 'd'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_8(stack, input_string):
    rule = [&#x27;S&#x27;, [&#x27;b&#x27;, &#x27;A&#x27;, &#x27;d&#x27;, &#x27;d&#x27;], 3]
    stack.append(8)
    symbol = input_string[0]
    if symbol == &#x27;d&#x27;: return state_9(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;d&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
State 9 is a reduction rule `S -> b A d d .`

<!--
############
def state_9(stack, input_string):
    stack.append(9)
    rule = ['S', ['b', 'A', 'd', 'd']]
    for _ in range(len(rule[1])): stack.pop() # Pop 'd', 9; 'd', 8; 'A', 6; 'b', 3
    if stack[-1] == 0: return state_1(stack, input_string)
    else: return Exception("Invalid state during reduction by S → b A d d")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_9(stack, input_string):
    stack.append(9)
    rule = [&#x27;S&#x27;, [&#x27;b&#x27;, &#x27;A&#x27;, &#x27;d&#x27;, &#x27;d&#x27;]]
    for _ in range(len(rule[1])): stack.pop() # Pop &#x27;d&#x27;, 9; &#x27;d&#x27;, 8; &#x27;A&#x27;, 6; &#x27;b&#x27;, 3
    if stack[-1] == 0: return state_1(stack, input_string)
    else: return Exception(&quot;Invalid state during reduction by S → b A d d&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us now verify if our parser works.

<!--
############
test_strings = [("abc", True), ("bbdd", True), ("bdd", False), ("baddd", False)]

for test_string, res in test_strings:
    print(f"Parsing: {test_string}")
    input_string = list(test_string) + ['$']
    try:
        val = state_0([], input_string)
    except Exception as e:
        if res: print(e)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
test_strings = [(&quot;abc&quot;, True), (&quot;bbdd&quot;, True), (&quot;bdd&quot;, False), (&quot;baddd&quot;, False)]

for test_string, res in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    input_string = list(test_string) + [&#x27;$&#x27;]
    try:
        val = state_0([], input_string)
    except Exception as e:
        if res: print(e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Building the NFA
Now, let us try and build these dynamically.
We first build an NFA of the grammar. For that, we begin by adding a new
state `<>` to grammar.
First, we add a start extension to the grammar.

<!--
############
def add_start_state(g, start, new_start='<>'):
    new_g = dict(g)
    new_g[new_start] = [[start]]
    return new_g, new_start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def add_start_state(g, start, new_start=&#x27;&lt;&gt;&#x27;):
    new_g = dict(g)
    new_g[new_start] = [[start]]
    return new_g, new_start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Two sample grammars.

<!--
############
g1 = {
    '<S>': [
          ['<A>', '<B>'],
          ['<C>']],
   '<A>': [
        ['a']],
   '<B>': [
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

sample_grammar = {
    '<start>': [['<A>','<B>']],
    '<A>': [['a', '<B>', 'c'], ['a', '<A>']],
    '<B>': [['b', '<C>'], ['<D>']],
    '<C>': [['c']],
    '<D>': [['d']]
}

sample_start = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
    &#x27;&lt;S&gt;&#x27;: [
          [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;],
          [&#x27;&lt;C&gt;&#x27;]],
   &#x27;&lt;A&gt;&#x27;: [
        [&#x27;a&#x27;]],
   &#x27;&lt;B&gt;&#x27;: [
        [&#x27;b&#x27;]],
   &#x27;&lt;C&gt;&#x27;: [
        [&#x27;c&#x27;]],
}
g1_start = &#x27;&lt;S&gt;&#x27;

sample_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;,&#x27;&lt;B&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;c&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;, &#x27;&lt;C&gt;&#x27;], [&#x27;&lt;D&gt;&#x27;]],
    &#x27;&lt;C&gt;&#x27;: [[&#x27;c&#x27;]],
    &#x27;&lt;D&gt;&#x27;: [[&#x27;d&#x27;]]
}

sample_start = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Test

<!--
############
g1a, g1a_start = add_start_state(g1, g1_start)
for k in g1a:
    print(k)
    print('  |',g1a[k])
assert g1a_start in g1a
assert g1a[g1a_start][0][0] in g1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1a, g1a_start = add_start_state(g1, g1_start)
for k in g1a:
    print(k)
    print(&#x27;  |&#x27;,g1a[k])
assert g1a_start in g1a
assert g1a[g1a_start][0][0] in g1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For building an NFA, all we need is to start with start item, and then
recursively identify the transitions. First, we define the state
data structure. We define a unique id.
We also need the symbols in a given grammar.

<!--
############
def symbols(g):
    terminals = {}
    for k in g:
        for rule in g[k]:
            for t in rule:
                if fuzzer.is_nonterminal(t): continue
                terminals[t] = True
    return list(sorted(terminals.keys())), list(sorted(g.keys()))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def symbols(g):
    terminals = {}
    for k in g:
        for rule in g[k]:
            for t in rule:
                if fuzzer.is_nonterminal(t): continue
                terminals[t] = True
    return list(sorted(terminals.keys())), list(sorted(g.keys()))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## State
We first define our state data structure.
A state for an NFA is simply a production rule and a parse position.

<!--
############
class State:
    def __init__(self, name, expr, dot, sid):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid

    def finished(self):
        return self.dot >= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot < len(self.expr) else None

    def __repr__(self):
        return "(%s : %d)" % (str(self), self.sid)

    def show_dot(self, sym, rule, pos, dotstr='|', extents=''):
        extents = str(extents)
        return sym + '::= ' + ' '.join([
               str(p)
               for p in [*rule[0:pos], dotstr, *rule[pos:]]]) + extents

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

    def def_key(self):
        return self.name

    def main_item(self):
        return (self.name, list(self.expr))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class State:
    def __init__(self, name, expr, dot, sid):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid

    def finished(self):
        return self.dot &gt;= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot &lt; len(self.expr) else None

    def __repr__(self):
        return &quot;(%s : %d)&quot; % (str(self), self.sid)

    def show_dot(self, sym, rule, pos, dotstr=&#x27;|&#x27;, extents=&#x27;&#x27;):
        extents = str(extents)
        return sym + &#x27;::= &#x27; + &#x27; &#x27;.join([
               str(p)
               for p in [*rule[0:pos], dotstr, *rule[pos:]]]) + extents

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

    def def_key(self):
        return self.name

    def main_item(self):
        return (self.name, list(self.expr))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It can be tested this way

<!--
############
s = State('<S`>', ('<S>'), 0, 0)
print(s.at_dot())
print(str(s))
print(s.finished())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = State(&#x27;&lt;S`&gt;&#x27;, (&#x27;&lt;S&gt;&#x27;), 0, 0)
print(s.at_dot())
print(str(s))
print(s.finished())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we build an NFA out of a given grammar. An NFA is composed of
different states connected together by transitions.

<!--
############
class NFA:
    def __init__(self, g, start):
        self.states = {}
        self.g = g
        self.productions, self.production_rules = self.get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.sid_counter = 0

    def get_key(self, kr):
        return "%s -> %s" %kr

    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    def get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.g:
            for r in self.g[k]:
                production_rules["r:%d" % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules

    # create starting states for the given key
    def create_start(self, s):
        rules = self.g[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.g[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.states[state.sid] = state
        return self.my_states[(name, texpr, pos)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA:
    def __init__(self, g, start):
        self.states = {}
        self.g = g
        self.productions, self.production_rules = self.get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.sid_counter = 0

    def get_key(self, kr):
        return &quot;%s -&gt; %s&quot; %kr

    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    def get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.g:
            for r in self.g[k]:
                production_rules[&quot;r:%d&quot; % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules

    # create starting states for the given key
    def create_start(self, s):
        rules = self.g[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.g[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.states[state.sid] = state
        return self.my_states[(name, texpr, pos)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_nfa = NFA(S_g, S_s)
st = my_nfa.create_start(S_s)
assert str(st[0]) == '<S`>::= | <S> $'
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == '<S>::= | <A> <B>'
assert str(st[1]) == '<S>::= | <C>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
st = my_nfa.create_start(S_s)
assert str(st[0]) == &#x27;&lt;S`&gt;::= | &lt;S&gt; $&#x27;
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;
assert str(st[1]) == &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## find_transitions
Next, for processing a state, we need a few more tools. First,we need
to be able to advance a state.

<!--
############
class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        new_state = self.advance(state)
        return new_state

    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        new_state = self.advance(state)
        return new_state

    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Epsilon transitions. Given a state K -> t.V a
we get all rules of nonterminal V, and add with
starting 0

<!--
############
class NFA(NFA):
    def epsilon_transitions(self, state):
        key = state.at_dot()
        # key should not be none at this point.
        assert key is not None
        new_states = []
        for rule in self.g[key]:
            new_state = self.create_state(key, rule, 0)
            new_states.append(new_state)
        return new_states

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def epsilon_transitions(self, state):
        key = state.at_dot()
        # key should not be none at this point.
        assert key is not None
        new_states = []
        for rule in self.g[key]:
            new_state = self.create_state(key, rule, 0)
            new_states.append(new_state)
        return new_states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
processing the state itself for its transitions. First, if the
dot is before a symbol, then we add the transition to the advanced
state with that symbol as the transition. Next, if the key at
the dot is a nonterminal, then add all expansions of that nonterminal
as epsilon transfers.

<!--
############
class NFA(NFA):
    def find_transitions(self, state):
        key = state.at_dot()
        if key is None: return [] # dot after last.
        new_states = []

        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        new_state = self.symbol_transition(state)
        # add it to the states returned
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            # each rule of the nonterminal forms an epsilon transition
            # with the dot at the `0` position
            ns = self.epsilon_transitions(state)
            for s in ns:
                new_states.append(('', s))
        else:
            # no definition for terminal symbols
            pass
        return new_states

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def find_transitions(self, state):
        key = state.at_dot()
        if key is None: return [] # dot after last.
        new_states = []

        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        new_state = self.symbol_transition(state)
        # add it to the states returned
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            # each rule of the nonterminal forms an epsilon transition
            # with the dot at the `0` position
            ns = self.epsilon_transitions(state)
            for s in ns:
                new_states.append((&#x27;&#x27;, s))
        else:
            # no definition for terminal symbols
            pass
        return new_states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_nfa = NFA(S_g, S_s)
st = my_nfa.create_start(S_s)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == "('<S>', (<S`>::= <S> | $ : 1))"
assert str(new_st[1]) == "('', (<S>::= | a <A> c : 2))"
assert str(new_st[2]) == "('', (<S>::= | b <A> d d : 3))"


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
st = my_nfa.create_start(S_s)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == &quot;(&#x27;&lt;S&gt;&#x27;, (&lt;S`&gt;::= &lt;S&gt; | $ : 1))&quot;
assert str(new_st[1]) == &quot;(&#x27;&#x27;, (&lt;S&gt;::= | a &lt;A&gt; c : 2))&quot;
assert str(new_st[2]) == &quot;(&#x27;&#x27;, (&lt;S&gt;::= | b &lt;A&gt; d d : 3))&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, a utility method. Given a key, we want to get all items
that contains the parsing of this key.

<!--
############
class NFA(NFA):
    def get_all_rules_with_dot_after_key(self, key):
        states = []
        for k in self.g:
            for rule in self.g[k]:
                l_rule = len(rule)
                for i,t in enumerate(rule):
                    if i >= l_rule: continue
                    if t == key:
                        states.append(self.create_state(k, rule, i+1))
        return states

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def get_all_rules_with_dot_after_key(self, key):
        states = []
        for k in self.g:
            for rule in self.g[k]:
                l_rule = len(rule)
                for i,t in enumerate(rule):
                    if i &gt;= l_rule: continue
                    if t == key:
                        states.append(self.create_state(k, rule, i+1))
        return states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_nfa = NFA(S_g, S_s)
lst = my_nfa.get_all_rules_with_dot_after_key('<A>')
assert str(lst) == '[(<S>::= a <A> | c : 0), (<S>::= b <A> | d d : 1)]'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
lst = my_nfa.get_all_rules_with_dot_after_key(&#x27;&lt;A&gt;&#x27;)
assert str(lst) == &#x27;[(&lt;S&gt;::= a &lt;A&gt; | c : 0), (&lt;S&gt;::= b &lt;A&gt; | d d : 1)]&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we can build the NFA.

<!--
############
class NFA(NFA):
    def build_nfa(self):
        t_symbols, nt_symbols = symbols(self.g)
        start_item = self.create_start(self.start)[0]
        queue = [('$', start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                # if the key is a nonterminal then it is a goto
                if key == '':
                    self.add_child(state, key, s, 'shift')
                elif fuzzer.is_nonterminal(key):
                    self.add_child(state, key, s, 'goto')
                else:
                    self.add_child(state, key, s, 'shift')

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                N = self.productions[self.get_key((state.name, list(state.expr)))]
                # follow_set = follow(item.name, self.g)  # Compute FOLLOW set
                for k in self.terminals:
                    self.add_reduction(state, k, N, 'reduce')

                # Also, (only) for the graph, collect epsilon transmition to all
                # rules that are after the given nonterminal at the head.
                key = state.def_key()
                list_of_return_states = self.get_all_rules_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(state, '', s, 'to') # reduce to
                    # these are already processed. So we do not add to queue

            queue.extend(new_states)
        # now build the nfa table.
        state_count = len(self.states.keys())
        nfa_table = [[] for _ in range(state_count)]
        for i in range(0, state_count):
            nfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in nfa_table[parent]: nfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in nfa_table[parent][key]:
                nfa_table[parent][key].append(v)

        return nfa_table

    def add_reduction(self, p, key, c, notes):
        self.children.append((p.sid, key, c, notes))

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def build_nfa(self):
        t_symbols, nt_symbols = symbols(self.g)
        start_item = self.create_start(self.start)[0]
        queue = [(&#x27;$&#x27;, start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                # if the key is a nonterminal then it is a goto
                if key == &#x27;&#x27;:
                    self.add_child(state, key, s, &#x27;shift&#x27;)
                elif fuzzer.is_nonterminal(key):
                    self.add_child(state, key, s, &#x27;goto&#x27;)
                else:
                    self.add_child(state, key, s, &#x27;shift&#x27;)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                N = self.productions[self.get_key((state.name, list(state.expr)))]
                # follow_set = follow(item.name, self.g)  # Compute FOLLOW set
                for k in self.terminals:
                    self.add_reduction(state, k, N, &#x27;reduce&#x27;)

                # Also, (only) for the graph, collect epsilon transmition to all
                # rules that are after the given nonterminal at the head.
                key = state.def_key()
                list_of_return_states = self.get_all_rules_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(state, &#x27;&#x27;, s, &#x27;to&#x27;) # reduce to
                    # these are already processed. So we do not add to queue

            queue.extend(new_states)
        # now build the nfa table.
        state_count = len(self.states.keys())
        nfa_table = [[] for _ in range(state_count)]
        for i in range(0, state_count):
            nfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [&#x27;&#x27;])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == &#x27;reduce&#x27;: prefix = &#x27;r:&#x27; # N not a state.
            elif notes == &#x27;shift&#x27;: prefix = &#x27;s&#x27;
            elif notes == &#x27;goto&#x27;: prefix = &#x27;g&#x27;
            elif notes == &#x27;to&#x27;: prefix = &#x27;t&#x27;
            if key not in nfa_table[parent]: nfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in nfa_table[parent][key]:
                nfa_table[parent][key].append(v)

        return nfa_table

    def add_reduction(self, p, key, c, notes):
        self.children.append((p.sid, key, c, notes))

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test the build_nfa

<!--
############
my_nfa = NFA(S_g, S_s)
table = my_nfa.build_nfa()
rowh = table[0]
print('>', '\t','\t'.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(table):
    print(i, '\t','\t'.join([str(row[c]) for c in row.keys()]))
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
table = my_nfa.build_nfa()
rowh = table[0]
print(&#x27;&gt;&#x27;, &#x27;\t&#x27;,&#x27;\t&#x27;.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(table):
    print(i, &#x27;\t&#x27;,&#x27;\t&#x27;.join([str(row[c]) for c in row.keys()]))
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Show graph

<!--
############
def to_graph(nfa_tbl):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(nfa_tbl):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = 'rectangle'# rectangle, oval, diamond
        label = str(i)
        # if the state contains 'accept', then it is an accept state.
        for k in state:
            if  'accept' in state[k]: shape='doublecircle'
        G.add_node(pydot.Node(label, label=label, shape=shape, peripheries='1'))
            #peripheries= '2' if i == root else '1')
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = 'black'
            style='solid'
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = ''
                if state_name == 'accept':
                    continue
                elif state_name[0] == 'g':
                    color='blue'
                    transition_prefix = '(g) '
                    style='dashed'
                elif state_name[0] == 'r':
                    # reduction is not a state transition.
                    # color='red'
                    # transition_prefix = '(r) '
                    continue
                elif state_name[0] == 't':
                    color='green'
                    transition_prefix = '(t) '
                else:
                    assert state_name[0] == 's'
                    transition_prefix = '(s) '
                G.add_edge(pydot.Edge(label,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_graph(nfa_tbl):
    G = pydot.Dot(&quot;my_graph&quot;, graph_type=&quot;digraph&quot;)
    for i, state in enumerate(nfa_tbl):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = &#x27;rectangle&#x27;# rectangle, oval, diamond
        label = str(i)
        # if the state contains &#x27;accept&#x27;, then it is an accept state.
        for k in state:
            if  &#x27;accept&#x27; in state[k]: shape=&#x27;doublecircle&#x27;
        G.add_node(pydot.Node(label, label=label, shape=shape, peripheries=&#x27;1&#x27;))
            #peripheries= &#x27;2&#x27; if i == root else &#x27;1&#x27;)
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = &#x27;black&#x27;
            style=&#x27;solid&#x27;
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = &#x27;&#x27;
                if state_name == &#x27;accept&#x27;:
                    continue
                elif state_name[0] == &#x27;g&#x27;:
                    color=&#x27;blue&#x27;
                    transition_prefix = &#x27;(g) &#x27;
                    style=&#x27;dashed&#x27;
                elif state_name[0] == &#x27;r&#x27;:
                    # reduction is not a state transition.
                    # color=&#x27;red&#x27;
                    # transition_prefix = &#x27;(r) &#x27;
                    continue
                elif state_name[0] == &#x27;t&#x27;:
                    color=&#x27;green&#x27;
                    transition_prefix = &#x27;(t) &#x27;
                else:
                    assert state_name[0] == &#x27;s&#x27;
                    transition_prefix = &#x27;(s) &#x27;
                G.add_edge(pydot.Edge(label,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test our NFA.

<!--
############
my_nfa = NFA(S_g, S_s)
table = my_nfa.build_nfa()
for k in my_nfa.states:
  print(k, my_nfa.states[k])
g = to_graph(table)
__canvas__(str(g))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
table = my_nfa.build_nfa()
for k in my_nfa.states:
  print(k, my_nfa.states[k])
g = to_graph(table)
__canvas__(str(g))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we need to build a DFA.

# Building the DFA
For DFA, a state is no longer a single item. So, let us define item separately.

<!--
############
class Item(State): pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Item(State): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A DFAState contains many items.

<!--
############
class DFAState:
    def __init__(self, items, dsid):
        self.sid = dsid
        # now compute the closure.
        self.items = items

    def def_keys(self):
        #assert len(self.items) == 1 # completion
        return [i.def_key() for i in self.items]

    # there will be only one item that has an at_dot != None
    def main_item(self):
        for i in self.items:
            if i.at_dot() is not None:
                return i
        # assert False the <> will be None
        return self.items[0]

    def __repr__(self):
        return '(%s)' % self.sid

    def __str__(self):
        return str(sorted([str(i) for i in self.items]))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFAState:
    def __init__(self, items, dsid):
        self.sid = dsid
        # now compute the closure.
        self.items = items

    def def_keys(self):
        #assert len(self.items) == 1 # completion
        return [i.def_key() for i in self.items]

    # there will be only one item that has an at_dot != None
    def main_item(self):
        for i in self.items:
            if i.at_dot() is not None:
                return i
        # assert False the &lt;&gt; will be None
        return self.items[0]

    def __repr__(self):
        return &#x27;(%s)&#x27; % self.sid

    def __str__(self):
        return str(sorted([str(i) for i in self.items]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define our DFA initialization.

<!--
############
class DFA(NFA):
    def __init__(self, g, start):
        self.items = {}
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self.get_production_rules(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA(NFA):
    def __init__(self, g, start):
        self.items = {}
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self.get_production_rules(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The start item is similar to before. The main difference is that
rather than returning multiple states, we return a single state containing
multiple items.

<!--
############
class DFA(DFA):
    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item

    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule) for rule in self.g[s] ]
        return self.create_state(items) # create state does closure

    def compute_closure(self, items):
        to_process = list(items)
        seen = set()
        new_items = {}
        while to_process:
            item_, *to_process = to_process
            if str(item_) in seen: continue
            seen.add(str(item_))
            new_items[str(item_)] = item_
            key = item_.at_dot()
            if key is None:
                continue
            # no closure for terminals
            if not fuzzer.is_nonterminal(key): continue
            new_items_ = [self.create_start_item(key, rule) for rule in self.g[key] ]
            to_process.extend(list(new_items_))
            for t in new_items_:
                new_items[str(t)] = t
        return list(new_items.values())

    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = DFAState(self.compute_closure(items), self.dsid_counter)
            self.dsid_counter += 1
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA(DFA):
    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item

    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule) for rule in self.g[s] ]
        return self.create_state(items) # create state does closure

    def compute_closure(self, items):
        to_process = list(items)
        seen = set()
        new_items = {}
        while to_process:
            item_, *to_process = to_process
            if str(item_) in seen: continue
            seen.add(str(item_))
            new_items[str(item_)] = item_
            key = item_.at_dot()
            if key is None:
                continue
            # no closure for terminals
            if not fuzzer.is_nonterminal(key): continue
            new_items_ = [self.create_start_item(key, rule) for rule in self.g[key] ]
            to_process.extend(list(new_items_))
            for t in new_items_:
                new_items[str(t)] = t
        return list(new_items.values())

    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = DFAState(self.compute_closure(items), self.dsid_counter)
            self.dsid_counter += 1
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_dfa = DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        ['<>::= | <S>',
         '<S>::= | <A> <B>',
         '<S>::= | <C>',
         '<A>::= | a',
         '<C>::= | c']

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        [&#x27;&lt;&gt;::= | &lt;S&gt;&#x27;,
         &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;,
         &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;,
         &#x27;&lt;A&gt;::= | a&#x27;,
         &#x27;&lt;C&gt;::= | c&#x27;]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the transitions.

<!--
############
class DFA(DFA):
    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))

    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() == key:
                item_ = self.advance_item(item)
                advanced.append(item_)
            else:
                pass
                # ignore
        return advanced

    def symbol_transition(self, dfastate, key):
        assert key is not None
        items = self.advance(dfastate, key)
        if not items: return None
        new_dfastate = self.create_state(items) # create state does closure
        return new_dfastate

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.items[item.sid] = item
        return self.my_items[(name, texpr, pos)]

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def find_transitions(self, dfastate):
        new_dfastates = []
        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            # add it to the states returned
            new_dfastates.append((k, new_dfastate))
        return new_dfastates

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA(DFA):
    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))

    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() == key:
                item_ = self.advance_item(item)
                advanced.append(item_)
            else:
                pass
                # ignore
        return advanced

    def symbol_transition(self, dfastate, key):
        assert key is not None
        items = self.advance(dfastate, key)
        if not items: return None
        new_dfastate = self.create_state(items) # create state does closure
        return new_dfastate

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.items[item.sid] = item
        return self.my_items[(name, texpr, pos)]

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def find_transitions(self, dfastate):
        new_dfastates = []
        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            # add it to the states returned
            new_dfastates.append((k, new_dfastate))
        return new_dfastates
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_dfa = DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        ['<>::= | <S>', '<S>::= | <A> <B>', '<S>::= | <C>', '<A>::= | a', '<C>::= | c']
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [('a', ['<A>::= a |']),
         ('c', ['<C>::= c |']),
         ('<A>', ['<S>::= <A> | <B>', '<B>::= | b']),
         ('<C>', ['<S>::= <C> |']),
         ('<S>', ['<>::= <S> |'])]


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        [&#x27;&lt;&gt;::= | &lt;S&gt;&#x27;, &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;, &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;, &#x27;&lt;A&gt;::= | a&#x27;, &#x27;&lt;C&gt;::= | c&#x27;]
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [(&#x27;a&#x27;, [&#x27;&lt;A&gt;::= a |&#x27;]),
         (&#x27;c&#x27;, [&#x27;&lt;C&gt;::= c |&#x27;]),
         (&#x27;&lt;A&gt;&#x27;, [&#x27;&lt;S&gt;::= &lt;A&gt; | &lt;B&gt;&#x27;, &#x27;&lt;B&gt;::= | b&#x27;]),
         (&#x27;&lt;C&gt;&#x27;, [&#x27;&lt;S&gt;::= &lt;C&gt; |&#x27;]),
         (&#x27;&lt;S&gt;&#x27;, [&#x27;&lt;&gt;::= &lt;S&gt; |&#x27;])]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Bringing all these together, let us build the DFA.

<!--
############
class DFA(DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            i =  self.states[s].main_item()
            if i.expr[i.dot-1] == key:
                states.append(self.states[s])
        return states

    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [('$', start_dfastate)]
        seen = set()
        while queue:
            (pkey, dfastate), *queue = queue
            if str(dfastate) in seen: continue
            seen.add(str(dfastate))

            new_dfastates = self.find_transitions(dfastate)
            for key, s in new_dfastates:
                # if the key is a nonterminal then it is a goto
                if key == '':
                    self.add_child(dfastate, key, s, 'shift')
                elif fuzzer.is_nonterminal(key):
                    self.add_child(dfastate, key, s, 'goto')
                else:
                    self.add_child(dfastate, key, s, 'shift')

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if not item.finished(): continue
                N = self.productions[self.get_key((item.name, list(item.expr)))]
                terminal_set = self.terminals
                # terminal_set = follow(item.name, self.g)
                for k in terminal_set:
                    self.add_reduction(dfastate, k, N, 'reduce')

                # Also, (only) for the graph, collect epsilon transmission to all
                # rules that are after the given nonterminal at the head.
                key = item.def_key()
                list_of_return_states = self.get_all_states_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(dfastate, '', s, 'to') # reduce
                    # these are already processed. So we do not add to queue

            queue.extend(new_dfastates)

        # now build the dfa table.
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in dfa_table[parent]: dfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in dfa_table[parent][key]:
                dfa_table[parent][key].append(v)

        return dfa_table


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DFA(DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            i =  self.states[s].main_item()
            if i.expr[i.dot-1] == key:
                states.append(self.states[s])
        return states

    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [(&#x27;$&#x27;, start_dfastate)]
        seen = set()
        while queue:
            (pkey, dfastate), *queue = queue
            if str(dfastate) in seen: continue
            seen.add(str(dfastate))

            new_dfastates = self.find_transitions(dfastate)
            for key, s in new_dfastates:
                # if the key is a nonterminal then it is a goto
                if key == &#x27;&#x27;:
                    self.add_child(dfastate, key, s, &#x27;shift&#x27;)
                elif fuzzer.is_nonterminal(key):
                    self.add_child(dfastate, key, s, &#x27;goto&#x27;)
                else:
                    self.add_child(dfastate, key, s, &#x27;shift&#x27;)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if not item.finished(): continue
                N = self.productions[self.get_key((item.name, list(item.expr)))]
                terminal_set = self.terminals
                # terminal_set = follow(item.name, self.g)
                for k in terminal_set:
                    self.add_reduction(dfastate, k, N, &#x27;reduce&#x27;)

                # Also, (only) for the graph, collect epsilon transmission to all
                # rules that are after the given nonterminal at the head.
                key = item.def_key()
                list_of_return_states = self.get_all_states_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(dfastate, &#x27;&#x27;, s, &#x27;to&#x27;) # reduce
                    # these are already processed. So we do not add to queue

            queue.extend(new_dfastates)

        # now build the dfa table.
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [&#x27;&#x27;])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == &#x27;reduce&#x27;: prefix = &#x27;r:&#x27; # N not a state.
            elif notes == &#x27;shift&#x27;: prefix = &#x27;s&#x27;
            elif notes == &#x27;goto&#x27;: prefix = &#x27;g&#x27;
            elif notes == &#x27;to&#x27;: prefix = &#x27;t&#x27;
            if key not in dfa_table[parent]: dfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in dfa_table[parent][key]:
                dfa_table[parent][key].append(v)

        return dfa_table
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test building the DFA.

<!--
############
my_dfa = DFA(S_g, S_s)
table = my_dfa.build_dfa()

for k in my_dfa.states:
  print(k)
  for v in my_dfa.states[k].items:
    print('', v)

rowh = table[0]
print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(table):
    print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = DFA(S_g, S_s)
table = my_dfa.build_dfa()

for k in my_dfa.states:
  print(k)
  for v in my_dfa.states[k].items:
    print(&#x27;&#x27;, v)

rowh = table[0]
print(&#x27;State\t&#x27;, &#x27;\t&#x27;,&#x27;\t&#x27;.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(table):
    print(str(i) + &#x27;\t&#x27;, &#x27;\t&#x27;,&#x27;\t&#x27;.join([str(row[c]) for c in row.keys()]))
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try graphing

<!--
############
g = to_graph(table)
__canvas__(str(g))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = to_graph(table)
__canvas__(str(g))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now provide the complete parser that relies on this automata.

<!--
############
class LR0Parser:
    def __init__(self, my_dfa):
        self.dfa = my_dfa
        self.parse_table = self.dfa.build_dfa()
        self.production_rules = self.dfa.production_rules

    def log(self, stack, tokens):
        print('Stack', stack)
        print('Tokens', tokens)

    def parse(self, input_string, start):
        tokens = list(input_string + '$')
        stack = [(None, 's0')]

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])
            if symbol == '$':
                i = self.dfa.states[state].main_item()
                if i.name == start and i.at_dot() == '$':
                    return True, "Input Accepted"

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f"Parsing Error: No actions state{state}:{symbol}"

            assert len(actions) == 1
            action = actions[0]

            if action.startswith('s'):
                tokens.pop(0)
                stack.append((symbol, action))

            elif action.startswith('r:'): # reduction. Not the next state.
                lhs, rhs = self.production_rules[action]
                for _ in rhs: stack.pop()

                _, prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f"Parsing Error: No transition {prev_state}:{lhs}"

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith('g'):
                self.stack.append((lhs, action))
            else: assert False

            self.log(stack, tokens)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0Parser:
    def __init__(self, my_dfa):
        self.dfa = my_dfa
        self.parse_table = self.dfa.build_dfa()
        self.production_rules = self.dfa.production_rules

    def log(self, stack, tokens):
        print(&#x27;Stack&#x27;, stack)
        print(&#x27;Tokens&#x27;, tokens)

    def parse(self, input_string, start):
        tokens = list(input_string + &#x27;$&#x27;)
        stack = [(None, &#x27;s0&#x27;)]

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])
            if symbol == &#x27;$&#x27;:
                i = self.dfa.states[state].main_item()
                if i.name == start and i.at_dot() == &#x27;$&#x27;:
                    return True, &quot;Input Accepted&quot;

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f&quot;Parsing Error: No actions state{state}:{symbol}&quot;

            assert len(actions) == 1
            action = actions[0]

            if action.startswith(&#x27;s&#x27;):
                tokens.pop(0)
                stack.append((symbol, action))

            elif action.startswith(&#x27;r:&#x27;): # reduction. Not the next state.
                lhs, rhs = self.production_rules[action]
                for _ in rhs: stack.pop()

                _, prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f&quot;Parsing Error: No transition {prev_state}:{lhs}&quot;

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith(&#x27;g&#x27;):
                self.stack.append((lhs, action))
            else: assert False

            self.log(stack, tokens)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing it.

<!--
############
my_dfa = DFA(S_g, S_s)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message = parser.parse(test_string, S_s)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = DFA(S_g, S_s)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;bbdd&quot;, &quot;baddd&quot;, &quot;aac&quot;, &quot;bdd&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message = parser.parse(test_string, S_s)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Attaching parse tree extraction.

<!--
############
class LR0Parser(LR0Parser):
    def parse(self, input_string, start):
        tokens = list(input_string) + ['$']
        stack = [(None, 's0')]
        self.node_stack = []

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f"Parsing Error: No actions state{state}:{symbol}", None

            if symbol == '$':
                i = self.dfa.states[state].main_item()
                if i.name == start and i.at_dot() == '$':
                    return True, "Input Accepted", self.node_stack[0]

            assert len(actions) == 1
            action = actions[0]

            if action.startswith('s'):
                tokens.pop(0)
                stack.append((symbol, action))
                self.node_stack.append((symbol, []))

            elif action.startswith('r'):
                lhs, rhs = self.production_rules[action]
                children = []
                for _ in rhs:
                    stack.pop()  # Pop state, symbol
                    children.insert(0, self.node_stack.pop())

                new_node = (lhs, children)
                self.node_stack.append(new_node)

                _,prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f"Parsing Error: No transition {prev_state}:{lhs}", None

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith('g'):
                stack.append((lhs, next_state))

            else: assert False

            self.log(stack, tokens)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0Parser(LR0Parser):
    def parse(self, input_string, start):
        tokens = list(input_string) + [&#x27;$&#x27;]
        stack = [(None, &#x27;s0&#x27;)]
        self.node_stack = []

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f&quot;Parsing Error: No actions state{state}:{symbol}&quot;, None

            if symbol == &#x27;$&#x27;:
                i = self.dfa.states[state].main_item()
                if i.name == start and i.at_dot() == &#x27;$&#x27;:
                    return True, &quot;Input Accepted&quot;, self.node_stack[0]

            assert len(actions) == 1
            action = actions[0]

            if action.startswith(&#x27;s&#x27;):
                tokens.pop(0)
                stack.append((symbol, action))
                self.node_stack.append((symbol, []))

            elif action.startswith(&#x27;r&#x27;):
                lhs, rhs = self.production_rules[action]
                children = []
                for _ in rhs:
                    stack.pop()  # Pop state, symbol
                    children.insert(0, self.node_stack.pop())

                new_node = (lhs, children)
                self.node_stack.append(new_node)

                _,prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f&quot;Parsing Error: No transition {prev_state}:{lhs}&quot;, None

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith(&#x27;g&#x27;):
                stack.append((lhs, next_state))

            else: assert False

            self.log(stack, tokens)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, let us build parse trees

<!--
############
my_dfa = DFA(S_g, S_s)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, S_s)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = DFA(S_g, S_s)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;bbdd&quot;, &quot;baddd&quot;, &quot;aac&quot;, &quot;bdd&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, S_s)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

[^lang1974deterministic]: Bernard Lang. "Deterministic techniques for efficient non-deterministic parsers." International Colloquium on Automata, Languages, and Programming. Springer, Berlin, Heidelberg, 1974.
[^bouckaert1975efficient]: M. Bouckaert, Alain Pirotte, M. Snelling. "Efficient parsing algorithms for general context-free parsers." Information Sciences 8.1 (1975): 1-26.

[^scott2013gll]: Elizabeth Scott, Adrian Johnstone. "GLL parse-tree generation." Science of Computer Programming 78.10 (2013): 1828-1844.

[^scott2010gll]: Elizabeth Scott, Adrian Johnstone. "GLL parsing." Electronic Notes in Theoretical Computer Science 253.7 (2010): 177-189.

[^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

[^tomita1984lr]: Masaru Tomita. LR parsers for natural languages. In 22nd conference on Association for Computational Linguistics, pages 354–357, Stanford, California, 1984. Association for Computational Linguistics.

[^tomita1986efficient]: Masaru Tomita. Efficient parsing for natural language: a fast algorithm for practical systems. Kluwer Academic Publishers, Boston, 1986.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-07-01-lr-parsing.py).


