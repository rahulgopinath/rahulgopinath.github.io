# ---
# published: true
# title: Grammar Coverage with K-Paths for Syntax Testing
# layout: post
# comments: true
# tags: grammars peg
# categories: post
# ---
#  
# TLDR; This tutorial describes how to design test cases that can effectively
# cover features of a given context-free grammar using the k-path strategy.
# 
# ## Definitions
#
# For this post, we use the following terms as we have defiend  previously:
#
# * The _alphabet_ is the set all of symbols in the input language. For example,
#   in this post, we use all ASCII characters as alphabet.
#  
# * A _terminal_ is a single alphabet symbol.
#
#   For example, `x` is a terminal symbol.
#
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is
#   _defined_ in the grammar using _rules_ for expansion.
#
#   For example, `<term>` is a nonterminal symbol.
#
# * A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
#   nonterminals) that describe an expansion of a given terminal.
#
#   For example, `[<term>+<expr>]` is one of the expansion rules of the
#   nonterminal `<expr>`.
#
# * A _definition_ is a set of _rules_ that describe the expansion of a given
#   nonterminal.
#
#   For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the
#   nonterminal `<digits>`
#
# * A _context-free grammar_ is  composed of a set of nonterminals and
#   corresponding definitions that define the structure of the nonterminal.
#
#   The grammar given below is an example context-free grammar.
#
# * A terminal _derives_ a string if the string contains only the symbols in the
#   terminal. A nonterminal derives a string if the corresponding definition
#   derives the string. A definition derives the  string if one of the rules in
#   the definition derives the string. A rule derives a string if the sequence
#   of terms that make up the rule can derive the string, deriving one substring
#   after another contiguously (also called parsing).
#
# * A *derivation tree* is an ordered tree that describes how an input string is
#   derived by the given start symbol. Also called a *parse tree*.
#  
# * A derivation tree can be collapsed into its string equivalent. Such a string
#   can be parsed again by the nonterminal at the root node of the derivation
#   tree such that at least one of the resulting derivation trees would be the
#   same as the one we started with.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

import math
import random

# ## Syntax Based Testing
# When the abstract model of a program is a graph, to test such programs
# effectively, one uses the syntax based testing. Similarly, if the input domain
# of a program is a context-free language, to test such programs effectively,
# one needs to rely on syntax based testing. In both these cases, the following
# are the traditional test design objectives.
# 
# * Covering all terminal symbols in the context-free grammar
# * Covering all definitions in the context-free grammar
# * Covering all rules in the context-free grammar (subsumes the above two).
# 
# However, these test design objectives do not produce inputs that are diverse
# enough for modern grammars. Hence, one may have to rely on stronger
# criteria. One such is called *K-Paths* [^havricov2019].
# 
# ###  K-Paths
# 
# A *K-path* is a sequence of expansions with K nonterminal symbols.
# A *1-path* is a path where there is only a single nonterminal symbol is
# involved. So, a test suite designed with all *1-path* criteria is same as one
# defined with *all definitions* obligation. A *2-path* is a path with exactly
# two nonterminal symbols that are expanded consecutively.
# For example, say you have a definition such as
# 
#  ```
# <digits>:[
#                [<digit><digits>],
#                [<digit>],
# ],
# 
# <digit>: [[1],[0]]
#  ```
# 
# and a derivation tree that looks like
#  
#  
#  ```
# ('<digits>', [
#           ('<digit>', [('1', [])])
#           ])
#  ```
# 
# Such a tree is an instance of a *2-path*, which is `[<digits>, <digit>]`. In a tree such as 
# 
# 
#  ```
# ('<digits>', [
#           ('<digit>', [('1', [])]),
#           ('<digits>',
#               [('<digit>', [('1', [])])])
#           ])
#  ```
# 
# we haveone *3-path*, which is `[<digits>,<digits>, <digit>]`. We also have two
# *2-paths* `[<digits>, <digit>]`, `[<digits>,<digits>]` and `[<digits>, <digit>]`
# , but there are only two unique *2-paths*.
# So, the question is, how to compute the more complex k-paths?
# 
# We stat by defining a function `parents()` which takes in a grammar, and
# identifies possible parent nodes for a given nonterminal symbol.

def parents(g):
    parent = {}
    for k in g:
        for r in g[k]:
            for t in r:
                if t not in g: continue
                if t not in parent: parent[t] = set()
                parent[t].add(k)
    return parent

# That is, given the expression grammar

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

EXPR_START = '<start>'
# The parents are
if __name__ == '__main__' :
    parent = parents(EXPR_GRAMMAR)
    for k in parent:
        print('parent nodes for', k)
        for v in parent[k]:
            print("  ", v)

# Next, we define a function to compute all k-paths in a grammar.

def _k_paths(g, k, parent):
    if k == 1: return [[k] for k in g]
    _k_1_paths = _k_paths(g, k-1, parent)
    # attach parents to each of the _k_1_paths.
    new_paths = []
    for path in _k_1_paths:
        if path[0] not in parent: continue
        for p in parent[path[0]]:
            new_paths.append([p] + path)
    return new_paths

# Using it:
if __name__ == '__main__' :
    for path in _k_paths(EXPR_GRAMMAR, 4, parent):
        if path[0] in ['<start>']: # limit the output
            print(path)

# We can now tie both together

def k_paths(g, k):
    g_parents = parents(g)
    return _k_paths(g, k, g_parents)

# Using
if __name__ == '__main__' :
    for path in k_paths(EXPR_GRAMMAR, 4):
        if path[0] in ['<start>']: # limit the output
            print(path)

# Now that we have the k-paths, how do we obtain the test cases?
# For that, we first define a procedure that given a a node of the tree,
# and the parent nonterminal symbol (key), looks through the rules of the
# parent key, and identifies one of the rule which contains the root nonterminal
# of the # given node as a token. Given such a rule, we can embed the current
# node, forming a partial tree.

def find_rule_containing_key(g, key, root):
    leaf = root[0]
    for rule in g[key]:
        r = []
        while rule:
            token, *rule = rule
            if leaf != token:
                r.append(token)
            else:
                return r + [root] + rule
    assert False

# using it
if __name__ == '__main__' :
    node = ('<digit>', [('1', [])])
    v = find_rule_containing_key(EXPR_GRAMMAR, '<integer>', node)
    # this would be the tree.
    print(('<integer>', v))

# Next, given a k-path, we want to make it into a tree.
def path_to_tree(path_, g):
    leaf, *path = reversed(path_)
    root = (leaf, [])
    # take the lowest
    while path:
        leaf, *path = path
        if not path: return root
        rule = find_rule_containing_key(g, leaf, root)
        root = [leaf, rule]

# Using it.
if __name__ == '__main__':
    path = ['<start>', '<expr>', '<term>', '<factor>', '<integer>']
    tree = path_to_tree(path, EXPR_GRAMMAR)
    print(tree)

# Let us define a method to display such trees

def display_tree(node, level=0, c='-'):
    key, children = node
    print(' ' * 4 * level + c+'> ' + key)
    for c in children:
        if isinstance(c, str):
            print(' ' * 4 * (level+1) + c)
        else:
            display_tree(c, level + 1, c='+')

# Using it
if __name__ == '__main__':
    display_tree(tree)

# Note that the tree is partial. We need to expad the nodes to make this into a
# complete test input.
# 
# [^havricov2019]: Havrikov, Nikolas, and Andreas Zeller. "Systematically covering input structure." 2019 34th IEEE/ACM international conference on automated software engineering (ASE). IEEE, 2019.

