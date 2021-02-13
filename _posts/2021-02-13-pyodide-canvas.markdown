---
published: true
title: Pyodide Canvas
layout: post
comments: true
tags: pyodide
categories: post
---

<script type="text/javascript">window.languagePluginUrl='https://cdn.jsdelivr.net/pyodide/v0.16.1/full/';</script>
<script src="https://cdn.jsdelivr.net/pyodide/v0.16.1/full/pyodide.js"></script>
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

Loading the prerequisite:
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
"https://rahul.gopinath.org/py/pyparsing-2.4.7-py2.py3-none-any.whl"
"https://rahul.gopinath.org/py/graphviz-0.16-py2.py3-none-any.whl"
"https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl"
</textarea>
</form>

Canvas

<!--
############
print(__canvas__)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(__canvas__)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Imports
<!--
############
import  matplotlib.pyplot as plt
import networkx as nx
import io, base64
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import  matplotlib.pyplot as plt
import networkx as nx
import io, base64
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Add graph

<!--
############
plt.clf()
G = nx.Graph()
G.add_nodes_from([('A', {'weight':5}), ('B', {'weight':3}), ('C', {'weight':3})])
G.add_edges_from([('A', 'B', {'weight':20})])
G.add_edges_from([('A', 'C', {'weight':20})])
pos = nx.shell_layout(G)
labels = {'A': 'aaa', 'B': 'bbb', 'C':'ccc'}
nx.draw(G, pos=pos, node_size=1000, with_labels=True, labels=labels)
#nx.draw_networkx_labels(G,pos=pos,font_size=30)
plt.axis('off')
plt.show()
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
plt.clf()
G = nx.Graph()
G.add_nodes_from([(&#x27;A&#x27;, {&#x27;weight&#x27;:5}), (&#x27;B&#x27;, {&#x27;weight&#x27;:3}), (&#x27;C&#x27;, {&#x27;weight&#x27;:3})])
G.add_edges_from([(&#x27;A&#x27;, &#x27;B&#x27;, {&#x27;weight&#x27;:20})])
G.add_edges_from([(&#x27;A&#x27;, &#x27;C&#x27;, {&#x27;weight&#x27;:20})])
pos = nx.shell_layout(G)
labels = {'A': 'aaa', 'B': 'bbb', 'C':'ccc'}
nx.draw(G, pos=pos, node_size=1000, with_labels=True, labels=labels)
#nx.draw_networkx_labels(G,pos=pos,font_size=30)
plt.axis(&#x27;off&#x27;)
plt.show()
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Image data
<!--
############
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_str = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
print(len(img_str))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
buf = io.BytesIO()
plt.savefig(buf, format=&#x27;png&#x27;)
buf.seek(0)
img_str = &#x27;data:image/png;base64,&#x27; + base64.b64encode(buf.read()).decode(&#x27;UTF-8&#x27;)
print(len(img_str))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Show


<!--
############
__canvas__(img_str)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(img_str)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


dot

<!--
############
import pydot
dotFormat = """
digraph G{
edge [dir=forward]
node [shape=plaintext]
0 [label="0 (None)"]
0 -> 7 [label="root"]
1 [label="1 (The)"]
4 [label="4 (great Indian Circus)"]
4 -> 4 [label="compound"]
4 -> 1 [label="det"]
4 -> 4 [label="amod"]
5 [label="5 (is)"]
6 [label="6 (in)"]
7 [label="7 (Mumbai)"]
7 -> 6 [label="case"]
7 -> 5 [label="cop"]
7 -> 4 [label="nsubj"]
}
"""
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pydot
dotFormat = &quot;&quot;&quot;
digraph G{
edge [dir=forward]
node [shape=plaintext]
0 [label=&quot;0 (None)&quot;]
0 -&gt; 7 [label=&quot;root&quot;]
1 [label=&quot;1 (The)&quot;]
4 [label=&quot;4 (great Indian Circus)&quot;]
4 -&gt; 4 [label=&quot;compound&quot;]
4 -&gt; 1 [label=&quot;det&quot;]
4 -&gt; 4 [label=&quot;amod&quot;]
5 [label=&quot;5 (is)&quot;]
6 [label=&quot;6 (in)&quot;]
7 [label=&quot;7 (Mumbai)&quot;]
7 -&gt; 6 [label=&quot;case&quot;]
7 -&gt; 5 [label=&quot;cop&quot;]
7 -&gt; 4 [label=&quot;nsubj&quot;]
}
&quot;&quot;&quot;
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
pg = pydot.graph_from_dot_data(dotFormat)
g = nx.nx_pydot.from_pydot(pg[0])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
pg = pydot.graph_from_dot_data(dotFormat)
g = nx.nx_pydot.from_pydot(pg[0])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
plt.clf()
nx.draw(g, with_labels=True)
plt.axis('off')
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_str = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
print(len(img_str))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
plt.clf()
nx.draw(g, with_labels=True)
plt.axis(&#x27;off&#x27;)
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format=&#x27;png&#x27;)
buf.seek(0)
img_str = &#x27;data:image/png;base64,&#x27; + base64.b64encode(buf.read()).decode(&#x27;UTF-8&#x27;)
print(len(img_str))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
__canvas__(img_str)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(img_str)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


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
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


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
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


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
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
import pydot
dotFormat = str(v)

pg = pydot.graph_from_dot_data(dotFormat)
g = nx.nx_pydot.from_pydot(pg[0])
print(pg[0])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pydot
dotFormat = str(v)

pg = pydot.graph_from_dot_data(dotFormat)
g = nx.nx_pydot.from_pydot(pg[0])
print(pg[0])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
def hierarchy_pos(G, root=None, width=0.01, vert_gap = 0.002, vert_loc = 1, xcenter = 0.005):

    '''
    From Joel's answer at https://stackoverflow.com/a/29597209/2966723.  
    Licensed under Creative Commons Attribution-Share Alike 
    
    If the graph is a tree this will return the positions to plot this in a 
    hierarchical layout.
    
    G: the graph (must be a tree)
    
    root: the root node of current branch 
    - if the tree is directed and this is not given, 
      the root will be found and used
    - if the tree is directed and this is given, then 
      the positions will be just for the descendants of this node.
    - if the tree is undirected and not given, 
      then a random choice will be used.
    
    width: horizontal space allocated for this branch - avoids overlap with other branches
    
    vert_gap: gap between levels of hierarchy
    
    vert_loc: vertical location of root
    
    xcenter: horizontal location of root
    '''
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        '''
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        '''
    
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos

            
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def hierarchy_pos(G, root=None, width=0.01, vert_gap = 0.002, vert_loc = 1, xcenter = 0.005):

    &#x27;&#x27;&#x27;
    From Joel&#x27;s answer at https://stackoverflow.com/a/29597209/2966723.  
    Licensed under Creative Commons Attribution-Share Alike 
    
    If the graph is a tree this will return the positions to plot this in a 
    hierarchical layout.
    
    G: the graph (must be a tree)
    
    root: the root node of current branch 
    - if the tree is directed and this is not given, 
      the root will be found and used
    - if the tree is directed and this is given, then 
      the positions will be just for the descendants of this node.
    - if the tree is undirected and not given, 
      then a random choice will be used.
    
    width: horizontal space allocated for this branch - avoids overlap with other branches
    
    vert_gap: gap between levels of hierarchy
    
    vert_loc: vertical location of root
    
    xcenter: horizontal location of root
    &#x27;&#x27;&#x27;
    if not nx.is_tree(G):
        raise TypeError(&#x27;cannot use hierarchy_pos on a graph that is not a tree&#x27;)

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        &#x27;&#x27;&#x27;
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        &#x27;&#x27;&#x27;
    
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos

            
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
plt.clf()
pos = hierarchy_pos(g,'0')

nx.draw(g, pos=pos, with_labels=True, labels=labels)

plt.axis('off')
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_str = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
print(len(img_str))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
plt.clf()
pos = hierarchy_pos(g,&#x27;0&#x27;)

nx.draw(g, pos=pos, with_labels=True, labels=labels)

plt.axis(&#x27;off&#x27;)
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format=&#x27;png&#x27;)
buf.seek(0)
img_str = &#x27;data:image/png;base64,&#x27; + base64.b64encode(buf.read()).decode(&#x27;UTF-8&#x27;)
print(len(img_str))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
__canvas__(img_str)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
__canvas__(img_str)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

