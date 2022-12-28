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

# #### Prerequisites
#
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

import simplefuzzer as fuzzer

# ## Our grammar

G = {
  '<S>': [
       ['<A>', '<S>', 'd'],
       ['<B>', '<S>'],
       ['g', 'p', '<C>'],
       []],
  '<A>': [['a'], ['c']],
  '<B>': [['a'], ['b']],
  '<C>': ['c']
}
start = '<S>'

# ## GLL with Separate Stacks
# 
# ### The GLL Stack

class GLLStack:
    def __init__(self, s):
        self.threads = []
        self.I = s + '$'

    def add_thread(self, L, u, j):
        self.threads.append((L, u, j))

    def next_thread(self):
        (L, sval, i), *self.threads = self.threads
        return (L, sval, i)

    def fn_return(self, s, i):
        s, (L, i_) = s
        self.add_thread(L, s, i)
        return s

    def register_return(self, L, s, i):
        return (tuple(s), (L, i))

# ### The Stack GLL Compiler

def tuple_to_str(g, sym, n_alt, pos):
    rule = g[sym][n_alt]
    return sym + '::=' + ' '.join(rule[0:pos]) + ' * ' + ' '.join(rule[pos:])

# #### (1) Compiling an empty rule
def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon -- we skip the end and go directly to L_
            L = 'L_'
            continue
''' % (key, n_alt, tuple_to_str(g, key, n_alt, 0))

# #### (1) Compiling a Terminal Symbol
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s", %d, %d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s", %d, %d): # %s
            if parser.I[i] == '%s':
                i = i+1
                L = %s
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, tuple_to_str(g, key, n_alt, r_pos), token, Lnxt)

# #### (1) Compiling a Nonterminal Symbol
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s", %d, %d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ("%s", %d, %d): # %s
            sval = parser.register_return(%s, sval, i)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, tuple_to_str(g, key, n_alt, r_pos), Lnxt, token)

# #### (1) Compiling a Rule
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
        elif L == ("%s", %d, %d): # %s
            L = 'L_'
            continue
''' % (key, n_alt, len(rule), tuple_to_str(g, key, n_alt, len(rule))))
    return '\n'.join(res)

# #### (1) Compiling a Definition
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # %s
            parser.add_thread( ("%s",%d, 0), sval, i)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

# #### (1) Compiling a Grammar
def compile_grammar(g, start):
    res = ['''\
def parse_string(parser):
    L, sval, i = '%s', parser.register_return('L0', [], 0), 0
    while True:
        if L == 'L0':
            if parser.threads:
                (L, sval, i) = parser.next_thread()
                if ('L0', (), len(parser.I)-1) == (L, sval, i): return 'success'
                else: continue
            else: return 'error'
        elif L == 'L_':
            sval = parser.fn_return(sval, i)
            L = 'L0'
            continue
    ''' % start]
    for k in g: 
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''\
        else:
            assert False
''')
    return '\n'.join(res)

# #### Example

if __name__ == '__main__':
    res = compile_grammar(G, start)
    print(res)
    exec(res)

# ### Usage
if __name__ == '__main__':
    import sys
    gf = fuzzer.LimitFuzzer(G)
    for i in range(10):
        print('stack:.')
        s = gf.iter_fuzz(key=start, max_depth=5)
        print(s)
        g = GLLStack(s)
        assert parse_string(g) == 'success'
        print('parsed.')

# ## GLL with a Graph Structured Stack (GSS)

# ### The GSS Node
# Each GSS Node is of the form $L_i^j$ where `j` is the index of the character
# consumed.

class Node:
    def __init__(self, L, j):
        self.L, self.i, self.children = L, j, []
        self.label = (self.L, self.i)

    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

# ### The GSS container

class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, L, i):
        my_label = (L, i)
        if my_label not in self.gss:
            self.gss[my_label] = Node(L, i)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        # indexes for which pop has been executed for label.
        return self.P[label]

    def __repr__(self): return str(self.gss)

# ### The GLL GSS

class GLLStructuredStack:
    def register_return(self, L, u, j): # create
        v = self.gss.get(L, j) # Let v be the GSS node labeled L^j
        # If there is not an edge from v to u
        v_to_u = [c for c in v.children if c.label == u.label]
        if u not in v_to_u:
            v.children.append(u)
            # paper p183: When a new child node u is added to v,
            # for all (v, k) in P if (Lv, u) notin Uk then
            # (Lv,v,k) is added to R, where Lv is the label of v.
            # **Note:** The above is confusing because according to it, what
            # we should add is (v.L, v, k) while what we are adding below from
            # the same paper, p184 `create(L, u, j)` is `add(v.L, u, j)`
            # but in 183 again, it is said: The function create(L, u, j) creates
            # a GSS node v = Lj with child u if one does not already exist, and
            # then returns v. If (v, k) in P then add(L, u, k) is called.
            for k in self.gss.parsed_indexes(v.label):
                self.add_thread(v.L, u, k) # v.L == L
        return v

    def add_thread(self, L, u, j): # add
        if (L, u) not in self.U[j]:
            self.U[j].append((L, u))
            self.threads.append((L, u, j))

    def next_thread(self):
        (L, sval, i), *self.threads = self.threads
        return (L, sval, i)

    # paper: actions POP(s, i, R) are replaced by actions which add (L, v, i) to
    # R for all children v of node corresponding to the top of s.
    # 
    # **Note.** Because this is a GSS, we might already know the children of u
    # which is the node corresponding to top of s. Hence, we can start these
    # threads. However, what if new children are added? This is addressed by
    # maintaining P which maintains (u, k) for which pop has been executed.
    # See register_return
    def fn_return(self, u, j): # pop
        if u != self.u0:
            self.gss.add_parsed_index(u.label, j)
            for v in u.children:
                self.add_thread(u.L, v, j)
        return u


    def __init__(self, input_str):
        self.threads = []
        self.gss = GSS()
        self.I = input_str
        self.m = len(self.I) # |I| + 1
        self.u1 = self.gss.get('L0', 0)
        self.u0 = self.gss.get('$', self.m)
        self.u1.children.append(self.u0)

        self.U = []
        for j in range(self.m): # 0<=j<=m
            self.U.append([]) # U_j = empty

# ### The GSS GLL Compiler
# The only difference in the main body when using the GSS is how we check
# for termination.

# #### (2) Compiling a Grammar
def compile_grammar(g, start):
    res = ['''\
def parse_string(parser):
    L, sval, i = '%s', parser.u1, 0
    while True:
        if L == 'L0':
            if parser.threads:
                (L, sval, i) = parser.next_thread()
                continue
            else:
                if ('L0', parser.u0) in parser.U[parser.m-1]: return 'success'
                else: return 'error'
        elif L == 'L_':
            sval = parser.fn_return(sval, i)
            L = 'L0'
            continue
    ''' % start]
    for k in g: 
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    return '\n'.join(res)

# #### Example

if __name__ == '__main__':
    res = compile_grammar(G, start)
    print(res)
    exec(res)

# ### Usage
if __name__ == '__main__':
    g = GLLStructuredStack('agpcd$')
    assert parse_string(g) == 'success'
    for k in (g.gss.gss):
        print(k)
        print("   ", g.gss.gss[k])

    gf = fuzzer.LimitFuzzer(G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=start, max_depth=10)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar
if __name__ == '__main__':
    E_G = {
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
    E_start = '<start>'

    res = compile_grammar(E_G, E_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E_G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=E_start, max_depth=10)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar
if __name__ == '__main__':
    E2_G = {
        '<start>': [['<expr>']],
        '<expr>': [
            ['<expr>', '+', '<term>'],
            ['<expr>', '-', '<term>'],
            ['<term>']],
        '<term>': [
            ['<term>', '*', '<fact>'],
            ['<term>', '/', '<fact>'],
            ['<fact>']],
        '<fact>': [
            ['<digits>'],
            ['(','<expr>',')']],
        '<digits>': [
            ['<digit>','<digits>'],
            ['<digit>']],
        '<digit>': [["%s" % str(i)] for i in range(10)],
    }
    E2_start = '<start>'
    res = compile_grammar(E2_G, E2_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E2_G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=E2_start, max_depth=10)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar
if __name__ == '__main__':
    E3_G = {
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
    E3_start = '<start>'
    res = compile_grammar(E3_G, E3_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E3_G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=E3_start, max_depth=5)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar
if __name__ == '__main__':
    E4_G = {
        '<start>': [['<A>', '<B>']],
        '<A>': [['a'], [], ['<C>']],
        '<B>': [['b']],
        '<C>': [['<A>'], ['<B>']]
    }
    E4_start = '<start>'
    res = compile_grammar(E4_G, E4_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E4_G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=E4_start, max_depth=5)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar

if __name__ == '__main__':
    RR_GRAMMAR2 = {
        '<start>': [['<A>']],
        '<A>': [['a','b', '<A>'], []],
    }
    mystring2 = 'ababababab'
    res = compile_grammar(RR_GRAMMAR2, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring2+'$')
    assert parse_string(g) == 'success'
     
    RR_GRAMMAR3 = {
        '<start>': [['c', '<A>']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring3 = 'cababababab'
     
    res = compile_grammar(RR_GRAMMAR3, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring3+'$')
    assert parse_string(g) == 'success'
     
    RR_GRAMMAR4 = {
        '<start>': [['<A>', 'c']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring4 = 'ababababc'
     
    res = compile_grammar(RR_GRAMMAR4, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring4+'$')
    assert parse_string(g) == 'success'
     
    RR_GRAMMAR5 = {
    '<start>': [['<A>']],
    '<A>': [['a', 'b', '<B>'], []],
    '<B>': [['<A>']],
    }
    mystring5 = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR5, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring5+'$')
    assert parse_string(g) == 'success'
     
    RR_GRAMMAR6 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<B>'], []],
    '<B>': [['b', '<A>']],
    }
    mystring6 = 'abababab'
     
    res = compile_grammar(RR_GRAMMAR6, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring6+'$')
    assert parse_string(g) == 'success'

    RR_GRAMMAR7 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']],
    }
    mystring7 = 'aaaaaaaa'

    res = compile_grammar(RR_GRAMMAR7, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring7+'$')
    assert parse_string(g) == 'success'

    RR_GRAMMAR8 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']]
    }
    mystring8 = 'aa'

    res = compile_grammar(RR_GRAMMAR8, '<start>')
    exec(res)
    g = GLLStructuredStack(mystring8+'$')
    assert parse_string(g) == 'success'



# # from GLL parse-tree generation Scott, Johnstone 2013
# # SPPF Hookup

class SPPF_node:
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

class SPPF_dummy(SPPF_node):
    def __init__(self, s='$'):
        self.label = (s, 0, 0)
        self.children = []

class SPPF_symbol_node(SPPF_node):
    def __init__(self, x, j, i):
        # x is a terminal, nonterminal, or epsilon -- ''
        # j and i are the extents
        #assert 0<= j <= i <= m
        self.label = (x, j, i)
        self.children = []

    def to_s(self, g):
        return (self.label)

class SPPF_intermediate_node(SPPF_node):
    def __init__(self, t, j, i):
        self.label = (t, j, i)
        self.children = []

    def right_extent(self):
        return self.label[-1]

    def to_s(self, g):
        if isinstance(self.label[0], str):
            return str(self.label)
        ((sym, n_alt, dot), i, j)  = self.label
        return ( sym + ' ::= ' +
                str(g.grammar[sym][n_alt][:dot]) + '.' +
                str(g.grammar[sym][n_alt][dot:]) + ' ' + str(i) + ',' + str(j))


class SPPF_packed_node(SPPF_node):
    def __init__(self, t, k, children):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = children # left and right or just left

    def to_s(self, g):
        (sym, n_alt, dot), lat = self.label
        return ( sym + ' ::= ' +
                str(g.grammar[sym][n_alt][:dot]) + '.' +
                str(g.grammar[sym][n_alt][dot:]) + ' ' + str(lat) )

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

class GLLStructuredStackP:
    def set_grammar(self, g):
        self.grammar = g
        self.nullable = nullable(g)

    # add: if ((L, u, w) not in U_i { add (L, u, w) to U_i, add (L, u, i, w) to R } }
    def add_thread(self, L, u, i, w): # add +
        # w needs to be an SPPF node.
        assert not isinstance(u, int)
        assert isinstance(w, SPPF_node)
        if (L, u, w) not in self.U[i]:
            self.U[i].append((L, u, w))
            self.threads.append((L, u, i, w))

    def fn_return(self, u, i, z): # pop +
        # z needs to be SPPF.
        assert isinstance(z, SPPF_node)
        if u != self.u0:
            # let (L, k) be label of u
            (L, k) = u.label
            self.gss.add_parsed_index(u.label, z)
            for v,w in u.children: # edge labeled w, an SPPF node.
                assert isinstance(w, SPPF_node)
                #assert w.label[2] == z.label[1]
                y = self.getNodeP(L, w, z)
                self.add_thread(L, v, i, y)
        return u

    def register_return(self, L, u, i, w): # create (returns to c_u) +
        assert isinstance(w, SPPF_node)
        v = self.gss.get(L, i) # Let v be the GSS node labeled L^i
        # all gss children are edges, and they are labeled with SPPF nodes.
        # if there is not an edge from v to u labelled w
        #assert not v.children # test. why are there no children?
        v_to_u_labeled_w = [c for c,lbl in v.children if c.label == u.label and lbl == w]
        if not v_to_u_labeled_w:
            # create an edge from v to u labelled w
            v.children.append((u,w))

            #sppf_node = (v,z)
            for z in self.gss.parsed_indexes(v.label):
                assert isinstance(z, SPPF_intermediate_node)
                #assert w.label[2] == z.label[1]
                y = self.getNodeP(L, w, z)
                h = z.right_extent()
                self.add_thread(v.L, u, h, y) # v.L == L
        return v

    def next_thread(self): # i \in R
        (L, sval, i, w), *self.threads = self.threads
        return (L, sval, i, w)

    def __init__(self, input_str):
        self.I = input_str + '$' # read the input I and set I[m] = `$`
        self.m = len(input_str)
        # create GSS node u_0 = (L_0, 0)
        self.gss = GSS()
        self.u0 = self.gss.get('L0', 0)
        #self.u0 = self.gss.get('$', self.m) <- not present in this.
        #self.u1.children.append(self.u0) <- not present in this.

        # c_I = 0, c_u := u_0 are done in compile

        # R := \empty
        self.threads = [] # R

        self.U = []
        for j in range(self.m+1): # 0<=j<=m
            self.U.append([]) # U_j = empty

        self.SPPF_nodes = {}

    def get_sppf_symbol_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_symbol_node(*n)
        return self.SPPF_nodes[n] 

    def get_sppf_intermediate_node(self, n):
        if n not in self.SPPF_nodes:
            self.SPPF_nodes[n] = SPPF_intermediate_node(*n)
        return self.SPPF_nodes[n] 

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
            # if beta != []: # from Exploring_and_Visualizing
            #     t = X
            # else:
            #     t = X_rule_pos
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
                if beta == []:
                    y = self.get_sppf_symbol_node((t, j, i))
                else:
                    y = self.get_sppf_intermediate_node((t, j, i))

                if not [c for c in y.children if c.label == (X_rule_pos, k)]:
                    # create a child of y with left child with w right child z
                    # the extent of w-z is the same as y
                    # packed nodes do not keep extents
                    pn = SPPF_packed_node(X_rule_pos, k, [w,z])
                    y.add_child(pn)
            else:
                # if there does not exist an SPPF node y labelled (t, k, i) create one
                # returns (t,k,i) <- (X:= alpha.beta, k) <- (r,k,i)
                y = self.get_sppf_intermediate_node((t, k, i))
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

# #### (3) Compiling an empty rule (P)
def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            c_r = parser.getNodeT(None, c_i)
            c_n = parser.getNodeP(L, c_n, c_r)
            L = 'L_'
            continue
''' % (key, n_alt,tuple_to_str(g, key, n_alt, 0))

# #### (3) Compiling a Terminal Symbol
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[c_i] == '%s':
                c_r = parser.getNodeT(parser.I[c_i], c_i)
                c_i = c_i+1
                L = %s
                c_n = parser.getNodeP(L, c_n, c_r)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, tuple_to_str(g, key, n_alt, r_pos), token, Lnxt)

# #### (3) Compiling a Nonterminal Symbol
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            c_u = parser.register_return(%s, c_u, c_i, c_n)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, tuple_to_str(g, key, n_alt, r_pos), Lnxt, token)

# #### (3) Compiling a Rule
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
''' % (key, n_alt, len(rule), tuple_to_str(g, key, n_alt, len(rule))))
    return '\n'.join(res)

# #### (3) Compiling a Definition
def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # need to check first() if performance is important.
            # %s
            parser.add_thread( ('%s',%d,0), c_u, c_i, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)


# #### (3) Compiling a Grammar

def compile_grammar(g, start):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = ['''\
# u_0 = (L_0, 0) # -- GSS base node+
# c_i = 0        # current input index+
# c_U = u_0      # current GSS node+
# c_N = \delta   # current SPPF Node
# U = \empty     # descriptor set+
# R = \empty     # descriptors still to be processed+
# P = \empty     # poped nodes set.
def parse_string(parser):
    parser.set_grammar(
%s
    )
    # L contains start nt.
    S = '%s'
    end_rule = SPPF_dummy('$')
    L, c_u, c_i, c_n = S, parser.u0, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, c_u, c_i, c_n) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (S, 0, parser.m)
                      return 'success'
                else: return 'error'
        elif L == 'L_':
            c_u = parser.fn_return(c_u, c_i, c_n) # pop
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

# Another grammar
import shutil

def write_res(res, mystring):
    with open('a.py', 'w+') as f:
        f.write('from x import GLLStructuredStackP, SPPF_dummy, SPPF_intermediate_node, SPPF_symbol_node, SPPF_packed_node \n')
        f.write('''
import random

def process_sppf_symbol(node, hmap, tab):
    assert isinstance(node, SPPF_symbol_node)
    print(' ' * tab, 'S', node.to_s(g))
    for n in node.children:
        process_sppf_packed(n,hmap, tab+1)

def process_sppf_packed(node, hmap, tab):
    assert isinstance(node, SPPF_packed_node)
    print(' ' * tab, 'P', node.to_s(g))
    for n in node.children:
        if isinstance(n, SPPF_symbol_node):
            process_sppf_symbol(n,hmap, tab+1)
        elif isinstance(n, SPPF_intermediate_node):
            process_sppf_intermediate_node(n,hmap, tab+1)
        else: assert False

def process_sppf_intermediate_node(node, hmap, tab):
    assert isinstance(node, SPPF_intermediate_node)
    print(' '*tab, 'I', node.to_s(g))
    #assert len(node.children) == 1
    #n = random.choice(node.children)
    for n in node.children:
        process_sppf_packed(n,hmap, tab+1)

''')
        f.write(res)
        f.write('\n')
        f.write('mystring = "%s"\n' % mystring)
        f.write('g = GLLStructuredStackP(mystring)\n')
        f.write('print(parse_string(g))\n')
        f.write('process_sppf_symbol(g.SPPF_nodes[g.root], g.SPPF_nodes, tab=0)\n')
    shutil.copyfile(sys.argv[0], 'x.py')

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

    RR_GRAMMAR2 = {
        '<start>': [['<A>']],
        '<A>': [['a','b', '<A>'], []],
    }
    mystring2 = 'ababababab'
    res = compile_grammar(RR_GRAMMAR2, '<start>')
    #write_res(res, mystring2)
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print(6)

    RR_GRAMMAR3 = {
        '<start>': [['c', '<A>']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring3 = 'cababababab'
     
    res = compile_grammar(RR_GRAMMAR3, '<start>')
    exec(res)
    g = GLLStructuredStackP(mystring3)
    assert parse_string(g) == 'success'
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


    res = compile_grammar(E_G, E_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E_G)
    for i in range(10):
        print('sppf:.')
        s = gf.iter_fuzz(key=E_start, max_depth=10)
        print(s)
        g = GLLStructuredStackP(s)
        assert parse_string(g) == 'success'
        print('sppf parsed.')

    res = compile_grammar(E2_G, E2_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E2_G)
    for i in range(10):
        print('sppf:.')
        s = gf.iter_fuzz(key=E2_start, max_depth=10)
        print(s)
        g = GLLStructuredStackP(s)
        assert parse_string(g) == 'success'
        print('sppf parsed.')

    res = compile_grammar(E3_G, E3_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E3_G)
    for i in range(10):
        print('sppf:.')
        s = gf.iter_fuzz(key=E3_start, max_depth=5)
        print(s)
        g = GLLStructuredStackP(s)
        assert parse_string(g) == 'success'
        print('sppf parsed.')

    res = compile_grammar(E4_G, E4_start)
    exec(res)
    gf = fuzzer.LimitFuzzer(E4_G)
    for i in range(10):
        print('sppf:.')
        s = gf.iter_fuzz(key=E4_start, max_depth=5)
        print(s)
        g = GLLStructuredStackP(s)
        assert parse_string(g) == 'success'
        print('sppf parsed.')

    X_G1 = {
        '<start>': [['a']],
    }
    mystring2 = 'a'
    res = compile_grammar(X_G1, '<start>')
    write_res(res, mystring2)
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print('X_G1')

    X_G2 = {
        '<start>': [['a', 'b']],
    }
    mystring2 = 'ab'
    res = compile_grammar(X_G2, '<start>')
    write_res(res, mystring2)
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
    write_res(res, mystring2)
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
    write_res(res, mystring2)
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
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
    write_res(res, mystring2)
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
    write_res(res, mystring2)
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'
    print('X_G6')

