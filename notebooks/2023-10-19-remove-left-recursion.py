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
# direct left-recursion. The nonterminal symbols `<E>` , `<F>`, and `<Ds>` have
# direct left-recursion.

E1 = {
 '<start>': [['<E>']],
 '<E>': [['<E>', '*', '<F>'],
         ['<E>', '/', '<F>'],
         ['<F>']],
 '<F>': [['<F>', '+', '<T>'],
         ['<F>', '-', '<T>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<Ds>']],
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

# First, we need to check for left recursion

class GrammarUtils:
    def __init__(self, grammar):
        self.grammar = grammar

    def has_direct_left_recursion(self):
        for k in self.grammar:
            for r in self.grammar[k]:
                if r and r[0] == k:
                    return True
        return False

# Using it
if __name__ == '__main__':
    p = GrammarUtils(RG)
    print(p.has_direct_left_recursion())

# Next, to eliminate direct left recursion for the nonterminal `<A>`
# we repeat the following transformations until the direct left recursions
# from `<A>` are removed.

class GrammarUtils(GrammarUtils):
    def remove_direct_recursion(self, A):
        # repeat this process until no left recursion remains
        while self.has_direct_left_recursion():
            Aprime = '<%s_>' % (A[1:-1])

            # Each alpha is of type A -> A alpha1
            alphas = [rule[1:] for rule in self.grammar[A]
                      if rule and rule[0] == A]

            # Each beta is a sequence of nts that does not start with A
            betas = [rule for rule in self.grammar[A]
                      if not rule or rule[0] != A]

            if not alphas: return # no direct left recursion

            # replace these with two sets of productions one set for A
            self.grammar[A] = [[Aprime]] if not betas else [
                    beta + [Aprime] for beta in betas]

            # and another set for the fresh A'
            self.grammar[Aprime] = [alpha + [Aprime]
                                       for alpha in alphas] + [[]]

# Using it
import json
if __name__ == '__main__':
    p = GrammarUtils(RG)
    p.remove_direct_recursion('<E>')
    print(json.dumps(p.grammar, indent=4))
    p.remove_direct_recursion('<F>')
    print(p.has_direct_left_recursion())

# Removing the indirect left-recursion is a bit more trickier. The algorithm
# starts by establishing some stable ordering of the nonterminals so that
# they can be procesed in order. Next, we apply an algorithm called `Paull's`
# algorithm [^1], which is as follows:

class GrammarUtils(GrammarUtils):
    def remove_left_recursion(self) :
        # Establish a topological ordering of nonterminals.
        keylst = list(self.grammar.keys())

        # For each nonterminal A_i
        for i,_ in enumerate(keylst):
            Ai = keylst[i]

            # Repeat until iteration leaves the grammar unchanged.
            # cont = True
            # while cont:
            # For each rule Ai -> alpha_i
            for alpha_i in self.grammar[Ai]:
                #   if alpha_i begins with a nonterminal Aj and j < i
                Ajs = [keylst[j] for j in range(i)]
                if alpha_i and alpha_i[0] in Ajs:
                    Aj = alpha_i[0]
                    # Let beta_i be alpha_i without leading Ai
                    beta_i = alpha_i[1:]
                    # remove rule Ai -> alpha_i
                    lst = [r for r in self.grammar[Ai] if r != alpha_i]
                    self.grammar[Ai] = lst
                    # for each rule Aj -> alpha_j
                    #   add Ai -> alpha_j beta_i
                    for alpha_j in self.grammar[Aj]:
                        self.grammar[Ai].append(alpha_j + beta_i)
            #        cont = True
            #cont = False
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

# Another algorithm is here: https://www.microsoft.com/en-us/research/wp-content/uploads/2000/04/naacl2k-proc-rev.pdf
# 
# [^1]: Marvin C. Paull Algorithm design: a recursion transformation framework
