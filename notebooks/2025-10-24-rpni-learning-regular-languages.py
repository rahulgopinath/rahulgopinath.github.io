# ---
# published: true
# title: Learning Regular Languages with RPNI Algorithm
# layout: post
# comments: true
# tags: regular-grammars induction
# categories: post
# ---
# 
# TLDR; This tutorial is a complete implementation of RPNI algorithm
# which infers the input specification from positive and negative samples.
# Such grammars are can be useful for identifying the specification
# of blackbox programs when it is impossible to query the program
# directly, and only its behaviour on a limited set of samples is known.
# The Python interpreter is embedded so that you
# can work through the implementation steps.
#  
# In my previous posts, I have discussed how to
# [parse with](/post/2023/11/03/matching-regular-expressions/),
# [fuzz with](/post/2021/10/22/fuzzing-with-regular-expressions/), and
# manipulate regular and context-free grammars. However, the availability
# of the input grammars may not be guaranteed in many cases. Often,
# the available documentation may not fully capture the input specification.
# For example, an input field advertizing the
# [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) date format as input may
# accept slight variations, or may not implement the format fully. In such
# cases, one has to rely on the available behaviour to infer the true
# specification.
# 
# Regular Positive and Negative Inference, RPNI for short, is a classical
# algorithm that allows us to determine the input specification from a set
# of positive and negative samples. It was introducd by Oncia and Garcia in
# 1992 [^oncia1992]. The core idea of RPNI is to construct
# a Prefix Tree Acceptor (PTA), then iteratively try and merge
# each state pair, and checking the resulting DFA against negative samples to
# verify that the resulting DFA is not overgenaralizing. Because the new DFA is
# produced by merging states within the DFA, it will continue to accept all
# existing positive samples. The negative samples provide the defense against
# overgeneralization. If any negative samples are accepted, the merging of the
# state pair is rejected. Continuing in this fashion, RPNI will compute the
# DFA that can accept all positive samples, and reject all negative samples.
# 
# To things to note: Every DFA has a characteristic set of samples including
# positive and negative samples, when given to the RPNI algorithm, will result
# in the exact DFA of the blackbox. Secondly, RPNI will also infer the precise
# DFA _in the limit_. Secondly, L* is called an active grammar inference
# algorithm because it is able to query the blackbox, while RPNI is called a
# passive grammar inference algorithm because it cannot query the blackbox.
# 
# # Definitions
# 
# * Input symbol: A single symbol that is consumed by the machine which can move
#   it from one state to another. The set of such symbols is called an alphabet,
#   and is represented by $$ A $$.
# * DFA: A Deterministic Finite-state Automaton is a machine which is a model of
#   an input processor. It is represented as a set of discrete states, and
#   transitions between them. The DFA is initialized to the start state.
# * State: A state is one of the components of the DFA, and represents a
#   particular phase of the machine. A state transitions to another when it is
#   fed an input symbol. Some states are marked as
#   accepting.
# * Accepting State: Starting from the start state, and after consuming all
#   the symbols in the input, the state reached is one of the accept states,
#   then we say that the input was accepted by the machine.
# * Starting State: The machine starts at the start state.
# * Transition: A transition is a link between two states. A DFA transitions
#   from one state to the next on consuming an input symbol.
# * Terminal Symbol: A terminal symbol is a symbol in the alphabet of the
#   language in a regular grammar. It is the equivalnt of DFA transition in the
#   grammar.
# * Nonterminal Symbol: A nonterminal symbol defines the rules of expansion
#   in the grammar. A nonterminal symbol is associated with a definition in
#   the grammar which contains the above rules. It corresponds to a state in
#   the DFA.
# * Definition: A set of rules which can be applied to a nonterminal symbol
#   for expansion.
# * Rule: A single way to expand a nonterminal symbol. In the DFA context,
#   it contains the transition as the token, and the ending state as the
#   final nonterminal symbol.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl

# #### Prerequisites
# 
# We need the fuzzer to generate inputs to parse and also to provide some
# utilities such as conversion of regular expression to grammars, random
# sampling from grammars etc. Hence, we import all that.

import simplefuzzer as fuzzer
import rxcanonical

# # Grammar Inference
# 
# As before, let us assume that the specification to be inferred is
# a [regular language](https://en.wikipedia.org/wiki/Regular_language).
#  
# So, given a list of inputs which contain strings that were accepted
# (postive samples) and rejected (negative samples), and without the ability
# to query the blackbox program, or look inside the blackbox program,
# how do you find what the program accepts? We start by constructing a
# PTA, which is then generalized
# into a
# [DFA](https://en.wikipedia.org/wiki/Deterministic_finite_automaton).
# The intuition here is that the PTA is already an over specialized
# DFA, and all we need to do is to identify which of the states are
# actually the same. So we keep pairing the states, and checking
# whether the constraints, i.e. all negative strings are rejected, hold.
# This is the key intuition for all algorithms that work with positive
# and negative samples only.
# 
## The RPNI Algorithm
# 
# RPNI is a classic algorithm for learning regular languages from positive and
# negative strings. As we mentioned before, the algorithm has two phases.
# 
# 1. Building a Prefix Tree Acceptor: Create a PTA accepting all positive samples
# 2. State Merging: Iteratively merge states to generalize the DFA while holding the constraints.
# 
# ## The Reg Parse
# Before we go further, let us define a few helper functions. First,
# we need to represent a DFA. A Deterministic Finite Automation can
# be adequately represented by a right linear regular grammar. That is,
# each onterminal is equivalent to a state in the DFA. The start symbol
# of the grammar is the entry point for the DFA. Transitions from
# a state `A` to another state `B` is indicated as a rule `<A> := b <B>`.
# That is, state `A` transitions to state B on receiving the token `b`.
# This is represented as a Python dictionary.

# ```
# {
# '<A>'     : [['b', '<B>'], ['c', '<C>']],
# '<B>'     : [['b', '<B>'], []],
# '<C>'     : [[]]
# }
# ```
# 
# As you can noticce in the above representation, the accepting states are
# indicated by adding `[]` to the state. In the above, both `<B>` and `<C>` are
# accepting states. To make it easier to recognize, we insist that `[]` be only
# added as the last rule.
# 
# With this in mind, it becomes easy to define a matcher for this DFA. It is
# close to our original `peg_parse`, but with additional handling for the
# accepting states.
# 
# ## Reg parse
import sys

class dfa_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            if text[at:].startswith(key):
                return (at + len(key), (key, [])) 
            else: return (at, None)
        rules = self.grammar[key]
        for rule in rules:
            if not rule: continue # we process [] separately
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)

        if [] in rules: # process []
            l, res = self.unify_rule([], text, at)
            if res is not None: return l, (key, res)

        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

    def accept(self, start_key, text):
        (at, res) = self.unify_key(start_key, text)
        if res is None: return False
        if at == len(text): return True
        return False

# Let us test the reg parse.
if __name__ == '__main__':
    rgrammar = { '<A>': [['b', '<B>'], ['c', '<C>']],
                 '<B>': [['b', '<B>'], []],
                 '<C>': [[]] }
    rparser = dfa_parse(rgrammar)
    print('All should be accepted')
    for example in ['bbb', 'c', 'bbbb']:
        res = rparser.accept('<A>', example)
        print(res)
    print('All should be rejectd')
    for example in ['abb', 'bc', 'cb']:
        res = rparser.accept('<A>', example)
        print(res)

# ## RPNI Algorithm
# We next detail the RPNI algorithm. The first step is to build the PTA
# 
# ## Building the Prefix Tree Acceptor (PTA)
# 
# We construct a PTA, from all examples.
# 
# ### The PTA data structure
# 
# A PTA is nothing but a simple DFA in the form of a tree.
# We wrap our grammar in a simple class.

KEY_COUNTER = 1
class DFA:
    def __init__(self, start_symbol='<start>'):
        self.grammar = {}
        self.start_symbol = start_symbol
        self.grammar[self.start_symbol] = []

    def transition(self, key, char):
        rules = self.grammar[key]
        for rule in rules:
            if not rule: continue
            if char == rule[0]: return rule
        return None

    def add_transition(self, from_key, token, to_key):
        self.grammar[from_key].append([token, to_key])
    
    def accepts(self, string):
        return dfa_parse(self.grammar).accept(
                self.start_symbol, string)

    def new_state(self):
        global KEY_COUNTER
        key = '<%s>' % KEY_COUNTER
        self.grammar[key] = []
        KEY_COUNTER += 1
        return key

# Build a Prefix Tree Acceptor from positive examples. Given an
# example, we take it apart to characters, then take the first character,
# and identify the transition (i.e. the rule) from start symbol that
# contains the given character. Since this is a new DFA, such a
# transition will not be found. Hence, we create a new rule with a new
# nonterminal. Then, we proceed with the next character in the input the same
# way extending the transitions step by step in the grammar. We mark the
# final nonterminal created as *accepting*.
# 
# From the second example onward, we can start to trace the existing
# transitions. But as before, if a transition can't be found, we create a
# new nonterminal representing the new state, and add the given transition
# to the grammar.

class DFA(DFA):
    def build_pta(self, positive_examples):
        for example in positive_examples:
            # Trace or create path for this example
            cur_state = self.start_symbol
            for char in example:
                transition_rule = self.transition(cur_state,char)
                if transition_rule is None:
                    new_state = self.new_state()
                    self.add_transition(cur_state, char, new_state)
                    cur_state = new_state
                else:
                    cur_state = transition_rule[1]
            if [] not in self.grammar[cur_state]:
                self.grammar[cur_state].append([])
        return self

# Let us test it out!
if __name__ == '__main__':
    positive = ['abcdefgh']
    pta = DFA().build_pta(positive)
    for key in pta.grammar:
        print(key)
        for rule in pta.grammar[key]:
            print('',rule)
    positive = [ "b", "ab", "bb", "aab", "abb", "bab" ]
    pta = DFA().build_pta(positive)
    for key in pta.grammar:
        print(key)
        for rule in pta.grammar[key]:
            print('',rule)

# ### State Merging
# 
# Check if two states can be merged without accepting negative examples
# Two states are compatible if we can represent both state by a new common state
# The idea is to create a new DFA where first, we replace both states by a new
# state, which creates a regular grammar, then, convert it to a canonical
# regular grammar, then check if they are still rejecting
# negative samples.
# 
# First, we define a helper function

def unique_rules(rules):
    new_def = {}
    for r in rules:
        sr = str(r)
        if sr in new_def: continue
        new_def[sr] = r
    return [new_def[k] for k in new_def]

# to merge two states, we first create the name of the new state, which
# we name as `<or(state1,state2)>`. Then, we replace the nonterminals
# representing state1 and state2 in all rules with the nonterminal
# `<or(state1,state2)>`. Once we do this, the regular grammar we obtain
# is no longer a simple DFA, but an NFA, i.e., a
# Nondeterministic Finite Automaton. We will need to reduce this back to
# a DFA later.

class DFA(DFA):
    def merge_to_nfa(self, state1, state2):
        defs1, defs2 = self.grammar[state1], self.grammar[state2]
        new_state = '<or(%s,%s)>' % (state1[1:-1], state2[1:-1])
        # copy the grammar over. The defs are copied later
        new_grammar = {k:self.grammar[k] for k in self.grammar
                       if k not in [state1, state2]}
        new_grammar[new_state] = unique_rules(defs1+defs2)
        # replace usage of state1 or state2 with new_state
        for k in new_grammar:
            new_def = []
            for r in new_grammar[k]:
                if not(r):
                    new_def.append(r)
                    continue
                assert len(r) > 1
                if state1 == r[1]: new_def.append([r[0], new_state])
                elif state2 == r[1]: new_def.append([r[0], new_state])
                else: new_def.append([r[0], r[1]])
            new_grammar[k] = new_def
        return new_grammar, new_state

# Let us test it. We can make an NFA to a DFA by calling
# `canonical_regular_grammar()` from earlier posts. We need a DFA to
# parse the input using `dfa_parse`. So we do that.

if __name__ == '__main__':
    KEY_COUNTER = 0
    positive = [ "ab", "ac" ]
    negative = [ "", ]
    pta = DFA().build_pta(positive)
    for key in pta.grammar:
        print(key)
        for rule in pta.grammar[key]:
            print('',rule)
    merged_nfa, ns = pta.merge_to_nfa('<1>', '<2>')
    start_key = '<start>'
    merged, start_key = rxcanonical.canonical_regular_grammar(merged_nfa, start_key)
    for key in merged:
        print(key)
        for rule in merged[key]:
            print('',rule)
    print('All should be eaccepted')
    for example in positive:
        dfap = dfa_parse(merged)
        res = dfap.accept(start_key, example)
        print(res)

# When merging two states, we also need to verify that the end result is
# consistent with the negative examples. So, we define this function.

class DFA(DFA):
    def is_consistent(self, negative_examples, positive_examples):
        for neg_example in negative_examples:
            if self.accepts(neg_example): return False

        for pos_example in positive_examples:
            assert self.accepts(pos_example)
        return True

# Let us test it.
if __name__ == '__main__':
    KEY_COUNTER = 0
    positive = [
            "ab",
            "ac"
            ]
    negative = [
        "",
    ]
    pta = DFA().build_pta(positive)
    start_key = '<start>'
    merged_nfa, ns = pta.merge_to_nfa('<1>', '<2>')
    merged_g, start_key = rxcanonical.canonical_regular_grammar(merged_nfa, start_key)
    merged_dfa = DFA(start_symbol = start_key)
    merged_dfa.grammar = merged_g
    res = merged_dfa.is_consistent(negative, positive)
    print(res)
    KEY_COUNTER = 0
    positive = [ "abd", "acd" ]
    negative = [ "ad" ]
    pta = DFA().build_pta(positive)
    for key in pta.grammar:
        print(key)
        for rule in pta.grammar[key]:
            print('',rule)
    print()
    merged_nfa, ns = pta.merge_to_nfa('<1>', '<3>')
    merged_g, start_symbol = rxcanonical.canonical_regular_grammar(merged_nfa, start_key)
    for key in merged_g:
        print(key)
        for rule in merged_g[key]:
            print('',rule)

# ### RPNI algorithm implementation

def rpni(positive_examples, negative_examples):
    # Step 1: Build PTA
    dfa = DFA().build_pta(positive)
    start = dfa.start_symbol
    
    # Step 2: Try to merge states
    # In the canonical order: try to merge each state with earlier states
    changed = True
    while changed:
        changed = False
        keys = list(dfa.grammar.keys())
        for i in range(1, len(keys)):
            for j in range(i):
                state_i, state_j = keys[i], keys[j]
                
                # Check if merge is compatible
                merged_nfa, new_state = dfa.merge_to_nfa(state_i, state_j)
                if state_i == start or state_j == start: new_start = new_state
                else: new_start = start
                merged, new_start = rxcanonical.canonical_regular_grammar(
                        merged_nfa, new_start)

                merged_dfa = DFA(start_symbol = new_start)
                merged_dfa.grammar = merged
                res = merged_dfa.is_consistent(negative_examples, positive_examples)
                if res:
                    dfa = merged_dfa
                    start = new_start
                    changed = True
                    break
            if changed: break
    return dfa

# ## A Simple Example
# 
# Let us use RPNI to learn a simple pattern: strings over {a, b} that end with 'b'.

if __name__ == '__main__':
    positive = [
        "b",
        "ab",
        "bb",
        "aab",
        "abb",
        "bab"
    ]
    negative = [
        "",
        "a",
        "aa",
        "ba",
        "aba",
        "bba"
    ]

    learned_dfa = rpni(positive, negative)
    print('should all be accepted', "Y" )
    for s in positive:
        result = "Y" if learned_dfa.accepts(s) else "X"
        print(f"{result} '{s}'")
    print()
    print('should all be rejected', "X")
    for s in negative:
        result = "Y" if learned_dfa.accepts(s) else "X"
        print(f"{result} '{s}'")

    print()
    print('others')

    test_strings = ["aab", "aba", "bbb", "aa"]
    for s in test_strings:
        result = "Y" if learned_dfa.accepts(s) else "X"
        print(f"{result} '{s}'")

# ## Complexity and Limitations
# 
# Time Complexity: The RPNI algorithm is $ O(p^3 n) $ where p is the size (sum
# of the lengths of all strings) of positive data, and n is the size of negative
# data.
# 
# ## Extensions and Improvements
# 
# Some of the important extensions to RPNI include EDSM and RPNI2. 
# 
# ---
# [^oncia1992]: J Oncia and P Garcia, Inferring regular languages in polynomial update time, 1992
