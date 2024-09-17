---
published: true
title: Shift-Reduce Parsers LR(0) SLR(1) and LR(1)
layout: post
comments: true
tags: parsing gll
categories: post
---
TLDR; This tutorial is a complete implementation of shift-reduce
Parsers in Python. We build LR(0) parser, SLR(1) Parser and the
canonical LR(1) parser, and show how to extract the parse trees.
The Python interpreter is embedded so that you can
work through the implementation steps.
An LR parser is a bottom-up parser. The *L* stands for scanning the input
left-to-right, and the *R* stands for constructing a rightmost derivation.
This contrasts with LL parsers which are again left-to-right but construct
the leftmost derivation.


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
style. For example, given below is a simple grammar for nested parenthesis.

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
Equivalently,

```
<P> := '(' <P> ')'
     | '(' <D> ')'
<D> := 0 | 1
```

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

## Building the NFA
Let us try and build these dynamically.
We first build an NFA of the grammar. For that, we begin by adding a new
state `<>` to grammar.

### Augment Grammar with Start

<!--
############
def add_start_state(g, start, new_start='<>'):
    new_g = dict(g)
    new_g[new_start] = [[start, '$']]
    return new_g, new_start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def add_start_state(g, start, new_start=&#x27;&lt;&gt;&#x27;):
    new_g = dict(g)
    new_g[new_start] = [[start, &#x27;$&#x27;]]
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
A utility procedure to extract all symbols in a grammar.

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
### The State Data-structure
For building an NFA, all we need is to start with start item, and then
recursively identify the transitions. First, we define the state
data structure.
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

    def remaining(self):
        # x[0] is current, then x[1:] is remaining
        return self.expr[self.dot+1:]

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

    def remaining(self):
        # x[0] is current, then x[1:] is remaining
        return self.expr[self.dot+1:]

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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It can be tested this way

<!--
############
s = State('<S`>', ('<S>',), 0, 0)
print(s.at_dot())
print(str(s))
print(s.finished())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = State(&#x27;&lt;S`&gt;&#x27;, (&#x27;&lt;S&gt;&#x27;,), 0, 0)
print(s.at_dot())
print(str(s))
print(s.finished())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The NFA class
Next, we build an NFA out of a given grammar. An NFA is composed of
different states connected together by transitions.
#### NFA Initialization routines

<!--
############
class NFA:
    def __init__(self, g, start):
        self.grammar = g
        self.productions, self.production_rules = self._get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.state_sids = {} # Convenience for debugging only
        self.sid_counter = 0

    def get_key(self, kr):
        return "%s -> %s" %kr

    def _get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.grammar:
            for r in self.grammar[k]:
                production_rules["r:%d" % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA:
    def __init__(self, g, start):
        self.grammar = g
        self.productions, self.production_rules = self._get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.state_sids = {} # Convenience for debugging only
        self.sid_counter = 0

    def get_key(self, kr):
        return &quot;%s -&gt; %s&quot; %kr

    def _get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.grammar:
            for r in self.grammar[k]:
                production_rules[&quot;r:%d&quot; % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### NFA Start State (create_start)

<!--
############
class NFA(NFA):
    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    # create starting states for the given key
    def create_start(self, s):
        rules = self.grammar[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.grammar[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.state_sids[state.sid] = state
        return self.my_states[(name, texpr, pos)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    # create starting states for the given key
    def create_start(self, s):
        rules = self.grammar[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.grammar[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.state_sids[state.sid] = state
        return self.my_states[(name, texpr, pos)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.
Here is a  grammar.
 
```
 <S`> := <S>
 <S>  := 'a' <A> 'c'
       | 'b' '<A>' 'd' 'd'
 <A>  := 'b'
```
Equivalently, we have

<!--
############
S_g = {'<S>': [ ['a', '<A>', 'c'],
                 ['b', '<A>', 'd', 'd']],
        '<A>': [ ['b']]}
S_s = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
S_g = {&#x27;&lt;S&gt;&#x27;: [ [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;],
                 [&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;d&#x27;, &#x27;d&#x27;]],
        &#x27;&lt;A&gt;&#x27;: [ [&#x27;b&#x27;]]}
S_s = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can list the grammar production rules as follows:

<!--
############
S_g1, S_s1 = add_start_state(S_g, S_s)
i = 1
for k in S_g:
    for r in S_g[k]:
        print(i, k, r)
        i+=1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
S_g1, S_s1 = add_start_state(S_g, S_s)
i = 1
for k in S_g:
    for r in S_g[k]:
        print(i, k, r)
        i+=1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us use the grammar.

<!--
############
my_nfa = NFA(S_g1, S_s1)
st = my_nfa.create_start(S_s1)
assert str(st[0]) == '<>::= | <S> $'
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == '<S>::= | <A> <B>'
assert str(st[1]) == '<S>::= | <C>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g1, S_s1)
st = my_nfa.create_start(S_s1)
assert str(st[0]) == &#x27;&lt;&gt;::= | &lt;S&gt; $&#x27;
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;
assert str(st[1]) == &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Advance the state of parse by one token 

<!--
############
class NFA(NFA):
    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_nfa = NFA(S_g1, S_s1)
st_ = my_nfa.create_start(S_s1)
st = my_nfa.advance(st_[0])
assert str(st) == '<>::= <S> | $'
my_nfa = NFA(g1, g1_start)
st_ = my_nfa.create_start(g1_start)
st = [my_nfa.advance(s) for s in st_]
assert str(st[0]) == '<S>::= <A> | <B>'
assert str(st[1]) == '<S>::= <C> |'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g1, S_s1)
st_ = my_nfa.create_start(S_s1)
st = my_nfa.advance(st_[0])
assert str(st) == &#x27;&lt;&gt;::= &lt;S&gt; | $&#x27;
my_nfa = NFA(g1, g1_start)
st_ = my_nfa.create_start(g1_start)
st = [my_nfa.advance(s) for s in st_]
assert str(st[0]) == &#x27;&lt;S&gt;::= &lt;A&gt; | &lt;B&gt;&#x27;
assert str(st[1]) == &#x27;&lt;S&gt;::= &lt;C&gt; |&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### NFA find_transitions
Next, given a state, we need to find all other states reachable from it.
The first one is simply a transition from the current to the next state
when moving the parsing point one location. For example,
```
'<S>::= <A> | <B>'
```

is connected to the below by the key `<A>`.
```
'<S>::= <A> <B> |'
```

<!--
############
class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        return self.advance(state)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        return self.advance(state)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, note that this is an NFA. So, we also connect all
production rules of the next nonterminal with epsilon.
That is, given a state K -> t.V a
we get all rules of nonterminal V, and add with
starting 0

```
'<S>::= <A> | <B>'
```

is connected to below by $$\epsilon$$ 

```
'<A>::= | a',
```

<!--
############
class NFA(NFA):
    def epsilon_transitions(self, state):
        key = state.at_dot()
        # key should not be none at this point.
        assert key is not None
        new_states = []
        for rule in self.grammar[key]:
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
        for rule in self.grammar[key]:
            new_state = self.create_state(key, rule, 0)
            new_states.append(new_state)
        return new_states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Combining both and processing the state itself for its transitions.
First, if the dot is before a symbol, then we add the transition to the
advanced state with that symbol as the transition. Next, if the key at
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
my_nfa = NFA(S_g1, S_s1)
st = my_nfa.create_start(S_s1)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == "('<S>', (<>::= <S> | $ : 1))"
assert str(new_st[1]) == "('', (<S>::= | a <A> c : 2))"
assert str(new_st[2]) == "('', (<S>::= | b <A> d d : 3))"


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g1, S_s1)
st = my_nfa.create_start(S_s1)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == &quot;(&#x27;&lt;S&gt;&#x27;, (&lt;&gt;::= &lt;S&gt; | $ : 1))&quot;
assert str(new_st[1]) == &quot;(&#x27;&#x27;, (&lt;S&gt;::= | a &lt;A&gt; c : 2))&quot;
assert str(new_st[2]) == &quot;(&#x27;&#x27;, (&lt;S&gt;::= | b &lt;A&gt; d d : 3))&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, a utility method. This is only used to display the graph.
Given a key, we want to get all items that contains the parsing of this key.

<!--
############
class NFA(NFA):
    def get_all_rules_with_dot_after_key(self, key):
        states = []
        for k in self.grammar:
            for rule in self.grammar[k]:
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
        for k in self.grammar:
            for rule in self.grammar[k]:
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
#### NFA build_nfa
Now, we can build the NFA.

<!--
############
class NFA(NFA):
    def build_table(self):
        nfa_table = []
        for _ in self.my_states.keys():
            row = {k:[] for k in (self.terminals + self.non_terminals + [''])}
            nfa_table.append(row)

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

    def add_shift(self, state, key, s):
        # if the key is a nonterminal then it is a goto
        if key == '':
            self.add_child(state, key, s, 'shift')
        elif fuzzer.is_nonterminal(key):
            self.add_child(state, key, s, 'goto')
        else:
            self.add_child(state, key, s, 'shift')

    def add_reduce(self, state):
        N = self.productions[self.get_key((state.name, list(state.expr)))]
        for k in self.terminals:
            self.add_reduction(state, k, N, 'reduce')

    def add_actual_reductions(self, state):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = state.def_key()
        list_of_return_states = self.get_all_rules_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(state, '', s, 'to') # reduce to

    def build_nfa(self):
        start_item = self.create_start(self.start)[0]
        queue = [('$', start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                self.add_shift(state, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                self.add_reduce(state)

                # only for the graph, not for traditional algorithm
                self.add_actual_reductions(state)

            queue.extend(new_states)
        return self.build_table()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def build_table(self):
        nfa_table = []
        for _ in self.my_states.keys():
            row = {k:[] for k in (self.terminals + self.non_terminals + [&#x27;&#x27;])}
            nfa_table.append(row)

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

    def add_shift(self, state, key, s):
        # if the key is a nonterminal then it is a goto
        if key == &#x27;&#x27;:
            self.add_child(state, key, s, &#x27;shift&#x27;)
        elif fuzzer.is_nonterminal(key):
            self.add_child(state, key, s, &#x27;goto&#x27;)
        else:
            self.add_child(state, key, s, &#x27;shift&#x27;)

    def add_reduce(self, state):
        N = self.productions[self.get_key((state.name, list(state.expr)))]
        for k in self.terminals:
            self.add_reduction(state, k, N, &#x27;reduce&#x27;)

    def add_actual_reductions(self, state):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = state.def_key()
        list_of_return_states = self.get_all_rules_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(state, &#x27;&#x27;, s, &#x27;to&#x27;) # reduce to

    def build_nfa(self):
        start_item = self.create_start(self.start)[0]
        queue = [(&#x27;$&#x27;, start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                self.add_shift(state, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                self.add_reduce(state)

                # only for the graph, not for traditional algorithm
                self.add_actual_reductions(state)

            queue.extend(new_states)
        return self.build_table()
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
## Show graph

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
for k in my_nfa.state_sids:
  print(k, my_nfa.state_sids[k])
g = to_graph(table)
__canvas__(str(g))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(S_g, S_s)
table = my_nfa.build_nfa()
for k in my_nfa.state_sids:
  print(k, my_nfa.state_sids[k])
g = to_graph(table)
__canvas__(str(g))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# LR0 Automata

An NFA is not very practical for parsing. For one, it is an NFA,
over-approximating the grammar, and secondly, there can be multiple possible
paths for a given prefix.  Hence, it is not very optimal.
Let us next see how to generate a DFA instead.

 An LR automata is composed of multiple states, and each state represents a set
of items that indicate the parsing progress. The states are connected together
using transitions which are composed of the terminal and nonterminal symbols
in the grammar.

To construct the LR automata, one starts with the initial state containing the
augmented start symbol (if necessary), and we apply closure to expand the
context. For the closure, we simply merge all epsilon transitions to current
item.

## Closure
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
### Compiled DFA States

#### State 0
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
#### State 1
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
#### State 2
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
#### State 3
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
#### State 4
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
#### State 5
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
#### State 6
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
#### State 7
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
#### State 8
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
#### State 9
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
## Building the DFA
Next, we need to build a DFA.
For DFA, a state is no longer a single item. So, let us define item separately.
### Item

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
### DFAState

A DFAState contains many items.

<!--
############
class DFAState:
    def __init__(self, items, dsid):
        self.sid = dsid
        self.items = items

    def def_keys(self):
        return [i.def_key() for i in self.items]

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
        self.items = items

    def def_keys(self):
        return [i.def_key() for i in self.items]

    def __repr__(self):
        return &#x27;(%s)&#x27; % self.sid

    def __str__(self):
        return str(sorted([str(i) for i in self.items]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### LR(0) DFA
We define our DFA initialization. We also define two utilities for
creating new items and DFA states.

<!--
############
class LR0DFA(NFA):
    def __init__(self, g, start):
        self.item_sids = {}
        self.states = {}
        self.grammar = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)

    def new_state(self, items):
        s = DFAState(items, self.dsid_counter)
        self.dsid_counter += 1
        return s

    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(NFA):
    def __init__(self, g, start):
        self.item_sids = {}
        self.states = {}
        self.grammar = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)

    def new_state(self, items):
        s = DFAState(items, self.dsid_counter)
        self.dsid_counter += 1
        return s

    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### DFA Compute the closure
We have discussed computing the closure before. The idea is to identify any
nonterminals that are next to be parsed, and recursively expand them, adding
to the items.

<!--
############
class LR0DFA(LR0DFA):
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
            if key is None: continue
            if not fuzzer.is_nonterminal(key): continue
            for rule in self.grammar[key]:
                new_item = self.create_start_item(key, rule)
                to_process.append(new_item)
        return list(new_items.values())

    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
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
            if key is None: continue
            if not fuzzer.is_nonterminal(key): continue
            for rule in self.grammar[key]:
                new_item = self.create_start_item(key, rule)
                to_process.append(new_item)
        return list(new_items.values())

    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### DFA Start State (create_start)
The start item is similar to before. The main difference is that
rather than returning multiple states, we return a single state containing
multiple items.

<!--
############
class LR0DFA(LR0DFA):
    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = self.new_state(self.compute_closure(items))
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        items = [self.create_start_item(s, rule) for rule in self.grammar[s] ]
        return self.create_state(items) # create state does closure

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = self.new_state(self.compute_closure(items))
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        items = [self.create_start_item(s, rule) for rule in self.grammar[s] ]
        return self.create_state(items) # create state does closure
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        ['<>::= | <S> $',
         '<S>::= | <A> <B>',
         '<S>::= | <C>',
         '<A>::= | a',
         '<C>::= | c']


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        [&#x27;&lt;&gt;::= | &lt;S&gt; $&#x27;,
         &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;,
         &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;,
         &#x27;&lt;A&gt;::= | a&#x27;,
         &#x27;&lt;C&gt;::= | c&#x27;]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Advance the state of parse by the given token 
Unlike in NFA, where we had only one item, and hence, there
was only one advancing possible, here we have multiple items.
Hence, we are given a token by which to advance, and return
all items that advance by that token, advanced.

<!--
############
class LR0DFA(LR0DFA):
    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() != key: continue
            item_ = self.advance_item(item)
            advanced.append(item_)
        return advanced

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() != key: continue
            item_ = self.advance_item(item)
            advanced.append(item_)
        return advanced

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_dfa = LR0DFA(g1a, g1a_start)
start = my_dfa.create_start(g1a_start)
st = my_dfa.advance(start, '<S>')
assert [str(s) for s in st] == ['<>::= <S> | $']

st = my_dfa.advance(start, 'a')
assert [str(s) for s in st] == [ '<A>::= a |']

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
start = my_dfa.create_start(g1a_start)
st = my_dfa.advance(start, &#x27;&lt;S&gt;&#x27;)
assert [str(s) for s in st] == [&#x27;&lt;&gt;::= &lt;S&gt; | $&#x27;]

st = my_dfa.advance(start, &#x27;a&#x27;)
assert [str(s) for s in st] == [ &#x27;&lt;A&gt;::= a |&#x27;]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### DFA find_transitions

Next, we define the transitions. Unlike in the case of NFA where we had only a
single item, we have multiple items. So, we look through each possible
token (terminals and nonterminals)

<!--
############
class LR0DFA(LR0DFA):
    def symbol_transition(self, dfastate, key):
        items = self.advance(dfastate, key)
        if not items: return None
        return self.create_state(items) # create state does closure

    def find_transitions(self, dfastate):
        new_dfastates = []
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            new_dfastates.append((k, new_dfastate))
        return new_dfastates

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
    def symbol_transition(self, dfastate, key):
        items = self.advance(dfastate, key)
        if not items: return None
        return self.create_state(items) # create state does closure

    def find_transitions(self, dfastate):
        new_dfastates = []
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            new_dfastates.append((k, new_dfastate))
        return new_dfastates
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        ['<>::= | <S> $', '<S>::= | <A> <B>', '<S>::= | <C>', '<A>::= | a', '<C>::= | c']
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [('a', ['<A>::= a |']),
         ('c', ['<C>::= c |']),
         ('<A>', ['<S>::= <A> | <B>', '<B>::= | b']),
         ('<C>', ['<S>::= <C> |']),
         ('<S>', ['<>::= <S> | $'])]


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        [&#x27;&lt;&gt;::= | &lt;S&gt; $&#x27;, &#x27;&lt;S&gt;::= | &lt;A&gt; &lt;B&gt;&#x27;, &#x27;&lt;S&gt;::= | &lt;C&gt;&#x27;, &#x27;&lt;A&gt;::= | a&#x27;, &#x27;&lt;C&gt;::= | c&#x27;]
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [(&#x27;a&#x27;, [&#x27;&lt;A&gt;::= a |&#x27;]),
         (&#x27;c&#x27;, [&#x27;&lt;C&gt;::= c |&#x27;]),
         (&#x27;&lt;A&gt;&#x27;, [&#x27;&lt;S&gt;::= &lt;A&gt; | &lt;B&gt;&#x27;, &#x27;&lt;B&gt;::= | b&#x27;]),
         (&#x27;&lt;C&gt;&#x27;, [&#x27;&lt;S&gt;::= &lt;C&gt; |&#x27;]),
         (&#x27;&lt;S&gt;&#x27;, [&#x27;&lt;&gt;::= &lt;S&gt; | $&#x27;])]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### add_reduce
This is different from NFA because we are iterating over items, but we need
to add reduction to the dfastate

<!--
############
class LR0DFA(LR0DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in  self.terminals:
            self.add_reduction(dfastate, k, N, 'reduce')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in  self.terminals:
            self.add_reduction(dfastate, k, N, &#x27;reduce&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Similarly the graph related utilities also change a bit.

<!--
############
class LR0DFA(LR0DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            for item in self.states[s].items:
                if item.dot == 0: continue # no token parsed.
                if item.expr[item.dot-1] == key:
                    states.append(self.states[s])
        return states

    def add_actual_reductions(self, item, dfastate):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = item.def_key()
        list_of_return_states = self.get_all_states_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(dfastate, '', s, 'to') # reduce

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            for item in self.states[s].items:
                if item.dot == 0: continue # no token parsed.
                if item.expr[item.dot-1] == key:
                    states.append(self.states[s])
        return states

    def add_actual_reductions(self, item, dfastate):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = item.def_key()
        list_of_return_states = self.get_all_states_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(dfastate, &#x27;&#x27;, s, &#x27;to&#x27;) # reduce
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### LR0DFA build_dfa
Bringing all these together, let us build the DFA. (Compare to build_nfa).

<!--
############
class LR0DFA(LR0DFA):
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
                assert key != ''
                self.add_shift(dfastate, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if item.finished():
                    self.add_reduce(item, dfastate)

                    # Also, (only) for the graph, collect epsilon transmission to all
                    # rules that are after the given nonterminal at the head.
                    self.add_actual_reductions(item, dfastate)

            queue.extend(new_dfastates)

        return self.build_table()


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR0DFA(LR0DFA):
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
                assert key != &#x27;&#x27;
                self.add_shift(dfastate, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if item.finished():
                    self.add_reduce(item, dfastate)

                    # Also, (only) for the graph, collect epsilon transmission to all
                    # rules that are after the given nonterminal at the head.
                    self.add_actual_reductions(item, dfastate)

            queue.extend(new_dfastates)

        return self.build_table()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test building the DFA.

<!--
############
my_dfa = LR0DFA(S_g, S_s)
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
my_dfa = LR0DFA(S_g, S_s)
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
# LR0Recognizer
We can now provide the complete parser that relies on this automata.

<!--
############
class LR0Recognizer:
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
                for i in self.dfa.states[state].items:
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
class LR0Recognizer:
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
                for i in self.dfa.states[state].items:
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
my_dfa = LR0DFA(S_g1, S_s1)
parser = LR0Recognizer(my_dfa)
# Test the parser with some input strings
test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message = parser.parse(test_string, S_s1)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(S_g1, S_s1)
parser = LR0Recognizer(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;bbdd&quot;, &quot;baddd&quot;, &quot;aac&quot;, &quot;bdd&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message = parser.parse(test_string, S_s1)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# LR0Parser
Attaching parse tree extraction.

<!--
############
class LR0Parser(LR0Recognizer):
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
                for i in self.dfa.states[state].items:
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
class LR0Parser(LR0Recognizer):
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
                for i in self.dfa.states[state].items:
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
my_dfa = LR0DFA(S_g1, S_s1)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, S_s1)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(S_g1, S_s1)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;bbdd&quot;, &quot;baddd&quot;, &quot;aac&quot;, &quot;bdd&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, S_s1)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, let us consider the following grammar.

<!--
############
G2_g = {
        '<S`>' : [['<S>', '$']],
        '<S>' :  [['a', '<B>', 'c'],
                  ['a', '<D>', 'd']],
        '<B>' :  [[ 'b']],
        '<D>' :  [['b']]
        }
G2_s = '<S`>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G2_g = {
        &#x27;&lt;S`&gt;&#x27; : [[&#x27;&lt;S&gt;&#x27;, &#x27;$&#x27;]],
        &#x27;&lt;S&gt;&#x27; :  [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;c&#x27;],
                  [&#x27;a&#x27;, &#x27;&lt;D&gt;&#x27;, &#x27;d&#x27;]],
        &#x27;&lt;B&gt;&#x27; :  [[ &#x27;b&#x27;]],
        &#x27;&lt;D&gt;&#x27; :  [[&#x27;b&#x27;]]
        }
G2_s = &#x27;&lt;S`&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us build the parse table.

<!--
############
my_dfa = LR0DFA(G2_g, G2_s)
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
my_dfa = LR0DFA(G2_g, G2_s)
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
As you can see, on State 3, we have a two possible reductions -- r3 and r4.
This is called a reduce/reduce conflict. The issue is that when we come to
state 3, that is.
```
<B>::= b |
<D>::= b |
```
We have two possible choices of reduction. We can either reduce to `<B>` or
to `<D>`. To determine which one to reduce to, we need a lookahead. If the
next token is `c`, then we should reduce to `<B>`. If the next one is `d`,
we should reduce to `<D>`. This is what SLR parsers do.

# SLR1 Automata

For using SLR1 automation, we require first and follow sets. This has been
discussed previously. Hence, providing the code here directly.
### First and follow

<!--
############
nullable_grammar = {
    '<start>': [['<A>', '<B>']],
    '<A>': [['a'], [], ['<C>']],
    '<B>': [['b']],
    '<C>': [['<A>'], ['<B>']]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nullable_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;], [], [&#x27;&lt;C&gt;&#x27;]],
    &#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;]],
    &#x27;&lt;C&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;], [&#x27;&lt;B&gt;&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The definition is as follows.

<!--
############
def union(a, b):
    n = len(a)
    a |= b
    return len(a) != n

def get_first_and_follow(grammar):
    terminals, nonterminals = symbols(grammar)
    first = {i: set() for i in nonterminals}
    first.update((i, {i}) for i in terminals)
    follow = {i: set() for i in nonterminals}
    nullable = set()
    while True:
        added = 0
        productions = [(k,rule) for k in nonterminals for rule in grammar[k]]
        for k, rule in productions:
            can_be_empty = True
            for t in rule:
                added += union(first[k], first[t])
                if t not in nullable:
                    can_be_empty = False
                    break
            if can_be_empty:
                added += union(nullable, {k})

            follow_ = follow[k]
            for t in reversed(rule):
                if t in follow:
                    added += union(follow[t], follow_)
                if t in nullable:
                    follow_ = follow_.union(first[t])
                else:
                    follow_ = first[t]
        if not added:
            return first, follow, nullable

def first_of_rule(rule, first_sets, nullable_set):
    first_set = set()
    for token in rule:
        if fuzzer.is_nonterminal(token):
            first_set |= first_sets[token]
            if token not in nullable_set: break
        else:
            first_set.add(token)
            break
    return first_set

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def union(a, b):
    n = len(a)
    a |= b
    return len(a) != n

def get_first_and_follow(grammar):
    terminals, nonterminals = symbols(grammar)
    first = {i: set() for i in nonterminals}
    first.update((i, {i}) for i in terminals)
    follow = {i: set() for i in nonterminals}
    nullable = set()
    while True:
        added = 0
        productions = [(k,rule) for k in nonterminals for rule in grammar[k]]
        for k, rule in productions:
            can_be_empty = True
            for t in rule:
                added += union(first[k], first[t])
                if t not in nullable:
                    can_be_empty = False
                    break
            if can_be_empty:
                added += union(nullable, {k})

            follow_ = follow[k]
            for t in reversed(rule):
                if t in follow:
                    added += union(follow[t], follow_)
                if t in nullable:
                    follow_ = follow_.union(first[t])
                else:
                    follow_ = first[t]
        if not added:
            return first, follow, nullable

def first_of_rule(rule, first_sets, nullable_set):
    first_set = set()
    for token in rule:
        if fuzzer.is_nonterminal(token):
            first_set |= first_sets[token]
            if token not in nullable_set: break
        else:
            first_set.add(token)
            break
    return first_set
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing it.

<!--
############
first, follow, nullable = get_first_and_follow(nullable_grammar)
print("first:", first)
print("follow:", follow)
print("nullable", nullable)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
first, follow, nullable = get_first_and_follow(nullable_grammar)
print(&quot;first:&quot;, first)
print(&quot;follow:&quot;, follow)
print(&quot;nullable&quot;, nullable)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Building the DFA
#### DFA Initialization routines

<!--
############
class SLR1DFA(LR0DFA):
    def __init__(self, g, start):
        self.item_sids = {} # debugging convenience only
        self.states = {}
        self.grammar = g
        self.start = start
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)
        self.first, self.follow, self.nullable = get_first_and_follow(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SLR1DFA(LR0DFA):
    def __init__(self, g, start):
        self.item_sids = {} # debugging convenience only
        self.states = {}
        self.grammar = g
        self.start = start
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)
        self.first, self.follow, self.nullable = get_first_and_follow(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we build the dfa. There is only one change. (See CHANGED)
When reducing, we only reduce if the token lookahead is in the follow set.

<!--
############
class SLR1DFA(SLR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in self.follow[item.name]: # CHANGED
            self.add_reduction(dfastate, k, N, 'reduce')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SLR1DFA(SLR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in self.follow[item.name]: # CHANGED
            self.add_reduction(dfastate, k, N, &#x27;reduce&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see if it works.

<!--
############
my_dfa = SLR1DFA(G2_g, G2_s)
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
my_dfa = SLR1DFA(G2_g, G2_s)
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
### SLR1Parser
There is no difference in the parser.

<!--
############
class SLR1Parser(LR0Parser): pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SLR1Parser(LR0Parser): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try parsing with it.

<!--
############
G2_g = {
        '<>' : [['<S>', '$']],
        '<S>' :  [['a', '<B>', 'c'],
                  ['a', '<D>', 'd']],
        '<B>' :  [[ 'b']],
        '<D>' :  [['b']]
        }
G2_s = '<>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G2_g = {
        &#x27;&lt;&gt;&#x27; : [[&#x27;&lt;S&gt;&#x27;, &#x27;$&#x27;]],
        &#x27;&lt;S&gt;&#x27; :  [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;c&#x27;],
                  [&#x27;a&#x27;, &#x27;&lt;D&gt;&#x27;, &#x27;d&#x27;]],
        &#x27;&lt;B&gt;&#x27; :  [[ &#x27;b&#x27;]],
        &#x27;&lt;D&gt;&#x27; :  [[&#x27;b&#x27;]]
        }
G2_s = &#x27;&lt;&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Parsing

<!--
############
my_dfa = SLR1DFA(G2_g, G2_s)
parser = SLR1Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["abc", "abd", "aabc"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, G2_s)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = SLR1DFA(G2_g, G2_s)
parser = SLR1Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;abd&quot;, &quot;aabc&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, G2_s)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, consider this grammar

<!--
############
LR_g = {
        "<>": [["<S>", "$"]],
        "<S>": [
            ["a", "<B>", "c"],
            ["a", "<D>", "d"],
            ["<B>", "d"]
            ],
        "<B>": [["b"]],
        "<D>": [["b"]]
        }
LR_s = '<>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
LR_g = {
        &quot;&lt;&gt;&quot;: [[&quot;&lt;S&gt;&quot;, &quot;$&quot;]],
        &quot;&lt;S&gt;&quot;: [
            [&quot;a&quot;, &quot;&lt;B&gt;&quot;, &quot;c&quot;],
            [&quot;a&quot;, &quot;&lt;D&gt;&quot;, &quot;d&quot;],
            [&quot;&lt;B&gt;&quot;, &quot;d&quot;]
            ],
        &quot;&lt;B&gt;&quot;: [[&quot;b&quot;]],
        &quot;&lt;D&gt;&quot;: [[&quot;b&quot;]]
        }
LR_s = &#x27;&lt;&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see if it works.

<!--
############
my_dfa = SLR1DFA(LR_g, LR_s)
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
my_dfa = SLR1DFA(LR_g, LR_s)
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
You will notice a conflict in State 5. To resolve this, we need the full
LR(1) parser.
## LR1 Automata
### LR1Item
The LR1 item is similar to the Item, except that it contains a lookahead.

<!--
############
class LR1Item(Item):
    def __init__(self, name, expr, dot, sid, lookahead):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid
        self.lookahead = lookahead

    def __repr__(self):
        return "(%s, %s : %d)" % (str(self), self.lookahead, self.sid)

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1Item(Item):
    def __init__(self, name, expr, dot, sid, lookahead):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid
        self.lookahead = lookahead

    def __repr__(self):
        return &quot;(%s, %s : %d)&quot; % (str(self), self.lookahead, self.sid)

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### LR1DFA class

We also need update on create_item etc to handle the lookahead.
The advance_item is called from `advance(item)` which does not require
changes.

<!--
############
class LR1DFA(SLR1DFA):
    def advance_item(self, item):
        return self.create_item(item.name, item.expr, item.dot+1, item.lookahead)

    def new_item(self, name, texpr, pos, lookahead):
        item =  LR1Item(name, texpr, pos, self.sid_counter, lookahead)
        self.sid_counter += 1
        return item

    def create_item(self, name, expr, pos, lookahead):
        texpr = tuple(expr)
        if (name, texpr, pos, lookahead) not in self.my_items:
            item = self.new_item(name, texpr, pos, lookahead)
            self.my_items[(name, texpr, pos, lookahead)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos, lookahead)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1DFA(SLR1DFA):
    def advance_item(self, item):
        return self.create_item(item.name, item.expr, item.dot+1, item.lookahead)

    def new_item(self, name, texpr, pos, lookahead):
        item =  LR1Item(name, texpr, pos, self.sid_counter, lookahead)
        self.sid_counter += 1
        return item

    def create_item(self, name, expr, pos, lookahead):
        texpr = tuple(expr)
        if (name, texpr, pos, lookahead) not in self.my_items:
            item = self.new_item(name, texpr, pos, lookahead)
            self.my_items[(name, texpr, pos, lookahead)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos, lookahead)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The compute_closure now contains the lookahead.
This is the biggest procedure change from LR0DFA. 
The main difference in computing the lookahead. 
The lines added and modified from LR0DFA indicated in the procedure.

Here, say we are computing the closure of `A -> Alpha . <B> <Beta>`.
Remember that when we create new items for closure, we have to provide it with
a lookahead.

So, To compute the closure at `<B>`, we create items with lookahead which are
characters that can follow `<B>`. This need not be just the `first(<Beta>)`
but also what may follow `<Beta>` if `<Beta>` is nullable. This would be the
lookahead of the item `A -> Alpha . <B> <Beta>` which we already have, let us
say this is `l`. So, # we compute `first(<Beta> l)` for lookahead.

<!--
############
class LR1DFA(LR1DFA):

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
            if key is None: continue
            if not fuzzer.is_nonterminal(key): continue
            remaining = list(item_.remaining()) + [item_.lookahead] # ADDED
            lookaheads = first_of_rule(remaining, self.first, self.nullable) # ADDED
            for rule in self.grammar[key]:
                for lookahead in lookaheads: # ADDED
                    new_item = self.create_start_item(key, rule, lookahead) # lookahead
                    to_process.append(new_item)
        return list(new_items.values())

    def create_start_item(self, s, rule, lookahead):
        return self.new_item(s, tuple(rule), 0, lookahead)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1DFA(LR1DFA):

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
            if key is None: continue
            if not fuzzer.is_nonterminal(key): continue
            remaining = list(item_.remaining()) + [item_.lookahead] # ADDED
            lookaheads = first_of_rule(remaining, self.first, self.nullable) # ADDED
            for rule in self.grammar[key]:
                for lookahead in lookaheads: # ADDED
                    new_item = self.create_start_item(key, rule, lookahead) # lookahead
                    to_process.append(new_item)
        return list(new_items.values())

    def create_start_item(self, s, rule, lookahead):
        return self.new_item(s, tuple(rule), 0, lookahead)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### LR1DFA building DFA
This method create_start changes to include the '$' as lookahead.

<!--
############
class LR1DFA(LR1DFA):
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule, '$') for rule in self.grammar[s]]
        return self.create_state(items)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1DFA(LR1DFA):
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule, &#x27;$&#x27;) for rule in self.grammar[s]]
        return self.create_state(items)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another major change, we no longer add a reduction to all follows of item.name
instead, we restrict it to just item.lookahead.

<!--
############
class LR1DFA(LR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        # k is changed to item.lookahead
        self.add_reduction(dfastate, item.lookahead, N, 'reduce') # DEL/CHANGED

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1DFA(LR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        # k is changed to item.lookahead
        self.add_reduction(dfastate, item.lookahead, N, &#x27;reduce&#x27;) # DEL/CHANGED
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### LR1Parser
the parse class does not change.

<!--
############
class LR1Parser(SLR1Parser): pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LR1Parser(SLR1Parser): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
grammar

<!--
############
LR_g = {
        "<>": [["<S>", "$"]],
        "<S>": [
            ["a", "<B>", "c"],
            ["a", "<D>", "d"],
            ["<B>", "d"]
            ],
        "<B>": [["b"]],
        "<D>": [["b"]]
        }
LR_s = '<>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
LR_g = {
        &quot;&lt;&gt;&quot;: [[&quot;&lt;S&gt;&quot;, &quot;$&quot;]],
        &quot;&lt;S&gt;&quot;: [
            [&quot;a&quot;, &quot;&lt;B&gt;&quot;, &quot;c&quot;],
            [&quot;a&quot;, &quot;&lt;D&gt;&quot;, &quot;d&quot;],
            [&quot;&lt;B&gt;&quot;, &quot;d&quot;]
            ],
        &quot;&lt;B&gt;&quot;: [[&quot;b&quot;]],
        &quot;&lt;D&gt;&quot;: [[&quot;b&quot;]]
        }
LR_s = &#x27;&lt;&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Parsing

<!--
############
my_dfa = LR1DFA(LR_g, LR_s)
parser = LR1Parser(my_dfa)

for k in my_dfa.states:
  print(k)
  for v in my_dfa.states[k].items:
    print('', v)

rowh = parser.parse_table[0]
print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(parser.parse_table):
    print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
print()


# Test the parser with some input strings
test_strings = ["abc", "abd", "bd"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, LR_s)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR1DFA(LR_g, LR_s)
parser = LR1Parser(my_dfa)

for k in my_dfa.states:
  print(k)
  for v in my_dfa.states[k].items:
    print(&#x27;&#x27;, v)

rowh = parser.parse_table[0]
print(&#x27;State\t&#x27;, &#x27;\t&#x27;,&#x27;\t&#x27;.join([repr(c) for c in rowh.keys()]))
for i,row in enumerate(parser.parse_table):
    print(str(i) + &#x27;\t&#x27;, &#x27;\t&#x27;,&#x27;\t&#x27;.join([str(row[c]) for c in row.keys()]))
print()


# Test the parser with some input strings
test_strings = [&quot;abc&quot;, &quot;abd&quot;, &quot;bd&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, LR_s)
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


