# ---
# published: true
# title: Hierarchical Delta Debugging
# layout: post
# comments: true
# tags: reducing
# categories: post
# ---

# Previously, we [discussed](/post/2019/12/03/ddmin/) how Delta-debug (_ddmin_)
# worked. However, pure _ddmin_ is limited when it comes to structured inputs.
# One of the problems with the unstructured version of `ddmin()` above is that
# it assumes that parts of the inputs can be cut away, while still retaining
# validity in that it will actually reach the testing function. This, however,
# may not be a reasonable assumption especially in the case of structured
# inputs. The problem is that if you have a JSON `[{"a": null}]` that produces
# an error because the key value is `null`, `ddmin()` will try to partition it
# as `[{"a":` followed by `null}]` neither of which are valid. Further, any
# chunk removed from either parts are also likely to be invalid. Hence,
# `ddmin()` will not be able to proceed.
#
# The solution here is to go for a variant called *Hierarchical Delta Debugging*
# [^misherghi2006hdd].
# The basic idea is to first extract the parse tree (either by parsing the input
# using a grammar, or by either relying on a generator to generate the parse
# tree along with the input, or by extracting the parse tree in-flight from the
# target program if it supports it), and then try and apply `ddmin()` on each
# level of the derivation tree. Another notable improvement was invented by
# Herfert et al. [^herfert2017automatically].
# In this paper, the authors describe a simple strategy: Try and replace a given
# node by one of its child nodes. This works reasonably well for inputs that are
# context sensitive such as programs that can trigger bugs in compilers.
# A final algorithm is Perses[^sun2018perses] which uses the program grammar
# directly to avoid creating invalid nodes. In this post, I will explain the
# main algorithm of *Perses*. I note that a similar idea was explored by Pike in
# 2014[^pike2014smartcheck] albeit for data structures.
# 
# The basic idea of Perses is to try and replace a parent node by either an
# empty expansion (so that the corresponding string fragment can be deleted)
# or by a child node of the same nonterminal. To accomplish the first (that is,
# to be able to use empty expansions), Perses first transofrms the given grammar
# to a *Perses normal form*. We can however skip that portion if we are careful
# and use a grammar where we explicitly use nonterminals that can have an empty
# exansion. In this post, I only explain the *perses reduction* algorithm.
#

# First, some book keeping

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

# We need a parser

parser = import_file('parser', '2018-09-06-peg-parsing.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')

# ## Predicate
# For the delta debug algorithm to work, we need a predicate. However, unlike
# *ddmin* which works with simple pass or fail status, we need a bit more
# sophistication here. The reason is that in many cases, the newly constructed
# strings we generate may also be *invalid*. For example, a particular program
# may produce a core dump from the C compiler. Hence, the core dump is the
# `pass` for the predicate. On the other hand, deleting the declaration of a
# variable may result in a compilation error. This is different from a simple
# `fail` which is no coredump on a semantically valid program. To capture these
# different conditions, we define new return values for the predicate.
#
# There can be four outcomes when an input is executed:
# * Success (failure condition reproduced)
# * Failed (failure condition not reproduced)
# * Invalid (Did not reach failure condition  possibly semantically invalid)
# * Timeout (equivalant to Failed)

from enum import Enum
import copy

class PRes(str, Enum):
    success = 'SUCCESS'
    failed = 'FAILED'
    invalid = 'INVALID'
    timeout = 'TIMEOUT'

# We now define our predicate

import re

def expr_double_paren(inp):
    if re.match(r'.*[(][(].*[)][)].*', inp):
        return PRes.success
    return PRes.failed

# Checking

if __name__ == '__main__':
    print(expr_double_paren('((1))'))
    print(expr_double_paren('(1)'))

# We now define a grammar
EXPR_GRAMMAR = {
 '<start>': [['<expr>']],
 '<expr>': [['<term>', '+', '<expr>'],
            ['<term>', '-', '<expr>'],
            ['<term>']],
 '<term>': [['<factor>', '*', '<term>'],
            ['<factor>', '/', '<term>'],
            ['<factor>']],
 '<factor>': [['+', '<factor>'],
              ['-', '<factor>'],
              ['(', '<expr>', ')'],
              ['<integer>', '.', '<integer>'],
              ['<integer>']],
 '<integer>': [['<digit>', '<integer>'], ['<digit>']],
 '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']]}

# define a display_tree function

def display_tree(tree):
    print(fuzzer.iter_tree_to_str(tree))

# Now, let us define an input, and parse it

if __name__ == '__main__':
    my_input = '1+((2*3/4))'
    expr_parser = parser.peg_parse(EXPR_GRAMMAR)
    tfrom, parsed_expr = expr_parser.unify_key('<start>', my_input, 0)
    print(parsed_expr)
    display_tree(parsed_expr)

# The perses algorithm is as follows: We start the root, and recursively go down
# the child nodes. For each node, we check if that node can be replaced by a
# subtree with the same nonterminal, and still reproduce the failure, and find
# the smallest such tree (length determined by number of leaves).
# 
# Since this procedure can result in multiple trees, the tree to work on is
# chosen based on a priority queue where the priority is given to the smallest
# tree.

# The particular node chosen to replace the current node is determined based
# first on its numer of leaf nodes, and then on its rank in a priority queue,
# where the priority is determined by the depth of the subtree from the current
# node. That is, a child gets priority over a grand child.
# We first have to define a way to address a specific node.

if __name__ == '__main__':
    t = parsed_expr[1][0][1][2][1][0]
    print(t)
    display_tree(t)

# For the path, we simply use a list of numbers indicating the child node. For example, in the above, the path would be [0, 2, 0]
# Given a path, get_child() will simply return the node at the path.

def get_child(tree, path):
    if not path: return tree
    cur, *path = path
    return get_child(tree[1][cur], path)

# Using it.
if __name__ == '__main__':
    te = get_child(parsed_expr, [0, 2, 0])
    display_tree(te)

# We also need a way to replace one node with another. This is done by replace_path().

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

# Using it.

if __name__ == '__main__':
    t = parsed_expr[1][0][1][2][1][0]
    display_tree(t)
    te = replace_path(parsed_expr, [0, 2, 0], [])
    display_tree(te)
    tn = replace_path(parsed_expr, [0, 2, 0], ('x',[]))
    display_tree(tn)

# # Priority queue
# 
# For perses reduction, one needs a way to count the number of leaf nodes to
# determine the priority of a node. This is done by count_leaves()

import heapq

def count_leaves(node):
    name, children, *_ = node
    if not children:
        return 1
    return sum(count_leaves(i) for i in children)

if __name__ == '__main__':
    print(count_leaves(parsed_expr))
    print(count_leaves(te))

# We also define a helper that simply counts the internal nodes.

def count_nodes(node):
    name, children, *_ = node
    if not children:
        return 0
    return sum(count_nodes(i) for i in children) + 1

if __name__ == '__main__':
    print(count_nodes(parsed_expr))

# Next, we need to maintain a priority queue of the [(tree, path)]. The
# essential idea is to prioritize the items first by the number of leaves in  the
# full tree (that is, the smallest tree that we have currently gets priority),
# then next by the number of leaves in the node pointed to by path, and finally,
# tie break by the insertion order (ecount).

ecount = 0

def add_to_pq(tup, q):
    global ecount
    dtree, F_path = tup
    stree = get_child(dtree, F_path)
    n =  count_leaves(dtree)
    m =  count_leaves(stree)
    # heap smallest first
    heapq.heappush(q, (n, m, -ecount, tup))
    ecount += 1

# We define another helper function nt_group() that groups all nonterminals that have the same name. These are used to determine the nodes that can be used to replace one node.

def nt_group(tree, all_nodes=None):
    if all_nodes is None: all_nodes = {}
    name, children, *_ = tree
    if not fuzzer.is_nonterminal(name): return
    all_nodes.setdefault(name, []).append(tree)
    for c in children:
        nt_group(c, all_nodes)
    return all_nodes

# Using it

if __name__ == '__main__':
    gp = nt_group(te)
    for key in gp:
        print(key)
        for node in gp[key]:
            print(fuzzer.iter_tree_to_str(node))

# What are the compatible nodes? These are all the nodes that have the same nonterminal name, and is a descendent of the current node. Further, if the nonterminal allows empty node, then this is the first in the list. This is defined by compatible_nodes()

def compatible_nodes(tree, grammar):
    key, children, *_ = tree
    # Here is the first choice. Do we restrict ourselves to only children of the tree
    # or do we allow all nodes in the original tree? given in all_nodes?
    lst = nt_group(tree)
    node_lst = [(i, n) for i,n in enumerate(lst[key])]

    # insert empty if the grammar allows it as the first element
    if [] in grammar[key]: node_lst.insert(0, (-1, (key, [])))
    return node_lst

# Using it.

if __name__ == '__main__':
    print(get_child(te, [0]))
    print(compatible_nodes(get_child(te, [0]), EXPR_GRAMMAR))

# Some programming languages have tokens which are first level lexical elements. The parser is often defined using the lexer tokens. We do not want to try to reduce tokens further. So we define a way to identify them (we have to keep in mind when we produce grammars). For now, we assume the ANTLR convention of identifying tokens by uppercase letters.

def is_token(val):
    assert val != '<>'
    assert (val[0], val[-1]) == ('<', '>')
    if val[1].isupper(): return True
    #if val[1] == '_': return val[2].isupper() # token derived.
    return False

# # Perses reduction
# We finally define the reduction algorithm. The implementation of Perses is given in reduction(). The essential idea is as follows:
# 
# 1. We have a priority queue of (tree, path_to_node) structures, where node is a node within the tree.
#   * The highest priority is given to the smallest tree.
#   * With in the nodes in the same tree, priority is given to nodes with smallest number of leaves
#   * In case of tie break, the shallowest subnode gets the highest priority (i.e child has higher priority over grand child, and empty node has the highest priority since it is a peer of the current node).
# 2. We pick each nodes, and find compatible subnodes that reproduce the failure.
# 3. Each compatible node and the corresponding tree is put back into the priority queue.
# 4. If no child nodes were found that could replace the current node, then we add each children with the current tree into the priority queue. (If we had to recurse into the child nodes, then the next tree that will get picked will be a different tree.)

def reduction(tree, grammar, predicate):
    first_tuple = (tree, [])
    p_q = []
    add_to_pq(first_tuple, p_q)

    ostr = fuzzer.iter_tree_to_str(tree)
    assert predicate(ostr) == PRes.success
    failed_set = {ostr: True}

    min_tree, min_tree_size = tree, count_leaves(tree)
    while p_q:
        # extract the tuple
        _n, _m, _ec, (dtree, F_path) = heapq.heappop(p_q)
        stree = get_child(dtree, F_path)
        skey, schildren = stree
        found = False
        # we now want to replace stree with alternate nodes.
        for i, node in compatible_nodes(stree, grammar):
            # replace with current (copy).
            ctree = replace_path(dtree, F_path, node)
            if ctree is None: continue # same node
            v = fuzzer.iter_tree_to_str(ctree)
            if v in failed_set: continue
            failed_set[v] = predicate(v) # we ignore PRes.invalid results
            if failed_set[v] == PRes.success:
                found = True
                ctree_size = count_leaves(ctree)
                if ctree_size < min_tree_size: min_tree, min_tree_size = ctree, ctree_size

                if v not in failed_set:
                    print(v)
                t = (ctree, F_path)
                assert get_child(ctree, F_path) is not None
                add_to_pq(t, p_q)

        # The CHOICE here is that we explore the children if and only if we fail
        # to find a node that can replace the current
        if found: continue
        if is_token(skey): continue # do not follow children TOKEN optimization
        for i, child in enumerate(schildren):
            if not fuzzer.is_nonterminal(child[0]): continue
            assert get_child(tree=dtree, path=F_path + [i]) is not None
            t = (dtree, F_path + [i])
            add_to_pq(t, p_q)
    return min_tree

# Using it

if __name__ == '__main__':
    er = reduction(parsed_expr, EXPR_GRAMMAR, expr_double_paren)
    display_tree(er)

# ### Is this Enough? (Semantics)
# 
# Note that at this point, we can generate syntactically valid inputs to check reduction, but there is no guarantee that they
# would be semantically valid (i.e. variable def-use etc.). So, we still suffer a large _unresolved_ rate. Is there a better
# solution? One option notably followed by _[creduce](http://embed.cs.utah.edu/creduce/)_ is to rely on custom reduction passes
# that maintains the validity of the string being operated on. That is, incorporate domain knowledge into reduction.
# 
# A rather different approach is taken by [Hypothesis](https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis-python/src/hypothesis/internal/conjecture/shrinker.py). Hypothesis is again a generator based reduction.
# 
# Hypothesis reducer works as follows: Given any generator that relies on randomness, one can envision an array of random bits that
# is passed to the generator. For example, consider the simple grammar generator below. It is passed `bits` which is an array of random
# bits with a function `next()`, which returns an integer and advances the index.
# 
# ```python
# def unify_key(bits, grammar, key):
#    return unify_rule(bits, grammar, grammar[key][bits.next() % len(grammar[key])]) if key in grammar else [key]
# 
# def unify_rule(bits, grammar, rule):
#     return sum([unify_key(bits, grammar, token) for token in rule], [])
# ```
# 
# When the generator wants to make a random choice, it consumes a number of bits from this array, and advances the index
# to denote that the bits were consumed. Now, at the end of generation, the bits consumed so far is essentially the trail of generation. 
# 
# Hypothesis tries to reduce the length of this trail (which it calls the _choice sequence_). Hypothesis tries to identify shorter choice sequences (short-lex order)
# that can reproduce the failure. This it does by certain surgeries in the choice sequence obtained from generating the string. The particular surgeries
# are simply removal of chunks that seems to work well in practice, with no specific reasoning behind it. If it finds
# that more bits are required than in the original choice sequence, then it discards the edit. Otherwise, the idea is that short-lex order almost
# always leads to shorter strings by prioritizing strings with smaller number of decisions, and consequently smaller number of recursion and hence
# terminal symbols.
# 
# Note that unlike HDD variants, any edit on the choice sequence is guaranteed to produce a valid string.
# 
# One question here is, why does the almost arbitrary edits in choice sequences work? The surprise here is that, arbitrary edits work even though any edit
# can end up making the remaining bits be passed to different choices than original.
# The reason seems to be that, the bugs are usually locally concentrated. That is, once one is able to reproduce the failure pattern, one can fill in
# the remaining parts of the input with randomly generated (but valid) values. Note that skeleton of the input will be generated by the initial choices itself.
# So, the hypothesis strategy seems to be to find edits that reach the pattern to reproduce fast, and then fill in the remaining blanks, which seems to work in practice.

# 
# # References
# 
# [^misherghi2006hdd]: *HDD: hierarchical delta debugging*, Ghassan Misherghi, Zhendong Su, ICSE 2006
# 
# [^herfert2017automatically]: *Automatically Reducing Tree-Structured Test Inputs*, Satia Herfert, Jibesh Patra, Michael Pradel, ASE 2017
# 
# [^sun2018perses] *Perses: Syntax-Guided Program Reduction*, Chengnian Sun, Yuanbo Li, Qirun Zhang, Tianxiao Gu, Zhendong Su, ICSE 2018
# 
# [^pike2014smartcheck] *SmartCheck: automatic and efficient counterexample reduction and generalization* Lee Pike, Haskell 2014

