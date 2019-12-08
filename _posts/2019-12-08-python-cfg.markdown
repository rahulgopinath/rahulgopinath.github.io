---
published: false
title: The Python Control Flow Graph
layout: post
comments: true
tags: controlflow
---

We [previously discussed](/2019/12/07/python-mci/) how one can write an interpreter for
Python. We hinted at that time that it could be used for a variety of other applications,
including exctracting the call and control flow graph. In this post, we will show how one
can extract the control flow graph using such an interpteter.

A [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) is a directed graph
data structure that encodes all paths that may be traversed through a program. That is, in some
sense, it is an abstract view of the interpreter as a whole.

Control flow graphs are useful for a variety of tasks. They are one of the most frequently
used tools for visualization. But more imporatntly it is the starting point for further
analysis of the program including code generation, optimizations, and other static analysis
techniques. For this post, I will focus on the visualization aspect.

### Prerequisites

As before, we start with the prerequisite imports.

```python
import ast
import re
import astunparse
import pygraphviz
```

### The CFGNode

The control flow graph is a graph, and hence we need a data structue for the *node*.
```
class CFGNode(dict):
    registry = 0
    cache = {}
    stack = []
    def __init__(self, parents=[], ast=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.rid  = CFGNode.registry
        CFGNode.cache[self.rid] = self
        CFGNode.registry += 1
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

We also hook up `to_graph()` which turns the graph data structure to
*graphviz* *dot* format.

```python
class CFGNode(CFGNode):
    @classmethod
    def to_graph(cls, arcs=[]):
        def unhack(v):
            for i in ['if', 'while', 'for', 'elif']:
                v = re.sub(r'^_%s:' % i, '%s:' % i, v)
            return v
        G = pygraphviz.AGraph(directed=True)
        cov_lines = [i for i,j in arcs]
        for nid, cnode in CFGNode.cache.items():
            G.add_node(cnode.rid)
            n = G.get_node(cnode.rid)
            lineno = cnode.lineno()
            n.attr['label'] = "%d: %s" % (lineno, unhack(cnode.source()))
            for pn in cnode.parents:
                plineno = pn.lineno()
                if arcs:
                    if  (plineno, lineno) in arcs:
                        G.add_edge(pn.rid, cnode.rid, color='blue')
                    elif plineno == lineno and lineno in cov_lines:
                        G.add_edge(pn.rid, cnode.rid, color='blue')
                    else:
                        G.add_edge(pn.rid, cnode.rid, color='red')
                else:
                    G.add_edge(pn.rid, cnode.rid)
        return G
```

### The control flow graph extractor.

```python
class PyCFG:
    def __init__(self):
        self.founder = CFGNode(parents=[], ast=ast.parse('start').body[0]) # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}

    def parse(self, src):
        return ast.parse(src)

    def walk(self, node, myparents):
        if node is None: return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            fn = getattr(self, fname)
            v = fn(node, myparents)
            return v
        else:
            return myparents

    def on_module(self, node, myparents):
        """
        Module(stmt* body)
        """
        # each time a statement is executed unconditionally, make a link from
        # the result to next statement
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p

    def on_assign(self, node, myparents):
        """
        Assign(expr* targets, expr value)
        TODO: AugAssign(expr target, operator op, expr value)
        -- 'simple' indicates that we annotate simple name without parens
        TODO: AnnAssign(expr target, expr annotation, expr? value, int simple)
        """
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')

        p = [CFGNode(parents=myparents, ast=node)]
        p = self.walk(node.value, p)

        return p

    def on_pass(self, node, myparents):
        return [CFGNode(parents=myparents, ast=node)]

    def on_break(self, node, myparents):
        parent = myparents[0].parents[0]
        while not hasattr(parent, 'exit_nodes'):
            # we have ordered parents
            parent = CFGNode.i(parent).parents[0]

        assert hasattr(parent, 'exit_nodes')
        p = CFGNode(parents=myparents, ast=node)

        # make the break one of the parents of label node.
        parent.exit_nodes.append(p)

        # break doesnt have immediate children
        return []

    def on_continue(self, node, myparents):
        parent = myparents[0].parents[0]
        while not hasattr(parent, 'exit_nodes'):
            # we have ordered parents
            parent = parent.parents[0]
        assert hasattr(parent, 'exit_nodes')
        p = CFGNode(parents=myparents, ast=node)

        # make continue one of the parents of the original test node.
        parent.add_parent(p)

        # return the parent because a continue is not the parent
        # for the just next node
        return []

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


    def on_while(self, node, myparents):
        # For a while, the earliest parent is the node.test
        _test_node = CFGNode(parents=myparents, ast=ast.parse(
               '_while: %s' % astunparse.unparse(node.test).strip()).body[0])
        ast.copy_location(_test_node.ast_node, node.test)
        _test_node.exit_nodes = []
        test_node = self.walk(node.test, [_test_node])

        # we attach the label node here so that break can find it.

        # now we evaluate the body, one at a time.
        p1 = test_node
        for n in node.body:
            p1 = self.walk(n, p1)

        # the test node is looped back at the end of processing.
        _test_node.add_parents(p1)

        # link label node back to the condition.
        return _test_node.exit_nodes + test_node

    def on_if(self, node, myparents):
        _test_node = CFGNode(parents=myparents, ast=ast.parse(
              '_if: %s' % astunparse.unparse(node.test).strip()).body[0])
        ast.copy_location(_test_node.ast_node, node.test)
        test_node = self.walk(node.test, [_test_node])
        g1 = test_node
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        for n in node.orelse:
            g2 = self.walk(n, g2)

        return g1 + g2

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        return right

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        return right

    def on_unaryop(self, node, myparents):
        return self.walk(node.operand, myparents)

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

    def on_expr(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
        return self.walk(node.value, p)

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
        """
        >>> i = PyCFG()
        >>> i.walk("100")
        5
        """
        node = self.parse(src)
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
    cfg = PyCFG()
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
        cfg = PyCFG()
        cfg.gen_cfg(slurp(args.pythonfile).strip())
        g = CFGNode.to_graph(arcs)
        g.draw('out.png', prog='dot')
        print(g.string(), file=sys.stderr)
    elif args.cfg:
        cfg = get_cfg(args.pythonfile)
        for i in sorted(cfg.keys()):
            print(i,'parents:', cfg[i]['parents'], 'children:', cfg[i]['children'])
```
