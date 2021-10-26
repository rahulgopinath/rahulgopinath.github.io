# ---
# published: true
# title: Intersection of Two Regular Grammars
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/)
# I showed how to produce a grammar out of regular expressions. In the
# second [post](/post/2021/10/23/regular-expression-to-regular-grammar/), I
# claimed that we need a regular grammar because
# regular grammars have more interesting properties such as being closed under
# intersection and complement. Now, the question is how do we actually do
# the intersection between two regular grammars?
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
gexpr = import_file('gexpr', '2021-09-11-fault-expressions.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')

# There are only three patterns of rules (assuming no degenerate rules)
# in regular grammars.
#
# 1. $$ A -> aB $$
# 2. $$ A -> a $$
# 3. $$ A -> \epsilon $$
#
# The idea is that when evaluating intersection of the start symbol,
# pair up all rules that start with the same terminal symbol.
# Only the intersecion of these would exist in the resulting grammar.
# The intersection of $$ <A1> -> a <B1> $$ and $$ <A2> -> a <B2> $$
# is simply $$ <A1&A2> -> a <B1&B2> $$.
#
# For constructing such rules, we also need to parse the boolean expressions
# in the nonterminals. So, we define our grammar first.

import string
EMPTY_NT = '<_>'
BEXPR_GRAMMAR = {
    '<start>': [['<', '<bexpr>', '>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexprs>', ')'],
        ['<key>']],
    '<bexprs>' : [['<bexpr>', ',', '<bexprs>'], ['<bexpr>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<key>': [['<letters>'],[EMPTY_NT[1:-1]]], # epsilon is <_>
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']
    ],
    '<digits>': [
        ['<digit>'],
        ['<digit>', '<digits>']],
    '<digit>': [[i] for i in (string.digits)],
    '<letter>' : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = '<start>'

# Next, we define our expression class
class BExpr(gexpr.BExpr):
    def create_new(self, e): return BExpr(e)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][1]
        return bexpr

    def as_key(self):
        s = self.simple()
        return '<%s>' % s

# Ensure that it works
if __name__ == '__main__':
    strings = [
            '<1>',
            '<and(1,2)>',
            '<or(1,2)>',
            '<and(1,or(2,3,1))>',
    ]
    for s in strings:
        e = BExpr(s)
        print(e.as_key())

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

def nonterminal_intersection(k1, k2): return '<%s&%s>' % (k1[1:-1], k2[1:-1])

import itertools as I

def intersect_nonterminals(k1, k2):
    return '<and(%s,%s)>' % (k1[1:-1], k2[1:-1])

def intersect_rules(r1, r2):
    # the initial chars are the same
    if not r1: return [], [] # epsilon
    assert r1[0] == r2[0]
    if len(r1) == 1:
        if len(r2) == 1: return [], r2
        nk = intersect_nonterminals(r1[1], EMPTY_NT)
        return [nk], [r1[0], nk]
    elif len(r2) == 1:
        nk = intersect_nonterminals(r1[1], EMPTY_NT)
        return [nk], [r2[0], nk]
    else:
        nk = intersect_nonterminals(r1[1], r2[1])
        return [nk], [r1[0], nk]

def pair_up_rulesets(rs1, rs2):
    nks = []
    new_rules = []
    for r1, r2 in I.product(rs1, rs2):
        nk, new_rule = intersect_rules(r1, r2)
        nks.extend(nk)
        new_rules.append(new_rule)
    return nks, new_rules

def and_definitions(d1, d2):
    # first find the rule sets with same starting terminal symbol.
    rule_sets1 = split_to_rulesets(d1)
    rule_sets2 = split_to_rulesets(d2)
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for char in rule_sets1:
        if char not in rule_sets2: continue
        rset1 = rule_sets1[char]
        rset2 = rule_sets2[char]
        nks, intersected = pair_up_rulesets(rset1, rset2)
        new_rules.extend(intersected)
        new_keys.extend(nks)
    return new_rules

def reconstruct_key(key, g):
    pass

def intersect_grammars(g1, s1, g2, s2):
    ss = intersect_nonterminals(s1, s2)
    remaining_keys = [ss]
    g = {**g1, **g2}
    while remaining_keys:
        key, *remaining_keys = remaining_keys
        if key in g: continue
        g, s, remaining = reconstruct_key(key, g)
        remaining_keys.extend(remaining)
    return g, ss

class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

    def reconstruct_rules_from_bexpr(self, bexpr):
        f_key = bexpr.as_key()
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == 'and':
                return self.reconstruct_and_bexpr(bexpr)
            elif operator == 'or':
                return self.reconstruct_or_bexpr(bexpr)
            elif operator == 'neg':
                return self.reconstruct_neg_bexpr(bexpr)
            else:
                return self.reconstruct_orig_bexpr(bexpr)

    def reconstruct_orig_bexpr(self, bexpr):
        assert False

    def reconstruct_neg_bexpr(self, bexpr):
        assert False

    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key

    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key

    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            if log: print(len(keys))
            key_to_reconstruct, *keys = keys
            if log: print('reconstructing:', key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception('Key found:', key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            nrek = key_to_reconstruct
            if bexpr.simple():
                nkey = bexpr.as_key()
                if log: print('simplified_to:', nkey)
                d, s = self.reconstruct_rules_from_bexpr(bexpr)
                self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            else:
                nkey = nrek # base key
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct

def remove_empty_key_refs(grammar, ek):
    new_grammar = {}
    for k in grammar:
        if k == ek: continue
        new_rules = []
        for r in grammar[k]:
            if ek in r:
                continue
            new_rules.append(r)
        new_grammar[k] = new_rules
    return new_grammar


def remove_empty_defs(grammar, start):
    empty = [k for k in grammar if not grammar[k]]
    while empty:
        k, *empty = empty
        grammar = remove_empty_key_refs(grammar, k)
        empty = [k for k in grammar if not grammar[k]]
    return grammar, start

def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start

# Using

if __name__ == '__main__':
    my_re1 = 'a1(b1(c1)|b1)'
    g_empty = {EMPTY_NT: [[]]}
    g1 = {
            '<start1>' : [['0', '<A1>']],
            '<A1>' : [['a', '<B1>']],
            '<B1>' : [['b','<C1>'], ['b']],
            '<C1>' : [['c1']]
            }
    s1 = '<start1>'
    my_re2 = 'a2(b2)|a2'
    g2 = {
            '<start2>' : [['0', '<A2>']],
            '<A2>' : [['a', '<B2>'], ['a2']],
            '<B2>' : [['b']]
            }
    s2 = '<start2>'
    s1_s2 = intersect_nonterminals(s1, s2)
    g, s = complete({**g1, **g2, **g_empty}, s1_s2, True)
    print(s)
    gatleast.display_grammar(g,s)

# The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py)
