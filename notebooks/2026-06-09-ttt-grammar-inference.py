# ---
# published: true
# title: Learning Regular Languages with the TTT Algorithm
# layout: post
# comments: true
# tags: regular-grammars induction
# categories: post
# ---
# 
# TLDR; This tutorial is a complete implementation of the TTT algorithm
# for active automata learning in Python. TTT combines the discrimination
# tree of Kearns and Vazirani with binary search counterexample analysis
# from Rivest and Schapire, and adds prefix transformation and discriminator
# finalization to eliminate all redundant membership queries. The Python
# interpreter is embedded so that you can work through the implementation
# steps.
# 
# In my [previous post](/post/2024/01/04/lstar-learning-regular-languages/),
# I implemented Angluin's L* algorithm for learning regular languages from
# a blackbox oracle. L* uses a flat observation table to track state
# distinctions, which leads to redundant membership queries: when a
# counterexample arrives, all its suffixes are added as columns even though
# most distinguish no new states.
# 
# The key insight that the discrimination tree is a better data structure
# for this job was due to Kearns and Vazirani [^kearns1994], who replaced
# L*'s observation table with a binary tree of discriminators. Rivest and
# Schapire [^rivest1993] independently contributed binary search
# counterexample analysis, which finds the single relevant suffix in a
# counterexample in $$ O(\log k) $$ queries rather than adding all $$ k $$
# suffixes.
# 
# TTT by Isberner, Howar and Steffen [^isberner2014]
# adds two further refinements: *prefix transformation*,
# which keeps access sequences minimal, and *discriminator finalization*,
# which keeps the discrimination tree shallow. Together these make TTT
# provably redundancy-free. That is, it never makes a membership query whose
# answer could have been derived from earlier queries.
# 
# TTT is the algorithm of choice in practical automata learning tools such
# as LearnLib [^learnlib]. ADT [^adt] extends TTT with adaptive
# distinguishing sequences, which can reduce resets in hardware settings,
# though performance differences in software engineering settings are modest.
# 
# ## Definitions
# 
# * _Alphabet_ $$ A $$: the set of input symbols the DFA reads.
# * _Membership query_: a string passed to the blackbox oracle. The oracle
#   answers yes (accepted) or no (rejected).
# * _Equivalence query_: a hypothesis grammar passed to the teacher. The
#   teacher answers yes, or returns a counterexample string where the
#   hypothesis and the target disagree.
# * _PAC oracle_: a probabilistic approximation to the equivalence oracle.
#   After $$ N $$ random tests without finding a counterexample, we declare
#   the hypothesis probably approximately correct.
# * _Discrimination tree (DT)_: a binary tree whose inner nodes are
#   discriminator suffixes and whose leaves are states. Sifting a string
#   $$ w $$ through the tree classifies it to a state using one membership
#   query per level.
# * _Access sequence_ $$ acc(q) $$: the shortest known string that reaches
#   state $$ q $$ in the target.
# * _Spanning tree_: a mapping from each known state to its access sequence.
#   The dual of the PTA from RPNI (where PTA maps strings to states, the
#   spanning tree maps states to strings).
# * _Open transition_: a transition $$ \delta(q, a) $$ whose target state
#   has no access sequence yet. The TTT equivalent of L*'s closedness
#   violation.
# * _Counterexample decomposition_: the process of finding the split point
#   in a counterexample, extracting a new discriminator, and splitting a
#   leaf in the DT.

# ## Prerequisites
# 
# We import the `Teacher` and `Oracle` from the L* post, and use them unchanged.
# The PAC equivalence oracle in `Teacher` is a direct drop-in for TTT.
# The rest of the algorithm is completely independent of how equivalence
# queries are answered.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/lstar-0.0.1-py2.py3-none-any.whl

import simplefuzzer as fuzzer
import math
import random
from lstar import Teacher, Oracle

# Since this notebook serves both as a web notebook as well as a script
# that can be run on the command line, we redefine canvas if it is not
# defined already. The `__canvas__` function is defined externally when
# it is used as a web notebook.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print

# ## The Road from L* to TTT
#  
# In L*, when the equivalence oracle returns a counterexample $$ ce $$ of
# length $$ k $$, the algorithm adds all $$ k $$ suffixes of $$ ce $$ as
# new columns. For each new column, it must re-query every existing row.
# Many of these new columns are, however, redundant. They do not
# distinguish any new pair of states, but given that they exist, the cells
# need to be filled, and hence you pay the price in queries.
# 
# The key insight in TTT is that
# **a counterexample only ever witnesses one new distinction**:
# one pair of states was wrongly merged. Hence, exactly **one** new
# discriminator is sufficient, not $$ k $$. Getting to this point required
# three independent contributions:
# 
# * **Kearns and Vazirani (1994)** [^kearns1994] replaced the observation
#   table with a *discrimination tree*. A binary tree of discriminator
#   suffixes where each leaf is a state.
#   Sifting a string down the tree classifies it in $$ O(depth) $$ queries
#   rather than $$ O(|suffixes|) $$.
# * **Rivest and Schapire (1993)** [^rivest1993] showed that binary search
#   over the counterexample finds the single relevant split point in
#   $$ O(\log k) $$ queries, rather than adding all $$ k $$ suffixes.
# * **Isberner, Howar and Steffen (2014)** [^isberner2014] combined these
#   with *prefix transformation* (keeping access sequences minimal) and
#   *discriminator finalization* (keeping the DT shallow), producing TTT.
# 
# ## The DFA Representation
# 
# The `DFA` class is similar to the one from the
# [RPNI post](/post/2025/10/24/rpni-learning-regular-languages/).
# We also add a `run()` method which returns the state reached after consuming
# a string, and `ensure_state()` which registers a state in the grammar
# without allocating a new key, which is needed when manually constructing DFAs
# in tests and when `close_transitions` discovers states from the DT.

class DFA:
    def __init__(self, start_symbol='<start>', key_counter=0):
        self.grammar = {}
        self.start_symbol = start_symbol
        self.grammar[self.start_symbol] = []
        self.key_counter = key_counter

    def transition(self, key, char):
        rules = self.grammar[key]
        for rule in rules:
            if not rule: continue
            if char == rule[0]: return rule
        return None

    def add_transition(self, from_key, token, to_key):
        self.grammar[from_key].append([token, to_key])

    def set_accepting(self, key):
        if [] not in self.grammar[key]:
            self.grammar[key].append([])

    def ensure_state(self, key):
        if key not in self.grammar:
            self.grammar[key] = []

    def new_state(self):
        key = '<%s>' % self.key_counter
        self.grammar[key] = []
        self.key_counter += 1
        return key

    def run(self, string):
        state = self.start_symbol
        for char in string:
            rule = self.transition(state, char)
            if rule is None: return None
            state = rule[1]
        return state

    def accepts(self, string):
        state = self.run(string)
        if state is None: return False
        return [] in self.grammar[state]

# The DFA class can now model a deterministic finite state machine. So, let us
# test it thoroughly.

if __name__ == '__main__':
    dfa = DFA()
    s1 = dfa.new_state()
    dfa.add_transition('<start>', 'a', s1)
    dfa.add_transition(s1, 'a', '<start>')
    dfa.add_transition('<start>', 'b', '<start>')
    dfa.add_transition(s1, 'b', s1)
    dfa.set_accepting('<start>')
    assert dfa.run('') == '<start>'
    assert dfa.run('a') == s1
    assert dfa.run('aa') == '<start>'
    assert dfa.run('x') is None
    assert dfa.accepts('')
    assert dfa.accepts('aa')
    assert not dfa.accepts('a')
    print('DFA tests passed')

# ## The Oracle
# 
# Let us define a simple mock oracle for testing the components in isolation.
# The `Teacher` imported from L* is the full oracle, and will be used in the
# main loop.

class MockOracle(Oracle):
    def __init__(self, fn):
        self.fn = fn
    def is_member(self, q):
        return self.fn(q)

# ## The Discrimination Tree
# 
# The discrimination tree (DT) replaces L*'s flat observation table.
# Think of it as a game of 20 questions: each inner node asks:
# **if I append suffix $$ d $$ to this string, does the target accept it?**
# and routes left (no) or right (yes). Each leaf is a known state.
# 
# There are exactly two kinds of nodes: Leaf and Inner.

class DTNode:
    def is_leaf(self): return False

class DTInner(DTNode):
    def __init__(self, discriminator):
        self.discriminator = discriminator
        self.left = None    # membership query returned False
        self.right = None   # membership query returned True

class DTLeaf(DTNode):
    def __init__(self, state):
        self.state = state

    def is_leaf(self): return True

# We test the node types before proceeding.

if __name__ == '__main__':
    leaf = DTLeaf('<start>')
    assert leaf.is_leaf() == True
    inner = DTInner('a')
    assert inner.is_leaf() == False
    print('DTNode tests passed')

# ### Sifting
# 
# To classify any string $$ w $$ to a state, we walk the DT from root to
# leaf. At each inner node labeled $$ d $$, we query $$ member(w \cdot d) $$
# and go right (yes) or left (no). The leaf we land on is the state $$ w $$
# belongs to. Each step is one membership query, so sifting costs at most
# $$ depth(DT) $$ queries, far fewer than L*'s $$ O(|suffixes|) $$.

def sift(root, w, oracle):
    node = root
    while not node.is_leaf():
        if oracle.is_member(w + node.discriminator):
            node = node.right
        else:
            node = node.left
    return node   # always a DTLeaf

# We test sifting on the even-a's example: the DT has one discriminator
# (the empty string) that separates even-a states from odd-a states.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    # single leaf: everything maps to start
    dt = DTLeaf('<start>')
    assert sift(dt, 'aa', oracle).state == '<start>'
    assert sift(dt, '', oracle).state == '<start>'
    # two-level tree:  [''] / <1> (odd) \ <start> (even)
    dt = DTInner('')
    dt.left = DTLeaf('<1>')
    dt.right = DTLeaf('<start>')
    assert sift(dt, 'aa', oracle).state == '<start>'
    assert sift(dt, 'a', oracle).state == '<1>'
    assert sift(dt, '', oracle).state == '<start>'
    assert sift(dt, 'b', oracle).state == '<start>'
    print('sift tests passed')

# ## The Spanning Tree
# 
# If you have read the
# [RPNI post](/post/2025/10/24/rpni-learning-regular-languages/),
# the spanning tree will look familiar. The RPNI Prefix Tree Acceptor (PTA)
# is a tree-shaped DFA where every path from root to a node spells out the
# string that reaches that state. The spanning tree is the *dual* of the PTA:
# 
# * **PTA** maps *strings -> states*. You start with examples and build
#   states to match them.
# * **Spanning tree** maps *states -> strings*. You start with states
#   (discovered by TTT) and record the string that reaches each one.
# 
# In TTT, we never traverse the spanning tree as a tree. We only ever look
# up $$ acc(q) $$ for a given state, or add a new state with its access
# sequence. So the implementation reduces to a simple dict.

class SpanningTree:
    def __init__(self, start_symbol='<start>'):
        self.acc = { start_symbol: '' }

    def add_state(self, state, parent, char):
        self.acc[state] = self.acc[parent] + char

    def access(self, state):
        return self.acc[state]

# We test the spanning tree.

if __name__ == '__main__':
    st = SpanningTree()
    assert st.access('<start>') == ''
    st.add_state('<1>', '<start>', 'a')
    assert st.access('<1>') == 'a'
    st.add_state('<2>', '<1>', 'b')
    assert st.access('<2>') == 'ab'
    st.add_state('<3>', '<start>', 'b')
    assert st.access('<3>') == 'b'
    print('SpanningTree tests passed')

# ## Hypothesis Construction
# 
# The DT and spanning tree together define all transitions of the hypothesis
# DFA. For each state $$ q $$ and symbol $$ a $$:
# 
# 1. Form $$ acc(q) \cdot a $$, the string that reaches $$ q $$ and then reads $$ a $$.
# 2. Sift it through the DT. The oracle queries at each node ask:
#    *"which known state does this string belong to?"*
# 3. The leaf returned is the target state $$ \delta(q, a) $$.
# 
# This is closely related to L*'s closedness and consistency checks, but
# handled in a single pass:
# 
# * **Closedness** In L*, closedness means that every reachable state has a row
#   in the table. In TTT, the equivalent is *open transitions*. These are
#   transitions where sifting lands on a leaf with no access sequence yet.
#   When an open transition is found, we close it immediately,
#   adding the new state as we go.
# * **Consistency** In L*, consistency means that no two identical rows have
#   different successors. In TTT, consistency is *structurally maintained* by
#   the DT.
#   Two strings share a leaf only if no discriminator in the tree separates
#   them. A counterexample split is the consistency repair, done once per
#   counterexample rather than checked globally.
# 
# A transition is *open* if its target has no access sequence yet.

def is_open(dfa, state, char, st):
    rule = dfa.transition(state, char)
    if rule is None: return True
    return rule[1] not in st.acc

# We close all open transitions by sifting. We use an index-based loop
# so that newly discovered states are appended to `states` and processed
# in the same pass.
#
# `leaf_index` maps each `DTLeaf` object to the list of `(state, char)` pairs
# whose transition was established by sifting to that leaf. This is the index
# that the incremental update needs to find stale transitions after a split.

def close_transitions(dfa, dt, st, oracle, alphabet, leaf_index=None):
    states = list(st.acc.keys())
    i = 0
    while i < len(states):
        state = states[i]
        i += 1
        dfa.ensure_state(state)
        for char in alphabet:
            if not is_open(dfa, state, char, st): continue
            target_leaf = sift(dt, st.access(state) + char, oracle)
            target_state = target_leaf.state
            if target_state not in st.acc:
                # new state discovered: register and queue for processing
                st.add_state(target_state, state, char)
                states.append(target_state)
            if dfa.transition(state, char) is None:
                dfa.add_transition(state, char, target_state)
            if leaf_index is not None:
                leaf_index.setdefault(id(target_leaf), []).append((state, char))

# Accepting states are determined by querying the oracle directly on each
# access sequence. If $$ acc(q) $$ is accepted by the target, then $$ q $$
# is an accepting state.

def build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index=None):
    for state in list(st.acc.keys()):
        dfa.ensure_state(state)
        if oracle.is_member(st.access(state)):
            dfa.set_accepting(state)
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)

# ### Incremental Hypothesis Update
#
# After `split_leaf` turns leaf $$ \ell $$ into an inner node, every transition
# that previously targeted $$ \ell $$ may now belong to either child.
# We find those transitions via `leaf_index`, remove the old entry from
# the DFA, re-sift to the correct child, and update the DFA in place.
# Every other transition is unaffected.
#
# Newly discovered states (from re-sifting or from the new state itself) are
# handled by a targeted call to `close_transitions` restricted to those states.
# Accepting status for any new state is set immediately.
#
# `split_id` is the Python `id()` of the leaf *before* it was mutated; the
# caller must capture it before calling `split_leaf`.

def update_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index, split_id, new_state):
    # record the new state's accepting status and ensure it exists in the DFA
    dfa.ensure_state(new_state)
    if oracle.is_member(st.access(new_state)):
        dfa.set_accepting(new_state)

    # collect transitions that pointed to the now-split leaf
    stale = leaf_index.pop(split_id, [])

    # remove the stale transitions from the DFA grammar and re-sift them
    for (from_state, char) in stale:
        rules = dfa.grammar[from_state]
        dfa.grammar[from_state] = [r for r in rules if not (r and r[0] == char)]

    # re-close just the stale transitions (plus any new open ones from new_state)
    # mark new_state as needing closure by ensuring its transitions are absent
    close_transitions(dfa, dt, st, oracle, alphabet, leaf_index)

# We test hypothesis construction on the even-a's example.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    alphabet = ['a', 'b']
    dt = DTInner('')
    dt.left  = DTLeaf('<1>')
    dt.right = DTLeaf('<start>')
    st = SpanningTree()
    dfa = DFA()
    leaf_index = {}
    build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)
    assert dfa.transition('<start>', 'a')[1] == '<1>'
    assert dfa.transition('<start>', 'b')[1] == '<start>'
    assert dfa.transition('<1>', 'a')[1] == '<start>'
    assert dfa.transition('<1>', 'b')[1] == '<1>'
    assert dfa.accepts('')
    assert dfa.accepts('aa')
    assert not dfa.accepts('a')
    assert st.access('<1>') == 'a'
    print('build_hypothesis tests passed')

# ## Counterexample Decomposition
# 
# When the equivalence oracle returns a counterexample $$ ce $$, we know the
# hypothesis is wrong on $$ ce $$. But *where exactly* does it go wrong?
# 
# ### The Split Point
# 
# Walk $$ ce $$ through the hypothesis. At position 0, both hypothesis and
# target are in $$ \langle start \rangle $$, so they agree. At position
# $$ |ce| $$, they disagree (that is what the counterexample means). So
# somewhere in between is the *first point of disagreement*. That is, the
# position $$ i $$ where the hypothesis first takes a wrong transition.
# 
# We find this by binary search in $$ O(\log|ce|) $$ queries. At each
# midpoint $$ m $$, we check whether $$ acc(q_m) \cdot ce[m:] $$ gives the
# same answer as the full counterexample. If yes, the split point is to the
# right; if no, it is here or to the left.
# 
# ### Prefix Transformation
# 
# After finding the split point $$ i $$, we need the string that reaches
# state $$ q_i $$ and then reads $$ ce[i] $$. The raw counterexample prefix
# $$ ce[:i+1] $$ would work, but we use $$ acc(q_i) \cdot ce[i] $$ instead.
# This is the *prefix transformation*, and it gives two guarantees:
# 
# * **Correctness**: $$ acc(q_i) $$ traces a known path through the
#   hypothesis, so the sift is guaranteed to work even if the hypothesis
#   is partially stale.
# * **Minimality**: the new state gets access sequence $$ acc(q_i) \cdot
#   ce[i] $$, which is the shortest possible. Using $$ ce[:i+1] $$ could
#   produce a much longer access sequence, making future sifts more expensive.

def prefix_transformation(states, st, ce, i):
    # replace the raw prefix ce[:i+1] with acc(q_i) + ce[i]
    # states[i] is the hypothesis state reached after consuming ce[:i]
    q_i = states[i]
    return st.access(q_i) + ce[i], q_i

# ### Splitting a Leaf
# 
# Once we have the split point, we know:
# 
# * A leaf $$ \ell $$ currently represents `old_state`
# * A `new_state` was hiding inside it
# * The discriminator $$ ce[i+1:] $$ separates them
# 
# We *mutate the leaf in place* into an inner node. This is essential because
# other parts of the tree already hold references to $$ \ell $$, so replacing
# it with a new object would leave those references stale.

def split_leaf(leaf, discriminator, new_state, oracle, st):
    old_state = leaf.state
    old_leaf = DTLeaf(old_state)
    new_leaf = DTLeaf(new_state)
    # ask the oracle which side old_state goes on
    old_goes_right = oracle.is_member(st.access(old_state) + discriminator)
    # mutate the leaf in place into an inner node
    leaf.__class__ = DTInner
    leaf.discriminator = discriminator
    if old_goes_right:
        leaf.right = old_leaf
        leaf.left  = new_leaf
    else:
        leaf.left  = old_leaf
        leaf.right = new_leaf
    del leaf.state

# We test split_leaf.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    st = SpanningTree()
    st.add_state('<1>', '<start>', 'a')
    leaf = DTLeaf('<start>')
    # '' distinguishes <start> (even, True) from <1> (odd, False)
    split_leaf(leaf, '', '<1>', oracle, st)
    assert leaf.is_leaf() == False
    assert leaf.discriminator == ''
    assert leaf.right.state == '<start>'   # <start> answered True
    assert leaf.left.state == '<1>'        # <1> answered False
    assert sift(leaf, '', oracle).state == '<start>'
    assert sift(leaf, 'a', oracle).state == '<1>'
    assert sift(leaf, 'aa', oracle).state == '<start>'
    print('split_leaf tests passed')

# ### Discriminator Finalization
# 
# The discriminator $$ ce[i+1:] $$ is correct but may be longer than
# necessary. A shorter suffix of $$ ce[i+1:] $$ may distinguish the two
# states just as well. Keeping discriminators short keeps the DT shallow,
# which reduces sifting costs in all future iterations.
# 
# We try suffixes from shortest to longest, stopping at the first one that
# distinguishes the two states.
# Once a candidate fails, all shorter suffixes will also fail, so we stop early.

def finalize_discriminator(old_state, new_state, ce_suffix, st, oracle):
    best = ce_suffix
    for j in range(len(ce_suffix) - 1, 0, -1):
        candidate = ce_suffix[j:]
        old_answer = oracle.is_member(st.access(old_state) + candidate)
        new_answer = oracle.is_member(st.access(new_state) + candidate)
        if old_answer != new_answer:
            best = candidate
        else:
            break   # shorter suffixes won't work either
    return best

# We test discriminator finalization.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    st = SpanningTree()
    st.add_state('<1>', '<start>', 'a')
    # '' is already minimal
    d = finalize_discriminator('<start>', '<1>', '', st, oracle)
    assert d == ''
    print('finalize test 1 passed')
    # 'ba' can be shortened to 'a'
    # acc('<start>') + 'a' = 'a'   -> False (odd)
    # acc('<1>')     + 'a' = 'aa'  -> True  (even), so 'a' distinguishes them
    d = finalize_discriminator('<start>', '<1>', 'ba', st, oracle)
    assert d == 'a'
    print('finalize test 2 passed')
    print('finalize_discriminator tests passed')

# ### Putting Decomposition Together
# 
# We now have all the pieces. `decompose` finds the split point by binary
# search, applies the prefix transformation, finalizes the discriminator,
# and splits the leaf. One counterexample yields one new state and one new
# discriminator. This is the tightest possible refinement.
# 
# Note: decompose uses hypothesis transitions only to *find* the split point.
# The actual split uses $$ acc(q_i) $$, which is always correct with respect
# to the target. This means decompose is correct even if the hypothesis is
# partially stale. The access sequences in the spanning tree are ground
# truth, independent of hypothesis quality.

def decompose(dfa, dt, st, oracle, ce):
    # record hypothesis states along ce
    # note: we use these only to find the split point, not for the split itself
    states = [dfa.start_symbol]
    for char in ce:
        rule = dfa.transition(states[-1], char)
        states.append(rule[1])

    target_answer = oracle.is_member(ce)

    # binary search for split point: O(log|ce|) queries
    lo, hi = 0, len(ce) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        q_mid = states[mid]
        if oracle.is_member(st.access(q_mid) + ce[mid:]) == target_answer:
            lo = mid + 1   # still correct at mid: split point is to the right
        else:
            hi = mid       # already wrong at mid: split point is here or left

    # prefix transformation: use acc(q_i) + ce[i] instead of ce[:i+1]
    transformed, q_i = prefix_transformation(states, st, ce, lo)

    # find the leaf to split; capture its id before mutation
    leaf = sift(dt, transformed, oracle)
    old_state = leaf.state
    split_id = id(leaf)

    # create the new state with its access sequence
    new_state = dfa.new_state()
    st.add_state(new_state, q_i, ce[lo])

    # discriminator finalization: find shortest distinguishing suffix
    new_discriminator = finalize_discriminator(
            old_state, new_state, ce[lo+1:], st, oracle)

    # split the leaf (mutates leaf in place; id(leaf) is still split_id)
    split_leaf(leaf, new_discriminator, new_state, oracle, st)

    return new_state, split_id

# We test decompose.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    alphabet = ['a', 'b']

    # test 1: single symbol counterexample 'a'
    dt = DTLeaf('<start>')
    st = SpanningTree()
    dfa = DFA()
    dfa.set_accepting('<start>')
    dfa.add_transition('<start>', 'a', '<start>')
    dfa.add_transition('<start>', 'b', '<start>')
    new_state, _ = decompose(dfa, dt, st, oracle, 'a')
    assert not dt.is_leaf()
    assert st.access(new_state) == 'a'
    assert sift(dt, '', oracle).state == '<start>'
    assert sift(dt, 'a', oracle).state == new_state
    print('decompose test 1 passed')

    # test 2: longer counterexample 'aab'
    dt = DTLeaf('<start>')
    st = SpanningTree()
    dfa = DFA()
    dfa.set_accepting('<start>')
    dfa.add_transition('<start>', 'a', '<start>')
    dfa.add_transition('<start>', 'b', '<start>')
    new_state, _ = decompose(dfa, dt, st, oracle, 'aab')
    assert not dt.is_leaf()
    assert st.access(new_state) == 'a'
    print('decompose test 2 passed')

    # test 3: two states, counterexample reveals a third
    dt2 = DTInner('')
    dt2.left  = DTLeaf('<1>')
    dt2.right = DTLeaf('<start>')
    st2 = SpanningTree()
    st2.add_state('<1>', '<start>', 'a')
    dfa2 = DFA()
    dfa2.ensure_state('<1>')
    dfa2.set_accepting('<start>')
    dfa2.add_transition('<start>', 'a', '<1>')
    dfa2.add_transition('<start>', 'b', '<start>')
    dfa2.add_transition('<1>', 'a', '<1>')   # wrong
    dfa2.add_transition('<1>', 'b', '<1>')
    new_state2, _ = decompose(dfa2, dt2, st2, oracle, 'aa')
    assert st2.access(new_state2) == 'aa'
    print('decompose test 3 passed')

    print('all decompose tests passed')

# ## Non-Redundancy
# 
# The central claim of the TTT paper is that it never makes a membership
# query whose answer could have been derived from earlier queries. This holds
# at every level:
# 
# * **Sifting is non-redundant.** Every query is $$ w \cdot d $$ where $$ d $$
#   was placed in the DT by a previous split that proved it necessary.
# * **Splitting is non-redundant.** Each split adds exactly one discriminator,
#   proven necessary by the counterexample.
# * **Closing is non-redundant.** Each transition is sifted exactly once per
#   iteration. Newly discovered states come with their DT position already
#   established by the sift that found them. That is, no extra queries are needed.
# 
# This contrasts with L*, where adding all $$ k $$ suffixes of a counterexample
# forces re-querying every existing row against every new column, most of
# which add no new information.

# ## DT Coherence After Split
#
# After `split_leaf` turns a leaf into an inner node, some transitions in the
# hypothesis that targeted the old leaf are now stale, because the DT now
# routes some of those strings to the new child instead.
#
# The incremental strategy finds exactly those stale transitions via
# `leaf_index`, removes them from the DFA, and re-sifts only them. Every
# other transition remains valid and costs no queries. New states discovered
# during re-sifting are registered and their own transitions are closed in the
# same pass.

# ## The Main Loop
#
# The main loop orchestrates everything:
#
# 1. Build the hypothesis from the DT and spanning tree (first iteration only).
# 2. Ask the equivalence oracle. If it says yes, we are done.
# 3. If not, decompose the counterexample to find one new state and one new
#    discriminator.
# 4. Incrementally update the hypothesis by re-sifting only the stale transitions.
# 5. Repeat.
#
# The loop runs exactly $$ n - 1 $$ times where $$ n $$ is the number of
# states in the minimal DFA, one counterexample per new state discovered.

def ttt(oracle, alphabet):
    dt = DTLeaf('<start>')
    st = SpanningTree()
    leaf_index = {}

    # initial hypothesis: one state, no transitions yet
    dfa = DFA()
    build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)

    while True:
        # equivalence query via PAC oracle from Teacher
        is_eq, ce = oracle.is_equivalent(dfa.grammar, dfa.start_symbol)
        if is_eq:
            return dfa   # done: hypothesis matches target

        # one counterexample yields one new state and one new discriminator
        new_state, split_id = decompose(dfa, dt, st, oracle, ce)

        # incremental update: re-sift only the stale transitions
        update_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index, split_id, new_state)

# ## Examples
# 
# We test TTT on three targets of increasing complexity.

# target 1: strings over {a, b} with an even number of a's
if __name__ == '__main__':
    teacher = Teacher('(b*ab*a)*b*') # even a
    result = ttt(teacher, ['a', 'b'])
    assert result.accepts('')
    assert result.accepts('aa')
    assert result.accepts('bb')
    assert not result.accepts('a')
    assert not result.accepts('aaa')
    print("test 1 passed: even a's")

# target 2: strings over {a, b} that end in 'b'
if __name__ == '__main__':
    teacher = Teacher('(a|b)*b')
    result = ttt(teacher, ['a', 'b'])
    assert result.accepts('b')
    assert result.accepts('ab')
    assert result.accepts('aab')
    assert not result.accepts('')
    assert not result.accepts('a')
    assert not result.accepts('ba')
    print('test 2 passed: ends in b')

# target 3: binary strings whose value is divisible by 3
if __name__ == '__main__':
    class DivBy3Teacher(Teacher):
        def __init__(self, delta=0.5, epsilon=0.5):
            super().__init__('0', delta=delta, epsilon=epsilon)

        def is_member(self, w):
            if not w: return True
            return int(w, 2) % 3 == 0

        def is_equivalent(self, grammar, start):
            self.equivalence_query_counter += 1
            num_calls = math.ceil(1.0/self.epsilon *
                      (math.log(1.0/self.delta +
                                  self.equivalence_query_counter * math.log(2))))
            dfa = DFA(start_symbol=start)
            dfa.grammar = grammar
            for _ in range(num_calls):
                # sample a random binary string up to length 10
                length = random.randint(0, 10)
                w = ''.join(random.choice(['0', '1']) for _ in range(length))
                if bool(self.is_member(w)) != bool(dfa.accepts(w)):
                    return False, w
            return True, None

    result = ttt(DivBy3Teacher(delta=0.2, epsilon=0.2), ['0', '1'])
    assert result.accepts('')
    assert result.accepts('0')
    assert result.accepts('11')    # 3 in binary
    assert result.accepts('110')   # 6 in binary
    assert not result.accepts('1')
    assert not result.accepts('10') # 2 in binary
    print('test 3 passed: divisible by 3 in binary')

# ## Comparison with L*
# 
# | | L* | TTT |
# |---|---|---|
# | Data structure | Flat observation table | Discrimination tree (Kearns-Vazirani) |
# | Counterexample processing | Add all $$ k $$ suffixes | Binary search for 1 suffix (Rivest-Schapire) |
# | Prefix transformation | No | Yes (minimal access sequences, TTT) |
# | Discriminator finalization | No | Yes (shallow DT, TTT) |
# | Redundant queries | Many | None by construction |
# | Closedness check | Explicit global scan | Lazy, local (open transitions) |
# | Consistency check | Explicit global scan | Structurally prevented by DT |
# 
# The DT depth is bounded by $$ n $$ (one split per state), so sifting never
# becomes expensive. This makes TTT the preferred algorithm when membership
# queries are costly, as is typical when learning protocol implementations
# or library APIs through testing.

# ## References
# 
# [^kearns1994]: Michael Kearns and Umesh Vazirani. An Introduction to Computational Learning Theory. MIT Press, 1994. pp. 44-58.
# 
# [^rivest1993]: Ronald L. Rivest and Robert E. Schapire. Inference of Finite Automata Using Homing Sequences. Information and Computation, 103(2):51-73, 1993.
# 
# [^isberner2014]: Malte Isberner, Falk Howar, and Bernhard Steffen. The TTT Algorithm: A Redundancy-Free Approach to Active Automata Learning. RV 2014.
# 
# [^isbernerphd]: Malte Isberner. Foundations of Active Automata Learning: An Algorithmic Perspective. PhD Dissertation, TU Dortmund, 2015. http://129.217.131.68:8080/bitstream/2003/34282/1/Dissertation.pdf
# 
# [^isbernerce]: Malte Isberner and Bernhard Steffen. An Abstract Framework for Counterexample Analysis in Active Automata Learning. ICGI 2014. http://proceedings.mlr.press/v34/isberner14a.pdf
# 
# [^learnlib]: Falk Howar and Bernhard Steffen. Active Automata Learning in Practice. Springer, 2022.
# 
# [^adt]: Markus Frohme. Active Automata Learning with Adaptive Distinguishing Sequences. Master Thesis, TU Dortmund, 2015. https://arxiv.org/abs/1902.01139
