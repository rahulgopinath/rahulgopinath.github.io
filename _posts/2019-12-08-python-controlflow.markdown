---
published: true
title: The Python Control Flow Graph
layout: post
comments: true
tags: controlflow
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.9/';</script>
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
We [previously discussed](/post/2019/12/07/python-mci/) how one can write an interpreter for
Python. We hinted at that time that the machinery could be used for a variety of
other applications, including exctracting the call and control flow graph. In this
post, we will show how one can extract the control flow graph using such an interpteter.

A [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) is a directed graph
data structure that encodes all paths that may be traversed through a program. That is, in some
sense, it is an abstract view of the interpreter as a whole.

This implementation is based on the [fuzzingbook CFG appendix](https://www.fuzzingbook.org/html/ControlFlow.html)
However, the fuzzingbook implementation is focused on Python statements as it is used primarily for
visualization, while this is based on basic blocks with the intension of using it for code
generation.

Control flow graphs are useful for a variety of tasks. They are one of the most frequently
used tools for visualization. But more imporatntly it is the starting point for further
analysis of the program including code generation, optimizations, and other static analysis
techniques.

#### Prerequisites
As before, we start with the prerequisite imports.

<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<ol>
<li>matplotlib</li>
<li>networkx</li>
</ol>
<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
matplotlib
networkx
</textarea>
</form>
</div>
</details>

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.

<ol>
<li><a href="https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl</a></li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import ast
import pydot
import metacircularinterpreter

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import ast
import pydot
import metacircularinterpreter
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### A few helper functions for visualization

The *color* is used to determine whether true or false branch was taken.

<!--
############
def get_color(p, c):
    color='black'
    while not p.annotation():
        if p.label == 'if:True':
            return 'blue'
        elif p.label == 'if:False':
            return 'red'
        p = p.parents[0]
    return color

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_color(p, c):
    color=&#x27;black&#x27;
    while not p.annotation():
        if p.label == &#x27;if:True&#x27;:
            return &#x27;blue&#x27;
        elif p.label == &#x27;if:False&#x27;:
            return &#x27;red&#x27;
        p = p.parents[0]
    return color
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The *peripheries* determines the number of border lines. Start and stop gets double borders.

<!--
############
def get_peripheries(p):
    annot = p.annotation()
    if annot  in {'<start>', '<stop>'}:
        return '2'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return '2'
    return '1'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_peripheries(p):
    annot = p.annotation()
    if annot  in {&#x27;&lt;start&gt;&#x27;, &#x27;&lt;stop&gt;&#x27;}:
        return &#x27;2&#x27;
    if annot.startswith(&#x27;&lt;define&gt;&#x27;) or annot.startswith(&#x27;&lt;exit&gt;&#x27;):
        return &#x27;2&#x27;
    return &#x27;1&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The *shape* determines the kind of node. A diamond is a conditional, and start and stop are ovals.

<!--
############
def get_shape(p):
    annot = p.annotation()
    if annot in {'<start>', '<stop>'}:
        return 'oval'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return 'oval'

    if annot.startswith('if:'):
        return 'diamond'
    else:
        return 'rectangle'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_shape(p):
    annot = p.annotation()
    if annot in {&#x27;&lt;start&gt;&#x27;, &#x27;&lt;stop&gt;&#x27;}:
        return &#x27;oval&#x27;
    if annot.startswith(&#x27;&lt;define&gt;&#x27;) or annot.startswith(&#x27;&lt;exit&gt;&#x27;):
        return &#x27;oval&#x27;

    if annot.startswith(&#x27;if:&#x27;):
        return &#x27;diamond&#x27;
    else:
        return &#x27;rectangle&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `to_graph()` function produces a graph from the nodes in the registry.

<!--
############
def to_graph(my_nodes, arcs=[], comment='', get_shape=lambda n: 'rectangle', get_peripheries=lambda n: '1', get_color=lambda p,c: 'black'):
    G = pydot.Dot(comment, graph_type="digraph")
    for nid, cnode in my_nodes:
        if not cnode.annotation():
            continue
        sn = cnode.annotation()
        G.add_node(pydot.Node(cnode.name(), label=sn, shape=get_shape(cnode), peripheries=get_peripheries(cnode)))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            G.add_edge(pydot.Edge(gp, str(cnode.rid), color=color))
    return G


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_graph(my_nodes, arcs=[], comment=&#x27;&#x27;, get_shape=lambda n: &#x27;rectangle&#x27;, get_peripheries=lambda n: &#x27;1&#x27;, get_color=lambda p,c: &#x27;black&#x27;):
    G = pydot.Dot(comment, graph_type=&quot;digraph&quot;)
    for nid, cnode in my_nodes:
        if not cnode.annotation():
            continue
        sn = cnode.annotation()
        G.add_node(pydot.Node(cnode.name(), label=sn, shape=get_shape(cnode), peripheries=get_peripheries(cnode)))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            G.add_edge(pydot.Edge(gp, str(cnode.rid), color=color))
    return G
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The CFGNode

The control flow graph is a graph, and hence we need a data structue for the *node*. We need to store the parents
of this node, the children of this node, and register itself in the registery.

<!--
############
class GraphState:
    def __init__(self):
        self.counter = 0
        self.registry = {}
        self.stack = []

class CFGNode:
    counter = 0
    registry = {}
    stack = []
    def __init__(self, parents=[], ast=None, label=None, annot=None, state=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.label = label
        self.annot = annot
        self.rid  = state.counter
        state.registry[self.rid] = self
        state.counter += 1
        self.state = state

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GraphState:
    def __init__(self):
        self.counter = 0
        self.registry = {}
        self.stack = []

class CFGNode:
    counter = 0
    registry = {}
    stack = []
    def __init__(self, parents=[], ast=None, label=None, annot=None, state=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.label = label
        self.annot = annot
        self.rid  = state.counter
        state.registry[self.rid] = self
        state.counter += 1
        self.state = state
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given that it is a directed graph node, we need the ability to add parents and children.

<!--
############
class CFGNode(CFGNode):
    def add_child(self, c):
        if c not in self.children:
            self.children.append(c)

    def add_parent(self, p):
        if p not in self.parents:
            self.parents.append(p)

    def add_parents(self, ps):
        for p in ps:
            self.add_parent(p)

    def add_calls(self, func):
        mid = None
        if hasattr(func, 'id'): # ast.Name
            mid = func.id
        else: # ast.Attribute
            mid = func.value.id
        self.calls.append(mid)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFGNode(CFGNode):
    def add_child(self, c):
        if c not in self.children:
            self.children.append(c)

    def add_parent(self, p):
        if p not in self.parents:
            self.parents.append(p)

    def add_parents(self, ps):
        for p in ps:
            self.add_parent(p)

    def add_calls(self, func):
        mid = None
        if hasattr(func, &#x27;id&#x27;): # ast.Name
            mid = func.id
        else: # ast.Attribute
            mid = func.value.id
        self.calls.append(mid)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A few convenience methods to make our life simpler.

<!--
############
class CFGNode(CFGNode):
    def __eq__(self, other):
        return self.rid == other.rid

    def __neq__(self, other):
        return self.rid != other.rid

    def lineno(self):
        return self.ast_node.lineno if hasattr(self.ast_node, 'lineno') else 0

    def name(self):
        return str(self.rid)

    def expr(self):
        return self.source()

    def __str__(self):
        return "id:%d line[%d] parents: %s : %s" % \
           (self.rid, self.lineno(), str([p.rid for p in self.parents]), self.source())

    def __repr__(self):
        return str(self)

    def source(self):
        return ast.unparse(self.ast_node).strip()

    def annotation(self):
        if self.annot is not None:
            return self.annot
        if self.source() in {'start', 'stop'}:
            return "<%s>" % self.source()
        return self.source()

    def to_json(self):
        return {'id':self.rid, 'parents': [p.rid for p in self.parents],
               'children': [c.rid for c in self.children],
               'calls': self.calls, 'at':self.lineno() ,'ast':self.source()}

    def get_gparent_id(self):
        p = self.state.registry[self.rid]
        while not p.annotation():
            p = p.parents[0]
        return str(p.rid)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFGNode(CFGNode):
    def __eq__(self, other):
        return self.rid == other.rid

    def __neq__(self, other):
        return self.rid != other.rid

    def lineno(self):
        return self.ast_node.lineno if hasattr(self.ast_node, &#x27;lineno&#x27;) else 0

    def name(self):
        return str(self.rid)

    def expr(self):
        return self.source()

    def __str__(self):
        return &quot;id:%d line[%d] parents: %s : %s&quot; % \
           (self.rid, self.lineno(), str([p.rid for p in self.parents]), self.source())

    def __repr__(self):
        return str(self)

    def source(self):
        return ast.unparse(self.ast_node).strip()

    def annotation(self):
        if self.annot is not None:
            return self.annot
        if self.source() in {&#x27;start&#x27;, &#x27;stop&#x27;}:
            return &quot;&lt;%s&gt;&quot; % self.source()
        return self.source()

    def to_json(self):
        return {&#x27;id&#x27;:self.rid, &#x27;parents&#x27;: [p.rid for p in self.parents],
               &#x27;children&#x27;: [c.rid for c in self.children],
               &#x27;calls&#x27;: self.calls, &#x27;at&#x27;:self.lineno() ,&#x27;ast&#x27;:self.source()}

    def get_gparent_id(self):
        p = self.state.registry[self.rid]
        while not p.annotation():
            p = p.parents[0]
        return str(p.rid)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The usage is as below:

<!--
############
gs = GraphState()
start = CFGNode(parents=[], ast=ast.parse('start').body, state=gs)
g = to_graph(gs.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GraphState()
start = CFGNode(parents=[], ast=ast.parse(&#x27;start&#x27;).body, state=gs)
g = to_graph(gs.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="70pt" height="52pt"
 viewBox="0.00 0.00 70.00 52.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 48)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-48 66,-48 66,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-22" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-22" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-18.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
</g>
</svg>
### Extracting the control flow

The control flow graph is essentially a source code walker, and shares the basic
structure with our interpreter.

<!--
############
class PyCFGExtractor(metacircularinterpreter.PyMCInterpreter):
    def __init__(self):
        self.gstate = self.create_graphstate()
        self.founder = CFGNode(parents=[], ast=ast.parse('start').body[0], state=self.gstate) # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}

    def create_graphstate(self):
        return GraphState()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(metacircularinterpreter.PyMCInterpreter):
    def __init__(self):
        self.gstate = self.create_graphstate()
        self.founder = CFGNode(parents=[], ast=ast.parse(&#x27;start&#x27;).body[0], state=self.gstate) # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}

    def create_graphstate(self):
        return GraphState()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, we define `walk()` that walks a given AST node.
A major difference from MCI is in the functions that handle each node. Since it is a directed
graph traversal, our `walk()` accepts a list of parent nodes that point to this node, and also
invokes the various `on_*()` functions with the same list. These functions in turn return a list
of nodes that exit them.

While expressions, and single statements only have one node that comes out of them, control flow
structures and function calls can have multiple nodes that come out of them going into the next
node. For example, an `If` statement will have a node from both the `if.body` and `if.orelse`
going into the next one.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def walk(self, node, myparents):
        if node is None: return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, myparents)
        raise SyntaxError('walk: Not Implemented in %s' % type(node))

class PyCFGExtractor(PyCFGExtractor):
    def parse(self, src):
        return ast.parse(src)

    def eval(self, src):
        node = self.parse(src)
        nodes = self.walk(node, [self.founder])
        self.last_node = CFGNode(parents=nodes, ast=ast.parse('stop').body[0], state=self.gstate)
        ast.copy_location(self.last_node.ast_node, self.founder.ast_node)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def walk(self, node, myparents):
        if node is None: return
        fname = &quot;on_%s&quot; % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, myparents)
        raise SyntaxError(&#x27;walk: Not Implemented in %s&#x27; % type(node))

class PyCFGExtractor(PyCFGExtractor):
    def parse(self, src):
        return ast.parse(src)

    def eval(self, src):
        node = self.parse(src)
        nodes = self.walk(node, [self.founder])
        self.last_node = CFGNode(parents=nodes, ast=ast.parse(&#x27;stop&#x27;).body[0], state=self.gstate)
        ast.copy_location(self.last_node.ast_node, self.founder.ast_node)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Pass

The pass statement is trivial. It simply adds one more node.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the CFG from a single pass statement.


<!--
############
s = """\
pass
"""

cfge = PyCFGExtractor()
cfge.on_pass(node=ast.parse(s).body[0], myparents=[start])
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
pass
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.on_pass(node=ast.parse(s).body[0], myparents=[start])
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="70pt" height="124pt"
 viewBox="0.00 0.00 70.00 124.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 120)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-120 66,-120 66,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-94" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-94" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-90.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="58,-36 4,-36 4,0 58,0 58,-36"/>
<text text-anchor="middle" x="31" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M31,-71.6086C31,-63.7272 31,-54.7616 31,-46.4482"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-46.3974 31,-36.3975 27.5001,-46.3975 34.5001,-46.3974"/>
</g>
</g>
</svg>
#### Module(stmt* body)

We next define the `Module`. A python module is composed of a sequence of statements,
and the graph is a linear path through these statements. That is, each time a statement
is executed, we make a link from it to the next statement.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_module(self, node, myparents):
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_module(self, node, myparents):
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the CFG from the following which is wrapped in a module

<!--
############
s = """\
pass
pass
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
pass
pass
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="70pt" height="196pt"
 viewBox="0.00 0.00 70.00 196.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 192)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-192 66,-192 66,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-166" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-166" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-162.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="58,-108 4,-108 4,-72 58,-72 58,-108"/>
<text text-anchor="middle" x="31" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M31,-143.6086C31,-135.7272 31,-126.7616 31,-118.4482"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-118.3974 31,-108.3975 27.5001,-118.3975 34.5001,-118.3974"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<polygon fill="none" stroke="#000000" points="58,-36 4,-36 4,0 58,0 58,-36"/>
<text text-anchor="middle" x="31" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M31,-71.8314C31,-64.131 31,-54.9743 31,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-46.4132 31,-36.4133 27.5001,-46.4133 34.5001,-46.4132"/>
</g>
</g>
</svg>
### Expressions
#### Primitives

How should we handle primitives? Since they are simply interpreted as is, they can be embedded right in.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_str(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return p

    def on_num(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return p

    def on_constant(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_str(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p

    def on_num(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p

    def on_constant(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
They however, are simple expressions

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node, state=self.gstate)]
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node, state=self.gstate)]
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Generating the following CFG


<!--
############
s = """\
10
'a'
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
10
&#x27;a&#x27;
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="70pt" height="196pt"
 viewBox="0.00 0.00 70.00 196.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 192)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-192 66,-192 66,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-166" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-166" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-162.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 2 -->
<g id="node2" class="node">
<title>2</title>
<polygon fill="none" stroke="#000000" points="58,-108 4,-108 4,-72 58,-72 58,-108"/>
<text text-anchor="middle" x="31" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">10</text>
</g>
<!-- 0&#45;&gt;2 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M31,-143.6086C31,-135.7272 31,-126.7616 31,-118.4482"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-118.3974 31,-108.3975 27.5001,-118.3975 34.5001,-118.3974"/>
</g>
<!-- 4 -->
<g id="node3" class="node">
<title>4</title>
<polygon fill="none" stroke="#000000" points="58,-36 4,-36 4,0 58,0 58,-36"/>
<text text-anchor="middle" x="31" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">&#39;a&#39;</text>
</g>
<!-- 2&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>2&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M31,-71.8314C31,-64.131 31,-54.9743 31,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-46.4132 31,-36.4133 27.5001,-46.4133 34.5001,-46.4132"/>
</g>
</g>
</svg>
### Arithmetic expressions

The following implements the arithmetic expressions. The `unaryop()` simply walks
the arguments and adds the current node to the chain. The `binop()` has to walk
the left argument, then walk the right argument, and finally insert the current
node in the chain. `compare()` is again similar to `binop()`. `expr()`, again has
only one argument to walk, and one node out of it.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_unaryop(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return self.walk(node.operand, p)

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        p = [CFGNode(parents=right, ast=node, annot='', state=self.gstate)]
        return p

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        p = [CFGNode(parents=right, ast=node, annot='', state=self.gstate)]
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_unaryop(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return self.walk(node.operand, p)

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        p = [CFGNode(parents=right, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        p = [CFGNode(parents=right, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
CFG for this expression


<!--
############
s = """
10+1
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;
10+1
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="70pt" height="124pt"
 viewBox="0.00 0.00 70.00 124.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 120)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-120 66,-120 66,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-94" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-94" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-90.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 4 -->
<g id="node2" class="node">
<title>4</title>
<polygon fill="none" stroke="#000000" points="62,-36 0,-36 0,0 62,0 62,-36"/>
<text text-anchor="middle" x="31" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">(10 + 1)</text>
</g>
<!-- 0&#45;&gt;4 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M31,-71.6086C31,-63.7272 31,-54.7616 31,-46.4482"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-46.3974 31,-36.3975 27.5001,-46.3975 34.5001,-46.3974"/>
</g>
</g>
</svg>
#### Assign(expr* targets, expr value)

Unlike MCI, assignment is simple as it has only a single node coming out of it.

The following are not yet implemented:

* AugAssign(expr target, operator op, expr value)
* AnnAssign(expr target, expr annotation, expr? value, int simple)

Further, we do not yet implement parallel assignments.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_assign(self, node, myparents):
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        p = self.walk(node.value, p)
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_assign(self, node, myparents):
        if len(node.targets) &gt; 1: raise NotImplemented(&#x27;Parallel assignments&#x27;)
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        p = self.walk(node.value, p)
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """
a = 10+1
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;
a = 10+1
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="91pt" height="124pt"
 viewBox="0.00 0.00 91.00 124.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 120)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-120 87,-120 87,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="41.5" cy="-94" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="41.5" cy="-94" rx="31" ry="22"/>
<text text-anchor="start" x="29.5" y="-90.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="83,-36 0,-36 0,0 83,0 83,-36"/>
<text text-anchor="middle" x="41.5" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = (10 + 1)</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M41.5,-71.6086C41.5,-63.7272 41.5,-54.7616 41.5,-46.4482"/>
<polygon fill="#000000" stroke="#000000" points="45.0001,-46.3974 41.5,-36.3975 38.0001,-46.3975 45.0001,-46.3974"/>
</g>
</g>
</svg>
 
#### Name

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return p

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot=&#x27;&#x27;, state=self.gstate)]
        return p
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Control structures

#### If

We now come to the control structures. For the `if` statement, we have two
parallel paths. We first evaluate the test expression, then add a new node
corresponding to the if statement, and provide the paths through the `if.body`
and `if.orelse`.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_if(self, node, myparents):
        p = self.walk(node.test, myparents)
        test_node = [CFGNode(parents=p, ast=node, annot="if: %s" % ast.unparse(node.test).strip(), state=self.gstate)]
        g1 = test_node
        g_true = [CFGNode(parents=g1, ast=None, label="if:True", annot='', state=self.gstate)]
        g1 = g_true
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        g_false = [CFGNode(parents=g2, ast=None, label="if:False", annot='', state=self.gstate)]
        g2 = g_false
        for n in node.orelse:
            g2 = self.walk(n, g2)
        return g1 + g2

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_if(self, node, myparents):
        p = self.walk(node.test, myparents)
        test_node = [CFGNode(parents=p, ast=node, annot=&quot;if: %s&quot; % ast.unparse(node.test).strip(), state=self.gstate)]
        g1 = test_node
        g_true = [CFGNode(parents=g1, ast=None, label=&quot;if:True&quot;, annot=&#x27;&#x27;, state=self.gstate)]
        g1 = g_true
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        g_false = [CFGNode(parents=g2, ast=None, label=&quot;if:False&quot;, annot=&#x27;&#x27;, state=self.gstate)]
        g2 = g_false
        for n in node.orelse:
            g2 = self.walk(n, g2)
        return g1 + g2
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example


<!--
############
s = """\
a = 1
if a>1:
    a = 1
else:
    a = 0
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
a = 1
if a&gt;1:
    a = 1
else:
    a = 0
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="137pt" height="268pt"
 viewBox="0.00 0.00 136.68 268.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 264)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-264 132.682,-264 132.682,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="64.341" cy="-238" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="64.341" cy="-238" rx="31" ry="22"/>
<text text-anchor="start" x="52.341" y="-234.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="91.341,-180 37.341,-180 37.341,-144 91.341,-144 91.341,-180"/>
<text text-anchor="middle" x="64.341" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M64.341,-215.6086C64.341,-207.7272 64.341,-198.7616 64.341,-190.4482"/>
<polygon fill="#000000" stroke="#000000" points="67.8411,-190.3974 64.341,-180.3975 60.8411,-190.3975 67.8411,-190.3974"/>
</g>
<!-- 6 -->
<g id="node3" class="node">
<title>6</title>
<polygon fill="none" stroke="#000000" points="64.341,-108 .1586,-90 64.341,-72 128.5234,-90 64.341,-108"/>
<text text-anchor="middle" x="64.341" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (a &gt; 1)</text>
</g>
<!-- 1&#45;&gt;6 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M64.341,-143.8314C64.341,-136.131 64.341,-126.9743 64.341,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="67.8411,-118.4132 64.341,-108.4133 60.8411,-118.4133 67.8411,-118.4132"/>
</g>
<!-- 8 -->
<g id="node4" class="node">
<title>8</title>
<polygon fill="none" stroke="#000000" points="55.341,-36 1.341,-36 1.341,0 55.341,0 55.341,-36"/>
<text text-anchor="middle" x="28.341" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = 1</text>
</g>
<!-- 6&#45;&gt;8 -->
<g id="edge3" class="edge">
<title>6&#45;&gt;8</title>
<path fill="none" stroke="#0000ff" d="M56.3514,-74.0209C52.113,-65.5441 46.7889,-54.8957 41.9236,-45.1652"/>
<polygon fill="#0000ff" stroke="#0000ff" points="45.0527,-43.5971 37.45,-36.2181 38.7917,-46.7276 45.0527,-43.5971"/>
</g>
<!-- 11 -->
<g id="node5" class="node">
<title>11</title>
<polygon fill="none" stroke="#000000" points="127.341,-36 73.341,-36 73.341,0 127.341,0 127.341,-36"/>
<text text-anchor="middle" x="100.341" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = 0</text>
</g>
<!-- 6&#45;&gt;11 -->
<g id="edge4" class="edge">
<title>6&#45;&gt;11</title>
<path fill="none" stroke="#ff0000" d="M72.3306,-74.0209C76.569,-65.5441 81.8932,-54.8957 86.7584,-45.1652"/>
<polygon fill="#ff0000" stroke="#ff0000" points="89.8903,-46.7276 91.232,-36.2181 83.6293,-43.5971 89.8903,-46.7276"/>
</g>
</g>
</svg>
#### While
The `while` statement is more complex than the `if` statement. For one,
we need to provide a way to evaluate the condition at the beginning of
each iteration.

Essentially, given something like this:

```python
while x > 0:
    statement1
    if x:
       continue;
    if y:
       break
    statement2
```

We need to expand this into:

```
lbl1: v = x > 0
lbl2: if not v: goto lbl2
      statement1
      if x: goto lbl1
      if y: goto lbl3
      statement2
      goto lbl1
lbl3: ...

```

The basic idea is that when we walk the `node.body`, if there is a break
statement, it will start searching up the parent chain, until it finds a node with
`loop_entry` label. Then it will attach itself to the `exit_nodes` as one
of the exits.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_while(self, node, myparents):
        loop_id = self.gstate.counter
        lbl1_node = CFGNode(parents=myparents, ast=node, label='loop_entry', annot='%s:while' % loop_id, state=self.gstate)
        p = self.walk(node.test, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=node.test, label='while:test',
               annot='if: %s' % ast.unparse(node.test).strip(), state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node], ast=None, label="if:False", annot='', state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node], ast=None, label="if:True", annot='', state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        for n in node.body:
            p = self.walk(n, p)

        # the last node is the parent for the lb1 node.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_while(self, node, myparents):
        loop_id = self.gstate.counter
        lbl1_node = CFGNode(parents=myparents, ast=node, label=&#x27;loop_entry&#x27;, annot=&#x27;%s:while&#x27; % loop_id, state=self.gstate)
        p = self.walk(node.test, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=node.test, label=&#x27;while:test&#x27;,
               annot=&#x27;if: %s&#x27; % ast.unparse(node.test).strip(), state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node], ast=None, label=&quot;if:False&quot;, annot=&#x27;&#x27;, state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node], ast=None, label=&quot;if:True&quot;, annot=&#x27;&#x27;, state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        for n in node.body:
            p = self.walk(n, p)

        # the last node is the parent for the lb1 node.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
x = 1
while x > 0:
    x = x -1
y = x
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
while x &gt; 0:
    x = x -1
y = x
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="165pt" height="340pt"
 viewBox="0.00 0.00 165.00 340.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 336)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-336 161,-336 161,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="74" cy="-310" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="74" cy="-310" rx="31" ry="22"/>
<text text-anchor="start" x="62" y="-306.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="101,-252 47,-252 47,-216 101,-216 101,-252"/>
<text text-anchor="middle" x="74" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M74,-287.6086C74,-279.7272 74,-270.7616 74,-262.4482"/>
<polygon fill="#000000" stroke="#000000" points="77.5001,-262.3974 74,-252.3975 70.5001,-262.3975 77.5001,-262.3974"/>
</g>
<!-- 3 -->
<g id="node3" class="node">
<title>3</title>
<polygon fill="none" stroke="#000000" points="104.5,-180 43.5,-180 43.5,-144 104.5,-144 104.5,-180"/>
<text text-anchor="middle" x="74" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: while</text>
</g>
<!-- 1&#45;&gt;3 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M74,-215.8314C74,-208.131 74,-198.9743 74,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="77.5001,-190.4132 74,-180.4133 70.5001,-190.4133 77.5001,-190.4132"/>
</g>
<!-- 7 -->
<g id="node5" class="node">
<title>7</title>
<polygon fill="none" stroke="#000000" points="157,-108 65,-108 65,-72 157,-72 157,-108"/>
<text text-anchor="middle" x="111" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">while: (x &gt; 0)</text>
</g>
<!-- 3&#45;&gt;7 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;7</title>
<path fill="none" stroke="#000000" d="M83.3367,-143.8314C87.4243,-135.8771 92.3104,-126.369 96.8309,-117.5723"/>
<polygon fill="#000000" stroke="#000000" points="100.0799,-118.9074 101.5376,-108.4133 93.8539,-115.7078 100.0799,-118.9074"/>
</g>
<!-- 10 -->
<g id="node4" class="node">
<title>10</title>
<polygon fill="none" stroke="#000000" points="74,-36 0,-36 0,0 74,0 74,-36"/>
<text text-anchor="middle" x="37" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 10&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>10&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M40.1895,-36.0732C43.5609,-54.3489 49.3103,-83.3402 56,-108 58.3177,-116.5434 61.2173,-125.7197 64.0078,-134.0398"/>
<polygon fill="#000000" stroke="#000000" points="60.7542,-135.3418 67.3111,-143.6639 67.375,-133.0693 60.7542,-135.3418"/>
</g>
<!-- 7&#45;&gt;10 -->
<g id="edge5" class="edge">
<title>7&#45;&gt;10</title>
<path fill="none" stroke="#0000ff" d="M92.3267,-71.8314C83.4751,-63.219 72.7514,-52.7851 63.1105,-43.4048"/>
<polygon fill="#0000ff" stroke="#0000ff" points="65.2754,-40.6279 55.6674,-36.1628 60.3939,-45.645 65.2754,-40.6279"/>
</g>
<!-- 14 -->
<g id="node6" class="node">
<title>14</title>
<polygon fill="none" stroke="#000000" points="146,-36 92,-36 92,0 146,0 146,-36"/>
<text text-anchor="middle" x="119" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 7&#45;&gt;14 -->
<g id="edge6" class="edge">
<title>7&#45;&gt;14</title>
<path fill="none" stroke="#ff0000" d="M113.0187,-71.8314C113.8743,-64.131 114.8917,-54.9743 115.8426,-46.4166"/>
<polygon fill="#ff0000" stroke="#ff0000" points="119.3283,-46.7386 116.9541,-36.4133 112.3711,-45.9656 119.3283,-46.7386"/>
</g>
</g>
</svg>

#### Break

As we explained before, the `break` when it is encountred, looks up
the parent chain. Once it finds a parent that has the `loop_entry` label,
it attaches itself to that parent. The statements following the `break` are not
its immediate children. Hence, we return an empty list.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_break(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]

        assert hasattr(parent, 'exit_nodes')
        p = CFGNode(parents=myparents, ast=node, state=self.gstate)

        # make the break one of the parents of label node.
        parent.exit_nodes.append(p)

        # break doesnt have immediate children
        return []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_break(self, node, myparents):
        parent = myparents[0]
        while parent.label != &#x27;loop_entry&#x27;:
            parent = parent.parents[0]

        assert hasattr(parent, &#x27;exit_nodes&#x27;)
        p = CFGNode(parents=myparents, ast=node, state=self.gstate)

        # make the break one of the parents of label node.
        parent.exit_nodes.append(p)

        # break doesnt have immediate children
        return []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
x = 1
while x > 0:
    if x > 1:
        break
    x = x -1
y = x
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
while x &gt; 0:
    if x &gt; 1:
        break
    x = x -1
y = x
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="216pt" height="484pt"
 viewBox="0.00 0.00 216.00 484.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 480)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-480 212,-480 212,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="139" cy="-454" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="139" cy="-454" rx="31" ry="22"/>
<text text-anchor="start" x="127" y="-450.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="166,-396 112,-396 112,-360 166,-360 166,-396"/>
<text text-anchor="middle" x="139" y="-374.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M139,-431.6086C139,-423.7272 139,-414.7616 139,-406.4482"/>
<polygon fill="#000000" stroke="#000000" points="142.5001,-406.3974 139,-396.3975 135.5001,-406.3975 142.5001,-406.3974"/>
</g>
<!-- 3 -->
<g id="node3" class="node">
<title>3</title>
<polygon fill="none" stroke="#000000" points="169.5,-324 108.5,-324 108.5,-288 169.5,-288 169.5,-324"/>
<text text-anchor="middle" x="139" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: while</text>
</g>
<!-- 1&#45;&gt;3 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M139,-359.8314C139,-352.131 139,-342.9743 139,-334.4166"/>
<polygon fill="#000000" stroke="#000000" points="142.5001,-334.4132 139,-324.4133 135.5001,-334.4133 142.5001,-334.4132"/>
</g>
<!-- 7 -->
<g id="node5" class="node">
<title>7</title>
<polygon fill="none" stroke="#000000" points="139,-252 47,-252 47,-216 139,-216 139,-252"/>
<text text-anchor="middle" x="93" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">while: (x &gt; 0)</text>
</g>
<!-- 3&#45;&gt;7 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;7</title>
<path fill="none" stroke="#000000" d="M127.3923,-287.8314C122.2022,-279.7079 115.9768,-269.9637 110.2575,-261.0118"/>
<polygon fill="#000000" stroke="#000000" points="113.0974,-258.9559 104.764,-252.4133 107.1985,-262.7246 113.0974,-258.9559"/>
</g>
<!-- 17 -->
<g id="node4" class="node">
<title>17</title>
<polygon fill="none" stroke="#000000" points="208,-108 134,-108 134,-72 208,-72 208,-108"/>
<text text-anchor="middle" x="171" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 17&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>17&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M171.1191,-108.0105C171.0242,-126.2374 170.2823,-155.1915 167,-180 162.4793,-214.1686 153.2834,-252.7625 146.662,-278.13"/>
<polygon fill="#000000" stroke="#000000" points="143.2738,-277.2525 144.0908,-287.8158 150.0395,-279.0486 143.2738,-277.2525"/>
</g>
<!-- 13 -->
<g id="node6" class="node">
<title>13</title>
<polygon fill="none" stroke="#000000" points="93,-180 27.9788,-162 93,-144 158.0212,-162 93,-180"/>
<text text-anchor="middle" x="93" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (x &gt; 1)</text>
</g>
<!-- 7&#45;&gt;13 -->
<g id="edge5" class="edge">
<title>7&#45;&gt;13</title>
<path fill="none" stroke="#0000ff" d="M93,-215.8314C93,-208.131 93,-198.9743 93,-190.4166"/>
<polygon fill="#0000ff" stroke="#0000ff" points="96.5001,-190.4132 93,-180.4133 89.5001,-190.4133 96.5001,-190.4132"/>
</g>
<!-- 21 -->
<g id="node8" class="node">
<title>21</title>
<polygon fill="none" stroke="#000000" points="54,-36 0,-36 0,0 54,0 54,-36"/>
<text text-anchor="middle" x="27" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 7&#45;&gt;21 -->
<g id="edge8" class="edge">
<title>7&#45;&gt;21</title>
<path fill="none" stroke="#ff0000" d="M54.8117,-215.8328C40.9025,-207.0933 26.71,-195.1707 19,-180 -2.7363,-137.2301 8.003,-79.6352 17.6187,-45.892"/>
<polygon fill="#ff0000" stroke="#ff0000" points="20.9965,-46.8132 20.5296,-36.2286 14.294,-44.7941 20.9965,-46.8132"/>
</g>
<!-- 13&#45;&gt;17 -->
<g id="edge7" class="edge">
<title>13&#45;&gt;17</title>
<path fill="none" stroke="#ff0000" d="M108.0392,-148.1177C118.1347,-138.7988 131.7275,-126.2516 143.6994,-115.2006"/>
<polygon fill="#ff0000" stroke="#ff0000" points="146.3054,-117.5582 151.2795,-108.2035 141.5575,-112.4145 146.3054,-117.5582"/>
</g>
<!-- 15 -->
<g id="node7" class="node">
<title>15</title>
<polygon fill="none" stroke="#000000" points="101,-108 47,-108 47,-72 101,-72 101,-108"/>
<text text-anchor="middle" x="74" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">break</text>
</g>
<!-- 13&#45;&gt;15 -->
<g id="edge6" class="edge">
<title>13&#45;&gt;15</title>
<path fill="none" stroke="#0000ff" d="M88.4973,-144.937C86.3764,-136.9001 83.791,-127.1029 81.394,-118.0195"/>
<polygon fill="#0000ff" stroke="#0000ff" points="84.7383,-116.9751 78.8026,-108.1992 77.97,-118.7612 84.7383,-116.9751"/>
</g>
<!-- 15&#45;&gt;21 -->
<g id="edge9" class="edge">
<title>15&#45;&gt;21</title>
<path fill="none" stroke="#000000" d="M62.1399,-71.8314C56.8371,-63.7079 50.4763,-53.9637 44.6327,-45.0118"/>
<polygon fill="#000000" stroke="#000000" points="47.4169,-42.8739 39.0198,-36.4133 41.5552,-46.7003 47.4169,-42.8739"/>
</g>
</g>
</svg>

#### Continue

Continue is similar to `break`, except that it has to restart the loop. Hence,
it adds itself as a parent to the node with `loop_entry` attribute. As like `break`,
execution does not proceed to the lexically next statement after `continue`. Hence,
we return an empty set.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_continue(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]

        p = CFGNode(parents=myparents, ast=node, state=self.gstate)
        parent.add_parent(p)

        return []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_continue(self, node, myparents):
        parent = myparents[0]
        while parent.label != &#x27;loop_entry&#x27;:
            parent = parent.parents[0]

        p = CFGNode(parents=myparents, ast=node, state=self.gstate)
        parent.add_parent(p)

        return []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example


<!--
############
s = """\
x = 1
while x > 0:
    if x > 1:
        continue
    x = x -1
y = x
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
while x &gt; 0:
    if x &gt; 1:
        continue
    x = x -1
y = x
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="242pt" height="412pt"
 viewBox="0.00 0.00 241.53 412.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 408)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-408 237.5286,-408 237.5286,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="104.5286" cy="-382" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="104.5286" cy="-382" rx="31" ry="22"/>
<text text-anchor="start" x="92.5286" y="-378.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="131.5286,-324 77.5286,-324 77.5286,-288 131.5286,-288 131.5286,-324"/>
<text text-anchor="middle" x="104.5286" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M104.5286,-359.6086C104.5286,-351.7272 104.5286,-342.7616 104.5286,-334.4482"/>
<polygon fill="#000000" stroke="#000000" points="108.0287,-334.3974 104.5286,-324.3975 101.0287,-334.3975 108.0287,-334.3974"/>
</g>
<!-- 3 -->
<g id="node3" class="node">
<title>3</title>
<polygon fill="none" stroke="#000000" points="135.0286,-252 74.0286,-252 74.0286,-216 135.0286,-216 135.0286,-252"/>
<text text-anchor="middle" x="104.5286" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: while</text>
</g>
<!-- 1&#45;&gt;3 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M104.5286,-287.8314C104.5286,-280.131 104.5286,-270.9743 104.5286,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="108.0287,-262.4132 104.5286,-252.4133 101.0287,-262.4133 108.0287,-262.4132"/>
</g>
<!-- 7 -->
<g id="node6" class="node">
<title>7</title>
<polygon fill="none" stroke="#000000" points="150.5286,-180 58.5286,-180 58.5286,-144 150.5286,-144 150.5286,-180"/>
<text text-anchor="middle" x="104.5286" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">while: (x &gt; 0)</text>
</g>
<!-- 3&#45;&gt;7 -->
<g id="edge5" class="edge">
<title>3&#45;&gt;7</title>
<path fill="none" stroke="#000000" d="M104.5286,-215.8314C104.5286,-208.131 104.5286,-198.9743 104.5286,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="108.0287,-190.4132 104.5286,-180.4133 101.0287,-190.4133 108.0287,-190.4132"/>
</g>
<!-- 15 -->
<g id="node4" class="node">
<title>15</title>
<polygon fill="none" stroke="#000000" points="102.0286,-36 39.0286,-36 39.0286,0 102.0286,0 102.0286,-36"/>
<text text-anchor="middle" x="70.5286" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">continue</text>
</g>
<!-- 15&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>15&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M38.8073,-35.3342C25.6346,-44.3717 11.756,-56.7483 4.5286,-72 -2.3231,-86.4587 .1177,-92.62 4.5286,-108 16.3201,-149.1147 49.795,-186.1325 74.7879,-209.2397"/>
<polygon fill="#000000" stroke="#000000" points="72.4667,-211.8594 82.2386,-215.9534 77.1526,-206.6592 72.4667,-211.8594"/>
</g>
<!-- 17 -->
<g id="node5" class="node">
<title>17</title>
<polygon fill="none" stroke="#000000" points="233.5286,-36 159.5286,-36 159.5286,0 233.5286,0 233.5286,-36"/>
<text text-anchor="middle" x="196.5286" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 17&#45;&gt;3 -->
<g id="edge4" class="edge">
<title>17&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M209.3531,-36.1673C220.6401,-54.5162 233.9273,-83.5632 224.5286,-108 208.0459,-150.855 168.8334,-187.2386 139.6925,-209.7282"/>
<polygon fill="#000000" stroke="#000000" points="137.276,-207.1662 131.3888,-215.9749 141.4841,-212.7601 137.276,-207.1662"/>
</g>
<!-- 13 -->
<g id="node7" class="node">
<title>13</title>
<polygon fill="none" stroke="#000000" points="150.5286,-108 85.5074,-90 150.5286,-72 215.5498,-90 150.5286,-108"/>
<text text-anchor="middle" x="150.5286" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (x &gt; 1)</text>
</g>
<!-- 7&#45;&gt;13 -->
<g id="edge6" class="edge">
<title>7&#45;&gt;13</title>
<path fill="none" stroke="#0000ff" d="M116.1363,-143.8314C121.9235,-134.7731 128.9981,-123.6999 135.2228,-113.9568"/>
<polygon fill="#0000ff" stroke="#0000ff" points="138.2047,-115.7903 140.6392,-105.479 132.3059,-112.0216 138.2047,-115.7903"/>
</g>
<!-- 21 -->
<g id="node8" class="node">
<title>21</title>
<polygon fill="none" stroke="#000000" points="67.5286,-108 13.5286,-108 13.5286,-72 67.5286,-72 67.5286,-108"/>
<text text-anchor="middle" x="40.5286" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 7&#45;&gt;21 -->
<g id="edge9" class="edge">
<title>7&#45;&gt;21</title>
<path fill="none" stroke="#ff0000" d="M88.3787,-143.8314C80.8569,-135.3694 71.772,-125.1489 63.5482,-115.8971"/>
<polygon fill="#ff0000" stroke="#ff0000" points="66.1555,-113.5621 56.8959,-108.4133 60.9237,-118.2127 66.1555,-113.5621"/>
</g>
<!-- 13&#45;&gt;15 -->
<g id="edge7" class="edge">
<title>13&#45;&gt;15</title>
<path fill="none" stroke="#0000ff" d="M135.1038,-76.1177C124.7494,-66.7988 110.8081,-54.2516 98.5292,-43.2006"/>
<polygon fill="#0000ff" stroke="#0000ff" points="100.5291,-40.2917 90.7547,-36.2035 95.8463,-45.4947 100.5291,-40.2917"/>
</g>
<!-- 13&#45;&gt;17 -->
<g id="edge8" class="edge">
<title>13&#45;&gt;17</title>
<path fill="none" stroke="#ff0000" d="M160.5099,-74.3771C166.0688,-65.6762 173.1405,-54.6074 179.5434,-44.5855"/>
<polygon fill="#ff0000" stroke="#ff0000" points="182.5086,-46.4451 184.9431,-36.1338 176.6097,-42.6764 182.5086,-46.4451"/>
</g>
</g>
</svg>

#### For

The `For` statement in Python is rather complex. Given a for loop as below

```python
for i in my_expr:
    statement1
    statement2
```

This has to be extracted to the following:

```python
lbl1: 
      __iv = iter(my_expr)
lbl2: if __iv.length_hint() > 0: goto lbl3
      i = next(__iv)
      statement1
      statement2
lbl3: ...
```
We need `on_call()` for implementing `on_for()`. Essentially, we walk through
the arguments, then add a node corresponding to the call to the parents.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_call(self, node, myparents):
        p = myparents
        for a in node.args:
            p = self.walk(a, p)
        myparents[0].add_calls(node.func)
        p = [CFGNode(parents=p, ast=node, label='call', annot='', state=self.gstate)]
        return p

class PyCFGExtractor(PyCFGExtractor):
    def on_for(self, node, myparents):
        #node.target in node.iter: node.body
        loop_id = self.gstate.counter

        for_pre = CFGNode(parents=myparents, ast=None, label='for_pre', annot='', state=self.gstate)

        init_node = ast.parse('__iv_%d = iter(%s)' % (loop_id, ast.unparse(node.iter).strip())).body[0]
        p = self.walk(init_node, [for_pre])

        lbl1_node = CFGNode(parents=p, ast=node, label='loop_entry', annot='%s: for' % loop_id, state=self.gstate)
        _test_node = ast.parse('__iv_%d.__length__hint__() > 0' % loop_id).body[0].value
        p = self.walk(_test_node, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=_test_node, label='for:test', annot='for: %s' % ast.unparse(_test_node).strip(), state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node], ast=None, label="if:False", annot='', state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node], ast=None, label="if:True", annot='', state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        # now we evaluate the body, one at a time.
        for n in node.body:
            p = self.walk(n, p)

        # the test node is looped back at the end of processing.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_call(self, node, myparents):
        p = myparents
        for a in node.args:
            p = self.walk(a, p)
        myparents[0].add_calls(node.func)
        p = [CFGNode(parents=p, ast=node, label=&#x27;call&#x27;, annot=&#x27;&#x27;, state=self.gstate)]
        return p

class PyCFGExtractor(PyCFGExtractor):
    def on_for(self, node, myparents):
        #node.target in node.iter: node.body
        loop_id = self.gstate.counter

        for_pre = CFGNode(parents=myparents, ast=None, label=&#x27;for_pre&#x27;, annot=&#x27;&#x27;, state=self.gstate)

        init_node = ast.parse(&#x27;__iv_%d = iter(%s)&#x27; % (loop_id, ast.unparse(node.iter).strip())).body[0]
        p = self.walk(init_node, [for_pre])

        lbl1_node = CFGNode(parents=p, ast=node, label=&#x27;loop_entry&#x27;, annot=&#x27;%s: for&#x27; % loop_id, state=self.gstate)
        _test_node = ast.parse(&#x27;__iv_%d.__length__hint__() &gt; 0&#x27; % loop_id).body[0].value
        p = self.walk(_test_node, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=_test_node, label=&#x27;for:test&#x27;, annot=&#x27;for: %s&#x27; % ast.unparse(_test_node).strip(), state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node], ast=None, label=&quot;if:False&quot;, annot=&#x27;&#x27;, state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node], ast=None, label=&quot;if:True&quot;, annot=&#x27;&#x27;, state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        # now we evaluate the body, one at a time.
        for n in node.body:
            p = self.walk(n, p)

        # the test node is looped back at the end of processing.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
x = 1
for i in val:
    x = x -1
y = x
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
for i in val:
    x = x -1
y = x
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="263pt" height="412pt"
 viewBox="0.00 0.00 262.50 412.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 408)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-408 258.5,-408 258.5,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="77" cy="-382" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="77" cy="-382" rx="31" ry="22"/>
<text text-anchor="start" x="65" y="-378.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="104,-324 50,-324 50,-288 104,-288 104,-324"/>
<text text-anchor="middle" x="77" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M77,-359.6086C77,-351.7272 77,-342.7616 77,-334.4482"/>
<polygon fill="#000000" stroke="#000000" points="80.5001,-334.3974 77,-324.3975 73.5001,-334.3975 80.5001,-334.3974"/>
</g>
<!-- 4 -->
<g id="node3" class="node">
<title>4</title>
<polygon fill="none" stroke="#000000" points="133.5,-252 20.5,-252 20.5,-216 133.5,-216 133.5,-252"/>
<text text-anchor="middle" x="77" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">__iv_3 = iter(val)</text>
</g>
<!-- 1&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M77,-287.8314C77,-280.131 77,-270.9743 77,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="80.5001,-262.4132 77,-252.4133 73.5001,-262.4133 80.5001,-262.4132"/>
</g>
<!-- 6 -->
<g id="node4" class="node">
<title>6</title>
<polygon fill="none" stroke="#000000" points="104,-180 50,-180 50,-144 104,-144 104,-180"/>
<text text-anchor="middle" x="77" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: for</text>
</g>
<!-- 4&#45;&gt;6 -->
<g id="edge3" class="edge">
<title>4&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M77,-215.8314C77,-208.131 77,-198.9743 77,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="80.5001,-190.4132 77,-180.4133 73.5001,-190.4133 80.5001,-190.4132"/>
</g>
<!-- 9 -->
<g id="node6" class="node">
<title>9</title>
<polygon fill="none" stroke="#000000" points="254.5,-108 37.5,-108 37.5,-72 254.5,-72 254.5,-108"/>
<text text-anchor="middle" x="146" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">for: (__iv_3.__length__hint__() &gt; 0)</text>
</g>
<!-- 6&#45;&gt;9 -->
<g id="edge5" class="edge">
<title>6&#45;&gt;9</title>
<path fill="none" stroke="#000000" d="M94.4116,-143.8314C102.521,-135.3694 112.3156,-125.1489 121.182,-115.8971"/>
<polygon fill="#000000" stroke="#000000" points="123.9618,-118.0549 128.354,-108.4133 118.9079,-113.2115 123.9618,-118.0549"/>
</g>
<!-- 12 -->
<g id="node5" class="node">
<title>12</title>
<polygon fill="none" stroke="#000000" points="74,-36 0,-36 0,0 74,0 74,-36"/>
<text text-anchor="middle" x="37" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 12&#45;&gt;6 -->
<g id="edge4" class="edge">
<title>12&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M30.4399,-36.2395C24.8016,-54.8984 18.8944,-84.415 28,-108 32.1192,-118.6694 39.4336,-128.5335 47.1749,-136.8319"/>
<polygon fill="#000000" stroke="#000000" points="44.7819,-139.3887 54.325,-143.9909 49.7348,-134.442 44.7819,-139.3887"/>
</g>
<!-- 9&#45;&gt;12 -->
<g id="edge6" class="edge">
<title>9&#45;&gt;12</title>
<path fill="none" stroke="#0000ff" d="M118.4947,-71.8314C104.682,-62.7074 87.7744,-51.539 72.9471,-41.7449"/>
<polygon fill="#0000ff" stroke="#0000ff" points="74.7696,-38.7541 64.4965,-36.1628 70.9114,-44.5949 74.7696,-38.7541"/>
</g>
<!-- 16 -->
<g id="node7" class="node">
<title>16</title>
<polygon fill="none" stroke="#000000" points="173,-36 119,-36 119,0 173,0 173,-36"/>
<text text-anchor="middle" x="146" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 9&#45;&gt;16 -->
<g id="edge7" class="edge">
<title>9&#45;&gt;16</title>
<path fill="none" stroke="#ff0000" d="M146,-71.8314C146,-64.131 146,-54.9743 146,-46.4166"/>
<polygon fill="#ff0000" stroke="#ff0000" points="149.5001,-46.4132 146,-36.4133 142.5001,-46.4133 149.5001,-46.4132"/>
</g>
</g>
</svg>


<!--
############
s = """\
x = 1
for i in val:
    if x > 1:
        break
    x = x -1
y = x
"""

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
for i in val:
    if x &gt; 1:
        break
    x = x -1
y = x
&quot;&quot;&quot;

cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
<svg width="276pt" height="556pt"
 viewBox="0.00 0.00 275.50 556.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 552)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-552 271.5,-552 271.5,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="176.5" cy="-526" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="176.5" cy="-526" rx="31" ry="22"/>
<text text-anchor="start" x="164.5" y="-522.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="203.5,-468 149.5,-468 149.5,-432 203.5,-432 203.5,-468"/>
<text text-anchor="middle" x="176.5" y="-446.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M176.5,-503.6086C176.5,-495.7272 176.5,-486.7616 176.5,-478.4482"/>
<polygon fill="#000000" stroke="#000000" points="180.0001,-478.3974 176.5,-468.3975 173.0001,-478.3975 180.0001,-478.3974"/>
</g>
<!-- 4 -->
<g id="node3" class="node">
<title>4</title>
<polygon fill="none" stroke="#000000" points="233,-396 120,-396 120,-360 233,-360 233,-396"/>
<text text-anchor="middle" x="176.5" y="-374.3" font-family="Times,serif" font-size="14.00" fill="#000000">__iv_3 = iter(val)</text>
</g>
<!-- 1&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M176.5,-431.8314C176.5,-424.131 176.5,-414.9743 176.5,-406.4166"/>
<polygon fill="#000000" stroke="#000000" points="180.0001,-406.4132 176.5,-396.4133 173.0001,-406.4133 180.0001,-406.4132"/>
</g>
<!-- 6 -->
<g id="node4" class="node">
<title>6</title>
<polygon fill="none" stroke="#000000" points="203.5,-324 149.5,-324 149.5,-288 203.5,-288 203.5,-324"/>
<text text-anchor="middle" x="176.5" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: for</text>
</g>
<!-- 4&#45;&gt;6 -->
<g id="edge3" class="edge">
<title>4&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M176.5,-359.8314C176.5,-352.131 176.5,-342.9743 176.5,-334.4166"/>
<polygon fill="#000000" stroke="#000000" points="180.0001,-334.4132 176.5,-324.4133 173.0001,-334.4133 180.0001,-334.4132"/>
</g>
<!-- 9 -->
<g id="node6" class="node">
<title>9</title>
<polygon fill="none" stroke="#000000" points="217,-252 0,-252 0,-216 217,-216 217,-252"/>
<text text-anchor="middle" x="108.5" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">for: (__iv_3.__length__hint__() &gt; 0)</text>
</g>
<!-- 6&#45;&gt;9 -->
<g id="edge5" class="edge">
<title>6&#45;&gt;9</title>
<path fill="none" stroke="#000000" d="M159.3407,-287.8314C151.3489,-279.3694 141.6962,-269.1489 132.9584,-259.8971"/>
<polygon fill="#000000" stroke="#000000" points="135.3011,-257.2802 125.8903,-252.4133 130.212,-262.0866 135.3011,-257.2802"/>
</g>
<!-- 19 -->
<g id="node5" class="node">
<title>19</title>
<polygon fill="none" stroke="#000000" points="267.5,-108 193.5,-108 193.5,-72 267.5,-72 267.5,-108"/>
<text text-anchor="middle" x="230.5" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 19&#45;&gt;6 -->
<g id="edge4" class="edge">
<title>19&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M234.0997,-108.3394C239.3068,-139.2841 246.2981,-203.2576 226.5,-252 222.193,-262.6037 214.7781,-272.3985 206.9578,-280.652"/>
<polygon fill="#000000" stroke="#000000" points="204.3973,-278.2615 199.7393,-287.7775 209.3149,-283.2432 204.3973,-278.2615"/>
</g>
<!-- 15 -->
<g id="node7" class="node">
<title>15</title>
<polygon fill="none" stroke="#000000" points="152.5,-180 87.4788,-162 152.5,-144 217.5212,-162 152.5,-180"/>
<text text-anchor="middle" x="152.5" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (x &gt; 1)</text>
</g>
<!-- 9&#45;&gt;15 -->
<g id="edge6" class="edge">
<title>9&#45;&gt;15</title>
<path fill="none" stroke="#0000ff" d="M119.6031,-215.8314C125.0822,-206.8656 131.7677,-195.9257 137.6772,-186.2555"/>
<polygon fill="#0000ff" stroke="#0000ff" points="140.8126,-187.8369 143.0406,-177.479 134.8396,-184.1867 140.8126,-187.8369"/>
</g>
<!-- 23 -->
<g id="node9" class="node">
<title>23</title>
<polygon fill="none" stroke="#000000" points="113.5,-36 59.5,-36 59.5,0 113.5,0 113.5,-36"/>
<text text-anchor="middle" x="86.5" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 9&#45;&gt;23 -->
<g id="edge9" class="edge">
<title>9&#45;&gt;23</title>
<path fill="none" stroke="#ff0000" d="M95.1438,-215.5137C88.7492,-205.5235 81.782,-192.6657 78.5,-180 66.6962,-134.4477 73.7116,-79.336 80.0067,-46.5554"/>
<polygon fill="#ff0000" stroke="#ff0000" points="83.5209,-46.8379 82.0857,-36.3407 76.6616,-45.4417 83.5209,-46.8379"/>
</g>
<!-- 15&#45;&gt;19 -->
<g id="edge8" class="edge">
<title>15&#45;&gt;19</title>
<path fill="none" stroke="#ff0000" d="M167.5392,-148.1177C177.6347,-138.7988 191.2275,-126.2516 203.1994,-115.2006"/>
<polygon fill="#ff0000" stroke="#ff0000" points="205.8054,-117.5582 210.7795,-108.2035 201.0575,-112.4145 205.8054,-117.5582"/>
</g>
<!-- 17 -->
<g id="node8" class="node">
<title>17</title>
<polygon fill="none" stroke="#000000" points="160.5,-108 106.5,-108 106.5,-72 160.5,-72 160.5,-108"/>
<text text-anchor="middle" x="133.5" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">break</text>
</g>
<!-- 15&#45;&gt;17 -->
<g id="edge7" class="edge">
<title>15&#45;&gt;17</title>
<path fill="none" stroke="#0000ff" d="M147.9973,-144.937C145.8764,-136.9001 143.291,-127.1029 140.894,-118.0195"/>
<polygon fill="#0000ff" stroke="#0000ff" points="144.2383,-116.9751 138.3026,-108.1992 137.47,-118.7612 144.2383,-116.9751"/>
</g>
<!-- 17&#45;&gt;23 -->
<g id="edge10" class="edge">
<title>17&#45;&gt;23</title>
<path fill="none" stroke="#000000" d="M121.6399,-71.8314C116.3371,-63.7079 109.9763,-53.9637 104.1327,-45.0118"/>
<polygon fill="#000000" stroke="#000000" points="106.9169,-42.8739 98.5198,-36.4133 101.0552,-46.7003 106.9169,-42.8739"/>
</g>
</g>
</svg>


<!--
############
s = """\
x = 1
for i in val:
    if x > 1:
        continue
    x = x -1
y = x
"""
cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
for i in val:
    if x &gt; 1:
        continue
    x = x -1
y = x
&quot;&quot;&quot;
cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="261pt" height="484pt"
 viewBox="0.00 0.00 261.15 484.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 480)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-480 257.1485,-480 257.1485,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="122.9739" cy="-454" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="122.9739" cy="-454" rx="31" ry="22"/>
<text text-anchor="start" x="110.9739" y="-450.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="149.9739,-396 95.9739,-396 95.9739,-360 149.9739,-360 149.9739,-396"/>
<text text-anchor="middle" x="122.9739" y="-374.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M122.9739,-431.6086C122.9739,-423.7272 122.9739,-414.7616 122.9739,-406.4482"/>
<polygon fill="#000000" stroke="#000000" points="126.474,-406.3974 122.9739,-396.3975 119.474,-406.3975 126.474,-406.3974"/>
</g>
<!-- 4 -->
<g id="node3" class="node">
<title>4</title>
<polygon fill="none" stroke="#000000" points="179.4739,-324 66.4739,-324 66.4739,-288 179.4739,-288 179.4739,-324"/>
<text text-anchor="middle" x="122.9739" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">__iv_3 = iter(val)</text>
</g>
<!-- 1&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M122.9739,-359.8314C122.9739,-352.131 122.9739,-342.9743 122.9739,-334.4166"/>
<polygon fill="#000000" stroke="#000000" points="126.474,-334.4132 122.9739,-324.4133 119.474,-334.4133 126.474,-334.4132"/>
</g>
<!-- 6 -->
<g id="node4" class="node">
<title>6</title>
<polygon fill="none" stroke="#000000" points="149.9739,-252 95.9739,-252 95.9739,-216 149.9739,-216 149.9739,-252"/>
<text text-anchor="middle" x="122.9739" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">3: for</text>
</g>
<!-- 4&#45;&gt;6 -->
<g id="edge3" class="edge">
<title>4&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M122.9739,-287.8314C122.9739,-280.131 122.9739,-270.9743 122.9739,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="126.474,-262.4132 122.9739,-252.4133 119.474,-262.4133 126.474,-262.4132"/>
</g>
<!-- 9 -->
<g id="node7" class="node">
<title>9</title>
<polygon fill="none" stroke="#000000" points="231.4739,-180 14.4739,-180 14.4739,-144 231.4739,-144 231.4739,-180"/>
<text text-anchor="middle" x="122.9739" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">for: (__iv_3.__length__hint__() &gt; 0)</text>
</g>
<!-- 6&#45;&gt;9 -->
<g id="edge6" class="edge">
<title>6&#45;&gt;9</title>
<path fill="none" stroke="#000000" d="M122.9739,-215.8314C122.9739,-208.131 122.9739,-198.9743 122.9739,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="126.474,-190.4132 122.9739,-180.4133 119.474,-190.4133 126.474,-190.4132"/>
</g>
<!-- 17 -->
<g id="node5" class="node">
<title>17</title>
<polygon fill="none" stroke="#000000" points="114.4739,-36 51.4739,-36 51.4739,0 114.4739,0 114.4739,-36"/>
<text text-anchor="middle" x="82.9739" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">continue</text>
</g>
<!-- 17&#45;&gt;6 -->
<g id="edge4" class="edge">
<title>17&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M51.2572,-34.6273C37.1526,-43.722 21.7748,-56.3466 12.9739,-72 3.9465,-88.0562 -5.691,-163.3909 4.9739,-180 22.6759,-207.5686 58.3434,-221.2413 85.8535,-227.9093"/>
<polygon fill="#000000" stroke="#000000" points="85.4238,-231.3987 95.9431,-230.1363 86.9326,-224.5632 85.4238,-231.3987"/>
</g>
<!-- 19 -->
<g id="node6" class="node">
<title>19</title>
<polygon fill="none" stroke="#000000" points="245.9739,-36 171.9739,-36 171.9739,0 245.9739,0 245.9739,-36"/>
<text text-anchor="middle" x="208.9739" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = (x &#45; 1)</text>
</g>
<!-- 19&#45;&gt;6 -->
<g id="edge5" class="edge">
<title>19&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M220.4182,-36.1121C238.8561,-67.8351 270.2499,-134.4066 240.9739,-180 223.2718,-207.5686 187.6043,-221.2413 160.0943,-227.9093"/>
<polygon fill="#000000" stroke="#000000" points="159.0152,-224.5632 150.0047,-230.1363 160.524,-231.3987 159.0152,-224.5632"/>
</g>
<!-- 15 -->
<g id="node8" class="node">
<title>15</title>
<polygon fill="none" stroke="#000000" points="158.9739,-108 93.9527,-90 158.9739,-72 223.9951,-90 158.9739,-108"/>
<text text-anchor="middle" x="158.9739" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (x &gt; 1)</text>
</g>
<!-- 9&#45;&gt;15 -->
<g id="edge7" class="edge">
<title>9&#45;&gt;15</title>
<path fill="none" stroke="#0000ff" d="M132.0582,-143.8314C136.4324,-135.083 141.7464,-124.455 146.4933,-114.9611"/>
<polygon fill="#0000ff" stroke="#0000ff" points="149.6538,-116.4663 150.9955,-105.9568 143.3928,-113.3358 149.6538,-116.4663"/>
</g>
<!-- 23 -->
<g id="node9" class="node">
<title>23</title>
<polygon fill="none" stroke="#000000" points="75.9739,-108 21.9739,-108 21.9739,-72 75.9739,-72 75.9739,-108"/>
<text text-anchor="middle" x="48.9739" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = x</text>
</g>
<!-- 9&#45;&gt;23 -->
<g id="edge10" class="edge">
<title>9&#45;&gt;23</title>
<path fill="none" stroke="#ff0000" d="M104.3006,-143.8314C95.449,-135.219 84.7253,-124.7851 75.0844,-115.4048"/>
<polygon fill="#ff0000" stroke="#ff0000" points="77.2493,-112.6279 67.6412,-108.1628 72.3678,-117.645 77.2493,-112.6279"/>
</g>
<!-- 15&#45;&gt;17 -->
<g id="edge8" class="edge">
<title>15&#45;&gt;17</title>
<path fill="none" stroke="#0000ff" d="M143.9587,-75.7751C134.0936,-66.4292 120.9179,-53.947 109.3379,-42.9764"/>
<polygon fill="#0000ff" stroke="#0000ff" points="111.6761,-40.3703 102.0094,-36.0336 106.8618,-45.452 111.6761,-40.3703"/>
</g>
<!-- 15&#45;&gt;19 -->
<g id="edge9" class="edge">
<title>15&#45;&gt;19</title>
<path fill="none" stroke="#ff0000" d="M169.5776,-74.7307C175.7139,-65.8943 183.6057,-54.5303 190.7123,-44.2967"/>
<polygon fill="#ff0000" stroke="#ff0000" points="193.6123,-46.2568 196.4415,-36.0467 187.8627,-42.264 193.6123,-46.2568"/>
</g>
</g>
</svg>
#### FunctionDef

When defining a function, we should define the `return_nodes` for the
return statement to hook into. Further, we should also register our
functions.

Next, we have to decide: Do we want the call graph of the function definition to
be attached to the previous statements? In Python, the function definition itself
is independent of the previous statements. Hence, here, we choose not to have
parents for the definition.

<!--
############
DEFS_HAVE_PARENTS = False

class PyCFGExtractor(PyCFGExtractor):
    def on_functiondef(self, node, myparents):
        # name, args, body, decorator_list, returns
        fname = node.name
        args = node.args
        returns = node.returns
        p = myparents if DEFS_HAVE_PARENTS else []
        enter_node = CFGNode(parents=p, ast=node, label='enter',
                annot='<define>: %s' % node.name, state=self.gstate)
        enter_node.return_nodes = [] # sentinel

        p = [enter_node]
        for n in node.body:
            p = self.walk(n, p)

        enter_node.return_nodes.extend(p)

        self.functions[fname] = [enter_node, enter_node.return_nodes]
        self.functions_node[enter_node.lineno()] = fname

        return myparents

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
DEFS_HAVE_PARENTS = False

class PyCFGExtractor(PyCFGExtractor):
    def on_functiondef(self, node, myparents):
        # name, args, body, decorator_list, returns
        fname = node.name
        args = node.args
        returns = node.returns
        p = myparents if DEFS_HAVE_PARENTS else []
        enter_node = CFGNode(parents=p, ast=node, label=&#x27;enter&#x27;,
                annot=&#x27;&lt;define&gt;: %s&#x27; % node.name, state=self.gstate)
        enter_node.return_nodes = [] # sentinel

        p = [enter_node]
        for n in node.body:
            p = self.walk(n, p)

        enter_node.return_nodes.extend(p)

        self.functions[fname] = [enter_node, enter_node.return_nodes]
        self.functions_node[enter_node.lineno()] = fname

        return myparents
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Return

For `return`, we need to look up which function we have to return from.

<!--
############
class PyCFGExtractor(PyCFGExtractor):
    def on_return(self, node, myparents):
        parent = myparents[0]

        val_node = self.walk(node.value, myparents)
        # on return look back to the function definition.
        while not hasattr(parent, 'return_nodes'):
            parent = parent.parents[0]
        assert hasattr(parent, 'return_nodes')

        p = CFGNode(parents=val_node, ast=node, state=self.gstate)

        # make the break one of the parents of label node.
        parent.return_nodes.append(p)

        # return doesnt have immediate children
        return []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCFGExtractor(PyCFGExtractor):
    def on_return(self, node, myparents):
        parent = myparents[0]

        val_node = self.walk(node.value, myparents)
        # on return look back to the function definition.
        while not hasattr(parent, &#x27;return_nodes&#x27;):
            parent = parent.parents[0]
        assert hasattr(parent, &#x27;return_nodes&#x27;)

        p = CFGNode(parents=val_node, ast=node, state=self.gstate)

        # make the break one of the parents of label node.
        parent.return_nodes.append(p)

        # return doesnt have immediate children
        return []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
x = 1
def my_fn(v1, v2):
    if v1 > v2:
        return v1
    else:
        return v2
y = 2
"""
cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
x = 1
def my_fn(v1, v2):
    if v1 &gt; v2:
        return v1
    else:
        return v2
y = 2
&quot;&quot;&quot;
cfge = PyCFGExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
print(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<svg width="266pt" height="276pt"
 viewBox="0.00 0.00 266.00 276.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 272)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-272 262,-272 262,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="31" cy="-246" rx="27" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="31" cy="-246" rx="31" ry="22"/>
<text text-anchor="start" x="19" y="-242.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<polygon fill="none" stroke="#000000" points="58,-188 4,-188 4,-152 58,-152 58,-188"/>
<text text-anchor="middle" x="31" y="-166.3" font-family="Times,serif" font-size="14.00" fill="#000000">x = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M31,-223.6086C31,-215.7272 31,-206.7616 31,-198.4482"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-198.3974 31,-188.3975 27.5001,-198.3975 34.5001,-198.3974"/>
</g>
<!-- 15 -->
<g id="node8" class="node">
<title>15</title>
<polygon fill="none" stroke="#000000" points="58,-116 4,-116 4,-80 58,-80 58,-116"/>
<text text-anchor="middle" x="31" y="-94.3" font-family="Times,serif" font-size="14.00" fill="#000000">y = 2</text>
</g>
<!-- 1&#45;&gt;15 -->
<g id="edge7" class="edge">
<title>1&#45;&gt;15</title>
<path fill="none" stroke="#000000" d="M31,-151.8314C31,-144.131 31,-134.9743 31,-126.4166"/>
<polygon fill="#000000" stroke="#000000" points="34.5001,-126.4132 31,-116.4133 27.5001,-126.4133 34.5001,-126.4132"/>
</g>
<!-- 3 -->
<g id="node3" class="node">
<title>3</title>
<ellipse fill="none" stroke="#000000" cx="174" cy="-246" rx="71.4876" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="174" cy="-246" rx="75.4873" ry="22"/>
<text text-anchor="middle" x="174" y="-242.3" font-family="Times,serif" font-size="14.00" fill="#000000">&lt;define&gt;: my_fn</text>
</g>
<!-- 8 -->
<g id="node7" class="node">
<title>8</title>
<polygon fill="none" stroke="#000000" points="174,-188 96.581,-170 174,-152 251.419,-170 174,-188"/>
<text text-anchor="middle" x="174" y="-166.3" font-family="Times,serif" font-size="14.00" fill="#000000">if: (v1 &gt; v2)</text>
</g>
<!-- 3&#45;&gt;8 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;8</title>
<path fill="none" stroke="#000000" d="M174,-223.6086C174,-215.7272 174,-206.7616 174,-198.4482"/>
<polygon fill="#000000" stroke="#000000" points="177.5001,-198.3974 174,-188.3975 170.5001,-198.3975 177.5001,-198.3974"/>
</g>
<!-- 4 -->
<g id="node4" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="183" cy="-22" rx="63.0862" ry="18"/>
<ellipse fill="none" stroke="#000000" cx="183" cy="-22" rx="67.0888" ry="22"/>
<text text-anchor="middle" x="183" y="-18.3" font-family="Times,serif" font-size="14.00" fill="#000000">&lt;exit&gt;: my_fn</text>
</g>
<!-- 11 -->
<g id="node5" class="node">
<title>11</title>
<polygon fill="none" stroke="#000000" points="174,-116 108,-116 108,-80 174,-80 174,-116"/>
<text text-anchor="middle" x="141" y="-94.3" font-family="Times,serif" font-size="14.00" fill="#000000">return v1</text>
</g>
<!-- 11&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>11&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M150.9534,-79.9891C155.4654,-71.8246 160.9284,-61.9391 166.056,-52.6605"/>
<polygon fill="#000000" stroke="#000000" points="169.2506,-54.1158 171.0242,-43.6705 163.1239,-50.73 169.2506,-54.1158"/>
</g>
<!-- 14 -->
<g id="node6" class="node">
<title>14</title>
<polygon fill="none" stroke="#000000" points="258,-116 192,-116 192,-80 258,-80 258,-116"/>
<text text-anchor="middle" x="225" y="-94.3" font-family="Times,serif" font-size="14.00" fill="#000000">return v2</text>
</g>
<!-- 14&#45;&gt;4 -->
<g id="edge3" class="edge">
<title>14&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M215.0466,-79.9891C210.5346,-71.8246 205.0716,-61.9391 199.944,-52.6605"/>
<polygon fill="#000000" stroke="#000000" points="202.8761,-50.73 194.9758,-43.6705 196.7494,-54.1158 202.8761,-50.73"/>
</g>
<!-- 8&#45;&gt;11 -->
<g id="edge5" class="edge">
<title>8&#45;&gt;11</title>
<path fill="none" stroke="#0000ff" d="M166.5118,-153.6621C162.661,-145.2603 157.8655,-134.7974 153.475,-125.2181"/>
<polygon fill="#0000ff" stroke="#0000ff" points="156.6177,-123.6747 149.2694,-116.0423 150.2543,-126.5913 156.6177,-123.6747"/>
</g>
<!-- 8&#45;&gt;14 -->
<g id="edge6" class="edge">
<title>8&#45;&gt;14</title>
<path fill="none" stroke="#ff0000" d="M185.0662,-154.3771C191.2294,-145.6762 199.0698,-134.6074 206.1686,-124.5855"/>
<polygon fill="#ff0000" stroke="#ff0000" points="209.2311,-126.3171 212.1552,-116.1338 203.5189,-122.271 209.2311,-126.3171"/>
</g>
</g>
</svg>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
