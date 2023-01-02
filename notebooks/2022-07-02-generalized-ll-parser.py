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

import simplefuzzer as fuzzer

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

# We often have to display a partial parse of a rule. We use `@` to indicate
# until where the current rule has parsed.

def show_dot(g, t):
    sym, n_alt, pos = t
    rule = g[sym][n_alt]
    return sym + '::=' + ' '.join(rule[0:pos]) + ' @ ' + ' '.join(rule[pos:])

# Using it:

if __name__ == '__main__':
    print(show_dot(grammar, ('<fact>', 1, 1)))

# ## Utilities
# ### Nullable -- defined as before in [earley-parsing](/post/2021/02/06/earley-parsing/#nonterminals-deriving-empty-strings)

def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not fuzzer.is_nonterminal(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys

# Using it:

if __name__ == '__main__':
    print(nullable(grammar))


# ### The GSS Graph
# The GLL parser uses something called a Graph Structured Stack to limit the 
# space consumption during parsing. The idea is to share as much of the stack
# during parsing as possible.
# 
# #### The GSS Node
# Each GSS Node is of the form $$L_i^j$$ where $$j$$ is the index of the
# character consumed.

class GSSNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

# #### The GSS container

class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.gss:
            self.gss[my_label] = GSSNode(my_label)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        # indexes for which pop has been executed for label.
        return self.P[label]

    def __repr__(self): return str(self.gss)

# ### SPPF Graph
# To ensure that we can actually extract the parsed trees, we use 
# the Shared Packed Parse Forest datastructure to represent parses.

# #### SPPF Node

class SPPFNode:
    def __init__(self):
        self.children = []
        self.lablel = '<None>'
        pass

    def __eq__(self, o):
        return self.label == o.label

    def __repr__(self):
        return 'D:%s [%d]' % (str(self.label), len(self.children))

    def add_child(self, child):
        self.children.append(child)

# #### SPPF Dummy Node

class SPPF_dummy(SPPFNode):
    def __init__(self, s='$'):
        self.label = (s, 0, 0)
        self.children = []

# #### SPPF Symbol Node

class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, j, i):
        # x is a terminal, nonterminal, or epsilon -- ''
        # j and i are the extents
        #assert 0<= j <= i <= m
        self.label = (x, j, i)
        self.children = []

    def to_s(self, g):
        return (self.label[0])

# #### SPPF Intermediate Node
# Has only two children max (or 1 child).
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i):
        self.label = (t, j, i)
        self.children = []

    def right_extent(self):
        return self.label[-1]

    def to_s(self, g):
        #if isinstance(self.label[0], str):
        return (self.label[0])
        #((sym, n_alt, dot), i, j)  = self.label
        #return ( sym + ' ::= ' +
        #        str(g.grammar[sym][n_alt][:dot]) + '.' +
        #        str(g.grammar[sym][n_alt][dot:]) + ' ' + str(i) + ',' + str(j))

# #### SPPF Packed Node

class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k, children):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = children # left and right or just left

    def to_s(self, g):
        return (self.label[0])
        #(sym, n_alt, dot), lat = self.label
        #return ( sym + ' ::= ' +
        #        str(g.grammar[sym][n_alt][:dot]) + '.' +
        #        str(g.grammar[sym][n_alt][dot:]) + ' ' + str(lat) )

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
        self.nullable = nullable(g)

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

    def get_sppf_symbol_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_symbol_node(*n)
        return self.SPPF_nodes[n] 

    def get_sppf_intermediate_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_intermediate_node(*n)
        return self.SPPF_nodes[n] 

    def sppf_find_or_create(self, label, j, i):
        if isinstance(label, str):
            return self.get_sppf_symbol_node((label, j, i))
        else:
            return self.get_sppf_intermediate_node((label, j, i))


# # SPPF Build
    # getNode(x, i) creates and returns an SPPF node labeled (x, i, i+1) or
    # (epsilon, i, i) if x is epsilon
    def getNodeT(self, x, i):
        if x is None: h = i # x is epsilon
        else: h = i+1
        return self.get_sppf_symbol_node((x, i, h))

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
                assert k == _k # TODO: this should be true.
                #k = _k

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

# #### Compiling an empty rule

def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            c_r = parser.getNodeT(None, current_index)
            current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
            L = 'L_'
            continue
''' % (key, n_alt,show_dot(g, (key, n_alt, 0)))

# #### Compiling a Terminal Symbol
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[current_index] == '%s':
                c_r = parser.getNodeT(parser.I[current_index], current_index)
                current_index = current_index+1
                L = %s
                current_sppf_node = parser.getNodeP(L, current_sppf_node, c_r)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), token, Lnxt)

# #### Compiling a Nonterminal Symbol
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, current_index, current_sppf_node)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, show_dot(g, (key, n_alt, r_pos)), Lnxt, token)

# #### Compiling a Rule
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

# #### Compiling a Definition
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # need to check first() if performance is important.
            # %s
            parser.add_thread( ('%s',%d,0), stack_top, current_index, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)


# #### Compiling a Grammar

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
    end_rule = SPPF_dummy('$')
    L, stack_top, current_index, current_sppf_node = S, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, current_index, current_sppf_node) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return 'success'
                else: return 'error'
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, current_index, current_sppf_node) # pop
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
    G1 = {
        '<S>': [['c']]
    }
    mystring2 = 'c'
    res = compile_grammar(G1, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(1)

    G2 = {
        '<S>': [['c', 'c']]
    }
    mystring2 = 'cc'
    res = compile_grammar(G2, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(2)

    G3 = {
        '<S>': [['c', 'c', 'c']]
    }
    mystring2 = 'ccc'
    res = compile_grammar(G3, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(3)


    G4 = {
        '<S>': [['c'],
                ['a']]
    }
    mystring2 = 'a'
    res = compile_grammar(G4, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(4)


    G5 = {
        '<S>': [['<A>']],
        '<A>': [['a']]
    }
    mystring2 = 'a'
    res = compile_grammar(G5, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(5)


import random

def process_sppf_symbol(node, hmap, tab):
    key = node.to_s(g)
    if key is None:
        return ['$', []]
    assert isinstance(key, str)
    if node.children:
        n = random.choice(node.children)
        return [key, process_sppf_packed(n,hmap, tab+1)]
    return [key, []]

def process_sppf_packed(node, hmap, tab):
    key = node.to_s(g)
    # packed nodes (rounded) represent on particular derivation. No need to add key
    assert isinstance(node, SPPF_packed_node)
    assert not isinstance(key, str)
    children = []
    # A packed node may have two children, just left and right.
    children
    for n in node.children:
        if isinstance(n, SPPF_symbol_node):
            v = process_sppf_symbol(n,hmap, tab+1)
            children.append(v)
        elif isinstance(n, SPPF_intermediate_node):
            v = process_sppf_intermediate_node(n,hmap, tab+1)
            children.extend(v)
        else: assert False
    return children

def process_sppf_intermediate_node(node, hmap, tab):
    key = node.to_s(g)
    assert isinstance(node, SPPF_intermediate_node)
    #print(' '*tab, 'I', node.to_s(g))
    #assert len(node.children) == 1
    #n = random.choice(node.children)
    assert not isinstance(key, str)
    ret = []
    for n in node.children:
        v = process_sppf_packed(n,hmap, tab+1)
        ret.extend(v)
    return ret

# Using it.
if __name__ == '__main__':
    RR_GRAMMAR2 = {
        '<start>': [
        ['b', 'a', 'c'],
        ['b', 'a', 'a'],
        ['b', '<A>', 'c']
        ],
        '<A>': [['a']],
    }
    mystring2 = 'bac'
    res = compile_grammar(RR_GRAMMAR2, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    RR_GRAMMAR3 = {
        '<start>': [['c', '<A>']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring3 = 'cababababab'
     
    res = compile_grammar(RR_GRAMMAR3, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring3)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print(7)
     
    RR_GRAMMAR4 = {
        '<start>': [['<A>', 'c']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring4 = 'ababababc'
     
    res = compile_grammar(RR_GRAMMAR4, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring4)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print(8)
     
    RR_GRAMMAR5 = {
    '<start>': [['<A>']],
    '<A>': [['a', 'b', '<B>'], []],
    '<B>': [['<A>']],
    }
    mystring5 = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR5, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring5)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print(9)
     
    RR_GRAMMAR6 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<B>'], []],
    '<B>': [['b', '<A>']],
    }
    mystring6 = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR6, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring6)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print(10)

    RR_GRAMMAR7 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']],
    }
    mystring7 = 'aaaaaaaa'

    res = compile_grammar(RR_GRAMMAR7, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring7)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print(11)

    RR_GRAMMAR8 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']]
    }
    mystring8 = 'aa'

    res = compile_grammar(RR_GRAMMAR8, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring8)
    assert parse_string(g) == 'success'
    print(12)


    X_G1 = {
        '<start>': [['a']],
    }
    mystring2 = 'a'
    res = compile_grammar(X_G1, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print('X_G1')

    X_G2 = {
        '<start>': [['a', 'b']],
    }
    mystring2 = 'ab'
    res = compile_grammar(X_G2, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print('X_G2')

    X_G3 = {
        '<start>': [['a', '<b>']],
        '<b>': [['b']]
    }
    mystring2 = 'ab'
    res = compile_grammar(X_G3, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
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
    mystring2 = 'ab'
    res = compile_grammar(X_G4, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print('X_G4')

    X_G5 = {
        '<start>': [['<expr>']],
        '<expr>': [
            ['<expr>', '+', '<expr>'],
            ['1']]
    }
    X_G5_start = '<start>'

    mystring2 = '1+1'
    res = compile_grammar(X_G5, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
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

    mystring2 = 'bac'
    res = compile_grammar(X_G6, '<S>')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    v = process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)
    print(v)
    fuzzer.display_tree(v)

    print('X_G6')

