# ---
# published: true
# title: A Shift-Reduce LR0 Parser
# layout: post
# comments: true
# tags: parsing gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of a simple shift-reduce
# LR(0) Parser in Python. The Python interpreter is embedded so that you can
# work through the implementation steps.
#
# An LR parser is a bottom-up parser. The *L* stands for scanning the input
# left-to-right, and the *R* stands for constructing a rightmost derivation.
# This contrasts with LL parsers which are again left-to-right but construct
# the leftmost derivation.
# 
# We are implementing LR(0) which means that the decisions on which state to
# transition to are determined exclusively on the current parsed prefix. There
# is no lookahead.

# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.

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

# We use the random choice to extract derivation trees from the parse forest.
import random

# Pydot is needed for drawing
import pydot

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar
# style. That is, given below is a simple grammar for nested parenthesis.
# 
# ```
# <P> := '(' <P> ')'
#      | '(' <D> ')'
# <D> := 0 | 1
# ```
# Equivalently,

paren_g = {
        '<P>' : [['(', '<P>', ')'],
                 ['(', '<D>', ')']],
        '<D>' : [['0'],['1']]
}
# Here is another gramamr. Here, we extend the grammar with the augmented
# stard sybmol `S``
# 
# ```
#  <S`> := <S>
#  <S>  := 'a' <A> 'c'
#        | 'b' '<A>' 'd' 'd'
#  <A>  := 'b'
# ```
# Again, equivalently, we have

S_g = {'<S`>': [['<S>', '$']],
        '<S>': [ ['a', '<A>', 'c'],
                 ['b', '<A>', 'd', 'd']],
        '<A>': [ ['b']]}
S_s = '<S`>'
# We can list the grammar production rules as follows:

if __name__ == '__main__':
    i = 1
    for k in S_g:
        for r in S_g[k]:
            print(i, k, r)
            i+=1

# The main difference between an LR parser and an LL parser is that an LL
# parser uses the current nonterminal and the next symbol to determine the
# production rule to apply. In contrast, the LR parser uses the current
# viable prefix and the next symbol to determine the next action to take.
# 
# The viable-prefix is the string prefix that has been currently recognized.
# This recognition is accomplished by the LR automata, which we describe next.
# 
# But before that, let us start slow. If we are going for a naive translation
# of the grammar into an automata, this is what we could do. That is, we start
# with the starting production rule
# `S' -> S`. Since we are starting to parse, let us indicate the parse point
# also, which would be before `S` is parsed. That is, `S' -> .S`. The period
# represents the current parse point. If we somehow parsed `S` now, then we
# would transition to an accept state. This is represented by `S' -> S.`.
# However, since the transition is a nonterminal, it can't happen by reading
# the corresponding symbol `S` from the input stream. It has to happen through
# another path. Hence, we indicate this by a dashed line. Next, when the parse
# is at `S' -> .S`, any of the expansions of `S` can now be parsed. So, we add
# each expansion of `S` as $$\epsilon$$ transition away. These are
# `S := . a A c` and `S := . b A d d`. Continuing in this fashion, we have: 

if __name__ == '__main__':
    __canvas__('''
    digraph NFA {
     rankdir=TB;
     node [shape = rectangle];
     start [shape = point];
     
     // States
     S0 [label = "S' := . S"];
     SF [label = "S' := S .", shape = doublecircle];
     S1 [label = "S := . a A c"];
     S2 [label = "S := . b A d d"];
     S3 [label = "S := a . A c"];
     S4 [label = "S := a A . c"];
     S5 [label = "S := a A c ."];
     S6 [label = "S := b . A d d"];
     S7 [label = "S := b A . d d"];
     S8 [label = "S := b A d . d"];
     S9 [label = "S := b A d d ."];
     A1 [label = "A := . b"];
     A2 [label = "A := b ."];
     
     // Regular transitions
     start -> S0;
     S0 -> S1 [label = "ε"];
     S0 -> S2 [label = "ε"];
     S1 -> S3 [label = "a"];
     S3 -> A1 [label = "ε"];
     S4 -> S5 [label = "c"];
     S2 -> S6 [label = "b"];
     S6 -> A1 [label = "ε"];
     S7 -> S8 [label = "d"];
     S8 -> S9 [label = "d"];
     A1 -> A2 [label = "b"];
     
     // Nonterminal transitions (dashed)
     edge [style = dashed];
     S0 -> SF [label = "S"];
     S3 -> S4 [label = "A"];
     S6 -> S7 [label = "A"];
    }''')

# Notice that this NFA is not complete. For example, what happens when `A := b .`
# is complete? Then, the parse need to transition to a state that has just
# completed `A`. For example, `S := a A . c` or `S := b A . d d`. Here is how
# it looks like.

if __name__ == '__main__':
   __canvas__('''
   digraph NFA {
     rankdir=TB;
     node [shape = rectangle];
     start [shape = point];
     
     // States
     S0 [label = "S' := . S"];
     SF [label = "S' := S .", shape = doublecircle];
     S1 [label = "S := . a A c"];
     S2 [label = "S := . b A d d"];
     S3 [label = "S := a . A c"];
     S4 [label = "S := a A . c"];
     S5 [label = "S := a A c ."];
     S6 [label = "S := b . A d d"];
     S7 [label = "S := b A . d d"];
     S8 [label = "S := b A d . d"];
     S9 [label = "S := b A d d ."];
     A1 [label = "A := . b"];
     A2 [label = "A := b ."];
     
     // Regular transitions
     start -> S0;
     S0 -> S1 [label = "ε"];
     S0 -> S2 [label = "ε"];
     S1 -> S3 [label = "a"];
     S3 -> A1 [label = "ε"];
     S4 -> S5 [label = "c"];
     S2 -> S6 [label = "b"];
     S6 -> A1 [label = "ε"];
     S7 -> S8 [label = "d"];
     S8 -> S9 [label = "d"];
     A1 -> A2 [label = "b"];
     
     // Nonterminal transitions (dashed)
     edge [style = dashed];
     S0 -> SF [label = "S"];
     S3 -> S4 [label = "A"];
     S6 -> S7 [label = "A"];
     
     // Red arrows for completed rules
     edge [color = red, constraint = false, style = solid];
     A2 -> S4 [label = "completion"];
     A2 -> S7 [label = "completion"];
     S5 -> SF [label = "completion"];
     S9 -> SF [label = "completion"];
    }''')

# As before, the dashed arrows represent non-terminal transitions that are
# actually completed through other paths. The red arrows represent reductions.
# You will notice that there can be multiple reductions from the same
# item. At this point, this NFA over-approximates our grammar.
# The right reduction needs to chosen based on the prefix so far, and we
# will see how to do this later.
# 
# While this is reasonable, it is not very useful. For one, it is an NFA,
# over-approximating the grammar, and secondly, there can be multiple possible
# paths for a given prefix.  Hence, it is not very optimal.
# Let us next see how to generate a DFA instead.
# 
# ## LR0 Automata
#  An LR automata is composed of multiple states, and each state represents a set
# of items that indicate the parsing progress. The states are connected together
# using transitions which are composed of the terminal and nonterminal symbols
# in the grammar.
# 
# To construct the LR automata, one starts with the initial state containing the
# augmented start symbol (if necessary), and we apply closure to expand the
# context. For the closure, we simply merge all epsilon transitions to current
# item.
# 
# ### Closure
# A closure to represents all possible parse paths at a given
# point. The idea is to look at the current parse progress; Identify any
# nonterminals that need to be expanded next, and add the production rules of that
# nonterminal to the current item, with parse point (dot) at the beginning.
# 
# For example, given the first state, where `*` represent the parse progress
#  
# ```
# <S`> := * <S>
# ```
# Applying closure, we expand `<S>` further.
#  
# ```
# <S`> := * <S>
# <S>  := * a <A> c
# <S>  := * b <A> d d
# ```
# No more nonterminals to expand. Hence, this is the closure of the first state.
# 
# Consider what happens when we apply a transition of `a` to this state.
# 
# ```
# <S> := a * A c
# ```
# Now, we apply closure
# ```
# <S> := a * A c
# <A> := * b
# ```
# 
# This gives us the following graph with each closure, and the transitions indicated. Note that
# the nonterminal transitions are dashed.

if __name__ == '__main__':
    __canvas__('''
    digraph ParsingAutomaton {
    rankdir=TB;

    // Node definitions with labels
    node [shape=rectangle];

    // State definitions with reduction instructions
    0 [label="I0:\nS' → • S\nS → • a A c\nS → • b A d d"];
    1 [label="I1:\nS' → S •\n[Accept]"];
    2 [label="I2:\nS → a • A c\nA → • b"];
    3 [label="I3:\nS → b • A d d\nA → • b"];
    4 [label="I4:\nS → a A • c"];
    5 [label="I5:\nA → b •"];
    6 [label="I6:\nS → b A • d d"];
    7 [label="I7:\nS → a A c •"];
    8 [label="I8:\nS → b A d • d"];
    9 [label="I9:\nS → b A d d •"];

    // Edge definitions with labels
    0 -> 2 [label="a"];
    0 -> 3 [label="b"];
    0 -> 1 [label="S", style=dashed];

    2 -> 5 [label="b"];
    2 -> 4 [label="A", style=dashed];

    3 -> 5 [label="b"];
    3 -> 6 [label="A", style=dashed];

    4 -> 7 [label="c"];

    5 -> 4 [label="A", color=red]; // GOTO after reduction in state 5
    5 -> 6 [label="A", color=red]; // GOTO after reduction in state 5

    6 -> 8 [label="d"];

    7 -> 1 [label="S", color=red]; // GOTO after reduction in state 7

    8 -> 9 [label="d"];

    9 -> 1 [label="S", color=red]; // GOTO after reduction in state 9
    }''')

# This is the basic automaton. However, you may notice that there are two types
# of nodes in this diagram. The first one represents partial parses which
# contain the dot at a position other than the end, and the second one
# represents a complete parse of a rule with the dot at the end. You will also
# note that the complete parse nodes seem to have red outgoing arrows, and
# at least in one, multiple red outgoing arrows. That is, it is not a true
# DFA. The next state to transition to is actually chosen based on the path
# the input string took through the DFA with the help of a stack.
# Let us now represent these states step by step.

# State 0
# This is the initial state. It transitions into State 2 or State 3 based
# on the input symbol. Note that we save the current state in the stack
# before transitioning to the next state after consuming one token.

def state_0(stack, input_string):
    rule = ['S`', ['S'], 0]
    stack.append(0)
    symbol = input_string[0]
    if symbol == 'a': return state_2(stack, input_string[1:])
    elif symbol == 'b': return state_3(stack, input_string[1:])
    else: raise Exception("Expected 'a' or 'b'")

# State 1
# This is the acceptor state.
def state_1(stack, input_string):
    rule = ['S`', ['S'], 1]
    stack.append(1)
    symbol = input_string[0]
    if symbol == '$': print("Input accepted.")
    else: raise Exception("Expected end of input")

# State 2 which is the production rule `S -> a . A c` just after consuming `a`.
# We need `b` to transition to State 5 which represents a production rule of A.
def state_2(stack, input_string):
    rule = ['S', ['a', 'A', 'c'], 1]
    stack.append(2)
    symbol = input_string[0]
    if symbol == 'b': return state_5(stack, input_string[1:])
    else: raise Exception("Expected 'b'")

# State 3 which is the production rule `S -> b . A d d` just after consuming `b`.
def state_3(stack, input_string):
    rule = ['S', ['b', 'A', 'd', 'd'], 1]
    stack.append(3)
    symbol = input_string[0]
    if symbol == 'b': return state_5(stack, input_string[1:])
    else: raise Exception("Expected 'b'")

# State 4 which is the production rule `S -> a A.  c` just after consuming `a`.
def state_4(stack, input_string):
    rule = ['S', ['a', 'A', 'c'], 2]
    stack.append(4)
    symbol = input_string[0]
    if symbol == 'c': return state_7(stack, input_string[1:])
    else: raise Exception("Expected 'c'")

# State 5 which is the production rule `A -> b .`. That is, it has completed
# parsing A, and now need to decide which state to transition to. This is
# decided by what was in the stack before. We simply pop off as many symbols
# as there are tokens in the RHS of the production rule, and check the
# remaining top symbol.
def state_5(stack, input_string):
    stack.append(5)
    rule = ['A', ['b']]
    for _ in range(len(rule[1])): stack.pop()  # Pop state 'b', 5
    if stack[-1] == 2: return state_4(stack, input_string)
    elif stack[-1] == 3: return state_6(stack, input_string)
    else: raise Exception(position, "Invalid state during reduction by A → b")

# State 6 `S -> b A . d d`
def state_6(stack, input_string):
    stack.append(6)
    rule = ['S', ['b', 'A', 'd', 'd'], 2]
    symbol = input_string[0]
    if symbol == 'd': return state_8(stack, input_string[1:])
    else: raise Exception("Expected 'd'")

# State 7 is a reduction rule `S -> a A c .`
def state_7(stack, input_string):
    stack.append(7)
    rule = ['S', ['a', 'A', 'c'], 3]
    for _ in range(len(rule[1])): stack.pop() # Pop 'c', 7; 'A', 4; 'a', 2

    if stack[-1] == 0: return state_1(stack, input_string)
    else: raise Exception("Invalid state during reduction by S → a A c")

# State 8 `S -> b A d . d`
def state_8(stack, input_string):
    rule = ['S', ['b', 'A', 'd', 'd'], 3]
    stack.append(8)
    symbol = input_string[0]
    if symbol == 'd': return state_9(stack, input_string[1:])
    else: raise Exception("Expected 'd'")

# State 9 is a reduction rule `S -> b A d d .`
def state_9(stack, input_string):
    stack.append(9)
    rule = ['S', ['b', 'A', 'd', 'd']]
    for _ in range(len(rule[1])): stack.pop() # Pop 'd', 9; 'd', 8; 'A', 6; 'b', 3
    if stack[-1] == 0: return state_1(stack, input_string)
    else: return Exception("Invalid state during reduction by S → b A d d")

# Let us now verify if our parser works.
if __name__ == '__main__':
    test_strings = [("abc", True), ("bbdd", True), ("bdd", False), ("baddd", False)]

    for test_string, res in test_strings:
        print(f"Parsing: {test_string}")
        input_string = list(test_string) + ['$']
        try:
            val = state_0([], input_string)
        except Exception as e:
            if res: print(e)

# # Building the NFA
# Now, let us try and build these dynamically.
# We first build an NFA of the grammar. For that, we begin by adding a new
# state `<>` to grammar.
# First, we add a start extension to the grammar.

def add_start_state(g, start, new_start='<>'):
    new_g = dict(g)
    new_g[new_start] = [[start]]
    return new_g, new_start

# Two sample grammars.
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
# data structure. We define a unique id.

# We also need the symbols in a given grammar.

def symbols(g):
    terminals = {}
    for k in g:
        for rule in g[k]:
            for t in rule:
                if fuzzer.is_nonterminal(t): continue
                terminals[t] = True
    return list(sorted(terminals.keys())), list(sorted(g.keys()))

# ## State
# We first define our state data structure.
# A state for an NFA is simply a production rule and a parse position.
class State:
    def __init__(self, name, expr, dot, sid):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid

    def finished(self):
        return self.dot >= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot < len(self.expr) else None

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

    def main_item(self):
        return (self.name, list(self.expr))

# It can be tested this way
if __name__ == '__main__':
    s = State('<S`>', ('<S>'), 0, 0)
    print(s.at_dot())
    print(str(s))
    print(s.finished())


# Next, we build an NFA out of a given grammar. An NFA is composed of
# different states connected together by transitions.

class NFA:
    def __init__(self, g, start):
        self.states = {}
        self.g = g
        self.productions, self.production_rules = self.get_production_rules(g)
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_states = {}
        self.terminals, self.non_terminals = symbols(g)
        self.sid_counter = 0

    def get_key(self, kr):
        return "%s -> %s" %kr

    def new_state(self, name, texpr, pos):
        state = State(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return state

    def get_production_rules(self, g):
        productions = {}
        count = 0
        production_rules = {}
        for k in self.g:
            for r in self.g[k]:
                production_rules["r:%d" % count] = (k, r)
                productions[self.get_key((k, r))] = count
                count += 1
        return productions, production_rules

    # create starting states for the given key
    def create_start(self, s):
        rules = self.g[s]
        return [self.create_state(s, tuple(rule), 0) for rule in self.g[s]]

    def create_state(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_states:
            state = self.new_state(name, texpr, pos)
            self.my_states[(name, texpr, pos)] = state
            self.states[state.sid] = state
        return self.my_states[(name, texpr, pos)]

# Let us test this.
if __name__ == '__main__':
    my_nfa = NFA(S_g, S_s)
    st = my_nfa.create_start(S_s)
    assert str(st[0]) == '<S`>::= | <S> $'
    my_nfa = NFA(g1, g1_start)
    st = my_nfa.create_start(g1_start)
    assert str(st[0]) == '<S>::= | <A> <B>'
    assert str(st[1]) == '<S>::= | <C>'

# ## find_transitions
# Next, for processing a state, we need a few more tools. First,we need
# to be able to advance a state.
class NFA(NFA):
    def symbol_transition(self, state):
        key = state.at_dot()
        assert key is not None
        new_state = self.advance(state)
        return new_state

    def advance(self, state):
        return self.create_state(state.name, state.expr, state.dot+1)

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

# processing the state itself for its transitions. First, if the
# dot is before a symbol, then we add the transition to the advanced
# state with that symbol as the transition. Next, if the key at
# the dot is a nonterminal, then add all expansions of that nonterminal
# as epsilon transfers.
class NFA(NFA):
    def find_transitions(self, state):
        key = state.at_dot()
        if key is None: return [] # dot after last.
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

# Let us test this.
if __name__ == '__main__':
    my_nfa = NFA(S_g, S_s)
    st = my_nfa.create_start(S_s)
    new_st = my_nfa.find_transitions(st[0])
    assert str(new_st[0]) == "('<S>', (<S`>::= <S> | $ : 1))"
    assert str(new_st[1]) == "('', (<S>::= | a <A> c : 2))"
    assert str(new_st[2]) == "('', (<S>::= | b <A> d d : 3))"


# Next, a utility method. Given a key, we want to get all items
# that contains the parsing of this key.
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

# Let us test this.
if __name__ == '__main__':
    my_nfa = NFA(S_g, S_s)
    lst = my_nfa.get_all_rules_with_dot_after_key('<A>')
    assert str(lst) == '[(<S>::= a <A> | c : 0), (<S>::= b <A> | d d : 1)]'

# Now, we can build the NFA.
class NFA(NFA):
    def build_nfa(self):
        t_symbols, nt_symbols = symbols(self.g)
        start_item = self.create_start(self.start)[0]
        queue = [('$', start_item)]
        seen = set()
        while queue:
            (pkey, state), *queue = queue
            if str(state) in seen: continue
            seen.add(str(state))

            new_states = self.find_transitions(state)
            for key, s in new_states:
                # if the key is a nonterminal then it is a goto
                if key == '':
                    self.add_child(state, key, s, 'shift')
                elif fuzzer.is_nonterminal(key):
                    self.add_child(state, key, s, 'goto')
                else:
                    self.add_child(state, key, s, 'shift')

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, find the main_def (for NFA, there is only one),
            # and add its number as the rN
            if state.finished():
                N = self.productions[self.get_key((state.name, list(state.expr)))]
                # follow_set = follow(item.name, self.g)  # Compute FOLLOW set
                for k in self.terminals:
                    self.add_reduction(state, k, N, 'reduce')

                # Also, (only) for the graph, collect epsilon transmition to all
                # rules that are after the given nonterminal at the head.
                key = state.def_key()
                list_of_return_states = self.get_all_rules_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(state, '', s, 'to') # reduce to
                    # these are already processed. So we do not add to queue

            queue.extend(new_states)
        # now build the nfa table.
        state_count = len(self.states.keys())
        nfa_table = [[] for _ in range(state_count)]
        for i in range(0, state_count):
            nfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in nfa_table[parent]: nfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in nfa_table[parent][key]:
                nfa_table[parent][key].append(v)

        return nfa_table

    def add_reduction(self, p, key, c, notes):
        self.children.append((p.sid, key, c, notes))

    def add_child(self, p, key, c, notes):
        self.children.append((p.sid, key, c.sid, notes))



# Let us test the build_nfa

if __name__ == '__main__':
    my_nfa = NFA(S_g, S_s)
    table = my_nfa.build_nfa()
    rowh = table[0]
    print('>', '\t','\t'.join([repr(c) for c in rowh.keys()]))
    for i,row in enumerate(table):
        print(i, '\t','\t'.join([str(row[c]) for c in row.keys()]))
    print()

# Show graph

def to_graph(nfa_tbl):
    G = pydot.Dot("my_graph", graph_type="digraph")
    for i, state in enumerate(nfa_tbl):
        # 0: a:s2 means on s0, on transition with a, it goes to state s2
        shape = 'rectangle'# rectangle, oval, diamond
        label = str(i)
        # if the state contains 'accept', then it is an accept state.
        for k in state:
            if  'accept' in state[k]: shape='doublecircle'
        G.add_node(pydot.Node(label, label=label, shape=shape, peripheries='1'))
            #peripheries= '2' if i == root else '1')
        for transition in state:
            cell = state[transition]
            if not cell: continue
            color = 'black'
            style='solid'
            for state_name in cell:
                # state_name = cell[0]
                transition_prefix = ''
                if state_name == 'accept':
                    continue
                elif state_name[0] == 'g':
                    color='blue'
                    transition_prefix = '(g) '
                    style='dashed'
                elif state_name[0] == 'r':
                    # reduction is not a state transition.
                    # color='red'
                    # transition_prefix = '(r) '
                    continue
                elif state_name[0] == 't':
                    color='green'
                    transition_prefix = '(t) '
                else:
                    assert state_name[0] == 's'
                    transition_prefix = '(s) '
                G.add_edge(pydot.Edge(label,
                          state_name[1:],
                          color=color,
                          style=style,
                          label=transition_prefix + transition))
    return G
# Let us test our NFA.
if __name__ == '__main__':
    my_nfa = NFA(S_g, S_s)
    table = my_nfa.build_nfa()
    for k in my_nfa.states:
      print(k, my_nfa.states[k])
    g = to_graph(table)
    __canvas__(str(g))

# Next, we need to build a DFA.
# 
# # Building the DFA
# For DFA, a state is no longer a single item. So, let us define item separately.

class Item(State): pass

# A DFAState contains many items.
class DFAState:
    def __init__(self, items, dsid):
        self.sid = dsid
        # now compute the closure.
        self.items = items

    def def_keys(self):
        #assert len(self.items) == 1 # completion
        return [i.def_key() for i in self.items]

    # there will be only one item that has an at_dot != None
    def main_item(self):
        for i in self.items:
            if i.at_dot() is not None:
                return i
        # assert False the <> will be None
        return self.items[0]

    def __repr__(self):
        return '(%s)' % self.sid

    def __str__(self):
        return str(sorted([str(i) for i in self.items]))

# We define our DFA initialization.

class LR0DFA(NFA):
    def __init__(self, g, start):
        self.items = {}
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self.get_production_rules(g)

# The start item is similar to before. The main difference is that
# rather than returning multiple states, we return a single state containing
# multiple items.
class LR0DFA(LR0DFA):
    def new_item(self, name, texpr, pos):
        item =  Item(name, texpr, pos, self.sid_counter)
        self.sid_counter += 1
        return item

    def create_start_item(self, s, rule):
        return self.new_item(s, tuple(rule), 0)

    # the start in DFA is simply a closure of all rules from that key.
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule) for rule in self.g[s] ]
        return self.create_state(items) # create state does closure

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
            # no closure for terminals
            if not fuzzer.is_nonterminal(key): continue
            for rule in self.g[key]:
                new_item = self.create_start_item(key, rule)
                to_process.append(new_item)
        return list(new_items.values())

    def create_state(self, items):
        texpr = tuple(sorted([str(i) for i in items]))
        if (texpr) not in self.my_states:
            state = DFAState(self.compute_closure(items), self.dsid_counter)
            self.dsid_counter += 1
            self.my_states[texpr] = state
            self.states[state.sid] = state
        return self.my_states[texpr]

# Let us test this.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    st = my_dfa.create_start(g1a_start)
    assert [str(s) for s in st.items] == \
            ['<>::= | <S>',
             '<S>::= | <A> <B>',
             '<S>::= | <C>',
             '<A>::= | a',
             '<C>::= | c']

# Next, we define the transitions.
class LR0DFA(LR0DFA):
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

    def create_item(self, name, expr, pos):
        texpr = tuple(expr)
        if (name, texpr, pos) not in self.my_items:
            item = self.new_item(name, texpr, pos)
            self.my_items[(name, texpr, pos)] = item
            self.items[item.sid] = item
        return self.my_items[(name, texpr, pos)]

    def advance_item(self, state):
        return self.create_item(state.name, state.expr, state.dot+1)

    def find_transitions(self, dfastate):
        new_dfastates = []
        # first add the symbol transition, for both
        # terminal and nonterminal symbols
        for k in (self.terminals + self.non_terminals):
            new_dfastate = self.symbol_transition(dfastate, k)
            if new_dfastate is None: continue
            # add it to the states returned
            new_dfastates.append((k, new_dfastate))
        return new_dfastates

# Let us test this.
if __name__ == '__main__':
    my_dfa = LR0DFA(g1a, g1a_start)
    st = my_dfa.create_start(g1a_start)
    assert [str(s) for s in st.items] == \
            ['<>::= | <S>', '<S>::= | <A> <B>', '<S>::= | <C>', '<A>::= | a', '<C>::= | c']
    sts = my_dfa.find_transitions(st)
    assert [(s[0],[str(v) for v in s[1].items]) for s in sts] == \
            [('a', ['<A>::= a |']),
             ('c', ['<C>::= c |']),
             ('<A>', ['<S>::= <A> | <B>', '<B>::= | b']),
             ('<C>', ['<S>::= <C> |']),
             ('<S>', ['<>::= <S> |'])]
    

# Bringing all these together, let us build the DFA.

class LR0DFA(LR0DFA):
    def get_all_states_with_dot_after_key(self, key):
        states = []
        for s in self.states:
            i =  self.states[s].main_item()
            if i.expr[i.dot-1] == key:
                states.append(self.states[s])
        return states

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
                # if the key is a nonterminal then it is a goto
                if fuzzer.is_nonterminal(key):
                    self.add_child(dfastate, key, s, 'goto')
                else:
                    self.add_child(dfastate, key, s, 'shift')

            # Add reductions for all finished items
            # this happens when the dot has reached the end of the rule.
            # in this case, (LR(0)) there should be only one.
            # and add its number as the rN
            for item in dfastate.items:
                if not item.finished(): continue
                N = self.productions[self.get_key((item.name, list(item.expr)))]
                terminal_set = self.terminals
                # terminal_set = follow(item.name, self.g)
                for k in terminal_set:
                    self.add_reduction(dfastate, k, N, 'reduce')

                # Also, (only) for the graph, collect epsilon transmission to all
                # rules that are after the given nonterminal at the head.
                key = item.def_key()
                list_of_return_states = self.get_all_states_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(dfastate, '', s, 'to') # reduce
                    # these are already processed. So we do not add to queue

            queue.extend(new_dfastates)

        # now build the dfa table.
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in dfa_table[parent]: dfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in dfa_table[parent][key]:
                dfa_table[parent][key].append(v)

        return dfa_table


# Let us test building the DFA.
if __name__ == '__main__':
    my_dfa = LR0DFA(S_g, S_s)
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
    g = to_graph(table)
    __canvas__(str(g))

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
                i = self.dfa.states[state].main_item()
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
    my_dfa = LR0DFA(S_g, S_s)
    parser = LR0Recognizer(my_dfa)
    # Test the parser with some input strings
    test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message = parser.parse(test_string, S_s)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# Attaching parse tree extraction.
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
                i = self.dfa.states[state].main_item()
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
    my_dfa = LR0DFA(S_g, S_s)
    parser = LR0Parser(my_dfa)
    # Test the parser with some input strings
    test_strings = ["abc", "bbdd", "baddd", "aac", "bdd"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, S_s)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# Next, let us consider the following grammar.
G2_g = {
        '<S`>' : [['<S>', '$']],
        '<S>' :  [['a', '<B>', 'c'],
                  ['a', '<D>', 'd']],
        '<B>' :  [[ 'b']],
        '<D>' :  [['b']]
        }
G2_s = '<S`>'

# Let us build the parse table.
if __name__ == '__main__':
    my_dfa = LR0DFA(G2_g, G2_s)
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

# As you can see, on State 3, we have a two possible reductions -- r3 and r4.
# This is called a reduce/reduce conflict. The issue is that when we come to
# state 3, that is.

# ```
# <B>::= b |
# <D>::= b |
# ```
# We have two possible choices of reduction. We can either reduce to `<B>` or
# to `<D>`. To determine which one to reduce to, we need a lookahead. If the
# next token is `c`, then we should reduce to `<B>`. If the next one is `d`,
# we should reduce to `<D>`. This is what SLR parsers do.
# 
# ## SLR1 Automata
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

# Testing it.
if __name__ == '__main__':
    first, follow, nullable = get_first_and_follow(nullable_grammar)
    print("first:", first)
    print("follow:", follow)
    print("nullable", nullable)

# At this point, we can update our parsing algorithm.
class SLR1DFA(LR0DFA):
    def __init__(self, g, start):
        self.items = {}
        self.states = {}
        self.g = g
        self.start = start
        self.nfa_table = None
        self.children = []
        self.my_items = {}
        self.my_states = {}
        self.sid_counter = 0
        self.dsid_counter = 0
        self.terminals, self.non_terminals = symbols(g)
        self.productions, self.production_rules = self.get_production_rules(g)
        self.first, self.follow, self.nullable = get_first_and_follow(g)

# Next, we build the dfa. There is only one change. (See CHANGED) When reducing,
# we only reduce if the token lookahead is in the follow set.
class SLR1DFA(SLR1DFA):
    def build_dfa(self):
        start_dfastate = self.create_start(self.start)
        queue = [('$', start_dfastate)]
        seen = set()
        while queue:
            (pkey, dfastate), *queue = queue
            if str(dfastate) in seen: continue
            seen.add(str(dfastate))

            new_dfastates = self.find_transitions(dfastate)
            
            # Add shifts and gotos
            for key, s in new_dfastates:
                if fuzzer.is_nonterminal(key):
                    self.add_child(dfastate, key, s, 'goto')
                else:
                    self.add_child(dfastate, key, s, 'shift')

            # Add reductions for all finished items
            for item in dfastate.items:
                if not item.finished(): continue
                N = self.productions[self.get_key((item.name, list(item.expr)))]
                terminal_set = self.follow[item.name]  # <-- CHANGED HERE
                for k in terminal_set:
                    self.add_reduction(dfastate, k, N, 'reduce')

                # Add "to" transitions for the graph
                key = item.def_key()
                list_of_return_states = self.get_all_states_with_dot_after_key(key)
                for s in list_of_return_states:
                    self.add_child(dfastate, '', s, 'to')

            queue.extend(new_dfastates)

        # Build the DFA table
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        
        # Resolve conflicts and build the table
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:'
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            else: continue
            if key not in dfa_table[parent]: dfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in dfa_table[parent][key]:
                dfa_table[parent][key].append(v)

        return dfa_table

# Let us see if it works.
if __name__ == '__main__':
    my_dfa = SLR1DFA(G2_g, G2_s)
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

# There is no difference in the parser.

class SLR1Parser(LR0Parser): pass

# Let us try parsing with it.
G2_g = {
        '<S`>' : [['<S>', '$']],
        '<S>' :  [['a', '<B>', 'c'],
                  ['a', '<D>', 'd']],
        '<B>' :  [[ 'b']],
        '<D>' :  [['b']]
        }
G2_s = '<S`>'

# Parsing
if __name__ == '__main__':
    my_dfa = SLR1DFA(G2_g, G2_s)
    parser = SLR1Parser(my_dfa)
    # Test the parser with some input strings
    test_strings = ["abc", "abd", "aabc"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, S_s)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()

# Now, consider this grammar
LR_g = {
        "<S`>": [["<S>", "$"]],
        "<S>": [
            ["a", "<B>", "c"],
            ["a", "<D>", "d"],
            ["<B>", "d"]
            ],
        "<B>": [["b"]],
        "<D>": [["b"]]
        }
LR_s = '<S`>'

# Let us see if it works.
if __name__ == '__main__':
    my_dfa = SLR1DFA(LR_g, LR_s)
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

# You will notice a conflict in State 5. To resolve this, we need the full
# LR(1) parser.
class LR1Item(State):
    def __init__(self, name, expr, dot, sid, lookahead):
        self.name, self.expr, self.dot = name, expr, dot
        self.sid = sid
        self.lookahead = lookahead

    def __repr__(self):
        return "(%s, %s : %d)" % (str(self), self.lookahead, self.sid)

    def __str__(self):
        return self.show_dot(self.name, self.expr, self.dot)

class LR1DFA(SLR1DFA):
    def get_first(self, lst):
        if fuzzer.is_nonterminal(lst[0]):
            return self.first[lst[0]]
        else: return lst[0]

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
            rest_of_item = item_.expr[item_.dot+1:] + (item_.lookahead,)
            for rule in self.g[key]:
                for lookahead in self.get_first(rest_of_item):
                    new_item = self.create_item(key, rule, 0, lookahead)
                    to_process.append(new_item)
        return list(new_items.values())

# We also need update on create_item
class LR1DFA(LR1DFA):
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
            self.items[item.sid] = item
        return self.my_items[(name, texpr, pos, lookahead)]

# The build_dfa
class LR1DFA(LR1DFA):
    def create_start(self, s):
        assert fuzzer.is_nonterminal(s)
        items = [self.create_start_item(s, rule, '$') for rule in self.g[s]]
        return self.create_state(items)

    def create_start_item(self, s, rule, lookahead):
        return self.new_item(s, tuple(rule), 0, lookahead)

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
                if fuzzer.is_nonterminal(key):
                    self.add_child(dfastate, key, s, 'goto')
                else:
                    self.add_child(dfastate, key, s, 'shift')

            for item in dfastate.items:
                if item.finished():
                    N = self.productions[self.get_key((item.name, list(item.expr)))]
                    self.add_reduction(dfastate, item.lookahead, N, 'reduce')

            queue.extend(new_dfastates)
        # now build the dfa table.
        state_count = len(self.states.keys())
        dfa_table = [[] for _ in range(state_count)]
        t_symbols, nt_symbols = symbols(self.g)
        for i in range(0, state_count):
            dfa_table[i] = {k:[] for k in (t_symbols + nt_symbols + [''])}
        # column is the transition.
        # row is the state id.
        for parent, key, child, notes in self.children:
            if notes == 'reduce': prefix = 'r:' # N not a state.
            elif notes == 'shift': prefix = 's'
            elif notes == 'goto': prefix = 'g'
            elif notes == 'to': prefix = 't'
            if key not in dfa_table[parent]: dfa_table[parent][key] = []
            v = prefix+str(child)
            if v not in dfa_table[parent][key]:
                dfa_table[parent][key].append(v)

        return dfa_table


# the parse class does not change.
class LR1Parser(SLR1Parser): pass

# grammar
LR_g = {
        "<S`>": [["<S>", "$"]],
        "<S>": [
            ["a", "<B>", "c"],
            ["a", "<D>", "d"],
            ["<B>", "d"]
            ],
        "<B>": [["b"]],
        "<D>": [["b"]]
        }
LR_s = '<S`>'

# Parsing
if __name__ == '__main__':
    my_dfa = LR1DFA(LR_g, LR_s)
    parser = LR1Parser(my_dfa)
    # Test the parser with some input strings
    test_strings = ["abc", "abd", "bd"]
    for test_string in test_strings:
        print(f"Parsing: {test_string}")
        success, message, tree = parser.parse(test_string, S_s)
        if tree is not None:
            ep.display_tree(tree)
        print(f"Result: {'Accepted' if success else 'Rejected'}")
        print(f"Message: {message}")
        print()



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
