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
# simply providing the source until I have more bandwidth to complete the
# tutorial.

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
        self.I = s

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

# #### Compiling a Terminal Symbol
def compile_terminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = '%s[%d]_%d' % (key, n_alt, r_pos+1)
    return '''\
        elif L == '%s[%d]_%d':
            if parser.I[i] == '%s':
                i = i+1
                L = '%s'
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, token, Lnxt)

# #### Compiling a Nonterminal Symbol
def compile_nonterminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = '%s[%d]_%d' % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  '%s[%d]_%d':
            sval = parser.register_return('%s', sval, i)
            L = '%s'
            continue
''' % (key, n_alt, r_pos, Lnxt, token)

# #### Compiling a Rule
def compile_rule(key, n_alt, rule):
    res = []
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            r = compile_nonterminal(key, n_alt, i, len(rule), t)
        else:
            r = compile_terminal(key, n_alt, i, len(rule), t)
        res.append(r)

    res.append('''\
        elif L == '%s[%d]_%d':
            L = 'L_'
            continue
''' % (key, n_alt, len(rule)))
    return '\n'.join(res)

# #### Compiling a Definition
def compile_def(key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            parser.add_thread( '%s[%d]_0', sval, i)''' % (key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

# #### Compiling a Grammar
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
        r = compile_def(k, g[k])
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
        g = GLLStack(s+'$')
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
        if u not in v.children:
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
        r = compile_def(k, g[k])
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
        pass

class SPPF_delta_node(SPPF_node):
    def __init__(self):
        self.label = ('$', 0, 0)
        self.children = []

class SPPF_symbol_node(SPPF_node):
    def __init__(self, x, j, i):
        # x is a terminal, nonterminal, or epsilon -- ''
        # j and i are the extents
        #assert 0<= j <= i <= m
        self.label = (x, j, i)
        self.children = []

class SPPF_intermediate_node(SPPF_node):
    def __init__(self, t, j, i):
        self.label = (t, j, i)
        self.children = []

class SPPF_packed_node(SPPF_node):
    def __init__(self, t, k):
        # k is the pivot of the packed node.
        self.label = (t,k) # t is a grammar slot X := alpha dot beta
        self.children = []


class GLLStructuredStackP:
    def add_thread(self, L, u, i, w): # add +
        if (L, u, w) not in self.U[i]:
            self.U[i].append((L, u, w))
            self.threads.append((L, u, i, w))

    def fn_return(self, u, i, z): # pop +
        if u != self.u0:
            # let (L, k) be label of u
            (L, k) = u.label
            self.gss.add_parsed_index(u.label, z)
            for n in u.children:
                (u_, w, v) = n.label
                y = self.getNodeP(L, w, z)
                self.add_thread(L, v, i, y)
        return u

    def register_return(self, L, u, i, w): # create (returns to c_u) +
        v = self.gss.get(L, i) # Let v be the GSS node labeled L^i
        if w not in v.children:
            v.children.append(w)
            for (v,z) in self.gss.parsed_indexes(v.label):
                y = self.getNodeP(L, w, z)
                h = right_extent(z)
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
        self.epsilon = ''
        #self.u0 = self.gss.get('$', self.m) <- not present in this.
        #self.u1.children.append(self.u0) <- not present in this.

        # c_I = 0, c_u := u_0 are done in compile

        # R := \empty
        self.threads = [] # R

        self.U = []
        for j in range(self.m+1): # 0<=j<=m
            self.U.append([]) # U_j = empty

        self.SPPF_nodes = {}

# # SPPF Build
    def getNodeT(self, x, i):
        if x is self.epsilon: h = i
        else: h = i+1
        if (x,i,h) not in self.SPPF_nodes:
            self.SPPF_nodes[(x, i, h)] = SPPF_symbol_node(x, i, h)
        return self.SPPF_nodes[(x, i, h)]

    def getNodeP(self, X_eq_alpha_dot_beta, w, z):
        X, alpha, beta = X_eq_alpha_dot_beta
        if self.is_non_nullable(X, alpha, beta) and beta != self.epsilon:
            return z
        else:
            if beta == self.epsilon:
                t = X
            else:
                t = X_eq_alpha_dot_beta
            z = (q,k,i).label
            if (w != '$'):
                w = (s,j,k).label
                if not [node for node in self.SPPF_nodes if node.label == (t, j, i)]:
                    self.SPPF_nodes[(t, j, i)] = SPPF_intermediate_node(t, j, i)
                if not [c for c in y.children if c.label == (X_eq_alpha_dot_beta, k)]:
                    y.add_child((w, z)) # create a child of y with left child with w right child z
            else:
                if (t, k, i) not in SPFF_nodes:
                    self.SPPF_nodes[(t, k, i)] = SPPF_intermediate_node(t, k, i)
                if not [c for c in y.children if c.label == (X_eq_alpha_dot_beta, k)]:
                    y.add_child(z) # create a child with child z
            return y

    def is_non_nullable(self, X, v, beta):
        # TODO
        #k = self.grammar[X][alpha][beta]
        return True


# #### Compiling a Terminal Symbol
def compile_terminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d):
            if parser.I[c_i] == '%s':
                c_r = parser.getNodeT(parser.I[c_i], c_i)
                c_i = c_i+1
                L = %s
                c_n = parser.getNodeP(L, c_n, c_r)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, token, Lnxt)

# #### Compiling a Nonterminal Symbol
def compile_nonterminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d):
            c_u = parser.register_return(%s, c_u, c_i, c_n)
            L = '%s'
            continue
''' % (key, n_alt, r_pos, Lnxt, token)

# #### Compiling a Rule
def compile_rule(key, n_alt, rule):
    res = []
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            r = compile_nonterminal(key, n_alt, i, len(rule), t)
        else:
            r = compile_terminal(key, n_alt, i, len(rule), t)
        res.append(r)

    res.append('''\
        elif L == ('%s',%d,%d):
            L = 'L_'
            continue
''' % (key, n_alt, len(rule)))
    return '\n'.join(res)

# #### Compiling a Definition
def compile_def(key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            parser.add_thread( ('%s',%d,0), c_u, c_i, c_n)''' % (key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

def compile_grammar(g, start):
    res = ['''\
# u_0 = (L_0, 0) # -- GSS base node+
# c_i = 0        # current input index+
# c_U = u_0      # current GSS node+
# c_N = \delta   # current SPPF Node
# U = \empty     # descriptor set+
# R = \empty     # descriptors still to be processed+
# P = \empty     # poped nodes set.
def parse_string(parser):
    # L contains start nt.
    S = '%s'
    L, c_u, c_i, c_n = S, parser.u0, 0, SPPF_delta_node()
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, c_u, c_i, c_n) = parser.next_thread() # remove from R
                # goto L
                continue
            else:
                # if there is an SPPF node (S, 0, m) then report success
                if (S, parser.u0, parser.m) in parser.SPPF_nodes: return 'success'
                else: return 'error'
        elif L == 'L_':
            c_u = parser.fn_return(c_u, c_i, c_n) # pop
            L = 'L0' # goto L_0
            continue
    ''' % start]
    for k in g: 
        r = compile_def(k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    return '\n'.join(res)

# Another grammar

if __name__ == '__main__':
    RR_GRAMMAR2 = {
        '<start>': [['<A>']],
        '<A>': [['a','b', '<A>'], []],
    }
    mystring2 = 'ababababab'
    res = compile_grammar(RR_GRAMMAR2, '<start>')
    with open('a.py', 'w+') as f:
        f.write('from x import GLLStructuredStackP, SPPF_delta_node\n')
        f.write(res)
        f.write('\n')
        f.write('mystring = "%s"\n' % mystring2)
        f.write('g = GLLStructuredStackP(mystring)\n')
        f.write('parse_string(g)\n')
    exec(res)
    g = GLLStructuredStackP(mystring2)
    assert parse_string(g) == 'success'

