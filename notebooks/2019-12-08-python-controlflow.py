# ---
# published: true
# title: The Python Control Flow Graph
# layout: post
# comments: true
# tags: controlflow
# categories: post
# ---

# We [previously discussed](/post/2019/12/07/python-mci/) how one can write an interpreter for
# Python. We hinted at that time that the machinery could be used for a variety of
# other applications, including exctracting the call and control flow graph. In this
# post, we will show how one can extract the control flow graph using such an interpteter.
# Note that a much more complete implementation can be found [here](https://github.com/vrthra/pycfg).
# 
# A [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) is a directed graph
# data structure that encodes all paths that may be traversed through a program. That is, in some
# sense, it is an abstract view of the interpreter as a whole.
# 
# This implementation is based on the [fuzzingbook CFG appendix](https://www.fuzzingbook.org/html/ControlFlow.html)
# However, the fuzzingbook implementation is focused on Python statements as it is used primarily for
# visualization, while this is based on basic blocks with the intension of using it for code
# generation.
# 
# Control flow graphs are useful for a variety of tasks. They are one of the most frequently
# used tools for visualization. But more imporatntly it is the starting point for further
# analysis of the program including code generation, optimizations, and other static analysis
# techniques.
# 
# #### Prerequisites
#
# As before, we start with the prerequisite imports.

#^
# matplotlib
# networkx

#@
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl

import ast
import pydot
import metacircularinterpreter

# #### A few helper functions for visualization

class Graphics:
    def display_dot(self, dotsrc):
        raise NotImplemented

class WebGraphics(Graphics):
    def display_dot(self, dotsrc):
        __canvas__(g.to_string())


class CLIGraphics(Graphics):
    def __init__(self):
        global graphviz
        import graphviz
        globals()['graphviz'] = graphviz
        self.i = 0

    def display_dot(self, dotsrc):
        graphviz.Source(dotsrc).render(format='png', outfile='%s.png' % self.i)
        self.i += 1

# 
if __name__ == '__main__':
    graphics = WebGraphics()
 
# The *color* is used to determine whether true or false branch was taken.

def get_color(p, c):
    color='black'
    while not p.annotation():
        if p.label == 'if:True':
            return 'blue'
        elif p.label == 'if:False':
            return 'red'
        p = p.parents[0]
    return color

# The *peripheries* determines the number of border lines. Start and stop gets double borders.

def get_peripheries(p):
    annot = p.annotation()
    if annot  in {'<start>', '<stop>'}:
        return '2'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return '2'
    return '1'

# The *shape* determines the kind of node. A diamond is a conditional, and start and stop are ovals.

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

# The `to_graph()` function produces a graph from the nodes in the registry.

def to_graph(my_nodes, arcs=[], comment='',
             get_shape=lambda n: 'rectangle',
             get_peripheries=lambda n: '1', get_color=lambda p,c: 'black'):
    G = pydot.Dot(comment, graph_type="digraph")
    for nid, cnode in my_nodes:
        if not cnode.annotation():
            continue
        sn = cnode.annotation()
        G.add_node(pydot.Node(cnode.name(),
                              label=sn,
                              shape=get_shape(cnode),
                              peripheries=get_peripheries(cnode)))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            G.add_edge(pydot.Edge(gp, str(cnode.rid), color=color))
    return G


# ### The CFGNode
# 
# The control flow graph is a graph, and hence we need a data structue for the *node*. We need to store the parents
# of this node, the children of this node, and register itself in the registery.

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

# Given that it is a directed graph node, we need the ability to add parents and children.

class CFGNode(CFGNode):
    def add_child(self, c):
        if c not in self.children:
            self.children.append(c)

    def set_parents(self, p):
        self.parents = p

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

# A few convenience methods to make our life simpler.

class CFGNode(CFGNode):
    def __eq__(self, other):
        return self.rid == other.rid

    def __neq__(self, other):
        return self.rid != other.rid

    def lineno(self):
        if hasattr(self.ast_node, 'lineno'):
            if (isinstance(self.ast_node, ast.AnnAssign)):
                if self.ast_node.target.id == 'exit':
                    return -self.ast_node.lineno
            return self.ast_node.lineno
        # should we return the parent line numbers instead?
        return 0
        
    def name(self):
        return str(self.rid)
        
    def expr(self):
        return self.source()
        
    def __str__(self):
        return "id:%d line[%d] parents: %s : %s" % \
           (self.rid, self.lineno(),
            str([p.rid for p in self.parents]), self.source())

    def __repr__(self):
        return str(self)

    def source(self):
        if self.ast_node is None: return ''
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

# The usage is as below:
if __name__ == '__main__':
    gs = GraphState()
    start = CFGNode(parents=[], ast=ast.parse('start').body, state=gs)
    g = to_graph(gs.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# ### Extracting the control flow
# 
# The control flow graph is essentially a source code walker, and shares the basic
# structure with our interpreter.

class PyCFGExtractor(metacircularinterpreter.PyMCInterpreter):
    def __init__(self):
        self.gstate = self.create_graphstate()
        self.founder = CFGNode(parents=[],
                               ast=ast.parse('start').body[0],
                               state=self.gstate) # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}

    def create_graphstate(self):
        return GraphState()

# As before, we define `walk()` that walks a given AST node.

# A major difference from MCI is in the functions that handle each node. Since it is a directed
# graph traversal, our `walk()` accepts a list of parent nodes that point to this node, and also
# invokes the various `on_*()` functions with the same list. These functions in turn return a list
# of nodes that exit them.
# 
# While expressions, and single statements only have one node that comes out of them, control flow
# structures and function calls can have multiple nodes that come out of them going into the next
# node. For example, an `If` statement will have a node from both the `if.body` and `if.orelse`
# going into the next one.

class PyCFGExtractor(PyCFGExtractor):
    def walk(self, node, myparents):
        if node is None: return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, myparents)
        raise SyntaxError('walk: Not Implemented in %s' % type(node))

# parse is just ast.parse
class PyCFGExtractor(PyCFGExtractor):
    def parse(self, src):
        return ast.parse(src)

# defining eval.
class PyCFGExtractor(PyCFGExtractor):
    def eval(self, src):
        for i,l in enumerate(src.split('\n')):
            print(i+1, l)
        node = self.parse(src)
        nodes = self.walk(node, [self.founder])
        self.last_node = CFGNode(parents=nodes,
                                 ast=ast.parse('stop').body[0],
                                 state=self.gstate)
        ast.copy_location(self.last_node.ast_node, self.founder.ast_node)
        self.post_eval()

    def post_eval(self): ... # to be overridden

# #### Pass
# 
# The pass statement is trivial. It simply adds one more node.

class PyCFGExtractor(PyCFGExtractor):
    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        return p

# Here is the CFG from a single pass statement.
# 
if __name__ == '__main__':
    s = """\
    pass
    """
    cfge = PyCFGExtractor()
    cfge.on_pass(node=ast.parse(s).body[0], myparents=[start])
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### Module(stmt* body)
# 
# We next define the `Module`. A python module is composed of a sequence of statements,
# and the graph is a linear path through these statements. That is, each time a statement
# is executed, we make a link from it to the next statement.

class PyCFGExtractor(PyCFGExtractor):
    def on_module(self, node, myparents):
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p

# Here is the CFG from the following which is wrapped in a module
if __name__ == '__main__':
    s = """\
    pass
    pass
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# ### Expressions
# #### Primitives
# 
# How should we handle primitives? Since they are simply interpreted as is, they can be embedded right in.

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

# They however, are simple expressions

class PyCFGExtractor(PyCFGExtractor):
    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node, state=self.gstate)]
        return p

# Generating the following CFG
# 
if __name__ == '__main__':
    s = """\
    10
    'a'
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())


# ### Arithmetic expressions
# 
# The following implements the arithmetic expressions. The `unaryop()` simply walks
# the arguments and adds the current node to the chain. The `binop()` has to walk
# the left argument, then walk the right argument, and finally insert the current
# node in the chain. `compare()` is again similar to `binop()`. `expr()`, again has
# only one argument to walk, and one node out of it.

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

# CFG for this expression
# 
if __name__ == '__main__':
    s = """
    10+1
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())


# #### Assign(expr* targets, expr value)
# 
# Unlike MCI, assignment is simple as it has only a single node coming out of it.
# 
# The following are not yet implemented:
# 
# * AugAssign(expr target, operator op, expr value)
# * AnnAssign(expr target, expr annotation, expr? value, int simple)
# 
# Further, we do not yet implement parallel assignments.

class PyCFGExtractor(PyCFGExtractor):
    def on_assign(self, node, myparents):
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')
        p = [CFGNode(parents=myparents, ast=node, state=self.gstate)]
        p = self.walk(node.value, p)
        return p

# Example

if __name__ == '__main__':
    s = """
    a = 10+1
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())


# #### Name

class PyCFGExtractor(PyCFGExtractor):
    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='', state=self.gstate)]
        return p

# ### Control structures
# 
# #### If
# 
# We now come to the control structures. For the `if` statement, we have two
# parallel paths. We first evaluate the test expression, then add a new node
# corresponding to the if statement, and provide the paths through the `if.body`
# and `if.orelse`.

class PyCFGExtractor(PyCFGExtractor):
    def on_if(self, node, myparents):
        p = self.walk(node.test, myparents)
        test_node = [CFGNode(parents=myparents, ast=ast.parse(
                            '_if: %s' % ast.unparse(node.test).strip()).body[0],
                            annot="if: %s" % ast.unparse(node.test).strip(),
                            state=self.gstate)]
        ast.copy_location(test_node[0].ast_node, node.test)
        g1 = test_node
        g_true = [CFGNode(parents=g1,
                          ast=ast.parse('_if: True').body[0],
                          label="if:True",
                          annot='',
                          state=self.gstate)]
        ast.copy_location(g_true[0].ast_node, node.test)
        g1 = g_true
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        g_false = [CFGNode(parents=g2,
                           ast=ast.parse('_if: False').body[0],
                           label="if:False",
                           annot='',
                           state=self.gstate)]
        ast.copy_location(g_false[0].ast_node, node.test)
        g2 = g_false
        for n in node.orelse:
            g2 = self.walk(n, g2)
        return g1 + g2

# Example
# 
if __name__ == '__main__':
    s = """\
    a = 1
    if a>1:
        a = 1
    else:
        a = 0
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### While

# The `while` statement is more complex than the `if` statement. For one,
# we need to provide a way to evaluate the condition at the beginning of
# each iteration.
# 
# Essentially, given something like this:
# 
# ```python
# while x > 0:
#     statement1
#     if x:
#        continue;
#     if y:
#        break
#     statement2
# ```
# 
# We need to expand this into:
# 
# ```
# lbl1: v = x > 0
# lbl2: if not v: goto lbl2
#       statement1
#       if x: goto lbl1
#       if y: goto lbl3
#       statement2
#       goto lbl1
# lbl3: ...
# 
# ```
# 
# The basic idea is that when we walk the `node.body`, if there is a break
# statement, it will start searching up the parent chain, until it finds a node with
# `loop_entry` label. Then it will attach itself to the `exit_nodes` as one
# of the exits.

class PyCFGExtractor(PyCFGExtractor):
    def on_while(self, node, myparents):
        loop_id = self.gstate.counter
        lbl1_node = CFGNode(parents=myparents,
                            ast=node,
                            label='loop_entry',
                            annot='%s: while' % loop_id,
                            state=self.gstate)
        p = self.walk(node.test, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=node.test, label='while:test',
               annot='if: %s' % ast.unparse(node.test).strip(), state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node],
                          ast=None,
                          label="if:False",
                          annot='',
                          state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node],
                         ast=None,
                         label="if:True",
                         annot='',
                         state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        for n in node.body:
            p = self.walk(n, p)

        # the last node is the parent for the lb1 node.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

# Example
if __name__ == '__main__':
    s = """\
    x = 1
    while x > 0:
        x = x -1
    y = x
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### Break
# 
# As we explained before, the `break` when it is encountred, looks up
# the parent chain. Once it finds a parent that has the `loop_entry` label,
# it attaches itself to that parent. The statements following the `break` are not
# its immediate children. Hence, we return an empty list.

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

# Example

if __name__ == '__main__':
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
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### Continue
# 
# Continue is similar to `break`, except that it has to restart the loop. Hence,
# it adds itself as a parent to the node with `loop_entry` attribute. As like `break`,
# execution does not proceed to the lexically next statement after `continue`. Hence,
# we return an empty set.

class PyCFGExtractor(PyCFGExtractor):
    def on_continue(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]
            
        p = CFGNode(parents=myparents, ast=node, state=self.gstate)
        parent.add_parent(p)
        
        return []

# Example
# 
if __name__ == '__main__':
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
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### For
# 
# The `For` statement in Python is rather complex. Given a for loop as below
# 
# ```python
# for i in my_expr:
#     statement1
#     statement2
# ```
# 
# This has to be extracted to the following:
# 
# ```python
# lbl1: 
#       __iv = iter(my_expr)
# lbl2: if __iv.length_hint() > 0: goto lbl3
#       i = next(__iv)
#       statement1
#       statement2
# lbl3: ...
# ```
#
# We need `on_call()` for implementing `on_for()`. Essentially, we walk through
# the arguments, then add a node corresponding to the call to the parents.

class PyCFGExtractor(PyCFGExtractor):
    def on_call(self, node, myparents):
        p = myparents
        for a in node.args:
            p = self.walk(a, p)
        myparents[0].add_calls(node.func)
        p = [CFGNode(parents=p,
                     ast=node,
                     label='call',
                     annot='',
                     state=self.gstate)]
        return p

class PyCFGExtractor(PyCFGExtractor):
    def on_for(self, node, myparents):
        #node.target in node.iter: node.body
        loop_id = self.gstate.counter

        for_pre = CFGNode(parents=myparents,
                          ast=None,
                          label='for_pre',
                          annot='',
                          state=self.gstate)

        init_node = ast.parse('__iv_%d = iter(%s)' % (
            loop_id, ast.unparse(node.iter).strip())).body[0]
        p = self.walk(init_node, [for_pre])

        lbl1_node = CFGNode(parents=p,
                            ast=node,
                            label='loop_entry',
                            annot='%s: for' % loop_id,
                            state=self.gstate)
        _test_node = ast.parse(
                '__iv_%d.__length__hint__() > 0' % loop_id).body[0].value
        p = self.walk(_test_node, [lbl1_node])

        lbl2_node = CFGNode(parents=p,
                            ast=_test_node,
                            label='for:test',
                            annot='for: %s' % ast.unparse(_test_node).strip(),
                            state=self.gstate)
        g_false = CFGNode(parents=[lbl2_node],
                          ast=None,
                          label="if:False",
                          annot='', state=self.gstate)
        g_true = CFGNode(parents=[lbl2_node],
                         ast=None,
                         label="if:True",
                         annot='',
                         state=self.gstate)
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        # now we evaluate the body, one at a time.
        for n in node.body:
            p = self.walk(n, p)

        # the test node is looped back at the end of processing.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

# Example
 
if __name__ == '__main__':
    s = """\
    x = 1
    for i in val:
        x = x -1
    y = x
    """
    cfge = PyCFGExtractor()
    cfge.eval(s)
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# more
if __name__ == '__main__':
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
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# more
if __name__ == '__main__':
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
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())

# #### FunctionDef
# 
# When defining a function, we should define the `return_nodes` for the
# return statement to hook into. Further, we should also register our
# functions.
# 
# Next, we have to decide: Do we want the call graph of the function definition to
# be attached to the previous statements? In Python, the function definition itself
# is independent of the previous statements. Hence, here, we choose not to have
# parents for the definition.

class PyCFGExtractor(PyCFGExtractor):  
    def on_functiondef(self, node, myparents):
        # name, args, body, decorator_list, returns
        fname = node.name
        args = node.args
        returns = node.returns
        enter_node = CFGNode(
                parents=[], ast=ast.parse('enter: %s(%s)' % (
                node.name, ', '.join([a.arg for a in node.args.args]))).body[0],
                annot='<define>: %s' % node.name, state=self.gstate
                )  # sentinel
        enter_node.calleelink = True
        ast.copy_location(enter_node.ast_node, node)

        exit_node = CFGNode(parents=[], ast=ast.parse('exit: %s(%s)' % (
               node.name, ', '.join([a.arg for a in node.args.args]))).body[0],
               annot='<>: %s' % node.name, state=self.gstate
               ) #  sentinel
        enter_node.return_nodes = [] # sentinel

        p = [enter_node]
        for n in node.body:
            p = self.walk(n, p)

        for n in p:
            if n not in enter_node.return_nodes:
                enter_node.return_nodes.append(n)

        for n in enter_node.return_nodes:
            exit_node.add_parent(n)

        self.functions[fname] = [enter_node, exit_node]
        self.functions_node[enter_node.lineno()] = fname

        return myparents

# #### Return
# 
# For `return`, we need to look up which function we have to return from.

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

# We just need few more functions to ensure that our arrows are linked up
class PyCFGExtractor(PyCFGExtractor):
    def post_eval(self):
        self.update_children()
        self.update_functions()
        self.link_functions()

# First, we make sure that all the child nodes are linked to from the parents.
class PyCFGExtractor(PyCFGExtractor):
    def update_children(self):
        for nid,node in self.gstate.registry.items():
            for p in node.parents:
                p.add_child(node)

# Next, we make sure that for any node (marked by its line number), we know
# where it is defined.
class PyCFGExtractor(PyCFGExtractor):
    def get_defining_function(self, node):
        if node.lineno() in self.functions_node:
            return self.functions_node[node.lineno()]
        if not node.parents:
            self.functions_node[node.lineno()] = ''
            return ''
        val = self.get_defining_function(node.parents[0])
        self.functions_node[node.lineno()] = val
        return val

    def update_functions(self):
        for nid,node in self.gstate.registry.items():
            _n = self.get_defining_function(node)
        
# Finally, we link functions call sites.
class PyCFGExtractor(PyCFGExtractor):
    def link_functions(self):
        for nid,node in self.gstate.registry.items():
            if not node.calls: continue
            for calls in node.calls:
                if not calls in self.functions: continue
                enter, exit = self.functions[calls]
                enter.add_parent(node)
                if node.children:
                    # # unlink the call statement
                    assert node.calllink > -1
                    node.calllink += 1
                    for i in node.children:
                        i.add_parent(exit)

# Example
 
if __name__ == '__main__':
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
    g = to_graph(cfge.gstate.registry.items(),
                 get_color=get_color,
                 get_peripheries=get_peripheries,
                 get_shape=get_shape)
    graphics.display_dot(g.to_string())


