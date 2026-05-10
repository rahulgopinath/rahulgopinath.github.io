# ---
# published: true
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
# that are fast and powerful, but require conflict-free parse tables. They
# require conflict-free parse tables. Ambiguous grammars, and many
# grammars that produce shift/reduce or reduce/reduce conflicts, therefore
# cannot be parsed deterministically without additional conflict-resolution
# mechanisms such as precedence or associativity declarations.
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
# defined already. The `__canvas__` function is defined externally when it is
# used as a web notebook.


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
# * `Accept` — accept the input
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
# goto transitions (after reductions) are blue.

def to_graph(dfa_table):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(dfa_table):
        shape = 'rectangle'
        peripheries = '1'
        for k in state:
            if any('accept' in str(a).lower() for a in state[k]): peripheries = '2'
        G.add_node(pydot.Node(str(i), label=str(i), shape=shape,
                              peripheries=peripheries))
        for transition in state:
            cell = state[transition]
            if not cell: continue
            for action in cell:
                if not action or 'accept' in str(action).lower(): continue
                color = 'black'
                if action[0] == 'g':   color = 'blue'
                elif action[0] == 'r': continue   # reductions are not edges
                target = action[1:]
                if not target.isdigit(): continue
                G.add_edge(pydot.Edge(str(i), target, color=color,
                                      label=transition))
    return G

# test

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
# Hand-unrolled LR parser corresponding to the DFA of grammar g2

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
            stack.append(('a', 'sA'))   # shift, go to state for A->a.
            return self.s_A(stack, tokens)
        elif symbol == 'c':
            tokens.pop(0)
            stack.append(('c', 'sC'))
            return self.s_C(stack, tokens)
        return False

    # State after shifting 'a': A -> a .  (reduce by A -> a)
    def s_A(self, stack, tokens):
        stack.pop()                        # pop 'a'
        lhs = '<A>'
        _, prev = stack[-1]
        stack.append((lhs, 'gA'))
        return self.s_gA(stack, tokens)    # goto after reducing <A>

    # State after goto <A> from state 0: S -> <A> . <B>
    #                                    <B> -> . b
    def s_gA(self, stack, tokens):
        symbol = tokens[0]
        if symbol == 'b':
            tokens.pop(0)
            stack.append(('b', 'sB'))
            return self.s_B(stack, tokens)
        return False

    # State after shifting 'b': B -> b .  (reduce by B -> b)
    def s_B(self, stack, tokens):
        stack.pop()                        # pop 'b'
        lhs = '<B>'
        stack.append((lhs, 'sAB'))
        return self.s_AB(stack, tokens)    # S -> <A> <B> .

    # State after S -> <A> <B> . : reduce by S -> <A> <B>
    def s_AB(self, stack, tokens):
        stack.pop()                        # pop '<B>'
        stack.pop()                        # pop '<A>'
        lhs = '<S>'
        stack.append((lhs, 'gS'))
        return self.s_accept(stack, tokens)

    # State after shifting 'c': C -> c .  (reduce by C -> c)
    def s_C(self, stack, tokens):
        stack.pop()                        # pop 'c'
        lhs = '<C>'
        stack.append((lhs, 'sC_done'))
        return self.s_C_done(stack, tokens)

    # State after C -> c . : reduce by C -> c, then S -> <C>
    def s_C_done(self, stack, tokens):
        stack.pop()                        # pop '<C>'
        lhs = '<S>'
        stack.append((lhs, 'gS'))
        return self.s_accept(stack, tokens)

    # Accept state
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
#  
# ## The Graph Structured Stack
#
# The key challenge in running multiple LR parse stacks in parallel is
# efficiency. Maintaining fully independent stacks would lead to
# exponentially many of them on ambiguous grammars. The *Graph Structured
# Stack* (GSS) solves this by merging any two stacks that reach the same
# LR state at the same input position into a single shared node.
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
# `k` times).
#  
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
#  
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
                # Acceptance: shifting '$' into a state with no further
                # actions means <> -> <start> $ is complete.
                if symbol == '$' and all(
                        not acts for acts in self.parse_table[target].values()):
                    self.accepted = True
            elif operation[0] == 'r':
                rule_num    = operation    # production_rules is keyed by 'r:N'
                _lhs, rhs   = self.production_rules[rule_num]
                if len(rhs) == 0:
                    # Epsilon rule: no symbol node to traverse.
                    R.append((v, None, rule_num))
                else:
                    # Queue (node, first_symbol_edge, rule) for every
                    # active state node at position i sharing this LR state.
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
# new one. When we add a new GSS edge to an *existing* node, reductions
# pending on that node must be re-queued with the new edge in case they
# produce a new derivation path.

class GLRRecognizer(GLRRecognizer):
    def reducer(self, v, x, rule_num, i, A, R):
        lhs, rhs = self.production_rules[rule_num]
        k        = len(rhs)
        symbol   = self.input_string[i]

        # Find all state nodes below the k-symbol right-hand side.
        if k == 0:
            all_w = {v}           # epsilon: w is v itself
        else:
            all_w = self.gss.find_nodes_at_depth(x, 2 * k - 1)

        for w in all_w:
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
                # Re-queue reductions triggered from u via this new edge.
                if u not in A:
                    for op in self.parse_table[u.state].get(symbol, []):
                        if op and op[0] == 'r':
                            R.append((u, z, op))
            else:
                # Create a fresh state node and connect it.
                u = self.gss.create_node(is_state=True, state=s)
                z = self.gss.create_node(is_state=False, symbol=lhs)
                self.gss.add_edge(u, z)
                self.gss.add_edge(z, w)
                A.append(u)
                self.U[i].append(u)

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

# test
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
    print('recognizer ok')

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
    print('unambiguous recognizer ok')

# ## GLR Parser
# A recognizer tells us only whether a string is in the language. To
# extract parse trees we augment the GSS so that every symbol node also
# carries a *tree fragment* — the partial parse tree for the symbol it
# represents. Terminals carry leaf nodes; nonterminals carry the tree
# built during the reduction that created them.
#
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
# (state→symbol→state). Each symbol node along the way carries one child
# tree. We collect all such paths from a given state node, yielding every
# `(bottom_state_node, [child_trees])` pair.
# 
# Invariant: the GSS strictly alternates state nodes and symbol nodes.
# Every edge created by shifter() and reducer() respects this structure,
# which is what makes collect_paths correct without additional checking.

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

# ### Actor (parser version)
# When we detect Accept, we harvest the tree from the top-of-stack symbol
# node. Otherwise, the actor is identical to the recognizer's version.

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
                    # Trees are collected after the full loop in parse_on,
                    # once all reductions at position n are complete.
            elif operation[0] == 'r':
                rule_num  = operation    # production_rules is keyed by 'r:N'
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
# path, and attaches that tree to every new symbol node it creates.

class GLRParser(GLRParser):
    def reducer(self, v, x, rule_num, i, A, R):
        lhs, rhs = self.production_rules[rule_num]
        k        = len(rhs)
        symbol   = self.input_string[i]

        if k == 0:
            all_paths = [(v, [])]
        else:
            all_paths = collect_paths(v, k)

        for (w, children) in all_paths:
            # collect_paths returns children rightmost-first (top-of-stack
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
                    # Path exists; add this tree if it is a new derivation.
                    if new_tree not in z_existing.trees:
                        z_existing.trees.append(new_tree)
                        if u not in A:
                            for op in self.parse_table[u.state].get(symbol, []):
                                if op and op[0] == 'r':
                                    R.append((u, z_existing, op))
                else:
                    z = self.gss.create_node(is_state=False, symbol=lhs,
                                             tree=new_tree)
                    self.gss.add_edge(u, z)
                    self.gss.add_edge(z, w)
                    if u not in A:
                        for op in self.parse_table[u.state].get(symbol, []):
                            if op and op[0] == 'r':
                                R.append((u, z, op))
            else:
                u = self.gss.create_node(is_state=True, state=s)
                z = self.gss.create_node(is_state=False, symbol=lhs,
                                         tree=new_tree)
                self.gss.add_edge(u, z)
                self.gss.add_edge(z, w)
                A.append(u)
                self.U[i].append(u)

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

# ## Notes on Complexity
# The GSS ensures that whenever two parse stacks reach the same LR state
# at the same input position they share a single node. This sharing is
# what keeps the underlying stack representation polynomial in size.
#
# In the worst case, generalized LR parsing has cubic-time recognition
# complexity, matching other general context-free parsing algorithms such
# as Earley and GLL parsing. The shared graph structures used by GLR also
# remain polynomial in size in the worst case.
#
# However, the number of distinct parse trees for an ambiguous grammar may
# still be exponential in the length of the input. Since this tutorial
# materializes explicit parse trees rather than a shared packed parse
# forest (SPPF), the total output size may therefore also become
# exponential.
#
# For LR(1) grammars there are no parse-table conflicts, so GLR behaves
# similarly to ordinary LR parsing and is typically linear-time.
#
# Note on implementation discipline: this implementation uses worklists
# (A, R, Q, U) for duplicate suppression rather than the explicit
# descriptor sets of the form (state, input_position, node) used in
# production GLR implementations (Tomita; Scott & Johnstone). The result
# is correct and polynomial, but termination and idempotence guarantees
# are implicit in the worklist membership checks rather than structurally
# enforced by a descriptor memo.


# ## References
#
# [^tomita1984lr]: Masaru Tomita. LR parsers for natural languages. In
# 22nd Annual Meeting of the ACL, pages 354–357, 1984.
#
# [^tomita1986efficient]: Masaru Tomita. Efficient Parsing for Natural
# Language. Kluwer Academic Publishers, Boston, 1986.
#
# [^scott2013glr]: Elizabeth Scott, Adrian Johnstone. Structuring the
# GLL parsing algorithm for performance. Science of Computer Programming,
# 78(10):1828–1844, 2013.
#
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs. Parsing
# Techniques: A Practical Guide. Springer, 2008.
