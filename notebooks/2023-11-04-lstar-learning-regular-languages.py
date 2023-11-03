# ---
# published: true
# title: Learning Regular Languages with Angluins L* Algorithm
# layout: post
# comments: true
# tags: regular-grammars induction
# categories: post
# ---
#  
# In many previous posts, I have discussed how to [parse with](/post/2023/11/03/matching-regular-expressions/),
# [fuzz with](/post/2021/10/22/fuzzing-with-regular-expressions/), and
# manipulate regular and context-free grammars. However, in many cases, such
# grammars may be unavailable. If you are given a blackbox program, where the
# program indicates in some way that the input was accepted or not, what can
# we do to learn the actual input specification of the blackbox?
# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.
# 
#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/ py/rgtorx-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities

import simplefuzzer as fuzzer
import rxfuzzer
import rgtorx

# We start with a few definitions
# 
# ## Definitions
# 
# * A symbol X 
# 

class StateTable:
    def __init__(self, alphabet, oracle):
        self._T, self.S, self.E = {}, [''], ['']
        self.oracle = oracle
        self.A = alphabet

    def init_table(self):
        self._T[''] = {'': self.oracle.is_member('') }
        self.extend()

    # An observation table (S, E) is closed if for each t in S·A
    # there exists an s in S such that row(t) = row(s)
    def closed(self):
        S_A = [s+a for s in self.S for a in self.A]
        for t in S_A:
            res = [s for s in self.S if self.row(t) == self.row(s)]
            if not res: return False, t
        return True, None

    def append_S(self, s):
        self.S.append(s)
        self.extend()

    # An observation table (S, E) is consistent if, whenever s1 and s2
    # are elements of S such that row(s1) = row(s2), for each a in A,
    # row(s1a) = row(s2a). 
    # /If/ there are two rows in the top part of the table repeated, then the
    # corresponding extensions should be the same.
    def consistent(self):
        for s1,s2 in [(s1,s2) for s1 in self.S for s2 in self.S if s1 != s2]:
            if self.row(s1) != self.row(s2): continue
            for a in self.A:
                for e in self.E:
                    if self.cell(s1+a,e) != self.cell(s2+a,e):
                        return False, (a + e)
                #assert False
        return True, None

    def append_AE(self, ae):
        self.E.append(ae)
        self.extend()

    def row(self, v): return self._T[v]

    def cell(self, v, e): return self._T[v][e]

    def extend(self):
        # extend T to (S u S.A).E using membership queries
        SuS_A = self.S + [s + a for s in self.S for a in self.A]
        SuS_A_E = [(s,e) for s in SuS_A for e in self.E]
        for s,e in SuS_A_E:
            if s in self._T and e in self._T[s]: continue
            if s not in self._T: self._T[s] = {}
            self._T[s][e] = self.oracle.is_member(s + e)

    def get_sid(self, s):
        row = self.row(s)
        return ''.join([str(row[e]) for e in self.E])

    def dfa(self):
        row_map = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for s in self.S:
            sid = self.get_sid(s)
            if sid not in states:
                states[sid] = [s]
            else:
                states[sid].append(s)
            row_map[s] = sid

        for sid in states: grammar['<%s>' % sid] = []

        # Step 2: Identify the start state, which corresponds to epsilon row
        start_state = row_map['']
        start_nt = '<%s>' % start_state
        grammar[start_nt] = []

        # Step 3: Identify the accepting states
        accepting = [row_map[s] for s in self.S if self.row(s)[''] == 1]
        if not accepting: return None, None
        for s in accepting:
            grammar['<%s>' % s] = [['<_>']]
        grammar['<_>'] = [[]]

        # Step 4: Create the transition function

        for sid1 in states:
            first_such_row = states[sid1][0]
            for a in self.A:
                sid2 = self.get_sid(first_such_row + a)
                grammar['<%s>' % sid1].append([a, '<%s>' % sid2])

        return grammar, start_nt

# FOR DFA
# Q = {row(s) : s \in S}             --- states
# q0 = row(e)                        -- start
# F = {row(s) : s \in S, T(s) = 1}   -- accepting state
# \delta(row(s), a) = row(s.a)      ---- Transition function

def prefixes(s):
    pref = []
    st = ''
    for e in s:
        st += e
        pref.append(st)
    return pref

def l_star(T):
    T.init_table()

    while True:
        while True:
            is_closed, counter_E = T.closed()
            is_consistent, counter_A = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.append_S(counter_E)
            if not is_consistent: T.append_AE(counter_A)

        g, s = T.dfa()
        res, counterX = oracle.is_equivalent(g, s)
        if res: return T
        for s in prefixes(counterX): T.append_S(s)

import re
import random
import hashlib
random.seed(0)

class Oracle:
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == ('^', '$'):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)
        self.rgf = fuzzer.LimitFuzzer(self.g)
        #self.cache = {'496d46f8': (False, 'aa'), 'daea2ea3': (False, 'bb')}

    def dfa_to_str(self, q):
        s = hashlib.shake_128(bytes(str(q), 'utf-8')).hexdigest(4)
        return s


    def generate(self, g, start):
        rgf = fuzzer.LimitFuzzer(g)
        v = rgf.fuzz(start)
        return v

    def is_member(self, q):
        if re.search(self.rex, q) is not None:
            return 1 # True
        return 0 # False

    def is_equivalent(self, grammar, start):
        if grammar is None:
            return False, self.generate(self.g, self.s)
        rex = rgtorx.rg_to_regex(grammar, start)
        #if v in self.cache: return self.cache[v]
        while True:
            k = self.generate(grammar, start)
            if not self.is_member(k):
                return False, k
        return True, None

class OracleFn(Oracle):
    def is_equivalent(self, grammar, start):
        if str(grammar) == "{'<1>': [['<_>'], ['a', '<0>'], ['b', '<0>']], '<0>': [['a', '<1>'], ['b', '<0>']], '<_>': [[]]}":
            return False, 'bb'
        if str(grammar) == "{'<10>': [['<_>'], ['a', '<01>'], ['b', '<00>']], '<01>': [['a', '<10>'], ['b', '<00>']], '<00>': [['a', '<00>'], ['b', '<10>']], '<_>': [[]]}":
            return False, 'abb'
        i = 0
        while i < 1000:
            i+= 1
            v = self.generate(grammar, start)
            if not self.is_member(v):
                print(v)
                assert False
        return True, None

    def is_member(self, q):
        as_ = sum([1 for i in q if i == 'a'])
        bs_ = sum([1 for i in q if i == 'b'])
        v = (as_ % 2) == 0 and (bs_ % 2) == 0
        if v: return 1
        return 0

oracle = OracleFn('^(aa|bb)$')
g_T = StateTable(['a', 'b'], oracle)
l_star(g_T)
print(g_T.dfa())

# num of calls made in place of ith oracle query qi = [1/epsilon * (ln(1/delta) + i * ln 2)]


# A problem with this algorithm is its exponential case behavior as Moore [^2]
# notes. The solution that Moore offers is to order the nonterminals in the
# decreasing order of the number of distinct left corners.
#  
# 
# [^1]: Marvin C. Paull, Algorithm design: a recursion transformation framework, 1988
# [^2]: Robert C Moore, Removing Left Recursion from Context-Free Grammars [*](https://www.microsoft.com/en-us/research/wp-content/uploads/2000/04/naacl2k-proc-rev.pdf)., 2000
