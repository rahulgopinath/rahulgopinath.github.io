# ---
# published: true
# title: Delta Debugging
# layout: post
# comments: true
# tags: reducing
# categories: post
# ---
 
# Note: This is based on the *ddmin* in [the fuzzingbook](https://www.fuzzingbook.org/html/Reducer.html#Delta-Debugging).

# ### About Delta Debugging
# 
# Delta Debugging is a method to reduce failure inducing inputs to their
# smallest required size that still induces the same failure. It was
# first formally introduced in the paper
# [*Simplifying and Isolating Failure-Inducing Input*](https://www.st.cs.uni-saarland.de/papers/tse2002/tse2002.pdf)
# by Zeller and Hildebrandt.
# 
# The idea of delta debugging is fairly simple. We start by partitioning
# the given input string, starting with two partitions -- which have a
# given partition length. Then, we check if any of these parts can be
# removed without removing the observed failure. If any of these can be
# removed, we remove all such parts of the given length. Once no such
# parts of the given length can be removed, we reduce the partition
# length by two, and do the same process again. This obtains us the
# *1-minimal* failure causing string where removal of even a single
# character will remove the observed failure.
# 
# Given a causal function as below,

def test(s):
    v = re.match("<SELECT.*>", s)
    print("%s  %s %d" % (('+' if v else '.'),  s, len(s)))
    return v

# Here is an example run:
# 
# ```shell
# $ python ddmin.py '<SELECT NAME="priority" MULTIPLE SIZE=7>'
# .  ty" MULTIPLE SIZE=7> 20
# .  <SELECT NAME="priori 20
# .  ME="priority" MULTIPLE SIZE=7> 30
# +  <SELECT NAty" MULTIPLE SIZE=7> 30
# +  <SELECT NALE SIZE=7> 20
# .  <SELECT NA 10
# .  CT NALE SIZE=7> 15
# .  <SELELE SIZE=7> 15
# +  <SELECT NAZE=7> 15
# .  <SELECT NA 10
# .  ELECT NAZE=7> 13
# .  <SECT NAZE=7> 13
# .  <SELT NAZE=7> 13
# .  <SELECNAZE=7> 13
# +  <SELECT ZE=7> 13
# +  <SELECT =7> 11
# +  <SELECT > 9
# .  <SELECT  8
# .  SELECT > 8
# .  <ELECT > 8
# .  <SLECT > 8
# .  <SEECT > 8
# .  <SELCT > 8
# .  <SELET > 8
# .  <SELEC > 8
# +  <SELECT> 8
# .  <SELECT 7
# <SELECT>
# ```

# ## Implementation
# 
# How do we implement this?
# 
# First, the prerequisites:

import random
import string
import re

# ### remove_check_each_fragment()

# Given a partition length, we want to split the string into
# that many partitions, remove each partition one at a time from the
# string, and check if for any of them, the `causal()` succeeds. If it
# succeeds for any, then we can skip that section of the string.
 
def remove_check_each_fragment(instr, part_len, causal):
    pre = ''
    for i in range(0, len(instr), part_len):
        stitched =  pre + instr[i+part_len:]
        if not causal(stitched):
             pre = pre + instr[i:i+part_len]
    return pre

# There is a reason this function is split from the main function unlike in the
# original implementation of `ddmin`. The function `remove_check_each_fragment`
# obeys the contract that any string returned by it obeys the contract represented
# by the `causal` function. This means that any test case that is produced by
# `remove_check_each_fragment` will reproduce the specified behavior, and can be
# used for other computations. For example, one may use it for evaluating test
# reduction slippage, or for finding other reductions.
# 
# 
# ### ddmin()
# 
# The main function. We start by the smallest number of partitions -- 2.
# Then, we check by removing each fragment for success. If removing one
# fragment succeeds, we change the current string to the string without that
# fragment. So, we remove all fragments that can be removed in that partition
# size.
# If none of the fragments could be removed, then we reduce the partition length
# by half.
# If the partition cannot be halved again (i.e, the last partition length was
# one) or the string has become empty, we stop the iteration.

def ddmin(cur_str, causal_fn):
    part_len = len(cur_str) // 2
    while part_len and cur_str:
        _str = remove_check_each_fragment(cur_str, part_len, causal_fn)
        if _str == cur_str:
            part_len = part_len // 2
        cur_str = _str

    return cur_str

# The driver.

def test(s):
    print("%s %d" % (s, len(s)))
    return set('()') <= set(s)

# 

inputstring = ''.join(random.choices(string.digits +
                      string.ascii_letters +
                      string.punctuation, k=1024))
print(inputstring)

# 

assert test(inputstring)
solution = ddmin(inputstring, test)
print(solution)

# The nice thing is that, if you invoke the driver, you can see the reduction in
# input length in action. Note that our driver is essentially a best case
# scenario. In the worst case, the complexity is $$O(n^2)$$
# 
# ### Recursive
# 
# That was of course illuminating. However, is that the only way to implement this?
# *delta-debug* at its heart, is a divide and conquer algorithm. Can we implement it
# recursively?
# 
# The basic idea is that given a string, we can split it into parts, and check if either
# part reproduces the failure. If either one does, then call `ddrmin()` on the part that
# reproduced the failure.
# 
# If neither one did, then it means that there is some part in the first partition that
# is required for failure, and there is some part in the second partition too that is required
# for failure. All that we need to do now, is to isolate these parts. How should we do that?
# 
# Call `ddrmin()` but with an updated check. For example, for the first part, rather than
# checking if some portion of the first part alone produces the failure, check if some part of
# first, when combined with the second will cause the failure.
# 
# All we have left to do, is to define the base case. In our case, a character of length one
# can not be partitioned to strictly smaller parts. Further, we already know that any string
# passed into `ddrmin()` was required for reproducing the failure. So, we do not have to
# worry about empty string. Hence, we can return it as is.
# 
# Here is the implementation.
# 
# ### ddrmin()

def ddrmin(cur_str, causal_fn, pre='', post=''):
    if len(cur_str) == 1: return cur_str
    
    part_i = len(cur_str) // 2
    string1, string2 = cur_str[:part_i], cur_str[part_i:]
    if causal_fn(pre + string1 + post):
        return ddrmin(string1, causal_fn, pre, post)
    elif causal_fn(pre + string2 + post):
        return ddrmin(string2, causal_fn, pre, post)
    s1 = ddrmin(string1, causal_fn, pre, string2 + post)
    s2 = ddrmin(string2, causal_fn, pre + s1, post)
    return s1 + s2
    
ddmin = ddrmin

# Given that it is a recursive procedure, one may worry about stack exhaustion, especially
# in languages such as Python which allocates just the bare minimum stack by default. The
# nice thing here is that, since we split the string by half again and again, the maximum
# stack size required is $$log(N)$$ of the input size. So there is no danger of exhaustion.
# 
# The recursive algorithm is given in *Yesterday, my program worked.Today, it does not. Why?* by Zeller in 1999.
# 
# ### Is this Enough? (Syntax)
# 
# One of the problems with the unstructured version of `ddmin()` above is that it assumes
# that parts of the inputs can be cut away, while still retaining validity in that it will
# actually reach the testing function. This, however, may not be a reasonable assumption
# especially in the case of structured inputs. The problem is that if you have a JSON
# `[{"a": null}]`
# that produces an error because the key value is `null`, `ddmin()` will try to partition it
# as `[{"a":` followed by `null}]` neither of which are valid. Further, any chunk removed from
# either parts are also likely to be invalid. Hence, `ddmin()` will not be able to proceed.
# 
# The solution here is to go for a variant called `Hierarchical Delta Debugging` described
# in *HDD: hierarchical delta debugging* by Misherghi et al. in 2006. The basic idea is to
# first extract the parse tree (either by parsing the input using a grammar, or by either
# relying on a generator to generate the parse tree along with the input, or by extracting
# the parse tree in-flight from the target program if it supports it), and then try and apply `ddmin()` on each level
# of the derivation tree. Another notable improvement is
# *Automatically Reducing Tree-Structured Test Inputs* by Herfert et al. in 2017. In this
# paper, the authors describe a simple strategy: Try and replace a given node by one of
# its child nodes. This works reasonably well for inputs that are context sensitive such
# as programs that can trigger bugs in compilers. Another is *Perses: Syntax-Guided Program Reduction*
# by Sun et al. in 2018 which uses the program grammar directly to avoid creating invalid nodes.
# 
# The problem in the above approach is that, it assumes that there exist a child node that
# is of same type as the parent node. This need not be the case. Hence an even better idea
# might be to simply do a breadth first search of the first node that
# has the same symbol as that of the current node, and try replacing with that node,
# continuing with the next symbol of the same kind if it fails.
# 
# ### Perses
# 
# Below is a variant of hierarchical `ddmin()` from "Perses: syntax-guided program reduction" by Sun et al. 2018

import sys
import re
import copy
import heapq

# #### A few helpers
# 
# Check if a given token is a noterminal

def is_nt(v):
    return (v[0], v[-1]) == ('<', '>')

def tree_to_string(tree):
    name, children, *rest = tree
    if not is_nt(name): return name
    else: return ''.join([tree_to_string(c) for c in children])

# #### We prioritize the smallest trees.

def count_leaves(node):
    name, children = node
    if not children:
        return 1
    return sum(count_leaves(i) for i in children)

# #### A priority queue

def add_to_queue(node, q):
    heapq.heappush(q, (count_leaves(node), node))

# #### A way to tempoararily replace a node in a tree.

class ReplaceNode:
    def __init__(self, node, new_node = None):
        self.node, self.new_node = node, ['', []] if new_node is None else new_node
        self.node_copy = copy.copy(self.node)

    def __enter__(self):
        # we dont worry about legal grammar here as this is temporary
        self.node.clear()
        if self.new_node is not None:
            self.node.extend(self.new_node)

    def __exit__(self, *args):
        self.node.clear()
        self.node.extend(self.node_copy)

# #### Find all subtrees with the given symbol

def subtrees_with_symbol(node, symbol, result=None, depth=0):
    if result is None: result = []
    name, children = node
    if name == symbol:
        result.append((depth, node))
    for c in children:
        subtrees_with_symbol(c, symbol, result, depth+1)
    return result

# #### The perses algorithm itself.
# 
# Note that we do not do the Perses-Normal-Form. Hence, the
# grammar should be amenable to deletion of nonterminals.
# This means that we have to do a bit kludge here.
# The issue is that not all grammars
# may indicate a deletable sequence with a single nonterminal.
# some may simply indicate that by using two rules like below
# ```
# <mykey> := <a> <b> <c>
#         |  <a> <b>
# ```
# which indicates <c> may be deleted.
# Hence, checking for empty expansion in a nonterminal will not
# always work; the tradeoff here is to allow _some_ invalid
# strings, which is what we do below. If you do not want invalid
# strings at all use the first one.
# 
# (1) empty nonterminal in grammar
# ```
#     if [] in grammar[bsymbol]: # empty expansion
#        ssubtrees.insert(0, (0, (bsymbol, [])))
# ```
# (2) allow invalid trees
# ```
#     ssubtrees.insert(0, (0, (bsymbol, [])))
# ```

def perses_delta_debug(grammar, orig_tree, predicate):
    tree = copy.deepcopy(orig_tree) # we minify the original tree
    p_q = []
    add_to_queue(tree, p_q)
    while p_q:
        reprocess = None
        _, biggest_node = heapq.heappop(p_q)
        bsymbol = biggest_node[0]
        _root, *subtrees = subtrees_with_symbol(biggest_node, bsymbol)
        ssubtrees = sorted(subtrees, reverse=True)
        # note the choice above.
        ssubtrees.insert(0, (0, (bsymbol, [])))

        for _depth,stree in ssubtrees:
            with ReplaceNode(biggest_node, stree):
                s = tree_to_string(tree)
                if predicate(s):
                    reprocess = stree
                    break
        if reprocess is not None:
            biggest_node.clear()
            biggest_node.extend(reprocess)
            add_to_queue(biggest_node, p_q)
        else:
            for c in biggest_node[1]:
                if is_nt(c[0]):
                    add_to_queue(c, p_q)
    return tree

# #### The driver
# 
# First, we define the predicate. Our predicate is simple. We check if the expression has doubled parenthesis.

def test_bb(inp):
    if re.match(r'.*[(][(].*[)][)].*', inp):
        return True
    return False

# We have the following grammar

EXPR_GRAMMAR = {'<start>': [['<expr>']],
 '<expr>': [['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
 '<term>': [['<factor>', '*', '<term>'], ['<factor>', '/', '<term>'], ['<factor>']],
 '<factor>': [['+', '<factor>'],
  ['-<factor>'],
  ['(', '<expr>', ')'],
  ['<integer>', '.', '<integer>'],
  ['<integer>']],
 '<integer>': [['<digit>', '<integer>'], ['<digit>']],
 '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']]}

# And the following input

my_input = '1+((2*3/4))'

# We parse and generate a derivation tree as follows

# Loading the prerequisite:

"https://rahul.gopinath.org/py/earleyparser-0.0.4-py3-none-any.whl"

# 

import earleyparser

# 

d_tree_, *_ = earleyparser.EarleyParser(EXPR_GRAMMAR).parse_on(my_input, '<start>')


# The derivation tree looks like this

print(d_tree_)

# 

def modifiable(tree):
    name, children, *rest = tree
    if not is_nt(name): return [name, []]
    else:
      return [name, [modifiable(c) for c in children]]

d_tree = modifiable(d_tree_)

# Now, we are ready to use the `perses_delta_debug()`

tree = perses_delta_debug(EXPR_GRAMMAR, d_tree, test_bb)
print(tree_to_string(tree))

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