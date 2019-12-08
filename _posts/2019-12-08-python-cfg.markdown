---
published: false
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
def to_graph(registry, arcs=[], comment='', get_shape=lambda n: 'oval', get_peripheries=lambda n: '1'):
    graph = Digraph(comment=comment)
    for nid, cnode in registry.items():
        sn = cnode.name()
        graph.node(cnode.name(), sn, shape=get_shape(cnode), peripheries=get_peripheries(cnode))
        for pn in cnode.parents:
            graph.edge(str(pn.rid), str(cnode.rid), color='black')
    return graph
```


### The CFGNode

The control flow graph is a graph, and hence we need a data structue for the *node*. We need to store the parents
of this node, the children of this node, and register itself in the registery.

```python
class CFGNode:
    counter = 0
    registry = {}
    def __init__(self, parents=[], ast=None, label=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.label = label
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

    def to_json(self):
        return {'id':self.rid, 'parents': [p.rid for p in self.parents],
               'children': [c.rid for c in self.children],
               'calls': self.calls, 'at':self.lineno() ,'ast':self.source()}
```

The usage is as below:

```python
start = CFGNode(parents=[], ast=ast.parse('start').body)
g = to_graph(CFGNode.registry)
g.format = 'svg'
print(g.pipe().decode())
```

<svg width="63pt" height="44pt"
 viewBox="0.00 0.00 63.32 44.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 40)">
<title>%0</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-40 59.3219,-40 59.3219,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="27.6609" cy="-18" rx="27.8228" ry="18"/>
<text text-anchor="middle" x="27.6609" y="-13.8" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
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

<svg width="62pt" height="116pt"
 viewBox="0.00 0.00 62.00 116.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 112)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-112 58,-112 58,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-90" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-18" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M27,-71.8314C27,-64.131 27,-54.9743 27,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-46.4132 27,-36.4133 23.5001,-46.4133 30.5001,-46.4132"/>
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

<svg width="62pt" height="188pt"
 viewBox="0.00 0.00 62.00 188.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 184)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-184 58,-184 58,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-162" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-90" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M27,-143.8314C27,-136.131 27,-126.9743 27,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-118.4132 27,-108.4133 23.5001,-118.4133 30.5001,-118.4132"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-18" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">pass</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M27,-71.8314C27,-64.131 27,-54.9743 27,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-46.4132 27,-36.4133 23.5001,-46.4133 30.5001,-46.4132"/>
</g>
</g>
</svg>

#### Expressions

#### Primitives

How should we handle primitives? Since they are simply interpreted as is, they can be embedded right in.

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_str(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
        return p
        
    def on_num(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
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

<svg width="62pt" height="332pt"
 viewBox="0.00 0.00 62.00 332.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 328)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-328 58,-328 58,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-306" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-234" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">10</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M27,-287.8314C27,-280.131 27,-270.9743 27,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-262.4132 27,-252.4133 23.5001,-262.4133 30.5001,-262.4132"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-162" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">10</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M27,-215.8314C27,-208.131 27,-198.9743 27,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-190.4132 27,-180.4133 23.5001,-190.4133 30.5001,-190.4132"/>
</g>
<!-- 3 -->
<g id="node4" class="node">
<title>3</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-90" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">&#39;a&#39;</text>
</g>
<!-- 2&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>2&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M27,-143.8314C27,-136.131 27,-126.9743 27,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-118.4132 27,-108.4133 23.5001,-118.4133 30.5001,-118.4132"/>
</g>
<!-- 4 -->
<g id="node5" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="27" cy="-18" rx="27" ry="18"/>
<text text-anchor="middle" x="27" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">&#39;a&#39;</text>
</g>
<!-- 3&#45;&gt;4 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M27,-71.8314C27,-64.131 27,-54.9743 27,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="30.5001,-46.4132 27,-36.4133 23.5001,-46.4133 30.5001,-46.4132"/>
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
        p = [CFGNode(parents=myparents, ast=node)]
        return self.walk(node.operand, p)

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        p = [CFGNode(parents=right, ast=node)]
        return p

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        p = [CFGNode(parents=right, ast=node)]
        return p
```

CFG for this expression

```
10+1
```
<svg width="89pt" height="332pt"
 viewBox="0.00 0.00 88.59 332.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 328)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-328 84.5928,-328 84.5928,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="40.2964" cy="-306" rx="27" ry="18"/>
<text text-anchor="middle" x="40.2964" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="40.2964" cy="-234" rx="27" ry="18"/>
<text text-anchor="middle" x="40.2964" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">10</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M40.2964,-287.8314C40.2964,-280.131 40.2964,-270.9743 40.2964,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="43.7965,-262.4132 40.2964,-252.4133 36.7965,-262.4133 43.7965,-262.4132"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="40.2964" cy="-162" rx="27" ry="18"/>
<text text-anchor="middle" x="40.2964" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">1</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M40.2964,-215.8314C40.2964,-208.131 40.2964,-198.9743 40.2964,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="43.7965,-190.4132 40.2964,-180.4133 36.7965,-190.4133 43.7965,-190.4132"/>
</g>
<!-- 3 -->
<g id="node4" class="node">
<title>3</title>
<ellipse fill="none" stroke="#000000" cx="40.2964" cy="-90" rx="40.0939" ry="18"/>
<text text-anchor="middle" x="40.2964" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">(10 + 1)</text>
</g>
<!-- 2&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>2&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M40.2964,-143.8314C40.2964,-136.131 40.2964,-126.9743 40.2964,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="43.7965,-118.4132 40.2964,-108.4133 36.7965,-118.4133 43.7965,-118.4132"/>
</g>
<!-- 4 -->
<g id="node5" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="40.2964" cy="-18" rx="40.0939" ry="18"/>
<text text-anchor="middle" x="40.2964" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">(10 + 1)</text>
</g>
<!-- 3&#45;&gt;4 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M40.2964,-71.8314C40.2964,-64.131 40.2964,-54.9743 40.2964,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="43.7965,-46.4132 40.2964,-36.4133 36.7965,-46.4133 43.7965,-46.4132"/>
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

<svg width="116pt" height="332pt"
 viewBox="0.00 0.00 115.89 332.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 328)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-328 111.8904,-328 111.8904,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="53.9452" cy="-306" rx="27" ry="18"/>
<text text-anchor="middle" x="53.9452" y="-302.3" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="53.9452" cy="-234" rx="53.8905" ry="18"/>
<text text-anchor="middle" x="53.9452" y="-230.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = (10 + 1)</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M53.9452,-287.8314C53.9452,-280.131 53.9452,-270.9743 53.9452,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="57.4453,-262.4132 53.9452,-252.4133 50.4453,-262.4133 57.4453,-262.4132"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="53.9452" cy="-162" rx="27" ry="18"/>
<text text-anchor="middle" x="53.9452" y="-158.3" font-family="Times,serif" font-size="14.00" fill="#000000">10</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M53.9452,-215.8314C53.9452,-208.131 53.9452,-198.9743 53.9452,-190.4166"/>
<polygon fill="#000000" stroke="#000000" points="57.4453,-190.4132 53.9452,-180.4133 50.4453,-190.4133 57.4453,-190.4132"/>
</g>
<!-- 3 -->
<g id="node4" class="node">
<title>3</title>
<ellipse fill="none" stroke="#000000" cx="53.9452" cy="-90" rx="27" ry="18"/>
<text text-anchor="middle" x="53.9452" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">1</text>
</g>
<!-- 2&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>2&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M53.9452,-143.8314C53.9452,-136.131 53.9452,-126.9743 53.9452,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="57.4453,-118.4132 53.9452,-108.4133 50.4453,-118.4133 57.4453,-118.4132"/>
</g>
<!-- 4 -->
<g id="node5" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="53.9452" cy="-18" rx="40.0939" ry="18"/>
<text text-anchor="middle" x="53.9452" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">(10 + 1)</text>
</g>
<!-- 3&#45;&gt;4 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M53.9452,-71.8314C53.9452,-64.131 53.9452,-54.9743 53.9452,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="57.4453,-46.4132 53.9452,-36.4133 50.4453,-46.4133 57.4453,-46.4132"/>
</g>
</g>
</svg>

#### Name

```python
class PyCFGExtractor(PyCFGExtractor):
    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
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
        test_node = [CFGNode(parents=p, ast=node)]
        g1 = test_node
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        for n in node.orelse:
            g2 = self.walk(n, g2)
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

<svg width="142pt" height="680pt"
 viewBox="0.00 0.00 142.49 680.17" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 676.1665)">
<title>%3</title>
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-676.1665 138.4948,-676.1665 138.4948,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-654.1665" rx="27" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-650.4665" font-family="Times,serif" font-size="14.00" fill="#000000">start</text>
</g>
<!-- 1 -->
<g id="node2" class="node">
<title>1</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-582.1665" rx="29.4969" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-578.4665" font-family="Times,serif" font-size="14.00" fill="#000000">a = 1</text>
</g>
<!-- 0&#45;&gt;1 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;1</title>
<path fill="none" stroke="#000000" d="M67.2474,-635.9979C67.2474,-628.2975 67.2474,-619.1409 67.2474,-610.5832"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-610.5798 67.2474,-600.5798 63.7475,-610.5798 70.7475,-610.5798"/>
</g>
<!-- 2 -->
<g id="node3" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-510.1665" rx="27" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-506.4665" font-family="Times,serif" font-size="14.00" fill="#000000">1</text>
</g>
<!-- 1&#45;&gt;2 -->
<g id="edge2" class="edge">
<title>1&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M67.2474,-563.9979C67.2474,-556.2975 67.2474,-547.1409 67.2474,-538.5832"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-538.5798 67.2474,-528.5798 63.7475,-538.5798 70.7475,-538.5798"/>
</g>
<!-- 3 -->
<g id="node4" class="node">
<title>3</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-438.1665" rx="27" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-434.4665" font-family="Times,serif" font-size="14.00" fill="#000000">a</text>
</g>
<!-- 2&#45;&gt;3 -->
<g id="edge3" class="edge">
<title>2&#45;&gt;3</title>
<path fill="none" stroke="#000000" d="M67.2474,-491.9979C67.2474,-484.2975 67.2474,-475.1409 67.2474,-466.5832"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-466.5798 67.2474,-456.5798 63.7475,-466.5798 70.7475,-466.5798"/>
</g>
<!-- 4 -->
<g id="node5" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-366.1665" rx="27" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-362.4665" font-family="Times,serif" font-size="14.00" fill="#000000">1</text>
</g>
<!-- 3&#45;&gt;4 -->
<g id="edge4" class="edge">
<title>3&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M67.2474,-419.9979C67.2474,-412.2975 67.2474,-403.1409 67.2474,-394.5832"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-394.5798 67.2474,-384.5798 63.7475,-394.5798 70.7475,-394.5798"/>
</g>
<!-- 5 -->
<g id="node6" class="node">
<title>5</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-294.1665" rx="35.194" ry="18"/>
<text text-anchor="middle" x="67.2474" y="-290.4665" font-family="Times,serif" font-size="14.00" fill="#000000">(a &gt; 1)</text>
</g>
<!-- 4&#45;&gt;5 -->
<g id="edge5" class="edge">
<title>4&#45;&gt;5</title>
<path fill="none" stroke="#000000" d="M67.2474,-347.9979C67.2474,-340.2975 67.2474,-331.1409 67.2474,-322.5832"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-322.5798 67.2474,-312.5798 63.7475,-322.5798 70.7475,-322.5798"/>
</g>
<!-- 6 -->
<g id="node7" class="node">
<title>6</title>
<ellipse fill="none" stroke="#000000" cx="67.2474" cy="-192.0833" rx="49.4949" ry="48.1667"/>
<text text-anchor="middle" x="67.2474" y="-210.8833" font-family="Times,serif" font-size="14.00" fill="#000000">if (a &gt; 1):</text>
<text text-anchor="middle" x="67.2474" y="-195.8833" font-family="Times,serif" font-size="14.00" fill="#000000"> &#160;&#160;&#160;a = 1</text>
<text text-anchor="middle" x="67.2474" y="-180.8833" font-family="Times,serif" font-size="14.00" fill="#000000">else:</text>
<text text-anchor="middle" x="67.2474" y="-165.8833" font-family="Times,serif" font-size="14.00" fill="#000000"> &#160;&#160;&#160;a = 0</text>
</g>
<!-- 5&#45;&gt;6 -->
<g id="edge6" class="edge">
<title>5&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M67.2474,-275.9161C67.2474,-268.5879 67.2474,-259.6959 67.2474,-250.4771"/>
<polygon fill="#000000" stroke="#000000" points="70.7475,-250.404 67.2474,-240.404 63.7475,-250.4041 70.7475,-250.404"/>
</g>
<!-- 7 -->
<g id="node8" class="node">
<title>7</title>
<ellipse fill="none" stroke="#000000" cx="29.2474" cy="-90" rx="29.4969" ry="18"/>
<text text-anchor="middle" x="29.2474" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = 1</text>
</g>
<!-- 6&#45;&gt;7 -->
<g id="edge7" class="edge">
<title>6&#45;&gt;7</title>
<path fill="none" stroke="#000000" d="M50.3588,-146.7136C46.6143,-136.6543 42.759,-126.2976 39.3844,-117.2322"/>
<polygon fill="#000000" stroke="#000000" points="42.579,-115.7812 35.8103,-107.6305 36.0188,-118.2232 42.579,-115.7812"/>
</g>
<!-- 9 -->
<g id="node10" class="node">
<title>9</title>
<ellipse fill="none" stroke="#000000" cx="105.2474" cy="-90" rx="29.4969" ry="18"/>
<text text-anchor="middle" x="105.2474" y="-86.3" font-family="Times,serif" font-size="14.00" fill="#000000">a = 0</text>
</g>
<!-- 6&#45;&gt;9 -->
<g id="edge9" class="edge">
<title>6&#45;&gt;9</title>
<path fill="none" stroke="#000000" d="M84.1361,-146.7136C87.8806,-136.6543 91.7358,-126.2976 95.1104,-117.2322"/>
<polygon fill="#000000" stroke="#000000" points="98.476,-118.2232 98.6846,-107.6305 91.9158,-115.7812 98.476,-118.2232"/>
</g>
<!-- 8 -->
<g id="node9" class="node">
<title>8</title>
<ellipse fill="none" stroke="#000000" cx="29.2474" cy="-18" rx="27" ry="18"/>
<text text-anchor="middle" x="29.2474" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">1</text>
</g>
<!-- 7&#45;&gt;8 -->
<g id="edge8" class="edge">
<title>7&#45;&gt;8</title>
<path fill="none" stroke="#000000" d="M29.2474,-71.8314C29.2474,-64.131 29.2474,-54.9743 29.2474,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="32.7475,-46.4132 29.2474,-36.4133 25.7475,-46.4133 32.7475,-46.4132"/>
</g>
<!-- 10 -->
<g id="node11" class="node">
<title>10</title>
<ellipse fill="none" stroke="#000000" cx="105.2474" cy="-18" rx="27" ry="18"/>
<text text-anchor="middle" x="105.2474" y="-14.3" font-family="Times,serif" font-size="14.00" fill="#000000">0</text>
</g>
<!-- 9&#45;&gt;10 -->
<g id="edge10" class="edge">
<title>9&#45;&gt;10</title>
<path fill="none" stroke="#000000" d="M105.2474,-71.8314C105.2474,-64.131 105.2474,-54.9743 105.2474,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="108.7475,-46.4132 105.2474,-36.4133 101.7475,-46.4133 108.7475,-46.4132"/>
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
