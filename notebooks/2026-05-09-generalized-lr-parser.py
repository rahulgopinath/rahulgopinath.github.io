# ---
# published: false
# title: Generalized LR (GLR) Parser
# layout: post
# comments: true
# tags: parsing, glr
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of a GLR Parser in Python.
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#
# A GLR parser is a generalization of LR parsers. We
# [previously discussed](/post/2024/07/01/lr-parsing/) LR(0), SLR(1),
# LALR(1), and LR(1) parsers. These are deterministic bottom-up parsers
# that are fast and powerful, but require conflict-free parse tables.
# Ambiguous grammars, and many grammars that produce shift/reduce or
# reduce/reduce conflicts, therefore cannot be parsed deterministically
# without additional conflict-resolution mechanisms such as precedence or
# associativity declarations.
#
# The Generalized LR (GLR) parser, introduced by Tomita
# [^tomita1986efficient], solves this by pursuing *all* possible parse
# actions in parallel whenever a conflict arises. A conflict is no longer
# an error — it is simply a branch point. This is combined with the
# *Graph Structured Stack* (GSS) [^tomita1986efficient] that compactly
# shares common prefixes between simultaneously-live parse stacks.
#
# Similar to [Earley](/post/2021/02/06/earley-parsing/),
# [CYK](/post/2023/01/10/cyk-parser/), and
# [GLL](/post/2022/07/02/generalized-ll-parser/) parsers, the worst case
# for GLR parsing is $$ O(n^3) $$. For LR(1) grammars there are no
# conflicts, and the parse time is $$ O(n) $$.
#
# This post implements an extended version of what Tomita calls
# *Algorithm 1*. The original Algorithm 1 fails on grammars with *hidden
# right recursion* — a class of epsilon-rule grammars where a recursive
# nonterminal sits to the left of nullable nonterminals on a rule's
# right-hand side. We add a small extension (in the spirit of
# Nozohoor-Farshi [^nozohoor1991]) that handles those grammars correctly
# while keeping the rest of the algorithm intact. A different and more
# efficient solution called RNGLR (Right-Nulled GLR), which short-circuits
# nullable suffixes at parse-table construction time, is described by
# Scott and Johnstone [^scott2006rnglr]; we do not implement RNGLR here.

# ## Synopsis
#
# ```python
# import glrparser as P
# my_grammar = {
#     '<E>': [['<E>', '+', '<E>'], ['1']]
# }
# my_parser = P.compile_grammar(my_grammar, '<E>')
# for tree in my_parser.parse_on(text='1+1+1', start_symbol='<E>'):
#     print(P.format_parsetree(tree))
# ```

# ## Definitions
# For this post, we use the following terms:
#
# * The _alphabet_ is the set of all symbols in the input language. For
#   example, in this post, we use all ASCII characters as alphabet.
#
# * A _terminal_ is a single alphabet symbol. Note that this is slightly
#   different from usual definitions (done here for ease of parsing).
#
#   For example, `x` is a terminal symbol.
#
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is
#   _defined_ in the grammar.
#
#   For example, `<term>` is a nonterminal.
#
# * A _rule_ is a finite sequence of terminals and nonterminals describing
#   an expansion of a given nonterminal. Also called an _alternative_.
#
# * A _definition_ is a set of rules for a given nonterminal.
#
# * A _context-free grammar_ is composed of nonterminals and their
#   definitions.
#
# * A _parse tree_ (or _derivation tree_) describes how an input string is
#   derived from the start symbol.
#
# * A _shift_ action pushes the current input symbol and a new LR state
#   onto the parse stack. A _reduce_ action pops symbols matching a rule's
#   right-hand side and pushes the rule's left-hand side nonterminal.
#
# * A _conflict_ occurs when the parse table has more than one action for
#   a given (state, symbol) pair. Standard LR parsers fail on conflicts;
#   GLR pursues all of them in parallel.

# ## Prerequisites
# As before, we start with the prerequisite imports.
# If you are running this on the command line, please uncomment the
# following line.
#
# ```
# def __canvas__(g):
#    print(g)
# ```

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/lrparser-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and to provide utilities.
import simplefuzzer as fuzzer

# We use the `display_tree()` and `format_parsetree()` methods in earley
# parser for displaying trees.
import earleyparser as ep

# We reuse the LR infrastructure from the previous post. This gives us
# `add_start_state`, `SLR1DFA`, and related classes.
from lrparser import add_start_state, SLR1DFA

import copy
import pydot

# Since this notebook serves both as a web notebook as well as a script
# that can be run on the command line, we redefine canvas if it is not
# defined already. The `__canvas__` function is defined externally when
# it is used as a web notebook.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar
# style. Here is our running example — a simple ambiguous expression grammar.
# No conflict-free deterministic LR parse table exists for this grammar,
# because `1+1+1` is ambiguous: both `(1+1)+1` and `1+(1+1)` are valid
# parse trees.

g1 = {
    '<E>': [
        ['<E>', '+', '<E>'],
        ['1']
    ]
}
g1_start = '<E>'

# ## Review: The LR Parse Table and Conflicts
# Recall from the LR post that `SLR1DFA` builds an ACTION/GOTO table
# from the grammar. The table is a list of dicts, one per state. Each cell
# `(state, symbol)` contains a list of actions:
#
# * `sN`     — shift and go to state N
# * `r:N`    — reduce by production rule N
# * `gN`     — goto state N after a reduction (for nonterminals)
#
# Acceptance is encoded structurally: the augmented start rule is
# `<> -> <start> $`, so when the parser shifts `$` into the state that
# completes this rule and that state has no further outgoing actions, the
# input has been accepted.
#
# Let us build the table for our ambiguous grammar and observe the conflict.

if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    my_dfa = SLR1DFA(g1a, g1a_start)
    table = my_dfa.build_dfa()
    rowh = table[0]
    print('State\t', '\t'.join([repr(c) for c in rowh.keys()]))
    for i, row in enumerate(table):
        print(str(i) + '\t', '\t'.join([str(row[c]) for c in row.keys()]))
    print()

# Notice that some cells contain both `sN` and `r:N` actions — a classic
# shift/reduce conflict. A standard SLR parser would refuse to parse this
# grammar. GLR explores all branches simultaneously.

# ## Visualizing the Parse Table
# We can visualize the parse table as a graph. Shift transitions are black,
# goto transitions (after reductions) are blue. (Reductions themselves are
# not transitions and are not drawn as edges.)

def to_graph(dfa_table):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(dfa_table):
        shape = 'rectangle'
        peripheries = '1'
        G.add_node(pydot.Node(str(i), label=str(i), shape=shape,
                              peripheries=peripheries))
        for transition in state:
            cell = state[transition]
            if not cell: continue
            for action in cell:
                if not action: continue
                color = 'black'
                if action[0] == 'g':   color = 'blue'
                elif action[0] == 'r': continue   # reductions are not edges
                target = action[1:]
                if not target.isdigit(): continue
                G.add_edge(pydot.Edge(str(i), target, color=color,
                                      label=transition))
    return G

# Drawing it.

if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    my_dfa = SLR1DFA(g1a, g1a_start)
    g = to_graph(my_dfa.build_dfa())
    __canvas__(str(g))

# ## Traditional LR Parsing
# Before building the GLR parser, let us understand how a traditional LR
# parser works on a *conflict-free* grammar, so we have a clear baseline to
# generalize from.
#
# Consider this simple grammar:
#
# ```
# <S> -> <A> <B>   (rule 1)
#      | <C>        (rule 2)
# <A> -> a          (rule 3)
# <B> -> b          (rule 4)
# <C> -> c          (rule 5)
# ```

g2 = {
    '<S>': [['<A>', '<B>'], ['<C>']],
    '<A>': [['a']],
    '<B>': [['b']],
    '<C>': [['c']],
}
g2_start = '<S>'

# Its parse table looks like this.

if __name__ == '__main__':
    g2a, g2a_start = add_start_state(g2, g2_start)
    my_dfa2 = SLR1DFA(g2a, g2a_start)
    table2 = my_dfa2.build_dfa()
    rowh = table2[0]
    print('State\t', '\t'.join([repr(c) for c in rowh.keys()]))
    for i, row in enumerate(table2):
        print(str(i) + '\t', '\t'.join([str(row[c]) for c in row.keys()]))
    print()

# Each state in the table corresponds to a procedure in a traditional
# recursive LR parser. Here is what those procedures look like by hand.
# We use a list as the stack, where each entry is `(symbol, state_number)`.
# A shift pushes the symbol and target state. A reduce pops as many entries
# as there are symbols on the rule's right-hand side, then looks up the
# goto entry for the exposed state and the rule's nonterminal.
#
# Hand-unrolled LR parser corresponding to the DFA of grammar g2.

class G2TraditionalLR:
    def recognize_on(self, text):
        tokens = list(text) + ['$']
        stack  = [(None, 0)]
        return self.s0(stack, tokens)

    # State 0: S' -> . <S>
    #          <S> -> . <A> <B>
    #          <S> -> . <C>
    #          <A> -> . a
    #          <C> -> . c
    def s0(self, stack, tokens):
        symbol = tokens[0]
        if symbol == 'a':
            tokens.pop(0)
            stack.append(('a', 'sA'))
            return self.s_A(stack, tokens)
        elif symbol == 'c':
            tokens.pop(0)
            stack.append(('c', 'sC'))
            return self.s_C(stack, tokens)
        return False

    def s_A(self, stack, tokens):
        stack.pop()                        # pop 'a'
        stack.append(('<A>', 'gA'))
        return self.s_gA(stack, tokens)

    def s_gA(self, stack, tokens):
        symbol = tokens[0]
        if symbol == 'b':
            tokens.pop(0)
            stack.append(('b', 'sB'))
            return self.s_B(stack, tokens)
        return False

    def s_B(self, stack, tokens):
        stack.pop()                        # pop 'b'
        stack.append(('<B>', 'sAB'))
        return self.s_AB(stack, tokens)

    def s_AB(self, stack, tokens):
        stack.pop()                        # pop '<B>'
        stack.pop()                        # pop '<A>'
        stack.append(('<S>', 'gS'))
        return self.s_accept(stack, tokens)

    def s_C(self, stack, tokens):
        stack.pop()                        # pop 'c'
        stack.append(('<C>', 'sC_done'))
        return self.s_C_done(stack, tokens)

    def s_C_done(self, stack, tokens):
        stack.pop()                        # pop '<C>'
        stack.append(('<S>', 'gS'))
        return self.s_accept(stack, tokens)

    def s_accept(self, stack, tokens):
        return tokens[0] == '$'

# Testing it.

if __name__ == '__main__':
    p = G2TraditionalLR()
    assert     p.recognize_on('ab')
    assert     p.recognize_on('c')
    assert not p.recognize_on('abc')
    assert not p.recognize_on('ac')
    assert not p.recognize_on('')
    print('traditional LR ok')

# What happens when there is a conflict? Here is the ambiguous grammar again:
#
# ```
# <E> -> <E> + <E>
# <E> -> 1
# ```
#
# When we have parsed `<E>` and the next symbol is `+`, we face a choice:
# * *Shift* `+` (to continue building a longer `<E> + <E>`)
# * *Reduce* to `<E>` (to finish the current `<E>`)
#
# A traditional LR parser picks one and can fail. The GLR parser picks
# *both* and explores them in parallel using the Graph Structured Stack.

# ## The Graph Structured Stack
#
# The key challenge in running multiple LR parse stacks in parallel is
# efficiency. Maintaining fully independent stacks would lead to
# exponentially many of them on ambiguous grammars. The *Graph Structured
# Stack* (GSS) solves this by sharing stack prefixes wherever possible.
#
# Two complementary sharing rules operate on the GSS:
#
# 1. Whenever two parse stacks reach the same LR state at the same input
#    position, the algorithm merges them into a single GSS node. This is
#    why the GSS is a graph rather than a tree of stacks.
#
# 2. When a reduction at one input position would produce an edge into a
#    state that already exists, the new edge is added to the existing
#    node — possibly making the GSS cyclic. We will see exactly when this
#    happens, in the section on hidden left recursion below.
#
# The GSS is a directed graph. Its nodes alternate between two kinds:
#
# * *State nodes* carry an LR automaton state number. They represent the
#   top of a live parse stack at a particular input position.
# * *Symbol nodes* carry a grammar symbol (terminal or nonterminal). They
#   sit between state nodes and record what symbol was shifted or reduced
#   to arrive at the next state.
#
# Edges always point toward the *bottom* of the stack. So an edge from
# state node `u` through symbol node `z` to state node `v` means: "we
# arrived at state `u` after recognising `z` on top of state `v`."
# In this alternating-node representation, popping `k` grammar symbols
# means following `2k` edges in the GSS (alternating symbol→state,
# `k` times). Because the GSS may have multiple parallel edges leaving a
# single state node, "popping `k` symbols" is not a single sequence — it
# is a search for all paths of length `2k`. This search is the central
# expensive operation of the algorithm.

# ### GSSNode

class GSSNode:
    def __init__(self, is_state, state=-1, symbol=''):
        self.is_state  = is_state   # True = state node, False = symbol node
        self.state     = state      # LR state number  (state nodes only)
        self.symbol    = symbol     # grammar symbol   (symbol nodes only)
        self.successors = []        # edges toward bottom of stack

    def add_successor(self, node):
        self.successors.append(node)

    def __repr__(self):
        if self.is_state:
            return 'State(%d)' % self.state
        else:
            return 'Sym(%s)' % self.symbol

# ### GSS

class GSS:
    def __init__(self):
        self._counter = 0
        self.nodes    = {}   # id -> GSSNode

    def create_node(self, is_state, state=-1, symbol=''):
        node = GSSNode(is_state, state, symbol)
        self.nodes[self._counter] = node
        self._counter += 1
        return node

    def add_edge(self, from_node, to_node):
        from_node.add_successor(to_node)

# Let us verify the basic structure.

if __name__ == '__main__':
    gss = GSS()
    v0 = gss.create_node(is_state=True,  state=0)
    z  = gss.create_node(is_state=False, symbol='1')
    v1 = gss.create_node(is_state=True,  state=2)
    gss.add_edge(v1, z)
    gss.add_edge(z, v0)
    assert v1.successors == [z]
    assert z.successors  == [v0]
    print('GSS basic structure ok')

# ### Traversing the GSS at a given depth
# A key operation in GLR is: starting from a node, find all state nodes
# reachable by following exactly `depth` successor edges. This is how we
# "pop" the stack during a reduction — if the rule has `k` symbols on its
# right-hand side, we follow `2k` edges (symbol then state, `k` times).
# Because the GSS may be cyclic, we memoize by `(node, remaining-depth)`
# so we never expand the same subproblem twice.

class GSS(GSS):
    def dfs(self, node, depth, memo=None):
        if memo is None: memo = {}
        key = (id(node), depth)
        if key in memo: return memo[key]
        if depth == 0:
            result = {node}
            memo[key] = result
            return result
        result = set()
        for succ in node.successors:
            result |= self.dfs(succ, depth - 1, memo)
        memo[key] = result
        return result

    def find_nodes_at_depth(self, node, depth):
        return self.dfs(node, depth)

    def path_exists(self, start, end, depth):
        return end in self.find_nodes_at_depth(start, depth)

# Testing the traversal.

if __name__ == '__main__':
    gss = GSS()
    v0 = gss.create_node(is_state=True, state=0)
    z0 = gss.create_node(is_state=False, symbol='1')
    v1 = gss.create_node(is_state=True, state=2)
    z1 = gss.create_node(is_state=False, symbol='<E>')
    v2 = gss.create_node(is_state=True, state=3)
    gss.add_edge(v1, z0); gss.add_edge(z0, v0)
    gss.add_edge(v2, z1); gss.add_edge(z1, v1)
    assert gss.find_nodes_at_depth(v2, 0) == {v2}
    assert gss.find_nodes_at_depth(v2, 2) == {v1}
    assert gss.find_nodes_at_depth(v2, 4) == {v0}
    print('GSS traversal ok')

# ## The GLR Recognizer
#
# The algorithm processes input one symbol at a time. For each input
# position `i` it maintains `U[i]`, a list of active state nodes — all
# nodes that represent live parse stacks that have consumed exactly `i`
# input symbols.
#
# Three worklists drive the algorithm at each position:
#
# * `A` — active state nodes still to be examined by the *actor*
# * `R` — pending reductions `(v, x, rule_num)` for the *reducer*
# * `Q` — pending shifts `(v, target_state)` for the *shifter*
#
# The loop at position `i` is: run actor + reducer until quiescent, then
# run the shifter once to advance to position `i+1`.

# ### Initialization

class GLRRecognizer:
    def __init__(self, grammar, parse_table, production_rules):
        self.grammar          = grammar
        self.parse_table      = parse_table       # dict: state -> symbol -> [actions]
        self.production_rules = production_rules  # dict: ruleN -> (lhs, rhs)

    def setup(self, text):
        self.input_string = list(text) + ['$']
        self.gss          = GSS()
        root = self.gss.create_node(is_state=True, state=0)
        self.U            = {0: [root]}
        self.accepted     = False
        # Track per-reduction reach: maps (id(v), id(x), rule_num) to the
        # set of `w` nodes that the reduction has already processed.
        # This is what allows us to safely re-fire reductions after the
        # GSS grows new edges, while still terminating on hidden left
        # recursion. See "Hidden Right Recursion" below for details.
        self.last_fired_reach = {}

# ### Actor
# The actor examines active state node `v` against the current input symbol.
# For each action in the table it enqueues the appropriate follow-up:
# shifts go into `Q`, reductions into `R`.
#
# One subtlety: when we queue a reduction `(v, x, rule_num)`, `x` is the
# first *symbol node* below `v` on the stack. We find it by looking at
# `v`'s successors. Because multiple GSS nodes may share the same LR
# state (merged stacks from earlier positions), we search all nodes with
# `state == v.state` and queue all of their outgoing symbol edges.
#
# Acceptance is detected by checking, on a shift of `$`, whether the
# target state has no further actions. That target state corresponds to
# the augmented rule `<> -> <start> $ .` being complete.

class GLRRecognizer(GLRRecognizer):
    def actor(self, v, symbol, i, Q, R):
        state   = v.state
        actions = self.parse_table[state].get(symbol, [])
        for operation in actions:
            if not operation:
                continue
            if operation[0] == 's':
                target = int(operation[1:])
                Q.append((v, target))
                if symbol == '$' and all(
                        not acts for acts in self.parse_table[target].values()):
                    self.accepted = True
            elif operation[0] == 'r':
                rule_num = operation
                _lhs, rhs = self.production_rules[rule_num]
                if len(rhs) == 0:
                    # Epsilon rule: no symbol node to traverse.
                    R.append((v, None, rule_num))
                else:
                    for node in self.U[i]:
                        if node.is_state and node.state == state:
                            for x in node.successors:
                                R.append((node, x, rule_num))

# ### Reducer
# The reducer processes one pending `(v, x, rule_num)` triple. `x` is
# the first symbol node below `v`. The rule has `k` symbols on its RHS.
# In the GSS, each symbol accounts for two edges (symbol node + state
# node), so we find all state nodes at depth `2k - 1` from `x` — these
# are the nodes `w` that sit below the entire right-hand side.
#
# For each such `w`, we compute `goto(w.state, lhs)` to find the new
# state `s`, then either reuse an existing node for `(s, i)` or create a
# new one. There are two subtleties:
#
# 1. We may have already processed some `w` nodes in a previous firing
#    of this same `(v, x, rule_num)` triple. We track those in
#    `last_fired_reach` and only process newly-reachable `w` nodes.
#
# 2. When we add a new GSS edge between two existing nodes, that edge
#    may enable previously-impossible reductions in *other* active state
#    nodes. We re-enqueue every applicable reduction in `U[i]`; the
#    reach tracker from (1) prevents us from doing duplicate work.
#
# Together these two rules make the algorithm correct on grammars with
# hidden right recursion. The section "Hidden Right Recursion" below
# walks through why both are necessary.

class GLRRecognizer(GLRRecognizer):
    def reducer(self, v, x, rule_num, i, A, R):
        lhs, rhs = self.production_rules[rule_num]
        k        = len(rhs)
        symbol   = self.input_string[i]

        # Find all state nodes below the k-symbol right-hand side.
        if k == 0:
            all_w = frozenset({v})       # epsilon: w is v itself
        else:
            all_w = self.gss.find_nodes_at_depth(x, 2 * k - 1)

        # Skip if we've already processed this exact set of w nodes for
        # this (v, x, rule) triple. If the set has grown, only process
        # the new w's.
        key = (id(v), id(x), rule_num)
        prev = self.last_fired_reach.get(key)
        if prev is not None and all_w <= prev:
            return
        self.last_fired_reach[key] = all_w if prev is None else (prev | all_w)
        new_ws = all_w if prev is None else (all_w - prev)

        edge_added = False
        for w in new_ws:
            # Compute goto(w.state, lhs).
            goto_actions = self.parse_table[w.state].get(lhs, [])
            s = None
            for op in goto_actions:
                if op and op[0] == 'g':
                    s = int(op[1:])
            if s is None:
                continue

            # Does a state node for s already exist in U[i]?
            existing_u = None
            for u in self.U[i]:
                if u.state == s:
                    existing_u = u
                    break

            if existing_u is not None:
                u = existing_u
                # If the edge u -> w already exists, nothing to do.
                if self.gss.path_exists(u, w, 2):
                    continue
                # New edge: connect u -> symbol_node -> w.
                z = self.gss.create_node(is_state=False, symbol=lhs)
                self.gss.add_edge(u, z)
                self.gss.add_edge(z, w)
                edge_added = True
            else:
                # Create a fresh state node and connect it.
                u = self.gss.create_node(is_state=True, state=s)
                z = self.gss.create_node(is_state=False, symbol=lhs)
                self.gss.add_edge(u, z)
                self.gss.add_edge(z, w)
                A.append(u)
                self.U[i].append(u)

        if edge_added:
            # A new GSS edge has been added between existing nodes. Any
            # reduction in U[i] whose pop path could now go through this
            # new edge must be re-enqueued. The reach tracker above will
            # discard duplicates and only do work for newly-reachable w's.
            for t in list(self.U[i]):
                if not t.is_state:
                    continue
                for op in self.parse_table[t.state].get(symbol, []):
                    if not op or op[0] != 'r':
                        continue
                    _lhs2, rhs2 = self.production_rules[op]
                    if len(rhs2) == 0:
                        R.append((t, None, op))
                    else:
                        for x2 in t.successors:
                            R.append((t, x2, op))

# ### Shifter
# Once all reductions at position `i` are done, we consume input symbol
# `i`. For every `(v, s)` in `Q`, we build a new state node for state `s`
# at position `i+1` and add the appropriate symbol edge for the terminal.
# Multiple stacks that shift into the same state are merged into one node.

class GLRRecognizer(GLRRecognizer):
    def shifter(self, Q, i):
        terminal = self.input_string[i]
        by_state = {}
        for v, s in Q:
            by_state.setdefault(s, []).append(v)

        next_i = i + 1
        if next_i not in self.U:
            self.U[next_i] = []

        for s, predecessors in by_state.items():
            w = self.gss.create_node(is_state=True, state=s)
            self.U[next_i].append(w)
            for v in predecessors:
                z = self.gss.create_node(is_state=False, symbol=terminal)
                self.gss.add_edge(w, z)
                self.gss.add_edge(z, v)

# ### The main recognition loop

class GLRRecognizer(GLRRecognizer):
    def recognize_on(self, text, start_symbol):
        self.setup(text)
        n = len(text)
        for i in range(n + 1):
            symbol = self.input_string[i]
            # Reset the per-position reach tracker.
            self.last_fired_reach = {}
            A = list(self.U.get(i, []))
            Q = []
            R = []
            while A or R:
                while A:
                    v = A.pop(0)
                    self.actor(v, symbol, i, Q, R)
                while R:
                    v, x, rule_num = R.pop(0)
                    self.reducer(v, x, rule_num, i, A, R)
            if self.accepted:
                return True
            if i < n:
                self.shifter(Q, i)
        return self.accepted

# ### Testing the recognizer
# We need a small adapter because `SLR1DFA.build_dfa()` returns a list of
# dicts keyed by symbol strings with list-of-action-strings as values.
# We simply wrap it in a dict indexed by state number.

def make_parse_table(dfa_table):
    return {i: row for i, row in enumerate(dfa_table)}

# Testing on our ambiguous grammar.

if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    my_dfa = SLR1DFA(g1a, g1a_start)
    parse_table      = make_parse_table(my_dfa.build_dfa())
    production_rules = my_dfa.production_rules
    recognizer = GLRRecognizer(g1a, parse_table, production_rules)
    assert     recognizer.recognize_on('1',       g1a_start)
    assert     recognizer.recognize_on('1+1',     g1a_start)
    assert     recognizer.recognize_on('1+1+1',   g1a_start)
    assert not recognizer.recognize_on('1+',      g1a_start)
    assert not recognizer.recognize_on('+1',      g1a_start)
    assert not recognizer.recognize_on('',        g1a_start)
    print('recognizer on ambiguous grammar ok')

# Let us also verify with an unambiguous grammar.

if __name__ == '__main__':
    g2 = {
        '<E>': [['<D>', '+', '<E>'], ['<D>']],
        '<D>': [['1']]
    }
    g2a, g2a_start = add_start_state(g2, '<E>')
    my_dfa2 = SLR1DFA(g2a, g2a_start)
    rec2 = GLRRecognizer(g2a,
                         make_parse_table(my_dfa2.build_dfa()),
                         my_dfa2.production_rules)
    assert     rec2.recognize_on('1',     g2a_start)
    assert     rec2.recognize_on('1+1',   g2a_start)
    assert     rec2.recognize_on('1+1+1', g2a_start)
    assert not rec2.recognize_on('1+',    g2a_start)
    print('recognizer on unambiguous grammar ok')

# ### A worked example: a different shift/reduce conflict
# Following Smits[^smits2025glr] (his adaptation of grammar 4.1 from
# Economopoulos's dissertation[^economopoulos2006glr]), here is a small
# grammar that exhibits a shift/reduce conflict without left recursion:
#
# ```
# <E> -> a b <C>
# <E> -> a <B> <C>
# <B> -> b
# <C> -> d e
# ```
#
# After reading `a b`, the parser is at a state where `b` can either be
# shifted as the literal `b` of the first rule, or reduced to `<B>` for
# the second rule. The input `abde` has *two* parse trees — one where
# `b` is a literal, and one where `b` is the body of `<B>`.

if __name__ == '__main__':
    g_smits_41 = {
        '<E>': [['a', 'b', '<C>'], ['a', '<B>', '<C>']],
        '<B>': [['b']],
        '<C>': [['d', 'e']],
    }
    aug_g, aug_start = add_start_state(g_smits_41, '<E>')
    dfa = SLR1DFA(aug_g, aug_start)
    rec = GLRRecognizer(aug_g, make_parse_table(dfa.build_dfa()),
                        dfa.production_rules)
    assert     rec.recognize_on('abde', aug_start)
    assert not rec.recognize_on('ab',   aug_start)
    print('Smits grammar 4.1 recognizer ok')

# ### A worked example: hidden left recursion
# Hidden left recursion arises when a rule's first non-terminal is
# nullable, so the rule can reach itself without consuming input. The
# canonical small example is:
#
# ```
# <E> -> <B> <E> a
# <E> -> b
# <B> -> ε
# ```
#
# The language is `b a*`. Parsing this in GLR requires the GSS to grow a
# self-loop on the state that completes `<E>` from `<B> <E> a`, because
# the reducer keeps re-entering the same configuration. Our recognizer
# handles this correctly:

if __name__ == '__main__':
    g_hidden_left = {
        '<E>': [['<B>', '<E>', 'a'], ['b']],
        '<B>': [[]],
    }
    aug_g, aug_start = add_start_state(g_hidden_left, '<E>')
    dfa = SLR1DFA(aug_g, aug_start)
    rec = GLRRecognizer(aug_g, make_parse_table(dfa.build_dfa()),
                        dfa.production_rules)
    for s in ['b', 'ba', 'baa', 'baaa']:
        assert rec.recognize_on(s, aug_start), 'should accept %r' % s
    assert not rec.recognize_on('a',  aug_start)
    assert not rec.recognize_on('',   aug_start)
    print('hidden-left-recursion recognizer ok')

# ## GLR Parser
# A recognizer tells us only whether a string is in the language. To
# extract parse trees we augment the GSS so that every symbol node also
# carries a *tree fragment* — the partial parse tree for the symbol it
# represents. Terminals carry leaf nodes; nonterminals carry the tree
# built during the reduction that created them.
#
# When the same symbol edge connects the same pair of state nodes via
# more than one derivation (as happens in genuinely ambiguous grammars),
# the symbol node carries multiple tree fragments — one per distinct
# derivation. The reducer collects all of them when assembling new
# parse trees.

# ### GSSNodeP — GSS node with a tree payload

class GSSNodeP(GSSNode):
    def __init__(self, is_state, state=-1, symbol='', tree=None):
        super().__init__(is_state, state, symbol)
        # A sym node can carry multiple trees (one per distinct derivation).
        self.trees = [] if tree is None else [tree]

# ### GSSP — GSS that creates GSSNodeP nodes

class GSSP(GSS):
    def create_node(self, is_state, state=-1, symbol='', tree=None):
        node = GSSNodeP(is_state, state, symbol, tree)
        self.nodes[self._counter] = node
        self._counter += 1
        return node

# ### Collecting trees along a pop path
# When the reducer pops `k` symbols, it traverses `k` pairs of edges
# (state→symbol→state). Each symbol node along the way carries one or
# more child trees. We collect all such paths from a given state node,
# yielding every `(bottom_state_node, [child_trees])` pair across all
# combinations of stored derivations.
#
# Invariant: the GSS strictly alternates state nodes and symbol nodes.
# Every edge created by `shifter()` and `reducer()` respects this
# structure, which is what makes `collect_paths` correct without
# additional checking.

def collect_paths(node, k, memo=None):
    """
    Yield (bottom_node, [child_tree, ...]) for every path of k steps
    from `node`, where one step = follow one symbol edge + one state edge.
    Trees are returned in order from outermost (top of stack) inward.
    """
    if memo is None: memo = {}
    key = (id(node), k)
    if key in memo: return memo[key]
    if k == 0:
        result = [(node, [])]
        memo[key] = result
        return result
    result = []
    for sym_node in node.successors:          # state  -> symbol
        for state_node in sym_node.successors: # symbol -> state
            for tree in sym_node.trees:        # each distinct derivation
                for (bottom, frags) in collect_paths(state_node, k - 1, memo):
                    result.append((bottom, [tree] + frags))
    memo[key] = result
    return result

# Testing `collect_paths`.

if __name__ == '__main__':
    gp = GSSP()
    v0 = gp.create_node(is_state=True,  state=0)
    z0 = gp.create_node(is_state=False, symbol='1',   tree=('1',   []))
    v1 = gp.create_node(is_state=True,  state=2)
    z1 = gp.create_node(is_state=False, symbol='<D>', tree=('<D>', [('1', [])]))
    v2 = gp.create_node(is_state=True,  state=4)
    gp.add_edge(v1, z0); gp.add_edge(z0, v0)
    gp.add_edge(v2, z1); gp.add_edge(z1, v1)
    paths = collect_paths(v2, 1)
    assert len(paths) == 1
    bottom, frags = paths[0]
    assert bottom is v1
    assert frags == [('<D>', [('1', [])])]
    print('collect_paths ok')

# ### GLRParser
# The parser subclasses the recognizer and overrides `setup`, `actor`,
# `reducer`, and `shifter` to carry tree fragments through the GSS.

class GLRParser(GLRRecognizer):
    def setup(self, text):
        self.input_string = list(text) + ['$']
        self.gss          = GSSP()
        root = self.gss.create_node(is_state=True, state=0)
        self.U            = {0: [root]}
        self.accepted     = False
        self.parse_trees  = []
        self.last_fired_reach = {}

# ### Actor (parser version)
# Identical to the recognizer's version, except that we use `GSSP` nodes
# (which carry tree payloads on their symbol edges) implicitly via the
# superclass.

class GLRParser(GLRParser):
    def actor(self, v, symbol, i, Q, R):
        state   = v.state
        actions = self.parse_table[state].get(symbol, [])
        for operation in actions:
            if not operation:
                continue
            if operation[0] == 's':
                target = int(operation[1:])
                Q.append((v, target))
                if symbol == '$' and all(
                        not acts for acts in self.parse_table[target].values()):
                    self.accepted = True
                    # Trees are harvested at the end of parse_on, once all
                    # reductions at position n have completed.
            elif operation[0] == 'r':
                rule_num  = operation
                _lhs, rhs = self.production_rules[rule_num]
                if len(rhs) == 0:
                    R.append((v, None, rule_num))
                else:
                    for node in self.U[i]:
                        if node.is_state and node.state == state:
                            for x in node.successors:
                                R.append((node, x, rule_num))

# ### Reducer (parser version)
# The reducer is the same as the recognizer's version except that it
# assembles a parse tree node from the children collected along the pop
# path, and attaches that tree to every new symbol node it creates. When
# an existing symbol edge would receive a new derivation, we append the
# new tree to that symbol node's list of trees rather than creating a
# duplicate edge.
#
# Like the recognizer, the parser must handle hidden right recursion.
# We track which `(v, x, rule_num)` triples have already processed which
# pop paths (identified by bottom node + sequence of tree fragment ids),
# and re-fire all applicable reductions whenever a new GSS edge appears.

class GLRParser(GLRParser):
    def reducer(self, v, x, rule_num, i, A, R):
        lhs, rhs = self.production_rules[rule_num]
        k        = len(rhs)
        symbol   = self.input_string[i]

        if k == 0:
            all_paths = [(v, [])]
        else:
            all_paths = collect_paths(v, k)

        # Track which paths we have already processed for this triple.
        # Each path is keyed by (bottom-node-id, tuple of tree-fragment ids).
        key = (id(v), id(x), rule_num)
        prev_keys = self.last_fired_reach.setdefault(key, set())
        new_paths = []
        for (w, children) in all_paths:
            path_key = (id(w), tuple(id(t) for t in children))
            if path_key in prev_keys:
                continue
            prev_keys.add(path_key)
            new_paths.append((w, children))

        edge_added = False
        for (w, children) in new_paths:
            # collect_paths returns children outermost-first (top-of-stack
            # first); reverse to get the left-to-right order of the RHS.
            new_tree = (lhs, list(reversed(children)))

            goto_actions = self.parse_table[w.state].get(lhs, [])
            s = None
            for op in goto_actions:
                if op and op[0] == 'g':
                    s = int(op[1:])
            if s is None:
                continue

            existing_u = None
            for u in self.U[i]:
                if u.state == s:
                    existing_u = u
                    break

            if existing_u is not None:
                u = existing_u
                # Find an existing sym node on the path u -> ? -> w.
                z_existing = next(
                    (z for z in u.successors if w in z.successors), None)
                if z_existing is not None:
                    # Path exists; record a new derivation on the same edge.
                    if new_tree not in z_existing.trees:
                        z_existing.trees.append(new_tree)
                        edge_added = True
                else:
                    z = self.gss.create_node(is_state=False, symbol=lhs,
                                             tree=new_tree)
                    self.gss.add_edge(u, z)
                    self.gss.add_edge(z, w)
                    edge_added = True
            else:
                u = self.gss.create_node(is_state=True, state=s)
                z = self.gss.create_node(is_state=False, symbol=lhs,
                                         tree=new_tree)
                self.gss.add_edge(u, z)
                self.gss.add_edge(z, w)
                A.append(u)
                self.U[i].append(u)

        if edge_added:
            # A new GSS edge or new tree has been recorded. Re-enqueue
            # every applicable reduction in U[i]; the reach tracker
            # above will discard duplicate work.
            for t in list(self.U[i]):
                if not t.is_state:
                    continue
                for op in self.parse_table[t.state].get(symbol, []):
                    if not op or op[0] != 'r':
                        continue
                    _lhs2, rhs2 = self.production_rules[op]
                    if len(rhs2) == 0:
                        R.append((t, None, op))
                    else:
                        for x2 in t.successors:
                            R.append((t, x2, op))

# ### Shifter (parser version)
# The shifter creates terminal leaf nodes as tree fragments when it
# creates new symbol edges.

class GLRParser(GLRParser):
    def shifter(self, Q, i):
        terminal      = self.input_string[i]
        terminal_tree = (terminal, [])
        by_state      = {}
        for v, s in Q:
            by_state.setdefault(s, []).append(v)

        next_i = i + 1
        if next_i not in self.U:
            self.U[next_i] = []

        for s, predecessors in by_state.items():
            w = self.gss.create_node(is_state=True, state=s)
            self.U[next_i].append(w)
            for v in predecessors:
                z = self.gss.create_node(is_state=False, symbol=terminal,
                                         tree=terminal_tree)
                self.gss.add_edge(w, z)
                self.gss.add_edge(z, v)

# ### The main parse loop

class GLRParser(GLRParser):
    def parse_on(self, text, start_symbol):
        self.setup(text)
        n = len(text)
        for i in range(n + 1):
            symbol = self.input_string[i]
            # Reset the per-position reach tracker.
            self.last_fired_reach = {}
            A = list(self.U.get(i, []))
            Q = []
            R = []
            while A or R:
                while A:
                    v = A.pop(0)
                    self.actor(v, symbol, i, Q, R)
                while R:
                    v, x, rule_num = R.pop(0)
                    self.reducer(v, x, rule_num, i, A, R)
            if i < n:
                self.shifter(Q, i)
        # Collect all trees from every accepting state node at position n.
        # This is done after the loop so all reductions are complete and
        # every sym node has its full trees list populated.
        for v in self.U.get(n, []):
            for op in self.parse_table[v.state].get('$', []):
                if op and op[0] == 's':
                    target = int(op[1:])
                    if all(not acts for acts in self.parse_table[target].values()):
                        for sym_node in v.successors:
                            for tree in sym_node.trees:
                                if tree not in self.parse_trees:
                                    self.parse_trees.append(tree)
        return self.parse_trees

# ### Testing the parser
# Let us start with an unambiguous string.

if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    my_dfa = SLR1DFA(g1a, g1a_start)
    parse_table      = make_parse_table(my_dfa.build_dfa())
    production_rules = my_dfa.production_rules
    parser = GLRParser(g1a, parse_table, production_rules)

    trees = parser.parse_on('1', g1a_start)
    assert len(trees) >= 1
    assert fuzzer.tree_to_string(trees[0]) == '1'
    ep.display_tree(trees[0])
    print('parse "1" ok, %d tree(s)' % len(trees))

# Now the ambiguous string `1+1+1`. We expect two parse trees.

if __name__ == '__main__':
    trees = parser.parse_on('1+1+1', g1a_start)
    print('parse "1+1+1": %d tree(s)' % len(trees))
    for t in trees:
        assert fuzzer.tree_to_string(t) == '1+1+1'
        ep.display_tree(t)
    assert len(trees) == 2

# And on Smits's grammar 4.1, the input `abde` should produce two trees:

if __name__ == '__main__':
    g_smits_41 = {
        '<E>': [['a', 'b', '<C>'], ['a', '<B>', '<C>']],
        '<B>': [['b']],
        '<C>': [['d', 'e']],
    }
    aug_g, aug_start = add_start_state(g_smits_41, '<E>')
    dfa = SLR1DFA(aug_g, aug_start)
    parser = GLRParser(aug_g, make_parse_table(dfa.build_dfa()),
                       dfa.production_rules)
    trees = parser.parse_on('abde', aug_start)
    assert len(trees) == 2
    for t in trees: assert fuzzer.tree_to_string(t) == 'abde'
    print('Smits grammar 4.1 parser ok, %d tree(s) for "abde"' % len(trees))

# ## Compiling a Grammar
# To match the interface used in the GLL post, we provide a
# `compile_grammar` function that returns a parser with a
# `parse_on(text, start_symbol)` method.

class CompiledGLRParser:
    def __init__(self, grammar, start):
        aug_g, aug_start    = add_start_state(grammar, start)
        dfa                 = SLR1DFA(aug_g, aug_start)
        self._parse_table   = make_parse_table(dfa.build_dfa())
        self._prod_rules    = dfa.production_rules
        self._aug_g         = aug_g
        self._aug_start     = aug_start
        self._parser        = GLRParser(aug_g, self._parse_table,
                                        self._prod_rules)

    def parse_on(self, text, start_symbol):
        return self._parser.parse_on(text, self._aug_start)

def compile_grammar(grammar, start):
    return CompiledGLRParser(grammar, start)

# Using it.

if __name__ == '__main__':
    my_grammar = {'<E>': [['<E>', '+', '<E>'], ['1']]}
    my_parser = compile_grammar(my_grammar, '<E>')
    for tree in my_parser.parse_on(text='1+1+1', start_symbol='<E>'):
        print(ep.format_parsetree(tree))

# ## More Examples
# ### 1 — A right-recursive grammar

if __name__ == '__main__':
    RR_GRAMMAR = {
        '<start>': [['<A>']],
        '<A>':     [['a', '<A>'], []]
    }
    p = compile_grammar(RR_GRAMMAR, '<start>')
    for mystr in ['', 'a', 'aa', 'aaa']:
        trees = p.parse_on(mystr, '<start>')
        assert trees, 'no trees for: ' + repr(mystr)
        for t in trees:
            assert fuzzer.tree_to_string(t) == mystr
        print('"%s" -> %d tree(s)' % (mystr, len(trees)))

# ### 2 — A left-recursive grammar

if __name__ == '__main__':
    LR_GRAMMAR = {
        '<start>': [['<A>']],
        '<A>':     [['<A>', 'a'], []]
    }
    p = compile_grammar(LR_GRAMMAR, '<start>')
    for mystr in ['', 'a', 'aa', 'aaa']:
        trees = p.parse_on(mystr, '<start>')
        assert trees, 'no trees for: ' + repr(mystr)
        for t in trees:
            assert fuzzer.tree_to_string(t) == mystr
        print('"%s" -> %d tree(s)' % (mystr, len(trees)))

# ### 3 — Arithmetic (ambiguous without precedence)

if __name__ == '__main__':
    arith_grammar = {
        '<E>': [
            ['<E>', '+', '<E>'],
            ['<E>', '*', '<E>'],
            ['(', '<E>', ')'],
            ['a']
        ]
    }
    p = compile_grammar(arith_grammar, '<E>')
    for mystr, expected_min in [('a', 1), ('a+a', 1), ('a*a', 1),
                                  ('a+a*a', 2), ('a+a+a', 2)]:
        trees = p.parse_on(mystr, '<E>')
        assert len(trees) >= expected_min, \
            'expected >= %d trees for %s, got %d' % (expected_min, mystr, len(trees))
        for t in trees:
            assert fuzzer.tree_to_string(t) == mystr
        print('%s -> %d parse tree(s)' % (mystr, len(trees)))

# ### 4 — The γ₂ torture-test grammar from the GLL post

if __name__ == '__main__':
    gamma_2 = {
        '<S>':  [['<S3>'], ['<S2>'], ['x']],
        '<S3>': [['<Sx>', '<Sx>', '<Sx>']],
        '<S2>': [['<S>', '<S>']],
        '<Sx>': [['<S2>'], ['<S3>'], ['x']],
    }
    p = compile_grammar(gamma_2, '<S>')
    trees = p.parse_on('xxxx', '<S>')
    assert trees
    for t in trees:
        assert fuzzer.tree_to_string(t) == 'xxxx'
    print('gamma_2 "xxxx" -> %d tree(s)' % len(trees))

# ## Utilities

def format_parsetree(t):
    return ep.format_parsetree(t)

# ## Hidden Right Recursion
#
# Earlier we mentioned that the `reducer` does two things to keep the
# algorithm correct on grammars with hidden right recursion:
#
# 1. It tracks which `(v, x, rule_num)` triples have already processed
#    which `w` nodes, and only does work on newly-reachable `w`s.
# 2. When it adds a new GSS edge between existing nodes, it re-enqueues
#    every applicable reduction in `U[i]`.
#
# This subsection explains *why* both rules are necessary, using the
# canonical example from Smits [^smits2025glr] (his adaptation of
# grammar 4.2 from Economopoulos [^economopoulos2006glr]):
#
# ```
# <E> -> a <E> <B> <B>
# <E> -> b
# <B> -> ε
# <B> -> c
# ```
#
# This grammar describes the language `{ a^n b c^k : 0 ≤ k ≤ 2n }`.
# Recursion is *hidden* in the first rule because the recursive call to
# `<E>` sits to the left of two nullable `<B>` occurrences. On input
# `aab`, the parse must reduce `<E> -> a <E> <B> <B>` *twice in a row*,
# first popping back to the inner `a`, then again popping back to the
# outermost state.
#
# Without rule (2), the second reduction never fires. Here is the
# sequence: after shifting `a`, `a`, `b`, the parser reduces `<E> -> b`
# (producing a new state node for the goto of `<E>` from the second
# `a`'s state), then reduces `<B> -> ε` twice in succession (anticipating
# the trailing two `<B>`s). It now reaches a state where `<E> -> a<E>BB`
# completes. This reduction pops 7 GSS edges and lands at the GSS node
# for the *inner* `a`'s state. Goto on `<E>` from there is the same
# state as the one we are currently in — so a *new GSS edge* is added
# between two existing nodes. Without rule (2), we never re-fire the
# reductions that would now find a longer pop path through this new
# edge. With rule (2), we re-enqueue `<E> -> a<E>BB` on the topmost
# state, and rule (1) ensures we only do new work (the longer pop path
# is a new `w`).
#
# Without rule (1), the algorithm does not terminate on hidden *left*
# recursion. The hidden-left grammar `<E> -> <B><E>a | b; <B> -> ε`
# requires the GSS to grow a cycle through the `<B>` epsilon reduction.
# Every time we re-fire `<B> -> ε`, rule (2) would add another copy of
# the same edge. Rule (1) prevents that, because `w = v` for an epsilon
# rule and the reach tracker remembers `v` was processed.
#
# Let us verify that the implementation handles all of these correctly.

if __name__ == '__main__':
    # Hidden right recursion: aab requires two consecutive E -> aEBB
    # reductions and Algorithm 1 alone fails on this.
    g_hidden_right = {
        '<E>': [['a', '<E>', '<B>', '<B>'], ['b']],
        '<B>': [[], ['c']],
    }
    p = compile_grammar(g_hidden_right, '<E>')
    for s in ['b', 'ab', 'abc', 'abcc', 'aab', 'aabc', 'aabcc',
              'aaab', 'aaabcc']:
        trees = p.parse_on(s, '<E>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    # Not in the language: too many c's (k > 2n).
    assert not p.parse_on('abccc',    '<E>')
    assert not p.parse_on('aabccccc', '<E>')
    print('hidden right recursion ok')

# An efficient and well-studied alternative to the runtime fix above is
# *Right-Nulled GLR* (RNGLR) [^scott2006rnglr][^scott2003rnglr], in
# which "right-nulled" prefixes of rules are short-circuited as extra
# reduce actions at parse-table construction time. RNGLR avoids most
# of the re-fire work the runtime fix does, at the cost of more complex
# table construction. The runtime fix here is simpler to implement and
# correct on all the same grammars.

# ## More Hidden-Recursion Examples
# A few more grammars exercising the hidden-recursion edge cases.

# ### Nullable nonterminals on both sides

if __name__ == '__main__':
    # E -> X E Y a | b; X, Y -> ε. Both X and Y are nullable, hiding
    # both left and right recursion in the first rule.
    g_both = {
        '<E>': [['<X>', '<E>', '<Y>', 'a'], ['b']],
        '<X>': [[]],
        '<Y>': [[]],
    }
    p = compile_grammar(g_both, '<E>')
    for s in ['b', 'ba', 'baa', 'baaa']:
        trees = p.parse_on(s, '<E>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    assert not p.parse_on('a',  '<E>')
    assert not p.parse_on('',   '<E>')
    print('hidden-recursion both sides ok')

# ### Multiple nullable suffixes

if __name__ == '__main__':
    # E -> a E B B B | b; B -> ε | c. Like the canonical example but
    # with three trailing B's instead of two.
    g_three = {
        '<E>': [['a', '<E>', '<B>', '<B>', '<B>'], ['b']],
        '<B>': [[], ['c']],
    }
    p = compile_grammar(g_three, '<E>')
    for s in ['b', 'ab', 'aab', 'abc', 'aabccc', 'aabcccccc']:
        trees = p.parse_on(s, '<E>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    print('hidden right recursion (3 nullable suffixes) ok')

# ### Indirect hidden recursion

if __name__ == '__main__':
    # E -> a F B B | b; F -> E; B -> ε. The recursion is hidden through
    # an intermediate nonterminal F.
    g_indirect = {
        '<E>': [['a', '<F>', '<B>', '<B>'], ['b']],
        '<F>': [['<E>']],
        '<B>': [[]],
    }
    p = compile_grammar(g_indirect, '<E>')
    for s in ['b', 'ab', 'aab', 'aaab']:
        trees = p.parse_on(s, '<E>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    print('indirect hidden right recursion ok')

# ### The cyclic grammar
# Cycles in the grammar (rules where a nonterminal derives itself
# without consuming input) push on a different part of the algorithm.

if __name__ == '__main__':
    # E -> EE | a | ε. Highly ambiguous; produces many parse trees for
    # short strings. We only verify recognition here because the number
    # of trees grows quickly.
    g_cyc = {
        '<E>': [['<E>', '<E>'], ['a'], []],
    }
    aug_g, aug_start = add_start_state(g_cyc, '<E>')
    dfa = SLR1DFA(aug_g, aug_start)
    rec = GLRRecognizer(aug_g, make_parse_table(dfa.build_dfa()),
                        dfa.production_rules)
    for s in ['', 'a', 'aa', 'aaa', 'aaaa']:
        assert rec.recognize_on(s, aug_start), 'should accept %r' % s
    print('cyclic grammar recognition ok')

# ### Dyck-style nested parentheses
# We use the variant without an explicit epsilon rule so that the
# grammar is finitely ambiguous on each input (the standard Dyck rule
# `<S> -> ε` combined with `<S> -> <S><S>` yields infinitely many
# distinct derivations for any well-formed string, and our parser
# materializes every derivation as a separate tree).

if __name__ == '__main__':
    g_dyck = {
        '<S>': [['(', ')'], ['(', '<S>', ')'], ['<S>', '<S>']],
    }
    p = compile_grammar(g_dyck, '<S>')
    for s in ['()', '(())', '()()', '((()))', '(()())', '()()()']:
        trees = p.parse_on(s, '<S>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    assert not p.parse_on('(',   '<S>')
    assert not p.parse_on(')',   '<S>')
    assert not p.parse_on('()(', '<S>')
    print('Dyck grammar ok')

# ### The non-regular language a^n b^n
# `a^n b^n c^n` is famously not context-free, but `a^n b^n` is — and
# it exercises hidden right recursion through the recursive call to
# `<S>` sitting before terminal `b`. (No nullable nonterminal hides
# the recursion, so this is straightforward right recursion; we include
# it to show classic context-free examples still work.)

if __name__ == '__main__':
    g_anbn = {
        '<S>': [['a', '<S>', 'b'], []],
    }
    p = compile_grammar(g_anbn, '<S>')
    for n in range(5):
        s = 'a' * n + 'b' * n
        p_fresh = compile_grammar(g_anbn, '<S>')
        trees = p_fresh.parse_on(s, '<S>')
        assert trees, 'should accept %r' % s
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
    p_fresh = compile_grammar(g_anbn, '<S>')
    assert not p_fresh.parse_on('abab',  '<S>')
    p_fresh = compile_grammar(g_anbn, '<S>')
    assert not p_fresh.parse_on('aabbb', '<S>')
    p_fresh = compile_grammar(g_anbn, '<S>')
    assert not p_fresh.parse_on('aaabb', '<S>')
    print('a^n b^n grammar ok')

# ### Highly ambiguous PP-attachment grammar

if __name__ == '__main__':
    # Classic Tomita-style highly ambiguous: noun-verb-noun with optional
    # PP-attachment. We model it as: S -> NP VP; VP -> V NP | V NP PP;
    # NP -> n | NP PP; PP -> p NP.
    # The string `n v n p n` has two parses (PP attaches to first NP or
    # VP); each extra `p n` roughly doubles the count.
    g_pp = {
        '<S>':  [['<NP>', '<VP>']],
        '<VP>': [['v', '<NP>'], ['v', '<NP>', '<PP>']],
        '<NP>': [['n'], ['<NP>', '<PP>']],
        '<PP>': [['p', '<NP>']],
    }
    p = compile_grammar(g_pp, '<S>')
    for s, expected in [('nvn', 1), ('nvnpn', 2), ('nvnpnpn', 4),
                        ('nvnpnpnpn', 10)]:
        trees = p.parse_on(s, '<S>')
        assert len(trees) == expected, \
            'expected %d trees for %r, got %d' % (expected, s, len(trees))
        for t in trees:
            assert fuzzer.tree_to_string(t) == s
        print('%s -> %d tree(s)' % (s, len(trees)))

# ## Notes on Implementation
# This implementation uses worklists (`A`, `R`, `Q`, `U`) for duplicate
# suppression rather than the explicit descriptor sets of the form
# `(state, input_position, node)` used in production GLR implementations
# (Tomita; Scott & Johnstone). The result is correct and polynomial in
# time and space, but termination and idempotence guarantees are implicit
# in the worklist membership checks and the `last_fired_reach` map rather
# than structurally enforced by a descriptor memo.
#
# The GSS sharing rules ensure that whenever two parse stacks reach the
# same LR state at the same input position they share a single node.
# This sharing keeps the underlying stack representation polynomial.
# However, the number of distinct parse trees for an ambiguous grammar
# may still be exponential in the length of the input. Since this
# tutorial materializes explicit parse trees rather than a shared packed
# parse forest (SPPF), the total output size may also become exponential.
# For LR(1) grammars there are no parse-table conflicts, so GLR behaves
# similarly to ordinary LR parsing and is typically linear-time.

# ## References
#
# [^tomita1986efficient]: Masaru Tomita. Efficient Parsing for Natural Language. Kluwer Academic Publishers, Boston, 1986.
#
# [^nozohoor1991]: Rahman Nozohoor-Farshi. GLR parsing for ε-grammars.  In *Generalized LR Parsing*, Springer, 1991.
#
# [^economopoulos2006glr]: Rob Economopoulos. *Generalised LR Parsing Algorithms.* PhD dissertation, Royal Holloway, University of London, 2006.
#
# [^smits2025glr]: Jeffrey Smits. "(Right-Nulled) Generalised LR Parsing." *Whatever* blog, 12 Jan 2025.  `https://blog.jeffsmits.net/generalised-lr-parsing/`
#
# [^scott2003rnglr]: Elizabeth Scott and Adrian Johnstone. "Right nulled GLR parsers." *ACM Transactions on Programming Languages and Systems*, 28(4):577–618, 2006.
#
# [^scott2006rnglr]: Elizabeth Scott and Adrian Johnstone.  "Recognition is not parsing — SPPF-style parsing from cubic recognisers." *Science of Computer Programming*, 75:55–70, 2010.
