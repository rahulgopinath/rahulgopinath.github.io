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
G = nx.Graph()
G.add_nodes_from([('A', {'weight':5}), ('B', {'weight':3}), ('C', {'weight':3})])
G.add_edges_from([('A', 'B', {'weight':20})])
G.add_edges_from([('A', 'C', {'weight':20})])
pos = nx.shell_layout(G)
nx.draw(G, pos=pos, node_size=1000, with_labels=False)
nx.draw_networkx_labels(G,pos=pos,font_size=30)
plt.axis('off')
plt.show()
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G = nx.Graph()
G.add_nodes_from([(&#x27;A&#x27;, {&#x27;weight&#x27;:5}), (&#x27;B&#x27;, {&#x27;weight&#x27;:3}), (&#x27;C&#x27;, {&#x27;weight&#x27;:3})])
G.add_edges_from([(&#x27;A&#x27;, &#x27;B&#x27;, {&#x27;weight&#x27;:20})])
G.add_edges_from([(&#x27;A&#x27;, &#x27;C&#x27;, {&#x27;weight&#x27;:20})])
pos = nx.shell_layout(G)
nx.draw(G, pos=pos, node_size=1000, with_labels=False)
nx.draw_networkx_labels(G,pos=pos,font_size=30)
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

