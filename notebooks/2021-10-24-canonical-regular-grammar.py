# ---
# published: true
# title: Canonical Regualar Grammars
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
# with no further restrictions. However, for working with regular grammars,
# such freedom can be unwieldy. Hence, without loss of generality, we define
# a canonical format for regular grammars, to which any regular grammar can
# be converted to.
#
# * $$ A \rightarrow a $$
# * $$ A \rightarrow a B $$
# * $$ A \rightarrow \epsilon $$
# 
# where given a nonterminal $$A$$ and a terminal symbol $$ a $$ at most one of
# its rules will start with a terminal symbol $$ a $$. That is, if the original
# grammar had multiple rules that started with $$ a $$, they will be collected
# into a new nonterminal symbol. Further, there will be at most one terminal
# symbol in a rule. That is, if there are more terminal symbols, then we bundle
# that to a new nonterminal symbol
#
#
# We start with importing the prerequisites

import sys, imp, pprint, string

def make_module(modulesource, sourcestr, modname):
    codeobj = compile(modulesource, sourcestr, 'exec')
    newmodule = imp.new_module(modname)
    exec(codeobj, newmodule.__dict__)
    return newmodule

def import_file(name, location):
    if "pyodide" in sys.modules:
        import pyodide
        github_repo = 'https://raw.githubusercontent.com/'
        my_repo =  'rahulgopinath/rahulgopinath.github.io'
        module_loc = github_repo + my_repo + '/master/notebooks/%s' % location
        module_str = pyodide.open_url(module_loc).getvalue()
    else:
        module_loc = './notebooks/%s' % location
        with open(module_loc, encoding='utf8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# We import the following modules

earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')

# 


def is_degenerate_rule(rule):
    return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

def remove_degenerate_rules(g, s):
    # assumes no cycle
    cont = True
    while cont:
        cont = False
        new_g = {}
        for k in g:
            new_rules = []
            new_g[k] = new_rules
            for r in g[k]:
                if is_degenerate_rule(r):
                    if r[0] == k: continue # self recursion
                    new_r = g[r[0]]
                    if is_degenerate_rule(new_r): cont = True
                    new_rules.extend(new_r)
                else:
                    new_rules.append(r)
        return new_g, s

from collections import defaultdict

def split_to_rulesets(rules):
    rule_sets = defaultdict(list)
    for r in rules:
        if len(r) > 0:
            assert not fuzzer.is_nonterminal(r[0]) # no degenerate
            rule_sets[r[0]].append(r)
        else:
            rule_sets[''].append(r)
    return rule_sets

def join_keys(keys):
    return 'or(%s)' % ','.join(keys)

def join_rules(rules):
    # produce rules that combine their second nonterminal
    # and return the new key with `or(.,.)`
    terminal = rules[0][1]
    assert all(r[0] == terminal for r in rules)
    keys = []
    for r in rules:
        if len(r) > 1:
            keys.append(r[1])
        else:
            keys.append('')
    new_key = join_keys(keys)
    return tuple(keys), [terminal, new_key]

def construct_keys(new_key, g):

def collapse_similar_starting_rules(g, s):
    new_g = defaultdict(list)
    keys_to_construct = []
    for k in g:
        rsets = split_to_rulesets(g[k])
        # each ruleset will get one rule
        for c in rsets:
            keys_to_combine, new_rule = join_rules(rsets[c])
            new_g[k].append(new_rule)
            keys_to_construct.append(keys_to_combine)

    seen_keys = set()
    while keys_to_construct:
        cur_key_lst, *keys_to_construct = keys_to_construct
        if cur_key_lst in seen_keys: continue
        seen_keys.add(cur_key_lst)
        new_keys, new_g = construct_keys(cur_key_lst, {**g, **new_g})
        keys_to_construct.extend(new_keys)
    return new_g, s

def remove_multi_terminals(g, s):
    new_g = defaltdict(list)
    for k in g:
        for r in g[k]:
            if len(r) > 1:
                tok = r[1]
                if not fuzzer.is_nonterminal(tok):
                    new_key = '<%s_%s>' % (k[1:-1], tok)
                    new_rule = [r[0], new_key]

                    new_g[new_key].append(r[1:])
                    new_g[k].append(new_rule)
                else:
                    new_g[k].append(r)
            else:
                new_g[k].append(r)

def canonical_regular_grammar(g0, s0):
    g1, s1 = remove_degenerate_rules(g0, s0)
    g1, s1 = remove_multi_terminals(g0, s0)
    g2, s2 = collapse_similar_starting_rules(g1, s1)

    return g2, s2

