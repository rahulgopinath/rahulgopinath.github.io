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
    parsed_expr = list(expr_parser.parse_on(my_input, '<start>'))[0]

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
# a grammar is called the `reaching_grammar`.

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

def reach_suffix(nt, suffix):
    return '<%s %s>' % (nt[1:-1], suffix)

def insert_atleast_one_cnode_into_key(grammar, key, cnodesym, suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = get_reachable_positions(rule, cnodesym, reachable)
        if not positions: # make it len(positions) >= n if necessary
            # skip this rule because we can not embed the fault here.
            continue
        else:
            # at each position, insert the cnodesym
            for pos in positions:
                new_rule = [reach_suffix(t, suffix)
                            if pos == p else t for p,t in enumerate(rule)]
                my_rules.append(new_rule)
    return (reach_suffix(key, suffix), my_rules)


if __name__ == '__main__':
    for key in hdd.EXPR_GRAMMAR:
        fk, rules = insert_atleast_one_cnode_into_key(hdd.EXPR_GRAMMAR, key, '<factor>', 'F1', reaching)
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

# Given the reaching grammar, and the pattern grammar, we can combine them to
# produce the complete grammar

def insert_atleast_one_cnode_into_grammar(grammar, start, cnodesym, suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = insert_atleast_one_cnode_into_key(grammar, key, cnodesym, suffix, reachable)
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
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = insert_atleast_one_cnode_into_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = reach_suffix(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return grammar_gc(combined_grammar), reach_s

# The new grammar is as follows

if __name__ == '__main__':
    cnode = pattern[1][0][1][0][1][0]
    g, s = atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, '<start>', cnode, 'F1')
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
