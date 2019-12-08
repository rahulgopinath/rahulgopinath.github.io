---
published: true
title: The Python Control Flow Graph
layout: post
comments: true
tags: controlflow
---

We [previously discussed](/2019/12/07/python-mci/) how one can write an interpreter for
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

### Prerequisites

As before, we start with the prerequisite imports.

```python
import ast
import re
import astunparse
```

We define a simple viewing function for visualization

```python
import graphviz

def get_color(p, cp):
    color='black'
    while not p.annotation():
        if p.label == 'if:True':
            return 'blue'
        elif p.label == 'if:False':
            return 'red'
        p = p.parents[0]
    return color

def get_peripheries(p):
    if p.annotation() == '<start>':
        return '2'
    else:
        return '1'

def get_shape(p):
    if p.annotation() == '<start>':
        return 'oval'

    if p.annotation().startswith('if:'):
        return 'diamond'
    else:
        return 'rectangle'

def to_graph(registry, arcs=[], comment='', get_shape=lambda n: 'rectangle', get_peripheries=lambda n: '1', get_color=lambda p,c: 'black'):
    graph = Digraph(comment=comment)
    for nid, cnode in registry.items():
        if not cnode.annotation():
            continue
        sn = cnode.annotation()
        graph.node(cnode.name(), sn, shape=get_shape(cnode), peripheries=get_peripheries(cnode))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            graph.edge(gp, str(cnode.rid), color=color)
    return graph
```


### The CFGNode

The control flow graph is a graph, and hence we need a data structue for the *node*. We need to store the parents
of this node, the children of this node, and register itself in the registery.

```python
class CFGNode:
    counter = 0
    registry = {}
    stack = []
    def __init__(self, parents=[], ast=None, label=None, annot=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.label = label
        self.annot = annot
        self.rid  = CFGNode.counter
        CFGNode.registry[self.rid] = self
        CFGNode.counter += 1
```

Given that it is a directed graph node, we need the ability to add parents and children.

```python
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
        self.calls.append(func)
```

A few convenience methods to make our life simpler.

```python
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
        return astunparse.unparse(self.ast_node).strip()

    def annotation(self):
        if self.annot is not None:
            return self.annot
        return self.source()

    def to_json(self):
        return {'id':self.rid, 'parents': [p.rid for p in self.parents],
               'children': [c.rid for c in self.children],
               'calls': self.calls, 'at':self.lineno() ,'ast':self.source()}
               
    def get_gparent_id(self):
        p = CFGNode.registry[self.rid]
        while not p.annotation():
            p = p.parents[0]
        return str(p.rid)
```

The usage is as below:

```python
start = CFGNode(parents=[], ast=ast.parse('start').body)
g = to_graph(CFGNode.registry, get_color=get_color, get_peripheries=get_peripheries, get_shape=get_shape)
g.format = 'svg'
print(g.pipe().decode())
```

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
structure with our interpreter. It can indeed inherit from the interpreter, but
given that we override all functions in it, we chose not to inherit.

```python
class PyCFGExtractor:
    def __init__(self):
        self.founder = CFGNode(parents=[], ast=ast.parse('start').body[0]) # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}
```

As before, we define `walk()` that walks a given AST node.

A major difference from MCI is in the functions that handle each node. Since it is a directed
graph traversal, our `walk()` accepts a list of parent nodes that point to this node, and also
invokes the various `on_*()` functions with the same list. These functions in turn return a list
of nodes that exit them.

While expressions, and single statements only have one node that comes out of them, control flow
structures and function calls can have multiple nodes that come out of them going into the next
node. For example, an `If` statement will have a node from both the `if.body` and `if.orelse`
going into the next one.

```python
class PyCFGExtractor(PyCFGExtractor):
    def walk(self, node, myparents):
        if node is None: return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, myparents)
        raise SyntaxError('walk: Not Implemented in %s' % type(node))
```

#### Pass

The pass statement is trivial. It simply adds one more node.


```python
class PyCFGExtractor(PyCFGExtractor):
    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
        return p
```

Here is the CFG from a single pass statement.

```
pass
```

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

We start by defining the `Module`. A python module is composed of a sequence of statements,
and the graph is a linear path through these statements. That is, each time a statement
is executed, we make a link from it to the next statement.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_module(self, node, myparents):
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p
```

Here is the CFG from the following which is wrapped in a module

```python
pass
pass
```

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


#### Expressions

#### Primitives

How should we handle primitives? Since they are simply interpreted as is, they can be embedded right in.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_str(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p
        
    def on_num(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p
```

They however, are simple expressions

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node)]
        return p
```

Generating the following CFG

```
10
'a'
```
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

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_unaryop(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return self.walk(node.operand, p)

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        p = [CFGNode(parents=right, ast=node, annot='')]
        return p

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        p = [CFGNode(parents=right, ast=node, annot='')]
        return p
```

CFG for this expression

```
10+1
```

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

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_assign(self, node, myparents):
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')
        p = [CFGNode(parents=myparents, ast=node)]
        p = self.walk(node.value, p)
        return p
```

Example

```
a = 10+1
```

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

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p
```

### Control structures

#### If

We now come to the control structures. For the `if` statement, we have two
parallel paths. We first evaluate the test expression, then add a new node
corresponding to the if statement, and provide the paths through the `if.body`
and `if.orelse`.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_if(self, node, myparents):
        p = self.walk(node.test, myparents)
        test_node = [CFGNode(parents=p, ast=node, annot="if: %s" % astunparse.unparse(node.test).strip())]
        g1 = test_node
        g_true = [CFGNode(parents=g1, ast=None, label="if:True", annot='')]
        for n in node.body:
            g1 = self.walk(n, g_true)
        g2 = test_node
        g_false = [CFGNode(parents=g2, ast=None, label="if: False", annot='')]
        for n in node.orelse:
            g2 = self.walk(n, g_false)
        return g1 + g2
```

Example

```
a = 1
if a>1:
    a = 1
else:
    a = 0
```

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

```
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

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_while(self, node, myparents):
        lbl1_node = CFGNode(parents=myparents, ast=node, label='loop_entry')
        p = self.walk(node.test, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=node.test, label='while:test')
        lbl1_node.exit_nodes = [lbl2_node]
        
        p = [lbl2_node]

        for n in node.body:
            p = self.walk(n, p)

        # the last node is the parent for the lb1 node.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes
```

#### Break

As we explained before, the `break` when it is encountred, looks up
the parent chain. Once it finds a parent that has the `loop_entry` label,
it attaches itself to that parent. The statements following the `break` are not
its immediate children. Hence, we return an empty list.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_break(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]

        assert hasattr(parent, 'exit_nodes')
        p = CFGNode(parents=myparents, ast=node)

        # make the break one of the parents of label node.
        parent.exit_nodes.append(p)

        # break doesnt have immediate children
        return []
```

#### Continue

Continue is similar to `break`, except that it has to restart the loop. Hence,
it adds itself as a parent to the node with `loop_entry` attribute. As like `break`,
execution does not proceed to the lexically next statement after `continue`. Hence,
we return an empty set.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_continue(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry'):
            parent = parent.parents[0]
            
        p = CFGNode(parents=myparents, ast=node)
        parent.add_parent(p)
        
        return []
```       

#### For

The `For` statement in Python is rather complex. Given a for loop as below

```
for i in my_expr:
    statement1
    statement2
```

This has to be extracted to the following:

```
lbl1: 
      __iv = iter(my_expr)
lbl2: if __iv.length_hint() > 0: goto lbl3
      i = next(__iv)
      statement1
      statement2
lbl3: ...
```



```python
class PyCFGExtractor(PyCFGExtractor):
    def on_for(self, node, myparents):
        #node.target in node.iter: node.body
        _test_node = CFGNode(parents=myparents, ast=ast.parse(
               '_for: True if %s else False' % astunparse.unparse(node.iter).strip()).body[0])
        ast.copy_location(_test_node.ast_node, node)

        # we attach the label node here so that break can find it.
        _test_node.exit_nodes = []
        test_node = self.walk(node.iter, [_test_node])

        extract_node = CFGNode(parents=[_test_node], ast=ast.parse('%s = %s.shift()' % (
                astunparse.unparse(node.target).strip(),
                astunparse.unparse(node.iter).strip())).body[0])
        ast.copy_location(extract_node.ast_node, _test_node.ast_node)

        # now we evaluate the body, one at a time.
        p1 = extract_node
        for n in node.body:
            p1 = self.walk(n, p1)

        # the test node is looped back at the end of processing.
        _test_node.add_parent(p1)

        return _test_node.exit_nodes + test_node
```

```python
class PyCFGExtractor(PyCFGExtractor):  
    def on_call(self, node, myparents):
        p = myparents
        for a in node.args:
            p = self.walk(a, p)
        mid = None
        if hasattr(node.func, 'id'):
            mid = node.func.id
        else:
            mid = node.func.value.id
        myparents[0].add_calls(mid)
        return p

    def on_return(self, node, myparents):
        parent = myparents[0]

        val_node = self.walk(node.value, myparents)
        # on return look back to the function definition.
        while not hasattr(parent, 'return_nodes'):
            parent = parent.parents[0]
        assert hasattr(parent, 'return_nodes')

        p = CFGNode(parents=val_node, ast=node)

        # make the break one of the parents of label node.
        parent.return_nodes.append(p)

        # return doesnt have immediate children
        return []
```

```python
class PyCFGExtractor(PyCFGExtractor):  
    def on_functiondef(self, node, myparents):
        # a function definition does not actually continue the thread of
        # control flow
        # name, args, body, decorator_list, returns
        fname = node.name
        args = node.args
        returns = node.returns

        enter_node = CFGNode(parents=[], ast=ast.parse('enter: %s(%s)' % (
               node.name, ', '.join([a.arg for a in node.args.args])) ).body[0]) # sentinel
        ast.copy_location(enter_node.ast_node, node)
        enter_node.return_nodes = [] # sentinel

        p = [enter_node]
        for n in node.body:
            p = self.walk(n, p)

        if not enter_node.return_nodes:
            enter_node.return_nodes = p

        self.functions[fname] = [enter_node, enter_node.return_nodes]
        self.functions_node[enter_node.lineno()] = fname

        return myparents
```

```python
class PyCFGExtractor(PyCFGExtractor):  
    def get_defining_function(self, node):
        if node.lineno() in self.functions_node: return self.functions_node[node.lineno()]
        if not node.parents:
            self.functions_node[node.lineno()] = ''
            return ''
        val = self.get_defining_function(node.parents[0])
        self.functions_node[node.lineno()] = val
        return val

    def link_functions(self):
        for nid,node in CFGNode.cache.items():
            if node.calls:
                for calls in node.calls:
                    if calls in self.functions:
                        enter, exits = self.functions[calls]
                        enter.add_parent(node)
                        #node.add_parents(exits)
                        if node.children:
                            for c in node.children: c.add_parents(exits)

    def update_functions(self):
        for nid,node in CFGNode.cache.items():
            _n = self.get_defining_function(node)

    def update_children(self):
        for nid,node in CFGNode.cache.items():
            for p in node.parents:
                p.add_child(node)
                
    def gen_cfg(self, src):
        node = ast.parse(src)
        nodes = self.walk(node, [self.founder])
        self.last_node = CFGNode(parents=nodes, ast=ast.parse('stop').body[0])
        ast.copy_location(self.last_node.ast_node, self.founder.ast_node)
        self.update_children()
        self.update_functions()
        self.link_functions()
```
