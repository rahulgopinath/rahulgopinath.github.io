---
published: true
title: Pyodide Canvas
layout: post
comments: true
tags: pyodide
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
others

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/pyparsing-2.4.7-py2.py3-none-any.whl">pyparsing-2.4.7-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/graphviz-0.16-py2.py3-none-any.whl">graphviz-0.16-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl">pydot-1.4.1-py2.py3-none-any.whl</a></li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/pyparsing-2.4.7-py2.py3-none-any.whl
https://rahul.gopinath.org/py/graphviz-0.16-py2.py3-none-any.whl
https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
define the picture

<!--
############
dotFormat = """
digraph G {
    node [shape=rect];

    subgraph cluster_0 {
        style=filled;
        color=lightgrey;
        node [style=filled,color=white];
        a0 -> a1 -> a2 -> a3;
        label = "Hello";
    }

    subgraph cluster_1 {
        node [style=filled];
        b0 -> b1 -> b2 -> b3;
        label = "World";
        color=blue
    }

    start -> a0;
    start -> b0;
    a1 -> b3;
    b2 -> a3;
    a3 -> a0;
    a3 -> end;
    b3 -> end;

    start [shape=Mdiamond];
    end [shape=Msquare];
}
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
dotFormat = &quot;&quot;&quot;
digraph G {
    node [shape=rect];

    subgraph cluster_0 {
        style=filled;
        color=lightgrey;
        node [style=filled,color=white];
        a0 -&gt; a1 -&gt; a2 -&gt; a3;
        label = &quot;Hello&quot;;
    }

    subgraph cluster_1 {
        node [style=filled];
        b0 -&gt; b1 -&gt; b2 -&gt; b3;
        label = &quot;World&quot;;
        color=blue
    }

    start -&gt; a0;
    start -&gt; b0;
    a1 -&gt; b3;
    b2 -&gt; a3;
    a3 -&gt; a0;
    a3 -&gt; end;
    b3 -&gt; end;

    start [shape=Mdiamond];
    end [shape=Msquare];
}
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
draw

<!--
############
__canvas__(dotFormat)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(dotFormat)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Shapes

<!--
############
"""
digraph MyGraph {
  a [shape=box,style=filled,color=red]
  b [shape=polygon,sides=6]
  c [shape=triangle]
  d [shape=invtriangle]
  e [shape=polygon,sides=4,skew=.5]
  f [shape=polygon,sides=4,distortion=.5]
  g [shape=diamond, ,style=striped,fillcolor="red:green:blue"]
  h [shape=Mdiamond]
  i [shape=Msquare,style=dashed]
  j [peripheries=2,fontcolor=red]
  k [style=doted,penwidth=3]
  l [style=wedged]
  m [style=diagonals, label="Vertex"]
  a -- b [label="Arrow", fontcolor=green,fontsize=10]
  b -> c
  c -> d [dir=both]
  a -> e [dir=both,arrowhead=open,arrowtail=inv]
  e -> f [dir=both,arrowhead=dot,arrowtail=invdot]
  f -> g [dir=both,arrowhead=odot,arrowtail=invodot]
  g -> h [dir=both,arrowhead=tee,arrowtail=empty]
  h -> i [dir=both,arrowhead=halfopen,arrowtail=crow]
  i -> j [dir=both,arrowhead=diamond,arrowtail=box]
  j -> k [color="black:red:blue", style=dotted]
  k -> l [color="black:red;0.5:blue"]
  l -> m [arrowsize=2, style=dashed]
}
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
&quot;&quot;&quot;
digraph MyGraph {
  a [shape=box,style=filled,color=red]
  b [shape=polygon,sides=6]
  c [shape=triangle]
  d [shape=invtriangle]
  e [shape=polygon,sides=4,skew=.5]
  f [shape=polygon,sides=4,distortion=.5]
  g [shape=diamond, ,style=striped,fillcolor=&quot;red:green:blue&quot;]
  h [shape=Mdiamond]
  i [shape=Msquare,style=dashed]
  j [peripheries=2,fontcolor=red]
  k [style=doted,penwidth=3]
  l [style=wedged]
  m [style=diagonals, label=&quot;Vertex&quot;]
  a -- b [label=&quot;Arrow&quot;, fontcolor=green,fontsize=10]
  b -&gt; c
  c -&gt; d [dir=both]
  a -&gt; e [dir=both,arrowhead=open,arrowtail=inv]
  e -&gt; f [dir=both,arrowhead=dot,arrowtail=invdot]
  f -&gt; g [dir=both,arrowhead=odot,arrowtail=invodot]
  g -&gt; h [dir=both,arrowhead=tee,arrowtail=empty]
  h -&gt; i [dir=both,arrowhead=halfopen,arrowtail=crow]
  i -&gt; j [dir=both,arrowhead=diamond,arrowtail=box]
  j -&gt; k [color=&quot;black:red:blue&quot;, style=dotted]
  k -&gt; l [color=&quot;black:red;0.5:blue&quot;]
  l -&gt; m [arrowsize=2, style=dashed]
}
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
derivation tree

<!--
############
derivation_tree = ("<start>",
                   [("<expr>",
                     [("<expr>", None),
                      (" + ", []),
                         ("<term>", None)]
                     )])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
derivation_tree = (&quot;&lt;start&gt;&quot;,
                   [(&quot;&lt;expr&gt;&quot;,
                     [(&quot;&lt;expr&gt;&quot;, None),
                      (&quot; + &quot;, []),
                         (&quot;&lt;term&gt;&quot;, None)]
                     )])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
program

<!--
############
from graphviz import Digraph

import re
def dot_escape(s):
    """Return s in a form suitable for dot"""
    s = re.sub(r'([^a-zA-Z0-9" ])', r"\\\1", s)
    return s


def extract_node(node, id):
    symbol, children, *annotation = node
    return symbol, children, ''.join(str(a) for a in annotation)



def default_node_attr(dot, nid, symbol, ann):
    dot.node(repr(nid), dot_escape(symbol))

def default_edge_attr(dot, start_node, stop_node):
    dot.edge(repr(start_node), repr(stop_node))
def default_graph_attr(dot):
    dot.attr('node', shape='plain')
def display_tree(derivation_tree,
                 log=False,
                 extract_node=extract_node,
                 node_attr=default_node_attr,
                 edge_attr=default_edge_attr,
                 graph_attr=default_graph_attr):

    # If we import display_tree, we also have to import its functions
    from graphviz import Digraph

    counter = 0
    labels = {}

    def traverse_tree(dot, tree, id=0):
        (symbol, children, annotation) = extract_node(tree, id)
        labels[str(id)] = symbol
        node_attr(dot, id, symbol, annotation)

        if children:
            for child in children:
                nonlocal counter
                counter += 1
                child_id = counter
                edge_attr(dot, id, child_id)
                traverse_tree(dot, child, child_id)

    dot = Digraph(comment="Derivation Tree")
    graph_attr(dot)
    traverse_tree(dot, derivation_tree)
    if log:
        print(dot)
    return dot, labels

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from graphviz import Digraph

import re
def dot_escape(s):
    &quot;&quot;&quot;Return s in a form suitable for dot&quot;&quot;&quot;
    s = re.sub(r&#x27;([^a-zA-Z0-9&quot; ])&#x27;, r&quot;\\\1&quot;, s)
    return s


def extract_node(node, id):
    symbol, children, *annotation = node
    return symbol, children, &#x27;&#x27;.join(str(a) for a in annotation)



def default_node_attr(dot, nid, symbol, ann):
    dot.node(repr(nid), dot_escape(symbol))

def default_edge_attr(dot, start_node, stop_node):
    dot.edge(repr(start_node), repr(stop_node))
def default_graph_attr(dot):
    dot.attr(&#x27;node&#x27;, shape=&#x27;plain&#x27;)
def display_tree(derivation_tree,
                 log=False,
                 extract_node=extract_node,
                 node_attr=default_node_attr,
                 edge_attr=default_edge_attr,
                 graph_attr=default_graph_attr):

    # If we import display_tree, we also have to import its functions
    from graphviz import Digraph

    counter = 0
    labels = {}

    def traverse_tree(dot, tree, id=0):
        (symbol, children, annotation) = extract_node(tree, id)
        labels[str(id)] = symbol
        node_attr(dot, id, symbol, annotation)

        if children:
            for child in children:
                nonlocal counter
                counter += 1
                child_id = counter
                edge_attr(dot, id, child_id)
                traverse_tree(dot, child, child_id)

    dot = Digraph(comment=&quot;Derivation Tree&quot;)
    graph_attr(dot)
    traverse_tree(dot, derivation_tree)
    if log:
        print(dot)
    return dot, labels
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
display

<!--
############
v, labels = display_tree(derivation_tree)
print(str(v))
print(labels)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, labels = display_tree(derivation_tree)
print(str(v))
print(labels)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
pydot

<!--
############
import pydot
dotFormat = str(v)
__canvas__(dotFormat)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pydot
dotFormat = str(v)
__canvas__(dotFormat)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2020-02-13-pyodide-canvas.py).


