# ---
# published: true
# title: Converting a Regular Grammar to a Regular Expression
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---

# This post shows you how to convert a regular grammar to a regular expression
# using the state elimination algorithm. The intuition in this algorithm is to
# note that every nonterminal is just a way point between two sets of states
# A and B. So, Eliminating one nonterminal can be achieved by linking all pairs
# between A and B with the equivalent regular expression transmissions.
#
# We start with importing the prerequisites

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxcanonical

# Let us define a grammar that we want to extract the regular expression for.

G_1 = {"<S>": [["a", "<A>"]],
    "<A>" : [
        [rxcanonical.NT_EMPTY],
        ["b","<S>"],
        ["b","<A>"],
        ["a","<B>"],
    ],
    "<B>" : [
        ["b",rxcanonical.NT_EMPTY],
        ["a","<S>"]
    ],
    rxcanonical.NT_EMPTY : [[]]}
S_1 = '<S>'

# Let us first define a few helpr functions for regular expression conversion.
# we represent individual regular expressions by lists. So, concatenation is
# just list addition. An empty list represents epsilon. We justneed to take
# care of two meta symbols, kleene star and alternative, which is represented
# as below.


def star(r):
    if not r: return []
    return [('star', r)]

def union(r1, r2):
    if not r1: return r2
    if not r2: return r1
    return [('or', r1, r2)]

# We also define how to convert a regular expression to its string form.

def convert_rex(rex):
    if rex[0] == 'or':
        return '(%s|%s)' % (convert_rexs(rex[1]), convert_rexs(rex[2]))
    elif rex[0] == 'star':
        v = convert_rexs(rex[1])
        if len(v) > 1: # | or concat
            return "(%s)*" % v
        else:
            return "%s*" % v
    else:
        return rex

def convert_rexs(rexs):
    r = ''
    for rex in rexs:
        r += convert_rex(rex)
    return r

# We require grammars in a particular format. In particular,
# we reqire that we have only one nonterminal symbol `<_>: []`
# as the accept state. If the grammar doesn't conform, we can
# make it conform with `fix_grammar()` which adds the necessary
# definitions. Essentially,
# if the grammar already contains `<_>`, then it is kept, else
# a new defintion `<_>: []` is created. For any rule that contains
# a single terminal, we add `<_>` as the ending nonterminal symbol.
# if it is a single nonterminal, we assert that it is <_> which
# is one epsilon transition away from `k`.
def add_single_accept_state(g, accept=rxcanonical.NT_EMPTY):
    new_g = {}
    new_g[empty_nt] = [[]]
    for k in g:
        new_rules = []
        for rule in g[k]:
            if len(rule) == 0:
                if k == empty_nt:
                    new_rules.append([])
                else:
                    new_rules.append([empty_nt])
            elif len(rule) == 1:
                if fuzzer.is_nonterminal(rule[0]):
                    assert rule[0] == empty_nt
                    new_rules.append(rule)
                else:
                    new_rules.append([rule[0], empty_nt])
            else:
                new_rules.append(rule)
        new_g[k] = new_rules
    return new_g

# ## Adjuscency Matrix
# 
# Using the regular grammar directly is too unwieldy.
# Let us first extract the states, and transitions to build an adjuscency
# matrix. We do not want any incoming transitions to the start state, and we do
# not want any outgoing transitions from the accept. So, let us also define
# two phony states for these.

def adjuscency_matrix(grammar, start, stop):
    my_states = {k:i for i,k in enumerate(sorted(grammar.keys()))}
    new_start, new_stop = len(my_states) + 1, len(my_states) + 2
    states = set(my_states.values()) | {new_start, new_stop}
    regex = {(i, j): None for i in states for j in states}

    for k in grammar:
        for r in grammar[k]:
            if not r:
                assert k == rxcanonical.NT_EMPTY
            elif len(r) == 1:
                assert r[0] == rxcanonical.NT_EMPTY
                src, dst, trans  = my_states[k], my_states[r[0]], []
                regex[(src, dst)] = union(regex[(src, dst)], [])
            else:
                src, dst, trans  = my_states[k], my_states[r[1]], r[0]
                regex[(src, dst)] = union(regex[(src, dst)], [trans])
    regex[(new_start, my_states[start])] = [] # empty transition
    regex[(my_states[stop], new_stop)] = [] # empty transition
    return regex, states, new_start, new_stop

# Using it.
if __name__ == '__main__':
    regex,states, start, stop = adjuscency_matrix(G_1, S_1, rxcanonical.NT_EMPTY)
    for i in states:
        print(' '.join(['%s,%s: %s' % (i, j, regex[(i,j)]) for j in states]))

# We can now define our conversion routine. The idea is very simple,
# remove one state at a time. For any pair of states such that
# `<src> -> (a) -> <q> -> (b) -> <dst>`, replace it with 
# `<src> -> (ab) -> <dst>

def rg_to_regex(grammar, start, stop=rxcanonical.NT_EMPTY):
    regex, states, new_start, new_stop = adjuscency_matrix(grammar, start, stop)

    for q in sorted(states - {new_start, new_stop}):
        for i in states - {q}:
            for j in states - {q}:
                r_iq, r_qq, r_qj, r_ij = regex[(i, q)], regex[(q, q)], \
                        regex[(q, j)], regex[(i, j)]
                if r_iq is None or r_qj is None: continue
                new_part = r_iq + star(r_qq) + r_qj
                regex[(i, j)] = union(r_ij, new_part)

    return regex[(new_start, new_stop)]

# Using it.

if __name__ == '__main__':
    rxg = rg_to_regex(G_1, S_1)
    print(rxg)
    rx = convert_rexs(rxg)
    print(rx)
    import re
    rf = fuzzer.LimitFuzzer(G_1)
    for i in range(100):
        v = rf.fuzz(S_1)
        print(v)
        assert re.match(rx, v)


# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-11-13-regular-grammar-to-regular-expression.py).
