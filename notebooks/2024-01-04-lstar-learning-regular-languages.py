# ---
# published: true
# title: Learning Regular Languages with L* Algorithm
# layout: post
# comments: true
# tags: regular-grammars induction
# categories: post
# ---
# 
# TLDR; This tutorial is a complete implementation of Angluin's L-star algorithm
# with PAC learning for inferring input grammars of blackbox programs in Python
# (i.e. without using equivalence queries). Such grammars are typically useful
# for fuzzing such programs.
# The Python interpreter is embedded so that you
# can work through the implementation steps.
#  
# In many previous posts, I have discussed how to
# [parse with](/post/2023/11/03/matching-regular-expressions/),
# [fuzz with](/post/2021/10/22/fuzzing-with-regular-expressions/), and
# manipulate regular and context-free grammars. However, in many cases, such
# grammars may be unavailable. If you are given a blackbox program, where the
# program indicates in some way that the input was accepted or not, what can
# we do to learn the actual input specification of the blackbox? In such cases,
# the best option is to try and learn the input specification.
# 
# This particular research field which investigates how to learn the input
# specification of blackbox programs is called blackbox *grammar inference* or
# *grammatical inference* (see the **Note** at the end for a discussion on other
# names). In this post, I will discuss one of the classic algorithms for
# learning the input specification called L\*. The L\* algorithm was invented by
# Dana Angluin in 1987 [^angluin1987]. While the initial algorithm used what is
# called an equivalence query, which assumes that you can check the correctness
# of the learned grammar separate from yes/no oracle, Angluin in the same paper
# also talks about how to update this algorithm to make use of the PAC
# (*Probably Approximately Correct*) framework from Valiant [^valiant1984].
# Angluin expands on this further in 1988 [^angluin1988].
# 
# 

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl

# #### Prerequisites
# 
# We need the fuzzer to generate inputs to parse and also to provide some
# utilities such as conversion of regular expression to grammars, random
# sampling from grammars etc. Hence, we import all that.

import simplefuzzer as fuzzer
import rxfuzzer
import earleyparser
import cfgrandomsample
import cfgremoveepsilon
import math
import random

# # Grammar Inference
# 
# Let us start with the assumption that the blackbox program
# accepts a [regular language](https://en.wikipedia.org/wiki/Regular_language).
# By *accept* I mean that the program does some processing with input given
# rather than error out. For example, if the blackbox actually contained a JSON
# parser, it will *accept* a string in the JSON format, and *reject* strings
# that are not in the JSON format.
#  
# So, given such a program, and you are not allowed to peek inside the program
# source code, how do you find what the program accepts? assuming that the
# program accepts a regular language, we can start by constructing a
# [DFA](https://en.wikipedia.org/wiki/Deterministic_finite_automaton) (A
# deterministic finite state machine).
#  
# Finite state machines are of course the bread and butter of
# computer science. The idea is that the given program can be represented as a
# set of discrete states, and transitions between them. The DFA is
# initialized to the start state. A state transitions to another when it is
# fed an input symbol. Some states are marked as *accepting*. That is, starting
# from the start state, and after consuming all the symbols in the input, the
# state reached is one of the accept states, then we say that the input was
# *accepted* by the machine.
#  
# Given this information, how would we go about reconstructing the machine?
# An intuitive approach is to recognize that a state is represented by exactly
# two sets of strings. The first set of strings (the prefixes) is how the state
# can be reached from the start state. The second set of strings are
# continuations of input from the current state that distinguishes
# this state from every other state. That is, two states can be distinguished
# by the DFA if and only if there is at least one suffix string, which when fed
# into the pair of states, produces different answers -- i.e. for one, the
# machine accepts (or reaches one of the accept states), while for the other
# is rejected (or the end state is not an accept).
# 
# Given this information, a data structure for keeping track of our experiments
# presents itself -- the *observation table* where we keep our prefix strings
# as rows, and suffix strings as columns. The cell content simply marks
# whether program accepted the prefix + suffix string or not. So, here
# is our data structure.
# 
# ## ObservationTable
# 
# We initialize the observation table with the alphabet. We keep the table
# itself as an internal dict `_T`. We also keep the prefixes in `P` and
# suffixes in `S`.
# We initialize the set of prefixes `P` to be $${\epsilon}$$
# and the set of suffixes `S` also to be $$ {\epsilon} $$. We also add
# a few utility functions.

class ObservationTable:
    def __init__(self, alphabet):
        self._T, self.P, self.S, self.A = {}, [''], [''], alphabet

    def cell(self, v, e): return self._T[v][e]

    def get_sid(self, p):
        return '<%s>' % ''.join([str(self.cell(p,s)) for s in self.S])

# Using the observation table with some pre-cooked data.

if __name__ == '__main__':
    alphabet = list('abcdefgh')
    o = ObservationTable(alphabet)
    o._T = {p:{'':1, 'a':0, 'ba':1, 'cba':0} for p in alphabet}
    print(o.cell('a', 'ba'))
    print(o.get_sid('a'))

# ### Convert Table to Grammar
# 
# Given the observation table, we can recover the grammar from this table
# (corresponding to the DFA). The
# unique cell contents of rows are states. In many cases, multiple rows may
# correspond to the same state (as the cell contents are the same). We take
# the first prefix that resulted in a particular state as its representative
# prefix, and we denote the representative prefix of a state $$ s $$ by
# $$ <s> $$ (this is not used in this post).
# The *start state* is given by the state that correspond to the $$\epsilon$$
# row.
# A state is accepting if it on query of epsilon, it returns 1. The formal
# definitions are as follows. The notation $$ [p] $$ means the state
# corresponding to the prefix $$ p $$. The notation $$ [[p,s]] $$ means the
# result of oracle for the prefix $$ p $$ and the suffix $$ s $$.
# The notation $$ [p](a) $$ means the state obtained by feeding the input
# symbol $$ a $$ to the state $$ [p] $$.
#  
# * states: $$ Q = {[p] : p \in P} $$
# * start state: $$ q0 = [\epsilon] $$
# * transition function: $$ [p](a) \rightarrow [p.a] $$
# * accepting state: $$ F = {[p] : p \in P : [[p,\epsilon]] = 1} $$
# 
# For constructing the grammar from the table, we first identify all
# distinguished states. Next, we identify the start state, followed by
# accepting states. Finally, we connect states together with transitions
# between them.


class ObservationTable(ObservationTable):
    def table_to_grammar(self):
        # Step 1: identify all distinguished states.
        prefix_to_state = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for p in self.P:
            stateid = self.get_sid(p)
            if stateid not in states: states[stateid] = []
            states[stateid].append(p)
            prefix_to_state[p] = stateid

        for stateid in states: grammar[stateid] = []

        # Step 2: Identify the start state, which corresponds to epsilon row
        start_nt = prefix_to_state['']

        # Step 3: Identify the accepting states
        accepting = [prefix_to_state[p] for p in self.P if self.cell(p,'') == 1]
        if not accepting: return {'<start>': []}, '<start>'
        for s in accepting: grammar[s] = [['<_>']]
        grammar['<_>'] = [[]]

        # Step 4: Create the transition function
        for sid1 in states:
            first_such_row = states[sid1][0]
            for a in self.A:
                sid2 = self.get_sid(first_such_row + a)
                grammar[sid1].append([a, sid2])

        return grammar, start_nt

# Let us try the observation to grammar conversion for an observation table 
# that corresponds to recognition of the string `a`. We will use the alphabet
# `a`, `b`.

if __name__ == '__main__':
    alphabet = list('ab')
    o = ObservationTable(alphabet)
    o._T = {'':    {'': 0, 'a': 1},
            'a':   {'': 1, 'a': 0},
            'b':   {'': 0, 'a': 0},
            'aa':  {'': 0, 'a': 0},
            'ab':  {'': 0, 'a': 0},
            'ba':  {'': 0, 'a': 0},
            'bb':  {'': 0, 'a': 0},
            'baa': {'': 0, 'a': 0},
            'bab': {'': 0, 'a': 0}}
    P = [k for k in o._T]
    S = [k for k in o._T['']]
    o.P, o.S = P, S
    g, s = o.table_to_grammar()
    print('start: ', s)
    for k in g:
        print(k)
        for r in g[k]:
            print(" | ", r)

# ### Cleanup Grammar
# This gets us a grammar that can accept the string `a`, but it also has a
# problem. The issue is that the key `<00>` has no rule that does not include
# `<00>` in its expansion. That is, `<00>` is an infinite loop that once the
# machine goes in, is impossible to exit. We need to remove such rules. We do
# that using the `compute_cost()` function of LimitFuzzer. The idea is that
# if all rules of a nonterminal have `inf` as the cost, then that nonterminal
# produces an infinite loop and hence both the nonterminal, as well as any rule
# that references that nonterminal have to be removed recursively.

class ObservationTable(ObservationTable):
    def remove_infinite_loops(self, g, start):
        rule_cost = fuzzer.compute_cost(g)
        remove_keys = []
        for k in rule_cost:
            if k == start: continue
            res = [rule_cost[k][r] for r in rule_cost[k]
                   if rule_cost[k][r] != math.inf]
            if not res: remove_keys.append(k)

        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                if k in remove_keys: continue
                new_g[k] = []
                for r in g[k]:
                    if [t for t in r if t in remove_keys]: continue
                    new_g[k].append(r)
                if not new_g[k]:
                    if k == start: continue
                    remove_keys.append(k)
                    cont = True
        return new_g, start

# We can wrap up everything in one method.
class ObservationTable(ObservationTable):
    def grammar(self):
        g, s = self.table_to_grammar()
        return self.remove_infinite_loops(g, s)

# once again

if __name__ == '__main__':
    o = ObservationTable(alphabet)
    o._T = {'':    {'': 0, 'a': 1},
            'a':   {'': 1, 'a': 0},
            'b':   {'': 0, 'a': 0},
            'aa':  {'': 0, 'a': 0},
            'ab':  {'': 0, 'a': 0},
            'ba':  {'': 0, 'a': 0},
            'bb':  {'': 0, 'a': 0},
            'baa': {'': 0, 'a': 0},
            'bab': {'': 0, 'a': 0}}
    o.P, o.S = P, S
    g, s = o.grammar()
    print('start: ', s)
    for k in g:
        print(k)
        for r in g[k]:
            print(" | ", r)

# Now that we are convinced that we can produce a DFA or a grammar out of the
# table let us proceed to examining how to produce this table.
#  
# We start with the start state in the table, because we know for sure
# that it exists, and is represented by the empty string in row and column,
# which together (prefix + suffix) is the empty string '' or $$ \epsilon $$.
# We ask the program if it accepts the empty string, and if it accepts, we mark
# the corresponding cell in the table as accept (or `1`).
#  
# For any given state in the DFA, we should be able to say what happens when
# an input symbol is fed into the machine in that state. So, we can extend the
# table with what happens when each input symbol is fed into the start state.
# This means that we extend the table with rows corresponding to each symbol
# in the input alphabet. 
# 
# So, we can initialize the table as follows. First, we check whether the
# empty string is in the language. Then, we extend the table `T`
# to `(P u P.A).S` using membership queries. This is given in `update_table()`


class ObservationTable(ObservationTable):
    def init_table(self, oracle):
        self._T[''] = {'': oracle.is_member('') }
        self.update_table(oracle)

# The update table has two parts. First, it takes the current set of prefixes
# (`rows`) and determines the auxiliary rows to compute based on extensions of
# the current rows with the symbols in the alphabet (`auxrows`). This gives the
# complete set of rows for the table. Then, for each suffix in `S`, ensure that
# the table has a cell, and it is updated with the oracle result.

class ObservationTable(ObservationTable):
    def update_table(self, oracle):
        def unique(l): return list({s:None for s in l}.keys())
        rows = self.P
        auxrows = [p + a for p in self.P for a in self.A]
        PuPxA = unique(rows + auxrows)
        for p in PuPxA:
            if p not in self._T: self._T[p] = {}
            for s in self.S:
                if p in self._T and s in self._T[p]: continue
                self._T[p][s] = oracle.is_member(p + s)

# Using init_table and update_table

if __name__ == '__main__':
    o = ObservationTable(alphabet)
    def orcl(): pass
    orcl.is_member = lambda x: 1
    o.init_table(orcl)
    for p in o._T: print(p, o._T[p])

# Since we want to know what state we reached when we
# fed the input symbol to the start state, we add a set of cleverly chosen
# suffixes (columns) to the table, determine the machine response to these
# suffixes (by feeding the machine prefix+suffix for each combination), and
# check whether any new state other than the start state was identified. A
# new state reached by a prefix can be distinguished from the start state using
# some suffix, if, after consuming that particular prefix, followed by the
# particular suffix, the machine moved to say *accept*, but when the machine
# at the start state was fed the same suffix, the end state was not *accept*.
# (i.e. the machine accepted prefix + suffix but not suffix on its own).
# Symmetrically, if the machine did not accept the string prefix + suffix
# but did accept the string suffix, that also distinguishes the state from
# the start state. Once we have identified a new state, we can then extend
# the DFA with transitions from this new state, and check whether more
# states can be identified.
#  
# While doing this, there is one requirement we need to ensure. The result
# of transition from every state for every alphabet needs to be defined.
# The property that ensures this for the observation table is called
# *closedness* or equivalently, the observation table is *closed* if the
# table has the following property.
#  
# ### Closed
# The idea is that for every prefix we have, in set $$ P $$, we need to find
# the state that is reached for every $$ a \in A $$. Then, we need to make sure
# that the *state* represented by that prefix exists in $$ P $$. (If such a
# state does not exist in P, then it means that we have found a new state).
#  
# Formally:
# An observation table $$ P \times S $$ is closed if for each $$ t \in P·A $$
# there exists a $$ p \in P $$ such that $$ [t] = [p] $$

class ObservationTable(ObservationTable):
    def closed(self):
        states_in_P = {self.get_sid(p) for p in self.P}
        P_A = [p+a for p in self.P for a in self.A]
        for t in P_A:
            if self.get_sid(t) not in states_in_P: return False, t
        return True, None

# Using closed.

if __name__ == '__main__':
    def orcl(): pass
    orcl.is_member = lambda x: 1 if x in ['a'] else 0

    ot = ObservationTable(list('ab'))
    ot.init_table(orcl)
    for p in ot._T: print(p, ot._T[p])

    res, counter = ot.closed()
    assert not res
    print(counter)

# ### Add prefix
class ObservationTable(ObservationTable):
    def add_prefix(self, p, oracle):
        if p in self.P: return
        self.P.append(p)
        self.update_table(oracle)

# Using add_prefix

if __name__ == '__main__':
    def orcl(): pass
    orcl.is_member = lambda x: 1 if x in ['a'] else 0

    ot = ObservationTable(list('ab'))
    ot.init_table(orcl)
    res, counter = ot.closed()
    assert not res

    ot.add_prefix('a', orcl)
    for p in ot._T: print(p, ot._T[p])
    res, counter = ot.closed()
    assert res

# This is essentially the intuition behind most
# of the grammar inference algorithms, and the cleverness lies in how the
# suffixes are chosen. In the case of L\*, the when we find that one of the
# transitions from the current states result in a new state, we add the
# alphabet that caused the transition from the current state and the suffix
# that distinguished the new state to the suffixes (i.e, a + suffix is
# added to the columns).
# 
# This particular aspect is governed by the *consistence* property of the
# observation table.
# 
# ### Consistent
# 
# An observation table $$ P \times S $$ is consistent if, whenever p1 and p2
# are elements of P such that $$ [p1] = [p2] $$, for each $$ a \in A $$,
# $$ [p1.a] = [p2.a] $$.
# *If* there are two rows in the top part of the table repeated, then the
# corresponding suffix results should be the same.
# If not, we found a counter example, and we report the alphabet + the
# suffix that distinguished. We will then add the new string (a + suffix)
# as a new suffix to the table.

class ObservationTable(ObservationTable):
    def consistent(self):
        matchingpairs = [(p1, p2) for p1 in self.P for p2 in self.P
                         if p1 != p2 and self.get_sid(p1) == self.get_sid(p2)]
        suffixext = [(a, s) for a in self.A for s in self.S]
        for p1,p2 in matchingpairs:
            for a, s in suffixext:
                if self.cell(p1+a,s) != self.cell(p2+a,s):
                        return False, (p1, p2), (a + s)
        return True, None, None

# ### Add suffix

class ObservationTable(ObservationTable):
    def add_suffix(self, a_s, oracle):
        if a_s in self.S: return
        self.S.append(a_s)
        self.update_table(oracle)

# Using add_suffix

if __name__ == '__main__':
    def orcl(): pass
    orcl.is_member = lambda x: 1 if x in ['a'] else 0

    ot = ObservationTable(list('ab'))
    ot.init_table(orcl)
    is_closed, counter = ot.closed()
    assert not is_closed
    ot.add_prefix('a', orcl)
    ot.add_prefix('b', orcl)
    ot.add_prefix('ba', orcl)
    for p in ot._T: print(p, ot._T[p])

    is_closed, unknown_P = ot.closed() 
    print(is_closed)

    is_consistent,_, unknown_A = ot.consistent() 
    assert not is_consistent

    ot.add_suffix('a', orcl)
    for p in ot._T: print(p, ot._T[p])

    is_consistent,_, unknown_A = ot.consistent() 
    assert is_consistent

# Finally, L\* also relies on a *Teacher* for it to suggest new suffixes that
# can distinguish unrecognized states from current ones.
# 
# (Of course readers will quickly note that the table is not the best data
# structure here, and just because a suffix distinguished two particular
# states does not mean that it is a good idea to evaluate the same suffix
# on all other states. These are ideas that will be explored in later
# algorithms).

# ## Teacher
# We now construct our teacher. We have two requirements for the teacher.
# The first is that it should fulfil the requirement for Oracle. That is,
# it should answer `is_member()` queries. Secondly, it should also answer
# `is_equivalent()` queries.
#
# First, we define the oracle interface.

class Oracle:
    def is_member(self, q): pass

# As I promised, we will be using the PAC framework rather than the equivalence
# oracles. First, due to the limitations of our utilities for random
# sampling, we need to remove epsilon tokens from places other than
# the start rule.
# 
# We define a simple teacher based on regular expressions. That is, if you
# give it a regular expression, will convert it to an acceptor based on a
# [parser](/post/2021/02/06/earley-parsing/) and a generator based on a
# [random sampler](/post/2021/07/27/random-sampling-from-context-free-grammar/),
# and will then use it for verification of hypothesis grammars. We also
# input the PAC parameters delta for confidence and epsilon for accuracy

class Teacher(Oracle):
    def is_equivalent(self, grammar, start): assert False

class Teacher(Teacher):
    def __init__(self, rex, delta=0.1, epsilon=0.1):
        self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)
        self.parser = earleyparser.EarleyParser(self.g)
        self.sampler = cfgrandomsample.RandomSampleCFG(self.g)
        self.equivalence_query_counter = 0
        self.delta, self.epsilon = delta, epsilon

# We can define the membership query `is_member()` as follows:
class Teacher(Teacher):
    def is_member(self, q):
        try: list(self.parser.recognize_on(q, self.s))
        except: return 0
        return 1

# Given a grammar, check whether it is equivalent to the given grammar.
# The PAC guarantee is that we only need `num_calls` for the `n`th equivalence
# query. For equivalence check here, we check for strings of length 1, then
# length 2 etc, whose sum should be `num_calls`. We take the easy way out here,
# and just use `num_calls` as the number of calls for each string length.

class Teacher(Teacher):
    def is_equivalent(self, grammar, start, max_length_limit=10):
        self.equivalence_query_counter += 1
        num_calls = math.ceil(1.0/self.epsilon *
                  (math.log(1.0/self.delta) +
                              self.equivalence_query_counter * math.log(2)))

        for limit in range(1, max_length_limit):
            is_eq, counterex, c = self.is_equivalent_for(self.g, self.s,
                                                    grammar, start,
                                                    limit, num_calls)
            if counterex is None: # no members of length limit
                continue
            if not is_eq:
                c = [a for a in counterex if a is not None][0]
                return False, c
        return True, None

# Due to the limitations of our utilities for random
# sampling, we need to remove epsilon tokens from places other than
# the start rule.

class Teacher(Teacher):
    def fix_epsilon(self, grammar, start):
        gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
        gs.remove_epsilon_rules()
        return gs.grammar, start

# Next, we have a helper for producing the random sampler, and the
# parser for easy comparison.

class Teacher(Teacher):
    def digest_grammar(self, g, s, l, n):
        if not g[s]: return 0, None, None
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return cnt, key_node, ep

    def gen_random(self, key_node, cnt):
        if cnt == 0: return None
        at = random.randint(0, cnt-1)
        # sampler does not store state.
        st_ = self.sampler.key_get_string_at(key_node, at)
        return fuzzer.tree_to_string(st_)

# ## Check Grammar Equivalence
# Checking if two grammars are equivalent to a length of string for n count.

class Teacher(Teacher):
    def is_equivalent_for(self, g1, s1, g2, s2, l, n):
        cnt1, key_node1, ep1 = self.digest_grammar(g1, s1, l, n)
        cnt2, key_node2, ep2 = self.digest_grammar(g2, s2, l, n)
        count = 0

        str1 = {self.gen_random(key_node1, cnt1) for _ in range(n)}
        str2 = {self.gen_random(key_node2, cnt2) for _ in range(n)}

        for st1 in str1:
            if st1 is None: continue
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
            if st2 is None: continue
            count += 1
            try: list(ep1.recognize_on(st2, s1))
            except: return False, (None, st2), count

        return True, None, count

# Let us test this out.

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
    t = Teacher('a')
    v = t.is_equivalent_for(g1, '<0>', g2, '<0>', 2, 10)
    print(v)


#  
# ## L star main loop
# Given the observation table and the teacher, the algorithm itself is simple.
# The L* algorithm loops, doing the following operations in sequence. (1) keep
# the table closed, (2) keep the table consistent, and if it is closed and
# consistent (3) ask the teacher if the corresponding hypothesis grammar is
# correct.

def l_star(T, teacher):
    T.init_table(teacher)

    while True:
        while True:
            is_closed, unknown_P = T.closed()
            is_consistent, _, unknown_AS = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.add_prefix(unknown_P, teacher)
            if not is_consistent: T.add_suffix(unknown_AS, teacher)

        grammar, start = T.grammar()
        eq, counterX = teacher.is_equivalent(grammar, start)
        if eq: return grammar, start
        for i,_ in enumerate(counterX): T.add_prefix(counterX[0:i+1], teacher)


# Using it

if __name__ == '__main__':
    import re, string
    exprs = ['a', 'ab', 'a*b*', 'a*b', 'ab*', 'a|b', '(ab|cd|ef)*']
    for e in exprs:
        teacher = Teacher(e)
        tbl = ObservationTable(list(string.ascii_letters))
        g, s = l_star(tbl, teacher)
        print(s, g)

        ep = earleyparser.EarleyParser(g)
        gf = fuzzer.LimitFuzzer(g)
        for i in range(10):
            res = gf.iter_fuzz(key=s, max_depth=100)
            v = re.fullmatch(e, res)
            a, b = v.span()
            assert a == 0, b == len(res)
            print(a,b)

# # Definitions
# 
# * Input symbol: A single symbol that is consumed by the machine which can move
#   it from one state to another. The set of such symbols is called an alphabet,
#   and is represented by $$ A $$.
# * Membership query: A string that is passed to the blackbox. The blackbox
#   answers yes or no.
# * Equivalence query: A grammar that is passed to the teacher as a hypothesis
#   of what the target language is. The teacher answers yes or a counter
#   example that behaves differently on the blackbox and the hypothesis grammar.
# * Prefix closed: a set is prefix closed if all prefixes of any of its elements
#   are also in the same set.
# * Suffix closed: a set is suffix closed if all suffixes of any of its elements
#   are also in the same set.
# * Observation table: A table whose rows correspond to the *candidate states*.
#   The rows are made up of prefix strings that can reach given states ---
#   commonly represented as $$ S $$, but here we will denote these by $$ P $$
#   for prefixes --- and the columns are made up of suffix strings that serves
#   to distinguish these states --- commonly expressed as $$ E $$ for
#   extensions, but we will use $$ S $$ to denote suffixes here. The table
#   contains auxiliary rows that extends each item $$ p \in P $$ with each
#   alphabet $$ a \in A $$ as we discuss later in *closedness*.
#   This table defines the language inferred by the algorithm. The contents of
#   the table are the answers from the oracle on a string composed of the row
#   and column labels --- prefix + suffix. That is  $$ T[s,e] = O(s.e) $$.
#   The table has two properties: *closedness* and *consistency*.
#   If these are not met at any time, we take to resolve it.
# * The state: A state in the DFA is represented by a prefix in the observation
#   table, and is named by the pattern of 1s and 0s in the cell contents.
#   We represent a state corresponding the prefix $$ p $$ as $$ [p] $$.
# * Closedness of the observation table means that for each $$ p \in P $$ and
#   each $$ a \in A $$, the state represented by the auxiliary row $$ [p.a] $$
#   (i.e., its contents) exists in $$ P $$. That is, there is some
#   $$ p' \in P $$ such that $$ [p.a] == [p'] $$. The idea is that, the state
#   corresponding to $$ [p] $$ accepts alphabet $$ a $$ and transitions to the
#   state $$ [p'] $$, and $$ p' $$ must be in the main set of rows $$ P $$.
# * Consistency of the observation table means that if two prefixes represents
#   the same state (i.e. the contents of two rows are equal), that is
#   $$ [p1] = [p2] $$ then $$ [p1 . a] = [p2 . a] $$ for all alphabets.
#   The idea is that if two prefixes reach the state, then when fed any
#   alphabet, both prefixes should transition to the same next state
#   (represented by the pattern produced by the suffixes).
# * The candidate states `P` is prefix closed, while the set of suffixes `S`
#   is suffix closed.
# 
#  
# # Notes
# 
# While there is no strict specifications as to what grammar induction,
# inference, and learning is, according to [Higuera](http://videolectures.net/mlcs07_higuera_giv/),
# Grammar inference is about learning a *grammar* (i.e. the representation) when
# given information about a language, and focuses on the target, the grammar.
# That is, you start with the assumption that a target grammar exists. Then,
# try to guess that grammar based on your observations.
# If on the other hand, you do not believe that a particular target grammar
# exists, but want to do the best to learn the underlying principles, then it is
# grammar induction. That is, it focuses on the best possible grammar for the
# given data. Closely related fields are grammar mining, grammar recovery,
# and grammar extraction which are all whitebox approaches based on program
# or related artifact analysis. Language acquisition is another related term.
# 
# ## Context Free Languages
# Here, we discussed how to infer a regular grammar. In many cases the blackbox
# may accept a language that is beyond regular, for example, it could be
# context-free. The nice thing about L\* is that it can provide us a close
# approximation of such context-free language in terms of a regular grammar.
# One can then take the regular grammar thus produced, and try and identify
# context-free structure in that DFA based on recognition of repeating
# structures. It is still an open question on how to recover the context-free
# structure from such a DFA.
# 
# [^angluin1987]: Learning Regular Sets from Queries and Counterexamples, 1987 
# [^angluin1988]: Queries and Concept Learning, 1988
# [^valiant1984]: A theory of the learnable, 1984