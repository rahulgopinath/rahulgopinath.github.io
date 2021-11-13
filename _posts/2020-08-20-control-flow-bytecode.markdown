---
published: true
title: Control Flow Graph from Python Bytecode
layout: post
comments: true
tags: cfg, bytecode, python
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
We previous [discussed](/post/2019/12/08/python-controlflow/) how to extract the control flow graph
from the Python AST. However, the Python AST can change from version to version, with the introduction
of new control flow structures. The byte code, in comparison, stays relatively stable. Hence, we can
use the bytecode to recover the control flow graph too.

First, we need the following imports. The `dis` package gives us access to the Python disassembly, and
networkx and matplotlib lets us draw.

<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
matplotlib
networkx
</textarea>
</form>
</details>
We also need pydot for drawing

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
</textarea>
</form>
</details>

<!--
############
import sys
import dis
import networkx as nx
import matplotlib.pyplot as plt
import pydot
import textwrap
import base64

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
import dis
import networkx as nx
import matplotlib.pyplot as plt
import pydot
import textwrap
import base64
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us start by defining a few functions that we want to extract the control-flow graphs of.

<!--
############
def gcd(a, b):
    if a<b:
        c = a
        a = b
        b = c

    while b != 0:
        c = a
        a = b
        b = c % b
    return a

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gcd(a, b):
    if a&lt;b:
        c = a
        a = b
        b = c

    while b != 0:
        c = a
        a = b
        b = c % b
    return a
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the node in the graph.

<!--
############
class CFGNode:
    def __init__(self, i, bid):
        self.i = i
        self.bid = bid
        self.children = []
        self.props = {}

    def add_child(self, n):
        self.children.append(n)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFGNode:
    def __init__(self, i, bid):
        self.i = i
        self.bid = bid
        self.children = []
        self.props = {}

    def add_child(self, n):
        self.children.append(n)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we come to the main class

<!--
############
class CFG:
    def __init__(self, myfn):
        self.myfn = myfn

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG:
    def __init__(self, myfn):
        self.myfn = myfn
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A small helper

<!--
############
class CFG(CFG):
    def lstadd(self, hmap, key, val):
        if key not in hmap:
            hmap[key] = [val]
        else:
            hmap[key].append(val)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG(CFG):
    def lstadd(self, hmap, key, val):
        if key not in hmap:
            hmap[key] = [val]
        else:
            hmap[key].append(val)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define an entry point for the graph

<!--
############
class CFG(CFG):
    def entry(self):
        return CFGNode(dis.Instruction('NOP', opcode=dis.opmap['NOP'],
                                        arg=0, argval=0, argrepr=0,
                                        offset=0,starts_line=0, is_jump_target=False), 0)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG(CFG):
    def entry(self):
        return CFGNode(dis.Instruction(&#x27;NOP&#x27;, opcode=dis.opmap[&#x27;NOP&#x27;],
                                        arg=0, argval=0, argrepr=0,
                                        offset=0,starts_line=0, is_jump_target=False), 0)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, the meat of generation. We look handle the jump instructions specifically. Everything else is a simple block.

<!--
############
class CFG(CFG):
    def gen(self):
        enter = self.entry()
        last = enter
        self.jump_to = {}
        self.opcodes = {}
        for i,ins in enumerate(dis.get_instructions(self.myfn)):
            byte = i * 2
            node = CFGNode(ins, byte)
            self.opcodes[byte] = node
            #print(i,ins)
            if ins.opname in ['LOAD_CONST',
                              'LOAD_FAST',
                              'STORE_FAST',
                              'COMPARE_OP',
                              'INPLACE_ADD',
                              'INPLACE_SUBTRACT',
                              'RETURN_VALUE',
                              'BINARY_MODULO',
                              'STORE_NAME',
                              'MAKE_FUNCTION',
                              'POP_BLOCK']:
                last.add_child(node)
                last = node
            elif ins.opname == 'POP_JUMP_IF_FALSE':
                #print("will jump to", ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props['jmp'] = True
                last.add_child(node)
                last = node
            elif ins.opname == 'JUMP_FORWARD':
                node.props['jmp'] = True
                self.lstadd(self.jump_to, (i+1)*2 + ins.arg, node)
                #print("will jump to", (i+1)*2 + ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == 'SETUP_LOOP':
                #print("setuploop: ", byte , ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == 'JUMP_ABSOLUTE':
                #print("will jump to", ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props['jmp'] = True
                last.add_child(node)
                last = node
            else:
                assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG(CFG):
    def gen(self):
        enter = self.entry()
        last = enter
        self.jump_to = {}
        self.opcodes = {}
        for i,ins in enumerate(dis.get_instructions(self.myfn)):
            byte = i * 2
            node = CFGNode(ins, byte)
            self.opcodes[byte] = node
            #print(i,ins)
            if ins.opname in [&#x27;LOAD_CONST&#x27;,
                              &#x27;LOAD_FAST&#x27;,
                              &#x27;STORE_FAST&#x27;,
                              &#x27;COMPARE_OP&#x27;,
                              &#x27;INPLACE_ADD&#x27;,
                              &#x27;INPLACE_SUBTRACT&#x27;,
                              &#x27;RETURN_VALUE&#x27;,
                              &#x27;BINARY_MODULO&#x27;,
                              &#x27;STORE_NAME&#x27;,
                              &#x27;MAKE_FUNCTION&#x27;,
                              &#x27;POP_BLOCK&#x27;]:
                last.add_child(node)
                last = node
            elif ins.opname == &#x27;POP_JUMP_IF_FALSE&#x27;:
                #print(&quot;will jump to&quot;, ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props[&#x27;jmp&#x27;] = True
                last.add_child(node)
                last = node
            elif ins.opname == &#x27;JUMP_FORWARD&#x27;:
                node.props[&#x27;jmp&#x27;] = True
                self.lstadd(self.jump_to, (i+1)*2 + ins.arg, node)
                #print(&quot;will jump to&quot;, (i+1)*2 + ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == &#x27;SETUP_LOOP&#x27;:
                #print(&quot;setuploop: &quot;, byte , ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == &#x27;JUMP_ABSOLUTE&#x27;:
                #print(&quot;will jump to&quot;, ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props[&#x27;jmp&#x27;] = True
                last.add_child(node)
                last = node
            else:
                assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need to fix the jumps now.

<!--
############
class CFG(CFG):
    def fix_jumps(self):
        for byte in self.opcodes:
            if  byte in self.jump_to:
                node = self.opcodes[byte]
                assert node.i.is_jump_target
                for b in self.jump_to[byte]:
                    b.add_child(node)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG(CFG):
    def fix_jumps(self):
        for byte in self.opcodes:
            if  byte in self.jump_to:
                node = self.opcodes[byte]
                assert node.i.is_jump_target
                for b in self.jump_to[byte]:
                    b.add_child(node)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Making the graph to be displayed.

<!--
############
class CFG(CFG):
    def to_graph(self):
        self.gen()
        self.fix_jumps()
        G = pydot.Dot("my_graph", graph_type="digraph")
        for nid, cnode in self.opcodes.items():
            G.add_node(pydot.Node(str(cnode.bid)))
            ns = G.get_node(str(cnode.bid))
            ns[0].set_label("%d: %s" % (nid, cnode.i.opname))
            for cn in cnode.children:
                G.add_edge(pydot.Edge(str(cnode.bid), str(cn.bid)))
        return G

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CFG(CFG):
    def to_graph(self):
        self.gen()
        self.fix_jumps()
        G = pydot.Dot(&quot;my_graph&quot;, graph_type=&quot;digraph&quot;)
        for nid, cnode in self.opcodes.items():
            G.add_node(pydot.Node(str(cnode.bid)))
            ns = G.get_node(str(cnode.bid))
            ns[0].set_label(&quot;%d: %s&quot; % (nid, cnode.i.opname))
            for cn in cnode.children:
                G.add_edge(pydot.Edge(str(cnode.bid), str(cn.bid)))
        return G
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This finishes our implementation.

<!--
############
v = CFG(gcd)
g = v.to_graph()
print(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = CFG(gcd)
g = v.to_graph()
print(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Show the image

<!--
############
nxg = nx.nx_pydot.from_pydot(g)
plt.clf()
nx.draw(nxg, with_labels=True)
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
nxg = nx.nx_pydot.from_pydot(g)
plt.clf()
nx.draw(nxg, with_labels=True)
plt.axis(&#x27;off&#x27;)
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format=&#x27;png&#x27;)
buf.seek(0)
img_str = &#x27;data:image/png;base64,&#x27; + base64.b64encode(buf.read()).decode(&#x27;UTF-8&#x27;)
print(len(img_str))
</textarea><br />
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
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Unfortunately, the current WASM pydot and matplotlib implementation that we
use has a bug which graph display nonsensical. On the command line, the above
is displayed as

![bitcodecfg](/resources/posts/bitcodecfg.png)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
