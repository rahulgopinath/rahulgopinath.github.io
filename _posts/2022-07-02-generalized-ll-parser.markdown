---
published: true
title: Generalized LL (GLL) Parser
layout: post
comments: true
tags: controlflow
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
We [previously discussed](/post/2021/02/06/earley-parsing/) the
implementation of an Earley parser with Joop Leo's optimizations. Earley
parser is one of the general context-free parsing algorithms available.
Another popular general context-free parsing algorightm is
*Generalized LL* parsing, which was invented by
Elizabeth Scott and Adrian Johnstone. In this post, I provide a complete
implementation and a tutorial on how to implement a GLL parser in Python.

**Note:** This post is not complete. Given the interest in GLL parsers, I am
simply providing the source (which substantially follows the publications)
until I have more bandwidth to complete the tutorial. However, the code
itself is complete, and can be used.

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

<!--
############
import simplefuzzer as fuzzer
import earleyparser as ep
import random

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import earleyparser as ep
import random
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
        key = self.to_s(g) # ignored
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
        key = self.to_s(g) # ignored
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

    def to_tree_(self, hmap, tab):
        key = self.to_s(g)
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

    def to_tree_(self, hmap, tab):
        key = self.to_s(g)
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
    def __init__(self, input_str):
        self.I = input_str + '$'
        self.m = len(input_str)
        self.gss = GSS()
        self.stack_bottom = self.gss.get(('L0', 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)] # descriptors for each index
        self.SPPF_nodes = {}

    def set_grammar(self, g):
        self.grammar = g
        self.first, self.follow, self.nullable = get_first_and_follow(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP:
    def __init__(self, input_str):
        self.I = input_str + &#x27;$&#x27;
        self.m = len(input_str)
        self.gss = GSS()
        self.stack_bottom = self.gss.get((&#x27;L0&#x27;, 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)] # descriptors for each index
        self.SPPF_nodes = {}

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
### Compiling a Grammar

<!--
############
def compile_grammar(g, start):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = ['''\
def parse_string(parser):
    parser.set_grammar(
%s
    )
    # L contains start nt.
    S = '%s'
    end_rule = SPPF_dummy_node('$', 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return 'success'
                else: return 'error'
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = 'L0' # goto L_0
            continue
    ''' % (pp.pformat(g), start)]
    for k in g:
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_grammar(g, start):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = [&#x27;&#x27;&#x27;\
def parse_string(parser):
    parser.set_grammar(
%s
    )
    # L contains start nt.
    S = &#x27;%s&#x27;
    end_rule = SPPF_dummy_node(&#x27;$&#x27;, 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == &#x27;L0&#x27;:
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return &#x27;success&#x27;
                else: return &#x27;error&#x27;
        elif L == &#x27;L_&#x27;:
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = &#x27;L0&#x27; # goto L_0
            continue
    &#x27;&#x27;&#x27; % (pp.pformat(g), start)]
    for k in g:
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append(&#x27;&#x27;&#x27;
        else:
            assert False&#x27;&#x27;&#x27;)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
v = compile_grammar(grammar, '<start>')
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = compile_grammar(grammar, &#x27;&lt;start&gt;&#x27;)
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
res = compile_grammar(G1, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G1, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G2, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G2, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G3, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G3, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G4, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G4, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G5, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(G5, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(grammar, START)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
r = fuzzer.tree_to_string(v)
assert r == mystring
ep.display_tree(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;(1+1)*(23/45)-1&#x27;
res = compile_grammar(grammar, START)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(a_grammar, START)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(a_grammar, START)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(RR_GRAMMAR2, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

RR_GRAMMAR3 = {
    '<start>': [['c', '<A>']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring = 'cababababab'

res = compile_grammar(RR_GRAMMAR3, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(7)

RR_GRAMMAR4 = {
    '<start>': [['<A>', 'c']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring = 'ababababc'

res = compile_grammar(RR_GRAMMAR4, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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

res = compile_grammar(RR_GRAMMAR5, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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

res = compile_grammar(RR_GRAMMAR6, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(10)

RR_GRAMMAR7 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']],
}
mystring = 'aaaaaaaa'

res = compile_grammar(RR_GRAMMAR7, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(11)

RR_GRAMMAR8 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']]
}
mystring = 'aa'

res = compile_grammar(RR_GRAMMAR8, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(12)

X_G1 = {
    '<start>': [['a']],
}
mystring = 'a'
res = compile_grammar(X_G1, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print('X_G1')

X_G2 = {
    '<start>': [['a', 'b']],
}
mystring = 'ab'
res = compile_grammar(X_G2, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
print('X_G2')

X_G3 = {
    '<start>': [['a', '<b>']],
    '<b>': [['b']]
}
mystring = 'ab'
res = compile_grammar(X_G3, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G4, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G5, '<start>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G6, '<S>')
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == 'success'
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(RR_GRAMMAR2, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

RR_GRAMMAR3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;c&#x27;, &#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring = &#x27;cababababab&#x27;

res = compile_grammar(RR_GRAMMAR3, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(7)

RR_GRAMMAR4 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring = &#x27;ababababc&#x27;

res = compile_grammar(RR_GRAMMAR4, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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

res = compile_grammar(RR_GRAMMAR5, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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

res = compile_grammar(RR_GRAMMAR6, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(10)

RR_GRAMMAR7 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]],
}
mystring = &#x27;aaaaaaaa&#x27;

res = compile_grammar(RR_GRAMMAR7, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(11)

RR_GRAMMAR8 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]]
}
mystring = &#x27;aa&#x27;

res = compile_grammar(RR_GRAMMAR8, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(12)

X_G1 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;]],
}
mystring = &#x27;a&#x27;
res = compile_grammar(X_G1, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(&#x27;X_G1&#x27;)

X_G2 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;]],
}
mystring = &#x27;ab&#x27;
res = compile_grammar(X_G2, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
print(&#x27;X_G2&#x27;)

X_G3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;b&gt;&#x27;]],
    &#x27;&lt;b&gt;&#x27;: [[&#x27;b&#x27;]]
}
mystring = &#x27;ab&#x27;
res = compile_grammar(X_G3, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G4, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G5, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
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
res = compile_grammar(X_G6, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring)
assert parse_string(g) == &#x27;success&#x27;
v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
print(v)
r = fuzzer.tree_to_string(v)
assert r == mystring

print(&#x27;X_G6&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-07-02-generalized-ll-parser.py).


