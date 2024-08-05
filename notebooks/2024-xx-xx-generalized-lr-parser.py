# ---
# published: true
# title: Generalized LR (GLR) Parser
# layout: post
# comments: true
# tags: parsing, gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of GLR Parser in Python
# including SPPF parse tree extraction [^scott2013gll].
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#  
# ## Synopsis
#
# ```python
# import glrparser as P
# my_grammar = {'<start>': [['1', '<A>'],
#                           ['2']
#                          ],
#               '<A>'    : [['a']]}
# my_parser = P.compile_grammar(my_grammar)
# for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
#     print(P.format_parsetree(tree))
# ```

# ## Definitions
# For this post, we use the following terms:
#  
# * The _alphabet_ is the set all of symbols in the input language. For example,
#   in this post, we use all ASCII characters as alphabet.
# 
# * A _terminal_ is a single alphabet symbol. Note that this is slightly different
#   from usual definitions (done here for ease of parsing). (Usually a terminal is
#   a contiguous sequence of symbols from the alphabet. However, both kinds of
#   grammars have a one to one correspondence, and can be converted easily.)
# 
#   For example, `x` is a terminal symbol.
# 
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
#   in the grammar using _rules_ for expansion.
# 
#   For example, `<term>` is a nonterminal in the below grammar.
# 
# * A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
#   nonterminals) that describe an expansion of a given terminal. A rule is
#   also called an _alternative_ expansion.
# 
#   For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.
# 
# * A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.
# 
#   For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the nonterminal `<digits>`
# 
# * A _context-free grammar_ is  composed of a set of nonterminals and 
#   corresponding definitions that define the structure of the nonterminal.
# 
#   The grammar given below is an example context-free grammar.
#  
# * A terminal _derives_ a string if the string contains only the symbols in the
#   terminal. A nonterminal derives a string if the corresponding definition
#   derives the string. A definition derives the  string if one of the rules in
#   the definition derives the string. A rule derives a string if the sequence
#   of terms that make up the rule can derive the string, deriving one substring
#   after another contiguously (also called parsing).
# 
# * A *derivation tree* is an ordered tree that describes how an input string is
#   derived by the given start symbol. Also called a *parse tree*.
# * A derivation tree can be collapsed into its string equivalent. Such a string
#   can be parsed again by the nonterminal at the root node of the derivation
#   tree such that at least one of the resulting derivation trees would be the
#   same as the one we started with.
# 
# * The *yield* of a tree is the string resulting from collapsing that tree.
# 
# * An *epsilon* rule matches an empty string.

# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.
# If you are running this on command line, please uncomment the following line.
# 
# ```
# def __canvas__(g):
#    print(g)
# ```

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities
import simplefuzzer as fuzzer
# We use the `display_tree()` method in earley parser for displaying trees.
import earleyparser as ep

# We use the random choice to extract derivation trees from the parse forest.
import random

# Pydot is needed for drawing
import pydot

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
# Here is an example grammar for arithmetic expressions, starting at `<start>`.
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# Secondly, as per traditional implementations,
# there can only be one expansion rule for the `<start>` symbol. We work around
# this restriction by simply constructing as many charts as there are expansion
# rules, and returning all parse trees.

# ## Traditional Recursive Descent
# First we find a way to display a graph represented on tabular format.


def create_row(hdr):
    return {c:[] for c in hdr}

def create_tbl(nstates, hdr):
    tbl = []
    for i in range(nstates):
        tbl.append(create_row(hdr))
    return tbl

# 
if __name__ == '__main__':
    MY_TERMINALS = 'abcd$'
    MY_NON_TERMINALS = 'AS'
    MY_TBL = create_tbl(10, MY_TERMINALS + MY_NON_TERMINALS)
    for i in range(10):
        for k in MY_TERMINALS  + MY_NON_TERMINALS:
            MY_TBL[i][k] = []
    MY_TBL[0]['a'] = ['s2']
    MY_TBL[0]['b'] = ['s3']
    MY_TBL[0]['S'] = ['g1']

    MY_TBL[1]['$'] = ['accept']

    MY_TBL[2]['b'] = ['s5']
    MY_TBL[2]['A'] = ['g4']

    MY_TBL[3]['b'] = ['s5']
    MY_TBL[3]['A'] = ['g6']

    MY_TBL[4]['c'] = ['s7']

    MY_TBL[5]['a'] = ['r3']
    MY_TBL[5]['b'] = ['r3']
    MY_TBL[5]['c'] = ['r3']
    MY_TBL[5]['d'] = ['r3']
    MY_TBL[5]['$'] = ['r3']

    MY_TBL[6]['d'] = ['s8']

    MY_TBL[7]['a'] = ['r1']
    MY_TBL[7]['b'] = ['r1']
    MY_TBL[7]['c'] = ['r1']
    MY_TBL[7]['d'] = ['r1']
    MY_TBL[7]['$'] = ['r1']

    MY_TBL[8]['d'] = ['s9']

    MY_TBL[9]['a'] = ['r2']
    MY_TBL[9]['b'] = ['r2']
    MY_TBL[9]['c'] = ['r2']
    MY_TBL[9]['d'] = ['r2']
    MY_TBL[9]['$'] = ['r2']

    hdr = MY_TBL[0]
    print('\t'.join(k for k in hdr))
    for row in MY_TBL:
        print('\t'.join(str(row[k]) for k in row))


# Show graph

def to_graph(nfa_tbl):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(nfa_tbl):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = 'rectangle'# rectangle, oval, diamond
        label = str(i)
        G.add_node(pydot.Node(label, label=label, shape=shape, peripheries='1')
            #peripheries= '2' if i == root else '1')
                   )
        for transition in state:
            cell = state[transition]
            if not cell: continue
            G.add_edge(pydot.Edge(label, cell[0][1], color='black'))
    return G
#
if __name__ == '__main__':
    g = to_graph(MY_TBL)
    print(str(g))
    #__canvas__(str(g))

# Consider how you will parse a string that conforms to the following grammar

g1 = {
    '<S>': [
          ['<A>', '<B>'],
          ['<C>']],
   '<A>': [
        ['a']],
   '<B>': [
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

sample_grammar = {
    '<start>': [['<A>','<B>']],
    '<A>': [['a', '<B>', 'c'], ['a', '<A>']],
    '<B>': [['b', '<C>'], ['<D>']],
    '<C>': [['c']],
    '<D>': [['d']]
}

sample_start = '<S>'

# We first build an NFA of the grammar. For that, we begin by adding a new
# state `<>` to grammar.
# First, we add a start extension to the grammar.

def add_start_state(g, start, new_start='<>'):
    new_g = dict(g)
    new_g[new_start] = [[start]]
    return new_g, new_start

# Test
if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    for k in g1a:
        print(k)
        print('  |',g1a[k])
    assert g1a_start in g1a
    assert g1a[g1a_start][0][0] in g1

# For building an NFA, all we need is to start with start item, and then
# recursively identify the transitions. First, we define the state
# data structure.

class State:
    def __init__(self, name, expr, dot):
        global SID
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = SID
        SID += 1

    def finished(self):
        return self.dot >= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot < len(self.expr) else None

    def __repr__(self):
        return "{%s : %d}" % (str(self), self.sid)


    def show_dot(self, sym, rule, pos, dotstr='|', extents=''):
        extents = str(extents)
        return sym + '::= ' + ' '.join([
               str(p)
               for p in [*rule[0:pos], dotstr, *rule[pos:]]]) + extents

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

    def copy(self):
        assert False
        return State(self.name, self.expr, self.dot, self.s_col, self.e_col)

    def _t(self):
        return (self.name, self.expr, self.dot, self.s_col.index)

    def __hash__(self):
        return hash(self._t())

    def __eq__(self, other):
        return self._t() == other._t()

    def def_key(self):
        return self.name

# Next, we build an NFA out of a given grammar. The NFA is given by:
# States, which are rules with a dot.
# If the symbol at the dot is a nonterminal, then there is a link from
# current state to all expansions of the nonterminal.

SID = 0
class NFA:
    def __init__(self, g, start):
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}

    # create starting states for the given key
    def create_start(self, s):
        rules = self.g[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.g[s]]

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = State(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.states[state.sid] = state
        return self.my_states[(name, texpr, pos)]

    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)

# We now build the NFA table. For that, we start with the start state, and
# process each state. 

def symbols(g):
    terminals = {}
    for k in g:
        for rule in g[k]:
            for t in rule:
                if fuzzer.is_nonterminal(t): continue
                terminals[t] = True
    return list(terminals.keys()), list(g.keys())

class NFA(NFA):
    def get_all_rules_with_dot_after_key(self, key):
        states = []
        for k in self.g:
            for rule in self.g[k]:
                l_rule = len(rule)
                for i,t in enumerate(rule):
                    if i >= l_rule: continue
                    if t == key:
                        states.append(self.create_state(k, rule, i+1))
        return states

class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        new_state = self.advance(state)
        return new_state

# Epsilon transitions. Given a state K -> t.V a
# we get all rules of nonterminal V, and add with
# starting 0
class NFA(NFA):
    def epsilon_transitions(self, state):
        key = state.at_dot()
        # key should not be none at this point.
        assert key is not None
        new_states = []
        for rule in self.g[key]:
            new_state = self.create_state(key, rule, 0)
            new_states.append(new_state)
        return new_states

class NFA(NFA):
    def process_state(self, state):
        key = state.at_dot()
        if key is None: return []
        new_states = []

        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        new_state = self.symbol_transition(state)
        # add it to the states returned
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            # each rule of the nonterminal forms an epsilon transition
            # with the dot at the `0` position
            ns = self.epsilon_transitions(state)
            for s in ns:
                new_states.append(('', s))
        else:
            # no definition for terminal symbols
            pass
        return new_states


class NFA(NFA):
    def build_nfa(self):
        start_item = self.create_start(self.start)[0]
        queue = [('$', start_item)]
        while queue:
            (pkey, state), *queue = queue
            new_states = self.process_state(state)
            if not new_states:
                # this happens when the dot has reached the end of the rule.
                # in this case, go back epsilon to all rules that
                # are after the given nonterminal at the head.
                key = state.def_key()
                list_of_return_states = self.get_all_rules_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(state, '', s, 'reduce') # reduce
                    # these are already processed. So we do not add to queue
            else:
                for key, s in new_states:
                    self.add_child(state, key, s, 'shift')
                queue.extend(new_states)
        # now build the nfa table.
        state_count = len(self.states.keys())
        nfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            nfa_table[i] = {k:'|' for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            nfa_table[parent][key] = [child]

        return nfa_table

# Test
if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    table = my_nfa.build_nfa()
    rowh = table[0]
    print('>', '\t','\t\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(i, '\t','\t\t'.join([str(row[c]) for c in row.keys()]))
    print()

# ## Building a DFA.

# For DFA, a state is no longer a single item. So, lt us define item separately.

class Item(State):
    pass

# A DFAState contains many items.
DSID = 0

class DFAState:
    def __init__(self, items):
        global DSID
        self.sid = DSID
        DSID += 1
        # now computethe closure.
        self.items = items

    def __repr__(self):
        return '<%s>' % self.sid

# We define our DFA.

class DFA(NFA):
    def __init__(self, g, start):
        self.items = {}
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)

class DFA(DFA):
    def create_start_item(self, s, rule):
        return Item(s, tuple(rule), 0)

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule) for rule in self.g[s] ]
        return self.create_state(items) # create state does closure

    def compute_closure(self, items):
        to_process = list(items)
        seen = set()
        new_items = []
        while to_process:
            item_, *to_process = to_process
            if item_.sid in seen: continue
            seen.add(item_.sid)
            key = item_.at_dot()
            if key is None: continue
            # no closure for terminals
            if not fuzzer.is_nonterminal(key): continue
            new_items_ = [self.create_start_item(key, rule) for rule in self.g[key] ]
            to_process.extend(list(new_items_))
            new_items.extend(new_items_)
        return new_items


    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = DFAState(self.compute_closure(items))
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))


    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() == key:
                item_ = self.advance_item(item)
                advanced.append(item_)
            else:
                pass
                # ignore
        return advanced

    def symbol_transition(self, dfastate, key):
        assert key is not None
        items = self.advance(dfastate, key)
        if not items: return None
        new_dfastate = self.create_state(items) # create state does closure
        return new_dfastate

    def process_state(self, dfastate):
        new_dfastates = []
        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            self.add_child(dfastate, k, new_dfastate, 'shift') # shift
            # add it to the states returned
            new_dfastates.append((k, new_dfastate))
        return new_dfastates

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = Item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.items[item.sid] = item
        return self.my_items[(name, texpr, pos)]

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)


class DFA(DFA):
    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [('$', start_dfastate)]
        while queue:
            (pkey, dfastate), *queue = queue
            new_dfastates = self.process_state(dfastate)
            queue.extend(new_dfastates)

        # now build the dfa table.
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:'|' for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            dfa_table[parent][key] = [child]

        return dfa_table


# Test
if __name__ == '__main__':
    my_dfa = DFA(g1a, g1a_start)
    table = my_dfa.build_dfa()
    rowh = table[0]
    print('>', '\t','\t\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(i, '\t','\t\t'.join([str(row[c]) for c in row.keys()]))
    print()


# Now, let us recursively build the NFA.

# 
# **Note**: There is now (2024) a reference implementation for GLL from the authors. It is available at [https://github.com/AJohnstone2007/referenceImplementation](https://github.com/AJohnstone2007/referenceImplementation).
# 
# [^lang1974deterministic]: Bernard Lang. "Deterministic techniques for efficient non-deterministic parsers." International Colloquium on Automata, Languages, and Programming. Springer, Berlin, Heidelberg, 1974.
#
# [^bouckaert1975efficient]: M. Bouckaert, Alain Pirotte, M. Snelling. "Efficient parsing algorithms for general context-free parsers." Information Sciences 8.1 (1975): 1-26.
# 
# [^scott2013gll]: Elizabeth Scott, Adrian Johnstone. "GLL parse-tree generation." Science of Computer Programming 78.10 (2013): 1828-1844.
# 
# [^scott2010gll]: Elizabeth Scott, Adrian Johnstone. "GLL parsing." Electronic Notes in Theoretical Computer Science 253.7 (2010): 177-189.
# 
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008
# 
# [^tomita1984lr]: Masaru Tomita. LR parsers for natural languages. In 22nd conference on Association for Computational Linguistics, pages 354–357, Stanford, California, 1984. Association for Computational Linguistics.
# 
# [^tomita1986efficient]: Masaru Tomita. Efficient parsing for natural language: a fast algorithm for practical systems. Kluwer Academic Publishers, Boston, 1986.
