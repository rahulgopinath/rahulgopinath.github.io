# ---
# published: true
# title: Converting a Regular Expression to DFA using Regular Grammar
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---
#
# A regular grammar can in theory have rules with any of the following forms
# 
# * $$ A \rightarrow a $$
# * $$ A \rightarrow a B $$
# * $$ A \rightarrow a b c B $$
# * $$ A \rightarrow B $$
# * $$ A \rightarrow \epsilon $$
# 
# with no further restrictions. This is the direct equivalent grammar for
# a nondeterministic finite state automaton (**NFA**).
# However, for working with regular grammars,
# such freedom can be unwieldy. Hence, without loss of generality, we define
# a canonical format for regular grammars, to which any regular grammar can
# be converted to.
#
# * $$ A \rightarrow a B $$
# * $$ S \rightarrow E $$
# * $$ E \rightarrow \epsilon $$
# 
# where given a nonterminal $$A$$ and a terminal symbol $$ a $$ at most one of
# its rules will start with a terminal symbol $$ a $$. That is, if the original
# grammar had multiple rules that started with $$ a $$, they will be collected
# into a new nonterminal symbol. Further, there will be at most one terminal
# symbol in a rule. That is, if there are more terminal symbols, then we bundle
# that to a new nonterminal symbol.
# Finally, the $$ \epsilon $$ is attached to the $$ E $$ symbol, which is the
# only termination point. If the language contains $$ \epsilon $$, then the
# single degenerate rule, $$ S \rightarrow E $$ is added to the rules.
# As you can see, each node has at most one
# transition for a given terminal symbol. Hence, this canonical form is
# equivalent to a deterministic finite state automation (**DFA**).
# 
# What is the use of such a DFA compared to NFA? the great thing about a DFA is
# that there is exactly one state to which a DFA can transition to
# for any given alphabet from any given state. This means that when parsing
# with a regular grammar that directly represents a DFA, there is never a
# reason to backtrack! This means that when we parse with the grammar from such
# a DFA using an LL(1) parser, we are guaranteed $$ O(n) $$ matching time.
#  
# We start with importing the prerequisites

#^
# sympy

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import earleyparser
import rxfuzzer
import rxregular
import sympy
import itertools as I

# We start with a few common rules.
# First, we define the empty rule.
#  
# ```
# <_>  := 
# ```

NT_EMPTY = '<_>'

G_EMPTY = {NT_EMPTY: [[]]}
# 
# We also define our `TERMINAL_SYMBOLS`

TERMINAL_SYMBOLS = rxfuzzer.TERMINAL_SYMBOLS

# Then, use it to define `NT_ANY_STAR`
#  
# ```
# <.*>  := . <.*>
#        | <NT_EMPTY>
# ```
NT_ANY_STAR = '<.*>'

G_ANY_STAR = {
    NT_ANY_STAR: [[c, NT_ANY_STAR] for c in TERMINAL_SYMBOLS] + [[NT_EMPTY]]
}


# Use it to also define `NT_ANY_PLUS`
#  
# ```
# <.+>  := . <.+>
#        | . <NT_EMPTY>
# ```
# 
# use any_plus where possible.

NT_ANY_PLUS = '<.+>'

G_ANY_PLUS = {
    NT_ANY_PLUS: [
        [c, NT_ANY_PLUS] for c in TERMINAL_SYMBOLS] + [
        [c, NT_EMPTY] for c in TERMINAL_SYMBOLS]
}

# ## Removing terminal sequences
# 
# A terminal sequence is a sequence of terminal symbols in a rule. For example,
# in the rule
# ```
# <A> ::= a b c <B>
# ```
# `a b c` is a terminal sequence.
# We want to replace such sequences by a new nonterminal. For example,
# ```
# <A> ::= a <Aa>
# <Aa> ::= b <Aab>
# <Aab> ::= c <B>
# ```

from collections import defaultdict

def remove_duplicate_rules(g):
    new_g = {}
    for k in g:
        my_rules = {str(r):r for r in g[k]}
        new_g[k] = [my_rules[k] for k in my_rules]
    return new_g


def get_split_key(k, terminal):
    return '<%s_%s>' % (k[1:-1], terminal)

def split_multi_terminal_rule(rule, k):
    if len(rule) == 0:
        return k, [(k, [rule])]
    elif len(rule) == 1:
        assert not fuzzer.is_nonterminal(rule[0])
        return k, [(k, [rule])]
    elif len(rule) > 1:
        terminal = rule[0]
        tok = rule[1]
        if fuzzer.is_nonterminal(tok):
            assert len(rule) == 2
            return k, [(k, [rule])]
        else:
            kn, ngl = split_multi_terminal_rule(rule[1:], get_split_key(k, terminal))
            new_rule = [terminal, kn]
            return k, ([(k, [new_rule])] + ngl)
    else:
        assert False

def remove_multi_terminals(g, s):
    new_g = defaultdict(list)
    for key in g:
        for r in g[key]:
            nk, lst = split_multi_terminal_rule(r, key)
            for k, rules in lst:
                new_g[k].extend(rules)
            assert nk in new_g
    return remove_duplicate_rules(new_g), s

# Using it

if __name__ == '__main__':
   g2 = {
        '<start1>' : [['a1', 'a2', 'a3', '<A1>']],
        '<A1>' : [['a1', '<B1>'],
                  ['b1', 'b2']],
        '<B1>' : [['b1', 'c1', '<C1>'],
                  ['b1', 'c1', '<D1>']],
        '<C1>' : [['c1'], []],
        '<D1>' : [['d1'], []]
   }
   s2 = '<start1>'
   g, s = remove_multi_terminals(g2, s2)
   gatleast.display_grammar(g, s)

# ## Fix empty rules
# 
# If there are any rules of the form $$ A \rightarrow b $$, we replace it by
# $$ A \rightarrow b E $$, $$ E \rightarrow \epsilon $$.
# Next, if we have rules of the form $$ A \rightarrow \epsilon $$,
# and $$ B \rightarrow a A $$ then, we remove the $$ A \rightarrow \epsilon $$
# and add a new rule $$ B \rightarrow a E $$
#
# The reason for doing
# this is to make sure that we have a single termination point. If you are using
# NT_ANY_STAR, then make sure you run this after (or use NT_ANY_PLUS instead).

def fix_empty_rules(g, s):
    new_g = defaultdict(list)
    empty_keys = []
    for k in g:
        if k == NT_EMPTY: continue
        for r in g[k]:
            if len(r) == 0:
                empty_keys.append(k)
                continue
            elif len(r) == 1:
                tok = r[0]
                assert fuzzer.is_terminal(tok)
                new_g[k].append([tok, NT_EMPTY])
            else:
                new_g[k].append(r)

    new_g1 = defaultdict(list)
    for k in new_g:
        for r in new_g[k]:
            assert len(r) == 2 or k == s
            if r[1] in empty_keys:
                new_g1[k].append(r)
                new_g1[k].append([r[0], NT_EMPTY])
            else:
                new_g1[k].append(r)

    # special case.
    if s in empty_keys:
        new_g1[s].append([NT_EMPTY])

    return {**new_g1, **G_EMPTY}, s

# ## Collapse similar starting rules
# 
# Here, the idea is to join any set of rules of the form
# $$ A \rightarrow b B $$, $$ A \rightarrow b C $$ to $$ A \rightarrow b \,or(B,C) $$.
# We use the powerset construction from Automata theory for accomplishing this.
# 
# First, we define the epsilon closure. Epsilon closure of a nonterminal is any
# nonterminal that is reachable from a given nonterminal symbol without
# consuming any input.

def find_epsilon_closure(g, ekey):
    keys = [ekey]
    result = {ekey: None}
    while keys:
        key, *keys = keys
        for r in g[key]:
            if not r: continue
            k = r[0]
            if not fuzzer.is_nonterminal(k): continue
            assert k != '' # invalid key
            # we assume that this is a regular grammar. So, we can
            # be sure that only one nonterminal in the rule
            if k not in result:
                result[k] = None
                keys.append(k)

    return result

# Using it

if __name__ == '__main__':
   g1 = {
        '<start1>' : [['<A1>']],
        '<A1>' : [['a', '<B1>']],
        '<B1>' : [['b','<C1>'], ['<C1>']],
        '<C1>' : [['c'], ['<C1>'], ['<D1>']],
        '<D1>': [[]]
   }
   s1 = '<start1>'
   ks = find_epsilon_closure(g1, s1)
   print(ks)
   ks = find_epsilon_closure(g1, '<B1>')
   print(ks)

# We can also provide a name for such closures.

def closure_name(eclosure):
    rs = [s[1:-1] for s in sorted(eclosure.keys())]
    if len(rs) == 1:
        return '<%s>' % ','.join(rs)
    else:
        return '<or(%s)>' % ','.join(rs)

# Using it

if __name__ == '__main__':
   n = closure_name(ks)
   print(n)

# Next, we identify the acceptance states.

def get_first_accepts(grammar):
    accepts = {}
    for key in grammar:
        for rule in grammar[key]:
            if not rule:
                accepts[key] = None
    return accepts

def get_accepts(grammar):
    accepts = get_first_accepts(grammar) # typically <_>
    results = dict(accepts)

    for k in grammar:
        if k in results: continue
        ec = find_epsilon_closure(grammar, k)
        for k in ec:
            if k in accepts: # if k == <_>
                results[k] = None
    # any key that contains <_> in the epsilon closure
    return results

# Using it

if __name__ == '__main__':
   acc = get_accepts(g1)
   print(acc)

# ## Construct the canonical regular grammar (DFA)
#  
# The procedure is as follows:
# Start with the start symbol. While there are unprocessed nonterminals,
# remove one unprocessed nonterminal, then for each terminal symbol that
# starts its rules,

def reachable_with_sym(g, closure, tsym):
    result = {}
    states = {rule[1]:None for k in closure for rule in g[k]
              if len(rule) == 2 and rule[0] == tsym}
    result.update(states)
    for s in states:
        estates = find_epsilon_closure(g, s)
        result.update(estates)
    return result


def get_alphabets(grammar, estates):
    return {rule[0]:None for key in estates for rule in grammar[key]
                       if rule and not fuzzer.is_nonterminal(rule[0])}

def canonical_regular_grammar(grammar, start):
    eclosure = find_epsilon_closure(grammar, start)
    start_name =  closure_name(eclosure)
    accepts = get_accepts(grammar)

    new_grammar = {}
    my_closures = {start_name: eclosure}
    keys_to_process = [start_name]

    while keys_to_process:
        key, *keys_to_process = keys_to_process
        eclosure = my_closures[key]
        if key in new_grammar: continue
        new_grammar[key] = []
        # is any of the nonterminals an accept state?
        for k in eclosure:
            if k in accepts:
                new_grammar[key].append([])

        transitions = get_alphabets(grammar, eclosure)
        # check if eclosure has an end state.

        for t in transitions:
            reachable_nonterminals = reachable_with_sym(grammar, eclosure, t)
            if not reachable_nonterminals: continue
            dfa_key = closure_name(reachable_nonterminals)

            new_grammar[key].append([t, dfa_key])
            my_closures[dfa_key] = reachable_nonterminals
            keys_to_process.append(dfa_key)

    # mark accept states.
    return new_grammar, start_name

# Using it

if __name__ == '__main__':
   g1 = {
        '<start1>' : [['<A1>']],
        '<A1>' : [['a', '<A1>'], []],
   }
   s1 = '<start1>'
   g, s = canonical_regular_grammar(g1, s1)
   gatleast.display_grammar(g, s)


# Another example

if __name__ == '__main__':
   g3 = {
        '<start1>' : [
            ['a1', '<A1>'],
            ['a1', '<A2>'],
            ['a1', '<A3>']
            ],
        '<A1>' : [['b1', '<B1>']],
        '<A2>' : [['b2', '<B1>']],
        '<A3>' : [['b3', '<B1>']],
        '<B1>' : [['b1','<C1>'],
                  ['b2', '<C1>']],
        '<C1>' : [['c1'], []]
   }
   s3 = '<start1>'
   g, s = canonical_regular_grammar(g3, s2)
   gatleast.display_grammar(g, s)

# ## Display canonical grammar
#
# We also need the ability to compactly display a canonical regular grammar
# and we define it as below.


from collections import defaultdict

class DisplayGrammar(gatleast.DisplayGrammar):

    def definition_rev_split_to_rulesets(self, d1):
        rule_sets = defaultdict(list)
        for r in d1:
            if len(r) > 0:
                if self.is_nonterminal(r[0]):
                    if r[0] != '<_>':
                        assert False # no degenerate rules
                    else:
                        rule_sets['<_>'].append(r)
                else:
                    assert self.is_nonterminal(r[1]) # no degenerate rules
                    rule_sets[r[1]].append(r)
            else:
                rule_sets[''].append(r)
        return rule_sets

    def display_ruleset(self, nonterminal, ruleset, pre,
                        all_terminal_symbols=TERMINAL_SYMBOLS):
        if ruleset == [[]]:
            print('| {EMPTY}')
            return
        terminals = [t[0] for t in ruleset]
        rem_terminals = [t for t in all_terminal_symbols if t not in terminals]
        if len(terminals) <= len(rem_terminals):
            v = '%s %s' % (self.display_terminals(terminals), nonterminal)
            s = '%s|   %s' % (pre, v)
            print(s)
        else:
            if rem_terminals == []:
                v = '. %s' % nonterminal
            else:
                v = '%s %s' % (self.display_terminals(rem_terminals, negate=True),
                               nonterminal)
            s = '%s|   %s' % (pre, v)
            print(s)

    def display_terminals(sefl, terminals, negate=False):
        if negate: return '[^%s]' % (''.join(terminals))
        else:
            if len(terminals) == 1:
                return terminals[0]
            return '[%s]' % (''.join(terminals))

    def display_definition(self, key, r):
        if self.verbose > -1: print(key,'::=')
        rulesets = self.definition_rev_split_to_rulesets(self.grammar[key])
        for nonterminal in rulesets:
            pre = ''
            self.display_ruleset(nonterminal,
                                 rulesets[nonterminal],
                                 pre,
                                 all_terminal_symbols=TERMINAL_SYMBOLS)
        return r

    def display_unused(self, unused, verbose):
        pass

def display_canonical_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)

# Make sure it works

if __name__ == '__main__':
    g0, s0 = {
         '<start0>' : [['a', '<A0>']],
         '<A0>' : [['b', '<B0>'], ['c', '<C0>']],
         '<B0>' : [['c', NT_ANY_STAR]],
         '<C0>' : [['d', NT_EMPTY]]
    }, '<start0>'
    display_canonical_grammar(g0, s0)

# ## A canonical regular grammar from a regular expression.
#  This function extracts the DFA equivalent grammar for the regular
# expression given.

def regexp_to_regular_grammar(regexp):
    g1, s1 = rxregular.RegexToRGrammar().to_grammar(regexp)

    g2, s2 = remove_multi_terminals(g1, s1)
    g3, s3 = fix_empty_rules(g2, s2)
    g4, s4 = canonical_regular_grammar(g3, s3)
    return g3, s3

# Using it.

if __name__ == '__main__':
    my_re = '(a|b|c).(de|f)'
    print(my_re)
    g, s = regexp_to_regular_grammar(my_re)
    display_canonical_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        print(repr(v))
        assert re.match(my_re, v), v

#  
# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-24-canonical-regular-grammar.py).
