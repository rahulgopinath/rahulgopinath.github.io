# ---
# published: true
# title: Search Based Fuzzing with Approach Level
# layout: post
# comments: true
# tags: search fuzzing
# categories: post
# ---
#  
# Fuzzing is one of the more easy to use and efficient means of testing software
# systems. The idea is that we produce random inputs that are then executed by
# the system. If the system does something unexpected (such as crashing) then we
# know that the path taken by the execution was not considered by the
# programmer, and that such a path may be exploited to make the program do
# something that was unintended by the developer.
# 
# However, simply throwing random inputs at the program does not work well
# beyond a point. The issue is that the vast majority of such inputs will be
# rejected by common validations present in the program, and hence will not
# penetrate deep into the program. If there are say ten validations in the
# input processing section of the program, and there is 0.5 probability at
# each branch point for failing the validation, only one out of thousand inputs
# will successfully traverse the input processing stage. This ratio can worsen
# quickly when loops and recursion is present, leaving a majority of statements
# in the program uncovered.
# 
# One possible solution to enable better coverage of the program is to guide
# new inputs toward statements branches and paths that were not taken
# previously. This is the basic intuition behind search based testing.
# The field of search based software testing starts from Korel [^korel1990] in
# 1990.
# 
# Directed fuzzing leverages intuitions behind search based testing for
# generating inputs.
# The idea is that given a set of inputs, and a set of uncovered program
# elements we compute how far away each input execution is from the uncovered
# program elements. Then, if we want to new inputs to cover these uncovered
# elements, we choose those inputs that produced executions that are closest to
# the targeted element, mutate them, generating new inputs, and execute these
# inputs, and choose those that produce executions that are closest to the
# required program element. The intuition here is that mutating those inputs
# that produced an execution closest to the target program element has a better
# chance of producing inputs that are even more closer than mutating inputs that
# produced executions that were more farther.
# 
# In this post, I will be covering *approach level*
# (also called *approximation level*) a metric that can be used
# for computing the execution distance of inputs. Approach level was first
# proposed by Wegener et al.[^wegener2001]
# 
# As before, we start by importing the prerequisites

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pycfg-0.0.1-py2.py3-none-any.whl 
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl

import random
import simplefuzzer as fuzzer
import pycfg

import pydot
import textwrap as tw


# ## Visualization prerequisites
# If you are unfamiliar with control-flow, please see the
# [post on control flow](/post/2019/12/08/python-controlflow/)
# to understand what control flow is about.
# 
# From the same post, we need a few visualization functions, which we redefine,
# as they are slightly different.


class Graphics:
    def display_dot(self, dotsrc):
        raise NotImplemented

class WebGraphics(Graphics):
    def display_dot(self, dotsrc):
        __canvas__(g.to_string())

# Use CLIGraphics if you are running from the command line

class CLIGraphics(Graphics):
    def __init__(self):
        global graphviz
        import graphviz
        globals()['graphviz'] = graphviz
        self.i = 0

    def display_dot(self, dotsrc):
        graphviz.Source(dotsrc).render(format='png', outfile='%s.png' % self.i)
        self.i += 1

# Change WebGraphics to CLIGraphics here if you want to run from the command line

if __name__ == '__main__':
    graphics = WebGraphics()

# More helper functions for visualization from the control flow post.

def get_color(p, c):
    color='black'
    while not p.annotation():
        if p.label == 'if:True':
            return 'blue'
        elif p.label == 'if:False':
            return 'red'
        p = p.parents[0]
    return color

def get_peripheries(p):
    annot = p.annotation()
    if annot  in {'<start>', '<stop>'}:
        return '2'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return '2'
    return '1'

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

# Finally the to_graph stitches all these together.

def to_graph(my_nodes, arcs=[], comment='',
             get_shape=lambda n: 'rectangle',
             get_peripheries=lambda n: '1', get_color=lambda p,c: 'black'):
    G = pydot.Dot(comment, graph_type="digraph")
    for nid, cnode in my_nodes:
        if not cnode.annotation():
            continue
        sn = '%s: %s' % (nid, cnode.annotation())
        G.add_node(pydot.Node(cnode.name(),
                              label=sn,
                              shape=get_shape(cnode),
                              peripheries=get_peripheries(cnode)))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            G.add_edge(pydot.Edge(gp, str(cnode.rid), color=color))
    return G

# Let us consider the triangle function. This is a simple function that given
# three sides of a triangle, tells you what kind of a triangle it is.

if __name__ == '__main__':
    triangle = '''\
    def triangle(a, b, c):
        if a == b:
            if b == c:
                return 'Equilateral'
            else:
                return 'Isosceles'
        else:
            if b == c:
                return "Isosceles"
            else:
                if a == c:
                    return "Isosceles"
                else:
                    return "Scalene"
    '''
    cfge = pycfg.PyCFGExtractor()
    cfge.eval(tw.dedent(triangle))
    g = to_graph(cfge.gstate.registry.items(),
             get_color=get_color,
             get_peripheries=get_peripheries,
             get_shape=get_shape)
    graphics.display_dot(g.to_string())

# Another example, which is the GCD of two numbers.
if __name__ == '__main__':
    gcd = '''
    def gcd(a,b):
        if a < b:
            c = a
            a = b
            b = c
        while b != 0:
            c = a
            a = b
            b = c % b
        return a
    '''
    cfge = pycfg.PyCFGExtractor()
    cfge.eval(tw.dedent(gcd))
    g = to_graph(cfge.gstate.registry.items(),
             get_color=get_color,
             get_peripheries=get_peripheries,
             get_shape=get_shape)
    graphics.display_dot(g.to_string())

# ## Extract control-flow-graph in JSON
# Next, we need a helper function to extract the control flow graph.
# Note, function definitions do not have a parent.

import ast
def get_fn_cfg(src):
    m = ast.parse(src)
    name = m.body[0].name 

    parent_keys = {}
    child_keys = {}
    cfg = pycfg.PyCFGExtractor()
    cfg.eval(src)
    cache = cfg.gstate.registry
    g = {}

    for k,v in cache.items():
        j = v.to_json()
        at_key = 'id' # use the id rather than line number
        at = j[at_key]
        parents_at = [cache[p].to_json()[at_key] for p in j['parents']]
        children_at = [cache[c].to_json()[at_key] for c in j['children']]
        if at not in g:
            g[at] = {'parents':set(), 'children':set()}
        # remove dummy nodes
        ps = set([p for p in parents_at if p != at])
        cs = set([c for c in children_at if c != at])
        g[at]['parents'] |= ps
        g[at]['children'] |= cs 

    start, stop = cfg.functions[name]
    return (g, start.rid, stop.rid)

# Let us consider our triangle.

if __name__ == '__main__':
    tri_cfg, tri_first, tri_last = get_fn_cfg(tw.dedent(triangle))
    for k in tri_cfg: print(k, tri_cfg[k])

# The GCD
if __name__ == '__main__':
    gcd_cfg, gcd_first, gcd_last = get_fn_cfg(tw.dedent(gcd))
    for k in gcd_cfg: print(k, gcd_cfg[k])

# Now, we are ready for the main content.
# 
# ## Approach Level
# 
# How do you compute the distance between an execution and a program element?
# The approach level says that given an execution path, the distance is given
# by how many critical branches there are between the program element and the
# execution. A critical branch is a branch that, once taken, removes the target
# from reachable nodes. More intuitively, it is the number of potential problem
# nodes that lay on the shortest path from the closest node that diverted
# control flow away from the target goal node. Stated otherwise, approach level
# gives the minimum number of control dependencies between the goal and
# the execution path of the current input.
# 
# A is *control dependent* on B if and only if the following are true:
# 
# * B has two successors
# * B dominates A
# * B is not post-dominated by A
# * There is a successor of B that is post dominated by A.
# 
# So, let us start defining these. The simplest is the successors
# 
# ### Successors

def successors(cfg, a, key='children'):
    seen = set()
    successors = list(cfg[a][key])
    to_process = list(successors)
    while to_process:
        nodeid, *to_process = to_process
        seen.add(nodeid)
        new_children = [c for c in cfg[nodeid][key] if c not in seen]
        successors.extend(new_children)
        to_process.extend(new_children)
    return set(successors)

# Using it.

if __name__ == '__main__':
    s = successors(gcd_cfg, gcd_first)
    print(s)

# Same with triangle.

if __name__ == '__main__':
    s = successors(tri_cfg, tri_first)
    print(s)

# Next, we define the dominator.
# 
# ### Dominator
# 
# From the wiki, a node $A$ on a control-flow graph dominates a node $$ B $$ if
# every path from the entry node to $$ B $$ must go through $$ A $$. It is 
# typically written as $$ A >> B $$. A *post dominates* B if every path from
# $$ B $$ must go through $$ A $$.
# 
# Let us see how to compute the dominator set.

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

# Using it for GCD

if __name__ == '__main__':
    dom = compute_dominator(gcd_cfg, start=gcd_first)
    for k in dom:
        print(k, dom[k])

# For Triangle

if __name__ == '__main__':
    dom = compute_dominator(tri_cfg, start=tri_first)
    for k in dom:
        print(k, dom[k])

# ### Control Dependent
# 
# We can now define control dependence directly.

def a_control_dependent_on_b(cfg, dom, postdom, a, b):
    # B has at least 2 successors in CFG
    if len(cfg[b]['children']) < 2: return False

    b_successors = successors(cfg, b)
    # B dominates A
    v1 = b in dom[a]
    # B is not post dominated by A
    v2 = a not in postdom[b]
    # there exist a successor for B that is post dominated by A
    v3 = any(a in postdom[s] for s in b_successors)
    return v1 and v2 and v3

# Using it. Note how node 8 is control dependent on 6 from the main figure.
if __name__ == '__main__':
    gcd_dom = compute_dominator(gcd_cfg, start=gcd_first)
    gcd_postdom = compute_dominator(gcd_cfg, start=gcd_last, key='children')
    c = a_control_dependent_on_b(gcd_cfg, gcd_dom, gcd_postdom, 8, 6)
    print(c)

# For triangle
# Note how node 22 is control dependent on 6 from the main figure.
if __name__ == '__main__':
    tri_dom = compute_dominator(tri_cfg, start=tri_first)
    tri_postdom = compute_dominator(tri_cfg, start=tri_last, key='children')
    c = a_control_dependent_on_b(tri_cfg, tri_dom, tri_postdom, 22, 6)
    print(c)

# ## Approach Level of given path
# Next, we compute the approach level of a given path. The idea is that we may
# have reached the head of the path, and we have a potential path from the head
# node to the tail node. We now want to find how far away the head is from the
# tail. We first define a small class to hold the path.

class PathFitness:
    def __init__(self, cfg, dom, postdom):
        self.cfg = cfg
        self.dom = dom
        self.postdom = postdom

# Next, the approach level itself. We need to go from the tail to the head.
# Remember that our target is the last node. That is, if we reverse the path,
# then the first node (hd).

def approach_level(cfg, dom, postdom, path):
    hd, *tl = reversed(path)
    return _approach_level(cfg, dom, postdom, hd, tl)

def _approach_level(cfg, dom, postdom, target, path):
    if not path: return 0
    # find the node
    nxt_target = None
    while path:
        n, *path = path
        if a_control_dependent_on_b(cfg, dom, postdom, target, n):
            nxt_target = n
            break
    cost = 1 if nxt_target is not None else 0
    return cost + _approach_level(cfg, dom, postdom, nxt_target, path)

# Using it for triangle
if __name__ == '__main__':
    ffn = PathFitness(tri_cfg, tri_dom, tri_postdom)
    print('TRI Approach Level %d' % approach_level(tri_cfg, tri_dom, tri_postdom, [1, 6, 22, 30, 36]))
    print('TRI Approach Level %d' % approach_level(tri_cfg, tri_dom, tri_postdom, [1, 6, 22, 30]))
    print('TRI Approach Level %d' % approach_level(tri_cfg, tri_dom, tri_postdom, [1, 6, 22, 25]))

# Using it for GCD
if __name__ == '__main__':
    ffn = PathFitness(gcd_cfg, gcd_dom, gcd_postdom)
    print('GCD Approach Level %d' % approach_level(gcd_cfg, gcd_dom, gcd_postdom, [1, 6, 8, 10, 12, 15, 19, 31]))
    print('GCD Approach Level %d' % approach_level(gcd_cfg, gcd_dom, gcd_postdom, [1, 6, 15, 19, 31]))

# So, how do you use this for fuzzing? Given a program, and an uncovered
# program element such as a node (the target), we find all nodesin the program
# from which we can reach the uncovered node. Next, we compute the shortest path
# from such nodes to the target node. Then we compute the approach level to the
# target for each of these nodes. Given an input, we compute all the nodes that
# it covers, then identify all the nodes from which it can *reach* the target
# node, and finally, we find the node with the *minimum* of the approach levels
# that we computed previously. This would be the score of the corresponding
# input. We choose all inputs (based on our population size) that have the least
# approach level, and use that for evolution.
# 
# [^korel1990]: Bogdan Korel. "Automated software test data generation." IEEE Transactions on software engineering, 1990
# [^wegener2001]: J. Wegener, A. Baresel, and H. Sthamer. "Evolutionary test environment for automatic structural testing." Information and software technology, 2001
