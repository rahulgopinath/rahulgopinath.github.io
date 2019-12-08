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

```
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
print(to_graph(CFGNode.registry))
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

#### Pass

The pass statement is trivial. It simply adds one more node.


```python
class PyCFGExtractor(PyCFGExtractor):
    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
        return p
```

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

    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node)]
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
        p = self.walk(node.test, [_test_node])
        test_node = [CFGNode(parents=p, ast=node)]
        g1 = test_node
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        for n in node.orelse:
            g2 = self.walk(n, g2)
        return g1 + g2
```

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

```python
def compute_dominator(cfg, start = 0, key='parents'):
    dominator = {}
    dominator[start] = {start}
    all_nodes = set(cfg.keys())
    rem_nodes = all_nodes - {start}
    for n in rem_nodes:
        dominator[n] = all_nodes

    c = True
    while c:
        c = False
        for n in rem_nodes:
            pred_n = cfg[n][key]
            doms = [dominator[p] for p in pred_n]
            i = set.intersection(*doms) if doms else set()
            v = {n} | i
            if dominator[n] != v:
                c = True
            dominator[n] = v
    return dominator

def slurp(f):
    with open(f, 'r') as f: return f.read()

def get_cfg(pythonfile):
    cfg = PyCFGExtractor()
    cfg.gen_cfg(slurp(pythonfile).strip())
    cache = CFGNode.cache
    g = {}
    for k,v in cache.items():
        j = v.to_json()
        at = j['at']
        parents_at = [cache[p].to_json()['at'] for p in j['parents']]
        children_at = [cache[c].to_json()['at'] for c in j['children']]
        if at not in g:
            g[at] = {'parents':set(), 'children':set()}
        # remove dummy nodes
        ps = set([p for p in parents_at if p != at])
        cs = set([c for c in children_at if c != at])
        g[at]['parents'] |= ps
        g[at]['children'] |= cs
        if v.calls:
            g[at]['calls'] = v.calls
        g[at]['function'] = cfg.functions_node[v.lineno()]
    return (g, cfg.founder.ast_node.lineno, cfg.last_node.ast_node.lineno)

def compute_flow(pythonfile):
    cfg,first,last = get_cfg(pythonfile)
    return (cfg, compute_dominator(cfg, start=first),
             compute_dominator(cfg, start=last, key='children'))
```

### The driver

```python
if __name__ == '__main__':
    import json
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('pythonfile', help='The python file to be analyzed')
    parser.add_argument('-d','--dots', 
      action='store_true', help='generate a dot file')
    parser.add_argument('-c','--cfg', 
      action='store_true', help='print cfg')
    parser.add_argument('-x','--coverage', 
      action='store', dest='coverage', type=str, help='coverage file')
    parser.add_argument('-y','--ccoverage', 
      action='store', dest='ccoverage', type=str, help='custom coverage file')
    args = parser.parse_args()
    if args.dots:
        arcs = None
        if args.coverage:
            cdata = coverage.CoverageData()
            cdata.read_file(filename=args.coverage)
            arcs = [(abs(i),abs(j)) for i,j in cdata.arcs(cdata.measured_files()[0])]
        elif args.ccoverage:
            arcs = [(i,j) for i,j in json.loads(open(args.ccoverage).read())]
        else:
            arcs = []
        cfg = PyCFGExtractor()
        cfg.gen_cfg(slurp(args.pythonfile).strip())
        g = CFGNode.to_graph(arcs)
        g.draw('out.png', prog='dot')
        print(g.string(), file=sys.stderr)
    elif args.cfg:
        cfg = get_cfg(args.pythonfile)
        for i in sorted(cfg.keys()):
            print(i,'parents:', cfg[i]['parents'], 'children:', cfg[i]['children'])
```
