# ---
# published: true
# title: Conjunction, Disjunction, and Complement of Regular Grammars
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/)
# I showed how to produce a grammar out of regular expressions. In the
# second [post](/post/2021/10/23/regular-expression-to-regular-grammar/), I
# claimed that we need a regular grammar because regular grammars have more
# interesting properties such as being closed under
# intersection and complement. Now, the question is how do we actually do
# the intersection between two regular grammars? For this post, I assume that
# the regular expressions are in the canonical format as given in
# [this post](/post/2021/10/24/canonical-regular-grammar/).
# That is, there are only two possible rule formats $$ A \rightarrow a B $$
# and $$ A \rightarrow \epsilon $$. Further, the canonical format requires that
# there is only one rule in a nonterminal definition that starts with a
# particular terminal symbol. Refer to
# [this post](/post/2021/10/24/canonical-regular-grammar/) for how convert any
# regular grammar to the canonical format.
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
rxcanonical = import_file('rxcanonical', '2021-10-24-canonical-regular-grammar.py')

# There are only two patterns of rules in canonical regular grammars.
#  
# 1. $$ A \rightarrow aB $$
# 2. $$ A \rightarrow \epsilon $$
# 
# The idea is that when evaluating intersection of the start symbol,
# pair up all rules that start with the same terminal symbol.
# Only the intersection of these would exist in the resulting grammar.
# The intersection of
#  
# ```
# <A1> ::= a <B1>
# ```
#  
# and

# ```
# <A2> ::= a <B2>
# ```
#  
# is simply
#  
# ```
# <and(A1,A2)> ::= a <and(B1,B2)>
# ```
#  
# For constructing such rules, we also need to parse the boolean expressions
# in the nonterminals. So, we define our grammar first.

import string
EMPTY_NT = '<_>'
ALL_NT = '<.*>'
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
    '<letter>' : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = '<start>'

# Next, we define our expression class which is used to wrap boolean
# expressions and extract components of boolean expressions.

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

# Ensure that it can parse boolean expressions in nonterminals.

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

# ## Conjunction of two regular grammars
# 
# Next, we define the conjunction of two regular grammars in the canonical
# format. We will define the conjunction of two definitions, and at the end
# discuss how to stitch it together for the complete grammar. The nice thing
# here is that, because our grammar is in the canonical format, conjunction
# disjunction and negation is really simple, and follows roughly the same
# framework.
# 
# ### Conjunction of nonterminal symbols

def and_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<and(%s,%s)>' % (k1[1:-1], k2[1:-1])

# Ensure that it works

if __name__ == '__main__':
    k = and_nonterminals('<A>', '<B>')
    print(k)

# ### Conjunction of rules
# 
# We only provide conjunction for those rules whose initial terminal symbols are
# the same or it is an empty rule.

def and_rules(r1, r2):
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = and_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

# We check to make sure that conjunction of rules work.

if __name__ == '__main__':
    k, r = and_rules([], [])
    print(k, r)
    k, r = and_rules(['a', '<A>'], ['a', '<B>'])
    print(k, r)
    k, r = and_rules(['a', '<A>'], ['a', '<A>'])
    print(k, r)

# ### Conjunction of definitions

def get_leading_terminal(rule):
    if not rule: return ''
    return rule[0]

def and_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for terminal in paired1:
        if terminal not in paired2: continue
        new_key, intersected = and_rules(paired1[terminal], paired2[terminal])
        new_rules.append(intersected)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules

# Checking that conjunction of definitions work.

if __name__ == '__main__':
    g1, s1 = rxcanonical.canonical_regular_grammar({
         '<start1>' : [['a1', '<A1>']],
         '<A1>' : [['b1', '<B1>'], ['c1', '<C1>']],
         '<B1>' : [['c1','<C1>']],
         '<C1>' : [[]]
    }, '<start1>')
    g2, s2 = rxcanonical.canonical_regular_grammar({
         '<start2>' : [['a1', '<A2>']],
         '<A2>' : [['b1', '<B2>'], ['d1', '<C2>']],
         '<B2>' : [['c1','<C2>'], []],
         '<C2>' : [[]]
    }, '<start2>')

    rules = and_definitions(g1['<start1>'], g2['<start2>'])
    print(rules)
    rules = and_definitions(g1['<A1>'], g2['<A2>'])
    print(rules)
    rules = and_definitions(g1['<B1>'], g2['<B2>'])
    print(rules)

# ## Disjunction of two regular grammars
# 
# For disjunction, the strategy is the same. We line up rules in both
# definitions with same starting symbol, then construct the conjunction of the
# nonterminal parts. Unlike conjunction, however, we do not throw away the rules
# without partners in the other definition. Instead, they are added to the
# resulting definition.

# ### Disjunction of nonterminal symbols

def or_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<or(%s,%s)>' % (k1[1:-1], k2[1:-1])

# Ensure that it works

if __name__ == '__main__':
    k = or_nonterminals('<A>', '<B>')
    print(k)
    k = or_nonterminals('<A>', '<A>')
    print(k)

# ### Disjunction of rules
# 
# We assume that the starting terminal symbol is the same for both rules.

def or_rules(r1, r2):
    # the initial chars are the same
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = or_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

# We check to make sure that disjunction for rules work.

if __name__ == '__main__':
    k, r = or_rules([], [])
    print(k, r)
    k, r = or_rules(['a', '<A>'], ['a', '<B>'])
    print(k, r)
    k, r = or_rules(['a', '<A>'], ['a', '<A>'])
    print(k, r)

# ### Disjunction of definitions

def or_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    new_rules = []
    new_keys = []
    p0 = [c for c in paired1 if c in paired2]
    p1 = [c for c in paired1 if c not in paired2]
    p2 = [c for c in paired2 if c not in paired1]
    for terminal in p0:
        new_key, kunion = or_rules(paired1[terminal], paired2[terminal])
        new_rules.append(kunion)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules + [paired1[c] for c in p1] + [paired2[c] for c in p2]

# We check that disjunction of definitions work.

if __name__ == '__main__':
    g3, s3 = rxcanonical.canonical_regular_grammar({
         '<start3>' : [['a1', '<A3>']],
         '<A3>' : [['b1', '<B3>'], ['c1', '<C3>']],
         '<B3>' : [['c1','<C3>']],
         '<C3>' : [[]]
    }, '<start3>')
    g4, s4 = rxcanonical.canonical_regular_grammar({
         '<start4>' : [['a1', '<A4>']],
         '<A4>' : [['b1', '<B4>'], ['d1', '<C4>']],
         '<B4>' : [['c1','<C4>'], []],
         '<C4>' : [[]]
    }, '<start4>')

    rules = or_definitions(g3['<start3>'], g4['<start4>'])
    print(rules)
    rules = or_definitions(g3['<A3>'], g4['<A4>'])
    print(rules)
    rules = or_definitions(g3['<B3>'], g4['<B4>'])
    print(rules)

# ## Complement of regular grammars
# 
# For complement, the idea is to treat each pattern separately. We take the
# definition of each nonterminal separately.
# 
# 1. If the nonterminal definition does not contain $$ \epsilon $$, we add `EMPTY_NT`
#    to the resulting definition. If it contains, then we skip it. The `EMPTY_NT` is
#    defined below.

G_EMPTY = {EMPTY_NT: [[]]}

#  
# ```
# <_>  := 
# ```

# 2. We collect all terminal symbols that start up a rule in the definition.
#    For each such rule, we add a rule that complements the nonterminal used.
#    That is, given 
#  
# ```
# <A>  :=  a <B>
# ```
# 
#    We produce
# 
# ```
# <neg(A)>  :=  a <neg(B)>
# ```
#    as one of the complement rules.
# 
# 3. For every remaining terminal in the `TERMINAL_SYMBOLS`, we add a match for
#    any string given by `ALL_NT` (`<.*>`) and its definition is given below
# 
# We first define our `TERMINAL_SYMBOLS`

TERMINAL_SYMBOLS = list(string.digits + string.ascii_lowercase + string.ascii_uppercase)

# Then, use it to define `ALL_NT`

G_ALL = {ALL_NT:
        [[c, ALL_NT] for c in TERMINAL_SYMBOLS]
        + [[ ]]
        }

#  
# ```
# <.*>  := . <.*>
# ```
# 
# We start by producing the complement of a single nonterminal symbol.

def negate_nonterminal(k): return '<neg(%s)>' % k[1:-1]

# Ensure that it works

if __name__ == '__main__':
    k = negate_nonterminal('<A>')
    print(k)

# ### Complement of a single rule

def negate_key_in_rule(rule):
    if len(rule) == 0: return None
    assert len(rule) != 1
    assert fuzzer.is_terminal(rule[0])
    assert fuzzer.is_nonterminal(rule[1])
    return [rule[0], negate_nonterminal(rule[1])]

# Ensure that it works

if __name__ == '__main__':
    r = negate_key_in_rule(['a', '<A>'])
    print(r)
    r = negate_key_in_rule([])
    print(r)

# ### Complement a definition
#  
# We complement a definition by applying complement to each rule in the
# original definition, and adding any new rules that did not match the
# original definition.

def negate_definition(d1, terminal_symbols=TERMINAL_SYMBOLS):
    paired = {get_leading_terminal(r):r for r in d1}
    remaining_chars = [c for c in terminal_symbols if c not in paired]
    new_rules = [[c, '<.*>'] for c in remaining_chars]

    # Now, we try to negate individual rules. It starts with the same
    # character, but matches the negative.
    for rule in d1:
        r = negate_key_in_rule(rule)
        if r is not None:
            new_rules.append(r)

    # should we add empty rule match or not?
    if [] not in d1:
        new_rules.append([])
    return new_rules

# Checking complement of a definition in an example.

if __name__ == '__main__':
    g4, s4 = rxcanonical.canonical_regular_grammar({
         '<start4>' : [['a', '<A4>']],
         '<A4>' : [['b', '<B4>'], ['c', '<C4>']],
         '<B4>' : [['c','<C4>']],
         '<C4>' : [[]]
    }, '<start4>')

    rules = negate_definition(g4['<start4>'])
    print(rules)
    rules = negate_definition(g4['<A4>'])
    print(rules)
    rules = negate_definition(g4['<B4>'])
    print(rules)

# ## Complete
# 
# Until now, we have only produced conjunction, disjunction, and complement for
# definitions. When producing these, we have introduced new nonterminals in
# definitions that are not yet defined. For producing a complete grammar, we
# need to define these new nonterminals too. This is what we will do in this
# section. We first define a few helper procedures.
# 
# The `remove_empty_defs()` recursively removes any nonterminal that has empty
# definitions. That is, of the form `"<A>" : []`. Note that it is different from
# an epsilon rule which is `"<A>" : [[]]`

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

# We also need the ability to compactly display a canonical regular grammar
# and we define it as below.

def display_terminals(terminals, negate=False):
    if negate: return '[^%s]' % (''.join(terminals))
    else:
        if len(terminals) == 1:
            return terminals[0]
        return '[%s]' % (''.join(terminals))

def display_ruleset(nonterminal, ruleset, pre, verbose, all_terminal_symbols=TERMINAL_SYMBOLS):
    if ruleset == [[]]:
        print('| {EMPTY}')
        return
    terminals = [t[0] for t in ruleset]
    rem_terminals = [t for t in all_terminal_symbols if t not in terminals]
    if len(terminals) <= len(rem_terminals):
        v = '%s %s' % (display_terminals(terminals), nonterminal)
        s = '%s|   %s' % (pre, v)
        print(s)
    else:
        if rem_terminals == []:
            v = '. %s' % nonterminal
        else:
            v = '%s %s' % (display_terminals(rem_terminals, negate=True), nonterminal)
        s = '%s|   %s' % (pre, v)
        print(s)

from collections import defaultdict

def definition_rev_split_to_rulesets(d1):
    rule_sets = defaultdict(list)
    for r in d1:
        if len(r) > 0:
            assert fuzzer.is_terminal(r[0]) # no degenerate rules
            assert fuzzer.is_nonterminal(r[1]) # no degenerate rules
            rule_sets[r[1]].append(r)
        else:
            rule_sets[''].append(r)
    return rule_sets

def display_definition(grammar, key, r, verbose):
    if verbose > -1: print(key,'::=')
    rulesets = definition_rev_split_to_rulesets(grammar[key])
    for nonterminal in rulesets:
        pre = ''
        display_ruleset(nonterminal, rulesets[nonterminal], pre, verbose)
    return r

def display_canonical_grammar(grammar, start, verbose=0):
    r = 0
    k = 0
    order, not_used, undefined = gatleast.sort_grammar(grammar, start)
    print('[start]:', start)
    for key in order:
        k += 1
        r = display_definition(grammar, key, r, verbose)
        if verbose > 0:
            print(k, r)

    if undefined:
        print('[undefined keys]')
        for key in undefined:
            if verbose == 0:
                print(key)
            else:
                print(key, 'defined in')
                for k in undefined[key]: print(' ', k)

# Make sure it works

if __name__ == '__main__':
    g0, s0 = rxcanonical.canonical_regular_grammar({**{
         '<start0>' : [['a', '<A0>']],
         '<A0>' : [['b', '<B0>'], ['c', '<C0>']],
         '<B0>' : [['c', ALL_NT]],
         '<C0>' : [[EMPTY_NT]]
    }, **G_ALL, **G_EMPTY}, '<start0>')
    display_canonical_grammar(g0, s0)

# Next, we define `complete()` which recursively computes the complex
# nonterminals that is left undefined in a grammar from the simpler
# nonterminal definitions.

def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start

# That is, for any conjunction, disjunction, or negation of grammars, we start
# at the start symbol, and produce the corresponding operation in the definition
# of the start symbol. Then, we check if any new new nonterminal was used in any
# of the rules. If any were used, we recursively define them using the
# nonterminals already present in the grammar. This is very similar to the
# `ReconstructRules` from [fault expressions](/post/2021/09/11/fault-expressions/)
# for context-free grammars, but is also different enough. Hence, we define a
# completely new class.


class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

# We start with reconstructing a single key. For example, given the two grammars
# `G1` and `G2`, and their start symbols `S1`, and `S2`, to compute an intersection
# of `G1 & G2`, we simply reconstruct `<and(S1,S2)>` from the two grammars, and
# recursively define any undefined nonterminals.

class ReconstructRules(ReconstructRules):
    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            key_to_reconstruct, *keys = keys
            if log: print('reconstructing:', key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception('Key found:', key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            assert bexpr.simple()
            d, s = self.reconstruct_rules_from_bexpr(bexpr)
            if log: print('simplified_to:', s)
            self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct

# Given a complex boolean expression, construct the definition for it from the
# grammar rules.

class ReconstructRules(ReconstructRules):
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
                assert False

# Produce disjunction of grammars

class ReconstructRules(ReconstructRules):
    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key

# Using

if __name__ == '__main__':
    g1 = {
            '<start1>' : [['0', '<A1>']],
            '<A1>' : [['a', '<B1>']],
            '<B1>' : [['b','<C1>'], ['c', '<D1>']],
            '<C1>' : [['c', '<D1>']],
            '<D1>' : [[]],
            }
    s1 = '<start1>'
    g2 = {
            '<start2>' : [['0', '<A2>']],
            '<A2>' : [['a', '<B2>'], ['b', '<D2>']],
            '<B2>' : [['b', '<D2>']],
            '<D2>' : [['c', '<E2>']],
            '<E2>' : [[]],
            }
    s2 = '<start2>'
    s1_s2 = or_nonterminals(s1, s2)
    g, s = complete({**g1, **g2, **G_EMPTY, **G_ALL}, s1_s2, True)
    display_canonical_grammar(g, s)

    gf = fuzzer.LimitFuzzer(g)
    gp = earleyparser.EarleyParser(g, check_syntax=False)
    gp1 = earleyparser.EarleyParser(g1, check_syntax=False)
    gp2 = earleyparser.EarleyParser(g2, check_syntax=False)
    for i in range(10):
        v = gf.iter_fuzz(key=s, max_depth=10)
        r = gp.recognize_on(v, s)
        assert r
        r1 = gp1.recognize_on(v, s1)
        r2 = gp2.recognize_on(v, s2)
        assert r1 or r2

# Produce conjunction  of grammars

class ReconstructRules(ReconstructRules):
    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key

# We now verify that it works.

if __name__ == '__main__':
    g1 = {
            '<start1>' : [['0', '<A1>']],
            '<A1>' : [['a', '<B1>']],
            '<B1>' : [['b','<C1>'], ['c', '<D1>']],
            '<C1>' : [['c', '<D1>']],
            '<D1>' : [[]],
            }
    s1 = '<start1>'
    g2 = {
            '<start2>' : [['0', '<A2>']],
            '<A2>' : [['a', '<B2>'], ['b', '<D2>']],
            '<B2>' : [['b', '<D2>']],
            '<D2>' : [['c', '<E2>']],
            '<E2>' : [[]],
            }
    s2 = '<start2>'
    s1_s2 = and_nonterminals(s1, s2)
    g, s = complete({**g1, **g2, **G_EMPTY, **G_ALL}, s1_s2, True)
    display_canonical_grammar(g, s)

    gf = fuzzer.LimitFuzzer(g)
    gp = earleyparser.EarleyParser(g, check_syntax=False)
    gp1 = earleyparser.EarleyParser(g1, check_syntax=False)
    gp2 = earleyparser.EarleyParser(g2, check_syntax=False)
    for i in range(10):
        v = gf.iter_fuzz(key=s, max_depth=10)
        r = gp.recognize_on(v, s)
        assert r
        r1 = gp1.recognize_on(v, s1)
        r2 = gp2.recognize_on(v, s2)
        assert r1 and r2

# Next, we come to complement.

class ReconstructRules(ReconstructRules):
    def reconstruct_neg_bexpr(self, bexpr):
        fst = bexpr.op_fst()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        neg_rules = negate_definition(d1)
        return neg_rules, f_key

# Ensure that negation also works.

if __name__ == '__main__':
    g1 = {
            '<start1>' : [['0', '<A1>']],
            '<A1>' : [['a', '<B1>']],
            '<B1>' : [['b','<C1>'], ['c', '<D1>']],
            '<C1>' : [['c', '<D1>']],
            '<D1>' : [[]],
            }
    s1 = '<start1>'
    s1_ = negate_nonterminal(s1)
    g, s = complete({**g1, **G_EMPTY, **G_ALL}, s1_, True)
    display_canonical_grammar(g, s)

    gf = fuzzer.LimitFuzzer(g)
    gp = earleyparser.EarleyParser(g, check_syntax=False)
    gp1 = earleyparser.EarleyParser(g1, check_syntax=False)
    for i in range(10):
        v = gf.iter_fuzz(key=s, max_depth=10)
        r = gp.recognize_on(v, s)
        assert r
        r1 = gp1.recognize_on(v, s1)
        assert not r1

# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-26-regular-grammar-expressions.py)
