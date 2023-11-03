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
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities

import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser

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
        if not accepting: return {'<start>': []}, '<start>'
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
import math
random.seed(0)

# Next, we need to consider our oracle. It serves both as the
# blackbox to learn from and also as the teacher.
class Oracle:
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == ('^', '$'):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)
        self.rgf = fuzzer.LimitFuzzer(self.g)
        self.counter = 0
        # epsilon is the accuracy and delta is the confidence
        self.delta, self.epsilon = 0.1, 0.1

    def dfa_to_str(self, q):
        s = hashlib.shake_128(bytes(str(q), 'utf-8')).hexdigest(4)
        return s


    def generate(self):
        return self.rgf.fuzz(self.s)

    def is_member(self, q):
        if re.search(self.rex, q) is not None:
            return 1 # True
        return 0 # False

    def is_equivalent(self, grammar, start):
        self.counter += 1
        if not grammar[start]: return False, self.generate()
        num_calls = math.ceil(1.0/self.epsilon * (math.log(1.0/self.delta) + self.counter * math.log(2)))

        rgf = fuzzer.LimitFuzzer(grammar)
        ep = earleyparser.EarleyParser(grammar)
        for i in range(num_calls):
            k = rgf.fuzz(start)
            if not self.is_member(k): return False, k

            l = self.generate()
            # check if l is parsd by grammar/start 
            if not ep.parse_on(l):
                return False, k
        return True, None

oracle = Oracle('^(aa|bb)$')
g_T = StateTable(['a', 'b'], oracle)
l_star(g_T)
print(g_T.dfa())



# A problem with this algorithm is its exponential case behavior as Moore [^2]
# notes. The solution that Moore offers is to order the nonterminals in the
# decreasing order of the number of distinct left corners.
#  
# 
# [^1]: Marvin C. Paull, Algorithm design: a recursion transformation framework, 1988
# [^2]: Robert C Moore, Removing Left Recursion from Context-Free Grammars [*](https://www.microsoft.com/en-us/research/wp-content/uploads/2000/04/naacl2k-proc-rev.pdf)., 2000
