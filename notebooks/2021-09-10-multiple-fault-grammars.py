# ---
# published: true
# title: Specializing Context-Free Grammars for Inducing Multiple Faults
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# 
# This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)
# 
# In my previous post on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
# I explained the deficiency of abstract failure inducing inputs mined using
# DDSet, and showed how to overcome that by inserting that abstract (evocative)
# pattern into a grammar, producing evocative grammars that guarantee that the
# evocative fragment is present in any input generated.
#
# However, what if one wants to produce inputs that contain two evocative
# fragments? or wants to produce inputs that are guaranteed to contain at least
# one of them? This is what we will discuss in this post.
# 
# As before, let us start with importing our required modules.

#@
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import itertools as I

# # Producing inputs with two fault inducing fragments guaranteed to be present.
#
# From the previous post [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
# we extracted two evocative subtrees

if __name__ == '__main__':
    import ddset
    import hdd
    print(ddset.abstract_tree_to_str(gatleast.ETREE_DPAREN))
    ddset.display_abstract_tree(gatleast.ETREE_DPAREN)
    print()
    print(ddset.abstract_tree_to_str(gatleast.ETREE_DZERO))
    ddset.display_abstract_tree(gatleast.ETREE_DZERO)

# We now want to produce a grammar such that any input produced from that
# grammar is guaranteed to contain both evocative subtrees. First, let us
# extract the corresponding grammars. Here is the first one

if __name__ == '__main__':
    g1, s1 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, 'D1'))
    gatleast.display_grammar(g1, s1)

# We save this for later

EXPR_DPAREN_S = '<start D1>'
EXPR_DPAREN_G = {
        '<start>': [['<expr>']],
        '<expr>': [['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
        '<term>': [['<factor>', '*', '<term>'], ['<factor>', '/', '<term>'], ['<factor>']],
        '<factor>': [['+', '<factor>'], ['-', '<factor>'], ['(', '<expr>', ')'], ['<integer>', '.', '<integer>'], ['<integer>']],
        '<integer>': [['<digit>', '<integer>'], ['<digit>']],
        '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<factor D1_0>': [['(', '<expr D1_1>', ')']],
        '<expr D1_1>': [['<term D1_2>']],
        '<term D1_2>': [['<factor D1_3>']],
        '<factor D1_3>': [['(', '<expr>', ')']],
        '<start D1>': [['<expr D1>']],
        '<expr D1>': [['<term D1>', '+', '<expr>'], ['<term>', '+', '<expr D1>'], ['<term D1>', '-', '<expr>'], ['<term>', '-', '<expr D1>'], ['<term D1>']],
        '<term D1>': [['<factor D1>', '*', '<term>'], ['<factor>', '*', '<term D1>'], ['<factor D1>', '/', '<term>'], ['<factor>', '/', '<term D1>'], ['<factor D1>']],
        '<factor D1>': [['+', '<factor D1>'], ['-', '<factor D1>'], ['(', '<expr D1>', ')'], ['(', '<expr D1_1>', ')']]
} 


# Here is the second grammar.

if __name__ == '__main__':
    g2, s2 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, 'Z1'))
    gatleast.display_grammar(g2, s2)

# We save this for later

EXPR_DZERO_S = '<start Z1>'
EXPR_DZERO_G = {
        '<start>': [['<expr>']],
        '<expr>': [['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
        '<term>': [['<factor>', '*', '<term>'], ['<factor>', '/', '<term>'], ['<factor>']],
        '<factor>': [['+', '<factor>'], ['-', '<factor>'], ['(', '<expr>', ')'], ['<integer>', '.', '<integer>'], ['<integer>']],
        '<integer>': [['<digit>', '<integer>'], ['<digit>']],
        '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<term Z1_0>': [['<factor>', '/', '<term Z1_1>']],
        '<term Z1_1>': [['<factor Z1_2>']],
        '<factor Z1_2>': [['<integer Z1_3>']],
        '<integer Z1_3>': [['<digit Z1_4>']],
        '<digit Z1_4>': [['0']],
        '<start Z1>': [['<expr Z1>']],
        '<expr Z1>': [['<term Z1>', '+', '<expr>'], ['<term>', '+', '<expr Z1>'], ['<term Z1>', '-', '<expr>'], ['<term>', '-', '<expr Z1>'], ['<term Z1>']],
        '<term Z1>': [['<factor Z1>', '*', '<term>'], ['<factor>', '*', '<term Z1>'], ['<factor Z1>', '/', '<term>'], ['<factor>', '/', '<term Z1>'], ['<factor Z1>'], ['<factor>', '/', '<term Z1_1>']],
        '<factor Z1>': [['+', '<factor Z1>'], ['-', '<factor Z1>'], ['(', '<expr Z1>', ')']]
}

# ## And Grammars
# Now, we want to combine these grammars. Remember that a gramamr has a set of
# definitions that correspond to nonterminals, and each definition has a set of
# rules. We start from the rules. If we want to combine two grammars, we need
# to make sure that any input produced from the combined grammar is also parsed
# by the original grammars. That is, any rule from the combined grammar should
# have a corresponding rule in the original grammars. This gives us the
# algorithm for combining two rules. First, we can only combine rules that have
# similar base representation. That is, if ruleA is `[<A f1>, <B f2>, 'T']` 
# where `<A>` and `<B>` are nonterminals and `T` is a terminal
# and ruleB is `[<A f1>, <C f3>]`, these can't have a combination in the
# combined grammar. On the other hand, if ruleB is `[<A f3>, <B f4> 'T']`
# then, a combined rule of `[<A f1 & f3>, <B f2 & f4>, 'T']` can infact
# represent both parent rules. That is, when combining two rules from different,
# grammars, their combination is empty if they have different base
# representation.
# 
# The idea for combining two definitions of nonterminals is simply using the
# distributive law. A definition is simply # `A1 or B1 or C1` where `A1` etc are
# rules. Now, when you want to and two defintions, you have
# `and(A1 or B1 or C1, A2 or B2 or C2)` , and you want the `or` out again.
# So, this becomes
#
# ```
# (A1 AND A2) OR (A1 AND B2) OR (A1 AND C2) OR
# (A2 AND B1) OR (A2 AND C1) OR
# (B1 AND B2) OR (B1 AND C2) OR
# (B2 AND C1) OR (C1 AND C2)
# ```
# 
# which is essentially that many rules.

# ### Combining tokens
# If they have the same base representation, then we only have to deal with how
# to combine the nonterminal symbols. The terminal symbols are exactly the same
# in parent rules as well as combined rule. So, given two tokens, we can
# combine them as follows. The `and` of a refined nonterminal and a base
# nonterminal is always the refined nonterminal. Otherwise, it is simply an
# `and()` specialization of both refinements.

def and_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k2
    if not s2: return k1
    if s1 == s2: return k1
    return '<%s and(%s,%s)>' % (b1, s1, s2)

def and_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return and_nonterminals(t1, t2)

# Using it.

if __name__ == '__main__':
    print(and_tokens('C', 'C'))
    print(and_tokens('<A>', '<A f1>'))
    print(and_tokens('<A f2>', '<A f1>'))

# ## Combining rules
# Next, we define combination for rules

def and_rules(ruleA, ruleB):
    AandB_rule = []
    for t1,t2 in zip(ruleA, ruleB):
        AandB_rule.append(and_tokens(t1, t2))
    return AandB_rule

# Using it.
if __name__ == '__main__':
    print(and_rules(['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']))
    print(and_rules(['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))
    print(and_rules(['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))

# ### Combining rulesets
# 
# Next, our grammars may contain multiple rules that represent the same base
# rule. All the rules that represent the same base rule is called a ruleset.
# combining two rulesets is done by producing a new ruleset that contains all
# possible pairs of rules from the parent ruleset.
# 

def and_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = and_rules(ruleA, ruleB)
        rules.append(AandB_rule)
    return rules

# Using it.
if __name__ == '__main__':
    A = [['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']]
    B = [['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
    C = [['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
    for k in and_ruleset(A, B): print(k)
    print()
    for k in and_ruleset(A, C): print(k)
    print()
    for k in and_ruleset(B, C): print(k)
    print()

# Next, we define a few helper functions that collects all rulesets

def normalize(key):
    if gatleast.is_base_key(key): return key
    return '<%s>' % gatleast.stem(key)

def normalize_grammar(g):
    return {normalize(k):list({tuple([normalize(t) if fuzzer.is_nonterminal(t) else t for t in r]) for r in g[k]}) for k in g}

def rule_to_normalized_rule(rule):
    return [normalize(t) if fuzzer.is_nonterminal(t) else t for t in rule]

def normalized_rule_match(r1, r2):
    return rule_to_normalized_rule(r1) == rule_to_normalized_rule(r2)

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA if not normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def get_rulesets(rules):
    rulesets = {}
    for rule in rules:
        nr = tuple(rule_to_normalized_rule(rule))
        if nr not in rulesets: rulesets[nr] = []
        rulesets[nr].append(rule)
    return rulesets

# ### definition conjunction
# Now, we can define the conjunction of definitions as follows.

def and_definitions(rulesA, rulesB):
    AandB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) & set(rulesetsB.keys())
    for k in keys:
        new_rules = and_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules

# Using it.

if __name__ == '__main__':
    expr1 = [r for k in g1 if 'expr' in k for r in g1[k]]
    expr2 = [r for k in g2 if 'expr' in k for r in g2[k]]
    for k in and_definitions(expr1, expr2):
        print(k)
    print()

# ### grammar conjunction
# We can now define our grammar conjunction as follows.

def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    for k1,k2 in I.product(g1_keys, g2_keys):
        if normalize(k1) != normalize(k2): continue
        and_key = and_tokens(k1, k2)
        g[and_key] = and_definitions(g1[k1], g2[k2])
    return g, and_tokens(s1, s2)

# Using it.
if __name__ == '__main__':
    combined_g, combined_s = gatleast.grammar_gc(and_grammars_(g1, s1, g2, s2))
    gatleast.display_grammar(combined_g, combined_s)

# This grammar is now guaranteed to produce instances of both characterizing
# subtrees.

if __name__ == '__main__':
    combined_f = fuzzer.LimitFuzzer(combined_g)
    for i in range(10):
        v = combined_f.iter_fuzz(key=combined_s, max_depth=10)
        assert gatleast.expr_div_by_zero(v)
        assert hdd.expr_double_paren(v)
        print(v)

# ## Producing inputs with at least one of the two fault inducing fragments guaranteed to be present.
# 
# How do we construct grammars that are guaranteed to contain at least one of
# the evocative patterns? This is actually much less complicated than `and`
#
# The idea is simply using the distributive law. A definition is simply
# `A1 or B1 or C1` as before where `A1` etc are rules.
# Now, when you want to `or` two definitions, you have
# `or(A1 or B1 or C1, A2 or B2 or C2)`, then it simply becomes
# `A1 or B1 or C1 or A2 or B2 or C2`
# At this point, our work is essentially done. All that we need to do
# is to merge any rules that potentially allow us to merge. However, there is
# one constraint. When we do a disjunction, it is possible that the rules being
# combined may contain common parts. In such cases, a naive disjunction will
# produce rules which can lead to ambiguous grammars. So, we have to be more
# careful to remove ambiguity.
#
#
# ### Nonterminals
# For nonterminals, it is similar to `and` except that the base cases differ.
# `or` of a base nonterminal with a refined nonterminal is always the base.

def or_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k1
    if not s2: return k2
    if s1 == s2: return k1
    return '<%s or(%s,%s)>' % (b1, s1, s2)

def or_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return or_nonterminals(t1, t2)


# ## rules
# What rules can be merged? Only those rules can be merged that has
# a single refinement difference. That is if we have
# `or(<A 1> <B 5> <C>, <A 2> <B 5> <C>)`, then this merges to
# `<A or(1,2)><B 5><C>`. However `or(<A 1> <B 5> <C>, <A 2> <B 6> <C>)`
# is not mergeable directly. For now, we leave such rules separate. However,
# note that this can lead to ambiguity in grammar. In a later post, we will
# show how to remove this ambiguity.
#
# As a hint as to what we can do to remove ambiguity,
# if given `(<A a1> <B a2>) or (<A a3> <B a4>)`, we replace it with
#
# ```
#   (<A a1> <B a2>) and (<A a3> <B a4>)
# | (<A a1> <B a2>) and neg(<A a3> <B a4>)
# | (<A a3> <B a4>) and neg(<A a1> <B a2>)
# ```
# 
# However, we do not do that here as `neg` is yet to be implemented.


def or_rules(ruleA, ruleB):
    pos = []
    for i,(t1,t2) in enumerate(zip(ruleA, ruleB)):
        if t1 == t2: continue
        else: pos.append(i)
    if len(pos) == 0: return [ruleA]
    elif len(pos) == 1:
        return [[or_tokens(ruleA[i], ruleB[i]) if i == pos[0] else t
                for i,t in enumerate(ruleA)]]
    else: return [ruleA, ruleB]

if __name__ == '__main__':
    a1 = ['<A 1>', '<B>','<C>']
    a2 = ['<A 2>', '<B>','<C>']
    for r in or_rules(a1, a2): print(r)
    print()
    a3 = ['<A 1>', '<B 2>','<C>']
    a4 = ['<A 1>', '<B 3>','<C>']
    for r in or_rules(a3, a4): print(r)
    print()
    a5 = ['<A 1>', '<B 2>','<C 3>']
    a6 = ['<A 1>', '<B 3>','<C>']
    for r in or_rules(a5, a6): print(r)
    print()

# ## rulesets
# For `or` rulesets we first combine
# both rulesets together then (optional) take one at a time,
# and check if it can be merged with another.

def or_ruleset(rulesetA, rulesetB):
    rule,*rules = (rulesetA + rulesetB)
    current_rules = [rule]
    while rules:
        rule,*rules = rules
        new_rules = []
        modified = False
        for i,r in enumerate(current_rules):
            v =  or_rules(r, rule)
            if len(v) == 1:
                current_rules[i] = v[0]
                rule = None
                break
            else:
                continue
        if rule is not None:
            current_rules.append(rule)
    return current_rules

# Using it.
if __name__ == '__main__':
    A = [['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']]
    B = [['<A>', '<B f2>', 'C'], ['<A f1>', '<B f3>', 'C']]
    for k in or_ruleset(A, B): print(k)
    print()

# ### definition disjunction
# Now, we can define the disjunction of definitions as follows.

def or_definitions(rulesA, rulesB):
    AorB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    keys = set(rulesetsA.keys()) | set(rulesetsB.keys())
    for k in keys:
        new_rules = or_ruleset(rulesetsA.get(k, []), rulesetsB.get(k, []))
        AorB_rules.extend(new_rules)
    return AorB_rules

# Using

if __name__ == '__main__':
    expr1 = [r for k in g1 if 'expr' in k for r in g1[k]]
    expr2 = [r for k in g2 if 'expr' in k for r in g2[k]]
    for k in or_definitions(expr1, expr2):
        print(k)
    print()

# ### grammar disjunction

def or_grammars_(g1, s1, g2, s2):
    g = {}
    # now get the matching keys for each pair.
    for k in list(g1.keys()) + list(g2.keys()): 
         g[k] = [[t for t in r] for r in list(set([tuple(k) for k in (g1.get(k, []) + g2.get(k, []))]))]
    
    # We do not actually need to use merging of rule_sets for disjunction.
    s_or = or_nonterminals(s1, s2)
    g[s_or] = g1[s1] + g2[s2]
    return g, s_or


# Using it.
if __name__ == '__main__':
    or_g, or_s = gatleast.grammar_gc(or_grammars_(g1, s1, g2, s2))
    gatleast.display_grammar(or_g, or_s)

# This grammar is now guaranteed to produce at least one of the evocative subtrees
# Using it.
if __name__ == '__main__':
    or_f = fuzzer.LimitFuzzer(or_g)
    for i in range(10):
        v = or_f.iter_fuzz(key=or_s, max_depth=10)
        assert (gatleast.expr_div_by_zero(v) or hdd.expr_double_paren(v))
        print(v)
        if gatleast.expr_div_by_zero(v) == hdd.PRes.success: print('>', 1)
        if hdd.expr_double_paren(v) == hdd.PRes.success: print('>',2)

# As before, the runnable source of this notebook can be found [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-10-multiple-fault-grammars.py)
