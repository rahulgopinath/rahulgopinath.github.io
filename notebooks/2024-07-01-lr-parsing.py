# ---
# published: true
# title: Shift-Reduce Parsers LR(0) SLR(1), LALR(1) and LR(1)
# layout: post
# comments: true
# tags: parsing glr
# categories: post
# ---

# TLDR; This tutorial is a complete implementation of some of the
# shift-reduce parsers in Python. We build LR(0) parser, SLR(1) Parser and the
# canonical LR(1) parser, and show how to extract the parse trees.
# Python code snippets are provided throughout so that you can
# work through the implementation steps.
# 
# A **shift-reduce** parser is a *bottom-up* parser that works by shifting input
# symbols on to a stack, run matching procedures to identify what is on the
# stack, and attempts to reduce the symbols on the top of the stack to
# other symbols based on the matched production rules.
# 
# LR parsers are a class of bottom-up shift-reduce parsers[^grune2008parsing]
# that rely on constructing an automaton called LR-Automata (typically a parsing
# table) for their operation.
# The *L* in the *LR* parsing stands for scanning
# the input left-to-right, and the *R* stands for constructing a rightmost
# derivation. This contrasts with [LL parsers](/post/2022/07/02/generalized-ll-parser/)
# which are again left-to-right but construct the leftmost derivation.
# (Intuitively, LL parsers process and output the parse tree with pre-order
# traversal (root, left, right) where as LR
# outputs post order traversal, (left, right, root).)
# 
# Such parsers are shift-reduce parsers because the operation of the LR parser
# is to repeatedly shift an input symbol (left-to-right) into the stack,
# and based on the parsing-table, decide to either reduce the stack or shift
# more input symbols on to the stack. The parsing table, in this case, is
# constructed based on the production rules of the grammar.
# The **Right-most** in this case refers to the nonterminal that the parsing
# strategy decides to rewrite next. That is, in right-most strategy, the symbols
# on the top of the stack are reduced first.
# 
# To illustrate this, consider the following grammar:
# ```
# <E> := <T> + <E>
#      | <T>
# <T> := <F> * <T>
#      | <F>
# <F> := <D>
# <D> := 1 | 0
# ```
# 
# In the case of leftmost derivation, the sentence `0 + 1 * 1` would be parsed
# as follows, starting from `<E>`. The period (`.`) shows the current parse
# point in the rule, and the pipe (`|`) indicates the input stream. We show the
# top down parsing. We assume here that the parser simply uses the first rule
# to parse, and uses a lookahead when necessary. See my LL(1) post for more
# advanced techniques.
# 
# ```
# <E> := . <T> + <E>  | 0 + 1 * 1
#        . <F> + <E>  | 0 + 1 * 1
#        . <D> + <E>  | 0 + 1 * 1
#        . 0          | 0 + 1 * 1
#        0  . + <E>   | + 1 * 1
#        0  + . <E>   | 1 * 1
#        0  + . <T>   | 1 * 1
#        0  + . <F> * <T>  | 1 * 1
#        0  + . <D> * <T>  | 1 * 1
#        0  + . 1 * <T>  | 1 * 1
#        0  + 1 . * <T>  | * 1
#        0  + 1 * . <T>  | 1
#        0  + 1 * . <D>  | 1
#        0  + 1 * . 1  | 1
#        0  + 1 * 1 .  |
# ```
# As you can see, for top-down parsing, we needed to sort of unwrap the
# nonterminals from the start symbol before starting to match. Hence, we
# are forced to unwrap the leftmost nonterminal (if the next symbol in the
# production is a nonterminal, otherwise, simply match with the next input
# symbol) to match with the next input symbol from the stream.
# That is, the leftmost nonterminal is always rewritten first.
# 
# Below is the bottom-up right most parsing. We will be discussing how the
# rules are chosen later in this post.
# 
# ```
#   | 0 + 1 * 1
#   0 | + 1 * 1
#   <D> | + 1 * 1
#   <F> | + 1 * 1
#   <T> | + 1 * 1
#   <T> + | 1 * 1
#   <T> + 1 | * 1
#   <T> + <D> | * 1
#   <T> + <F> | * 1
#   <T> + <F> * | 1
#   <T> + <F> * 1 |
#   <T> + <F> * <D> |
#   <T> + <F> * <F> |
#   <T> + <F> * <T> |
#   <T> + <T> |
#   <T> + <E> |
#   <E> |
# ```
# As you can see, we construct nonterminals from the symbols on the stack.
# If the current token that was just shifted matches a nonterminal, then we
# rewrite the stack top with that nonterminal. So, the stack top is always
# considered for next action. Since we consider the stack to be the
# representation of a partially parsed rule, and the top of the stack is the
# right most part of the parsed rule, we say it is rightmost first.


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
# * A _rule_ (also production rule) is a finite sequence of _terms_ (two types
#   of terms: terminals and nonterminals) that describe an expansion of a given
#   terminal. A rule is also called an _alternative_ expansion.
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
# * A *terminal* _derives_ a string if the string contains only the symbols in the
#   terminal. A *nonterminal* derives a string if the corresponding definition
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
# * An *epsilon* rule matches an empty string, and an epsilon transition is a
#   transition that does not consume any tokens.
# 
# * A *recognizer* checks whether the input string can be matched by a given
#   grammar. That is, given the starting nonterminal symbol, can any set of
#   expansions result in the given input string?
# 
# * A *parser* is a recognizer that additionally returns corresponding
#   parser trees for the given input string and grammar.
# 
# * A *parse table* is a representation of the LR automation that is derived
#   from the production rules of the grammar.
# 
# * A *DFA* ([deterministic-finite-automaton[(https://en.wikipedia.org/wiki/Deterministic_finite_automaton)) is a state machine of the
#   representation of a state machine that consumes input symbols to decide
#   which state to shift to.
# 
# * A *NFA* ([nondeterministic-finite-automaton](https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton)) is a state machine that allows
#   both epsilon transitions as well as transitions to multiple states for the
#   same symbol.


# ### Prerequisites
# As before, we start with the prerequisite imports.
# Note: The following libraries may need to be installed separately.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl

# Since this notebook serves both as a web notebook as well as a script
# that can be run on the command line, we redefine canvas if it is not
# defined already. The `__canvas__` function is defined externally when it is
# used as a web notebook.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print

# Importing the fuzzer for a few simple utilities. 
import simplefuzzer as fuzzer

# We use the `display_tree()` method in earley parser for displaying trees.
import earleyparser as ep

# Pydot is needed for drawing
import pydot

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar
# style. For example, given below is a simple grammar for nested parentheses.

paren_g = {
        '<P>' : [['(', '<P>', ')'],
                 ['(', '<D>', ')']],
        '<D>' : [['0'],['1']]
}

# Equivalently,
# 
# ```
# <P> := '(' <P> ')'
#      | '(' <D> ')'
# <D> := 0 | 1
# ```
# 
# We have seen [LL parsers](/post/2020/03/17/recursive-descent-contextfree-parsing-with-left-recursion/)
# in the previous posts, culminating with the
# [GLL parser](/post/2022/07/02/generalized-ll-parser/).
# The main difference between an LR parser and an LL parser is that an LL
# parser uses the current nonterminal and the next symbol to determine the
# production rule to apply. That is, starting from the top-most, that is the
# start symbol, it recursively expands the rules until it finds a rule that
# starts with the token that was currently read in from the stream.
# In contrast, the LR parser acts bottom up. It starts by trying to recognize
# bottom most tokens, and push the recognized tokens into the stack, recursively
# building more higher level tokens.
# 
# We say that the LR parser uses the
# viable-prefix and the next symbol to determine the next action to
# take. The *viable prefix* is the portion of the input string that has been
# recognized so far. This recognition is accomplished by the LR automaton,
# which we describe next.
# 
# Let us consider the following grammar
# 
# ```
# E -> ( D + E )
# E -> D
# D -> 1
# ```
# To apply LR parsing to it, we need a starting definition such that the
# start symbol has only one production rule as its definition. So, we add
# a production rule (called augmentation) to conform.
# 
# ```
# S` -> E
# ```
#  
# For a naive translation of the grammar into the automata,
# we start with the starting production rule
# `S' -> E`. Since we are starting to parse, let us indicate the parse point
# also with `.'. This would be before `E` is parsed. That is, `S' -> .E`.
# That is, the period (`.') represents the current parse point.
# If we somehow parsed `E` now, then we would transition to an accept state.
# This is represented by `S' -> E.`. However, since the transition is a
# nonterminal, it can't happen by reading
# the corresponding symbol `E` from the input stream. It has to happen through
# another path. Hence, we indicate this by a dashed line. Next, when the parse
# is at `S' -> .E`, any of the expansions of `E` can now be parsed. So, we add
# each expansion of `E` as $$\epsilon$$ transition away. These are
# `E := . ( D + E )` and `E := . D`. Continuing in this fashion, we have: 

if __name__ == '__main__':
    __canvas__('''
    digraph LR0_Automaton {
     rankdir=TB;
     node [shape = rectangle];
     start [shape = point];
     // States
     0 [label = "0: S' -> . E $"];
     1 [label = "1: E -> . ( D + E )"];
     2 [label = "2: E -> . D"];
     3 [label = "3: D -> . 1"];
     4 [label = "4: S' -> E . $"];
     5 [label = "5: E -> ( . D + E )"];
     6 [label = "6: D -> 1 ."];
     7 [label = "7: E -> D ."];
     8 [label = "8: E -> ( D . + E )"];
     9 [label = "9: E -> ( D + . E )"];
     10 [label = "10: E -> ( D + E . )"];
     11 [label = "11: E -> ( D + E ) ."];
     12 [label = "12: S' -> E $ ."];
     // Regular transitions
     start -> 0;
     0 -> 1 [label = "ε"];
     0 -> 2 [label = "ε"];
     0 -> 3 [label = "ε"];
     1 -> 5 [label = "("];
     2 -> 3 [label = "ε"];
     3 -> 6 [label = "1"];
     5 -> 3 [label = "ε"];
     8 -> 9 [label = "+"];
     9 -> 1 [label = "ε"];
     9 -> 2 [label = "ε"];
     9 -> 3 [label = "ε"];
     10 -> 11 [label = ")"];
     4 -> 12 [label = "$"];
     // Nonterminal transitions (dashed)
     edge [style = dashed];
     0 -> 4 [label = "E"];
     2 -> 7 [label = "D"];
     5 -> 8 [label = "D"];
     9 -> 10 [label = "E"];
    }
    ''')

# Notice that this state machine is a nondeterministic finite automaton (NFA).
# That is, we have epsilon transitions. Furthermore the
# NFA is not complete. For example, what happens when `6. D := 1 .`
# is complete? Then, the parse needs to transition to a state that has just
# completed `D`. For example, `8. E := ( D . + E )` or `7. E := D .`. Here is how
# it looks like.

if __name__ == '__main__':
   __canvas__('''
    digraph LR0_Automaton {
     rankdir=TB;
     node [shape = rectangle];
     start [shape = point];
     // States
     0 [label = "0: S' -> . E"];
     1 [label = "1: E -> . ( D + E )"];
     2 [label = "2: E -> . D"];
     3 [label = "3: D -> . 1"];
     4 [label = "4: S' -> E . $"];
     5 [label = "5: E -> ( . D + E )"];
     6 [label = "6: D -> 1 ."];
     7 [label = "7: E -> D ."];
     8 [label = "8: E -> ( D . + E )"];
     9 [label = "9: E -> ( D + . E )"];
     10 [label = "10: E -> ( D + E . )"];
     11 [label = "11: E -> ( D + E ) ."];
     12 [label = "12: S' -> E $ ."];
     // Regular transitions
     start -> 0;
     0 -> 1 [label = "ε"];
     0 -> 2 [label = "ε"];
     0 -> 3 [label = "ε"];
     1 -> 5 [label = "("];
     2 -> 3 [label = "ε"];
     3 -> 6 [label = "1"];
     5 -> 3 [label = "ε"];
     8 -> 9 [label = "+"];
     9 -> 1 [label = "ε"];
     9 -> 2 [label = "ε"];
     9 -> 3 [label = "ε"];
     10 -> 11 [label = ")"];
     4 -> 12 [label = "$"];
     // Nonterminal transitions (dashed)
     edge [style = dashed];
     0 -> 4 [label = "E"];
     2 -> 7 [label = "D"];
     5 -> 8 [label = "D"];
     9 -> 10 [label = "E"];
     // Red arrows for completed rules
     edge [color = red, style = solid, constraint=false];
     6 -> 7 [label = "completion"];
     6 -> 8 [label = "completion"];  // Added this line
     11 -> 4 [label = "completion"];
     11 -> 10 [label = "completion"];
     7 -> 10 [label = "completion"];
     7 -> 4 [label = "completion"];
    }
    ''')
   # Note: change constraint=true for a different view.

# As before, the dashed arrows represent non-terminal transitions that are
# actually completed through other paths. The red arrows represent reductions.
# You will notice that there can be multiple reductions from the same
# item. At this point, this NFA over-approximates our grammar.
# The right reduction needs to be chosen based on the prefix so far, and we
# will see how to do this later.
# 
# ## Building the NFA
# Let us try and build these dynamically.
# We first build an NFA of the grammar. For that, we begin by adding a new
# state `<>` to grammar.
# 
# ### Augment Grammar with Start

def add_start_state(g, start, new_start='<>'):
    new_g = dict(g)
    new_g[new_start] = [[start, '$']]
    return new_g, new_start

# A sample grammar.
g1 = {
   '<E>': [
        ['(', '<D>', '+', '<E>', ')'],
        ['<D>']],
   '<D>': [
        ['1']]
}
g1_start = '<E>'

# Test
if __name__ == '__main__':
    g1a, g1a_start = add_start_state(g1, g1_start)
    for k in g1a:
        print(k)
        print('  |',g1a[k])
    assert g1a_start in g1a
    assert g1a[g1a_start][0][0] in g1

# A utility procedure to extract all symbols in a grammar.

def symbols(g):
    terminals = {}
    for k in g:
        for rule in g[k]:
            for t in rule:
                if fuzzer.is_nonterminal(t): continue
                terminals[t] = True
    return list(sorted(terminals.keys())), list(sorted(g.keys()))

# Test
if __name__ == '__main__':
    t, nt = symbols(g1)
    print(t)
    print(nt)

# ### The State Data-structure
# For building an NFA, all we need is to start with start item, and then
# recursively identify the transitions. First, we define the state
# data structure.
# A state for an NFA is simply a production rule and a parse position.
class State:
    def __init__(self, name, expr, dot, sid):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid

    def finished(self):
        return self.dot >= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot < len(self.expr) else None

    def remaining(self):
        # x[0] is current, then x[1:] is remaining
        return self.expr[self.dot+1:]

    def __repr__(self):
        return "(%s : %d)" % (str(self), self.sid)

    def show_dot(self, sym, rule, pos, dotstr='|', extents=''):
        extents = str(extents)
        return sym + '::= ' + ' '.join([
               str(p)
               for p in [*rule[0:pos], dotstr, *rule[pos:]]]) + extents

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

    def def_key(self):
        return self.name

# It can be tested this way
if __name__ == '__main__':
    s = State(g1a_start, ('<E>',), 0, 0)
    print(s.at_dot())
    print(str(s))
    print(s.finished())

# ### The NFA class
# Next, we build an NFA out of a given grammar. An NFA is composed of
# different states connected together by transitions.

# #### NFA Initialization routines
class NFA:
    def __init__(self, g, start):
        self.grammar = g
        self.productions, self.production_rules = self._get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.state_sids = {} # Convenience for debugging only
        self.sid_counter = 0

    def get_key(self, kr):
        return "%s -> %s" %kr

    def _get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.grammar:
            for r in self.grammar[k]:
                production_rules["r:%d" % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules

# #### NFA Start State (create_start)

class NFA(NFA):
    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    # create starting states for the given key
    def create_start(self, s):
        rules = self.grammar[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.grammar[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.state_sids[state.sid] = state
        return self.my_states[(name, texpr, pos)]

# Let us test this.
# We can list the grammar production rules as follows:
if __name__ == '__main__':
    i = 1
    for k in g1a:
        for r in g1a[k]:
            print(i, k, r)
            i+=1

# Let us use the grammar.
if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    st = my_nfa.create_start(g1a_start)
    assert str(st[0]) == '<>::= | <E> $'
    my_nfa = NFA(g1, g1_start)
    st = my_nfa.create_start(g1_start)
    assert str(st[0]) == '<E>::= | ( <D> + <E> )'

# #### Advance the state of parse by one token
class NFA(NFA):
    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)

# Let us test this.
if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    st_ = my_nfa.create_start(g1a_start)
    st = my_nfa.advance(st_[0])
    assert str(st) == '<>::= <E> | $'
    my_nfa = NFA(g1, g1_start)
    st_ = my_nfa.create_start(g1_start)
    st = [my_nfa.advance(s) for s in st_]
    assert str(st[0]) == '<E>::= ( | <D> + <E> )'

# #### NFA find_transitions
# Next, given a state, we need to find all other states reachable from it.
# The first one is simply a transition from the current to the next state
# when moving the parsing point one location. For example,
#
# ```
# '<S>::= <A> | <B>'
# ```
#
# is connected to the below by the key `<A>`.
#
# ```
# '<S>::= <A> <B> |'
# ```

class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        return self.advance(state)

# Note that we are building an NFA. Hence, epsilon
# transitions are allowed. This is what we use when we are
# starting to parse nonterminal symbols. For example, when
# we have a state with the parsing just before `<B>`, for e.g.
#
# ```
# '<S>::= <A> | <B>'
# ```
#
# Then, we add a new state
#
# ```
# '<A>::= | a',
# ```
# and connect this new state to the previous one with an $$\epsilon$$
# transition.

class NFA(NFA):
    def epsilon_transitions(self, state):
        key = state.at_dot()
        # key should not be none at this point.
        assert key is not None
        new_states = []
        for rule in self.grammar[key]:
            new_state = self.create_state(key, rule, 0)
            new_states.append(new_state)
        return new_states

# Combining both procedures and processing the state itself for its transitions.
# If the dot is before a symbol, then we add the transition to the
# advanced state with that symbol as the transition. If the key at
# the dot is a nonterminal, then add all expansions of that nonterminal
# as epsilon transfers.

class NFA(NFA):
    def find_transitions(self, state):
        key = state.at_dot()
        if key is None: return [] # dot after last.
        new_states = []
        new_state = self.symbol_transition(state)
        new_states.append((key, new_state))

        if fuzzer.is_nonterminal(key):
            ns = self.epsilon_transitions(state)
            for s in ns: new_states.append(('', s))
        else: pass
        return new_states

# Let us test this.

if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    st = my_nfa.create_start(g1a_start)
    new_st = my_nfa.find_transitions(st[0])
    assert str(new_st[0]) == "('<E>', (<>::= <E> | $ : 1))"
    assert str(new_st[1]) == "('', (<E>::= | ( <D> + <E> ) : 2))"


# Defining a utility method. This is only used to display the graph.
# Given a key, we want to get all states where this key has just been parsed.
# We use this method to identify where to go back to, after parsing a specific
# key.
class NFA(NFA):
    def get_all_rules_with_dot_after_key(self, key):
        states = []
        for k in self.grammar:
            for rule in self.grammar[k]:
                l_rule = len(rule)
                for i,t in enumerate(rule):
                    if i >= l_rule: continue
                    if t == key:
                        states.append(self.create_state(k, rule, i+1))
        return states

# Let us test this.
if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    lst = my_nfa.get_all_rules_with_dot_after_key('<D>')
    assert str(lst) == '[(<E>::= ( <D> | + <E> ) : 0), (<E>::= <D> | : 1)]'

# #### NFA build_nfa
# We can now build the complete NFA.
class NFA(NFA):
    def build_table(self, num_states, columns, children):
        table = [{k:[] for k in columns} for _ in range(num_states)]
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in table[parent]: table[parent][key] = []
            v = prefix+str(child)
            if v not in table[parent][key]:
                table[parent][key].append(v)
        return table

    def add_reduction(self, p, key, c, notes):
        self.children.append((p.sid, key, c, notes))

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))

    def add_shift(self, state, key, s):
        # if the key is a nonterminal then it is a goto
        if key == '':
            self.add_child(state, key, s, 'shift')
        elif fuzzer.is_nonterminal(key):
            self.add_child(state, key, s, 'goto')
        else:
            self.add_child(state, key, s, 'shift')

    def add_reduce(self, state):
        N = self.productions[self.get_key((state.name, list(state.expr)))]
        for k in self.terminals:
            self.add_reduction(state, k, N, 'reduce')

    def add_actual_reductions(self, state):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = state.def_key()
        list_of_return_states = self.get_all_rules_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(state, '', s, 'to') # reduce to

    def build_nfa(self):
        start_item = self.create_start(self.start)[0]
        queue = [('$', start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                self.add_shift(state, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                self.add_reduce(state)

                # only for the graph, not for traditional algorithm
                self.add_actual_reductions(state)

            queue.extend(new_states)
        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + ['']),
                                self.children)

# Testing the build_nfa

if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    table = my_nfa.build_nfa()
    rowh = table[0]
    print('>', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(i, '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# ## Constructing a graph
# To display the NFA (and DFAs) we need a graph. We construct this out of the
# table we built previously.

def to_graph(table, lookup=lambda y: str(y)):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(table):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = 'rectangle'# rectangle, oval, diamond
        peripheries = '1'# rectangle, oval, diamond
        nodename = str(i)
        label = lookup(i)
        # if the state contains 'accept', then it is an accept state.
        for k in state:
            if  'accept' in state[k]: peripheries='2'
        G.add_node(pydot.Node(nodename,
                              label=label,
                              shape=shape,
                              peripheries=peripheries))
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = 'black'
            style='solid'
            if not transition: transition = "ε"
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = ''
                if state_name == 'accept':
                    continue
                elif state_name[0] == 'g':
                    color='blue'
                    transition_prefix = '' # '(g) '
                    style='dashed'
                elif state_name[0] == 'r':
                    # reduction is not a state transition.
                    # color='red'
                    # transition_prefix = '(r) '
                    continue
                elif state_name[0] == 't':
                    color='red'
                    transition = ''
                    transition_prefix = '' # '(t) '
                else:
                    assert state_name[0] == 's'
                    transition_prefix = '' #'(s) '
                G.add_edge(pydot.Edge(nodename,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G

# Viewing the NFA
if __name__ == '__main__':
    my_nfa = NFA(g1a, g1a_start)
    table = my_nfa.build_nfa()
    for k in my_nfa.state_sids:
      print(k, my_nfa.state_sids[k])
    def lookup(i):
        return str(i) + ": "+ str(my_nfa.state_sids[i])
    g = to_graph(table, lookup)
    __canvas__(str(g))

# # LR0 Automata
#
# An LR(0) automaton is composed of multiple states, and each state represents a set
# of items that indicate the parsing progress. The states are connected together
# using transitions which are composed of the terminal and nonterminal symbols
# in the grammar.
#
# To construct the LR(0) automaton, we start with the initial state containing the
# augmented start symbol (if necessary), and we apply closure to expand the
# context. For the closure, we simply merge all epsilon transitions to the current
# item.
#
# ## Closure
# A closure represents all possible parse paths at a given
# point. The idea is to look at the current parse progress; Identify any
# nonterminals that need to be expanded next, and add the production rules of that
# nonterminal to the current item, with parse point (dot) at the beginning.
#
# For example, given the first state, where `*` represent the parse progress
#
# ```
# <S`> := * <E>
# ```
# Applying closure, we expand `<E>` further.
#
# ```
# <S`> := * <E>
# <E>  := * ( <D> + <E> )
# <D>  := * 1
# ```
# No more nonterminals to expand. Hence, this is the closure of the first state.
#
# Consider what happens when we apply a transition of `(` to this state.
#
# ```
# <E> := ( * <D> + <E> )
# <D> := * 1
# ```
# 
# Here is how we can compute a closure

def compute_closure(grammar, items,
            create_start_item=lambda s, rule: State(s, tuple(rule), 0, 0)):
    to_process = list(items)
    seen = set()
    new_items = {}
    while to_process:
        item_, *to_process = to_process
        if str(item_) in seen: continue
        seen.add(str(item_))
        new_items[str(item_)] = item_
        key = item_.at_dot()
        if key is None: continue
        if not fuzzer.is_nonterminal(key): continue
        for rule in grammar[key]:
            new_item = create_start_item(key, rule)
            to_process.append(new_item)
    return list(new_items.values())

# Test it.
if __name__ == '__main__':
    s = State(g1a_start, ('<E>',), 0, 0)
    closure = compute_closure(g1, [s])
    for item in closure:
        print(item)


# This gives us the following graph with each closure, and the transitions indicated. Note that
# the nonterminal transitions are dashed.

if __name__ == '__main__':
    __canvas__('''
    digraph my_graph {
    0 [label="0\n<>::= . <E> $\n<E>::= . ( <D> + <E> )\n<E>::= . <D>\n<D>::= . 1", peripheries=1, shape=rectangle];
    1 [label="1\n<E>::= ( . <D> + <E> )\n<D>::= . 1", peripheries=1, shape=rectangle];
    2 [label="2\n<D>::= 1 .", peripheries=1, shape=rectangle];
    3 [label="3\n<E>::= <D> .", peripheries=1, shape=rectangle];
    4 [label="4\n<>::= <E> . $", peripheries=1, shape=rectangle];
    5 [label="5\n<E>::= ( <D> . + <E> )", peripheries=1, shape=rectangle];
    6 [label="6\n<>::= <E> $ .", peripheries=1, shape=rectangle];
    7 [label="7\n<E>::= ( <D> + . <E> )\n<E>::= . ( <D> + <E> )\n<E>::= . <D>\n<D>::= . 1", peripheries=1, shape=rectangle];
    8 [label="8\n<E>::= ( <D> + <E> . )", peripheries=1, shape=rectangle];
    9 [label="9\n<E>::= ( <D> + <E> ) .", peripheries=1, shape=rectangle];

    0 -> 1  [color=black, label="(s) (", style=solid];
    0 -> 2  [color=black, label="(s) 1", style=solid];
    0 -> 3  [color=blue, label="(g) <D>", style=dashed];
    0 -> 4  [color=blue, label="(g) <E>", style=dashed];
    1 -> 2  [color=black, label="(s) 1", style=solid];
    1 -> 5  [color=blue, label="(g) <D>", style=dashed];
    2 -> 3  [color=red, label="(t) ", style=solid];
    2 -> 5  [color=red, label="(t) ", style=solid];
    3 -> 4  [color=red, label="(t) ", style=solid];
    4 -> 6  [color=black, label="(s) $", style=solid];
    5 -> 7  [color=black, label="(s) +", style=solid];

    7 -> 1  [color=black, label="(s) (", style=solid];
    7 -> 2  [color=black, label="(s) 1", style=solid];
    7 -> 3  [color=blue, label="(g) <D>", style=dashed];
    7 -> 8  [color=blue, label="(g) <E>", style=dashed];
    8 -> 9  [color=black, label="(s) )", style=solid];
    9 -> 4  [color=red, label="(t) ", style=solid];
    9 -> 8  [color=red, label="(t) ", style=solid];
    }

               ''')

# This is the basic automaton. However, you may notice that there are two types
# of nodes in this diagram. The first one represents partial parses which
# contain the dot at a position other than the end, and the second one
# represents a complete parse of a rule with the dot at the end. You will also
# note that the complete parse nodes seem to have red outgoing arrows, and
# at least in one, multiple red outgoing arrows. That is, it is not a true
# DFA. The next state to transition to is actually chosen based on the path
# the input string took through the DFA with the help of a stack.

# ### Compiling DFA States
# So, how should we represent these states? If you look at state 0, it would
# be possible to represent it as a procedure as below. We first save in to the
# stack the current state, then extract the current symbol, and depending on
# whether the symbol is one of the expected, we shift to the next state.
# Note that we ignore the blue dashed arrows (nonterminal symbols) because
# they were included just to indicate that the transition happens by another
# path. Another note is that each state represents one row of the automation
# table.

# ```
# <>::= . <E> $
# <E>::= . ( <D> + <E> ) 
# <E>::= . <D> 
# <D>::= . 1
# ```
def state_0(stack, input_string):
    stack.append(0)
    symbol = input_string[0]
    if symbol == '(': return state_1(stack, input_string[1:])
    elif symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '(' or '1'")

# ```
# <E>::= ( . <D> + <E> )
# <D>::= . 1
# ```

def state_1(stack, input_string):
    stack.append(1)
    symbol = input_string[0]
    if symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '1'")

# ```
# <D>::= 1 .
# ```
# This is the first reduction state. In a reduction state, what we do is to
# look at the stack if the corresponding rule was popped off the stack.
# From a reduction state, we can transition to any state that has just
# parsed the RHS (head) of the reduction.
def state_2(stack, input_string):
    stack.append(2)
    len_rule_rhs = 1 # D ::= 1
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_3(stack, input_string) # state0-<D>->state3
    if stack[-1] == 1: return state_5(stack, input_string) # state1-<D>->state5
    if stack[-1] == 7: return state_3(stack, input_string) # state7-<D>->state3
    else: raise Exception("Invalid state during reduction by D → 1")

# ```
# <E>::= <D> .
# ```
def state_3(stack, input_string):
    stack.append(3)
    len_rule_rhs = 1 # E ::= D
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-<E>->state4
    if stack[-1] == 7: return state_8(stack, input_string) # state7-<E>->state8
    else: raise Exception("Invalid state during reduction by E → D")

# ```
# <>::= <E> . $
# ```

def state_4(stack, input_string):
    stack.append(4)
    symbol = input_string[0]
    if symbol == '$': return state_6(stack, input_string[1:])
    else: raise Exception("Expected '$'")

# ```
# <E>::= ( <D> . + <E> )
# ```

def state_5(stack, input_string):
    stack.append(5)
    symbol = input_string[0]
    if symbol == '+': return state_7(stack, input_string[1:])
    else: raise Exception("Expected '+'")

# ```
# <>::= <E> $ .
# ```
def state_6(stack, input_string):
    stack.append(6)
    len_rule_rhs = 2 # <> ::= E $
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0:
        if input_string: raise Exception('Expected end of input')
        return True # Accept
    else: raise Exception("Invalid state during reduction by <> → E $")

# ```
# <E>::= ( <D> + . <E> ) 
# <E>::= . ( <D> + <E> ) 
# <E>::= . <D>
# <D>::= . 1
# ```

def state_7(stack, input_string):
    stack.append(7)
    symbol = input_string[0]
    if symbol == '(': return state_1(stack, input_string[1:])
    if symbol == '1': return state_2(stack, input_string[1:])
    else: raise Exception("Expected '(' or '1'")

# ```
# <E>::= ( <D> + <E> . )
# ```

def state_8(stack, input_string):
    stack.append(8)
    symbol = input_string[0]
    if symbol == ')': return state_9(stack, input_string[1:])
    else: raise Exception("Expected ')'")

# ```
# <E>::= ( <D> + <E> ) .
# ```

def state_9(stack, input_string):
    stack.append(9)
    len_rule_rhs = 5 # E ::= ( D + E )
    for _ in range(len_rule_rhs): stack.pop()
    if stack[-1] == 0: return state_4(stack, input_string) # state0-<E>->state4
    else: raise Exception("Invalid state during reduction by E → ( D + E )")

# Let us now verify if our parser works.
if __name__ == '__main__':
    test_strings = [("1", True), ("(1+1)", True), ("1+1", False), ("1+", False)]

    for test_string, res in test_strings:
        print(f"Parsing: {test_string}")
        input_string = list(test_string) + ['$']
        try:
            val = state_0([], input_string)
        except Exception as e:
            if res: print(e)

# Note that while the above does not contain multiple reductions, it is possible
# that a state can contain multiple reductions on more complex (e.g. LR(1))
# grammars. But otherwise, the general parsing is as above.
# 
# ## Building the DFA
# Given a grammar, we will next consider how to build such a DFA.
# For DFA, unlike an NFA, a state is no longer a single item. So, let us define
# item separately.

# ### Item
class Item(State): pass

# ### DFAState
#
# A DFAState contains many items.
class DFAState:
    def __init__(self, items, dsid):
        self.sid = dsid
        self.items = items

    def def_keys(self):
        return [i.def_key() for i in self.items]

    def __repr__(self):
        return '(%s)' % self.sid

    def __str__(self):
        return str(sorted([str(i) for i in self.items]))

# ### LR(0) DFA
# We define our DFA initialization. We also define two utilities for
# creating new items and DFA states.
class LR0DFA(NFA):
    def __init__(self, g, start):
        self.item_sids = {}
        self.states = {}
        self.grammar = g
        self.start = start
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)

    def new_state(self, items):
        s = DFAState(items, self.dsid_counter)
        self.dsid_counter += 1
        return s

    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item

# #### DFA Compute the closure
# We have discussed computing the closure before. The idea is to identify any
# nonterminals that are next to be parsed, and recursively expand them, adding
# to the items.

class LR0DFA(LR0DFA):
    def compute_closure(self, items):
        return compute_closure(self.grammar, items,
                               create_start_item=lambda s, rule:
                               self.create_start_item(s, rule))
    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)

# #### DFA Start State (create_start)
# The start item is similar to before. The main difference is that
# rather than returning multiple states, we return a single state containing
# multiple items.

class LR0DFA(LR0DFA):
    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = self.new_state(self.compute_closure(items))
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        items = [self.create_start_item(s, rule) for rule in self.grammar[s] ]
        return self.create_state(items) # create state does closure

# Let us test this.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    st = my_dfa.create_start(g1a_start)
    assert [str(s) for s in st.items] == \
            ['<>::= | <E> $',
             '<E>::= | ( <D> + <E> )', '<E>::= | <D>', '<D>::= | 1']

# #### Advance the state of parse by the given token
# Unlike in NFA, where we had only one item, and hence, there
# was only one advancing possible, here we have multiple items.
# Hence, we are given a token by which to advance, and return
# all items that advance by that token, advanced.

class LR0DFA(LR0DFA):
    def advance(self, dfastate, key):
        advanced = []
        for item in dfastate.items:
            if item.at_dot() != key: continue
            item_ = self.advance_item(item)
            advanced.append(item_)
        return advanced

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos)]

# Let us test this.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    start = my_dfa.create_start(g1a_start)
    st = my_dfa.advance(start, '<D>')
    assert [str(s) for s in st] == ['<E>::= <D> |'] 

    st = my_dfa.advance(start, '1')
    assert [str(s) for s in st] == ['<D>::= 1 |']

# #### DFA find_transitions
#
# Next, we define the transitions. Unlike in the case of NFA where we had only a
# single item, we have multiple items. So, we look through each possible
# token (terminals and nonterminals)
class LR0DFA(LR0DFA):
    def symbol_transition(self, dfastate, key):
        items = self.advance(dfastate, key)
        if not items: return None
        return self.create_state(items) # create state does closure

    def find_transitions(self, dfastate):
        new_dfastates = []
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            new_dfastates.append((k, new_dfastate))
        return new_dfastates

# Let us test this.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    st = my_dfa.create_start(g1a_start)
    assert [str(s) for s in st.items] == \
           ['<>::= | <E> $',
            '<E>::= | ( <D> + <E> )', '<E>::= | <D>', '<D>::= | 1']
    sts = my_dfa.find_transitions(st)
    assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
            [('(', ['<E>::= ( | <D> + <E> )', '<D>::= | 1']),
             ('1', ['<D>::= 1 |']),
             ('<D>', ['<E>::= <D> |']),
             ('<E>', ['<>::= <E> | $'])]


# #### add_reduce
# This is different from NFA because we are iterating over items, but we need
# to add reduction to the dfastate
class LR0DFA(LR0DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in  self.terminals:
            self.add_reduction(dfastate, k, N, 'reduce')

# Similarly the graph related utilities also change a bit.
class LR0DFA(LR0DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            for item in self.states[s].items:
                if item.dot == 0: continue # no token parsed.
                if item.expr[item.dot-1] == key:
                    states.append(self.states[s])
        return states

    def add_actual_reductions(self, item, dfastate):
        # Also, (only) for the graph, collect epsilon transmition to all
        # rules that are after the given nonterminal at the head.
        key = item.def_key()
        list_of_return_states = self.get_all_states_with_dot_after_key(key)
        for s in list_of_return_states:
            self.add_child(dfastate, '', s, 'to') # reduce

# #### LR0DFA build_dfa
# Bringing all these together, let us build the DFA. (Compare to build_nfa).
class LR0DFA(LR0DFA):
    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [('$', start_dfastate)]
        seen = set()
        while queue:
            (pkey, dfastate), *queue = queue
            if str(dfastate) in seen: continue
            seen.add(str(dfastate))

            new_dfastates = self.find_transitions(dfastate)
            for key, s in new_dfastates:
                assert key != ''
                self.add_shift(dfastate, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if item.finished():
                    self.add_reduce(item, dfastate)

                    # Also, (only) for the graph, collect epsilon transmission to all
                    # rules that are after the given nonterminal at the head.
                    self.add_actual_reductions(item, dfastate)

            queue.extend(new_dfastates)

        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + ['']),
                                self.children)

# Let us test building the DFA.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    table = my_dfa.build_dfa()

    for k in my_dfa.states:
      print(k)
      for v in my_dfa.states[k].items:
        print('', v)

    rowh = table[0]
    print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# Let us try graphing
if __name__ == '__main__':
    def lookup(i):
        return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
    g = to_graph(table, lookup)
    __canvas__(str(g))

# # LR0Recognizer
# We can now provide the complete parser that relies on this automata.

class LR0Recognizer:
    def __init__(self, my_dfa):
        self.dfa = my_dfa
        self.parse_table = self.dfa.build_dfa()
        self.production_rules = self.dfa.production_rules

    def log(self, stack, tokens):
        print('Stack', stack)
        print('Tokens', tokens)

    def parse(self, input_string, start):
        tokens = list(input_string + '$')
        stack = [(None, 's0')]

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])
            if symbol == '$':
                for i in self.dfa.states[state].items:
                    if i.name == start and i.at_dot() == '$':
                        return True, "Input Accepted"

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f"Parsing Error: No actions state{state}:{symbol}"

            assert len(actions) == 1
            action = actions[0]

            if action.startswith('s'):
                tokens.pop(0)
                stack.append((symbol, action))

            elif action.startswith('r:'): # reduction. Not the next state.
                lhs, rhs = self.production_rules[action]
                for _ in rhs: stack.pop()

                _, prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f"Parsing Error: No transition {prev_state}:{lhs}"

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith('g'):
                self.stack.append((lhs, action))
            else: assert False

            self.log(stack, tokens)

# Testing it.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    parser = LR0Recognizer(my_dfa)
    # Test the parser with some input strings
    test_strings = ["(1+1)", "(1+(1+1))", "1", "1+", "+1+1"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message = parser.parse(test_string, g1a_start)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# # LR0Parser
# We'll next implement the LR(0) parser, which includes parse tree extraction.
# Parse tree extraction involves building a tree structure that represents the
# syntactic structure of the input string according to the grammar rules.
class LR0Parser(LR0Recognizer):
    def parse(self, input_string, start):
        tokens = list(input_string) + ['$']
        stack = [(None, 's0')]
        self.node_stack = []

        while True:
            (_,state_), symbol = stack[-1], tokens[0]
            state = int(state_[1:])

            actions = self.parse_table[state][symbol]
            if not actions:
                return False, f"Parsing Error: No actions state{state}:{symbol}", None

            if symbol == '$':
                for i in self.dfa.states[state].items:
                    if i.name == start and i.at_dot() == '$':
                        return True, "Input Accepted", self.node_stack[0]

            assert len(actions) == 1
            action = actions[0]

            if action.startswith('s'):
                tokens.pop(0)
                stack.append((symbol, action))
                self.node_stack.append((symbol, []))

            elif action.startswith('r'):
                lhs, rhs = self.production_rules[action]
                children = []
                for _ in rhs:
                    stack.pop()  # Pop state, symbol
                    children.insert(0, self.node_stack.pop())

                new_node = (lhs, children)
                self.node_stack.append(new_node)

                _,prev_state_ = stack[-1]
                prev_state = int(prev_state_[1:])

                if not self.parse_table[prev_state][lhs]:
                    return False, f"Parsing Error: No transition {prev_state}:{lhs}", None

                next_state = self.parse_table[prev_state][lhs][0]
                stack.append((lhs, next_state))

            elif action.startswith('g'):
                stack.append((lhs, next_state))

            else: assert False

            self.log(stack, tokens)

# Now, let us build parse trees
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    parser = LR0Parser(my_dfa)
    # Test the parser with some input strings
    test_strings = ["(1+1)", "1", "(1+(1+1))", "+", "1+"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, g1a_start)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# Notice that we have used a quite simple grammar. For reference, this
# was our `g1` grammar. 
# 
# ```
# E -> ( D + E )
# E -> D
# D -> 1
# ```
# 
# The interesting fact about this grammar was that
# you could look at the current symbol, and decide which of these rules
# to apply. That is, if the current symbol was `(` then rule 0 applies,
# and if the symbol was `1`, then rule 1 applies.
# What if you have a grammar where that is impossible?
# Here is one such grammar
# 
# ```
# E -> D + E
# E -> D
# D -> 1
# ```
# 
# As you can see, it is no longer clear which rule of `<E>` to apply when we
# have a `<D>` parsed. To decide on such cases, we need to go up one level
# complexity.

g2 = {
        '<E>' :  [['<D>', '+', '<E>'],
                  ['<D>']],
        '<D>' :  [['1']]
        }
g2_start = '<E>'

# Let us build the parse table.
if __name__ == '__main__':
    g2a, g2a_start = add_start_state(g2, g2_start)
    my_dfa = LR0DFA(g2a, g2a_start)
    table = my_dfa.build_dfa()

    for k in my_dfa.states:
      print(k)
      for v in my_dfa.states[k].items:
        print('', v)

    rowh = table[0]
    print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# As you can see, on State 2, we have two possible choices -- s4 and r:1.
# This is called a shift/reduce conflict. The issue is that when we come to
# state 2, that is.

# ```
#  <E>::= <D> | + <E>
#  <E>::= <D> |
# ```
# We have two possible choices. We can either reduce to `<E>` or shift `+`.
# To determine which one to act upon, we need a lookahead. If the
# next token is `+`, then we should shift it to stack. If not,
# we should reduce to `<E>`. This is what SLR parsers do.
#
# # SLR1 Automata
#
# SLR(1) parsers, or Simple LR(1) parsers, are an improvement over LR(0) parsers.
# They use lookahead to resolve some conflicts that occur in LR(0) parsers.
# A lookahead is the next token in the input that hasn't been processed yet.
# By considering this lookahead token, SLR(1) parsers can make more informed
# decisions about which production to use when reducing.
#
# For using SLR1 automation, we require first and follow sets. This has been
# discussed previously. Hence, providing the code here directly.
# ### First and follow

nullable_grammar = {
    '<start>': [['<A>', '<B>']],
    '<A>': [['a'], [], ['<C>']],
    '<B>': [['b']],
    '<C>': [['<A>'], ['<B>']]
}

# The definition is as follows.

def union(a, b):
    n = len(a)
    a |= b
    return len(a) != n

def get_first_and_follow(grammar):
    terminals, nonterminals = symbols(grammar)
    first = {i: set() for i in nonterminals}
    first.update((i, {i}) for i in terminals)
    follow = {i: set() for i in nonterminals}
    nullable = set()

    while True:
        added = 0
        productions = [(k,rule) for k in nonterminals for rule in grammar[k]]

        for k, rule in productions:
            can_be_empty = True
            for t in rule:
                added += union(first[k], first[t])
                if t not in nullable:
                    can_be_empty = False
                    break
            if can_be_empty:
                added += union(nullable, {k})

            follow_ = follow[k]
            for t in reversed(rule):
                if t in follow:
                    added += union(follow[t], follow_)

                if t in nullable:
                    follow_ = follow_.union(first[t])
                else:
                    follow_ = first[t]

        if not added:
            return first, follow, nullable

def first_of_rule(rule, first_sets, nullable_set):
    first_set = set()
    for token in rule:
        if fuzzer.is_nonterminal(token):
            first_set |= first_sets[token]
            if token not in nullable_set: break
        else:
            first_set.add(token)
            break
    return first_set

# Testing it.
if __name__ == '__main__':
    first, follow, nullable = get_first_and_follow(nullable_grammar)
    print("first:", first)
    print("follow:", follow)
    print("nullable", nullable)

# ## Building the DFA
# #### DFA Initialization routines

class SLR1DFA(LR0DFA):
    def __init__(self, g, start):
        self.item_sids = {} # debugging convenience only
        self.states = {}
        self.grammar = g
        self.start = start
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)
        self.first, self.follow, self.nullable = get_first_and_follow(g)

# Next, we build the dfa. There is only one change. (See CHANGED)
# When reducing, we only reduce if the token lookahead is in the follow set.
class SLR1DFA(SLR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for k in self.follow[item.name]: # CHANGED
            self.add_reduction(dfastate, k, N, 'reduce')

    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [('$', start_dfastate)]
        seen = set()
        while queue:
            (pkey, dfastate), *queue = queue
            if str(dfastate) in seen: continue
            seen.add(str(dfastate))

            new_dfastates = self.find_transitions(dfastate)
            for key, s in new_dfastates:
                assert key != ''
                self.add_shift(dfastate, key, s)

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if item.finished():
                    self.add_reduce(item, dfastate)

                    # Also, (only) for the graph, collect epsilon transmission to all
                    # rules that are after the given nonterminal at the head.
                    self.add_actual_reductions(item, dfastate)

            queue.extend(new_dfastates)

        return self.build_table(len(self.my_states),
                                (self.terminals + self.non_terminals + ['']),
                                self.children)

# Let us see if it works.
if __name__ == '__main__':
    my_dfa = SLR1DFA(g2a, g2a_start)
    table = my_dfa.build_dfa()

    for k in my_dfa.states:
      print(k)
      for v in my_dfa.states[k].items:
        print('', v)

    rowh = table[0]
    print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# We can also view it as before.
if __name__ == '__main__':
    def lookup(i):
        return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
    g = to_graph(table, lookup)
    __canvas__(str(g))


# ### SLR1Parser
# There is no difference in the parser.

class SLR1Parser(LR0Parser): pass

# Let us try parsing with it.
if __name__ == '__main__':
    my_dfa = SLR1DFA(g2a, g2a_start)
    parser = SLR1Parser(my_dfa)
    # Test the parser with some input strings
    test_strings = ["1+1", "1", "1+1+1"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, g2a_start)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# But is this enough? Can we parse all useful grammars this way?
# Consider this grammar.
# 
# ```
# S -> E + T
# S -> T
# E -> + T
# E -> 1
# T -> E
# ```

g3 = {
    '<S>': [['<E>', '+', '<T>'], ['<T>']],
    '<E>': [['+', '<T>'], ['1']],
    '<T>': [['<E>']]
}

g3_start = '<S>'


# Let us see if it works.
if __name__ == '__main__':
    g3a, g3a_start = add_start_state(g3, g3_start)
    my_dfa = SLR1DFA(g3a, g3a_start)
    table = my_dfa.build_dfa()

    for k in my_dfa.production_rules:
        print(k, my_dfa.production_rules[k])

    for k in my_dfa.states:
      print(k)
      for v in my_dfa.states[k].items:
        print('', v)

    rowh = table[0]
    print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# You will notice a conflict in State 3.  ['s8', 'r:4']
# The question is whether to shift `+`
# and go to State 8, or to reduce with rule r:4.
# To resolve this, we need the full LR(1) parser.
# # LR1 Automata
# 
# LR(1) parsers, or Canonical LR(1) parsers, are the most powerful in the LR parser family.
# They are needed when SLR(1) parsers are not sufficient to handle certain complex grammars.
# LR(1) parsers differ from SLR(1) parsers in that they incorporate lookahead information
# directly into the parser states, allowing for even more precise parsing decisions.
# 
# ## Building the DFA
# ### LR1Item
# The LR1 item is similar to the Item, except that it contains a lookahead.
# This also is the most important difference between LR(0) and SLR(1) on one
# hand and LR(1) on the other. SLR uses LR(0) items which mean exactly one item
# per production rule + parse dot. However, in the case of LR(1) you can have
# multiple items with the same LR(0) core--that is, production rule and parse
# point--but with different lookahead. One may ask, what if use the LR(0) items
# but add possible lookaheads as extra information to it? This gets you LALR(1).

class LR1Item(Item):
    def __init__(self, name, expr, dot, sid, lookahead):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid
        self.lookahead = lookahead

    def __repr__(self):
        return "(%s, %s : %d)" % (str(self), self.lookahead, self.sid)

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot) + ':' + self.lookahead

# ### LR1DFA class
# 
# We also need update on create_item etc to handle the lookahead.
# The advance_item is called from `advance(item)` which does not require
# changes.
class LR1DFA(SLR1DFA):
    def advance_item(self, item):
        return self.create_item(item.name, item.expr, item.dot+1, item.lookahead)

    def new_item(self, name, texpr, pos, lookahead):
        item =  LR1Item(name, texpr, pos, self.sid_counter, lookahead)
        self.sid_counter += 1
        return item

    def create_item(self, name, expr, pos, lookahead):
        texpr = tuple(expr)
        if (name, texpr, pos, lookahead) not in self.my_items:
            item = self.new_item(name, texpr, pos, lookahead)
            self.my_items[(name, texpr, pos, lookahead)] = item
            self.item_sids[item.sid] = item
        return self.my_items[(name, texpr, pos, lookahead)]

# The compute_closure now contains the lookahead.
# This is the biggest procedure change from LR0DFA. 
# The main difference is in computing the lookahead. 
# The lines added and modified from LR0DFA are indicated in the procedure.
# 
# Here, say we are computing the closure of `A -> Alpha . <B> <Beta>`.
# Remember that when we create new items for closure, we have to provide it with
# a lookahead.
# 
# So, To compute the closure at `<B>`, we create items with lookahead which are
# characters that can follow `<B>`. This need not be just the `first(<Beta>)`
# but also what may follow `<Beta>` if `<Beta>` is nullable. This would be the
# lookahead of the item `A -> Alpha . <B> <Beta>` which we already have, let us
# say this is `l`. So, we compute `first(<Beta> l)` for lookahead.
# 
class LR1DFA(LR1DFA):
    def compute_closure(self, items):
        to_process = list(items)
        seen = set()
        new_items = {}
        while to_process:
            item_, *to_process = to_process
            if str(item_) in seen: continue
            seen.add(str(item_))
            new_items[str(item_)] = item_
            key = item_.at_dot()
            if key is None: continue
            if not fuzzer.is_nonterminal(key): continue
            remaining = list(item_.remaining()) + [item_.lookahead] # ADDED
            lookaheads = first_of_rule(remaining, self.first, self.nullable) # ADDED
            for rule in self.grammar[key]:
                for lookahead in lookaheads: # ADDED
                    new_item = self.create_start_item(key, rule, lookahead) # MODIFIED
                    to_process.append(new_item)
        return list(new_items.values())

    def create_start_item(self, s, rule, lookahead):
        return self.new_item(s, tuple(rule), 0, lookahead)

# #### LR1DFA building DFA
# This method create_start changes to include the '$' as lookahead.
class LR1DFA(LR1DFA):
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule, '$') for rule in self.grammar[s]]
        return self.create_state(items)

# Another major change, we no longer add a reduction to all follows of item.name
# instead, we restrict it to just item.lookahead.
# 
# **Note.** A possible confusion here is about the treatment of lookaheads,
# in `add_reduction`. In LR0DFA.add_reduction, we add a reduction link for
# all terminal symbols to each item. In SLR1DFA.add_reduction, we add a
# reduction link for all terminal symbols that are in the `follow(item.name)`
# Here, we may hence expect the lookaheads to be a subset of `follow(item.name)`
# and to add the reduction for each lookahead of a given item.
# 
# The difference is in the LR1Item compared to Item, where LR1Item contains one
# lookahead token per item. That is, there could be multiple items with same
# parse points, corresponding to each possible lookahead. Since there is one
# lookahead per LR1Item rather than multiple lookaheads per Item, we only need
# to add one reduction per item.


class LR1DFA(LR1DFA):
    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        # k is changed to item.lookahead
        self.add_reduction(dfastate, item.lookahead, N, 'reduce') # DEL/CHANGED

# ### LR1Parser
# the parse class does not change.
class LR1Parser(LR0Parser): pass

# Parsing
if __name__ == '__main__':
    my_dfa = LR1DFA(g3a, g3a_start)

    for k in my_dfa.production_rules:
        print(k, my_dfa.production_rules[k])

    print()
    parser = LR1Parser(my_dfa)

    for k in my_dfa.states:
      print(k)
      for v in my_dfa.states[k].items:
          print('', v)

    rowh = parser.parse_table[0]
    print('State\t', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(parser.parse_table):
        print(str(i) + '\t', '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# We can also view it as before.
if __name__ == '__main__':
    def lookup(i):
        return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
    table = parser.parse_table
    g = to_graph(table, lookup)
    __canvas__(str(g))


# Test the parser with some input strings
if __name__ == '__main__':
    test_strings = ["1", "1+1", "+1+1"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, g3a_start)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()


# # LALR1 Automata
# One of the problems with LR(1) parsing is that while powerful, (all
# deterministic context-free languages can be expressed as an LR(1) grammar)
# the number of states required is very large because we incorporate lookahead
# information into items. That is, each lookahead symbol in combination with the
# LR(0) core becomes an LR1 item. Hence, the number of such LR(1) items can be
# as large as the number of LR(0) items multiplied by the number of terminal
# symbols in the grammar. Hence, even for a simple language such as C, an LR(1)
# grammar may result in a table that occupies 1 MB of RAM. While this is not
# too onerous for modern computers, one may ask if there is some trade off that 
# we can make such that we can parse with a more larger set of DCFG grammars
# while still keeping the memory requirements similar to the SLR(1) table.
# 
# The LALR is one such technique. The idea is that similar to SLR(1) and LR(1)
# we maintain the lookahead. But unlike SLR(1) (and like LR(1)) we lookahead
# per production rule rather than per nonterminal. However, for any given state
# in the, automata, we merge those items in the state that has the same LR(0)
# core (but with different lookahead) into one item with a set of lookahead
# symbols.

# ## LALR1 Item
# As we stated above, we keep a set of lookahead symbols instead of one.

class LALR1Item(Item):
    def __init__(self, name, expr, dot, sid, lookaheads):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid
        self.lookaheads = lookaheads

    def core(self):
        return tuple((self.name, self.expr, self.dot))

    def __repr__(self):
        return f"({self.show_dot(self.name, self.expr, self.dot)}, {self.lookaheads} : {self.sid})"

    def __str__(self):
        return f"{self.show_dot(self.name, self.expr, self.dot)}:{','.join(sorted(self.lookaheads))}"

# ## LALR1 DFA
class LALR1DFA(LR1DFA):
    def __init__(self, g, start):
        self.item_sids = {} # debugging convenience only
        self.states = {}
        self.grammar = g
        self.start = start
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self._get_production_rules(g)
        self.first, self.follow, self.nullable = get_first_and_follow(g)

# LALR1DFA creating a new state is similar to before, but with an additional
# wrinkle. We update the lookahead symbols when creating a new state if the
# LR(0) core is the same. Furthermore, we merge those states that *differ only
# on the lookahead symbols of their items*.
class LALR1DFA(LALR1DFA):
    def new_item(self, name, texpr, pos, lookaheads):
        item = LALR1Item(name, texpr, pos, self.sid_counter, lookaheads)
        self.sid_counter += 1
        return item

    def create_item(self, name, expr, pos, lookaheads):
        assert isinstance(lookaheads, set)
        texpr = tuple(expr)
        key = (name, expr, pos, tuple(sorted(lookaheads)))
        if key not in self.my_items:
            self.my_items[key] = self.new_item(name, expr, pos, lookaheads)
        return self.my_items[key]

    def merge_items_by_core(self, core_items, items):
        # core_items == items in terms of core for state merge.
        # but we could also get a single item from compute_closure
        modified = False
        for item in items:
            core_item  = core_items[item.core()]
            if core_item.lookaheads != item.lookaheads:
                modified = True
                core_item.lookaheads.update(item.lookaheads)
        return modified

    # called by advance() and create_start()
    def create_state(self, items_):
        items = self.compute_closure(items_)
        key = str([str(item) for item in items])
        if key not in self.my_states:
            state = self.new_state(items)
            self.states[state.sid] = state
            self.my_states[key] = state
        else:
            # if the state was already created, we merge the
            # current one to it, and update the lookahead.
            state = self.my_states[key]
            core_items = {item.core():item for item in state.items}
            self.merge_items_by_core(core_items, items)
        return state

# ## LALR1 Closure
# Note how we have to keep reprocessing the items until the lookahead symbols
# are completely processed. This is because the `first_of_rule()` return can
# change with new lookahead symbols on current item.
class LALR1DFA(LALR1DFA):
    def compute_closure(self, items):
        to_process = list(items)
        seen = set()
        core_items = {}
        while to_process:
            item_, *to_process = to_process
            if str(item_) in seen: continue
            seen.add(str(item_))
            core_items[str(item_)] = item_
            key = item_.at_dot()
            if key is None or not fuzzer.is_nonterminal(key): continue

            remaining = list(item_.remaining())
            lookaheads = set()
            for lookahead in item_.lookaheads:
                l = first_of_rule(remaining + [lookahead], self.first, self.nullable)
                lookaheads.update(l)

            for rule in self.grammar[key]:
                new_item = self.create_start_item(key, rule, lookaheads)
                if str(new_item) not in core_items:
                    to_process.append(new_item)
                else:
                    modified = self.merge_items_by_core(core_items, [new_item])
                    if modified:
                        to_process.append(saved_item)

        return list(core_items.values())

    def create_start_item(self, s, rule, lookaheads):
        return self.new_item(s, tuple(rule), 0, lookaheads)

    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule, {'$'}) for rule in self.grammar[s]]
        return self.create_state(items)

    def advance_item(self, item):
        return self.create_item(item.name, item.expr, item.dot+1, item.lookaheads)

    def add_reduce(self, item, dfastate):
        N = self.productions[self.get_key((item.name, list(item.expr)))]
        for lookahead in item.lookaheads:
            self.add_reduction(dfastate, lookahead, N, 'reduce')

# The parser itself is no different from other parsers.
class LALR1Parser(LR0Parser):
    pass

# Grammars
g4 = {
        '<S>': [['<I>', '*', '<E>'],
                ['1']],
        '<I>': [['1']],
        '<E>' : [['<I>'], ['0']]
}

g4_start = '<S>'

# Usage example:
if __name__ == '__main__':
    g4a, g4a_start = add_start_state(g4, g4_start)
    my_dfa = LALR1DFA(g4a, g4a_start)
    table = my_dfa.build_dfa()
    parser = LALR1Parser(my_dfa)

    print("LALR(1) Production Rules:")
    for k in my_dfa.production_rules:
        print(k, my_dfa.production_rules[k])

    print("\nLALR(1) States:")
    for k in my_dfa.states:
        print(k)
        for v in my_dfa.states[k].items:
            print('', v)

    print("\nLALR(1) Parse Table:")
    rowh = parser.parse_table[0]
    print('State\t', '\t'.join([repr(c) for c in rowh.keys()]))
    for i, row in enumerate(parser.parse_table):
        print(f"{i}\t", '\t'.join([str(row[c]) for c in row.keys()]))

# Let us view it
if __name__ == '__main__':
    def lookup(i):
        return str(i) + '\n' + '\n'.join([str(k) for k in my_dfa.states[i].items])
    table = parser.parse_table
    g = to_graph(table, lookup)
    __canvas__(str(g))


# Testing
if __name__ == '__main__':
    print("\nTesting LALR(1) Parser:")
    test_strings = ["1", "11*1", "1*0"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, g4a_start)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# **Note:** The following resources helped me quite a bit in debugging. [SLR](https://jsmachines.sourceforge.net/machines/slr.html) and [LR](https://jsmachines.sourceforge.net/machines/lr1.html),
# [grammar checker](http://smlweb.cpsc.ucalgary.ca), [new checker](https://mdaines.github.io/grammophone/).
# 
# For LALR(1), it took me some time to understand that we do not merge items
# with same LR(0) cores globally. For example see [this grammar](https://smlweb.cpsc.ucalgary.ca/lalr1.php?grammar=S%27+-%3E+S.%0AS+-%3E+A+a%0A++%7C+b+A+c%0A++%7C+d+c%0A++%7C+b+d+a.%0AA+-%3E+d.&substs=)
# State 5 and State 8. The item `A -> d.` has different lookahead symbols (a and c) in these states.
# 
# # References
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008
