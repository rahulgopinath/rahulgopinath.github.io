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
# 
# However, such inputs are insufficient from a testing perspective. For example,
# such a pattern fails to capture the contexts in which the doubled parenthesis
# can appear, and hence induce the failure. That is, how do we use the
# pattern `((<expr>))` to produce inputs such as `'1+((2*3/4))'`? This is what
# this post will discuss.
# 
# Note that the guarantee of inducing failures is statistical. That is, the
# abstract input is mined by evaluating produced
# inputs for failure a fixed (configurable) number of times. It is possible that
# some rare inputs may still fail to induce the failure. Since abstract possibly
# failure inducing inputs is a mouthful, let us call these abstract failure
# inducing inputs **evocative patterns** for short. In this post, we will see
# how to transform such an **evocative pattern** to an **evocative grammar** that is
# guaranteed to produce *evocative inputs* in all contexts that are guaranteed
# (statistically) to induce failures.
# 
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

# # A grammar that produces at least one evocative fragment per input generated.

# The basic idea is that if we can find a `characterizing node` of the
# abstract fault tree, such that the presence of the abstract subtree
# in the input guarantees the failure, then we can modify the grammar such
# that this abstract subtree is always present. That is, for any input
# from such a grammar, at least one instance of the evocative 
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
# can actually embed such a node.

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
# Next, we need to ensure that our characterizing node can form a unique subtree.
# For that, all we need to do is that all nodes are named uniquely.
# Not all nodes in the characterizing node needs unique names however. DDSet
# produces trees such that some nodes in the tree are left abstract. We leave
# these with the original node names.

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

# We can convert this to grammar, but first, to display the grammar properly, we
# define `display_grammar()`

def display_rule(rule, pre, verbose):
    if verbose > -1:
        v = (' '.join([t if fuzzer.is_nonterminal(t) else repr(t) for t in rule]))
        s = '%s|   %s' % (pre, v)
        print(s)

def display_definition(grammar, key, r, verbose):
    if verbose > -1: print(key,'::=')
    for rule in grammar[key]:
        r += 1
        if verbose > 1:
            pre = r
        else:
            pre = ''
        display_rule(rule, pre, verbose)
    return r

def display_grammar(grammar, start, verbose=0):
    r = 0
    k = 0
    print('start:', start)
    for key in grammar:
        k += 1
        r = display_definition(grammar, key, r, verbose)
        if verbose > 0:
            print(k, r)
    print(k, r)

if __name__ == '__main__':
    g,s = unique_cnode_to_grammar(unique_pattern_tree)
    display_grammar(g,s)

# We define `pattern_grammar()` that wraps both calls.

def pattern_grammar(cnode, fname):
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    return pattern_g, pattern_s, unique_pattern_tree

# Using it.

if __name__ == '__main__':
    pattern_g,pattern_s, t = pattern_grammar(pattern, 'F1')
    display_grammar(pattern_g, pattern_s)

# We define a procedure to reverse our pattern grammar to ensure we can
# get back our tree.


def pattern_grammar_to_tree(g, s):
    rules = g[s]
    assert len(rules) == 1
    return (s, [pattern_grammar_to_tree(g,t) if t in g else (t, []) for t in rules[0]])

# The tree can be recovered thus.

if __name__ == '__main__':
    c_tree = pattern_grammar_to_tree(pattern_g,pattern_s)
    fuzzer.display_tree(c_tree)

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

# Using it

if __name__ == '__main__':
    characterizing_node = pattern[1][0][1][0][1][0]
    my_key_f = characterizing_node[0]
    reaching = reachable_dict(hdd.EXPR_GRAMMAR)
    reach_g, reach_s = reachable_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, my_key_f, 'F1', reaching)
    display_grammar(reach_g, reach_s)

# Here, you will notice a problem:
#
# There are a few nonterminals such as `<integer F1>` that do not have a
# definition. That is, it has no expansion (not even empty expansion). So,
# any rule that uses it will also by definition have no possible expansions.
# This has consequences during generation, forcing us to abandon partially
# constructed trees. Hence, we define a `grammar_gc()`

# ## Cleanup of the grammar
#
# Let us make sure that we are operating on a copy of the grammar.

def copy_grammar(g):
    return {k:[[t for t in r] for r in g[k]] for k in g}

# Next, we find the empty keys in the grammar that do not have a definition.

def find_empty_keys(g):
    return [k for k in g if not g[k]]

# Now, we need to remove such empty definitions, which also means any rules that
# refer to the corresponding nonterminals also have to be removed. The
# `remove_nonterminal` function takes a nonterminal, and removes its references
# from the given grammar.

def remove_nonterminal(nt, g):
    new_g = {}
    for k_ in g:
        if k_ == nt: continue
        new_rules = []
        for rule in g[k_]:
            if any(t == nt for t in rule): continue
            new_rules.append(rule)
        new_g[k_] = new_rules
    return new_g

# When removing a rule, it can also happen that the corresponding nonterminal
# may be left with no further rules. Hence, we need to
# define finding and removing empty nonterminals from the grammar recursively.

def remove_empty_nonterminals(g):
    new_g = copy_grammar(g)
    removed_keys = []
    empty_keys = find_empty_keys(new_g)
    while empty_keys:
        for k in empty_keys:
            removed_keys.append(k)
            new_g = remove_nonterminal(k, new_g)
        empty_keys = find_empty_keys(new_g)
    return new_g, removed_keys

# These gives us the `grammar_gc()`

def grammar_gc(g):
    grammar, start = g
    new_grammar, removed = remove_empty_nonterminals(grammar)
    return new_grammar, start

# At this point we are ready to define our `atleast_one_fault_grammar()`

def atleast_one_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, t = pattern_grammar(cnode, fname)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = refine_base_key(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return combined_grammar, reach_s

# The new grammar is as follows

if __name__ == '__main__':
    g, s = grammar_gc(atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, characterizing_node, 'F1'))
    display_grammar(g, s)

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
# The idea is fairly simple. We start from the root of the evocative pattern.
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
    g, s = grammar_gc(atleast_one_fault_grammar(grammar, start, fault_tree, 'F1'))
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
    ddset.display_abstract_tree(characterizing_node)

# At this point, we have the ability to guarantee that a evocative 
# fragment is present in any inputs produced. In later posts I will discuss how
# combine multiple such fragments together using `and`, `or` or `negation`. I
# will also discuss how to ensure `at most` one fragment in the input and
# `exactly` one fragment or `exactly n` fragments.
#
# As before, the runnable source of this notebook can be found [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-09-fault-inducing-grammar.py)
