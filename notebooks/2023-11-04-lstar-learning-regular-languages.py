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
# http://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
# http://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities

import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import cfgrandomsample
import cfgremoveepsilon
import math
import random

# We start with a few definitions
# 
# ## Definitions
# 
# * A symbol X 
# 

# ## StateTable
# 
# Next, we define the state table. We initialize it with an oracle, and the
# alphabet.
# That is, we initialize the set of prefixes `S` to be { $$\epsilon $$ }
# and the set of extensions (experiments) `E` also to be { $$\epsilon $$ }
class StateTable:
    def __init__(self, alphabet, oracle):
        self._T, self.S, self.E = {}, [''], ['']
        self.oracle = oracle
        self.A = alphabet

# We can initialize the table as follows. First, we check whether the
# empty string is in the language. Then, we extend the table `T`
# to `(S u S.A).E` using membership queries.
# 
# - For each s in S and each a in A, query the oracle for the output of `s.a`
# and update table `T` with the rows.
# - For each `t` in `E`, query the oracle for the output of `s.t` and update `T`


class StateTable(StateTable):
    def init_table(self):
        self._T[''] = {'': self.oracle.is_member('') }
        self.extend()

    def unique(self, l):
        return list({s:None for s in l}.keys())

    def extend(self):
        SuS_A = self.unique(self.S + [s + a for s in self.S for a in self.A])
        SuS_A_E = [(s,e) for s in SuS_A for e in self.E]
        for s,e in SuS_A_E:
            if s in self._T and e in self._T[s]: continue
            if s not in self._T: self._T[s] = {}
            self._T[s][e] = self.oracle.is_member(s + e)

    def row(self, v): return self._T[v]

    def cell(self, v, e): return self._T[v][e]


# ### Closed
# 
# An observation table (S, E) is closed if for each t in S·A
# there exists an s in S such that row(t) = row(s)
class StateTable(StateTable):
    def closed(self):
        S_A = [s+a for s in self.S for a in self.A]
        for t in S_A:
            res = [s for s in self.S if self.row(t) == self.row(s)]
            if not res: return False, t
        return True, None

# ### Consistent
# 
# An observation table (S, E) is consistent if, whenever s1 and s2
# are elements of S such that row(s1) = row(s2), for each a in A,
# row(s1a) = row(s2a). 
# /If/ there are two rows in the top part of the table repeated, then the
# corresponding extensions should be the same.

class StateTable(StateTable):
    def consistent(self):
        for s1,s2 in [(s1,s2) for s1 in self.S for s2 in self.S if s1 != s2]:
            if self.row(s1) != self.row(s2): continue
            for a in self.A:
                for e in self.E:
                    if self.cell(s1+a,e) != self.cell(s2+a,e):
                        return False, (a + e)
                #assert False
        return True, None

# ### Table utilities
class StateTable(StateTable):
    def append_S(self, s):
        if s in self.S: return
        self.S.append(s)
        self.extend()

    def append_AE(self, ae):
        if ae in self.E: return
        self.E.append(ae)
        self.extend()

# ### The DFA
# 
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


# Remove infinite loops
class StateTable(StateTable):
    def remove_infinite_loops(self, g, s):
        g = deep_clone(g)
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            # if all rules in a k cost inf, then it should be removed.
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        new_g = {}
        for k in g:
            if k in remove_keys: continue
            new_g[k] = []
            for r in g[k]:
                if [t for t in r if t in remove_keys]: continue
                new_g[k].append(r)
        return new_g, s

    def infer_grammar(self):
        g, s = self.dfa()
        g, s = self.remove_infinite_loops(g, s)
        return g, s


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
        #print(counterX)
        for p in prefixes(counterX): T.append_S(p)

import hashlib
random.seed(0)

# Next, we need to consider our oracle. It serves both as the
# blackbox to learn from and also as the teacher.

# First checking if two grammars are equivalent to a length
# of string for n count.

def deep_clone(grammar):
    grammar = dict(grammar)
    return {k:[list(r) for r in grammar[k]] for k in grammar} # deep clone

def fix_epsilon(grammar, start):
    grammar = deep_clone(grammar)
    gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
    gs.remove_epsilon_rules()
    return gs.grammar, start

def prepare_grammar(g, s, l, n):
    g, s = fix_epsilon(g, s)
    rgf = cfgrandomsample.RandomSampleCFG(g)
    key_node = rgf.key_get_def(s, l)
    cnt = key_node.count
    ep = earleyparser.EarleyParser(g)
    return rgf, key_node, cnt, ep

def is_equivalent_for(g1, s1, g2, s2, l, n):
    # start with 1 length
    rgf1, key_node1, cnt1, ep1 = prepare_grammar(g1, s1, l, n)
    rgf2, key_node2, cnt2, ep2 = prepare_grammar(g2, s2, l, n)
    count = 0

    if cnt1 == 0 and cnt2 == 0:
        return True, (None, None), count

    if cnt1 == 0:
        at2 = random.randint(0, cnt2-1)
        st2_ = rgf2.key_get_string_at(key_node2, at2)
        st2 = fuzzer.tree_to_string(st2_)
        return False, (None, st2), count

    if cnt2 == 0:
        at1 = random.randint(0, cnt1-1)
        st1_ = rgf1.key_get_string_at(key_node1, at1)
        st1 = fuzzer.tree_to_string(st1_)
        return False, (st1, None), count

    str1 = set()
    str2 = set()

    for i in range(n):
        at1, at2 = random.randint(0, cnt1-1), random.randint(0, cnt2-1)

        st1_ = rgf1.key_get_string_at(key_node1, at1)
        st1 = fuzzer.tree_to_string(st1_)
        str1.add(st1)
        st2_ = rgf2.key_get_string_at(key_node2, at2)
        st2 = fuzzer.tree_to_string(st2_)
        str2.add(st2)

    for st1 in str1:
        count += 1
        try: list(ep2.recognize_on(st1, s2))
        except: return False, (st1, None), count

    for st2 in str2:
        count += 1
        try: list(ep1.recognize_on(st2, s1))
        except: return False, (None, st2), count

    return True, None, count

#
if __name__ == '__main__':
    g1 = { # should end with one.
            '<0>': [
                ['1', '<1>'],
                ['0', '<0>']
                ],
            '<1>':[
                ['1', '<1>'],
                []
                ]
    }
    g2 = { # should end with one.
            '<0>': [
                ['1', '<1>'],
                ['0', '<1>']
                ],
            '<1>':[
                ['1', '<1>'],
                []
                ]
    }

    v = is_equivalent_for(g1, '<0>', g2, '<0>', 2, 10)
    print(v)


# 
class Oracle:
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == ('^', '$'):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)

        g, s = fix_epsilon(self.g, self.s)

        self.ep = earleyparser.EarleyParser(g)

        # only random samplers need '$', which gets removed after.
        # g = dict(self.g)
        # g = {k:[list(r) for r in g[k]] for k in g} # deep clone
        # for k in g:
        #     for r in g[k]:
        #         if not r: r.append('$')
        self.rgf = cfgrandomsample.RandomSampleCFG(g)
        # self.rgf = fuzzer.LimitFuzzer(self.g)
        self.counter = 0
        # epsilon is the accuracy and delta is the confidence
        self.delta, self.epsilon = 0.1, 0.1

    def dfa_to_str(self, q):
        s = hashlib.shake_128(bytes(str(q), 'utf-8')).hexdigest(4)
        return s


    def generate(self, l):
        cache = {}
        while not cache:
            l += 1
            self.rgf.produce_shared_forest(self.s, l)
            cache = self.rgf.compute_cached_index(l, {})
        cnt = self.rgf.get_total_count(cache)
        at = random.randint(1, cnt) # at least 1 length
        v, tree = self.rgf.random_sample(self.s, at, cache)
        return fuzzer.tree_to_string(tree)
        #return self.rgf.fuzz(self.s)


    def is_member(self, q):
        try: list(self.ep.recognize_on(q, self.s))
        except: return 0
        return 1

    # There are two things to consider here. The first is that we need to
    # generate  inputs from both our regular expression as well as the given grammar.
    def is_equivalent(self, grammar, start):
        #grammar = self.fix_epsilon(grammar)
        self.counter += 1
        if not grammar[start]:
            s = self.generate(self.counter)
            return False, s
        num_calls = math.ceil(1.0/self.epsilon * (math.log(1.0/self.delta) + self.counter * math.log(2)))

        #g = self.fix_epsilon(self.g)
        max_length_limit = 10
        for limit in range(1, max_length_limit):
            is_eq, counterex, c = is_equivalent_for(self.g, self.s, grammar, start, limit, num_calls)
            if counterex is None: # no members of length limit
                continue
            if not is_eq:
                c = [a for a in counterex if a is not None][0]
                return False, c
        return True, None

if __name__ == '__main__':
    oracle = Oracle('a*b*')
    g_T = StateTable(['a', 'b'], oracle)
    l_star(g_T)
    g, s = g_T.dfa()
    print(s, g)

    oracle = Oracle('a*b')
    g_T = StateTable(['a', 'b'], oracle)
    l_star(g_T)
    g, s = g_T.dfa()
    print(s, g)

    oracle = Oracle('ab')
    g_T = StateTable(['a', 'b'], oracle)
    l_star(g_T)
    g, s = g_T.dfa()
    print(s, g)

    oracle = Oracle('ab*')
    g_T = StateTable(['a', 'b'], oracle)
    l_star(g_T)
    g, s = g_T.dfa()
    print(s, g)

# ### Using it

if __name__ == '__main__':
    import re
    exprs = ['a*b*', 'ab', 'a*b', 'ab*', 'a|b', 'aba']
    for e in exprs:
        oracle = Oracle(e)
        tbl = StateTable(['a', 'b'], oracle)
        g_T = l_star(tbl)
        g, s = g_T.infer_grammar()
        print(s, g)

        ep = earleyparser.EarleyParser(g)
        gf = fuzzer.LimitFuzzer(g)
        for i in range(10):
            res = gf.iter_fuzz(key=s, max_depth=100)
            v = re.fullmatch(e, res)
            a, b = v.span()
            assert a == 0, b == len(res)
            print(a,b)


#  
# 
# [^1]: Marvin C. Paull, Algorithm design: a recursion transformation framework, 1988
