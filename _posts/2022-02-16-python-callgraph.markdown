---
published: true
title: A Minimal Static Call Graph for Python Programs
layout: post
comments: true
tags: callgraph
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
We [previously discussed](/post/2019/12/07/python-mci/) how one can write an
interpreter Python, and we made use of this machinery in generating a
[control flow graph](/post/2019/12/08/python-controlflow/).
In this post, we will show how one can extract the static call-graph using
the same machinery.
A [call-graph](https://en.wikipedia.org/wiki/Call_graph) is a directed graph
data structure that encodes the structure of function calls in a program.
One can extract the call-graph either dynamically or statically. A dynamic
call-grah can be constructed by following the execution path of the program
on multiple inputs. Such dynamic call-graphs under-approximate the actual
structure of the program to the functions that was covered by the set of
input. The dual of a dynamic call-graph is a static call-graph (the subject
of this post) which is constructed by statically analyzing the program. Such
call-graphs overapproximate the actual call-graph of the program (the
exceptions are when there are higher order functions and othe polymorphism).
As in control-flow graph, a static call-graph is another abstract view of the
interpreter.
Static call-graphs complement control flow graphs in static analysis. They
allow one to identify which functions may be impacted by a change in one
function (dependencies), evaluate reachability, and also can be used to
implement various traversals of the code.
Note that this is a limited proof of concept. It does not
implement the entire traversal other than what is required for us to get our
examples working.
#### Prerequisites
As before, we start with the prerequisite imports. Click on the bullets for
more information on how to obtain them.

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
<li><a href="https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl">metacircularinterpreter-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/07/python-mci/">Python Meta Circular Interpreter</a>".</li>
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
#### The graphical routines.

<!--
############
class Graphics:
    def display_dot(self, dotsrc): raise NotImplemented

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Graphics:
    def display_dot(self, dotsrc): raise NotImplemented
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The default class for Pyodide.

<!--
############
class WebGraphics(Graphics):
    def display_dot(self, dotsrc):
        __canvas__(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class WebGraphics(Graphics):
    def display_dot(self, dotsrc):
        __canvas__(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Use `CLIGraphics` if you are running it from the
command line.

<!--
############
class CLIGraphics(Graphics):
    def __init__(self):
        global graphviz
        import graphviz
        globals()['graphviz'] = graphviz
        self.i = 0

    def display_dot(self, dotsrc):
        graphviz.Source(dotsrc).render(format='png', outfile='%s.png' % self.i)
        self.i += 1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CLIGraphics(Graphics):
    def __init__(self):
        global graphviz
        import graphviz
        globals()[&#x27;graphviz&#x27;] = graphviz
        self.i = 0

    def display_dot(self, dotsrc):
        graphviz.Source(dotsrc).render(format=&#x27;png&#x27;, outfile=&#x27;%s.png&#x27; % self.i)
        self.i += 1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We use Pyodide here.

<!--
############
graphics = WebGraphics()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
graphics = WebGraphics()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `to_graph()` function produces a graph from the nodes in the registry.
This is more simplified than in control-flow because there is only one kind
of node in this graph -- a function.

<!--
############
def to_graph(my_nodes, comment=''):
    G = pydot.Dot(comment, graph_type="digraph")
    for nid, cnode in my_nodes:
        G.add_node(pydot.Node(cnode.name, label=cnode.name))
        for cn in cnode.calls:
            G.add_edge(pydot.Edge(cnode.name, cn.name))
    return G


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_graph(my_nodes, comment=&#x27;&#x27;):
    G = pydot.Dot(comment, graph_type=&quot;digraph&quot;)
    for nid, cnode in my_nodes:
        G.add_node(pydot.Node(cnode.name, label=cnode.name))
        for cn in cnode.calls:
            G.add_edge(pydot.Edge(cnode.name, cn.name))
    return G
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The GraphState
The call-graph is a graph, and hence we need a data structure for the *graph*.

<!--
############
class GraphState:
    def __init__(self):
        self.registry = {}

    def get_node(self, name):
        if name not in self.registry:
           self.registry[name] = CallNode(name)
        return self.registry[name]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GraphState:
    def __init__(self):
        self.registry = {}

    def get_node(self, name):
        if name not in self.registry:
           self.registry[name] = CallNode(name)
        return self.registry[name]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need a node class.

<!--
############
class CallNode:
    def __init__(self, name):
        self.name = name
        self.calls = []
        self.callers = []
        self.scope = []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallNode:
    def __init__(self, name):
        self.name = name
        self.calls = []
        self.callers = []
        self.scope = []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given that it is a directed graph node, we need the ability to add calls and
callers.

<!--
############
class CallNode(CallNode):
    def add_caller(self, c):
        self.callers.append(c)
        c.calls.append(self)

    def add_call(self, c):
        self.calls.append(c)
        c.callers.append(self)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallNode(CallNode):
    def add_caller(self, c):
        self.callers.append(c)
        c.calls.append(self)

    def add_call(self, c):
        self.calls.append(c)
        c.callers.append(self)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The context is really the lexical context (scope) in which a function was
defined. For example, functions may be defined in the context of modules
or classes, and classes may be defined in the context of modules.

<!--
############
class CallNode(CallNode):
    def add_context(self, parent):
        parent.scope.append(self)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallNode(CallNode):
    def add_context(self, parent):
        parent.scope.append(self)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We next define two convenience methods for printing any node.

<!--
############
class CallNode(CallNode):
    def __str__(self):
        return '%s calls:%s callers:%s' % (self.name, len(self.calls), len(self.callers))

    def __repr__(self):
        return '(%s %s %s)' % (self.name, str(self.calls), str(self.callers))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CallNode(CallNode):
    def __str__(self):
        return &#x27;%s calls:%s callers:%s&#x27; % (self.name, len(self.calls), len(self.callers))

    def __repr__(self):
        return &#x27;(%s %s %s)&#x27; % (self.name, str(self.calls), str(self.callers))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The usage of our graph structure is as below:

<!--
############
gs = GraphState()
start = gs.get_node('__module__')
g = to_graph(gs.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GraphState()
start = gs.get_node(&#x27;__module__&#x27;)
g = to_graph(gs.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Extracting the graph
The call-graph is essentially a source code walker, and shares the basic
structure with our interpreter.

<!--
############
class PyCallGraphExtractor(metacircularinterpreter.PyMCInterpreter):
    def __init__(self):
        self.gstate = self.create_graphstate()

    def create_graphstate(self):
        return GraphState()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(metacircularinterpreter.PyMCInterpreter):
    def __init__(self):
        self.gstate = self.create_graphstate()

    def create_graphstate(self):
        return GraphState()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As in previous posts, we define `walk()` that walks a given AST node.
A major difference from the control-flow graph is that we want to keep track
of the lexical
context in which a function is defined, but not necessarily the sequence.
So, our `walk()` accepts the node and the lexical context. It then
invokes the various `on_*()` functions with the same list. Since we ignore
the sequence of statements that resulted in a call, The return value is not
used.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def walk(self, node, parentcontext):
        if node is None: return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, parentcontext)
        raise SyntaxError('walk: Not Implemented in %s' % type(node))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def walk(self, node, parentcontext):
        if node is None: return
        fname = &quot;on_%s&quot; % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, parentcontext)
        raise SyntaxError(&#x27;walk: Not Implemented in %s&#x27; % type(node))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define `parse` which parses a given fragment and `eval` which
given a fragment, parses and walks the AST.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def parse(self, src):
        return ast.parse(src)

    def eval(self, src):
        node = self.parse(src)
        founder = CallNode('') # not in registry
        self.walk(node, founder)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def parse(self, src):
        return ast.parse(src)

    def eval(self, src):
        node = self.parse(src)
        founder = CallNode(&#x27;&#x27;) # not in registry
        self.walk(node, founder)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Module(stmt* body)
We first define the `Module`. The module is a basic context from where calls
to functions can be made.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_module(self, node, parentcontext):
        # the name of the module needs to be obtained elsewhere.
        m_node = self.gstate.get_node('__module__')
        m_node.add_context(parentcontext)
        for n in node.body:
            self.walk(n, m_node)
        return parentcontext


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_module(self, node, parentcontext):
        # the name of the module needs to be obtained elsewhere.
        m_node = self.gstate.get_node(&#x27;__module__&#x27;)
        m_node.add_context(parentcontext)
        for n in node.body:
            self.walk(n, m_node)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### FunctionDef
Similar to modules, we traverse function definitions looking for calls to
other functions.  Hence, we only have a basic traversal in place.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_functiondef(self, node, parentcontext):
        fn_node = self.gstate.get_node(node.name)
        fn_node.add_context(parentcontext)

        for n in node.body:
            self.walk(n, fn_node)

        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_functiondef(self, node, parentcontext):
        fn_node = self.gstate.get_node(node.name)
        fn_node.add_context(parentcontext)

        for n in node.body:
            self.walk(n, fn_node)

        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Pass
The pass statement is trivial. It does nothing but exist.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_pass(self, node, parentcontext): return parentcontext


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_pass(self, node, parentcontext): return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn():
    pass
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn():
    pass
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Name
The name is just a skeleton. It has no function other than to exist.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_name(self, node, parentcontext): return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_name(self, node, parentcontext): return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Return
The return statement can also have embedded function calls. Hence, we
traverse the value.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_return(self, node, parentcontext):
        self.walk(node.value, parentcontext)
        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_return(self, node, parentcontext):
        self.walk(node.value, parentcontext)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn():
    return v1
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn():
    return v1
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Call()
A call creates a link between two functions.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_call(self, node, parentcontext):
        for a in node.args:
            self.walk(a, parentcontext)

        mid = None
        if hasattr(node.func, 'id'): # ast.Name
            mid = node.func.id
        else: # ast.Attribute
            mid = node.func.value.id

        called = self.gstate.get_node(mid)
        parentcontext.add_call(called)
        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_call(self, node, parentcontext):
        for a in node.args:
            self.walk(a, parentcontext)

        mid = None
        if hasattr(node.func, &#x27;id&#x27;): # ast.Name
            mid = node.func.id
        else: # ast.Attribute
            mid = node.func.value.id

        called = self.gstate.get_node(mid)
        parentcontext.add_call(called)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\

def my_fn1():
    return my_fn2()

def my_fn2():
    return my_fn3()

def my_fn3():
    pass

"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\

def my_fn1():
    return my_fn2()

def my_fn2():
    return my_fn3()

def my_fn3():
    pass

&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Expressions can have function calls embedded. Hence, we traverse the value.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_expr(self, node, parentcontext):
        self.walk(node.value, parentcontext)
        return parentcontext


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_expr(self, node, parentcontext):
        self.walk(node.value, parentcontext)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn1():
    my_fn2()
    my_fn3()

def my_fn2():
    my_fn3()

def my_fn3():
    return my_fn1()

my_fn1()
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn1():
    my_fn2()
    my_fn3()

def my_fn2():
    my_fn3()

def my_fn3():
    return my_fn1()

my_fn1()
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Primitives
Similar to name, primitives also have no function other than to exist.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_str(self, node, parentcontext): return parentcontext

    def on_num(self, node, parentcontext): return parentcontext

    def on_constant(self, node, parentcontext): return parentcontext



############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_str(self, node, parentcontext): return parentcontext

    def on_num(self, node, parentcontext): return parentcontext

    def on_constant(self, node, parentcontext): return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Arithmetic expressions
For arithmetic expressions, we need to walk on the operands.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_unaryop(self, node, parentcontext):
        return self.walk(node.operand, parentcontext)

    def on_binop(self, node, parentcontext):
        self.walk(node.left, parentcontext)
        self.walk(node.right, parentcontext)
        return parentcontext

    def on_compare(self, node, parentcontext):
        self.walk(node.left, parentcontext)
        self.walk(node.comparators[0], parentcontext)
        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_unaryop(self, node, parentcontext):
        return self.walk(node.operand, parentcontext)

    def on_binop(self, node, parentcontext):
        self.walk(node.left, parentcontext)
        self.walk(node.right, parentcontext)
        return parentcontext

    def on_compare(self, node, parentcontext):
        self.walk(node.left, parentcontext)
        self.walk(node.comparators[0], parentcontext)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Assign(expr* targets, expr value)
For assignment, we walk the value.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_assign(self, node, parentcontext):
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')
        self.walk(node.value, parentcontext)
        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_assign(self, node, parentcontext):
        if len(node.targets) &gt; 1: raise NotImplemented(&#x27;Parallel assignments&#x27;)
        self.walk(node.value, parentcontext)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Control structures
#### If
We now come to the control structures. For the `if` statement, we have two
parallel paths. We first traverse the test expression, then the body of the
if branch, and the body of the else branch.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_if(self, node, parentcontext):
        self.walk(node.test, parentcontext)
        for n in node.body:
            self.walk(n, parentcontext)
        for n in node.orelse:
            self.walk(n, parentcontext)
        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_if(self, node, parentcontext):
        self.walk(node.test, parentcontext)
        for n in node.body:
            self.walk(n, parentcontext)
        for n in node.orelse:
            self.walk(n, parentcontext)
        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn():
    a = my_fn1()
    if a>1:
        a = my_fn2()
    else:
        a = my_fn3()

my_fn()
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn():
    a = my_fn1()
    if a&gt;1:
        a = my_fn2()
    else:
        a = my_fn3()

my_fn()
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### While

The `while` statement is more complex than the `if` statement, but the
essential idea is the same.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_while(self, node, parentcontext):
        self.walk(node.test, parentcontext)

        for n in node.body:
            self.walk(n, parentcontext)

        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_while(self, node, parentcontext):
        self.walk(node.test, parentcontext)

        for n in node.body:
            self.walk(n, parentcontext)

        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn():
   while my_fn1():
       x = my_fn2()

my_fn()
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn():
   while my_fn1():
       x = my_fn2()

my_fn()
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Break
Break and continue are simply skeletons.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_break(self, node, parentcontext): return parentcontext

    def on_continue(self, node, parentcontext): return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_break(self, node, parentcontext): return parentcontext

    def on_continue(self, node, parentcontext): return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
The `For` statement is again quite simple.

<!--
############
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_for(self, node, parentcontext):
        self.walk(node.target, parentcontext)
        self.walk(node.iter, parentcontext)

        for n in node.body: self.walk(n, parentcontext)
        for n in node.orelse: self.walk(n, parentcontext)

        return parentcontext

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class PyCallGraphExtractor(PyCallGraphExtractor):
    def on_for(self, node, parentcontext):
        self.walk(node.target, parentcontext)
        self.walk(node.iter, parentcontext)

        for n in node.body: self.walk(n, parentcontext)
        for n in node.orelse: self.walk(n, parentcontext)

        return parentcontext
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
s = """\
def my_fn():
    for i in my_fn1():
        my_fn2()

my_fn()
"""

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;\
def my_fn():
    for i in my_fn1():
        my_fn2()

my_fn()
&quot;&quot;&quot;

cfge = PyCallGraphExtractor()
cfge.eval(s)
g = to_graph(cfge.gstate.registry.items())
graphics.display_dot(g.to_string())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## What remains?

At this point, what we have is a very basic call-graph algorithm that
understands a restricted subset of Python. However, a lot more is left.

The main problem is that if you have higher order functions, it is very hard
to identify which functions can get called when the variable containing the
function is invoked. For example, the call-graph of

```
def f(x):
    x(1)

```
is almost impossible to compute because `x()` can be any function including
`f()` itself. Any polymorphic behavior (such as from objects) induce similar
ambiguity.

For example, many objects may override various operators such as arithmetic or
boolean operators, providing their own implementations. Given the dynamic
nature of Python, we can't identify such methods. That is, without full type
inference, accurate call-graphs are impossible. Even given full type
inference, we need accurate abstract interpretation of the program to
determine possible assignments (which we do not do here).

That is, while basic call-graph construction is easier than control-flow
construction, a complete call-graph is much harder than complete control-flow
graph.

## Related

We note that this post is a proof-of-concept, more intended for understanding
how to construct call-graphs than as a library for use in production. If you
need such libraries,
I recommend [Pyan](https://github.com/Technologicat/pyan), which seems to
work reasonably well, as well as [PyCG](https://github.com/vitsalis/pycg)
which is more rigorous.

For a much more indepth treatment of this subject, see the paper by
Salis et al.[^salis2021pycg] at ICSE 2021 (the result of which is PyCG),
by Yu[^yu2019empirical] and by Abadi et al.[^abadi2021nocfg].


[^salis2021pycg]: V Salis, T Sotiropoulos, P Louridas, D Spinellis, and D Mitropoulos. _Pycg: Practical call graph generation in python._ ICSE 2021.
[^yu2019empirical]: L Yu. _Empirical study of Python call graph_ ASE 2019.
[^abadi2021nocfg]: A Abadi, B Makovitzki, R Shemer, and S Tyszberowicz. _NoCFG: A Lightweight Approach for Sound Call Graph Approximation._ arXiv:2105.03099. 2021.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-02-16-python-callgraph.py).


