# ---
# published: true
# title: Simple DDSet
# layout: post
# comments: true
# tags: deltadebug, ddset, testcase reducer, cfg, generator
# categories: post
# ---

# We previously [discussed](/post/2020/07/15/ddset/) how
# DDSET [^gopinath2020abstracting] is implemented. However, DDSET is a fairly
# complex algorithm, and tries to handle diverse cases that may arise in the
# real world such as difference between syntactic and semantic validity,
# impact of tokens, variables etc.  This complexity is however, not innate. One
# can produce a much more simple version of DDSET if one is only interested in
# abstracting inputs, and one has a predicate that does not have a semantic
# validation phase. The algorithm is as follows:

# (We use a number of library functions from that post). Unlike previous posts,
# this post uses a top down approach since we have already
# defined a number of functions [previously](/post/2020/07/15/ddset/).

# First we load the prerequisite earley parser.

#@
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/simplefuzer-0.0.1-py2.py3-none-any.whl

# The imported modules

import earleyparser
import hdd
import simplefuzzer as fuzzer

# We first define our input, and make sure that our predicate works
 
if __name__ == '__main__':
    my_input = '1+((2*3/4))'
    assert hdd.expr_double_paren(my_input) == hdd.PRes.success

# Next, let us make sure that it parses correctly.

if __name__ == '__main__':
    expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
    parsed_expr = list(expr_parser.parse_on(my_input, '<start>'))[0]
    fuzzer.display_tree(parsed_expr)

# Next, we use the *perses* reducer to produce a reduced derivation tree.

if __name__ == '__main__':
    reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
    fuzzer.display_tree(reduced_expr_tree)

 
# Now we are ready to call our generalizer, which takes the expression tree, the grammar, and the predicate, and returns the generalized pattern.
# ```python
# pattern = ddset_simple(reduced_expr, EXPR_GRAMMAR, expr_double_paren)
# print(pattern)
# ```

# The `ddset_simple()` is implemented as follows:

def ddset_simple(reduced_tree, grammar, predicate):
  vals = generalize(reduced_tree, [], [], grammar, predicate)
  ta = get_abstract_tree(reduced_tree, vals)
  return abstract_tree_to_str(ta)

# If we do only want the abstract tree, we have another function `ddset_abstract()`

def ddset_abstract(reduced_tree, grammar, predicate):
  vals = generalize(reduced_tree, [], [], grammar, predicate)
  ta = get_abstract_tree(reduced_tree, vals)
  return ta

# The `generalize()` procedure tries to generalize a given tree recursively. For that, it starts at the root node, and replaces the node with
# a randomly generated tree rooted at the same node. It tries that a configurable number of times, and if the tree can be replaced each time
# without failure, then we mark the path as abstract. If not, we descent into its children and try the same. While generating a new tree, any
# previous nodes marked as abstract is also replaced by randomly generated values.

def generalize(tree, path, known_paths, grammar, predicate):
    node = hdd.get_child(tree, path)
    if not fuzzer.is_nonterminal(node[0]): return known_paths
    if can_abstract(tree, path, known_paths, grammar, predicate):
        known_paths.append(path)
        return known_paths
    for i,child in enumerate(node[1]):
        ps = generalize(tree, path + [i], known_paths, grammar, predicate)
    return known_paths

# The `can_abstract()` procedure above does the checking to see if the tree can be abstracted. It is implemented as follows.

MAX_TRIES_FOR_ABSTRACTION = 100

def can_abstract(tree, path, known_paths, grammar, predicate):
    i = 0
    while (i < MAX_TRIES_FOR_ABSTRACTION):
        t = replace_all_paths_with_generated_values(tree, known_paths + [path], grammar)
        s = fuzzer.iter_tree_to_str(t)
        if predicate(s) == hdd.PRes.failed:
            return False
        elif predicate(s) == hdd.PRes.invalid:
            continue
        i += 1
    return True

# The `can_abstract()` procedure tries to generate a valid value `MAX_TRIES_FOR_ABSTRACTION` times. For this, it relies on
# `replace_all_paths_with_generated_values()` which is implemented as follows.

def replace_all_paths_with_generated_values(tree, paths, grammar):
    my_tree = tree
    for p in paths:
        my_tree = replace_path_with_generated_value(my_tree, p, grammar)
    return my_tree

# Here, the major work is done by `replace_path_with_generated_value()` which replaces a single given path with a generated node
# of the same kind.

import copy
def replace_path(tree, path, new_node=None):
    if new_node is None: new_node = []
    if not path: return copy.deepcopy(new_node)
    cur, *path = path
    name, children, *rest = tree
    new_children = []
    for i,c in enumerate(children):
        if i == cur:
            nc = replace_path(c, path, new_node)
        else:
            nc = c
        if nc:
            new_children.append(nc)
    return (name, new_children, *rest)

def replace_path_with_generated_value(tree, path, grammar):
    node = hdd.get_child(tree, path)
    s, gnode = generate_random_value(grammar, node[0])
    t = replace_path(tree, path, gnode)
    return t

# Given a key, generate a random value for that key using the grammar. 

def generate_random_value(grammar, key):
    my_fuzzer = fuzzer.LimitFuzzer(grammar)
    s = my_fuzzer.iter_fuzz(key)
    return (s, my_fuzzer._s)

# Finally, the converter from an abstract tree to a string expression

def abstract_tree_to_str(tree):
    name, children, *general_ = tree
    if not fuzzer.is_nonterminal(name): return name
    if is_node_abstract(tree):
        return name
    return ''.join([abstract_tree_to_str(c) for c in children])

# We also need a few library functions for marking some nodes concrete and some abstract.

def mark_concrete_r(tree):
    name, children, *abstract_a = tree
    abstract = {'abstract': False} if not abstract_a else abstract_a[0]
    return (name, [mark_concrete_r(c) for c in children], abstract)

def mark_path_abstract(tree, path):
    name, children = hdd.get_child(tree, path)
    new_tree = replace_path(tree, path, (name, children, {'abstract': True}))
    return new_tree

def get_abstract_tree(tree, paths):
    for path in paths:
        tree = mark_path_abstract(tree, path)
    return mark_concrete_r(tree)

def is_node_abstract(node):
    name, children, *abstract_a = node
    if not abstract_a:
        return True
    else:
        return abstract_a[0]['abstract']

# With this, we are ready to extract our pattern.

def get_children(node):
    if is_node_abstract(node): return []
    return fuzzer.get_children(node)

def display_abstract_tree(node, format_node=fuzzer.format_node):
    fuzzer.display_tree(node, get_children=get_children, format_node=format_node)

# The tree
if __name__ == '__main__':
    pattern = ddset_abstract(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
    display_abstract_tree(pattern)

# The pattern
if __name__ == '__main__':
    pattern = ddset_simple(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
    print(pattern)
 
# So, given that this algorithm is much simpler than the original, why should we use the
# original algorithm? The problem is that when the input is a file in a programming language,
# one also needs to take into account the semantics. That is, the generated input needs to be
# valid both syntactically (by construction) as well as semantically. It is hard enough trying
# to fill one hole in the parse tree (abstract node) with a semantically valid subtree. Now,
# imagine that you have identified one abstraction and are evaluating a second node. You need to
# generate random nodes both for previously identified abstract node, as well as the node you are
# currently evaluating. Say you have identified three abstract nodes, for any node that will be
# evaluated next, you need to fill in three abstract nodes with randomly generated semantically
# valid values. This is exponential, and infeasible to continue as more nodes are added. Hence,
# in original DDSet, we try to independantly evaluate each single node, and once we have collected
# most of these nodes, we go for a second pass to verify.
# 
# How much difference does it make? For [Rhino bug 385](https://github.com/mozilla/rhino/issues/385)
# abstracting the minimal string `var {baz: baz => {}} = baz => {};` took 15643 executions for
# `ddsetsimple` when compared to 10340 executions for the ddset from the paper (discounting covarying
# fragments).
# 
# The full code is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2020-08-03-simple-ddset.py)
# 
# [^gopinath2020abstracting]: Rahul Gopinath, Alexander Kampmann, Nikolas Havrikov, Ezekiel Soremekun, Andreas Zeller, "Abstracting Failure Inducing Inputs" ISSTA 2020 URL:<https://rahul.gopinath.org/publications/#gopinath2020abstracting>
