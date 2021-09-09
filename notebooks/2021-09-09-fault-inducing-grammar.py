# ---
# published: true
# title: Specializing Grammars for Inducing Faults
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In my previous post on [DDSet](/post/2020/08/03/simple-ddset/) I explained how
# one can abstract failure inducing inputs. The idea is that given an input such
# as `'1+((2*3/4))'` which induces a
# failure in the program, one can extract a [minimal](/post/2019/12/04/hdd/)
# failure inducing input such as say `'((4))'`, which can again be abstracted to
# produce the expression `((<expr>))` which precisely defines the fault
# inducing input. Such an input is quite useful for the developers to understand
# why a failure occurred. 

# As before, let us start with importing our required modules.

import sys, imp

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
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# We import the following modules
earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
hdd = import_file('hdd', '2019-12-04-hdd.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
ddset = import_file('ddset', '2020-08-03-simple-ddset.py')

# We have our input that causes the failure.

if __name__ == '__main__':
    my_input = '1+((2*3/4))'
    assert hdd.expr_double_paren(my_input) == hdd.PRes.success

# We first parse the input

if __name__ == '__main__':
    expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
    parsed_expr = list(expr_parser.parse_on(my_input, hdd.EXPR_START))[0]

# Then reduce input

if __name__ == '__main__':
    reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)

# Finally, extract the abstract pattern.

if __name__ == '__main__':
    pattern = ddset.ddset_abstract(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
    ddset.display_abstract_tree(pattern)

# However, it does not actually tell you in what all
# circumstances the failure can be reproduced. The problem is that it
# represents a *complete* abstract input. The only general part here is
# `<expr>` between the doubled parenthesis. So, it tells us that we can
# produce `((1))`, `((2 + 3))` etc. but these are not the only possible
# errors. Indeed, our original error: '1+((2*3/4))' does not fit this
# template. So, how can we rectify this limitation?

# # A grammar with at least one fault inducing fragment

# The basic idea is that if we can find a `characterizing node` of the
# abstract fault tree, such that the presence of the abstract subtree
# in the input guarantees the failure, then we can modify the grammar such
# that this abstract subtree is always present. That is, for any input
# from such a grammar, at least one instance of the abstract failure iducing
# subtree will be present. This is fairly easy to do if the generated tree
# contains a nonterminal of the same kind as that of the characterizing node.
# Simply replace that node with the characterizing node, and fill in the
# abstract nonterminals with concrete values.

# ## Reachable Grammar
# 
# On the other hand, this gives us an idea. What if we modify the grammar
# such that at least one instance of such a nonterminal is present? Such
# a grammar is called the `reachable_grammar`.

# To produce a reaching grammar, first we need to find what nonterminals are
# reachable from the expansion of a given nonterminal.
# A nonterminal `<A>` is reachable from another nonterminal `<B>` if and only
# if one of the expansion rules for `<B>` contains the nonterminal `<A>` or
# it is reachable from one of the nonterminals in the expansion rules of `<B>`
# Note that it is not enough to be the same nonterminal. That is, (for e.g.)
# `<A>` is not # reachable from `<A>` if expansion rules of `<A>` contain only
# terminal symbols.

def find_reachable_keys(grammar, key, reachable_keys=None, found_so_far=None):
    if reachable_keys is None: reachable_keys = {}
    if found_so_far is None: found_so_far = set()

    for rule in grammar[key]:
        for token in rule:
            if not fuzzer.is_nonterminal(token): continue
            if token in found_so_far: continue
            found_so_far.add(token)
            if token in reachable_keys:
                for k in reachable_keys[token]:
                    found_so_far.add(k)
            else:
                keys = find_reachable_keys(grammar, token, reachable_keys, found_so_far)
    return found_so_far

# 
if __name__ == '__main__':
    for key in hdd.EXPR_GRAMMAR:
        keys = find_reachable_keys(hdd.EXPR_GRAMMAR, key, {})
        print(key, keys)

# We can now collect it in a data structure for easier access

def reachable_dict(grammar):
    reachable = {}
    for key in grammar:
        keys = find_reachable_keys(grammar, key, reachable)
        reachable[key] = keys
    return reachable

# That is, if we want to know the nonterminals that are reachable from `<integer>`,
# we can simply do

if __name__ == '__main__':
    reaching = reachable_dict(hdd.EXPR_GRAMMAR)
    print(reaching['<integer>'])

# That is, only `<digit>` and `<integer>` are reachable from the expansion of
# nonterminal `<integer>`

# ## Reachable positions.

# Next, given a characterizing node, we want to find what tokens of the grammar
# can can actually embed such a node.

def get_reachable_positions(rule, fkey, reachable):
    positions = []
    for i, token in enumerate(rule):
        if not fuzzer.is_nonterminal(token): continue
        if fkey == token or fkey in reachable[token]:
            positions.append(i)
    return positions

# Say we assume that `<factor>` is the characterizing node. Here are the
# locations in grammar where one can embed the characterizing node.

if __name__ == '__main__':
    for k in hdd.EXPR_GRAMMAR:
        print(k)
        for rule in hdd.EXPR_GRAMMAR[k]:
            v = get_reachable_positions(rule, '<factor>', reaching)
            print('\t', rule, v)


# ## Insertion Grammar

# Given the insertion locations, can we produce a grammar such that we can
# *guarantee* that *at least one* instance of characterizing node can be inserted?
# To do that, all we need to guarantee is that the start node in any derivation
# tree can *reach* the characterizing node.
#
# For now, let us call our fault `F1`. Let us indicate that our start symbol
# guarantees reachability of characterizing node by specializing it. So, our new
# start symbol is `<start F1>`
# 
# Next, for the start symbol to guarantee reachability to characterizing node,
# all that we need to ensure is that *all* the expansion rules of start can
# reach the characterizing node. On the other hand, for a guarantee that an
# expansion rule can reach the characterizing node, all that is required is that
# one of the nonterminals in that rule guarantees reachability.
#
# We start with a few helper functions

def tsplit(token):
    assert token[0], token[-1] == ('<', '>')
    front, *back = token[1:-1].split(None, 1)
    return front, ' '.join(back)

def refinement(token):
    return tsplit(token)[1].strip()

def is_refined_key(key):
    assert fuzzer.is_nonterminal(key)
    return (' ' in key)

def is_base_key(key):
    return not is_refined_key(key)

def stem(token):
    return tsplit(token)[0].strip()

def refine_base_key(k, prefix):
    assert fuzzer.is_nonterminal(k)
    assert is_base_key(k)
    return '<%s %s>' % (stem(k), prefix)

# Defining the `reachable_key()`

def reachable_key(grammar, key, cnodesym, suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # skip this rule because we can not embed the fault here.
            continue
        else:
            # at each position, insert the cnodesym
            for pos in positions:
                new_rule = [refine_base_key(t, suffix)
                            if pos == p else t for p,t in enumerate(rule)]
                my_rules.append(new_rule)
    return (refine_base_key(key, suffix), my_rules)

# It is used as follows

if __name__ == '__main__':
    for key in hdd.EXPR_GRAMMAR:
        fk, rules = reachable_key(hdd.EXPR_GRAMMAR, key, '<factor>', 'F1', reaching)
        print(fk)
        for r in rules:
            print('    ', r)
        print()

# ## Pattern Grammar
# Next, we need to ensure that our characterizing node can form a unique subtree
# For that, all we need to do is that all nodes except abstract are named uniquely.

def mark_unique_name(symbol, suffix, i):
    return '<%s %s_%s>' % (symbol[1:-1], suffix, str(i))

def mark_unique_nodes(node, suffix, counter=None):
    if counter is None: counter = [0]
    symbol, children, *abstract = node
    if ddset.is_node_abstract(node): # we don't markup further
        return node
    if fuzzer.is_nonterminal(symbol):
        i = counter[0]
        counter[0] += 1
        cs = [mark_unique_nodes(c, suffix, counter) for c in children]
        return (mark_unique_name(symbol, suffix, i), cs, *abstract)
    else:
        assert not children
        return (symbol, children, *abstract)

# Using

if __name__ == '__main__':
    unique_pattern_tree = mark_unique_nodes(pattern, 'F1')
    ddset.display_abstract_tree(unique_pattern_tree)

# We can extract a unique pattern grammar from this tree.

def unique_cnode_to_grammar(tree, grammar=None):
    if grammar is None: grammar = {}
    if ddset.is_node_abstract(tree): return grammar
    name, children, *rest = tree
    tokens = []
    if name not in grammar: grammar[name] = []
    for c in children:
        n, cs, *rest = c
        tokens.append(n)
        if fuzzer.is_nonterminal(n):
            unique_cnode_to_grammar(c, grammar)
    grammar[name].append(tokens)
    return grammar, tree[0]

# We can convert this to grammar

if __name__ == '__main__':
    g,s = unique_cnode_to_grammar(unique_pattern_tree)
    print('start:', s)
    for k in g:
        print(k)
        for r in g[k]:
            print('    ', r)

# We define `pattern_grammar()` that wraps both calls.

def pattern_grammar(cnode, fname):
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    return pattern_g, pattern_s, unique_pattern_tree

# Using it.

if __name__ == '__main__':
    pattern_g,pattern_s, t = pattern_grammar(pattern, 'F1')
    print('start:', pattern_s)
    for k in pattern_g:
        print(k)
        for r in pattern_g[k]:
            print('    ', r)

# Given the reaching grammar and the pattern grammar, we can combine them to
# produce the complete grammar

def reachable_grammar(grammar, start, cnodesym, suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = reachable_key(grammar, key, cnodesym, suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key

# Since some of the keys may not have any definition left in it,

def find_empty_keys(g):
    return [k for k in g if not g[k]]

def remove_key(k, g):
    new_g = {}
    for k_ in g:
        if k_ == k:
            continue
        else:
            new_rules = []
            for rule in g[k_]:
                new_rule = []
                for t in rule:
                    if t == k:
                        # skip this rule
                        new_rule = None
                        break
                    else:
                        new_rule.append(t)
                if new_rule is not None:
                    new_rules.append(new_rule)
            new_g[k_] = new_rules
    return new_g


def copy_grammar(g):
    return {k:[[t for t in r] for r in g[k]] for k in g}

def remove_empty_keys(g):
    new_g = copy_grammar(g)
    removed_keys = []
    empty_keys = find_empty_keys(new_g)
    while empty_keys:
        for k in empty_keys:
            removed_keys.append(k)
            new_g = remove_key(k, new_g)
        empty_keys = find_empty_keys(new_g)
    return new_g, removed_keys

def grammar_gc(grammar, start):
    g, removed = remove_empty_keys(grammar)
    return g, start

# At this point we are ready to define our `atleast_one_fault_grammar()`

def atleast_one_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, t = pattern_grammar(cnode, fname)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = refine_base_key(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return grammar_gc(combined_grammar, reach_s)

# The new grammar is as follows

if __name__ == '__main__':
    cnode = pattern[1][0][1][0][1][0]
    g, s = atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, cnode, 'F1')
    print()
    print('start:', s)
    for k in g:
        print(k)
        for r in g[k]:
            print('    ', r)


# This grammar is now guaranteed to produce at least one instance of the characterizing node.

if __name__ == '__main__':
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        print(gf.iter_fuzz(key=s, max_depth=10))


# This seems to work. However, there is a wrinkle. Note that we found the characterizing node
# as this node `pattern[1][0][1][0][1][0]`, which is a factor node. But why not
# any of the other nodes? for example, why not `pattern` itself? Indeed, the effectiveness of
# our specialized grammar is dependent on finding as small a characterizing node
# as possible that fully captures the fault. So, how do we automate it?
#
# The idea is fairly simple. We start from the root of the fault inducing pattern.
# We know that this pattern fully captures the predicate. That is, any valid input
# generated from this pattern by filling in the abstract nodes is guaranteed to
# produce the failure. Next, we move to the children of this node. If the node
# is abstract, we return immediately. If however, the child is not abstract, we
# let the child be the characterizing node, and try to reproduce the failure. If
# the failure is not reproduced, we move to the next child. If the failure is
# reproduced we recurse deeper into the current child.

def find_characterizing_node(fault_tree, grammar, start, fn):
    if ddset.is_node_abstract(fault_tree): return None
    if not fuzzer.is_nonterminal(fault_tree[0]): return None
    g, s = atleast_one_fault_grammar(grammar, start, fault_tree, 'F1')
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        string = gf.iter_fuzz(key=s, max_depth=10)
        rval = fn(string)
        if rval == hdd.PRes.failed:
            return None
        elif rval == hdd.PRes.invalid:
            continue
        else:
            continue

    node, children, rest = fault_tree
    for c in children:
        v = find_characterizing_node(c, grammar, start, fn)
        if v is not None:
            return v
    return fault_tree


# Usage
if __name__ == '__main__':
    fnode = find_characterizing_node(pattern, hdd.EXPR_GRAMMAR, hdd.EXPR_START, hdd.expr_double_paren)
    ddset.display_abstract_tree(fnode)

# That is, we found the correct characterizing node.
if __name__ == '__main__':
    ddset.display_abstract_tree(cnode)

# # A grammar with no fault inducing fragments.
#
# A similar procedure can be used to make sure that no failure inducing
# fragments are present in inputs generated by given grammar. The idea is as
#follows.

# ## Unreachable Grammar
#
# We start with the `get_reachable_positions()` output. If we can ensure
# that no nonterminals in the reachable_positions can actually produce a fault
# inducing fragment, then we are done. So, given the `get_reachable_positions`
# we can produce the unreachable grammar.
# 
# For ease of discussion, we name a
# nonterminal E that is guaranteed to not produce fault tree `F` as `<E neg(F)>`.
# That is, a tree that starts from <start neg(F)> is guaranteed not to contain
# the fault tree `F`.
#
# So, the definition of `<E neg(F)` is simple enough given the characterizing
# node of the fault tree, and the corresponding reaching positions in the
# grammar.
# For each expansion rule of `<E>`, we have to make sure that it does not lead
# to `F`. So rules for `<E>` that did not have reachable positions corresponding
# to characterizing node of `F` can be directly added to `<E neg(F)>`. Next,
# for any rule that contained reachable positions, for all such positions, we
# specialize the nonterminal in that position by `neg(F)`. This gives us the
# unreachable grammar.

def negate_suffix(fault):
    assert fault
    return 'neg(%s)' % fault

def unreachable_key(grammar, key, cnodesym, negated_suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # not embeddable here. We can add this rule.
            my_rules.append(rule)
        else:
            new_rule = [refine_base_key(t, negated_suffix) if p in positions else t for p,t in enumerate(rule)]
            my_rules.append(new_rule)
    return (refine_base_key(key, negated_suffix), my_rules)

# Using it.

if __name__ == '__main__':
    for key in hdd.EXPR_GRAMMAR:
        fk, rules = unreachable_key(hdd.EXPR_GRAMMAR, key, '<factor>', negate_suffix('F1'), reaching)
        print(fk)
        for r in rules:
            print('    ', r)
        print()


# Next, we can define unreachable grammar using it.

def unreachable_grammar(grammar, start, cnodesym, negated_suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = unreachable_key(grammar, key, cnodesym, negated_suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key

# ## Negated pattern grammar.
# 
# For negated pattern grammars, there are two parts. The first part is for
# pattern rules. The idea is to make sure that we can produce any but not the
# specific pattern in the current expansion. Next, we also need to make sure
# that the original fault is not reachable from any of the nonterminals.

def negate_key(k):
    return '<%s %s>' % (stem(k), negate_suffix(refinement(k)))

def normalize(key):
    if is_base_key(key): return key
    return '<%s>' % stem(key)

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

def unmatch_a_refined_rule_in_pattern_grammar(refined_rule):
    negated_rules = []
    for pos,token in enumerate(refined_rule):
        if not fuzzer.is_nonterminal(token): continue
        if is_base_key(token): continue
        r = [negate_key(t) if i==pos else t for i,t in enumerate(refined_rule)]
        negated_rules.append(r)
    return negated_rules

def unmatch_definition_in_pattern_grammar(refined_rules, base_rules):
    # Given the set of rules, we take one rule at a time,
    # and generate the negated rule set from that.
    negated_rules_refined = []
    for ruleR in refined_rules:
        neg_rules = unmatch_a_refined_rule_in_pattern_grammar(ruleR)
        negated_rules_refined.extend(neg_rules)

    # Finally, we need to add the other non-matching rules to the pattern def.
    negated_rules_base = rule_normalized_difference(base_rules, refined_rules)

    return negated_rules_refined + negated_rules_base


def unmatch_pattern_grammar(pattern_grammar, pattern_start, base_grammar):
    negated_grammar = {}
    for l_key in pattern_grammar:
        l_rule = pattern_grammar[l_key][0]
        nl_key = negate_key(l_key)
        # find all rules that do not match, and add to negated_grammar,
        normal_l_key = normalize(l_key)
        base_rules = base_grammar[normal_l_key]
        refined_rules = pattern_grammar[l_key]

        negated_rules = unmatch_definition_in_pattern_grammar(refined_rules, base_rules)
        negated_grammar[nl_key] = negated_rules
    # this needs to be negated with original fault TODO:
    return {**negated_grammar, **pattern_grammar} , negate_key(pattern_start)

# Using

if __name__ == '__main__':
    nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_g, pattern_s, hdd.EXPR_GRAMMAR)
    # next we need to conjunct
    print('start:', nomatch_s)
    for k in nomatch_g:
        print(k)
        for r in nomatch_g[k]:
            print('    ', r)

# Now, for negated pattern grammars, not only do we need to make sure that the
# pattern is not directly matchable, but also that the pattern cannot be
# embedded. For that we simply conjunct it with `neg(F1)`

def and_suffix(k1, suffix):
    if is_base_key(k1):
        return '<%s %s>' % (stem(k1), suffix)
    return '<%s and(%s,%s)>' % (stem(k1), refinement(k1), suffix)

def and_keys(k1, k2):
    if k1 == k2: return k1
    if not refinement(k1): return k2
    if not refinement(k2): return k1
    return '<%s and(%s,%s)>' % (stem(k1), refinement(k1), refinement(k2))


def negated_pattern_grammar(pattern_grammar, pattern_start, base_grammar, nfault_suffix):
    reachable_keys = reachable_dict(base_grammar)
    nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_grammar, pattern_start, base_grammar)

    new_grammar = {}

    my_key = normalize(pattern_start)
    # which keys can reach pattern_start?
    keys_that_can_reach_fault = [k for k in reachable_keys if my_key in reachable_keys[k]]
    #for k in keys_that_can_reach_fault: assert my_key in reachable_keys[k]
    new_g = {}
    for k in nomatch_g: 
        new_rules = []
        for rule in nomatch_g[k]:
            new_rule = [and_suffix(t, nfault_suffix) if t in keys_that_can_reach_fault else t for t in rule]
            new_rules.append(new_rule)
        new_g[k] = new_rules
    return new_g, negate_key(pattern_start)

# Using

if __name__ == '__main__':
    print()
    nomatch_g, nomatch_s = negated_pattern_grammar(pattern_g, pattern_s, hdd.EXPR_GRAMMAR, 'neg(F1)')
    # next we need to conjunct
    print('start:', nomatch_s)
    for k in nomatch_g:
        print(k)
        for r in nomatch_g[k]:
            print('    ', r)


def tokens(g):
    ts = []
    for k in g:
        for r in g[k]:
            for t in r:
                if fuzzer.is_nonterminal(t): ts.append(t)
    return ts
# At this point, we can now define our 1negated_grammar()`
# The new grammar is as follows

def no_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, tr = pattern_grammar(cnode, fname)
    negated_suffix = negate_suffix(fname)
    nomatch_g, nomatch_s = negated_pattern_grammar(pattern_g, pattern_s, grammar, negated_suffix)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)
    unreach_g, unreach_s = unreachable_grammar(grammar, start_symbol, key_f, negated_suffix, reachable_keys)

    combined_grammar = {**grammar, **nomatch_g, **reach_g, **unreach_g}
    unreaching_sym = refine_base_key(key_f, negated_suffix)
    combined_grammar[unreaching_sym] = unreach_g[unreaching_sym] + nomatch_g[nomatch_s] # TODO verify

    return grammar_gc(combined_grammar, unreach_s)

# Using it.

if __name__ == '__main__':
    cnode = pattern[1][0][1][0][1][0]
    g, s = no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, cnode, 'F1')
    print()
    print('start:', s)
    for k in g:
        print(k)
        for r in g[k]:
            print('    ', r)


# This grammar is now guaranteed not to produce any instance of the characterizing node.

import sympy

class LitB:
    def __init__(self, a): self.a = a
    def __str__(self): return self.a

TrueB = LitB('')
FalseB = LitB('_|_')

class OrB:
    def __init__(self, a): self.l = a
    def __str__(self): return 'or(%s)' % ','.join(sorted([str(s) for s in self.l]))
class AndB:
    def __init__(self, a): self.l = a
    def __str__(self): return 'and(%s)' % ','.join(sorted([str(s) for s in self.l]))
class NegB:
    def __init__(self, a): self.a = a
    def __str__(self): return 'neg(%s)' % str(self.a)
class B:
    def __init__(self, a): self.a = a
    def __str__(self): return str(self.a)


import string
BEXPR_GRAMMAR = {
    '<start>': [['<bexpr>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexpr>', ',', '<bexpr>', ')'],
        ['<bop>',  '(', '<bexpr>', ',', '<bexpr>', ')'],
        ['<bop>', '(', '<bexpr>', ')'],
        ['<fault>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<fault>': [['<letters>'], []],
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']],
    '<letter>': [[i] for i in (string.ascii_lowercase + string.ascii_uppercase + string.digits) + '_+*.-']
}
BEXPR_START = '<start>'

class BExpr:
    def __init__(self, s):
        if s is not None:
            self._s = s
            self._tree = self._parse(s)
            self._simple, self._sympy = self._simplify()
        else: # create
            self._s = None
            self._tree = None
            self._simple = None
            self._sympy = None

    def simple(self):
        if self._simple is None:
            self._simple = str(self._convert_sympy_to_bexpr(self._sympy))
        return self._simple

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR, canonical=True)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][0]
        return bexpr

    def with_key(self, k):
        s = self.simple()
        if s: return '<%s %s>' % (stem(k), s)
        return normalize(k)

    def _simplify(self):
        e0, defs = self._convert_to_sympy(self._tree)
        e1 = sympy.to_dnf(e0)
        e2 = self._convert_sympy_to_bexpr(e1)
        v = str(e2)
        my_keys = [k for k in defs]
        for k in my_keys:
            del defs[k]
        return v, e1

    def is_neg_sym(self):
        op = self.get_operator()
        if op != 'neg': return False
        if not isinstance(self._sympy.args[0], sympy.Symbol): return False
        return True

    def get_operator(self):
        if isinstance(self._sympy, sympy.And): return 'and'
        elif isinstance(self._sympy, sympy.Or): return 'or'
        elif isinstance(self._sympy, sympy.Not): return 'neg'
        else: return ''

    def op_fst(self):
        op = self.get_operator()
        assert op == 'neg'
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]
        return bexpr

    def op_fst_snd(self):
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]

        bexpr_rest = BExpr(None)
        op = self.get_operator()

        if op == 'and':
            bexpr_rest._sympy = sympy.And(*self._sympy.args[1:])
        elif op == 'or':
            bexpr_rest._sympy = sympy.Or(*self._sympy.args[1:])
        else:
            assert False
        return bexpr, bexpr_rest

    def negate(self):
        bexpr = BExpr(None)
        bexpr._sympy = sympy.Not(self._sympy).simplify()
        return bexpr

    def _flatten(self, bexprs):
        assert bexprs[0] == '<bexprs>'
        if len(bexprs[1]) == 1:
            return [bexprs[1][0]]
        else:
            assert len(bexprs[1]) == 3
            a = bexprs[1][0]
            comma = bexprs[1][1]
            rest = bexprs[1][2]
            return [a] + self._flatten(rest)

    def _convert_to_sympy(self, bexpr_tree, symargs=None):
        def get_op(node):
            assert node[0] == '<bop>', node[0]
            return ''.join([i[0] for i in node[1]])
        if symargs is None:
            symargs = {}
        name, children = bexpr_tree
        assert name == '<bexpr>', name
        if len(children) == 1: # fault node
            name = fuzzer.tree_to_string(children[0])
            if not name: return None, symargs
            if name not in symargs:
                symargs[name] = sympy.symbols(name)
            return symargs[name], symargs
        else:
            operator = get_op(children[0])
            if operator == 'and':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.And(*[a for a,_ in sp]), symargs

            elif operator == 'or':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.Or(*[a for a,_ in sp]), symargs

            elif operator == 'neg':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                assert len(res) == 1
                a,_ = self._convert_to_sympy(res[0], symargs)
                return sympy.Not(a), symargs
            else:
                assert False

    def _convert_sympy_to_bexpr(self, sexpr, log=False):
        if isinstance(sexpr, sympy.Symbol):
            return B(str(sexpr))
        elif isinstance(sexpr, sympy.Not):
            return NegB(self._convert_sympy_to_bexpr(sexpr.args[0]))
        elif isinstance(sexpr, sympy.And):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return FalseB # F & ~F == _|_
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return FalseB # F & ~F == _|_
            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if FalseB in sym_vars: return FalseB # if bottom is present in and, that is the result
            if TrueB in sym_vars:
                sym_vars = [s for s in sym_vars if s != TrueB] # base def does not do anything in and.
                if not sym_vars: return TrueB
            return AndB(sym_vars)
        elif isinstance(sexpr, sympy.Or):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(b)
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(a)

            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if TrueB in sym_vars: return TrueB # if original def is present in or, that is the result
            if FalseB in sym_vars:
                sym_vars = [s for s in sym_vars if s != FalseB]
                if not sym_vars: return FalseB
            return OrB(sym_vars)
        else:
            if log: print(repr(sexpr))
            assert False

def disj(k1, k2, simplify=False):
    assert is_nt(k1)
    if k1 == k2: return k1
    if not refinement(k1): return k1
    if not refinement(k2): return k2
    b = BExpr('or(%s,%s)' % (refinement(k1), refinement(k2)))
    return b.with_key(k1)

def conj(k1, k2, simplify=False):
    assert is_nt(k1)
    if k1 == k2: return k1
    if not refinement(k1): return k2
    if not refinement(k2): return k1
    b = BExpr('and(%s,%s)' % (refinement(k1), refinement(k2)))
    return b.with_key(k1)

def find_all_nonterminals(g):
    lst = []
    for k in g:
        for r in g[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    lst.append(t)
    return list(sorted(set(lst)))

def undefined_keys(grammar):
    keys = find_all_nonterminals(grammar)
    return [k for k in keys if k not in grammar]

def reconstruct_neg_bexpr(grammar, key, bexpr):
    fst = bexpr.op_fst()
    base_grammar, base_start = normalize_grammar(grammar), normalize(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    g1, saved_keys, undef_keys  = remove_unused(g1_, s1)
    g, s, r = negate_grammar_(g1, s1, base_grammar, base_start)
    assert s in g, s
    g = {**grammar, **g1, **g, **saved_keys}
    return g, s, undefined_keys(g)

def reconstruct_and_bexpr(grammar, key, bexpr):
    fst, snd = bexpr.op_fst_snd()
    f_key = bexpr.with_key(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    if fst == snd: # or of same keys is same
        print(f_key)
        g = {**grammar, **g1_}
        g[f_key] = g[s1]
        return g, f_key, undefined_keys(g)
    g1, saved_keys1, undef_keys1  = remove_unused(g1_, s1)
    g2_, s2, r2 = reconstruct_rules_from_bexpr(key, snd, grammar)
    g2, saved_keys2, undef_keys2  = remove_unused(g2_, s2)
    g, s, r = and_grammars_(g1, s1, g2, s2)
    assert s in g
    g = {**grammar, **g1, **g2, **g, **saved_keys1, **saved_keys2}
    assert f_key in g, f_key
    return g, s, undefined_keys(g)

def reconstruct_or_bexpr(grammar, key, bexpr):
    fst, snd = bexpr.op_fst_snd()
    f_key = bexpr.with_key(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    assert fst.with_key(key) in g1_
    if fst == snd: # and of same keys is same
        g = {**grammar, **g1_}
        g[f_key] = g[s1]
        return g, f_key, undefined_keys(g)
    g1, saved_keys1, undef_keys1  = remove_unused(g1_, s1)
    g2_, s2, r2 = reconstruct_rules_from_bexpr(key, snd, grammar)
    assert snd.with_key(key) in g2_
    g2, saved_keys2, undef_keys2  = remove_unused(g2_, s2)
    g, s, r = or_grammars_(g1, s1, g2, s2)
    assert s in g
    g = {**grammar, **g1, **g2, **g, **saved_keys1, **saved_keys2}
    assert f_key in g, (f_key, s)
    return g, s, undefined_keys(g)


def reconstruct_rules_from_bexpr(key, bexpr, grammar):
    f_key = bexpr.with_key(key)
    if f_key in grammar:
        return grammar, f_key, []
    else:
        new_grammar = grammar
        operator = bexpr.get_operator()
        if operator == 'and':
            return reconstruct_and_bexpr(grammar, key, bexpr)
        elif operator == 'or':
            return reconstruct_or_bexpr(grammar, key, bexpr)
        elif operator == 'neg':
            return reconstruct_neg_bexpr(grammar, key, bexpr)
        elif operator == '':
            # probably we have a negation
            assert False
            #return reconstruct_neg_fault(grammar, key, bexpr)
        else:
            assert False

def reconstruct_key(refined_key, grammar, log=False):
    keys = [refined_key]
    defined = set()
    while keys:
        if log: print(len(keys))
        key_to_reconstruct, *keys = keys
        if log: print('reconstructing:', key_to_reconstruct)
        if key_to_reconstruct in defined:
            raise Exception('Key found:', key_to_reconstruct)
        defined.add(key_to_reconstruct)
        bexpr = BExpr(refinement(key_to_reconstruct))
        nrek = normalize(key_to_reconstruct)
        if bexpr.simple():
            nkey = bexpr.with_key(key_to_reconstruct)
            if log: print('simplified_to:', nkey)
            grammar, s, refs = reconstruct_rules_from_bexpr(nrek, bexpr, grammar)
        else:
            nkey = nrek # base key
        assert nkey in grammar
        grammar[key_to_reconstruct] = grammar[nkey]
        keys = undefined_keys(grammar)
    return grammar


def find_reachable_keys_unchecked(grammar, key, reachable_keys=None, found_so_far=None):
    if reachable_keys is None: reachable_keys = {}
    if found_so_far is None: found_so_far = set()

    for rule in grammar.get(key, []):
        for token in rule:
            if not fuzzer.is_nonterminal(token): continue
            if token in found_so_far: continue
            found_so_far.add(token)
            if token in reachable_keys:
                for k in reachable_keys[token]:
                    found_so_far.add(k)
            else:
                keys = find_reachable_keys_unchecked(grammar, token, reachable_keys, found_so_far)
                # reachable_keys[token] = keys <- found_so_far contains results from earlier
    return found_so_far

def reachable_dict_unchecked(grammar):
    reachable = {}
    for key in grammar:
        keys = find_reachable_keys_unchecked(grammar, key, reachable)
        reachable[key] = keys
    return reachable

def complete(grammar, start, log=False):
    keys = undefined_keys(grammar)
    reachable_keys = reachable_dict_unchecked(grammar)
    for key in keys:
        if key not in reachable_keys[start]: continue
        grammar = reconstruct_key(key, grammar, log)
    grammar_, start_ = grammar_gc(grammar, start)
    return grammar_, start_

# Usage

if __name__ == '__main__':
    g_, s_ = complete(g, s)
    gf = fuzzer.LimitFuzzer(g_)
    for i in range(10):
        print(gf.iter_fuzz(key=s_, max_depth=10))


# # And

import itertools as I

def conjoin_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = []
        for t1,t2 in zip(ruleA, ruleB):
            if not is_nt(t1):
                AandB_rule.append(t1)
            elif is_base_key(t1) and is_base_key(t2):
                AandB_rule.append(t1)
            else:
                k = and_keys(t1, t2, simplify=True)
                AandB_rule.append(k)
        rules.append(AandB_rule)
    return rules

def and_rules(rulesA, rulesB):
    AandB_rules = []
    # key is the rule pattern
    rulesetsA = get_rulesets(rulesA)
    rulesetsB = get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) & set(rulesetsB.keys())
    for k in keys:
        new_rules = conjoin_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules

def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    # now get the matching keys for each pair.
    for k1,k2 in I.product(g1_keys, g2_keys):
        # define and(k1, k2)
        if normalize(k1) != normalize(k2): continue
        # find matching rules
        and_key = and_keys(k1, k2)
        g[and_key] = and_rules(g1[k1], g2[k2])
    return g, and_keys(s1, s2)

