# ---
# published: true
# title: Removing Left Recursion from Context Free Grammars
# layout: post
# comments: true
# tags: context-free-grammars left-recursion
# categories: post
# ---
# 
# Left recursion in context-free grammars is when a nonterminal when expanded,
# results in the same nonterminal symbol in the expansion as the first symbol.
# If the symbol is present as the first symbol in one of the expansion rules of
# the nonterminal, it is called a direct left-recursion. Below is a grammar with
# direct left-recursion. The nonterminal symbol `<Ds>` has a direct
# left-recursion.

E1 = {
 '<start>': [['<Ds>']],
 '<Ds>':[['<Ds>', '<D>'], ['<D>']],
 '<D>': [[str(i)] for i in range(10)]
}

# An indirect left-recursion occurs when the symbol is found after more than
# one expansion step. Here is an indirect left-recursion.

E2 = {
 '<start>': [['<I>']],
 '<I>' : [['<Ds>']],
 '<Ds>': [['<I>', '<D>'], ['<D>']],
 '<D>': [[str(i)] for i in range(10)]
}

# Here, `<I>` has an indirect left-recursion as expanding `<I>` through `<Ds>`
# results in `<I>` being the first symbol again.
# 
# For context-free grammars, in many cases left-recursions are a nuisance.
# During parsing, left-recursion in grammars can make simpler parsers recurse
# infinitely. Hence, it is often useful to eliminate them.
# 
# It is fairly simple to eliminate them from context-free grammars. Here is
# a solution.
#  
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities

import simplefuzzer as fuzzer

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# 
# We have our grammar:

RG = {
 '<start>': [['<E>']],
 '<E>': [['<E>', '*', '<F>'],
         ['<E>', '/', '<F>'],
         ['<F>']],
 '<F>': [['<F>', '+', '<T>'],
         ['<F>', '-', '<T>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<I>']],
 '<I>' : [['<Ds>']],
 '<Ds>': [['<I>', '<D>'], ['<D>']],
 '<D>': [[str(i)] for i in range(10)]
}

RGstart = '<start>'

# First, we need to check for left recursion.
# 
# ## Definitions
# 
# Following Moore [^1], we will use the following terminology.
# 
# * A symbol X is a *direct left corner* of a nonetrminal symbol A if
#   there is an expansion rule A -> X alpha, where alpha is any sequence
#   of tokens.
# 
# * A *left corner relation* is a reflexive transitive closure of the
#   direct left corner relation.
# 
# * A symbol is *directly left recursive* if it is in the direct left corner
#   of itself.
# 
# * A symbol is *left recursive* if it has a left corner relation with itself.
# 
# * A symbol is *indirectly left recursive* if it is left recursive but not
#   directly left recursive.
# 
# For this algorithm to work, we need the grammar to not have epsilon
# productions. You can refer to my [previous post](/post/2021/09/29/remove-epsilons/)
# for the algorithm for removing epsilon productions.

class GrammarUtils:
    def __init__(self, grammar):
        self.grammar = grammar
        # check no epsilons
        for k in grammar:
            for r in grammar[k]: assert r, "epsilons not allowed"

    def direct_left_corner(self, k):
        return [r[0] for r in self.grammar[k] if r]

    def has_direct_left_recursion(self):
        for k in self.grammar:
            if k in self.direct_left_corner(k): return True
        return False

# Using it
if __name__ == '__main__':
    p = GrammarUtils(RG)
    print(p.has_direct_left_recursion())

# Next, to eliminate direct left recursion for the nonterminal `<A>`
# we repeat the following transformations until the direct left recursions
# from `<A>` are removed.
# 
# Given
# 
# ```
# A -> A alpha_1
#   | ...
#   | A alpha_2
#   | beta_1
#   | ..
#   | beta_m
# ```
# 
# such that A -> A alpha_i is an expansion rule of A that contains a direct left
# recursion, and alpha_i is a sequence of tokens, and A -> beta_j represents
# an expansion rule without direct left recursion where beta_j is a sequence of
# tokens, for every beta_j, add a new expansion rule A -> beta_j A' and
# for every alpha_i, add A' -> alpha_i A' to the grammar. Finally add
# A' -> epsilon to the grammar.

class GrammarUtils(GrammarUtils):
    def remove_direct_recursion(self, A):
        # repeat this process until no left recursion remains
        while self.has_direct_left_recursion():
            Aprime = '<%s_>' % (A[1:-1])

            alphas = [rule[1:] for rule in self.grammar[A] if rule[0] == A]

            if not alphas: return
            self.grammar[Aprime] = [alpha + [Aprime] for alpha in alphas] + [[]]

            betas = [rule for rule in self.grammar[A] if rule[0] != A]
            if betas:
                self.grammar[A] = [beta + [Aprime] for beta in betas]
            else:
                self.grammar[A] = [[Aprime]]

# Using it
import json
if __name__ == '__main__':
    p = GrammarUtils(E1)
    p.remove_direct_recursion('<Ds>')
    print(json.dumps(p.grammar, indent=4))
    print(p.has_direct_left_recursion())

# Removing the indirect left-recursion is a bit more trickier. The algorithm
# starts by establishing some stable ordering of the nonterminals so that
# they can be procesed in order. Next, we apply an algorithm called `Paull's`
# algorithm [^1], which is as follows:
# For any nonterminals Ai and Aj such that i > j in the ordering, and Aj
# is a direct left corner of Ai, replace all occurrences of Aj as a direct
# left corner of Ai with all possible expansions of Aj

class GrammarUtils(GrammarUtils):
    def remove_left_recursion(self) :
        # Establish a topological ordering of nonterminals.
        keylst = list(self.grammar.keys())

        for i,Ai in enumerate(keylst):
            for alpha_i in self.grammar[Ai]:

                # if Aj is a direct left corner of Ai
                Ajs = [keylst[j] for j in range(i)]
                if alpha_i[0] not in Ajs: continue
                Aj = alpha_i[0]

                # remove alpha_i from Ai rules
                self.grammar[Ai] = [r for r in self.grammar[Ai] if r != alpha_i]

                # and replace it with expansions of Aj + beta_i.
                beta_i = alpha_i[1:]
                for alpha_j in self.grammar[Aj]:
                    self.grammar[Ai].append(alpha_j + beta_i)
            self.remove_direct_recursion(Ai)

# Using it:

if __name__ == '__main__':
    p = GrammarUtils(RG)
    p.remove_left_recursion()
    print(json.dumps(p.grammar, indent=4))

# Let us see if the grammar results in the right language

if __name__ == '__main__':
    gf = fuzzer.LimitFuzzer(p.grammar)
    for i in range(10):
       print(gf.iter_fuzz(key=RGstart, max_depth=10))

# A problem with this algorithm is its exponential case behavior as Moore [^2]
# notes. The solution that Moore offers is to order the nonterminals in the
# decreasing order of the number of distinct left corners.
#  
# 
# [^1]: Marvin C. Paull, Algorithm design: a recursion transformation framework, 1988
# [^2]: Robert C Moore, Removing Left Recursion from Context-Free Grammars [*](https://www.microsoft.com/en-us/research/wp-content/uploads/2000/04/naacl2k-proc-rev.pdf)., 2000
