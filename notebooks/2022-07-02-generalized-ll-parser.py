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
            # then returns v. If(v, k) in P then add(L, u, k) is called.
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
    gf = fuzzer.LimitFuzzer(G)
    for i in range(10):
        print('gss:.')
        s = gf.iter_fuzz(key=start, max_depth=10)
        print(s)
        g = GLLStructuredStack(s+'$')
        assert parse_string(g) == 'success'
        print('gss parsed.')

# Another grammar

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

# ### Usage
if __name__ == '__main__':
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


