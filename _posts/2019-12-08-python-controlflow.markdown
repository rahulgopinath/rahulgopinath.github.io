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
We [previously discussed](/post/2019/12/07/python-mci/) how one can write an interpreter for
Python. We hinted at that time that the machinery could be used for a variety of
other applications, including exctracting the call and control flow graph. In this
post, we will show how one can extract the control flow graph using such an interpteter.
Note that a much more complete implementation can be found [here](https://github.com/vrthra/pycfg).

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
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl">pydot-1.4.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl">metacircularinterpreter-0.0.1-py2.py3-none-any.whl</a></li>
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
__canvas__(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GraphState()
start = CFGNode(parents=[], ast=ast.parse(&#x27;start&#x27;).body, state=gs)
g = to_graph(gs.registry.items(), get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())


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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())


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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())


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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
        lbl1_node = CFGNode(parents=myparents, ast=node, label='loop_entry', annot='%s: while' % loop_id, state=self.gstate)
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
        lbl1_node = CFGNode(parents=myparents, ast=node, label=&#x27;loop_entry&#x27;, annot=&#x27;%s: while&#x27; % loop_id, state=self.gstate)
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
more

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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
more

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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
__canvas__(g.to_string())

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
__canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2019-12-08-python-controlflow.py).


The installable python wheel `pycfg` is available [here](/py/pycfg-0.0.1-py2.py3-none-any.whl). See the post "[The Python Control Flow Graph](/post/2019/12/08/python-controlflow/)" for further information.

