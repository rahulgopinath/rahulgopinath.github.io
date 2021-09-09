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

# The pattern grammar

def pattern_grammar(cnode, fname):
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    return pattern_g, pattern_s

# Using it.
if __name__ == '__main__':
    pattern_g,pattern_s = pattern_grammar(pattern, 'F1')
    print('start:', pattern_s)
    for k in pattern_g:
        print(k)
        for r in pattern_g[k]:
            print('    ', r)

# Given the reaching grammar, and the pattern grammar, we can combine them to
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

def grammar_gc(grammar):
    g = {}
    for k in grammar:
        if grammar[k]:
            g[k] = grammar[k]
    return g

def atleast_one_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s = pattern_grammar(cnode, fname)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = refine_base_key(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return grammar_gc(combined_grammar), reach_s

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
    return negated_grammar, negate_key(pattern_start)

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


def negated_pattern_grammar(pattern_grammar, pattern_start, fault_key, base_grammar):
    reachable_keys = reachable_dict(base_grammar)
    nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_g, pattern_s, base_grammar)
    new_grammar = {}
    keys_that_can_reach_fault = reachable_keys[normalize(fault_key)]
    new_g = {}
    nk = negate_suffix(refinement(fault_key))
    for k in nomatch_g: 
        new_rules = []
        for rule in nomatch_g[k]:
            new_rule = [and_suffix(t, nk) if t in keys_that_can_reach_fault else t for t in rule]
            new_rules.append(new_rule)
        new_g[k] = new_rules
    return new_g, negate_key(pattern_start)

# Using

if __name__ == '__main__':
    print()
    nomatch_g, nomatch_s = negated_pattern_grammar(pattern_g, pattern_s, '<factor F1>', hdd.EXPR_GRAMMAR)
    # next we need to conjunct
    print('start:', nomatch_s)
    for k in nomatch_g:
        print(k)
        for r in nomatch_g[k]:
            print('    ', r)


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

