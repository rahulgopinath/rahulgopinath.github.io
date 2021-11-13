# ---
# published: true
# title: Converting a Regular Grammar to a Regular Expression
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---

# For this post, we assume that we are working with the canonical regular
# grammar we defined [previously](/post/2021/10/24/canonical-regular-grammar/).
#
# * $$ A \rightarrow a B $$
# * $$ S \rightarrow E $$
# * $$ E \rightarrow \epsilon $$
# 
# Actually, the only restrictions we have are that (1) we have a single
# nonterminal that corresponds to the empty symbol, and (2) all rules
# except the empty symbol rule have exactly one nonterminal symbol in them.
# If your grammar is not already in this format, use that post to convert.
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
#import earleyparser
#import rxfuzzer
#import rxregular
import itertools as I

# Converting a regular gramamr to a regular expression is fairly simple. You
# start at the start symbol and start flattening.

EMPTY_KEY = "<_>"

def is_nonterminal(item):
    if not isinstance(item, str): return False
    return fuzzer.is_nonterminal(item)

def split_regex_prefix(rule):
    prefix = 0
    for token in rule:
        if is_nonterminal(token): break
        else: prefix += 1
    return rule[:prefix], rule[prefix:]

def refine(rule):
    prefix, nts = split_regex_prefix(rule)
    if len(nts) == 1:
        return [("concat", *prefix), nts[0]]
    elif len(nts) == 0:
        return prefix
    else:
        assert False


def flatten_rule(rule, grammar, nt):
    # find the prefix without nonterminal
    prefix, nts = split_regex_prefix(rule)
    assert len(nts) <= 1
    if not nts: return [prefix]
    if nts[0] == nt: # recursion
        return [rule]
    if nts[0] == EMPTY_KEY: # dont expand empty key
        return [rule]
    new_suffixes = grammar[nts[0]]
    return [refine(prefix+r) for r in new_suffixes]

# Using it.
MY_RGRAMMAR = {"<S>": [["a", "<A>"]],
    "<A>" : [
        ["<_>"],
        ["b","<S>"],
        ["b","<A>"],
        ["a","<B>"],
    ],
    "<B>" : [
        ["b","<_>"],
        ["a","<S>"]
    ],
    "<_>" : [[]]}

if __name__ == '__main__':
    gatleast.display_grammar(MY_RGRAMMAR, "<S>")
    print("<B>", "::", MY_RGRAMMAR['<B>'][1])
    rules = flatten_rule(MY_RGRAMMAR['<B>'][1], MY_RGRAMMAR, "<B>")
    print("Expanded to:")
    for r in rules:
        print(r)

# 
def flatten_definition(nt, grammar):
    rules = grammar[nt]
    new_rules = []
    for rule in rules:
        new_rule_set = flatten_rule(rule, grammar, nt)
        new_rules.extend(new_rule_set)
    return new_rules

# 
if __name__ == '__main__':
    print("Definition")
    gatleast.display_grammar(MY_RGRAMMAR, "<S>")
    print("<B>")
    rules = flatten_definition('<B>', MY_RGRAMMAR)
    print("Expanded to:")
    for r in rules:
        print(r)

# 

def produce_prefix_regex(rules, grammar):
    # convert a <B> | b <B> to (a|b) <B>
    lnt_hash = {}
    has_epsilon = False
    has_emptykey = False
    for rule in rules:
        if rule == []:
            has_epsilon = True
            continue
        if rule == [EMPTY_KEY]:
            has_emptykey = True
            continue
        prefix, lnt = split_regex_prefix(rule)
        assert len(prefix) == 1
        knt = lnt[0]
        if knt not in lnt_hash: lnt_hash[knt] = []
        lnt_hash[knt].append(prefix[0])

    new_rules = []
    if has_epsilon:
        new_rules.append([])
    if has_emptykey:
        new_rules.append([EMPTY_KEY])
    for lnt in lnt_hash:
        if len(lnt_hash[lnt]) > 1:
            rex = ("or", lnt_hash[lnt])
            new_rules.append([rex, lnt])
        else:
            rex = lnt_hash[lnt][0]
            new_rules.append([rex, lnt])
    return new_rules
# 
if __name__ == '__main__':
    print()
    print("Definition")
    gatleast.display_grammar(MY_RGRAMMAR, "<S>")
    print("<B>")
    rules = flatten_definition('<B>', MY_RGRAMMAR)
    print("Expanded to:")
    for r in rules:
        print(r)
    print()
    new_rules = produce_prefix_regex(rules, MY_RGRAMMAR)
    print("New Rules:")
    for r in new_rules:
        print(r)
    print()

# dealing with recursion
# A -> a B | b C | a A
# becomes A -> a* a B | a* b C

def handle_recursion(rules_, nt):
    rules = [r for r in rules_ if len(r) > 1]
    recursive_rules = [r for r in rules if r[-1] == nt]
    if not recursive_rules: return rules_
    assert len(recursive_rules) == 1
    r_rule = recursive_rules[0]
    assert r_rule[1] == nt
    new_rules = []
    for r in rules_:
        if r == r_rule: continue
        nr = refine([("star", r_rule[0]), *r])
        new_rules.append(nr)
    return new_rules
    

def convert_definition_to_regex_prefix(nt, grammar):
    rules = grammar[nt]
    my_rules = produce_prefix_regex(rules, grammar)
    my_rules_ = handle_recursion(my_rules, nt)
    return my_rules_
# 
if __name__ == '__main__':
    print()
    print("Definition")
    gatleast.display_grammar(MY_RGRAMMAR, "<S>")
    print("<A>")
    new_rules = convert_definition_to_regex_prefix("<A>", MY_RGRAMMAR)
    print("Rules:")
    for r in new_rules:
        print(r)
    print()


# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-24-canonical-regular-grammar.py).
