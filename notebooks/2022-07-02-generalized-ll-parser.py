# ---
# published: true
# title: Generalized LL (GLL) Parser
# layout: post
# comments: true
# tags: controlflow
# categories: post
# ---

# We [previously discussed](/post/2021/02/06/earley-parsing/) the
# implementation of an Earley parser with Joop Leo's optimizations. Earley
# parser is one of the general context-free parsing algorithms available.
# Another popular general context-free parsing algorightm is
# *Generalized LL* parsing, which was invented by
# Elizabeth Scott and Adrian Johnstone. In this post, I provide a complete
# implementation and a tutorial on how to implement a GLL parser in Python.
# 
# **Note:** This post is not complete. Given the interest in GLL parsers, I am
# simply providing the source (which substantially follows the publications)
# until I have more bandwidth to complete the tutorial. However, the code
# itself is complete, and can be used.
# 
# #### Prerequisites
#
# As before, we start with the prerequisite imports.


#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

import simplefuzzer as fuzzer
import earleyparser as ep
import random

# ## Our grammar

grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}

# Defining the start symbol

START = '<start>'

# ## Utilities.
# We start with a few utilities.
# ### show_dot()
# We often have to display a partial parse of a rule. We use `@` to indicate
# until where the current rule has parsed.

def show_dot(g, t):
    sym, n_alt, pos = t
    rule = g[sym][n_alt]
    return sym + '::=' + ' '.join(rule[0:pos]) + ' @ ' + ' '.join(rule[pos:])

# Using it:

if __name__ == '__main__':
    print(show_dot(grammar, ('<fact>', 1, 1)))

# We also need nullable() [earley-parsing](/post/2021/02/06/earley-parsing/#nonterminals-deriving-empty-strings).

if __name__ == '__main__':
    print(ep.nullable(grammar))

# ## The GSS Graph
# A naive conversion of recursive descent parsing to generalized recursive
# descent parsing can be done by maintaining independent stacks for each thread.
# However, this approach is very costly. GLL optimizes what it needs to generate
# by using a Graph-Structured Stack.
# The idea is to share as much of the stack during parsing as possible.
# 
# ### The GSS Node
# A GSS node is simply a node that can contain any number of children. Each
# child is actually an edge in the graph.
# 
# (Each GSS Node is of the form $$L_i^j$$ where $$j$$ is the index of the
# character consumed. However, we do not need to know the internals of the label
# here).

class GSSNode:
    def __init__(self, label): self.label, self.children = label, []
    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

# ### The GSS container
# Next, we define the graph container. We keep two structures. self.graph which
# is the shared stack, and  P which is the set of labels that went through a
# `fn_return`, i.e. `pop` operation.

class GSS:
    def __init__(self): self.graph, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.graph:
            self.graph[my_label], self.P[my_label] = GSSNode(my_label), []
        return self.graph[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        return self.P[label]

    def __repr__(self): return str(self.graph)

# ## SPPF Graph
# To ensure that we can actually extract the parsed trees, we use 
# the Shared Packed Parse Forest datastructure to represent parses.

# ### SPPF Node

class SPPFNode:
    def __init__(self): self.children, self.label = [], '<None>'

    def __eq__(self, o): return self.label == o.label

    def add_child(self, child): self.children.append(child)

    def to_tree(self, hmap, tab): raise NotImplemented

    def to_s(self, g): return self.label[0]

    def __repr__(self): return 'SPPF:%s' % str(self.label)


# ### SPPF Dummy Node
# The dummy SPPF node is used to indicate the empty node at the end of rules.

class SPPF_dummy(SPPFNode):
    def __init__(self, s, j, i):
        self.label, self.children = (s, j, i), []

    def to_tree(self, hmap, tab): return ['$', []]

# ### SPPF Symbol Node
# x is a terminal, nonterminal, or epsilon -- ''
# j and i are the extents.
# Each symbol can contain multiple packed nodes each
# representing a different derivation. See getNodeP

class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i):
        assert x is not None
        self.label, self.children = (x, j, i), []

    def to_tree(self, hmap, tab):
        key = self.to_s(g)
        if key is None: return ['', []]
        assert isinstance(key, str)
        if self.children:
            n = random.choice(self.children)
            assert isinstance(n, SPPF_packed_node)
            return [key, n.to_tree(hmap, tab+1)]
        return [key, []]

# ### SPPF Intermediate Node
# Has only two children max (or 1 child).
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i):
        self.label, self.children = (t, j, i), []

    def right_extent(self): return self.label[-1]

    def to_tree(self, hmap, tab):
        key = self.to_s(g)
        assert isinstance(self, SPPF_intermediate_node)
        assert not isinstance(key, str)
        ret = []
        for n in self.children:
            v = n.to_tree(hmap, tab+1)
            ret.extend(v)
        return ret

# ### SPPF Packed Node

class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k, children):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = children # left and right or just left

    def to_tree(self, hmap, tab):
        key = self.to_s(g)
        # packed nodes (rounded) represent one particular derivation. No need to add key
        assert not isinstance(key, str)
        children = []
        # A packed node may have two children, just left and right.
        for n in self.children:
            if isinstance(n, SPPF_symbol_node):
                v = n.to_tree(hmap, tab+1)
                children.append(v)
            elif isinstance(n, SPPF_intermediate_node):
                v = n.to_tree(hmap, tab+1)
                children.extend(v)
            elif isinstance(n, SPPF_dummy):
                pass
            else:
                assert False
        return children

# ## The GLL parser
# We can now build our GLL parser.
#
# We first define our initialization
class GLLStructuredStackP:
    def __init__(self, input_str):
        self.I = input_str + '$' # read the input I and set I[m] = `$`
        self.m = len(input_str)
        self.gss = GSS()
        # create GSS node u_0 = (L_0, 0)
        self.stack_bottom = self.gss.get(('L0', 0))

        # R := \empty
        self.threads = []

        self.U = [[] for j in range(self.m+1)]
        self.SPPF_nodes = {}

    def set_grammar(self, g):
        self.grammar = g
        self.nullable = ep.nullable(g)

# ### GLL add thread (add)
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, u, i, w):
        # w needs to be an SPPF node.
        assert not isinstance(u, int)
        assert isinstance(w, SPPFNode)
        if (L, u, w) not in self.U[i]:
            self.U[i].append((L, u, w))
            self.threads.append((L, u, i, w))

# ### GLL fn_return (pop)
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, u, i, z):
        # z needs to be SPPF.
        assert isinstance(z, SPPFNode)
        if u != self.stack_bottom:
            # let (L, k) be label of u
            (L, k) = u.label
            self.gss.add_parsed_index(u.label, z)
            for v,w in u.children: # edge labeled w, an SPPF node.
                assert isinstance(w, SPPFNode)
                #assert w.label[2] == z.label[1]
                y = self.getNodeP(L, w, z)
                self.add_thread(L, v, i, y)
        return u

# ### GLL register_return (create)
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, u, i, w): # returns to stack_top
        assert isinstance(w, SPPFNode)
        v = self.gss.get((L, i)) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        #assert not v.children # test. why are there no children?
        v_to_u_labeled_w = [c for c,lbl in v.children if c.label == u.label and lbl == w]
        if not v_to_u_labeled_w:
            # create an edge from v to u labelled w
            v.children.append((u,w))

            for z in self.gss.parsed_indexes(v.label):
                assert isinstance(z, SPPF_intermediate_node)
                y = self.getNodeP(L, w, z)
                h = z.right_extent()
                self.add_thread(v.L, u, h, y) # v.L == L
        return v

# ### GLL utilities.

class GLLStructuredStackP(GLLStructuredStackP):
    def next_thread(self): # i \in R
        t, *self.threads = self.threads
        return t

    def get_sppf_dummy_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_dummy(*n)
        return self.SPPF_nodes[n]

    def get_sppf_symbol_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_symbol_node(*n)
        return self.SPPF_nodes[n] 

    def get_sppf_intermediate_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_intermediate_node(*n)
        return self.SPPF_nodes[n] 

    def sppf_find_or_create(self, label, j, i):
        if label is None:
            return self.get_sppf_dummy_node((label, j, i))
        elif isinstance(label, str):
            return self.get_sppf_symbol_node((label, j, i))
        else:
            return self.get_sppf_intermediate_node((label, j, i))

# We also need the to produce SPPF nodes correctly.

class GLLStructuredStackP(GLLStructuredStackP):
    # getNode(x, i) creates and returns an SPPF node labeled (x, i, i+1) or
    # (epsilon, i, i) if x is epsilon
    def getNodeT(self, x, i):
        if x is None:
            return self.get_sppf_dummy_node((x, i, i))
        else:
            return self.get_sppf_symbol_node((x, i, i+1))

    # getNodeP(X::= alpha.beta, w, z) takes a grammar slot X ::= alpha . beta
    # and two SPPF nodes w, and z (z may be dummy node $).
    # the nodes w and z are not packed nodes, and will have labels of form
    # (s,j,k) and (r, k, i)
    def getNodeP(self, X_rule_pos, w, z): # w is left node, z is right node
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha = rule[:dot]
        beta = rule[dot:]
        if self.is_non_nullable_alpha(X, rule, dot) and beta: # beta != epsilon
            return z
        else:
            if beta == []: # if beta = epsilon from GLL_parse_tree_generation
                t = X # symbol node.
            else:
                t = X_rule_pos
            (q, k, i) = z.label # suppose z has label (q,k,i)
            if (w.label[0] != '$'): # is not delta
                # returns (t,j,i) <- (X:= alpha.beta, k) <- w:(s,j,k),<-z:(r,k,i)
                (s,j,_k) = w.label # suppose w has label (s,j,k)
                # w is the left node, and z is the right node. So the center (k)
                # should be shared.
                assert k == _k
                # if there does not exist an SPPF node y labelled (t, j, i) create one
                y = self.sppf_find_or_create(t, j, i)

                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    # create a child of y with left child with w right child z
                    # the extent of w-z is the same as y
                    # packed nodes do not keep extents
                    pn = SPPF_packed_node(X_rule_pos, k, [w,z])
                    y.add_child(pn)
            else:
                # if there does not exist an SPPF node y labelled (t, k, i) create one
                # returns (t,k,i) <- (X:= alpha.beta, k) <- (r,k,i)
                y = self.sppf_find_or_create(t, k, i)
                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    pn = SPPF_packed_node(X_rule_pos, k, [z])
                    y.add_child(pn) # create a child with child z
            return y

    # adapted from Exploring_and_Visualizing paper.
    def is_non_nullable_alpha(self, X, rule, dot):
        #  we need to convert this to X := alpha . beta
        alpha = rule[:dot]
        if not alpha: return False
        if len(alpha) != 1: return False
        if fuzzer.is_terminal(alpha[0]): return True
        if alpha[0] in self.nullable: return False
        return True

# ## Building the parser with GLL
# At this point, we are ready to build our parser.
# ### Compiling an empty rule
# We start with compiling an epsilon rule.

def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            c_r = parser.getNodeT(None, cur_idx)
            cur_sppf_node = parser.getNodeP(L, cur_sppf_node, c_r)
            L = 'L_'
            continue
''' % (key, n_alt,show_dot(g, (key, n_alt, 0)))

# Using it.
if __name__ == '__main__':
    v = compile_epsilon(grammar, '<expr>', 1)
    print(v)

# ### Compiling a Terminal Symbol
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[cur_idx] == '%s':
                c_r = parser.getNodeT(parser.I[cur_idx], cur_idx)
                cur_idx = cur_idx+1
                L = %s
                cur_sppf_node = parser.getNodeP(L, cur_sppf_node, c_r)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), token, Lnxt)

# ### Compiling a Nonterminal Symbol
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, cur_idx, cur_sppf_node)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), Lnxt, token)

# Using it.
if __name__ == '__main__':
    rule = grammar['<expr>'][1]
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            v = compile_nonterminal(grammar, '<expr>', 1, i, len(rule), t)
        else:
            v = compile_terminal(grammar, '<expr>', 1, i, len(rule), t)
        print(v)

# ### Compiling a Rule
# `n_alt` is the position of `rule`.
def compile_rule(g, key, n_alt, rule):
    res = []
    if not rule:
        r = compile_epsilon(g, key, n_alt)
        res.append(r)
    else:
        for i, t in enumerate(rule):
            if fuzzer.is_nonterminal(t):
                r = compile_nonterminal(g, key, n_alt, i, len(rule), t)
            else:
                r = compile_terminal(g, key, n_alt, i, len(rule), t)
            res.append(r)
        # if epsilon present, we do not want this branch.
        res.append('''\
        elif L == ('%s',%d,%d): # %s
            L = 'L_'
            continue
''' % (key, n_alt, len(rule), show_dot(g, (key, n_alt, len(rule)))))
    return '\n'.join(res)

# Using it.
if __name__ == '__main__':
    v = compile_rule(grammar, '<expr>', 1, grammar['<expr>'][1])
    print(v)


# ### Compiling a Definition
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # need to check first() if performance is important.
            # %s
            parser.add_thread( ('%s',%d,0), stack_top, cur_idx, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt, rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

# Using it.
if __name__ == '__main__':
    v = compile_def(grammar, '<expr>', grammar['<expr>'])
    print(v)

# ### Compiling a Grammar

def compile_grammar(g, start):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = ['''\
def parse_string(parser):
    parser.set_grammar(
%s
    )
    # L contains start nt.
    S = '%s'
    end_rule = SPPF_dummy('$', 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return 'success'
                else: return 'error'
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = 'L0' # goto L_0
            continue
    ''' % (pp.pformat(g), start)]
    for k in g: 
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    return '\n'.join(res)

# Using it
if __name__ == '__main__':
    v = compile_grammar(grammar, '<start>')
    print(v)

# ## Running it
# ### 1
if __name__ == '__main__':
    G1 = {
        '<S>': [['c']]
    }
    mystring = 'c'
    res = compile_grammar(G1, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 2
if __name__ == '__main__':
    G2 = {
        '<S>': [['c', 'c']]
    }
    mystring = 'cc'
    res = compile_grammar(G2, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 3
if __name__ == '__main__':
    G3 = {
        '<S>': [['c', 'c', 'c']]
    }
    mystring = 'ccc'
    res = compile_grammar(G3, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 4
if __name__ == '__main__':
    G4 = {
        '<S>': [['c'],
                ['a']]
    }
    mystring = 'a'
    res = compile_grammar(G4, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 5

if __name__ == '__main__':
    G5 = {
        '<S>': [['<A>']],
        '<A>': [['a']]
    }
    mystring = 'a'
    res = compile_grammar(G5, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ## Expression

# ### 1
if __name__ == '__main__':
    mystring = '(1+1)*(23/45)-1'
    res = compile_grammar(grammar, START)
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 2
if __name__ == '__main__':
    a_grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<expr>', '+', '<expr>'],
        ['<expr>', '-', '<expr>'],
        ['<expr>', '*', '<expr>'],
        ['<expr>', '/', '<expr>'],
        ['(', '<expr>', ')'],
        ['<integer>']],
    '<integer>': [
        ['<digits>']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
    }
    mystring = '(1+1)*(23/45)-1'
    res = compile_grammar(a_grammar, START)
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ## A few more examples
if __name__ == '__main__':
    RR_GRAMMAR2 = {
        '<start>': [
        ['b', 'a', 'c'],
        ['b', 'a', 'a'],
        ['b', '<A>', 'c']
        ],
        '<A>': [['a']],
    }
    mystring = 'bac'
    res = compile_grammar(RR_GRAMMAR2, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    RR_GRAMMAR3 = {
        '<start>': [['c', '<A>']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring = 'cababababab'
     
    res = compile_grammar(RR_GRAMMAR3, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(7)
     
    RR_GRAMMAR4 = {
        '<start>': [['<A>', 'c']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring = 'ababababc'
     
    res = compile_grammar(RR_GRAMMAR4, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(8)
     
    RR_GRAMMAR5 = {
    '<start>': [['<A>']],
    '<A>': [['a', 'b', '<B>'], []],
    '<B>': [['<A>']],
    }
    mystring = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR5, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(9)
     
    RR_GRAMMAR6 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<B>'], []],
    '<B>': [['b', '<A>']],
    }
    mystring = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR6, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(10)

    RR_GRAMMAR7 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']],
    }
    mystring = 'aaaaaaaa'

    res = compile_grammar(RR_GRAMMAR7, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(11)

    RR_GRAMMAR8 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']]
    }
    mystring = 'aa'

    res = compile_grammar(RR_GRAMMAR8, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(12)

    X_G1 = {
        '<start>': [['a']],
    }
    mystring = 'a'
    res = compile_grammar(X_G1, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G1')

    X_G2 = {
        '<start>': [['a', 'b']],
    }
    mystring = 'ab'
    res = compile_grammar(X_G2, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    print('X_G2')

    X_G3 = {
        '<start>': [['a', '<b>']],
        '<b>': [['b']]
    }
    mystring = 'ab'
    res = compile_grammar(X_G3, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G3')

    X_G4 = {
        '<start>': [
        ['a', '<a>'],
        ['a', '<b>'],
        ['a', '<c>']
        ],
        '<a>': [['b']],
        '<b>': [['b']],
        '<c>': [['b']]
    }
    mystring = 'ab'
    res = compile_grammar(X_G4, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring


    print('X_G4')

    X_G5 = {
        '<start>': [['<expr>']],
        '<expr>': [
            ['<expr>', '+', '<expr>'],
            ['1']]
    }
    X_G5_start = '<start>'

    mystring = '1+1'
    res = compile_grammar(X_G5, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring


    print('X_G5')

    X_G6 = {
        '<S>': [
        ['b', 'a', 'c'],
        ['b', 'a', 'a'],
        ['b', '<A>', 'c'],
        ],
        '<A>': [
            ['a']]
    }
    X_G6_start = '<S>'

    mystring = 'bac'
    res = compile_grammar(X_G6, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring)
    assert parse_string(g) == 'success'
    v = g.SPPF_nodes[g.root].to_tree(g.SPPF_nodes, tab=0)
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G6')

