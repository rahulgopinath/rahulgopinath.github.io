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
# Several independent contributions are incorporated in the TTT algorithm.
# Rivest and Schapire [^rivest1993] contributed the binary search
# counterexample analysis, which finds the single relevant suffix in a
# counterexample in $$ O(\log k) $$ queries (rather than $$ k $$ queries).
# The introduction of discrimination tree as a replacement for the observation
# table is due Kearns and Vazirani [^kearns1994].
# 
# TTT by Isberner, Howar and Steffen [^isberner2014]
# adds two further refinements: *prefix transformation*,
# which keeps access sequences minimal, and *discriminator finalization*,
# which keeps the discrimination tree shallow.
# TTT is provably redundancy-free. That is, it never makes a membership query
# whose answer could have been derived from earlier queries.
# 
# A notable extension is ADT [^adt], which extends TTT with adaptive
# distinguishing sequences, which can reduce resets in hardware settings.
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
#   A dict from state to the shortest string known to reach it.
# * _Open transition_: a transition from state $$ q $$ on symbol $$ a $$ whose
#   target state has no access sequence yet, meaning TTT has not yet
#   determined which state it leads to.
# * _Counterexample decomposition_: the process of finding the split point
#   in a counterexample, extracting a new discriminator, and splitting a
#   leaf in the DT.

# ## Prerequisites
# 
# We use the `Teacher` and `Oracle` from the L* post unchanged.
# The rest of the algorithm is independent of L*

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
import rxfuzzer
import earleyparser
import math
import random
import lstar

# Since this notebook serves both as a web notebook as well as a script
# that can be run on the command line, we redefine canvas if it is not
# defined already. The `__canvas__` function is defined externally when
# it is used as a web notebook.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print

# ## From L* to TTT
#
# In L*, when the equivalence oracle returns a counterexample $$ ce $$ of
# length $$ k $$, the algorithm adds all $$ k $$ suffixes of $$ ce $$ as
# new columns (i.e. discriminators for states).
# For each new column, it must re-query every existing row.
# However, many of these new columns are redundant because they do not
# distinguish any new pair of states.
#
# The key insight that distinguishes TTT from L* is that
# **a counterexample identifies only one pair of states** that was wrongly
# merged. Hence, exactly **one** new discriminator is sufficient, not $$ k $$.
# TTT incorporates the following independent contributions:
#
# * **Kearns and Vazirani (1994)**[^kearns1994] replaced the observation
#   table with a *discrimination tree*. A binary tree of discriminator
#   suffixes where each leaf is a state.
#   Sifting a string down the tree classifies it in $$ O(depth) $$ queries
#   rather than $$ O(|suffixes|) $$.
# * **Rivest and Schapire (1993)**[^rivest1993] showed that binary search
#   over the counterexample finds the single relevant split point in
#   $$ O(\log k) $$ queries, rather than adding all $$ k $$ suffixes.
# * **Isberner, Howar and Steffen (2014)**[^isberner2014] combined these
#   with *prefix transformation* (keeping access sequences minimal) and
#   *discriminator finalization* (keeping the DT shallow), producing TTT.
# 
# ## The DFA Representation
# 
# The `DFA` class is similar to the one from the
# [RPNI post](/post/2025/10/24/rpni-learning-regular-languages/).
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


# We also add a `run()` method which returns the state reached after consuming
# a string, and `ensure_state()` which registers a state in the grammar
# without allocating a new key, which is needed when manually constructing DFAs
# in tests and when `close_transitions` (defined later) discovers states from the DT.

class DFA(DFA):
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

# The DFA class can now model a deterministic finite state machine.
# We also add a helper to render any DFA as a Graphviz dot diagram.

def dfa_to_dot(dfa, name='DFA'):
    lines = ['digraph %s {' % name,
             '  rankdir=LR;',
             '  node [shape = circle];',
             '  __start__ [shape = point, label = ""];',
             '  __start__ -> "%s";' % dfa.start_symbol]
    for state, rules in dfa.grammar.items():
        accepting = [] in rules
        shape = 'doublecircle' if accepting else 'circle'
        lines.append('  "%s" [shape = %s];' % (state, shape))
        for rule in rules:
            if not rule: continue
            char, target = rule[0], rule[1]
            lines.append('  "%s" -> "%s" [label = "%s"];' % (state, target, char))
    lines.append('}')
    return '\n'.join(lines)

# Let us test it thoroughly.

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
    __canvas__(dfa_to_dot(dfa, 'DFA_even_a'))

# ## The Oracle
# 
# Let us define a simple mock oracle for testing the components in isolation.
# The `Teacher` imported from L* is the full oracle, and will be used in the
# main loop.

class MockOracle(lstar.Oracle):
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
# The discriminator suffixes at different nodes are **independent strings**
# with no linguistic relationship to each other. The tree structure is not a
# trie; a parent's suffix is not a prefix of its children's suffixes, and
# there is no requirement that sibling suffixes share anything in common.
# The tree is purely a *decision structure*: each node's suffix is the
# question that splits the states reachable at that point, chosen only
# because it distinguishes some pair of states that would otherwise be merged.
# Two nodes at different depths may share a suffix, or their suffixes may be
# completely unrelated; what matters is only the binary answer at each step.
# 
# Both children of an inner node can themselves be inner nodes, and the tree
# can be arbitrarily deep. A leaf appears only when we have fully classified
# a state: we know exactly which discriminator suffix distinguishes it from
# every other known state. Early in learning the tree is shallow; each
# counterexample adds exactly one new inner node, splitting one existing leaf
# into two children.
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

# ## The Spanning Tree
# 
# Each state in the hypothesis has an *access sequence*: the shortest known
# string that reaches it from `<start>`. The spanning tree is simply a dict
# from state to access sequence.
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
# It is called a tree because the states and their access sequences form an
# implicit tree: `<start>` is the root, and each state is a child of the
# state whose access sequence is one character shorter. If you drew it, every
# path from root to a node would spell out that node's access sequence.
# In TTT, we never traverse this tree structure. We only ever look
# up $$ acc(q) $$ for a given state, or add a new state with its access
# sequence. So the implementation reduces to a simple dict.

class SpanningTree:
    def __init__(self, start_symbol='<start>'):
        self.acc = { start_symbol: '' }

    def add_state(self, state, parent, char):
        self.acc[state] = self.acc[parent] + char

    def access(self, state):
        return self.acc[state]

# We add a helper to render a spanning tree as a Graphviz dot diagram.
# Each node shows its state name and access sequence.
# Edges are labelled with the character that extends the parent's access
# sequence to reach the child.

def st_to_dot(st, name='ST'):
    acc_to_state = {v: k for k, v in st.acc.items()}
    lines = ['digraph %s {' % name,
             '  rankdir=LR;',
             '  node [shape = rectangle];']
    for state, acc in st.acc.items():
        if acc:
            label = '%s\\naccess: %s' % (state, acc)
        else:
            label = state
        lines.append('  "%s" [label = "%s"];' % (state, label))
        if acc:  # has a parent
            parent_acc = acc[:-1]
            char = acc[-1]
            parent = acc_to_state.get(parent_acc)
            if parent is not None:
                lines.append('  "%s" -> "%s" [label = "%s"];' % (parent, state, char))
    lines.append('}')
    return '\n'.join(lines)

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
    __canvas__(st_to_dot(st, 'ST_example'))

# ## Splitting a Leaf
# 
# The DT starts as a single leaf `<start>`. Each counterexample causes exactly
# one leaf to be *split*: it is mutated in place into an inner node, and two
# new leaves are attached as its children.
# 
# We mutate the leaf in place because other parts of the code hold references
# to the same object. Replacing it with a new object would leave those
# references stale. After the split, the leaf's `state` attribute is removed
# and replaced with `discriminator`, `left`, and `right`.
# 
# `split_leaf` needs to know which side the old state goes on, so it queries
# the oracle: if `acc(old_state) + discriminator` is accepted, `old_state`
# goes right; otherwise left. The new state takes the other side.

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

# ### Sifting
# 
# To classify any string $$ w $$ to a state, we walk the DT from root to
# leaf. At each inner node labeled $$ d $$, we query $$ member(w \cdot d) $$
# and go right (yes) or left (no). The leaf we land on is the state $$ w $$
# belongs to. Each step is one membership query, so sifting costs at most
# $$ depth(DT) $$ queries, far fewer than L*'s $$ O(|suffixes|) $$.
# 
# At any inner node, either child may itself be another inner node. This is
# not like a trie where deeper nodes share a common prefix with their parent —
# the suffix at a deeper node is simply a different, independent question
# that separates states the shallower question could not. The tree gets deeper
# only when a pair of states survive all questions asked so far and a new
# discriminator must be introduced to tell them apart. Keeping the tree
# shallow therefore reduces the query cost of every future sift, which is why
# TTT's discriminator finalization step aggressively replaces long, incidental
# discriminators with shorter, permanent ones.

def sift(root, w, oracle):
    node = root
    while not node.is_leaf():
        if oracle.is_member(w + node.discriminator):
            node = node.right
        else:
            node = node.left
    return node   # always a DTLeaf

# We also add a helper to render a DT as a Graphviz dot diagram.
# Inner nodes show their discriminator suffix; leaves show the state name.
# Left edges (membership query returned False) are labelled "no";
# right edges (True) are labelled "yes".
# An empty discriminator is shown as ε (epsilon), meaning the string itself
# is queried directly with nothing appended.
# An optional `tracer` argument (a DTTracer, defined below) colours the
# recorded sift path blue.

def dt_to_dot(root, name='DT', tracer=None):
    path_nodes = tracer.path_nodes if tracer else set()
    path_edges = tracer.path_edges if tracer else set()
    lines = ['digraph %s {' % name, '  rankdir=TB;', '  node [shape = rectangle];']
    counter = [0]
    def node_id():
        counter[0] += 1
        return 'n%d' % counter[0]
    def blue(attrs):
        return attrs + ', color=blue, fontcolor=blue'
    def walk(node, nid):
        on_path = id(node) in path_nodes
        if node.is_leaf():
            attrs = 'shape = ellipse, label = "%s"' % node.state
            if on_path: attrs = blue(attrs)
            lines.append('  %s [%s];' % (nid, attrs))
        else:
            disc = node.discriminator if node.discriminator != '' else 'ε'
            attrs = 'label = "d: %s"' % disc
            if on_path: attrs = blue(attrs)
            lines.append('  %s [%s];' % (nid, attrs))
            left_id  = node_id()
            right_id = node_id()
            walk(node.left,  left_id)
            walk(node.right, right_id)
            no_attrs  = 'label = "no"'
            yes_attrs = 'label = "yes"'
            if (id(node), id(node.left))  in path_edges:
                no_attrs  += ', color=blue, fontcolor=blue, penwidth=2'
            if (id(node), id(node.right)) in path_edges:
                yes_attrs += ', color=blue, fontcolor=blue, penwidth=2'
            lines.append('  %s -> %s [%s];' % (nid, left_id,  no_attrs))
            lines.append('  %s -> %s [%s];' % (nid, right_id, yes_attrs))
    walk(root, node_id())
    lines.append('}')
    return '\n'.join(lines)

# `DTTracer` wraps a real DT node and records every step taken during a sift.
# It proxies `is_leaf`, `discriminator`, `left`, `right`, and `state` to the
# wrapped node, but intercepts the `left`/`right` accesses to record which
# edge was taken. After `sift(DTTracer(root), w, oracle)` returns, the tracer
# holds `path_nodes` and `path_edges` as sets of `id()`s referencing the
# *unwrapped* nodes, so they match what `dt_to_dot` sees.

class DTTracer:
    def __init__(self, node):
        self._node = node
        self.path_nodes = set()
        self.path_edges = set()

    def is_leaf(self):
        self.path_nodes.add(id(self._node))
        return self._node.is_leaf()

    @property
    def discriminator(self):
        return self._node.discriminator

    @property
    def state(self):
        return self._node.state

    @property
    def left(self):
        child = self._node.left
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @property
    def right(self):
        child = self._node.right
        self.path_edges.add((id(self._node), id(child)))
        return DTTracer._transfer(self, child)

    @staticmethod
    def _transfer(tracer, node):
        # Return a new DTTracer for the child that shares the same recording sets.
        t = DTTracer(node)
        t.path_nodes = tracer.path_nodes
        t.path_edges = tracer.path_edges
        return t

# We test sifting on the even-a's example: the DT has one discriminator
# (the empty string) that separates even-a states from odd-a states.
# 
# **Single leaf:** every string sifts to `<start>`.
if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    dt = DTLeaf('<start>')
    assert sift(dt, 'aa', oracle).state == '<start>'
    assert sift(dt, '', oracle).state == '<start>'
    __canvas__(dt_to_dot(dt, 'DT_single'))

# **Two-level tree:** a single split on discriminator ε separates `<odd>`
# (rejects ε) from `<start>` (accepts ε, since `''` has zero a's).
# We start from a single-leaf DT rooted at `<start>` and split it,
# recording that `<odd>` is reached via `'a'`.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    st_ea = SpanningTree()
    st_ea.add_state('<odd>', '<start>', 'a')
    dt = DTLeaf('<start>')
    split_leaf(dt, '', '<odd>', oracle, st_ea)
    assert sift(dt, 'aa', oracle).state == '<start>'
    assert sift(dt, 'a', oracle).state == '<odd>'
    assert sift(dt, '', oracle).state == '<start>'
    assert sift(dt, 'b', oracle).state == '<start>'
    __canvas__(dt_to_dot(dt, 'DT_even_a'))

# Sifting `'a'` (odd a's) goes left to `<odd>`; sifting `'aa'` (even a's) goes right to `<start>`.

if __name__ == '__main__':
    _tr = DTTracer(dt)
    sift(_tr, 'a', oracle)
    __canvas__(dt_to_dot(dt, 'DT_sift_a', tracer=_tr))

# Sifting `'aa'` goes right.

if __name__ == '__main__':
    _tr = DTTracer(dt)
    sift(_tr, 'aa', oracle)
    __canvas__(dt_to_dot(dt, 'DT_sift_aa', tracer=_tr))

# The two examples above only ever have one inner node at the root. To see
# both children being inner nodes, consider what happens after a second split.
# We split the `<start>` leaf again: discriminator `'aa'` separates `<start>`
# (accepts `'aa'`) from a new state `<even2>` (rejects `'aa'`, e.g. reached
# via `'aaa'`). The right child of the root is now itself an inner node, and
# sifting takes two steps before reaching a leaf.

if __name__ == '__main__':
    st_ea.add_state('<even2>', '<start>', 'aaa')
    dt3 = DTLeaf('<start>')
    split_leaf(dt3, '', '<odd>', oracle, st_ea)
    # dt3.right is now the <start> leaf; split it on 'aa'
    split_leaf(dt3.right, 'aa', '<even2>', oracle, st_ea)
    __canvas__(dt_to_dot(dt3, 'DT_three_state'))

# Sifting `'aa'`: `member('aa'+ε)` = True, go right to inner node `d='aa'`;
# `member('aa'+'aa')` = `member('aaaa')` = True, go right to leaf `<start>`.

if __name__ == '__main__':
    _tr = DTTracer(dt3)
    sift(_tr, 'aa', oracle)
    __canvas__(dt_to_dot(dt3, 'DT_sift_three_aa', tracer=_tr))

# Sifting `'aaa'`: goes right at root, then `member('aaa'+'aa')` = False,
# go left to leaf `<even2>`.

if __name__ == '__main__':
    _tr = DTTracer(dt3)
    sift(_tr, 'aaa', oracle)
    __canvas__(dt_to_dot(dt3, 'DT_sift_three_aaa', tracer=_tr))

# The even-a's DT uses ε as its discriminator because membership of the
# access sequence alone distinguishes all states. Most targets produce
# non-empty discriminators; we will see this concretely in the
# Counterexample Decomposition section and in the full worklist walkthrough.
# 
# ## Hypothesis Construction
# 
# At any point during learning, we have a DT and a spanning tree. Together
# they are enough to construct a complete hypothesis DFA. The idea is simple:
# to find the target state of transition $$ q \xrightarrow{a} ? $$, form the
# string $$ acc(q) \cdot a $$ and sift it through the DT. Whatever leaf it
# lands on is the state we assign as the target.
# 
# Concretely, for the even-a's example with a two-leaf DT (discriminator `''`,
# left = `<odd>`, right = `<start>`), and spanning tree
# `{<start>: '', <odd>: 'a'}`, we sift each transition in turn.
# The blue path shows the route taken through the DT.
# 
# $$ \langle start \rangle \xrightarrow{a} ? $$: sift `'' + 'a'` = `'a'`.
# Is `'a' + ''` accepted? No (odd a's), so go left; leaf `<odd>`.
# So `<start> -a-> <odd>`.

if __name__ == '__main__':
    _oracle_ea = MockOracle(lambda w: w.count('a') % 2 == 0)
    _dt_walk = DTInner('')
    _dt_walk.left  = DTLeaf('<odd>')
    _dt_walk.right = DTLeaf('<start>')
    _tr = DTTracer(_dt_walk)
    sift(_tr, 'a', _oracle_ea)
    __canvas__(dt_to_dot(_dt_walk, 'sift_start_a', tracer=_tr))

# $$ \langle start \rangle \xrightarrow{b} ? $$: sift `'' + 'b'` = `'b'`.
# Is `'b' + ''` accepted? Yes (zero a's), so go right; leaf `<start>`.
# So `<start> -b-> <start>`.

if __name__ == '__main__':
    _tr = DTTracer(_dt_walk)
    sift(_tr, 'b', _oracle_ea)
    __canvas__(dt_to_dot(_dt_walk, 'sift_start_b', tracer=_tr))

# $$ \langle odd \rangle \xrightarrow{a} ? $$: sift `'a' + 'a'` = `'aa'`.
# Is `'aa' + ''` accepted? Yes (even a's), so go right; leaf `<start>`.
# So `<odd> -a-> <start>`.

if __name__ == '__main__':
    _tr = DTTracer(_dt_walk)
    sift(_tr, 'aa', _oracle_ea)
    __canvas__(dt_to_dot(_dt_walk, 'sift_odd_a', tracer=_tr))

# $$ \langle odd \rangle \xrightarrow{b} ? $$: sift `'a' + 'b'` = `'ab'`.
# Is `'ab' + ''` accepted? No (odd a's), so go left; leaf `<odd>`.
# So `<odd> -b-> <odd>`.

if __name__ == '__main__':
    _tr = DTTracer(_dt_walk)
    sift(_tr, 'ab', _oracle_ea)
    __canvas__(dt_to_dot(_dt_walk, 'sift_odd_b', tracer=_tr))

# A transition is *open* if we have not yet determined its target: either the
# transition is missing from the DFA entirely, or its recorded target has no
# access sequence in the spanning tree. The second case arises when a sift
# landed on a leaf whose state is not yet in the spanning tree, meaning a new
# state was just discovered and needs to be registered.

def is_open(dfa, state, char, st):
    rule = dfa.transition(state, char)
    if rule is None: return True
    return rule[1] not in st.acc

# `close_transitions` works through all known states, sifting each open
# transition. When sifting discovers a state not yet in the spanning tree,
# that state is added and appended to the work list so its own transitions
# are processed in the same pass. This means the loop may grow as it runs:
# starting with one state, it may end with the full set.
# 
# `leaf_index` records, for each DT leaf, which `(state, char)` transitions
# were routed there. After a split, we use this index to find and re-sift
# only the transitions that are now stale, rather than re-sifting everything.

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

# To see what closing looks like step by step, consider the even-a's target
# with alphabet {a, b}. We start with one state `<start>` and a single-leaf
# DT. Every transition is open because no target state has been determined yet.
# Closing sifts `acc(<start>) + 'a'` = `'a'` and `acc(<start>) + 'b'` = `'b'`
# through the single-leaf DT. Both land on `<start>`, so both transitions
# point back to `<start>` -- the hypothesis says everything loops.
# We visualise the DT, spanning tree, and resulting DFA at this stage.

if __name__ == '__main__':
    oracle_ea = MockOracle(lambda w: w.count('a') % 2 == 0)
    dt_pre = DTLeaf('<start>')
    st_pre = SpanningTree()
    dfa_pre = DFA()
    build_hypothesis(dfa_pre, dt_pre, st_pre, oracle_ea, ['a', 'b'])
    __canvas__(dt_to_dot(dt_pre,  'DT_before_split'))

# The spanning tree
if __name__ == '__main__':
    __canvas__(st_to_dot(st_pre,  'ST_before_split'))

# DFA before the split.
if __name__ == '__main__':
    __canvas__(dfa_to_dot(dfa_pre, 'DFA_before_split'))

# After the first counterexample (say `'a'`) is processed, `decompose` splits
# the DT: a new inner node with discriminator `''` separates `<start>` (goes
# right: accepts `''`) from new state `<odd>` (goes left: rejects `''`).
# Re-sifting now correctly routes `'a'` to `<odd>` and `'b'` back to `<start>`.

if __name__ == '__main__':
    dt_post = DTInner('')
    dt_post.left  = DTLeaf('<odd>')
    dt_post.right = DTLeaf('<start>')
    st_post = SpanningTree()
    st_post.add_state('<odd>', '<start>', 'a')
    dfa_post = DFA()
    build_hypothesis(dfa_post, dt_post, st_post, oracle_ea, ['a', 'b'])
    __canvas__(dt_to_dot(dt_post,  'DT_after_split'))

# Spanning tree
if __name__ == '__main__':
    __canvas__(st_to_dot(st_post,  'ST_after_split'))

# DFA after split
if __name__ == '__main__':
    __canvas__(dfa_to_dot(dfa_post, 'DFA_after_split'))

# ### Incremental Hypothesis Update
#  
# When `decompose` splits a leaf $$ \ell $$ into an inner node, every
# transition that was previously routed to $$ \ell $$ is now stale: it
# pointed to a single state, but the DT now says some of those strings
# belong to the left child and some to the right.
#  
# We could re-sift every transition in the hypothesis from scratch, but that
# is wasteful. Instead, `leaf_index` tells us exactly which `(state, char)`
# pairs were routed to $$ \ell $$. We remove only those transitions from the
# DFA and re-sift only them. Every other transition remains correct.
#  
# Concretely, continuing the even-a's example: after the DT is split on `''`
# and state `<1>` is created, the stale transitions are those that sifted to
# the old single leaf -- all of them, since there was only one leaf. Each is
# removed and re-sifted through the new two-node DT. The transition
# `<start> -a-> <start>` becomes `<start> -a-> <1>`, and all others stay the
# same. We show the DFA before and after the update.

# `split_id` is the Python `id()` of the leaf *before* it was mutated; the
# caller must capture it before calling `split_leaf`, since the mutation
# changes the object in place and the old id is the key in `leaf_index`.

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
    dt.left  = DTLeaf('<odd>')
    dt.right = DTLeaf('<start>')
    st = SpanningTree()
    dfa = DFA()
    leaf_index = {}
    build_hypothesis(dfa, dt, st, oracle, alphabet, leaf_index)
    assert dfa.transition('<start>', 'a')[1] == '<odd>'
    assert dfa.transition('<start>', 'b')[1] == '<start>'
    assert dfa.transition('<odd>', 'a')[1] == '<start>'
    assert dfa.transition('<odd>', 'b')[1] == '<odd>'
    assert dfa.accepts('')
    assert dfa.accepts('aa')
    assert not dfa.accepts('a')
    assert st.access('<odd>') == 'a'

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
# * `old_state` and `new_state` were treated as identical by the hypothesis,
#   but the counterexample proves they are different
# * The discriminator $$ ce[i+1:] $$ is the suffix that tells them apart
# 
# `split_leaf` was introduced in the Splitting a Leaf section above and is
# used directly here. `decompose` calls it with the leaf found by sifting
# the transformed prefix, the new discriminator, and the fresh state.
# 
# We now show `update_hypothesis` in action. We build the stale hypothesis
# (single-leaf DT, everything loops to `<start>`), then split the leaf and
# call `update_hypothesis`. The stale transition `<start> -a-> <start>` is
# removed and re-sifted to `<1>`.

if __name__ == '__main__':
    oracle_ea = MockOracle(lambda w: w.count('a') % 2 == 0)
    dt_stale = DTLeaf('<start>')
    st_stale = SpanningTree()
    dfa_stale = DFA()
    leaf_index_stale = {}
    build_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea, ['a', 'b'], leaf_index_stale)
    __canvas__(dfa_to_dot(dfa_stale, 'DFA_stale'))

# Capture split_id before mutating the leaf, then split it.

if __name__ == '__main__':
    split_id = id(dt_stale)
    st_stale.add_state('<1>', '<start>', 'a')
    split_leaf(dt_stale, '', '<1>', oracle_ea, st_stale)
    __canvas__(dt_to_dot(dt_stale, 'DT_after_split2'))

# Now update: stale transitions are removed and re-sifted.

if __name__ == '__main__':
    update_hypothesis(dfa_stale, dt_stale, st_stale, oracle_ea,
                      ['a', 'b'], leaf_index_stale, split_id, '<1>')
    __canvas__(st_to_dot(st_stale, 'ST_after_update'))

# DFA after update: <start> -a-> <1>, all other transitions unchanged.

if __name__ == '__main__':
    assert dfa_stale.transition('<start>', 'a')[1] == '<1>'
    assert dfa_stale.transition('<start>', 'b')[1] == '<start>'
    assert dfa_stale.transition('<1>', 'a')[1] == '<start>'
    assert dfa_stale.transition('<1>', 'b')[1] == '<1>'
    __canvas__(dfa_to_dot(dfa_stale, 'DFA_after_update'))

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
    # 'ba' can be shortened to 'a'
    # acc('<start>') + 'a' = 'a'   -> False (odd)
    # acc('<1>')     + 'a' = 'aa'  -> True  (even), so 'a' distinguishes them
    d = finalize_discriminator('<start>', '<1>', 'ba', st, oracle)
    assert d == 'a'

# ### Finding the Split Point
# 
# `find_split_point` records the hypothesis states visited while reading
# $$ ce $$, then binary-searches for the first position where
# $$ acc(q_i) \cdot ce[i:] $$ disagrees with the target answer on $$ ce $$.
# That position $$ i $$ is where the hypothesis first takes a wrong transition.
# The search costs $$ O(\log|ce|) $$ membership queries.
# 
# The function returns both the split index and the full states list, since
# `decompose` needs the states list for the prefix transformation.

def find_split_point(dfa, st, oracle, ce):
    # walk the hypothesis along ce
    states = [dfa.start_symbol]
    for char in ce:
        rule = dfa.transition(states[-1], char)
        states.append(rule[1])

    target_answer = oracle.is_member(ce)

    # binary search: find first index where acc(q_i)+ce[i:] disagrees with target
    lo, hi = 0, len(ce)
    while lo < hi:
        mid = (lo + hi) // 2
        q_mid = states[mid]
        if oracle.is_member(st.access(q_mid) + ce[mid:]) == target_answer:
            lo = mid + 1   # mid agrees: split is to the right
        else:
            hi = mid       # mid disagrees: split is here or to the left

    # lo-1 is the last agreeing position; lo is the first disagreeing position
    return lo - 1, states

# We test find_split_point on a simple case.

if __name__ == '__main__':
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    # hypothesis: single state <start>, everything loops back, <start> is accepting
    dfa_sp = DFA()
    dfa_sp.set_accepting('<start>')
    dfa_sp.add_transition('<start>', 'a', '<start>')
    dfa_sp.add_transition('<start>', 'b', '<start>')
    st_sp = SpanningTree()
    # counterexample 'a': hypothesis accepts, target rejects
    i, states = find_split_point(dfa_sp, st_sp, oracle, 'a')
    assert i == 0, i
    # counterexample 'aab': split should be at position 0 (first divergence)
    i2, _ = find_split_point(dfa_sp, st_sp, oracle, 'aab')
    assert i2 == 0, i2

# ### Putting Decomposition Together
# 
# With `find_split_point`, `prefix_transformation`, `finalize_discriminator`,
# and `split_leaf` all in place, `decompose` is a straightforward
# four-step sequence. One counterexample yields exactly one new state and
# one new discriminator.
# 
# Note: `decompose` uses hypothesis transitions only to find the split point.
# The actual split uses $$ acc(q_i) $$ from the spanning tree, which is always
# correct with respect to the target, so `decompose` is correct even if the
# hypothesis is partially stale.

def decompose(dfa, dt, st, oracle, ce):
    # step 1: find split point by binary search
    i, states = find_split_point(dfa, st, oracle, ce)
    lo = i + 1

    # step 2: prefix transformation
    transformed, q_i = prefix_transformation(states, st, ce, i)

    # step 3: sift the transformed prefix to find the leaf, create the new state
    leaf = sift(dt, transformed, oracle)
    old_state = leaf.state
    split_id = id(leaf)
    new_state = dfa.new_state()
    st.add_state(new_state, q_i, ce[i])

    # step 4: finalize discriminator and split the leaf
    new_discriminator = finalize_discriminator(
            old_state, new_state, ce[lo:], st, oracle)
    split_leaf(leaf, new_discriminator, new_state, oracle, st)

    return new_state, split_id

# We test decompose.

if __name__ == '__main__':
    # preparation.
    oracle = MockOracle(lambda w: w.count('a') % 2 == 0)
    alphabet = ['a', 'b']

# test 1: single symbol counterexample 'a'
if __name__ == '__main__':
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
    __canvas__(dt_to_dot(dt, 'DT_decompose1'))

# test 2: longer counterexample 'aab'; binary search finds split at position 0,
# so the new state still gets access sequence 'a' and discriminator is 'b'.

if __name__ == '__main__':
    dt = DTLeaf('<start>')
    st = SpanningTree()
    dfa = DFA()
    dfa.set_accepting('<start>')
    dfa.add_transition('<start>', 'a', '<start>')
    dfa.add_transition('<start>', 'b', '<start>')
    new_state, _ = decompose(dfa, dt, st, oracle, 'aab')
    assert not dt.is_leaf()
    assert st.access(new_state) == 'a'
    __canvas__(dt_to_dot(dt, 'DT_decompose2'))

# test 3: two states, counterexample 'aa' reveals a third state.
# The DT gains a second level; the new state gets access sequence 'aa'.

if __name__ == '__main__':
    dt2 = DTInner('')
    dt2.left  = DTLeaf('<odd>')
    dt2.right = DTLeaf('<start>')
    st2 = SpanningTree()
    st2.add_state('<odd>', '<start>', 'a')
    dfa2 = DFA()
    dfa2.ensure_state('<odd>')
    dfa2.set_accepting('<start>')
    dfa2.add_transition('<start>', 'a', '<odd>')
    dfa2.add_transition('<start>', 'b', '<start>')
    dfa2.add_transition('<odd>', 'a', '<odd>')   # wrong
    dfa2.add_transition('<odd>', 'b', '<odd>')
    new_state2, _ = decompose(dfa2, dt2, st2, oracle, 'aa')
    assert st2.access(new_state2) == 'aa'
    __canvas__(dt_to_dot(dt2, 'DT_decompose3'))

# ### Worklist Growth in `close_transitions`
# 
# We now trace the full `(a|b)*ba` learning run to show how state names
# emerge from the algorithm and how the worklist grows during
# `close_transitions`. No states are pre-declared; they are created by
# `dfa.new_state()` inside `decompose` as each counterexample is processed.
# 
# **Step 1.** Single-leaf DT, only `<start>` in the spanning tree.
# `close_transitions` sifts `'' + 'a'` and `'' + 'b'`. Both land on the
# only leaf `<start>`, so no new states are discovered.

if __name__ == '__main__':
    oracle_ba = MockOracle(lambda w: w.endswith('ba'))
    dt_cl = DTLeaf('<start>')
    st_cl = SpanningTree()
    dfa_cl = DFA()
    leaf_index_cl = {}
    build_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba, ['a', 'b'], leaf_index_cl)
    print('step 1 states:', list(st_cl.acc.keys()))
    __canvas__(dt_to_dot(dt_cl, 'cl_dt_step1'))

# Spanning tree and DFA after step 1.

if __name__ == '__main__':
    __canvas__(st_to_dot(st_cl, 'cl_st_step1'))

# DFA after step 1: everything loops back to `<start>`.

if __name__ == '__main__':
    __canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step1'))

# **Step 2.** Counterexample `'ba'`: the hypothesis accepts it as `<start>`
# (which is accepting) but shouldn't, since `<start>` should only accept `''`.
# `decompose` creates a fresh state (call it `s1`) and splits the DT leaf
# with discriminator `'a'`. `update_hypothesis` re-sifts stale transitions;
# sifting `'' + 'b'` now lands on `s1`, which is new, so it is appended to the
# worklist and its transitions are closed immediately. Worklist grows from
# `['<start>']` to `['<start>', s1]`.

if __name__ == '__main__':
    new_s1, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, 'ba')
    update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba,
                      ['a', 'b'], leaf_index_cl, split_id, new_s1)
    print('step 2 states:', list(st_cl.acc.keys()), '  new state:', new_s1)
    __canvas__(dt_to_dot(dt_cl, 'cl_dt_step2'))

# Spanning tree after step 2: `s1` now has access sequence `'b'`.

if __name__ == '__main__':
    __canvas__(st_to_dot(st_cl, 'cl_st_step2'))

# DFA after step 2.

if __name__ == '__main__':
    __canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step2'))

# **Step 3.** Counterexample `'ba'` again; now the hypothesis rejects it
# because `s1 -a-> <start>` is wrong (should reach an accepting state).
# `decompose` creates `s2` and splits the `<start>` leaf with discriminator
# `ε`. `update_hypothesis` re-sifts; sifting `acc(s1) + 'a'` = `'ba'`
# lands on `s2`, which is new and appended. Worklist grows to include `s2`.
# Here is that sift path, the one that grows the worklist:

if __name__ == '__main__':
    new_s2, split_id = decompose(dfa_cl, dt_cl, st_cl, oracle_ba, 'ba')
    _tr = DTTracer(dt_cl)
    sift(_tr, 'ba', oracle_ba)
    __canvas__(dt_to_dot(dt_cl, 'cl_worklist_grow', tracer=_tr))

# And sifting `acc(s1) + 'b'` = `'bb'` lands on `<start>`, which is already known; no append.

if __name__ == '__main__':
    _tr = DTTracer(dt_cl)
    sift(_tr, 'bb', oracle_ba)
    __canvas__(dt_to_dot(dt_cl, 'cl_worklist_no_grow', tracer=_tr))

# After `update_hypothesis` finishes, all three states are wired up.

if __name__ == '__main__':
    update_hypothesis(dfa_cl, dt_cl, st_cl, oracle_ba,
                      ['a', 'b'], leaf_index_cl, split_id, new_s2)
    print('step 3 states:', list(st_cl.acc.keys()), '  new state:', new_s2)
    __canvas__(dt_to_dot(dt_cl, 'cl_dt_step3'))

# Spanning tree after step 3: three states, all access sequences minimal.

if __name__ == '__main__':
    __canvas__(st_to_dot(st_cl, 'cl_st_step3'))

# Final DFA, with states named by the algorithm as they were discovered.

if __name__ == '__main__':
    __canvas__(dfa_to_dot(dfa_cl, 'cl_dfa_step3'))

# ## Non-Redundancy
# 
# The central claim of the TTT is that it never makes a membership
# query whose answer could have been derived from earlier queries. To see
# what this means concretely: in L*, if the counterexample is `ba`, the
# algorithm adds both `a` and `ba` as new suffix columns and re-queries every
# existing state against both. If `a` was already a column, that work is
# wasted. TTT avoids this by extracting exactly one new suffix per
# counterexample and routing all future classification through the DT. This
# holds at every level:
# 
# * **Sifting is non-redundant.** Every query is $$ w \cdot d $$ where $$ d $$
#   was placed in the DT by a previous split that proved it necessary.
# * **Splitting is non-redundant.** Each split adds exactly one discriminator,
#   proven necessary by the counterexample.
# * **Closing is non-redundant.** Each transition is sifted exactly once per
#   iteration. Newly discovered states come with their DT position already
#   established by the sift that found them, so no extra queries are needed.
# 
# This contrasts with L*, where adding all $$ k $$ suffixes of a counterexample
# forces re-querying every existing row against every new column, most of
# which add no new information.

# ## A Note on the Equivalence Oracle
# 
# TTT assumes the equivalence oracle is *exact*: if it says the hypothesis is
# wrong, it returns a string the hypothesis genuinely misclassifies. The
# `Teacher` we use is a PAC oracle: it samples a finite set of strings and
# declares equivalence if none expose a mistake. This is an approximation.
# 
# In principle, a false counterexample from a PAC oracle could cause TTT to
# create a redundant state: one that could have been merged with an existing
# state without changing the language the DFA accepts. The DFA would still be
# correct, just slightly larger than necessary. Neither TTT nor L* guarantees
# a globally minimal DFA under a PAC oracle: both can acquire spurious states
# or columns from false counterexamples, and neither performs a global
# minimization pass afterward. In practice this is a minor concern: the PAC
# oracle is unlikely to produce false counterexamples with reasonable
# parameters, and the language accepted by the DFA is unaffected either way.

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
# 1. Build the initial hypothesis: one state, all transitions open.
# 2. Ask the equivalence oracle. If it says yes, we are done.
# 3. If not, decompose the counterexample to find one new state and one new
#    discriminator.
# 4. Incrementally update the hypothesis: re-sift only the stale transitions.
# 5. Repeat from step 2.
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
        if is_eq: break   # done: hypothesis matches target

        # one counterexample yields one new state and one new discriminator
        new_state, split_id = decompose(dfa, dt, st, oracle, ce)

        # incremental update: re-sift only the stale transitions
        update_hypothesis(dfa, dt, st, oracle, alphabet,
                          leaf_index, split_id, new_state)

    return dfa

# ## Examples
# 
# We test TTT on three targets of increasing complexity.
# 
# target 1: strings over {a, b} with an even number of a's
if __name__ == '__main__':
    teacher = lstar.Teacher('(b*ab*a)*b*') # even a
    result = ttt(teacher, ['a', 'b'])
    assert result.accepts('')
    assert result.accepts('aa')
    assert result.accepts('bb')
    assert not result.accepts('a')
    assert not result.accepts('aaa')
    print("test 1 passed: even a's")
    __canvas__(dfa_to_dot(result, 'DFA_even_a_ttt'))

# target 2: strings over {a, b} that end in 'b'
if __name__ == '__main__':
    teacher = lstar.Teacher('(a|b)*b')
    result = ttt(teacher, ['a', 'b'])
    assert result.accepts('b')
    assert result.accepts('ab')
    assert result.accepts('aab')
    assert not result.accepts('')
    assert not result.accepts('a')
    assert not result.accepts('ba')
    print('test 2 passed: ends in b')
    __canvas__(dfa_to_dot(result, 'DFA_ends_b_ttt'))

# target 3: binary strings whose value is divisible by 3
# 
# This target has no convenient regex, so we write a custom teacher.
# It is a good stress test: the minimal DFA has exactly 3 states (one per
# remainder mod 3), the alphabet is {0, 1}, and transitions are determined
# by how reading a bit updates the current value modulo 3. This exercises
# TTT on a target where the states correspond to arithmetic structure rather
# than string patterns.

class DivBy3Teacher(lstar.Teacher):
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

# Test this.
if __name__ == '__main__':
    result = ttt(DivBy3Teacher(delta=0.2, epsilon=0.2), ['0', '1'])
    assert result.accepts('')
    assert result.accepts('0')
    assert result.accepts('11')    # 3 in binary
    assert result.accepts('110')   # 6 in binary
    assert not result.accepts('1')
    assert not result.accepts('10') # 2 in binary
    print('test 3 passed: divisible by 3 in binary')
    __canvas__(dfa_to_dot(result, 'DFA_divby3_ttt'))

# ## Evaluating Model Accuracy
# 
# We measure precision and recall by cross-fuzzing the target grammar and the
# inferred grammar. Precision is the fraction of strings generated by the
# inferred DFA that the target accepts. Recall is the fraction of strings
# generated by the target that the inferred DFA accepts.
# 
# The inferred DFA may contain a dead/sink state: a non-accepting state with
# no exit, representing strings the target permanently rejects. Such a state
# causes `LimitFuzzer` to loop, because the grammar has no finite derivation
# from it. We remove dead states before fuzzing using `fuzzer.compute_cost`,
# which assigns each nonterminal the minimum number of steps needed to reach
# a terminal string. Any nonterminal with infinite cost is a dead state;
# we remove it and all rules that reference it.

def remove_infinite_loops(g, start):
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

# We define a `match` helper that wraps the Earley parser in a boolean check.

def match(p, start, text):
    try: p.recognize_on(text, start)
    except SyntaxError: return False
    return True

# Testing
# Each pair is (regex, alphabet). Cases cover a range of DFA shapes:
# two-segment and three-segment chains, prefix-anchored, suffix-anchored,
# substring-containment, exact-alternation, and disjoint finite sets.

if __name__ == '__main__':
    cases = [
        ('(b*ab*a)*b*',       ['a', 'b']),
        ('(a|b)*b',           ['a', 'b']),
        ('a*b*',              ['a', 'b']),
        ('ab*',               ['a', 'b']),   # must start with a, then any b's
        ('(a|b)*ba',          ['a', 'b']),   # must end with ba
        ('(ab)*',             ['a', 'b']),   # strictly alternating
        ('a*b*c*',            ['a', 'b', 'c']),
        ('a(a|b)*a',          ['a', 'b']),   # must start and end with a
        ('(aab)*',            ['a', 'b']),   # period-3 repetition
        ('(a|b)*aba(a|b)*',   ['a', 'b']),   # must contain substring aba
        ('(a|b)*abb',         ['a', 'b']),   # must end with abb
        ('aa|bb',             ['a', 'b']),   # exactly aa or exactly bb
        ('(ab|ba)*',          ['a', 'b']),   # even-length, alternating pairs
        ('(a|b)*ab(a|b)*',    ['a', 'b']),   # must contain substring ab
    ]
    for e, alphabet in cases:
        teacher = lstar.Teacher(e, delta=0.2, epsilon=0.2)
        t_g, t_s = teacher.g, teacher.s
        t_f = fuzzer.LimitFuzzer(t_g)

        result = ttt(teacher, alphabet)
        i_g, i_s = remove_infinite_loops(result.grammar, result.start_symbol)
        i_p = earleyparser.EarleyParser(i_g)
        i_f = fuzzer.LimitFuzzer(i_g)

        lgi = lgi_lgb = lgb = lgb_lgi = 0
        for _ in range(100):
            val = i_f.iter_fuzz(key=i_s, max_depth=100)
            if match(teacher.parser, t_s, val): lgi_lgb += 1
            lgi += 1

            val = t_f.iter_fuzz(key=t_s, max_depth=100)
            if match(i_p, i_s, val): lgb_lgi += 1
            lgb += 1

        precision = lgi_lgb / lgi if lgi else 1.0
        recall    = lgb_lgi / lgb if lgb else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        print('expr: %-20s  precision: %.2f  recall: %.2f  F1: %.2f'
              % (e, precision, recall, f1))

# ## Comparison with L*
# 
# | | L* | TTT |
# |---|---|---|
# | Data structure | Flat observation table | Discrimination tree (Kearns-Vazirani) |
# | Counterexample processing | Add all $$ k $$ suffixes | Binary search for 1 suffix (Rivest-Schapire) |
# | Prefix transformation | No | Yes (minimal access sequences, TTT) |
# | Discriminator finalization | No | Yes (shallow DT, TTT) |
# | Redundant queries | Many | None: the DT structure prevents re-querying known distinctions |
# | Closedness check | Explicit global scan | Lazy, local (open transitions) |
# | Consistency check | Explicit global scan | Structurally prevented by DT |
# 
# The DT depth is bounded by $$ n $$ (one split per state), so sifting never
# becomes expensive. This makes TTT the preferred algorithm when membership
# queries are costly, as is typical when learning protocol implementations
# or library APIs through testing.
# 
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
