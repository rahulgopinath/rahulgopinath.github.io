---
published: true
title: Shift-Reduce Parsers LR(0) SLR(1) and LR(1)
layout: post
comments: true
tags: parsing gll
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
TLDR; This tutorial is a complete implementation of shift-reduce
parsers in Python. We build LR(0) parser, SLR(1) Parser and the
canonical LR(1) parser, and show how to extract the parse trees.
Python code snippets are provided throughout so that you can
work through the implementation steps.
An LR parser is a bottom-up parser[^grune2008parsing]. The *L* stands for scanning the input
left-to-right, and the *R* stands for constructing a rightmost derivation.
This contrasts with LL parsers which are again left-to-right but construct
the leftmost derivation. It is a shift reduce parser because the operation
of the parser is to repeatedly shift an input symbol (left-to-right) into
the stack, and to match the current stack with some production rule based
on the length of the production rule, and if it matches, reduce the symbols on
the top of the stack to the head of the production rule.
### Prerequisites
As before, we start with the prerequisite imports.
Note: The following libraries may need to be installed separately.

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
style. For example, given below is a simple grammar for nested parentheses.

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

The viable prefix is the portion of the input string that has been
recognized so far. This recognition is accomplished by the LR automaton,
which we describe next.

But before that, let us start slow. Let us consider the following grammar

```
E -> ( D + E )
E -> D
D -> 1
```
Let us also introduce an augmented rule

```
S` -> E
```
 
If we are going for a naive translation
of the grammar into an automata, this is what we could do. That is, we start
with the starting production rule
`S' -> E`. Since we are starting to parse, let us indicate the parse point
also, which would be before `E` is parsed. That is, `S' -> .E`. The period
represents the current parse point. If we somehow parsed `E` now, then we
would transition to an accept state. This is represented by `S' -> E.`.
However, since the transition is a nonterminal, it can't happen by reading
the corresponding symbol `E` from the input stream. It has to happen through
another path. Hence, we indicate this by a dashed line. Next, when the parse
is at `S' -> .E`, any of the expansions of `E` can now be parsed. So, we add
each expansion of `E` as $$\epsilon$$ transition away. These are
`E := . ( D + E )` and `E := . D`. Continuing in this fashion, we have: 

<!--
############
__canvas__('''
digraph LR0_Automaton {
 rankdir=TB;
 node [shape = rectangle];
 start [shape = point];
 // States
 0 [label = "0: S' -> . E $"];
 1 [label = "1: E -> . ( D + E )"];
 2 [label = "2: E -> . D"];
 3 [label = "3: D -> . 1"];
 4 [label = "4: S' -> E . $"];
 5 [label = "5: E -> ( . D + E )"];
 6 [label = "6: D -> 1 ."];
 7 [label = "7: E -> D ."];
 8 [label = "8: E -> ( D . + E )"];
 9 [label = "9: E -> ( D + . E )"];
 10 [label = "10: E -> ( D + E . )"];
 11 [label = "11: E -> ( D + E ) ."];
 12 [label = "12: S' -> E $ ."];
 // Regular transitions
 start -> 0;
 0 -> 1 [label = "ε"];
 0 -> 2 [label = "ε"];
 0 -> 3 [label = "ε"];
 1 -> 5 [label = "("];
 2 -> 3 [label = "ε"];
 3 -> 6 [label = "1"];
 5 -> 3 [label = "ε"];
 8 -> 9 [label = "+"];
 9 -> 1 [label = "ε"];
 9 -> 2 [label = "ε"];
 9 -> 3 [label = "ε"];
 10 -> 11 [label = ")"];
 4 -> 12 [label = "$"];
 // Nonterminal transitions (dashed)
 edge [style = dashed];
 0 -> 4 [label = "E"];
 2 -> 7 [label = "D"];
 5 -> 8 [label = "D"];
 9 -> 10 [label = "E"];
}
''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
digraph LR0_Automaton {
 rankdir=TB;
 node [shape = rectangle];
 start [shape = point];
 // States
 0 [label = &quot;0: S&#x27; -&gt; . E $&quot;];
 1 [label = &quot;1: E -&gt; . ( D + E )&quot;];
 2 [label = &quot;2: E -&gt; . D&quot;];
 3 [label = &quot;3: D -&gt; . 1&quot;];
 4 [label = &quot;4: S&#x27; -&gt; E . $&quot;];
 5 [label = &quot;5: E -&gt; ( . D + E )&quot;];
 6 [label = &quot;6: D -&gt; 1 .&quot;];
 7 [label = &quot;7: E -&gt; D .&quot;];
 8 [label = &quot;8: E -&gt; ( D . + E )&quot;];
 9 [label = &quot;9: E -&gt; ( D + . E )&quot;];
 10 [label = &quot;10: E -&gt; ( D + E . )&quot;];
 11 [label = &quot;11: E -&gt; ( D + E ) .&quot;];
 12 [label = &quot;12: S&#x27; -&gt; E $ .&quot;];
 // Regular transitions
 start -&gt; 0;
 0 -&gt; 1 [label = &quot;ε&quot;];
 0 -&gt; 2 [label = &quot;ε&quot;];
 0 -&gt; 3 [label = &quot;ε&quot;];
 1 -&gt; 5 [label = &quot;(&quot;];
 2 -&gt; 3 [label = &quot;ε&quot;];
 3 -&gt; 6 [label = &quot;1&quot;];
 5 -&gt; 3 [label = &quot;ε&quot;];
 8 -&gt; 9 [label = &quot;+&quot;];
 9 -&gt; 1 [label = &quot;ε&quot;];
 9 -&gt; 2 [label = &quot;ε&quot;];
 9 -&gt; 3 [label = &quot;ε&quot;];
 10 -&gt; 11 [label = &quot;)&quot;];
 4 -&gt; 12 [label = &quot;$&quot;];
 // Nonterminal transitions (dashed)
 edge [style = dashed];
 0 -&gt; 4 [label = &quot;E&quot;];
 2 -&gt; 7 [label = &quot;D&quot;];
 5 -&gt; 8 [label = &quot;D&quot;];
 9 -&gt; 10 [label = &quot;E&quot;];
}
&#x27;&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Notice that this NFA is not complete. For example, what happens when `D := 1 .`
is complete? Then, the parse needs to transition to a state that has just
completed `D`. For example, `E := ( D . + E )` or `E := D .`. Here is how
it looks like.

<!--
############
__canvas__('''
 digraph LR0_Automaton {
  rankdir=TB;
  node [shape = rectangle];
  start [shape = point];
  // States
  0 [label = "0: S' -> . E"];
  1 [label = "1: E -> . ( D + E )"];
  2 [label = "2: E -> . D"];
  3 [label = "3: D -> . 1"];
  4 [label = "4: S' -> E . $"];
  5 [label = "5: E -> ( . D + E )"];
  6 [label = "6: D -> 1 ."];
  7 [label = "7: E -> D ."];
  8 [label = "8: E -> ( D . + E )"];
  9 [label = "9: E -> ( D + . E )"];
  10 [label = "10: E -> ( D + E . )"];
  11 [label = "11: E -> ( D + E ) ."];
  12 [label = "12: S' -> E $ ."];
  // Regular transitions
  start -> 0;
  0 -> 1 [label = "ε"];
  0 -> 2 [label = "ε"];
  0 -> 3 [label = "ε"];
  1 -> 5 [label = "("];
  2 -> 3 [label = "ε"];
  3 -> 6 [label = "1"];
  5 -> 3 [label = "ε"];
  8 -> 9 [label = "+"];
  9 -> 1 [label = "ε"];
  9 -> 2 [label = "ε"];
  9 -> 3 [label = "ε"];
  10 -> 11 [label = ")"];
  4 -> 12 [label = "$"];
  // Nonterminal transitions (dashed)
  edge [style = dashed];
  0 -> 4 [label = "E"];
  2 -> 7 [label = "D"];
  5 -> 8 [label = "D"];
  9 -> 10 [label = "E"];
  // Red arrows for completed rules
  edge [color = red, style = solid, constraint=false];
  6 -> 7 [label = "completion"];
  6 -> 8 [label = "completion"];  // Added this line
  11 -> 4 [label = "completion"];
  11 -> 10 [label = "completion"];
  7 -> 10 [label = "completion"];
  7 -> 4 [label = "completion"];
 }
 ''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
 digraph LR0_Automaton {
  rankdir=TB;
  node [shape = rectangle];
  start [shape = point];
  // States
  0 [label = &quot;0: S&#x27; -&gt; . E&quot;];
  1 [label = &quot;1: E -&gt; . ( D + E )&quot;];
  2 [label = &quot;2: E -&gt; . D&quot;];
  3 [label = &quot;3: D -&gt; . 1&quot;];
  4 [label = &quot;4: S&#x27; -&gt; E . $&quot;];
  5 [label = &quot;5: E -&gt; ( . D + E )&quot;];
  6 [label = &quot;6: D -&gt; 1 .&quot;];
  7 [label = &quot;7: E -&gt; D .&quot;];
  8 [label = &quot;8: E -&gt; ( D . + E )&quot;];
  9 [label = &quot;9: E -&gt; ( D + . E )&quot;];
  10 [label = &quot;10: E -&gt; ( D + E . )&quot;];
  11 [label = &quot;11: E -&gt; ( D + E ) .&quot;];
  12 [label = &quot;12: S&#x27; -&gt; E $ .&quot;];
  // Regular transitions
  start -&gt; 0;
  0 -&gt; 1 [label = &quot;ε&quot;];
  0 -&gt; 2 [label = &quot;ε&quot;];
  0 -&gt; 3 [label = &quot;ε&quot;];
  1 -&gt; 5 [label = &quot;(&quot;];
  2 -&gt; 3 [label = &quot;ε&quot;];
  3 -&gt; 6 [label = &quot;1&quot;];
  5 -&gt; 3 [label = &quot;ε&quot;];
  8 -&gt; 9 [label = &quot;+&quot;];
  9 -&gt; 1 [label = &quot;ε&quot;];
  9 -&gt; 2 [label = &quot;ε&quot;];
  9 -&gt; 3 [label = &quot;ε&quot;];
  10 -&gt; 11 [label = &quot;)&quot;];
  4 -&gt; 12 [label = &quot;$&quot;];
  // Nonterminal transitions (dashed)
  edge [style = dashed];
  0 -&gt; 4 [label = &quot;E&quot;];
  2 -&gt; 7 [label = &quot;D&quot;];
  5 -&gt; 8 [label = &quot;D&quot;];
  9 -&gt; 10 [label = &quot;E&quot;];
  // Red arrows for completed rules
  edge [color = red, style = solid, constraint=false];
  6 -&gt; 7 [label = &quot;completion&quot;];
  6 -&gt; 8 [label = &quot;completion&quot;];  // Added this line
  11 -&gt; 4 [label = &quot;completion&quot;];
  11 -&gt; 10 [label = &quot;completion&quot;];
  7 -&gt; 10 [label = &quot;completion&quot;];
  7 -&gt; 4 [label = &quot;completion&quot;];
 }
 &#x27;&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the dashed arrows represent non-terminal transitions that are
actually completed through other paths. The red arrows represent reductions.
You will notice that there can be multiple reductions from the same
item. At this point, this NFA over-approximates our grammar.
The right reduction needs to be chosen based on the prefix so far, and we
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
A sample grammar.

<!--
############
g1 = {
   '<E>': [
        ['(', '<D>', '+', '<E>', ')'],
        ['<D>']],
   '<D>': [
        ['1']]
}
g1_start = '<E>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
   &#x27;&lt;E&gt;&#x27;: [
        [&#x27;(&#x27;, &#x27;&lt;D&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;E&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;D&gt;&#x27;]],
   &#x27;&lt;D&gt;&#x27;: [
        [&#x27;1&#x27;]]
}
g1_start = &#x27;&lt;E&gt;&#x27;
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
s = State(g1a_start, ('<E>',), 0, 0)
print(s.at_dot())
print(str(s))
print(s.finished())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = State(g1a_start, (&#x27;&lt;E&gt;&#x27;,), 0, 0)
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
We can list the grammar production rules as follows:

<!--
############
i = 1
for k in g1a:
    for r in g1a[k]:
        print(i, k, r)
        i+=1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
i = 1
for k in g1a:
    for r in g1a[k]:
        print(i, k, r)
        i+=1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us use the grammar.

<!--
############
my_nfa = NFA(g1a, g1a_start)
st = my_nfa.create_start(g1a_start)
assert str(st[0]) == '<>::= | <E> $'
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == '<E>::= | ( <D> + <E> )'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(g1a, g1a_start)
st = my_nfa.create_start(g1a_start)
assert str(st[0]) == &#x27;&lt;&gt;::= | &lt;E&gt; $&#x27;
my_nfa = NFA(g1, g1_start)
st = my_nfa.create_start(g1_start)
assert str(st[0]) == &#x27;&lt;E&gt;::= | ( &lt;D&gt; + &lt;E&gt; )&#x27;
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
my_nfa = NFA(g1a, g1a_start)
st_ = my_nfa.create_start(g1a_start)
st = my_nfa.advance(st_[0])
assert str(st) == '<>::= <E> | $'
my_nfa = NFA(g1, g1_start)
st_ = my_nfa.create_start(g1_start)
st = [my_nfa.advance(s) for s in st_]
assert str(st[0]) == '<E>::= ( | <D> + <E> )'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(g1a, g1a_start)
st_ = my_nfa.create_start(g1a_start)
st = my_nfa.advance(st_[0])
assert str(st) == &#x27;&lt;&gt;::= &lt;E&gt; | $&#x27;
my_nfa = NFA(g1, g1_start)
st_ = my_nfa.create_start(g1_start)
st = [my_nfa.advance(s) for s in st_]
assert str(st[0]) == &#x27;&lt;E&gt;::= ( | &lt;D&gt; + &lt;E&gt; )&#x27;
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
Note that we are building an NFA. Hence, epsilon
transitions are allowed. This is what we use when we are
starting to parse nonterminal symbols. For example, when
we have a state with the parsing just before `<B>`, for e.g.
```
'<S>::= <A> | <B>'
```
Then, we add a new state
```
'<A>::= | a',
```
and connect this new state to the previous one with an $$\epsilon$$
transition.

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
Combining both procedures and processing the state itself for its transitions.
If the dot is before a symbol, then we add the transition to the
advanced state with that symbol as the transition. If the key at
the dot is a nonterminal, then add all expansions of that nonterminal
as epsilon transfers.

<!--
############
class NFA(NFA):
    def find_transitions(self, state):
        key = state.at_dot()
        if key is None: return [] # dot after last.
        new_states = []
        new_state = self.symbol_transition(state)
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            ns = self.epsilon_transitions(state)
            for s in ns: new_states.append(('', s))
        else: pass
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
        new_state = self.symbol_transition(state)
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            ns = self.epsilon_transitions(state)
            for s in ns: new_states.append((&#x27;&#x27;, s))
        else: pass
        return new_states
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
my_nfa = NFA(g1a, g1a_start)
st = my_nfa.create_start(g1a_start)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == "('<E>', (<>::= <E> | $ : 1))"
assert str(new_st[1]) == "('', (<E>::= | ( <D> + <E> ) : 2))"


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(g1a, g1a_start)
st = my_nfa.create_start(g1a_start)
new_st = my_nfa.find_transitions(st[0])
assert str(new_st[0]) == &quot;(&#x27;&lt;E&gt;&#x27;, (&lt;&gt;::= &lt;E&gt; | $ : 1))&quot;
assert str(new_st[1]) == &quot;(&#x27;&#x27;, (&lt;E&gt;::= | ( &lt;D&gt; + &lt;E&gt; ) : 2))&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Defining a utility method. This is only used to display the graph.
Given a key, we want to get all states where this key has just been parsed.
We use this method to identify where to go back to, after parsing a specific
key.

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
my_nfa = NFA(g1a, g1a_start)
lst = my_nfa.get_all_rules_with_dot_after_key('<D>')
assert str(lst) == '[(<E>::= ( <D> | + <E> ) : 0), (<E>::= <D> | : 1)]'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(g1a, g1a_start)
lst = my_nfa.get_all_rules_with_dot_after_key(&#x27;&lt;D&gt;&#x27;)
assert str(lst) == &#x27;[(&lt;E&gt;::= ( &lt;D&gt; | + &lt;E&gt; ) : 0), (&lt;E&gt;::= &lt;D&gt; | : 1)]&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### NFA build_nfa
We can now build the complete NFA.

<!--
############
class NFA(NFA):
    def build_table(self, num_states, columns, children):
        table = [{k:[] for k in columns} for _ in range(num_states)]
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in table[parent]: table[parent][key] = []
            v = prefix+str(child)
            if v not in table[parent][key]:
                table[parent][key].append(v)
        return table

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
        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + ['']),
                                self.children)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class NFA(NFA):
    def build_table(self, num_states, columns, children):
        table = [{k:[] for k in columns} for _ in range(num_states)]
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in children:
            if notes == &#x27;reduce&#x27;: prefix = &#x27;r:&#x27; # N not a state.
            elif notes == &#x27;shift&#x27;: prefix = &#x27;s&#x27;
            elif notes == &#x27;goto&#x27;: prefix = &#x27;g&#x27;
            elif notes == &#x27;to&#x27;: prefix = &#x27;t&#x27;
            if key not in table[parent]: table[parent][key] = []
            v = prefix+str(child)
            if v not in table[parent][key]:
                table[parent][key].append(v)
        return table

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
        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + [&#x27;&#x27;]),
                                self.children)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing the build_nfa

<!--
############
my_nfa = NFA(g1a, g1a_start)
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
my_nfa = NFA(g1a, g1a_start)
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
## Constructing a graph
To display the NFA (and DFAs) we need a graph. We construct this out of the
table we built previously.

<!--
############
def to_graph(table, lookup=lambda y: str(y)):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(table):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = 'rectangle'# rectangle, oval, diamond
        peripheries = '1'# rectangle, oval, diamond
        nodename = str(i)
        label = lookup(i)
        # if the state contains 'accept', then it is an accept state.
        for k in state:
            if  'accept' in state[k]: peripheries='2'
        G.add_node(pydot.Node(nodename,
                              label=label,
                              shape=shape,
                              peripheries=peripheries))
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = 'black'
            style='solid'
            if not transition: transition = "ε"
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = ''
                if state_name == 'accept':
                    continue
                elif state_name[0] == 'g':
                    color='blue'
                    transition_prefix = '' # '(g) '
                    style='dashed'
                elif state_name[0] == 'r':
                    # reduction is not a state transition.
                    # color='red'
                    # transition_prefix = '(r) '
                    continue
                elif state_name[0] == 't':
                    color='red'
                    transition = ''
                    transition_prefix = '' # '(t) '
                else:
                    assert state_name[0] == 's'
                    transition_prefix = '' #'(s) '
                G.add_edge(pydot.Edge(nodename,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_graph(table, lookup=lambda y: str(y)):
    G = pydot.Dot(&quot;my_graph&quot;, graph_type=&quot;digraph&quot;)
    for i, state in enumerate(table):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = &#x27;rectangle&#x27;# rectangle, oval, diamond
        peripheries = &#x27;1&#x27;# rectangle, oval, diamond
        nodename = str(i)
        label = lookup(i)
        # if the state contains &#x27;accept&#x27;, then it is an accept state.
        for k in state:
            if  &#x27;accept&#x27; in state[k]: peripheries=&#x27;2&#x27;
        G.add_node(pydot.Node(nodename,
                              label=label,
                              shape=shape,
                              peripheries=peripheries))
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = &#x27;black&#x27;
            style=&#x27;solid&#x27;
            if not transition: transition = &quot;ε&quot;
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = &#x27;&#x27;
                if state_name == &#x27;accept&#x27;:
                    continue
                elif state_name[0] == &#x27;g&#x27;:
                    color=&#x27;blue&#x27;
                    transition_prefix = &#x27;&#x27; # &#x27;(g) &#x27;
                    style=&#x27;dashed&#x27;
                elif state_name[0] == &#x27;r&#x27;:
                    # reduction is not a state transition.
                    # color=&#x27;red&#x27;
                    # transition_prefix = &#x27;(r) &#x27;
                    continue
                elif state_name[0] == &#x27;t&#x27;:
                    color=&#x27;red&#x27;
                    transition = &#x27;&#x27;
                    transition_prefix = &#x27;&#x27; # &#x27;(t) &#x27;
                else:
                    assert state_name[0] == &#x27;s&#x27;
                    transition_prefix = &#x27;&#x27; #&#x27;(s) &#x27;
                G.add_edge(pydot.Edge(nodename,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Viewing the NFA

<!--
############
my_nfa = NFA(g1a, g1a_start)
table = my_nfa.build_nfa()
for k in my_nfa.state_sids:
  print(k, my_nfa.state_sids[k])
def lookup(i):
    return str(i) + ": "+ str(my_nfa.state_sids[i])
g = to_graph(table, lookup)
__canvas__(str(g))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_nfa = NFA(g1a, g1a_start)
table = my_nfa.build_nfa()
for k in my_nfa.state_sids:
  print(k, my_nfa.state_sids[k])
def lookup(i):
    return str(i) + &quot;: &quot;+ str(my_nfa.state_sids[i])
g = to_graph(table, lookup)
__canvas__(str(g))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# LR0 Automata
An LR(0) automaton is composed of multiple states, and each state represents a set
of items that indicate the parsing progress. The states are connected together
using transitions which are composed of the terminal and nonterminal symbols
in the grammar.
To construct the LR(0) automaton, we start with the initial state containing the
augmented start symbol (if necessary), and we apply closure to expand the
context. For the closure, we simply merge all epsilon transitions to the current
item.
## Closure
A closure represents all possible parse paths at a given
point. The idea is to look at the current parse progress; Identify any
nonterminals that need to be expanded next, and add the production rules of that
nonterminal to the current item, with parse point (dot) at the beginning.
For example, given the first state, where `*` represent the parse progress
```
<S`> := * <E>
```
Applying closure, we expand `<E>` further.
```
<S`> := * <E>
<E>  := * ( <D> + <E> )
<D>  := * 1
```
No more nonterminals to expand. Hence, this is the closure of the first state.
Consider what happens when we apply a transition of `(` to this state.
```
<E> := ( * <D> + <E> )
<D> := * 1
```
This gives us the following graph with each closure, and the transitions indicated. Note that
the nonterminal transitions are dashed.

<!--
############
__canvas__('''
digraph my_graph {
0 [label="0\n<>::= . <E> $\n<E>::= . ( <D> + <E> )\n<E>::= . <D>\n<D>::= . 1", peripheries=1, shape=rectangle];
1 [label="1\n<E>::= ( . <D> + <E> )\n<D>::= . 1", peripheries=1, shape=rectangle];
2 [label="2\n<D>::= 1 .", peripheries=1, shape=rectangle];
3 [label="3\n<E>::= <D> .", peripheries=1, shape=rectangle];
4 [label="4\n<>::= <E> . $", peripheries=1, shape=rectangle];
5 [label="5\n<E>::= ( <D> . + <E> )", peripheries=1, shape=rectangle];
6 [label="6\n<>::= <E> $ .", peripheries=1, shape=rectangle];
7 [label="7\n<E>::= ( <D> + . <E> )\n<E>::= . ( <D> + <E> )\n<E>::= . <D>\n<D>::= . 1", peripheries=1, shape=rectangle];
8 [label="8\n<E>::= ( <D> + <E> . )", peripheries=1, shape=rectangle];
9 [label="9\n<E>::= ( <D> + <E> ) .", peripheries=1, shape=rectangle];

0 -> 1  [color=black, label="(s) (", style=solid];
0 -> 2  [color=black, label="(s) 1", style=solid];
0 -> 3  [color=blue, label="(g) <D>", style=dashed];
0 -> 4  [color=blue, label="(g) <E>", style=dashed];
1 -> 2  [color=black, label="(s) 1", style=solid];
1 -> 5  [color=blue, label="(g) <D>", style=dashed];
2 -> 3  [color=red, label="(t) ", style=solid];
2 -> 5  [color=red, label="(t) ", style=solid];
3 -> 4  [color=red, label="(t) ", style=solid];
4 -> 6  [color=black, label="(s) $", style=solid];
5 -> 7  [color=black, label="(s) +", style=solid];

7 -> 1  [color=black, label="(s) (", style=solid];
7 -> 2  [color=black, label="(s) 1", style=solid];
7 -> 3  [color=blue, label="(g) <D>", style=dashed];
7 -> 8  [color=blue, label="(g) <E>", style=dashed];
8 -> 9  [color=black, label="(s) )", style=solid];
9 -> 4  [color=red, label="(t) ", style=solid];
9 -> 8  [color=red, label="(t) ", style=solid];
}

           ''')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(&#x27;&#x27;&#x27;
digraph my_graph {
0 [label=&quot;0\n&lt;&gt;::= . &lt;E&gt; $\n&lt;E&gt;::= . ( &lt;D&gt; + &lt;E&gt; )\n&lt;E&gt;::= . &lt;D&gt;\n&lt;D&gt;::= . 1&quot;, peripheries=1, shape=rectangle];
1 [label=&quot;1\n&lt;E&gt;::= ( . &lt;D&gt; + &lt;E&gt; )\n&lt;D&gt;::= . 1&quot;, peripheries=1, shape=rectangle];
2 [label=&quot;2\n&lt;D&gt;::= 1 .&quot;, peripheries=1, shape=rectangle];
3 [label=&quot;3\n&lt;E&gt;::= &lt;D&gt; .&quot;, peripheries=1, shape=rectangle];
4 [label=&quot;4\n&lt;&gt;::= &lt;E&gt; . $&quot;, peripheries=1, shape=rectangle];
5 [label=&quot;5\n&lt;E&gt;::= ( &lt;D&gt; . + &lt;E&gt; )&quot;, peripheries=1, shape=rectangle];
6 [label=&quot;6\n&lt;&gt;::= &lt;E&gt; $ .&quot;, peripheries=1, shape=rectangle];
7 [label=&quot;7\n&lt;E&gt;::= ( &lt;D&gt; + . &lt;E&gt; )\n&lt;E&gt;::= . ( &lt;D&gt; + &lt;E&gt; )\n&lt;E&gt;::= . &lt;D&gt;\n&lt;D&gt;::= . 1&quot;, peripheries=1, shape=rectangle];
8 [label=&quot;8\n&lt;E&gt;::= ( &lt;D&gt; + &lt;E&gt; . )&quot;, peripheries=1, shape=rectangle];
9 [label=&quot;9\n&lt;E&gt;::= ( &lt;D&gt; + &lt;E&gt; ) .&quot;, peripheries=1, shape=rectangle];

0 -&gt; 1  [color=black, label=&quot;(s) (&quot;, style=solid];
0 -&gt; 2  [color=black, label=&quot;(s) 1&quot;, style=solid];
0 -&gt; 3  [color=blue, label=&quot;(g) &lt;D&gt;&quot;, style=dashed];
0 -&gt; 4  [color=blue, label=&quot;(g) &lt;E&gt;&quot;, style=dashed];
1 -&gt; 2  [color=black, label=&quot;(s) 1&quot;, style=solid];
1 -&gt; 5  [color=blue, label=&quot;(g) &lt;D&gt;&quot;, style=dashed];
2 -&gt; 3  [color=red, label=&quot;(t) &quot;, style=solid];
2 -&gt; 5  [color=red, label=&quot;(t) &quot;, style=solid];
3 -&gt; 4  [color=red, label=&quot;(t) &quot;, style=solid];
4 -&gt; 6  [color=black, label=&quot;(s) $&quot;, style=solid];
5 -&gt; 7  [color=black, label=&quot;(s) +&quot;, style=solid];

7 -&gt; 1  [color=black, label=&quot;(s) (&quot;, style=solid];
7 -&gt; 2  [color=black, label=&quot;(s) 1&quot;, style=solid];
7 -&gt; 3  [color=blue, label=&quot;(g) &lt;D&gt;&quot;, style=dashed];
7 -&gt; 8  [color=blue, label=&quot;(g) &lt;E&gt;&quot;, style=dashed];
8 -&gt; 9  [color=black, label=&quot;(s) )&quot;, style=solid];
9 -&gt; 4  [color=red, label=&quot;(t) &quot;, style=solid];
9 -&gt; 8  [color=red, label=&quot;(t) &quot;, style=solid];
}

           &#x27;&#x27;&#x27;)
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
### Compiling DFA States
So, how should we represent these states? If you look at state 0, it would
be possible to represent it as a procedure as below. We first save in to the
stack the current state, then extract the current symbol, and depending on
whether the symbol is one of the expected, we shift to the next state.
Note that we ignore the blue dashed arrows (nonterminal symbols) because
they were included just to indicate that the transition happens by another
path. Another note is that each state represents one row of the automation
table.
```
<>::= . <E> $
<E>::= . ( <D> + <E> ) 
<E>::= . <D> 
<D>::= . 1
```

<!--
############
def state_0(stack, input_string):
    stack.append(0)
    symbol = input_string[0]
    if symbol == '(': return state_1(stack, input_string[1:])
    elif symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '(' or '1'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_0(stack, input_string):
    stack.append(0)
    symbol = input_string[0]
    if symbol == &#x27;(&#x27;: return state_1(stack, input_string[1:])
    elif symbol == &#x27;1&#x27;: return state_2(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;(&#x27; or &#x27;1&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= ( . <D> + <E> )
<D>::= . 1
```

<!--
############
def state_1(stack, input_string):
    stack.append(1)
    symbol = input_string[0]
    if symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '1'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_1(stack, input_string):
    stack.append(1)
    symbol = input_string[0]
    if symbol == &#x27;1&#x27;: return state_2(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;1&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<D>::= 1 .
```
This is the first reduction state. In a reduction state, what we do is to
look at the stack if the corresponding rule was popped off the stack.
From a reduction state, we can transition to any state that has just
parsed the RHS (head) of the reduction.

<!--
############
def state_2(stack, input_string):
    stack.append(2)
    len_rule_rhs = 1 # D ::= 1
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_3(stack, input_string) # state0-<D>->state3
    if stack[-1] == 1: return state_5(stack, input_string) # state1-<D>->state5
    if stack[-1] == 7: return state_3(stack, input_string) # state7-<D>->state3
    else: raise Exception("Invalid state during reduction by D → 1")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_2(stack, input_string):
    stack.append(2)
    len_rule_rhs = 1 # D ::= 1
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_3(stack, input_string) # state0-&lt;D&gt;-&gt;state3
    if stack[-1] == 1: return state_5(stack, input_string) # state1-&lt;D&gt;-&gt;state5
    if stack[-1] == 7: return state_3(stack, input_string) # state7-&lt;D&gt;-&gt;state3
    else: raise Exception(&quot;Invalid state during reduction by D → 1&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= <D> .
```

<!--
############
def state_3(stack, input_string):
    stack.append(3)
    len_rule_rhs = 1 # E ::= D
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-<E>->state4
    if stack[-1] == 7: return state_8(stack, input_string) # state7-<E>->state8
    else: raise Exception("Invalid state during reduction by E → D")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_3(stack, input_string):
    stack.append(3)
    len_rule_rhs = 1 # E ::= D
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-&lt;E&gt;-&gt;state4
    if stack[-1] == 7: return state_8(stack, input_string) # state7-&lt;E&gt;-&gt;state8
    else: raise Exception(&quot;Invalid state during reduction by E → D&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<>::= <E> . $
```

<!--
############
def state_4(stack, input_string):
    stack.append(4)
    symbol = input_string[0]
    if symbol == '$': return state_6(stack, input_string[1:])
    else: raise Exception("Expected '$'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_4(stack, input_string):
    stack.append(4)
    symbol = input_string[0]
    if symbol == &#x27;$&#x27;: return state_6(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;$&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= ( <D> . + <E> )
```

<!--
############
def state_5(stack, input_string):
    stack.append(5)
    symbol = input_string[0]
    if symbol == '+': return state_7(stack, input_string[1:])
    else: raise Exception("Expected '+'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_5(stack, input_string):
    stack.append(5)
    symbol = input_string[0]
    if symbol == &#x27;+&#x27;: return state_7(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;+&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<>::= <E> $ .
```

<!--
############
def state_6(stack, input_string):
    stack.append(6)
    len_rule_rhs = 2 # <> ::= E $
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0:
        if input_string: raise Exception('Expected end of input')
        return True # Accept
    else: raise Exception("Invalid state during reduction by <> → E $")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_6(stack, input_string):
    stack.append(6)
    len_rule_rhs = 2 # &lt;&gt; ::= E $
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0:
        if input_string: raise Exception(&#x27;Expected end of input&#x27;)
        return True # Accept
    else: raise Exception(&quot;Invalid state during reduction by &lt;&gt; → E $&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= ( <D> + . <E> ) 
<E>::= . ( <D> + <E> ) 
<E>::= . <D>
<D>::= . 1
```

<!--
############
def state_7(stack, input_string):
    stack.append(7)
    symbol = input_string[0]
    if symbol == '(': return state_1(stack, input_string[1:])
    if symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '(' or '1'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_7(stack, input_string):
    stack.append(7)
    symbol = input_string[0]
    if symbol == &#x27;(&#x27;: return state_1(stack, input_string[1:])
    if symbol == &#x27;1&#x27;: return state_2(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;(&#x27; or &#x27;1&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= ( <D> + <E> . )
```

<!--
############
def state_8(stack, input_string):
    stack.append(8)
    symbol = input_string[0]
    if symbol == ')': return state_9(stack, input_string[1:])
    else: raise Exception("Expected ')'")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_8(stack, input_string):
    stack.append(8)
    symbol = input_string[0]
    if symbol == &#x27;)&#x27;: return state_9(stack, input_string[1:])
    else: raise Exception(&quot;Expected &#x27;)&#x27;&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
<E>::= ( <D> + <E> ) .
```

<!--
############
def state_9(stack, input_string):
    stack.append(9)
    len_rule_rhs = 5 # E ::= ( D + E )
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-<E>->state4
    else: raise Exception("Invalid state during reduction by E → ( D + E )")

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def state_9(stack, input_string):
    stack.append(9)
    len_rule_rhs = 5 # E ::= ( D + E )
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-&lt;E&gt;-&gt;state4
    else: raise Exception(&quot;Invalid state during reduction by E → ( D + E )&quot;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us now verify if our parser works.

<!--
############
test_strings = [("1", True), ("(1+1)", True), ("1+1", False), ("1+", False)]

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
test_strings = [(&quot;1&quot;, True), (&quot;(1+1)&quot;, True), (&quot;1+1&quot;, False), (&quot;1+&quot;, False)]

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
Note that while the above does not contain multiple reductions, it is possible
that a state can contain multiple reductions on more complex (e.g. LR(1))
grammars. But otherwise, the general parsing is as above.

## Building the DFA
Given a grammar, we will next consider how to build such a DFA.
For DFA, unlike an NFA, a state is no longer a single item. So, let us define
item separately.
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
        ['<>::= | <E> $',
         '<E>::= | ( <D> + <E> )', '<E>::= | <D>', '<D>::= | 1']

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
        [&#x27;&lt;&gt;::= | &lt;E&gt; $&#x27;,
         &#x27;&lt;E&gt;::= | ( &lt;D&gt; + &lt;E&gt; )&#x27;, &#x27;&lt;E&gt;::= | &lt;D&gt;&#x27;, &#x27;&lt;D&gt;::= | 1&#x27;]
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
st = my_dfa.advance(start, '<D>')
assert [str(s) for s in st] == ['<E>::= <D> |']

st = my_dfa.advance(start, '1')
assert [str(s) for s in st] == ['<D>::= 1 |']

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
start = my_dfa.create_start(g1a_start)
st = my_dfa.advance(start, &#x27;&lt;D&gt;&#x27;)
assert [str(s) for s in st] == [&#x27;&lt;E&gt;::= &lt;D&gt; |&#x27;]

st = my_dfa.advance(start, &#x27;1&#x27;)
assert [str(s) for s in st] == [&#x27;&lt;D&gt;::= 1 |&#x27;]
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
       ['<>::= | <E> $',
        '<E>::= | ( <D> + <E> )', '<E>::= | <D>', '<D>::= | 1']
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [('(', ['<E>::= ( | <D> + <E> )', '<D>::= | 1']),
         ('1', ['<D>::= 1 |']),
         ('<D>', ['<E>::= <D> |']),
         ('<E>', ['<>::= <E> | $'])]


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
st = my_dfa.create_start(g1a_start)
assert [str(s) for s in st.items] == \
       [&#x27;&lt;&gt;::= | &lt;E&gt; $&#x27;,
        &#x27;&lt;E&gt;::= | ( &lt;D&gt; + &lt;E&gt; )&#x27;, &#x27;&lt;E&gt;::= | &lt;D&gt;&#x27;, &#x27;&lt;D&gt;::= | 1&#x27;]
sts = my_dfa.find_transitions(st)
assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
        [(&#x27;(&#x27;, [&#x27;&lt;E&gt;::= ( | &lt;D&gt; + &lt;E&gt; )&#x27;, &#x27;&lt;D&gt;::= | 1&#x27;]),
         (&#x27;1&#x27;, [&#x27;&lt;D&gt;::= 1 |&#x27;]),
         (&#x27;&lt;D&gt;&#x27;, [&#x27;&lt;E&gt;::= &lt;D&gt; |&#x27;]),
         (&#x27;&lt;E&gt;&#x27;, [&#x27;&lt;&gt;::= &lt;E&gt; | $&#x27;])]
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

        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + ['']),
                                self.children)

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

        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + [&#x27;&#x27;]),
                                self.children)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test building the DFA.

<!--
############
my_dfa = LR0DFA(g1a, g1a_start)
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
my_dfa = LR0DFA(g1a, g1a_start)
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
def lookup(i):
    return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
g = to_graph(table, lookup)
__canvas__(str(g))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def lookup(i):
    return str(i) + &#x27;\n&#x27; + &#x27;\n&#x27;.join([str(k) for k in my_dfa.states[i].items])
g = to_graph(table, lookup)
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
my_dfa = LR0DFA(g1a, g1a_start)
parser = LR0Recognizer(my_dfa)
# Test the parser with some input strings
test_strings = ["(1+1)", "(1+(1+1))", "1", "1+", "+1+1"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message = parser.parse(test_string, g1a_start)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
parser = LR0Recognizer(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;(1+1)&quot;, &quot;(1+(1+1))&quot;, &quot;1&quot;, &quot;1+&quot;, &quot;+1+1&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message = parser.parse(test_string, g1a_start)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# LR0Parser
We'll next implement the LR(0) parser, which includes parse tree extraction.
Parse tree extraction involves building a tree structure that represents the
syntactic structure of the input string according to the grammar rules.

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
my_dfa = LR0DFA(g1a, g1a_start)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["(1+1)", "1", "(1+(1+1))", "+", "1+"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, g1a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR0DFA(g1a, g1a_start)
parser = LR0Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;(1+1)&quot;, &quot;1&quot;, &quot;(1+(1+1))&quot;, &quot;+&quot;, &quot;1+&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, g1a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Notice that we have used a quite simple grammar. For reference, this
was our `g1` grammar. 

```
E -> ( D + E )
E -> D
D -> 1
```

The interesting fact about this grammar was that
you could look at the current symbol, and decide which of these rules
to apply. That is, if the current symbol was `(` then rule 0 applies,
and if the symbol was `1`, then rule 1 applies.
What if you have a grammar where that is impossible?
Here is one such grammar

```
E -> D + E
E -> D
D -> 1
```

As you can see, it is no longer clear which rule of `<E>` to apply when we
have a `<D>` parsed. To decide on such cases, we need to go up one level
complexity.

<!--
############
g2 = {
        '<E>' :  [['<D>', '+', '<E>'],
                  ['<D>']],
        '<D>' :  [['1']]
        }
g2_start = '<E>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2 = {
        &#x27;&lt;E&gt;&#x27; :  [[&#x27;&lt;D&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;E&gt;&#x27;],
                  [&#x27;&lt;D&gt;&#x27;]],
        &#x27;&lt;D&gt;&#x27; :  [[&#x27;1&#x27;]]
        }
g2_start = &#x27;&lt;E&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us build the parse table.

<!--
############
g2a, g2a_start = add_start_state(g2, g2_start)
my_dfa = LR0DFA(g2a, g2a_start)
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
g2a, g2a_start = add_start_state(g2, g2_start)
my_dfa = LR0DFA(g2a, g2a_start)
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
As you can see, on State 2, we have two possible choices -- s4 and r:1.
This is called a shift/reduce conflict. The issue is that when we come to
state 2, that is.
```
 <E>::= <D> | + <E>
 <E>::= <D> |
```
We have two possible choices. We can either reduce to `<E>` or shift `+`.
To determine which one to act upon, we need a lookahead. If the
next token is `+`, then we should shift it to stack. If not,
we should reduce to `<E>`. This is what SLR parsers do.
# SLR1 Automata
SLR(1) parsers, or Simple LR(1) parsers, are an improvement over LR(0) parsers.
They use lookahead to resolve some conflicts that occur in LR(0) parsers.
A lookahead is the next token in the input that hasn't been processed yet.
By considering this lookahead token, SLR(1) parsers can make more informed
decisions about which production to use when reducing.
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
my_dfa = SLR1DFA(g2a, g2a_start)
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
my_dfa = SLR1DFA(g2a, g2a_start)
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
We can also view it as before.

<!--
############
def lookup(i):
    return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
g = to_graph(table, lookup)
__canvas__(str(g))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def lookup(i):
    return str(i) + &#x27;\n&#x27; + &#x27;\n&#x27;.join([str(k) for k in my_dfa.states[i].items])
g = to_graph(table, lookup)
__canvas__(str(g))
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
my_dfa = SLR1DFA(g2a, g2a_start)
parser = SLR1Parser(my_dfa)
# Test the parser with some input strings
test_strings = ["1+1", "1", "1+1+1"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, g2a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = SLR1DFA(g2a, g2a_start)
parser = SLR1Parser(my_dfa)
# Test the parser with some input strings
test_strings = [&quot;1+1&quot;, &quot;1&quot;, &quot;1+1+1&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, g2a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
But is this enough? Can we parse all useful grammars this way?
Consider this grammar.

```
S -> E + T
S -> T
E -> + T
E -> 1
T -> E
```

<!--
############
g3 = {
    '<S>': [['<E>', '+', '<T>'], ['<T>']],
    '<E>': [['+', '<T>'], ['1']],
    '<T>': [['<E>']]
}

g3_start = '<S>'


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g3 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;T&gt;&#x27;], [&#x27;&lt;T&gt;&#x27;]],
    &#x27;&lt;E&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;T&gt;&#x27;], [&#x27;1&#x27;]],
    &#x27;&lt;T&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;]]
}

g3_start = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see if it works.

<!--
############
g3a, g3a_start = add_start_state(g3, g3_start)
my_dfa = SLR1DFA(g3a, g3a_start)
table = my_dfa.build_dfa()

for k in my_dfa.production_rules:
    print(k, my_dfa.production_rules[k])

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
g3a, g3a_start = add_start_state(g3, g3_start)
my_dfa = SLR1DFA(g3a, g3a_start)
table = my_dfa.build_dfa()

for k in my_dfa.production_rules:
    print(k, my_dfa.production_rules[k])

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
You will notice a conflict in State 3.  ['s8', 'r:4']
The question is whether to shift `+`
and go to State 8, or to reduce with rule r:4.
To resolve this, we need the full LR(1) parser.
# LR1 Automata

LR(1) parsers, or Canonical LR(1) parsers, are the most powerful in the LR parser family.
They are needed when SLR(1) parsers are not sufficient to handle certain complex grammars.
LR(1) parsers differ from SLR(1) parsers in that they incorporate lookahead information
directly into the parser states, allowing for even more precise parsing decisions.

## Building the DFA
### LR1Item
The LR1 item is similar to the Item, except that it contains a lookahead.
This also is the most important difference between LR(0) and SLR(1) on one
hand and LR(1) on the other. SLR uses LR(0) items which mean exactly one item
per production rule + parse dot. However, in the case of LR(1) you can have
multiple items with the same LR(0) core--that is, production rule and parse
point--but with different lookahead. One may ask, what if use the LR(0) items
but add possible lookaheads as extra information to it? This gets you LALR(1).

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
        return self.show_dot(self.name, self.expr, self.dot) + ':' + self.lookahead

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
        return self.show_dot(self.name, self.expr, self.dot) + &#x27;:&#x27; + self.lookahead
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
The main difference is in computing the lookahead. 
The lines added and modified from LR0DFA are indicated in the procedure.

Here, say we are computing the closure of `A -> Alpha . <B> <Beta>`.
Remember that when we create new items for closure, we have to provide it with
a lookahead.

So, To compute the closure at `<B>`, we create items with lookahead which are
characters that can follow `<B>`. This need not be just the `first(<Beta>)`
but also what may follow `<Beta>` if `<Beta>` is nullable. This would be the
lookahead of the item `A -> Alpha . <B> <Beta>` which we already have, let us
say this is `l`. So, we compute `first(<Beta> l)` for lookahead.


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
                    new_item = self.create_start_item(key, rule, lookahead) # MODIFIED
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
                    new_item = self.create_start_item(key, rule, lookahead) # MODIFIED
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

**Note.** A possible confusion here is about the treatment of lookaheads,
in `add_reduction`. In LR0DFA.add_reduction, we add a reduction link for
all terminal symbols to each item. In SLR1DFA.add_reduction, we add a
reduction link for all terminal symbols that are in the `follow(item.name)`
Here, we may hence expect the lookaheads to be a subset of `follow(item.name)`
and to add the reduction for each lookahead of a given item.

The difference is in the LR1Item compared to Item, where LR1Item contains one
lookahead token per item. That is, there could be multiple items with same
parse points, corresponding to each possible lookahead. Since there is one
lookahead per LR1Item rather than multiple lookaheads per Item, we only need
to add one reduction per item.

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
Parsing

<!--
############
my_dfa = LR1DFA(g3a, g3a_start)

for k in my_dfa.production_rules:
    print(k, my_dfa.production_rules[k])

print()
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_dfa = LR1DFA(g3a, g3a_start)

for k in my_dfa.production_rules:
    print(k, my_dfa.production_rules[k])

print()
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can also view it as before.

<!--
############
def lookup(i):
    return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
table = parser.parse_table
g = to_graph(table, lookup)
__canvas__(str(g))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def lookup(i):
    return str(i) + &#x27;\n&#x27; + &#x27;\n&#x27;.join([str(k) for k in my_dfa.states[i].items])
table = parser.parse_table
g = to_graph(table, lookup)
__canvas__(str(g))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Test the parser with some input strings

<!--
############
test_strings = ["1", "1+1", "+1+1"]
for test_string in test_strings:
    print(f"Parsing: {test_string}")
    success, message, tree = parser.parse(test_string, g3a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f"Result: {'Accepted' if success else 'Rejected'}")
    print(f"Message: {message}")
    print()


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
test_strings = [&quot;1&quot;, &quot;1+1&quot;, &quot;+1+1&quot;]
for test_string in test_strings:
    print(f&quot;Parsing: {test_string}&quot;)
    success, message, tree = parser.parse(test_string, g3a_start)
    if tree is not None:
        ep.display_tree(tree)
    print(f&quot;Result: {&#x27;Accepted&#x27; if success else &#x27;Rejected&#x27;}&quot;)
    print(f&quot;Message: {message}&quot;)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Note:** The following resources helped me quite a bit in debugging. [SLR](https://jsmachines.sourceforge.net/machines/slr.html) and [LR](https://jsmachines.sourceforge.net/machines/lr1.html)

## References
[^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-07-01-lr-parsing.py).


