# ---
# published: true
# title: Learning Regular Languages with L* Algorithm
# layout: post
# comments: true
# tags: regular-grammars induction
# categories: post
# ---
# 
# TLDR; This tutorial is a complete implementation of Angluin's L* algorithm
# with PAC learning in Python (i.e. without using equivalence queries).
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
# specification of blackbox programs is called blackbox grammar inference or
# grammatical inference (see the note at the end for a discussion on other
# names). In this post, I will discuss one of the classic algorithms for
# learning the input specification calle L*. L* was invented by Dana Angluin
# in 1987 [^angluin1987]. While the initial algorithm used what is called an
# equivalence query, which assumes that you can check the correctness of the
# learned grammar separate from yes/no oracle, Angluin updated this algorithm
# to make use of the PAC (Probably Approximately Correct)
# framework [^valiant1984] from Valiant in 1988 [^angluin1988].
# 
# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl

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

# To start with, let us start with the assumption that the blackbox program
# accepts a regular language. In the classical algorithm from Angluin
# [^angluin1987], beyond the yes/no oracle (the program can tell you whether any
# given string is acceptable or not, traditionally called the
# *membership query*), we also require what is called an *equivalence query*.
# That is, the algorithm requires what is called a *Teacher* that is able to
# accept a guess of the target language in terms of a grammar, and tell us
# whether we guessed it right, or if not, provide us with a string that has
# different behavior on the blackbox and the guessed grammar -- a counter
# example. The idea is to use the counter example to refine the guess until the
# guess matches the target grammar. To start with, we require the following
# definitions.
#  
# ## Definitions
# 
# * Membership query: A string that is passed to the blackbox. The blackbox
#   answers yes or no.
# * Equivalence query: A grammar that is passed to the teacher as a hypothesis
#   of what the target language is. The teacher answers yes or a counter
#   example that behaves differetly on the blackbox and the hypothesis grammar.
# * Prefix closed: a set is prefix closed if all prefixes of any of its elements
#   are also in the same set.
# * Suffix closed: a set is suffix closed if all suffixes of any of its elements
#   are also in the same set.
# * State table: A table whose rows correspond to the *candidate states* (S) and
#   its extensions of one alphabet (S . a) and the columns correspond to
#   *query strings* or *experiments* (E). This table
#   defines the language inferred by the algorithm. The contents of the table
#   are the answers from the oracle on a string composed of the row and column
#   labels. That is `T[s,e] == O(s.e)`.
#   The table has two properties
#   *closedness* and *consistency*. If these are not met at any time, we take
#   to resolve it.
# * Closedness of the state table means that for each s in S and each a in the
#   alphabet, the contents of row(s.a) has a corresponding row(t) in
#   the state table with the same contents. The idea is that, the state
#   corresponding to row(s) accepts alphabet a and transitions to the state
#   represented by row(t).
# * Consistency of the state table means that if the contents of two rows are
#   equal, that is row(s1) == row(s2) then row(s1 . a) = row(s2 . a) for all
#   alphabets. The idea is tht if two states are the same, then their extensions
#   should also be the same.
# * The candidate states `S` is prefix closed, while the set of experiments `E`
#   is suffix closed.
# 
# Given the state table, the algorithm itself is simple
# 
# ## L*
# The L* algorithm loops, doing the following operations in sequence. (1) keep
# the table closed, (2) keep the table consistent, and if it is closed and
# consistent (3) ask the teacher if the corresponding hypothesis grammar is
# correct.

def l_star(T):
    T.init_table()

    while True:
        while True:
            is_closed, counter_E = T.closed()
            is_consistent, counter_A = T.consistent()
            if is_closed and is_consistent: break
            if not is_closed: T.append_S(counter_E)
            if not is_consistent: T.append_AE(counter_A)

        g, s = T.grammar()
        res, counterX = teacher.is_equivalent(g, s)
        if res: return T
        prefixes = [counterX[0:i] for i,a in enumerate(counterX)][1:]
        for p in prefixes: T.append_S(p)

# ## StateTable
# 
# Next, we define the state table, also called the observation table.

# We initialize the class with an teacher, and the alphabet.
# That is, we initialize the set of prefixes `S` to be { $$\epsilon $$ }
# and the set of extensions (experiments) `E` also to be { $$\epsilon $$ }

class StateTable:
    def __init__(self, alphabet, teacher):
        self._T, self.S, self.E = {}, [''], ['']
        self.teacher = teacher
        self.A = alphabet

    def row(self, v): return self._T[v]

    def cell(self, v, e): return self._T[v][e]

    def get_sid(self, s):
        row = self.row(s)
        return ''.join([str(row[e]) for e in self.E])


# We can initialize the table as follows. First, we check whether the
# empty string is in the language. Then, we extend the table `T`
# to `(S u S.A).E` using membership queries.
# 
# - For each s in S and each a in A, query the teacher for the output of `s.a`
# and update table `T` with the rows.
# - For each `t` in `E`, query the teacher for the output of `s.t` and update `T`


class StateTable(StateTable):
    def init_table(self):
        self._T[''] = {'': self.teacher.is_member('') }
        self.extend()

    def unique(self, l):
        return list({s:None for s in l}.keys())

    def extend(self):
        SuS_A = self.unique(self.S + [s + a for s in self.S for a in self.A])
        SuS_A_E = [(s,e) for s in SuS_A for e in self.E]
        for s,e in SuS_A_E:
            if s in self._T and e in self._T[s]: continue
            if s not in self._T: self._T[s] = {}
            self._T[s][e] = self.teacher.is_member(s + e)


# ### Closed
# 
# A state table (S, E) is closed if for each t in S·A
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
# A state table (S, E) is consistent if, whenever s1 and s2
# are elements of S such that row(s1) = row(s2), for each a in A,
# row(s1.a) = row(s2.a). 
# *If* there are two rows in the top part of the table repeated, then the
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
# Next, we define two utilities, one for appending a new S, and another
# for appending a new E. We also define a utility for naming a state,
# which corresponds to a unique row contents.

class StateTable(StateTable):
    def append_S(self, s):
        if s in self.S: return
        self.S.append(s)
        self.extend()

    def append_AE(self, ae):
        if ae in self.E: return
        self.E.append(ae)
        self.extend()


# ### The Grammar
# Given the state table, we can recover the grammar from this table
# (corresponding to the DFA). The
# unique cell contents of rows are states. In many cases, multiple rows may
# correspond to the same state (as the cell contents are the same).
# The *start state* is given by the state that correspond to the epsilon row.
# A state is acceptig if it on query of epsilon, it retunrs 1.
#  
# Q = {row(s) : s \in S}             --- states
# q0 = row(e)                        -- start
# F = {row(s) : s \in S, T(s) = 1}   -- accepting state
# \delta(row(s), a) = row(s.a)      ---- Transition function

class StateTable(StateTable):
    def grammar(self):
        row_map = {}  # Mapping from row string to state ID
        states = {}
        grammar = {}
        for s in self.S:
            sid = self.get_sid(s)
            if sid not in states: states[sid] = []
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

# ### Cleanup Grammar
# The grammar output by the `grammar()` method is a bit messy. It can contain
# keys will always lead to infinite loops. For example,
# 
# ```
# <A> ::= <B> <A>
#      |  <C> <A>
# ```
# We need to remove such infinite loops.

class StateTable(StateTable):
    def remove_infinite_loops(self, g, s):
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

# ### Infer Grammar
# We can now wrap up everything in one method.

class StateTable(StateTable):
    def infer_grammar(self):
        g, s = self.grammar()
        g, s = self.remove_infinite_loops(g, s)
        return g, s

# ## Teacher
# 
# Next, we need to construct our teacher. 
# As I promised, we will be using the PAC framework rather than the equivalence
# oracles. First, due to the limitations of our utilities for random
# sampling, we need to remove epsilon tokens from places other than
# the start rule.

class Teacher:
    def fix_epsilon(self, grammar, start):
        gs = cfgremoveepsilon.GrammarShrinker(grammar, start)
        gs.remove_epsilon_rules()
        return gs.grammar, start

# Next, we have a helper for producing the random sampler, and the
# parser for easy comparison.

class Teacher(Teacher):
    def prepare_grammar(self, g, s, l, n):
        g, s = self.fix_epsilon(g, s)
        rgf = cfgrandomsample.RandomSampleCFG(g)
        key_node = rgf.key_get_def(s, l)
        cnt = key_node.count
        ep = earleyparser.EarleyParser(g)
        return rgf, key_node, cnt, ep

    def generate_a_random_string(self, rgf, key_node, cnt):
        at = random.randint(0, cnt-1)
        st_ = rgf.key_get_string_at(key_node, at)
        return fuzzer.tree_to_string(st_)

# ## Check Grammar Equivalence
# Checking if two grammars are equivalent to a length of string for n count.

class Teacher(Teacher):
    def is_equivalent_for(self, g1, s1, g2, s2, l, n):
        rgf1, key_node1, cnt1, ep1 = self.prepare_grammar(g1, s1, l, n)
        rgf2, key_node2, cnt2, ep2 = self.prepare_grammar(g2, s2, l, n)
        count = 0

        if cnt1 == 0 and cnt2 == 0: return True, (None, None), count


        if cnt1 == 0:
            st2 = self.generate_a_random_string(rgf2, key_node2, cnt2)
            return False, (None, st2), count

        if cnt2 == 0:
            st1 = self.generate_a_random_string(rgf1, key_node1, cnt1)
            return False, (st1, None), count

        str1 = set()
        str2 = set()

        for i in range(n):
            str1.add(self.generate_a_random_string(rgf1, key_node1, cnt1))
            str2.add(self.generate_a_random_string(rgf2, key_node2, cnt2))

        for st1 in str1:
            count += 1
            try: list(ep2.recognize_on(st1, s2))
            except: return False, (st1, None), count

        for st2 in str2:
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
    t = Teacher()
    v = t.is_equivalent_for(g1, '<0>', g2, '<0>', 2, 10)
    print(v)


# We define a simple oracle based on regular expressions.

class Teacher(Teacher):
    def __init__(self, rex):
        self.rex = rex
        if (rex[0], rex[-1]) == ('^', '$'):
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex[1:-1])
        else:
            self.g, self.s = rxfuzzer.RegexToGrammar().to_grammar(rex)

        g, s = self.fix_epsilon(self.g, self.s)

        self.ep = earleyparser.EarleyParser(g)
        self.rgf = cfgrandomsample.RandomSampleCFG(g)
        self.counter = 0
        # epsilon is the accuracy and delta is the confidence
        self.delta, self.epsilon = 0.1, 0.1

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

    def is_member(self, q):
        try: list(self.ep.recognize_on(q, self.s))
        except: return 0
        return 1

    # There are two things to consider here. The first is that we need to
    # generate inputs from both our regular expression as well as the given grammar.
    def is_equivalent(self, grammar, start):
        self.counter += 1
        if not grammar[start]:
            s = self.generate(self.counter)
            return False, s

        num_calls = math.ceil(1.0/self.epsilon *
                              (math.log(1.0/self.delta) + self.counter * math.log(2)))

        max_length_limit = 10
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

if __name__ == '__main__':
    teacher = Teacher('a*b*')
    g_T = StateTable(['a', 'b'], teacher)
    l_star(g_T)
    g, s = g_T.grammar()
    print(s, g)

    teacher = Teacher('a*b')
    g_T = StateTable(['a', 'b'], teacher)
    l_star(g_T)
    g, s = g_T.grammar()
    print(s, g)

    teacher = Teacher('ab')
    g_T = StateTable(['a', 'b'], teacher)
    l_star(g_T)
    g, s = g_T.grammar()
    print(s, g)

    teacher = Teacher('ab*')
    g_T = StateTable(['a', 'b'], teacher)
    l_star(g_T)
    g, s = g_T.grammar()
    print(s, g)

# ### Using it

if __name__ == '__main__':
    import re
    exprs = ['a*b*', 'ab', 'a*b', 'ab*', 'a|b', 'aba']
    for e in exprs:
        teacher = Teacher(e)
        tbl = StateTable(['a', 'b'], teacher)
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


# # Notes
# While there is no strict specifications as to what grammar induction,
# inference, and learning is, according to [Higuera](http://videolectures.net/mlcs07_higuera_giv/),
# Grammar inference is about learning a *grammar* (i.e. the representation) when
# given information about a language, and focuses on the target, the grammar.
# That is, you start with the assumption that a target gramamr exists. Then,
# try to guess that grammar based on your observations.
# If on the other hand, you do not believe that a particular target grammar
# exists, but want to do the best to learn the underlying principles, then it is
# grammar induction. That is, it focues on the best possible grammar for the
# given data. Closely related fiels are grammar mining, grammar recovery,
# and grammar extraction which are all whitebox approaches based on program
# or related artifact analysis. Language acquisition is another related term.
# 
# [^angluin1987]: Learning Regular Sets from Queries and Counterexamples, 1987 
# [^angluin1988]: Queries and Concept Learning, 1988
# [^valiant1984]: A theory of the learnable, 1984
