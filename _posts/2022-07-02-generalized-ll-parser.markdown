---
published: true
title: Generalized LL (GLL) Parser
layout: post
comments: true
tags: controlflow
categories: post
---
TLDR; This tutorial is a complete implementation of GLL Parser in Python
including SPPF parse tree extraction [^scott2013gll].
The Python interpreter is embedded so that you can work through the
implementation steps.
 
A GLL parser is a generalization of LL parsers. The first generalized LL
parser was reported by Grune and Jacob [^grune2008parsing] (11.2) from a
masters thesis report in 1993. However, a better known generalization
of LL parsing was described by Scott and Johnstone [^scott2010gll]. This
post follows the later parsing technique.
In this post, I provide a complete
implementation and a tutorial on how to implement a GLL parser in Python.
 
We [previously discussed](/post/2021/02/06/earley-parsing/) 
Earley parser which is a general context-free parser. GLL
parser is another general context-free parser that is capable of parsing
strings that conform to **any** given context-free grammar.
The algorithm is a generalization of the traditional recursive descent parsing
style. In traditional recursive descent parsing, the programmer uses the
call stack for keeping track of the parse context. This approach, however,
fails when there is left recursion. The problem is that recursive
descent parsers cannot advance the parsed index as it is not immediately
clear how many recursions are required to parse a given string. Bounding
of recursion as we [discussed before](/post/2020/03/17/recursive-descent-contextfree-parsing-with-left-recursion/)
is a reasonable solution. However, it is very inefficient.
  
GLL parsing offers a solution. The basic idea behind GLL parsing is to
maintain the call stack programmatically, which allows us to iteratively
deepen the parse for any nonterminal at any given point. This combined with
sharing of the stack (GSS) and generation of parse forest (SPPF) makes the
GLL parsing very efficient. Furthermore, unlike Earley, CYK, and GLR parsers,
GLL parser operates by producing a custom parser for a given grammar. This
means that one can actually debug the recursive descent parsing program
directly. Hence, using GLL can be much more friendly to the practitioner.
 
Similar to Earley, GLR, CYK, and other general context-free parsers, the worst
case for parsing is $$O(n^3)$$. However, for LL(1) grammars, the parse time
is $$O(n)$$.
 
## Synopsis
```python
import gllparser as P
my_grammar = {'<start>': [['1', '<A>'],
                          ['2']
                         ],
              '<A>'    : [['a']]}
my_parser = P.compile_grammar(my_grammar)
for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
    print(P.format_parsetree(tree))
```

## Definitons
For this post, we use the following terms:
 
* The _alphabet_ is the set all of symbols in the input language. For example,
  in this post, we use all ASCII characters as alphabet.

* A _terminal_ is a single alphabet symbol. Note that this is slightly different
  from usual definitions (done here for ease of parsing). (Usually a terminal is
  a contiguous sequence of symbols from the alphabet. However, both kinds of
  grammars have a one to one correspondence, and can be converted easily.)

  For example, `x` is a terminal symbol.

* A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
  in the grammar using _rules_ for expansion.

  For example, `<term>` is a nonterminal in the below grammar.

* A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
  nonterminals) that describe an expansion of a given terminal.

  For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.

* A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.

  For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the nonterminal `<digits>`

* A _context-free grammar_ is  composed of a set of nonterminals and 
  corresponding definitions that define the structure of the nonterminal.

  The grammar given below is an example context-free grammar.
 
* A terminal _derives_ a string if the string contains only the symbols in the
  terminal. A nonterminal derives a string if the corresponding definition
  derives the string. A definition derives the  string if one of the rules in
  the definition derives the string. A rule derives a string if the sequence
  of terms that make up the rule can derive the string, deriving one substring 
  after another contiguously (also called parsing).

* A *derivation tree* is an ordered tree that describes how an input string is
  derived by the given start symbol. Also called a *parse tree*.
* A derivation tree can be collapsed into its string equivalent. Such a string
  can be parsed again by the nonterminal at the root node of the derivation
  tree such that at least one of the resulting derivation trees would be the
  same as the one we started with.

* The *yield* of a tree is the string resulting from collapsing that tree.


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
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
We need the fuzzer to generate inputs to parse and also to provide some
utilities

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
As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
Here is an example grammar for arithmetic expressions, starting at `<start>`.
A terminal symbol has exactly one character
(Note that we disallow empty string (`''`) as a terminal symbol).
Secondly, as per traditional implementations,
there can only be one expansion rule for the `<start>` symbol. We work around
this restriction by simply constructing as many charts as there are expansion
rules, and returning all parse trees.

**Note:** This post is not complete. Given the interest in GLL parsers, I am
simply providing the complete source (which substantially follows the
publications, except where I have simplified things a little bit)
until I have more bandwidth to complete the tutorial. However, the code
itself is complete, and can be used.
## Our grammar

<!--
############
grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [
        [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Defining the start symbol

<!--
############
START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Utilities.
We start with a few utilities.
### show_dot()
We often have to display a partial parse of a rule. We use `@` to indicate
until where the current rule has parsed.

<!--
############
def show_dot(g, t):
    sym, n_alt, pos = t
    rule = g[sym][n_alt]
    return sym + '::=' + ' '.join(rule[0:pos]) + ' @ ' + ' '.join(rule[pos:])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def show_dot(g, t):
    sym, n_alt, pos = t
    rule = g[sym][n_alt]
    return sym + &#x27;::=&#x27; + &#x27; &#x27;.join(rule[0:pos]) + &#x27; @ &#x27; + &#x27; &#x27;.join(rule[pos:])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it:

<!--
############
print(show_dot(grammar, ('<fact>', 1, 1)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(show_dot(grammar, (&#x27;&lt;fact&gt;&#x27;, 1, 1)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need first and nullable

Here is a nullable grammar

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
Here is a standard algorithm to compute first, follow and nullable sets

<!--
############
def symbols(grammar):
    terminals, nonterminals = [], []
    for k in grammar:
        for r in grammar[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    nonterminals.append(t)
                else:
                    terminals.append(t)
    return (sorted(list(set(terminals))), sorted(list(set(nonterminals))))

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

def get_beta_first(rule, dot, first, follow, nullable):
    alpha = rule[:dot]
    beta = rule[dot:]
    fst = []
    for t in beta:
        if fuzzer.is_terminal(t):
            fst.append(t)
            break
        else:
            fst.extend(first[t])
            if t not in nullable:
                break
            else:
                continue
    return sorted(list(set(fst)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def symbols(grammar):
    terminals, nonterminals = [], []
    for k in grammar:
        for r in grammar[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    nonterminals.append(t)
                else:
                    terminals.append(t)
    return (sorted(list(set(terminals))), sorted(list(set(nonterminals))))

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

def get_beta_first(rule, dot, first, follow, nullable):
    alpha = rule[:dot]
    beta = rule[dot:]
    fst = []
    for t in beta:
        if fuzzer.is_terminal(t):
            fst.append(t)
            break
        else:
            fst.extend(first[t])
            if t not in nullable:
                break
            else:
                continue
    return sorted(list(set(fst)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
first, follow, nullable = get_first_and_follow(nullable_grammar)
print(first)
print(follow)
print(nullable)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
first, follow, nullable = get_first_and_follow(nullable_grammar)
print(first)
print(follow)
print(nullable)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
another

<!--
############
first, follow, nullable = get_first_and_follow(grammar)
print(first)
print(follow)
print(nullable)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
first, follow, nullable = get_first_and_follow(grammar)
print(first)
print(follow)
print(nullable)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The GSS Graph
A naive conversion of recursive descent parsing to generalized recursive
descent parsing can be done by maintaining independent stacks for each thread.
However, this approach is very costly. GLL optimizes what it needs to generate
by using a Graph-Structured Stack.
The idea is to share as much of the stack during parsing as possible.

### The GSS Node
A GSS node is simply a node that can contain any number of children. Each
child is actually an edge in the graph.

(Each GSS Node is of the form $$L_i^j$$ where $$j$$ is the index of the
character consumed. However, we do not need to know the internals of the label
here).

<!--
############
class GSSNode:
    def __init__(self, label): self.label, self.children = label, []
    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GSSNode:
    def __init__(self, label): self.label, self.children = label, []
    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The GSS container
Next, we define the graph container. We keep two structures. self.graph which
is the shared stack, and  P which is the set of labels that went through a
`fn_return`, i.e. `pop` operation.

<!--
############
class GSS:
    def __init__(self): self.graph, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.graph:
            self.graph[my_label], self.P[my_label] = GSSNode(my_label), []
        return self.graph[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        return self.P[label]

    def __repr__(self): return str(self.graph)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GSS:
    def __init__(self): self.graph, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.graph:
            self.graph[my_label], self.P[my_label] = GSSNode(my_label), []
        return self.graph[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        return self.P[label]

    def __repr__(self): return str(self.graph)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## SPPF Graph
To ensure that we can actually extract the parsed trees, we use 
the Shared Packed Parse Forest datastructure to represent parses.
### SPPF Node

<!--
############
class SPPFNode:
    def __init__(self): self.children, self.label = [], '<None>'

    def __eq__(self, o): return self.label == o.label

    def add_child(self, child): self.children.append(child)

    def to_s(self, g): return self.label[0]

    def __repr__(self): return 'SPPF:%s' % str(self.label)

    def to_tree(self, hmap, tab): raise NotImplemented

    def to_tree_(self, hmap, tab):
        key = self.label[0] # ignored
        ret = []
        for n in self.children:
            v = n.to_tree_(hmap, tab+1)
            ret.extend(v)
        return ret


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPFNode:
    def __init__(self): self.children, self.label = [], &#x27;&lt;None&gt;&#x27;

    def __eq__(self, o): return self.label == o.label

    def add_child(self, child): self.children.append(child)

    def to_s(self, g): return self.label[0]

    def __repr__(self): return &#x27;SPPF:%s&#x27; % str(self.label)

    def to_tree(self, hmap, tab): raise NotImplemented

    def to_tree_(self, hmap, tab):
        key = self.label[0] # ignored
        ret = []
        for n in self.children:
            v = n.to_tree_(hmap, tab+1)
            ret.extend(v)
        return ret
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Dummy Node
The dummy SPPF node is used to indicate the empty node at the end of rules.

<!--
############
class SPPF_dummy_node(SPPFNode):
    def __init__(self, s, j, i): self.label, self.children = (s, j, i), []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_dummy_node(SPPFNode):
    def __init__(self, s, j, i): self.label, self.children = (s, j, i), []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Symbol Node
x is a terminal, nonterminal, or epsilon -- ''
j and i are the extents.
Each symbol can contain multiple packed nodes each
representing a different derivation. See getNodeP

<!--
############
class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i): self.label, self.children = (x, j, i), []

    def to_tree(self, hmap, tab): return self.to_tree_(hmap, tab)[0]

    # **Note.** In the presence of ambiguous parsing, we choose a derivation
    # at random. So, run the `to_tree()` multiple times to get all parse
    # trees. If you want a better solution, see the
    # [forest generation in earley parser](/post/2021/02/06/earley-parsing/)
    # which can be adapted here too.
    def to_tree_(self, hmap, tab):
        key = self.label[0]
        if self.children:
            n = random.choice(self.children)
            return [[key, n.to_tree_(hmap, tab+1)]]
        return [[key, []]]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i): self.label, self.children = (x, j, i), []

    def to_tree(self, hmap, tab): return self.to_tree_(hmap, tab)[0]

    # **Note.** In the presence of ambiguous parsing, we choose a derivation
    # at random. So, run the `to_tree()` multiple times to get all parse
    # trees. If you want a better solution, see the
    # [forest generation in earley parser](/post/2021/02/06/earley-parsing/)
    # which can be adapted here too.
    def to_tree_(self, hmap, tab):
        key = self.label[0]
        if self.children:
            n = random.choice(self.children)
            return [[key, n.to_tree_(hmap, tab+1)]]
        return [[key, []]]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Intermediate Node
Has only two children max (or 1 child).

<!--
############
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i): self.label, self.children = (t, j, i), []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i): self.label, self.children = (t, j, i), []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Packed Node

<!--
############
class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k): self.label, self.children = (t,k), []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k): self.label, self.children = (t,k), []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The GLL parser
We can now build our GLL parser.
We first define our initialization

<!--
############
class GLLStructuredStackP:
    def initialize(self, input_str):
        self.I = input_str + '$'
        self.m = len(input_str)
        self.gss = GSS()
        self.stack_bottom = self.gss.get(('L0', 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)] # descriptors for each index
        self.SPPF_nodes = {}


    def to_tree(self):
        return self.SPPF_nodes[self.root].to_tree(self.SPPF_nodes, tab=0)

    def set_grammar(self, g):
        self.grammar = g
        self.first, self.follow, self.nullable = get_first_and_follow(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP:
    def initialize(self, input_str):
        self.I = input_str + &#x27;$&#x27;
        self.m = len(input_str)
        self.gss = GSS()
        self.stack_bottom = self.gss.get((&#x27;L0&#x27;, 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)] # descriptors for each index
        self.SPPF_nodes = {}


    def to_tree(self):
        return self.SPPF_nodes[self.root].to_tree(self.SPPF_nodes, tab=0)

    def set_grammar(self, g):
        self.grammar = g
        self.first, self.follow, self.nullable = get_first_and_follow(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL add thread (add)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, stack_top, cur_idx, sppf_w):
        if (L, stack_top, sppf_w) not in self.U[cur_idx]:
            self.U[cur_idx].append((L, stack_top, sppf_w))
            self.threads.append((L, stack_top, cur_idx, sppf_w))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, stack_top, cur_idx, sppf_w):
        if (L, stack_top, sppf_w) not in self.U[cur_idx]:
            self.U[cur_idx].append((L, stack_top, sppf_w))
            self.threads.append((L, stack_top, cur_idx, sppf_w))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL fn_return (pop)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, stack_top, cur_idx, sppf_z):
        if stack_top != self.stack_bottom:
            (L, _k) = stack_top.label
            self.gss.add_parsed_index(stack_top.label, sppf_z)
            for c_st,sppf_w in stack_top.children:
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                self.add_thread(L, c_st, cur_idx, sppf_y)
        return stack_top

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, stack_top, cur_idx, sppf_z):
        if stack_top != self.stack_bottom:
            (L, _k) = stack_top.label
            self.gss.add_parsed_index(stack_top.label, sppf_z)
            for c_st,sppf_w in stack_top.children:
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                self.add_thread(L, c_st, cur_idx, sppf_y)
        return stack_top
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL register_return (create)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, stack_top, cur_idx, sppf_w): # returns to stack_top
        v = self.gss.get((L, cur_idx)) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        v_to_u_labeled_w = [c for c,lbl in v.children
                            if c.label == stack_top.label and lbl == sppf_w]
        if not v_to_u_labeled_w:
            v.children.append((stack_top, sppf_w))

            for sppf_z in self.gss.parsed_indexes(v.label):
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                h_idx = sppf_z.label[-1] # right extent
                self.add_thread(v.L, stack_top, h_idx, sppf_y) # v.L == L
        return v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, stack_top, cur_idx, sppf_w): # returns to stack_top
        v = self.gss.get((L, cur_idx)) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        v_to_u_labeled_w = [c for c,lbl in v.children
                            if c.label == stack_top.label and lbl == sppf_w]
        if not v_to_u_labeled_w:
            v.children.append((stack_top, sppf_w))

            for sppf_z in self.gss.parsed_indexes(v.label):
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                h_idx = sppf_z.label[-1] # right extent
                self.add_thread(v.L, stack_top, h_idx, sppf_y) # v.L == L
        return v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL utilities.

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def next_thread(self): # i \in R
        t, *self.threads = self.threads
        return t

    def sppf_find_or_create(self, label, j, i):
        n = (label, j, i)
        if  n not in self.SPPF_nodes:
            node = None
            if label is None:            node = SPPF_dummy_node(*n)
            elif isinstance(label, str): node = SPPF_symbol_node(*n)
            else:                        node = SPPF_intermediate_node(*n)
            self.SPPF_nodes[n] = node
        return self.SPPF_nodes[n]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def next_thread(self): # i \in R
        t, *self.threads = self.threads
        return t

    def sppf_find_or_create(self, label, j, i):
        n = (label, j, i)
        if  n not in self.SPPF_nodes:
            node = None
            if label is None:            node = SPPF_dummy_node(*n)
            elif isinstance(label, str): node = SPPF_symbol_node(*n)
            else:                        node = SPPF_intermediate_node(*n)
            self.SPPF_nodes[n] = node
        return self.SPPF_nodes[n]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need the to produce SPPF nodes correctly.

`getNode(x, i)` creates and returns an SPPF node labeled `(x, i, i+1)` or
`(epsilon, i, i)` if x is epsilon

`getNodeP(X::= alpha.beta, w, z)` takes a grammar slot `X ::= alpha . beta`
and two SPPF nodes w, and z (z may be dummy node $).
the nodes w and z are not packed nodes, and will have labels of form
`(s, j, k)` and `(r, k, i)`

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def not_dummy(self, sppf_w):
        if sppf_w.label[0] == '$':
            assert isinstance(sppf_w, SPPF_dummy_node)
            return False
        assert not isinstance(sppf_w, SPPF_dummy_node)
        return True

    def getNodeT(self, x, i):
        j = i if x is None else i+1
        return self.sppf_find_or_create(x, i, j)

    def getNodeP(self, X_rule_pos, sppf_w, sppf_z):
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha, beta = rule[:dot], rule[dot:]

        if self.is_non_nullable_alpha(alpha) and beta: return sppf_z

        t = X if beta == [] else X_rule_pos

        _q, k, i = sppf_z.label
        if self.not_dummy(sppf_w):
            _s,j,_k = sppf_w.label # assert k == _k
            children = [sppf_w,sppf_z]
        else:
            j = k
            children = [sppf_z]

        y = self.sppf_find_or_create(t, j, i)
        if not [c for c in y.children if c.label == (X_rule_pos, k)]:
            pn = SPPF_packed_node(X_rule_pos, k)
            for c_ in children: pn.add_child(c_)
            y.add_child(pn)
        return y

    def is_non_nullable_alpha(self, alpha):
        if not alpha: return False
        if len(alpha) != 1: return False
        if fuzzer.is_terminal(alpha[0]): return True
        if alpha[0] in self.nullable: return False
        return True

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def not_dummy(self, sppf_w):
        if sppf_w.label[0] == &#x27;$&#x27;:
            assert isinstance(sppf_w, SPPF_dummy_node)
            return False
        assert not isinstance(sppf_w, SPPF_dummy_node)
        return True

    def getNodeT(self, x, i):
        j = i if x is None else i+1
        return self.sppf_find_or_create(x, i, j)

    def getNodeP(self, X_rule_pos, sppf_w, sppf_z):
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha, beta = rule[:dot], rule[dot:]

        if self.is_non_nullable_alpha(alpha) and beta: return sppf_z

        t = X if beta == [] else X_rule_pos

        _q, k, i = sppf_z.label
        if self.not_dummy(sppf_w):
            _s,j,_k = sppf_w.label # assert k == _k
            children = [sppf_w,sppf_z]
        else:
            j = k
            children = [sppf_z]

        y = self.sppf_find_or_create(t, j, i)
        if not [c for c in y.children if c.label == (X_rule_pos, k)]:
            pn = SPPF_packed_node(X_rule_pos, k)
            for c_ in children: pn.add_child(c_)
            y.add_child(pn)
        return y

    def is_non_nullable_alpha(self, alpha):
        if not alpha: return False
        if len(alpha) != 1: return False
        if fuzzer.is_terminal(alpha[0]): return True
        if alpha[0] in self.nullable: return False
        return True
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Building the parser with GLL
At this point, we are ready to build our parser.
### Compiling an empty rule
We start with compiling an epsilon rule.

<!--
############
def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            right_sppf_child = parser.getNodeT(None, cur_idx)
            cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            L = 'L_'
            continue
''' % (key, n_alt,show_dot(g, (key, n_alt, 0)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_epsilon(g, key, n_alt):
    return &#x27;&#x27;&#x27;\
        elif L == (&quot;%s&quot;, %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            right_sppf_child = parser.getNodeT(None, cur_idx)
            cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            L = &#x27;L_&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt,show_dot(g, (key, n_alt, 0)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
v = compile_epsilon(grammar, '<expr>', 1)
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = compile_epsilon(grammar, &#x27;&lt;expr&gt;&#x27;, 1)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Compiling a Terminal Symbol

<!--
############
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[cur_idx] == '%s':
                right_sppf_child = parser.getNodeT(parser.I[cur_idx], cur_idx)
                cur_idx = cur_idx+1
                L = %s
                cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), token, Lnxt)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = &#x27;&quot;L_&quot;&#x27;
    else:
        Lnxt = &#x27;(&quot;%s&quot;,%d,%d)&#x27; % (key, n_alt, r_pos+1)
    return &#x27;&#x27;&#x27;\
        elif L == (&quot;%s&quot;,%d,%d): # %s
            if parser.I[cur_idx] == &#x27;%s&#x27;:
                right_sppf_child = parser.getNodeT(parser.I[cur_idx], cur_idx)
                cur_idx = cur_idx+1
                L = %s
                cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            else:
                L = &#x27;L0&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), token, Lnxt)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Compiling a Nonterminal Symbol

<!--
############
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, cur_idx, cur_sppf_node)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), Lnxt, token)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = &#x27;&quot;L_&quot;&#x27;
    else:
        Lnxt = &quot;(&#x27;%s&#x27;,%d,%d)&quot; % (key, n_alt, r_pos+1)
    return &#x27;&#x27;&#x27;\
        elif L ==  (&#x27;%s&#x27;,%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, cur_idx, cur_sppf_node)
            L = &quot;%s&quot;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), Lnxt, token)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
rule = grammar['<expr>'][1]
for i, t in enumerate(rule):
    if fuzzer.is_nonterminal(t):
        v = compile_nonterminal(grammar, '<expr>', 1, i, len(rule), t)
    else:
        v = compile_terminal(grammar, '<expr>', 1, i, len(rule), t)
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rule = grammar[&#x27;&lt;expr&gt;&#x27;][1]
for i, t in enumerate(rule):
    if fuzzer.is_nonterminal(t):
        v = compile_nonterminal(grammar, &#x27;&lt;expr&gt;&#x27;, 1, i, len(rule), t)
    else:
        v = compile_terminal(grammar, &#x27;&lt;expr&gt;&#x27;, 1, i, len(rule), t)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Compiling a Rule
`n_alt` is the position of `rule`.

<!--
############
def compile_rule(g, key, n_alt, rule):
    res = []
    if not rule:
        r = compile_epsilon(g, key, n_alt)
        res.append(r)
    else:
        for i, t in enumerate(rule):
            if fuzzer.is_nonterminal(t):
                r = compile_nonterminal(g, key, n_alt, i, len(rule), t)
            else:
                r = compile_terminal(g, key, n_alt, i, len(rule), t)
            res.append(r)
        # if epsilon present, we do not want this branch.
        res.append('''\
        elif L == ('%s',%d,%d): # %s
            L = 'L_'
            continue
''' % (key, n_alt, len(rule), show_dot(g, (key, n_alt, len(rule)))))
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_rule(g, key, n_alt, rule):
    res = []
    if not rule:
        r = compile_epsilon(g, key, n_alt)
        res.append(r)
    else:
        for i, t in enumerate(rule):
            if fuzzer.is_nonterminal(t):
                r = compile_nonterminal(g, key, n_alt, i, len(rule), t)
            else:
                r = compile_terminal(g, key, n_alt, i, len(rule), t)
            res.append(r)
        # if epsilon present, we do not want this branch.
        res.append(&#x27;&#x27;&#x27;\
        elif L == (&#x27;%s&#x27;,%d,%d): # %s
            L = &#x27;L_&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, len(rule), show_dot(g, (key, n_alt, len(rule)))))
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
v = compile_rule(grammar, '<expr>', 1, grammar['<expr>'][1])
print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = compile_rule(grammar, &#x27;&lt;expr&gt;&#x27;, 1, grammar[&#x27;&lt;expr&gt;&#x27;][1])
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Compiling a Definition
Note that if performance is important, you may want to check if the current
input symbol at `parser.I[cur_idx]` is part of the following, where X is a
nonterminal and p is a rule fragment. Note that if you care about the
performance, you will want to precompute first[p] for each rule fragment
`rule[j:]` in the grammar, and first and follow sets for each symbol in the
grammar. This should be checked before `parser.add_thread`.

<!--
############
def test_select(a, X, p, rule_first, follow):
    if a in rule_first[p]: return True
    if '' not in rule_first[p]: return False
    return a in follow[X]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def test_select(a, X, p, rule_first, follow):
    if a in rule_first[p]: return True
    if &#x27;&#x27; not in rule_first[p]: return False
    return a in follow[X]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given that removing this check does not affect the correctness of the
algorithm, I have chosen not to add it.

<!--
############
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # %s
            parser.add_thread( ('%s',%d,0), stack_top, cur_idx, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt, rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_def(g, key, definition):
    res = []
    res.append(&#x27;&#x27;&#x27;\
        elif L == &#x27;%s&#x27;:
&#x27;&#x27;&#x27; % key)
    for n_alt,rule in enumerate(definition):
        res.append(&#x27;&#x27;&#x27;\
            # %s
            parser.add_thread( (&#x27;%s&#x27;,%d,0), stack_top, cur_idx, end_rule)&#x27;&#x27;&#x27; % (key + &#x27;::=&#x27; + str(rule), key, n_alt))
    res.append(&#x27;&#x27;&#x27;
            L = &#x27;L0&#x27;
            continue&#x27;&#x27;&#x27;)
    for n_alt, rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
v = compile_def(grammar, '<expr>', grammar['<expr>'])
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = compile_def(grammar, &#x27;&lt;expr&gt;&#x27;, grammar[&#x27;&lt;expr&gt;&#x27;])
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A template.

<!--
############
class GLLParser(ep.Parser):
    def recognize_on(self, text, start_symbol):
        raise NotImplemented()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLParser(ep.Parser):
    def recognize_on(self, text, start_symbol):
        raise NotImplemented()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Compiling a Grammar

<!--
############
def compile_grammar(g, evaluate=True):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = ['''\
def recognize_on(self, text, start_symbol):
    parser = self.parser
    parser.initialize(text)
    parser.set_grammar(
%s
    )
    # L contains start nt.
    end_rule = SPPF_dummy_node('$', 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = start_symbol, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                # goto L
                continue
            else:
                # if there is an SPPF node (start_symbol, 0, m) then report success
                if (start_symbol, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (start_symbol, 0, parser.m)
                      return parser
                else: return []
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = 'L0' # goto L_0
            continue
    ''' % pp.pformat(g)]
    for k in g:
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    res.append('''
def parse_on(self, text, start_symbol):
    p = self.recognize_on(text, start_symbol)
    return [p.to_tree()]
    ''')

    parse_src = '\n'.join(res)
    s = GLLParser()
    s.src = parse_src
    if not evaluate: return parse_src
    l, g = locals().copy(), globals().copy()
    exec(parse_src, g, l)
    s.parser = GLLStructuredStackP()
    s.recognize_on = l['recognize_on'].__get__(s)
    s.parse_on = l['parse_on'].__get__(s)
    return s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_grammar(g, evaluate=True):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = [&#x27;&#x27;&#x27;\
def recognize_on(self, text, start_symbol):
    parser = self.parser
    parser.initialize(text)
    parser.set_grammar(
%s
    )
    # L contains start nt.
    end_rule = SPPF_dummy_node(&#x27;$&#x27;, 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = start_symbol, parser.stack_bottom, 0, end_rule
    while True:
        if L == &#x27;L0&#x27;:
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                # goto L
                continue
            else:
                # if there is an SPPF node (start_symbol, 0, m) then report success
                if (start_symbol, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (start_symbol, 0, parser.m)
                      return parser
                else: return []
        elif L == &#x27;L_&#x27;:
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = &#x27;L0&#x27; # goto L_0
            continue
    &#x27;&#x27;&#x27; % pp.pformat(g)]
    for k in g:
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append(&#x27;&#x27;&#x27;
        else:
            assert False&#x27;&#x27;&#x27;)
    res.append(&#x27;&#x27;&#x27;
def parse_on(self, text, start_symbol):
    p = self.recognize_on(text, start_symbol)
    return [p.to_tree()]
    &#x27;&#x27;&#x27;)

    parse_src = &#x27;\n&#x27;.join(res)
    s = GLLParser()
    s.src = parse_src
    if not evaluate: return parse_src
    l, g = locals().copy(), globals().copy()
    exec(parse_src, g, l)
    s.parser = GLLStructuredStackP()
    s.recognize_on = l[&#x27;recognize_on&#x27;].__get__(s)
    s.parse_on = l[&#x27;parse_on&#x27;].__get__(s)
    return s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
v = compile_grammar(grammar, False)
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = compile_grammar(grammar, False)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Running it
### 1

<!--
############
G1 = {
    '<S>': [['c']]
}
mystring = 'c'
p = compile_grammar(G1)
v = p.parse_on(mystring, '<S>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G1 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;]]
}
mystring = &#x27;c&#x27;
p = compile_grammar(G1)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### 2

<!--
############
G2 = {
    '<S>': [['c', 'c']]
}
mystring = 'cc'
p = compile_grammar(G2)
v = p.parse_on(mystring, '<S>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G2 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;, &#x27;c&#x27;]]
}
mystring = &#x27;cc&#x27;
p = compile_grammar(G2)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### 3

<!--
############
G3 = {
    '<S>': [['c', 'c', 'c']]
}
mystring = 'ccc'
p = compile_grammar(G3)
v = p.parse_on(mystring, '<S>')[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G3 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;, &#x27;c&#x27;, &#x27;c&#x27;]]
}
mystring = &#x27;ccc&#x27;
p = compile_grammar(G3)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### 4

<!--
############
G4 = {
    '<S>': [['c'],
            ['a']]
}
mystring = 'a'
p = compile_grammar(G4)
v = p.parse_on(mystring, '<S>')[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G4 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;],
            [&#x27;a&#x27;]]
}
mystring = &#x27;a&#x27;
p = compile_grammar(G4)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### 5

<!--
############
G5 = {
    '<S>': [['<A>']],
    '<A>': [['a']]
}
mystring = 'a'
p = compile_grammar(G5)
v = p.parse_on(mystring, '<S>')[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G5 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;]]
}
mystring = &#x27;a&#x27;
p = compile_grammar(G5)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Expression
### 1

<!--
############
mystring = '(1+1)*(23/45)-1'
p = compile_grammar(grammar)
v = p.parse_on(mystring, START)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;(1+1)*(23/45)-1&#x27;
p = compile_grammar(grammar)
v = p.parse_on(mystring, START)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### 2
Since we use a random choice to get different parse trees in ambiguity, click
the run button again and again to get different parses.

<!--
############
a_grammar = {
'<start>': [['<expr>']],
'<expr>': [
    ['<expr>', '+', '<expr>'],
    ['<expr>', '-', '<expr>'],
    ['<expr>', '*', '<expr>'],
    ['<expr>', '/', '<expr>'],
    ['(', '<expr>', ')'],
    ['<integer>']],
'<integer>': [
    ['<digits>']],
'<digits>': [
    ['<digit>','<digits>'],
    ['<digit>']],
'<digit>': [["%s" % str(i)] for i in range(10)],
}
mystring = '1+2+3+4'
p = compile_grammar(a_grammar)
v = p.parse_on(mystring, START)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
a_grammar = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
&#x27;&lt;expr&gt;&#x27;: [
    [&#x27;&lt;expr&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
    [&#x27;&lt;expr&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;],
    [&#x27;&lt;expr&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;expr&gt;&#x27;],
    [&#x27;&lt;expr&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;expr&gt;&#x27;],
    [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
    [&#x27;&lt;integer&gt;&#x27;]],
&#x27;&lt;integer&gt;&#x27;: [
    [&#x27;&lt;digits&gt;&#x27;]],
&#x27;&lt;digits&gt;&#x27;: [
    [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
    [&#x27;&lt;digit&gt;&#x27;]],
&#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
mystring = &#x27;1+2+3+4&#x27;
p = compile_grammar(a_grammar)
v = p.parse_on(mystring, START)[0]
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## A few more examples

<!--
############
RR_GRAMMAR2 = {
    '<start>': [
    ['b', 'a', 'c'],
    ['b', 'a', 'a'],
    ['b', '<A>', 'c']
    ],
    '<A>': [['a']],
}
mystring = 'bac'
p = compile_grammar(RR_GRAMMAR2)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

RR_GRAMMAR3 = {
    '<start>': [['c', '<A>']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring = 'cababababab'

p = compile_grammar(RR_GRAMMAR3)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(7)

RR_GRAMMAR4 = {
    '<start>': [['<A>', 'c']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring = 'ababababc'

p = compile_grammar(RR_GRAMMAR4)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(8)

RR_GRAMMAR5 = {
'<start>': [['<A>']],
'<A>': [['a', 'b', '<B>'], []],
'<B>': [['<A>']],
}
mystring = 'abababab'

p = compile_grammar(RR_GRAMMAR5)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(9)

RR_GRAMMAR6 = {
'<start>': [['<A>']],
'<A>': [['a', '<B>'], []],
'<B>': [['b', '<A>']],
}
mystring = 'abababab'

p = compile_grammar(RR_GRAMMAR6)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(10)

RR_GRAMMAR7 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']],
}
mystring = 'aaaaaaaa'

p = compile_grammar(RR_GRAMMAR7)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(11)

RR_GRAMMAR8 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']]
}
mystring = 'aa'

p = compile_grammar(RR_GRAMMAR8)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(12)

X_G1 = {
    '<start>': [['a']],
}
mystring = 'a'
p = compile_grammar(X_G1)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print('X_G1')

X_G2 = {
    '<start>': [['a', 'b']],
}
mystring = 'ab'
p = compile_grammar(X_G2)
v = p.parse_on(mystring, '<start>')[0]
print('X_G2')

X_G3 = {
    '<start>': [['a', '<b>']],
    '<b>': [['b']]
}
mystring = 'ab'
p = compile_grammar(X_G3)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print('X_G3')

X_G4 = {
    '<start>': [
    ['a', '<a>'],
    ['a', '<b>'],
    ['a', '<c>']
    ],
    '<a>': [['b']],
    '<b>': [['b']],
    '<c>': [['b']]
}
mystring = 'ab'
p = compile_grammar(X_G4)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring


print('X_G4')

X_G5 = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<expr>', '+', '<expr>'],
        ['1']]
}
X_G5_start = '<start>'

mystring = '1+1'
p = compile_grammar(X_G5)
v = p.parse_on(mystring, '<start>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring


print('X_G5')

X_G6 = {
    '<S>': [
    ['b', 'a', 'c'],
    ['b', 'a', 'a'],
    ['b', '<A>', 'c'],
    ],
    '<A>': [
        ['a']]
}
X_G6_start = '<S>'

mystring = 'bac'
p = compile_grammar(X_G6)
v = p.parse_on(mystring, '<S>')[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print('X_G6')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
RR_GRAMMAR2 = {
    &#x27;&lt;start&gt;&#x27;: [
    [&#x27;b&#x27;, &#x27;a&#x27;, &#x27;c&#x27;],
    [&#x27;b&#x27;, &#x27;a&#x27;, &#x27;a&#x27;],
    [&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;]
    ],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;]],
}
mystring = &#x27;bac&#x27;
p = compile_grammar(RR_GRAMMAR2)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

RR_GRAMMAR3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;c&#x27;, &#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring = &#x27;cababababab&#x27;

p = compile_grammar(RR_GRAMMAR3)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(7)

RR_GRAMMAR4 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring = &#x27;ababababc&#x27;

p = compile_grammar(RR_GRAMMAR4)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(8)

RR_GRAMMAR5 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;B&gt;&#x27;], []],
&#x27;&lt;B&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
}
mystring = &#x27;abababab&#x27;

p = compile_grammar(RR_GRAMMAR5)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(9)

RR_GRAMMAR6 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;], []],
&#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;]],
}
mystring = &#x27;abababab&#x27;

p = compile_grammar(RR_GRAMMAR6)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(10)

RR_GRAMMAR7 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]],
}
mystring = &#x27;aaaaaaaa&#x27;

p = compile_grammar(RR_GRAMMAR7)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(11)

RR_GRAMMAR8 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]]
}
mystring = &#x27;aa&#x27;

p = compile_grammar(RR_GRAMMAR8)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(12)

X_G1 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;]],
}
mystring = &#x27;a&#x27;
p = compile_grammar(X_G1)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(&#x27;X_G1&#x27;)

X_G2 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;]],
}
mystring = &#x27;ab&#x27;
p = compile_grammar(X_G2)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(&#x27;X_G2&#x27;)

X_G3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;b&gt;&#x27;]],
    &#x27;&lt;b&gt;&#x27;: [[&#x27;b&#x27;]]
}
mystring = &#x27;ab&#x27;
p = compile_grammar(X_G3)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(&#x27;X_G3&#x27;)

X_G4 = {
    &#x27;&lt;start&gt;&#x27;: [
    [&#x27;a&#x27;, &#x27;&lt;a&gt;&#x27;],
    [&#x27;a&#x27;, &#x27;&lt;b&gt;&#x27;],
    [&#x27;a&#x27;, &#x27;&lt;c&gt;&#x27;]
    ],
    &#x27;&lt;a&gt;&#x27;: [[&#x27;b&#x27;]],
    &#x27;&lt;b&gt;&#x27;: [[&#x27;b&#x27;]],
    &#x27;&lt;c&gt;&#x27;: [[&#x27;b&#x27;]]
}
mystring = &#x27;ab&#x27;
p = compile_grammar(X_G4)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring


print(&#x27;X_G4&#x27;)

X_G5 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;expr&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;1&#x27;]]
}
X_G5_start = &#x27;&lt;start&gt;&#x27;

mystring = &#x27;1+1&#x27;
p = compile_grammar(X_G5)
v = p.parse_on(mystring, &#x27;&lt;start&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring


print(&#x27;X_G5&#x27;)

X_G6 = {
    &#x27;&lt;S&gt;&#x27;: [
    [&#x27;b&#x27;, &#x27;a&#x27;, &#x27;c&#x27;],
    [&#x27;b&#x27;, &#x27;a&#x27;, &#x27;a&#x27;],
    [&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;],
    ],
    &#x27;&lt;A&gt;&#x27;: [
        [&#x27;a&#x27;]]
}
X_G6_start = &#x27;&lt;S&gt;&#x27;

mystring = &#x27;bac&#x27;
p = compile_grammar(X_G6)
v = p.parse_on(mystring, &#x27;&lt;S&gt;&#x27;)[0]
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(&#x27;X_G6&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We assign format parse tree so that we can refer to it from this module

<!--
############
def format_parsetree(t):
    return ep.format_parsetree(t)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def format_parsetree(t):
    return ep.format_parsetree(t)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^scott2013gll]: Elizabeth Scott and Adrian Johnstone. "GLL parse-tree generation." Science of Computer Programming 78.10 (2013): 1828-1844.

[^scott2010gll]: Elizabeth Scott, and Adrian Johnstone. "GLL parsing." Electronic Notes in Theoretical Computer Science 253.7 (2010): 177-189.

[^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-07-02-generalized-ll-parser.py).


