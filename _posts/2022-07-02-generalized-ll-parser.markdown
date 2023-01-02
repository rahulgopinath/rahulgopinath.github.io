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
<li><a href="/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

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
## Utilities
### Nullable -- defined as before in [earley-parsing](/post/2021/02/06/earley-parsing/#nonterminals-deriving-empty-strings)

<!--
############
def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not fuzzer.is_nonterminal(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not fuzzer.is_nonterminal(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it:

<!--
############
print(nullable(grammar))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable(grammar))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## The GSS Graph
The GLL parser uses something called a Graph Structured Stack to limit the 
space consumption during parsing. The idea is to share as much of the stack
during parsing as possible.

### The GSS Node
Each GSS Node is of the form $$L_i^j$$ where $$j$$ is the index of the
character consumed.

<!--
############
class GSSNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GSSNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The GSS container

<!--
############
class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.gss:
            self.gss[my_label] = GSSNode(my_label)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        # indexes for which pop has been executed for label.
        return self.P[label]

    def __repr__(self): return str(self.gss)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.gss:
            self.gss[my_label] = GSSNode(my_label)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        # indexes for which pop has been executed for label.
        return self.P[label]

    def __repr__(self): return str(self.gss)
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
    def __init__(self):
        self.children = []
        self.lablel = '<None>'
        pass

    def __eq__(self, o):
        return self.label == o.label

    def __repr__(self):
        return 'D:%s [%d]' % (str(self.label), len(self.children))

    def add_child(self, child):
        self.children.append(child)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPFNode:
    def __init__(self):
        self.children = []
        self.lablel = &#x27;&lt;None&gt;&#x27;
        pass

    def __eq__(self, o):
        return self.label == o.label

    def __repr__(self):
        return &#x27;D:%s [%d]&#x27; % (str(self.label), len(self.children))

    def add_child(self, child):
        self.children.append(child)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Dummy Node

<!--
############
class SPPF_dummy(SPPFNode):
    def __init__(self, s='$'):
        self.label = (s, 0, 0)
        self.children = []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_dummy(SPPFNode):
    def __init__(self, s=&#x27;$&#x27;):
        self.label = (s, 0, 0)
        self.children = []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Symbol Node

<!--
############
class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i):
        # x is a terminal, nonterminal, or epsilon -- ''
        # j and i are the extents
        #assert 0<= j <= i <= m
        self.label = (x, j, i)
        self.children = []

    def to_s(self, g):
        return (self.label[0])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i):
        # x is a terminal, nonterminal, or epsilon -- &#x27;&#x27;
        # j and i are the extents
        #assert 0&lt;= j &lt;= i &lt;= m
        self.label = (x, j, i)
        self.children = []

    def to_s(self, g):
        return (self.label[0])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Intermediate Node
Has only two children max (or 1 child).

<!--
############
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i):
        self.label = (t, j, i)
        self.children = []

    def right_extent(self):
        return self.label[-1]

    def to_s(self, g):
        #if isinstance(self.label[0], str):
        return (self.label[0])
        #((sym, n_alt, dot), i, j)  = self.label
        #return ( sym + ' ::= ' +
        #        str(g.grammar[sym][n_alt][:dot]) + '.' +
        #        str(g.grammar[sym][n_alt][dot:]) + ' ' + str(i) + ',' + str(j))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i):
        self.label = (t, j, i)
        self.children = []

    def right_extent(self):
        return self.label[-1]

    def to_s(self, g):
        #if isinstance(self.label[0], str):
        return (self.label[0])
        #((sym, n_alt, dot), i, j)  = self.label
        #return ( sym + &#x27; ::= &#x27; +
        #        str(g.grammar[sym][n_alt][:dot]) + &#x27;.&#x27; +
        #        str(g.grammar[sym][n_alt][dot:]) + &#x27; &#x27; + str(i) + &#x27;,&#x27; + str(j))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### SPPF Packed Node

<!--
############
class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k, children):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = children # left and right or just left

    def to_s(self, g):
        return (self.label[0])
        #(sym, n_alt, dot), lat = self.label
        #return ( sym + ' ::= ' +
        #        str(g.grammar[sym][n_alt][:dot]) + '.' +
        #        str(g.grammar[sym][n_alt][dot:]) + ' ' + str(lat) )

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k, children):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = children # left and right or just left

    def to_s(self, g):
        return (self.label[0])
        #(sym, n_alt, dot), lat = self.label
        #return ( sym + &#x27; ::= &#x27; +
        #        str(g.grammar[sym][n_alt][:dot]) + &#x27;.&#x27; +
        #        str(g.grammar[sym][n_alt][dot:]) + &#x27; &#x27; + str(lat) )
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
        self.I = input_str + '$' # read the input I and set I[m] = `$`
        self.m = len(input_str)
        self.gss = GSS()
        # create GSS node u_0 = (L_0, 0)
        self.stack_bottom = self.gss.get(('L0', 0))

        # R := \empty
        self.threads = []

        self.U = [[] for j in range(self.m+1)]
        self.SPPF_nodes = {}

    def set_grammar(self, g):
        self.grammar = g
        self.nullable = nullable(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP:
    def __init__(self, input_str):
        self.I = input_str + &#x27;$&#x27; # read the input I and set I[m] = `$`
        self.m = len(input_str)
        self.gss = GSS()
        # create GSS node u_0 = (L_0, 0)
        self.stack_bottom = self.gss.get((&#x27;L0&#x27;, 0))

        # R := \empty
        self.threads = []

        self.U = [[] for j in range(self.m+1)]
        self.SPPF_nodes = {}

    def set_grammar(self, g):
        self.grammar = g
        self.nullable = nullable(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL add thread (add)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, u, i, w):
        # w needs to be an SPPF node.
        assert not isinstance(u, int)
        assert isinstance(w, SPPFNode)
        if (L, u, w) not in self.U[i]:
            self.U[i].append((L, u, w))
            self.threads.append((L, u, i, w))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, u, i, w):
        # w needs to be an SPPF node.
        assert not isinstance(u, int)
        assert isinstance(w, SPPFNode)
        if (L, u, w) not in self.U[i]:
            self.U[i].append((L, u, w))
            self.threads.append((L, u, i, w))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL fn_return (pop)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, u, i, z):
        # z needs to be SPPF.
        assert isinstance(z, SPPFNode)
        if u != self.stack_bottom:
            # let (L, k) be label of u
            (L, k) = u.label
            self.gss.add_parsed_index(u.label, z)
            for v,w in u.children: # edge labeled w, an SPPF node.
                assert isinstance(w, SPPFNode)
                #assert w.label[2] == z.label[1]
                y = self.getNodeP(L, w, z)
                self.add_thread(L, v, i, y)
        return u

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, u, i, z):
        # z needs to be SPPF.
        assert isinstance(z, SPPFNode)
        if u != self.stack_bottom:
            # let (L, k) be label of u
            (L, k) = u.label
            self.gss.add_parsed_index(u.label, z)
            for v,w in u.children: # edge labeled w, an SPPF node.
                assert isinstance(w, SPPFNode)
                #assert w.label[2] == z.label[1]
                y = self.getNodeP(L, w, z)
                self.add_thread(L, v, i, y)
        return u
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### GLL register_return (create)

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, u, i, w): # returns to stack_top
        assert isinstance(w, SPPFNode)
        v = self.gss.get((L, i)) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        #assert not v.children # test. why are there no children?
        v_to_u_labeled_w = [c for c,lbl in v.children if c.label == u.label and lbl == w]
        if not v_to_u_labeled_w:
            # create an edge from v to u labelled w
            v.children.append((u,w))

            for z in self.gss.parsed_indexes(v.label):
                assert isinstance(z, SPPF_intermediate_node)
                y = self.getNodeP(L, w, z)
                h = z.right_extent()
                self.add_thread(v.L, u, h, y) # v.L == L
        return v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, u, i, w): # returns to stack_top
        assert isinstance(w, SPPFNode)
        v = self.gss.get((L, i)) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        #assert not v.children # test. why are there no children?
        v_to_u_labeled_w = [c for c,lbl in v.children if c.label == u.label and lbl == w]
        if not v_to_u_labeled_w:
            # create an edge from v to u labelled w
            v.children.append((u,w))

            for z in self.gss.parsed_indexes(v.label):
                assert isinstance(z, SPPF_intermediate_node)
                y = self.getNodeP(L, w, z)
                h = z.right_extent()
                self.add_thread(v.L, u, h, y) # v.L == L
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

    def get_sppf_symbol_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_symbol_node(*n)
        return self.SPPF_nodes[n]

    def get_sppf_intermediate_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_intermediate_node(*n)
        return self.SPPF_nodes[n]

    def sppf_find_or_create(self, label, j, i):
        if isinstance(label, str):
            return self.get_sppf_symbol_node((label, j, i))
        else:
            return self.get_sppf_intermediate_node((label, j, i))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStructuredStackP(GLLStructuredStackP):
    def next_thread(self): # i \in R
        t, *self.threads = self.threads
        return t

    def get_sppf_symbol_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_symbol_node(*n)
        return self.SPPF_nodes[n]

    def get_sppf_intermediate_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_intermediate_node(*n)
        return self.SPPF_nodes[n]

    def sppf_find_or_create(self, label, j, i):
        if isinstance(label, str):
            return self.get_sppf_symbol_node((label, j, i))
        else:
            return self.get_sppf_intermediate_node((label, j, i))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# SPPF Build

<!--
############
class GLLStructuredStackP(GLLStructuredStackP):
    # getNode(x, i) creates and returns an SPPF node labeled (x, i, i+1) or
    # (epsilon, i, i) if x is epsilon
    def getNodeT(self, x, i):
        if x is None: h = i # x is epsilon
        else: h = i+1
        return self.get_sppf_symbol_node((x, i, h))

    # getNodeP(X::= alpha.beta, w, z) takes a grammar slot X ::= alpha . beta
    # and two SPPF nodes w, and z (z may be dummy node $).
    # the nodes w and z are not packed nodes, and will have labels of form
    # (s,j,k) and (r, k, i)
    def getNodeP(self, X_rule_pos, w, z): # w is left node, z is right node
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha = rule[:dot]
        beta = rule[dot:]
        if self.is_non_nullable_alpha(X, rule, dot) and beta: # beta != epsilon
            return z
        else:
            if beta == []: # if beta = epsilon from GLL_parse_tree_generation
                t = X # symbol node.
            else:
                t = X_rule_pos
            (q, k, i) = z.label # suppose z has label (q,k,i)
            if (w.label[0] != '$'): # is not delta
                # returns (t,j,i) <- (X:= alpha.beta, k) <- w:(s,j,k),<-z:(r,k,i)
                (s,j,_k) = w.label # suppose w has label (s,j,k)
                # w is the left node, and z is the right node. So the center (k)
                # should be shared.
                assert k == _k # TODO: this should be true.
                #k = _k

                # if there does not exist an SPPF node y labelled (t, j, i) create one
                y = self.sppf_find_or_create(t, j, i)

                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    # create a child of y with left child with w right child z
                    # the extent of w-z is the same as y
                    # packed nodes do not keep extents
                    pn = SPPF_packed_node(X_rule_pos, k, [w,z])
                    y.add_child(pn)
            else:
                # if there does not exist an SPPF node y labelled (t, k, i) create one
                # returns (t,k,i) <- (X:= alpha.beta, k) <- (r,k,i)
                y = self.sppf_find_or_create(t, k, i)
                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    pn = SPPF_packed_node(X_rule_pos, k, [z])
                    y.add_child(pn) # create a child with child z
            return y

    # adapted from Exploring_and_Visualizing paper.
    def is_non_nullable_alpha(self, X, rule, dot):
        #  we need to convert this to X := alpha . beta
        alpha = rule[:dot]
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
    # getNode(x, i) creates and returns an SPPF node labeled (x, i, i+1) or
    # (epsilon, i, i) if x is epsilon
    def getNodeT(self, x, i):
        if x is None: h = i # x is epsilon
        else: h = i+1
        return self.get_sppf_symbol_node((x, i, h))

    # getNodeP(X::= alpha.beta, w, z) takes a grammar slot X ::= alpha . beta
    # and two SPPF nodes w, and z (z may be dummy node $).
    # the nodes w and z are not packed nodes, and will have labels of form
    # (s,j,k) and (r, k, i)
    def getNodeP(self, X_rule_pos, w, z): # w is left node, z is right node
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha = rule[:dot]
        beta = rule[dot:]
        if self.is_non_nullable_alpha(X, rule, dot) and beta: # beta != epsilon
            return z
        else:
            if beta == []: # if beta = epsilon from GLL_parse_tree_generation
                t = X # symbol node.
            else:
                t = X_rule_pos
            (q, k, i) = z.label # suppose z has label (q,k,i)
            if (w.label[0] != &#x27;$&#x27;): # is not delta
                # returns (t,j,i) &lt;- (X:= alpha.beta, k) &lt;- w:(s,j,k),&lt;-z:(r,k,i)
                (s,j,_k) = w.label # suppose w has label (s,j,k)
                # w is the left node, and z is the right node. So the center (k)
                # should be shared.
                assert k == _k # TODO: this should be true.
                #k = _k

                # if there does not exist an SPPF node y labelled (t, j, i) create one
                y = self.sppf_find_or_create(t, j, i)

                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    # create a child of y with left child with w right child z
                    # the extent of w-z is the same as y
                    # packed nodes do not keep extents
                    pn = SPPF_packed_node(X_rule_pos, k, [w,z])
                    y.add_child(pn)
            else:
                # if there does not exist an SPPF node y labelled (t, k, i) create one
                # returns (t,k,i) &lt;- (X:= alpha.beta, k) &lt;- (r,k,i)
                y = self.sppf_find_or_create(t, k, i)
                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    pn = SPPF_packed_node(X_rule_pos, k, [z])
                    y.add_child(pn) # create a child with child z
            return y

    # adapted from Exploring_and_Visualizing paper.
    def is_non_nullable_alpha(self, X, rule, dot):
        #  we need to convert this to X := alpha . beta
        alpha = rule[:dot]
        if not alpha: return False
        if len(alpha) != 1: return False
        if fuzzer.is_terminal(alpha[0]): return True
        if alpha[0] in self.nullable: return False
        return True
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling an empty rule

<!--
############
def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            c_r = parser.getNodeT(None, current_index)
            current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
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
            c_r = parser.getNodeT(None, current_index)
            current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
            L = &#x27;L_&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt,show_dot(g, (key, n_alt, 0)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Terminal Symbol

<!--
############
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[current_index] == '%s':
                c_r = parser.getNodeT(parser.I[current_index], current_index)
                current_index = current_index+1
                L = %s
                current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
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
            if parser.I[current_index] == &#x27;%s&#x27;:
                c_r = parser.getNodeT(parser.I[current_index], current_index)
                current_index = current_index+1
                L = %s
                current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
            else:
                L = &#x27;L0&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), token, Lnxt)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Nonterminal Symbol

<!--
############
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, current_index, current_sppf_node)
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
            stack_top = parser.register_return(%s, stack_top, current_index, current_sppf_node)
            L = &quot;%s&quot;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), Lnxt, token)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Rule

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
#### Compiling a Definition

<!--
############
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # need to check first() if performance is important.
            # %s
            parser.add_thread( ('%s',%d,0), stack_top, current_index, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
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
            # need to check first() if performance is important.
            # %s
            parser.add_thread( (&#x27;%s&#x27;,%d,0), stack_top, current_index, end_rule)&#x27;&#x27;&#x27; % (key + &#x27;::=&#x27; + str(rule), key, n_alt))
    res.append(&#x27;&#x27;&#x27;
            L = &#x27;L0&#x27;
            continue&#x27;&#x27;&#x27;)
    for n_alt,rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Grammar

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
    end_rule = SPPF_dummy('$')
    L, stack_top, current_index, current_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, current_index, current_sppf_node) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return 'success'
                else: return 'error'
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, current_index, current_sppf_node) # pop
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
    end_rule = SPPF_dummy(&#x27;$&#x27;)
    L, stack_top, current_index, current_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == &#x27;L0&#x27;:
            if parser.threads: # if R != \empty
                (L, stack_top, current_index, current_sppf_node) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return &#x27;success&#x27;
                else: return &#x27;error&#x27;
        elif L == &#x27;L_&#x27;:
            stack_top = parser.fn_return(stack_top, current_index, current_sppf_node) # pop
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
G1 = {
    '<S>': [['c']]
}
mystring2 = 'c'
res = compile_grammar(G1, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print(1)

G2 = {
    '<S>': [['c', 'c']]
}
mystring2 = 'cc'
res = compile_grammar(G2, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print(2)

G3 = {
    '<S>': [['c', 'c', 'c']]
}
mystring2 = 'ccc'
res = compile_grammar(G3, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print(3)


G4 = {
    '<S>': [['c'],
            ['a']]
}
mystring2 = 'a'
res = compile_grammar(G4, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print(4)


G5 = {
    '<S>': [['<A>']],
    '<A>': [['a']]
}
mystring2 = 'a'
res = compile_grammar(G5, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print(5)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G1 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;]]
}
mystring2 = &#x27;c&#x27;
res = compile_grammar(G1, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(1)

G2 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;, &#x27;c&#x27;]]
}
mystring2 = &#x27;cc&#x27;
res = compile_grammar(G2, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(2)

G3 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;, &#x27;c&#x27;, &#x27;c&#x27;]]
}
mystring2 = &#x27;ccc&#x27;
res = compile_grammar(G3, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(3)


G4 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;c&#x27;],
            [&#x27;a&#x27;]]
}
mystring2 = &#x27;a&#x27;
res = compile_grammar(G4, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(4)


G5 = {
    &#x27;&lt;S&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;]]
}
mystring2 = &#x27;a&#x27;
res = compile_grammar(G5, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(5)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Parse tree

<!--
############
import random

def process_sppf_symbol(node, hmap, tab):
    key = node.to_s(g)
    if key is None:
        return ['$', []]
    assert isinstance(key, str)
    if node.children:
        n = random.choice(node.children)
        return [key, process_sppf_packed(n,hmap, tab+1)]
    return [key, []]

def process_sppf_packed(node, hmap, tab):
    key = node.to_s(g)
    # packed nodes (rounded) represent on particular derivation. No need to add key
    assert isinstance(node, SPPF_packed_node)
    assert not isinstance(key, str)
    children = []
    # A packed node may have two children, just left and right.
    children
    for n in node.children:
        if isinstance(n, SPPF_symbol_node):
            v = process_sppf_symbol(n,hmap, tab+1)
            children.append(v)
        elif isinstance(n, SPPF_intermediate_node):
            v = process_sppf_intermediate_node(n,hmap, tab+1)
            children.extend(v)
        else: assert False
    return children

def process_sppf_intermediate_node(node, hmap, tab):
    key = node.to_s(g)
    assert isinstance(node, SPPF_intermediate_node)
    #print(' '*tab, 'I', node.to_s(g))
    #assert len(node.children) == 1
    #n = random.choice(node.children)
    assert not isinstance(key, str)
    ret = []
    for n in node.children:
        v = process_sppf_packed(n,hmap, tab+1)
        ret.extend(v)
    return ret

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random

def process_sppf_symbol(node, hmap, tab):
    key = node.to_s(g)
    if key is None:
        return [&#x27;$&#x27;, []]
    assert isinstance(key, str)
    if node.children:
        n = random.choice(node.children)
        return [key, process_sppf_packed(n,hmap, tab+1)]
    return [key, []]

def process_sppf_packed(node, hmap, tab):
    key = node.to_s(g)
    # packed nodes (rounded) represent on particular derivation. No need to add key
    assert isinstance(node, SPPF_packed_node)
    assert not isinstance(key, str)
    children = []
    # A packed node may have two children, just left and right.
    children
    for n in node.children:
        if isinstance(n, SPPF_symbol_node):
            v = process_sppf_symbol(n,hmap, tab+1)
            children.append(v)
        elif isinstance(n, SPPF_intermediate_node):
            v = process_sppf_intermediate_node(n,hmap, tab+1)
            children.extend(v)
        else: assert False
    return children

def process_sppf_intermediate_node(node, hmap, tab):
    key = node.to_s(g)
    assert isinstance(node, SPPF_intermediate_node)
    #print(&#x27; &#x27;*tab, &#x27;I&#x27;, node.to_s(g))
    #assert len(node.children) == 1
    #n = random.choice(node.children)
    assert not isinstance(key, str)
    ret = []
    for n in node.children:
        v = process_sppf_packed(n,hmap, tab+1)
        ret.extend(v)
    return ret
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

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
mystring2 = 'bac'
res = compile_grammar(RR_GRAMMAR2, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

RR_GRAMMAR3 = {
    '<start>': [['c', '<A>']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring3 = 'cababababab'

res = compile_grammar(RR_GRAMMAR3, '<start>')
exec(res)
g = GLLStructuredStackP(mystring3)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(7)

RR_GRAMMAR4 = {
    '<start>': [['<A>', 'c']],
    '<A>': [['a', 'b', '<A>'], []],
}
mystring4 = 'ababababc'

res = compile_grammar(RR_GRAMMAR4, '<start>')
exec(res)
g = GLLStructuredStackP(mystring4)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(8)

RR_GRAMMAR5 = {
'<start>': [['<A>']],
'<A>': [['a', 'b', '<B>'], []],
'<B>': [['<A>']],
}
mystring5 = 'abababab'

res = compile_grammar(RR_GRAMMAR5, '<start>')
exec(res)
g = GLLStructuredStackP(mystring5)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(9)

RR_GRAMMAR6 = {
'<start>': [['<A>']],
'<A>': [['a', '<B>'], []],
'<B>': [['b', '<A>']],
}
mystring6 = 'abababab'

res = compile_grammar(RR_GRAMMAR6, '<start>')
exec(res)
g = GLLStructuredStackP(mystring6)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(10)

RR_GRAMMAR7 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']],
}
mystring7 = 'aaaaaaaa'

res = compile_grammar(RR_GRAMMAR7, '<start>')
exec(res)
g = GLLStructuredStackP(mystring7)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(11)

RR_GRAMMAR8 = {
'<start>': [['<A>']],
'<A>': [['a', '<A>'], ['a']]
}
mystring8 = 'aa'

res = compile_grammar(RR_GRAMMAR8, '<start>')
exec(res)
g = GLLStructuredStackP(mystring8)
assert parse_string(g) == 'success'
print(12)


X_G1 = {
    '<start>': [['a']],
}
mystring2 = 'a'
res = compile_grammar(X_G1, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print('X_G1')

X_G2 = {
    '<start>': [['a', 'b']],
}
mystring2 = 'ab'
res = compile_grammar(X_G2, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
print('X_G2')

X_G3 = {
    '<start>': [['a', '<b>']],
    '<b>': [['b']]
}
mystring2 = 'ab'
res = compile_grammar(X_G3, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
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
mystring2 = 'ab'
res = compile_grammar(X_G4, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print('X_G4')

X_G5 = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<expr>', '+', '<expr>'],
        ['1']]
}
X_G5_start = '<start>'

mystring2 = '1+1'
res = compile_grammar(X_G5, '<start>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
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

mystring2 = 'bac'
res = compile_grammar(X_G6, '<S>')
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == 'success'
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

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
mystring2 = &#x27;bac&#x27;
res = compile_grammar(RR_GRAMMAR2, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

RR_GRAMMAR3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;c&#x27;, &#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring3 = &#x27;cababababab&#x27;

res = compile_grammar(RR_GRAMMAR3, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring3)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(7)

RR_GRAMMAR4 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;, &#x27;c&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;], []],
}
mystring4 = &#x27;ababababc&#x27;

res = compile_grammar(RR_GRAMMAR4, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring4)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(8)

RR_GRAMMAR5 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;, &#x27;&lt;B&gt;&#x27;], []],
&#x27;&lt;B&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
}
mystring5 = &#x27;abababab&#x27;

res = compile_grammar(RR_GRAMMAR5, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring5)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(9)

RR_GRAMMAR6 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;], []],
&#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;, &#x27;&lt;A&gt;&#x27;]],
}
mystring6 = &#x27;abababab&#x27;

res = compile_grammar(RR_GRAMMAR6, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring6)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(10)

RR_GRAMMAR7 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]],
}
mystring7 = &#x27;aaaaaaaa&#x27;

res = compile_grammar(RR_GRAMMAR7, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring7)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(11)

RR_GRAMMAR8 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;]],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;]]
}
mystring8 = &#x27;aa&#x27;

res = compile_grammar(RR_GRAMMAR8, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring8)
assert parse_string(g) == &#x27;success&#x27;
print(12)


X_G1 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;]],
}
mystring2 = &#x27;a&#x27;
res = compile_grammar(X_G1, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(&#x27;X_G1&#x27;)

X_G2 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;b&#x27;]],
}
mystring2 = &#x27;ab&#x27;
res = compile_grammar(X_G2, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
print(&#x27;X_G2&#x27;)

X_G3 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;b&gt;&#x27;]],
    &#x27;&lt;b&gt;&#x27;: [[&#x27;b&#x27;]]
}
mystring2 = &#x27;ab&#x27;
res = compile_grammar(X_G3, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
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
mystring2 = &#x27;ab&#x27;
res = compile_grammar(X_G4, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

print(&#x27;X_G4&#x27;)

X_G5 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;expr&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;1&#x27;]]
}
X_G5_start = &#x27;&lt;start&gt;&#x27;

mystring2 = &#x27;1+1&#x27;
res = compile_grammar(X_G5, &#x27;&lt;start&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
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

mystring2 = &#x27;bac&#x27;
res = compile_grammar(X_G6, &#x27;&lt;S&gt;&#x27;)
exec(res)
g = GLLStructuredStackP(mystring2)
assert parse_string(g) == &#x27;success&#x27;
v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
print(v)
fuzzer.display_tree(v)

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


