# ---
# published: true
# title: Valiant's Parser
# layout: post
# comments: true
# tags: parsing, gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of Leslie G Valiant's
# general context-free Parser[^valiant1975]
# adapted from the paper "CFG Parsing and Boolean Matrix Multiplication" by
# Franziska Ebert [^ebert2006], implemented in Python.
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#  
# Valiant's parer is a general context-free parser, and like [CYK](/post/2023/01/10/cyk-parser/) and [Earley](/post/2021/02/06/earley-parsing/), it
# operates on a chart. The claim to fame of Valiant's parser is that it showed
# how to *transform* recognition of general-context free languages to an
# instance of Boolean Matrix Multiplication. That is, if you have a good matrix
# multiplication algorithm, you can use it to improve the speed of context-free
# language recognition. In fact, while previously known algorithms such as CYK
# and Earley were $$O(n^3)$$ in the worst case, Valiant's algorithm showed how
# recognition could be done in $$O(n^{2.81})$$ time using [Strassen's](https://en.wikipedia.org/wiki/Strassen_algorithm) matrix
# multiplication algorithm.
#
# It uses the same chart as that of CYK, and similar to CYK, it requires the
# grammar to be in the Chomsky Normal Form, which
# allows at most two symbols on the right hand side of any production.
# In particular, all the rules have to conform to
# 
# $$ A -> BC $$
#  
# $$ A -> a $$
#  
# $$ S -> \epsilon $$
#
# Where A,B, and C are nonterminal symbols, a is a terminal symbol, S is the
# start symbol, and $$\epsilon$$ is the empty string.
#  
# We [previously discussed](/post/2021/02/06/earley-parsing/) 
# Earley parser which is a general context-free parser. CYK
# parser is another general context-free parser that is capable of parsing
# strings that conform to **any** given context-free grammar.
#  
# A peculiarity of Valiant's parser that it shares with CYK parser is that
# unlike Earley, GLL, and GLR, it is not a left-to-right parser.
# Rather, it is a bottom-up parser similar to CYK that builds substrings of
# fixed length at each pass.
#  
# ## Synopsis
#
# ```python
# import valiantparser as P
# my_grammar = {'<start>': [['1', '<A>'],
#                           ['2']
#                          ],
#               '<A>'    : [['a']]}
# my_parser = P.ValiantParser(my_grammar)
# assert my_parser.recognize_on(text='1a', start_symbol='<start>'):
# for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
#     P.display_tree(tree)
# ```

# ## Definitions
# In the interests of having a self contained post, we repeat the
# definitions. We use the following terms:
#  
# * The _alphabet_ is the set all of symbols in the input language. For example,
#   in this post, we use all ASCII characters as alphabet.
# 
# * A _terminal_ is a single alphabet symbol. Note that this is slightly different
#   from usual definitions (done here for ease of parsing). (Usually a terminal is
#   a contiguous sequence of symbols from the alphabet. However, both kinds of
#   grammars have a one to one correspondence, and can be converted easily.)
# 
#   For example, `x` is a terminal symbol.
# 
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
#   in the grammar using _rules_ for expansion.
# 
#   For example, `<term>` is a nonterminal in the below grammar.
# 
# * A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
#   nonterminals) that describe an expansion of a given terminal. A rule is
#   also called an _alternative_ expansion.
# 
#   For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.
# 
# * A _production_ is a combination of a nonterminal and one of its productions.
# 
#   For example `<expr>: [<term>+<expr>]` is a production.
# 
# * A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.
# 
#   For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the nonterminal `<digits>`
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
# * A derivation tree can be collapsed into its string equivalent. Such a string
#   can be parsed again by the nonterminal at the root node of the derivation
#   tree such that at least one of the resulting derivation trees would be the
#   same as the one we started with.
# 
# * The *yield* of a tree is the string resulting from collapsing that tree.
# 
# * An *epsilon* rule matches an empty string.

# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cykparser-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities
import simplefuzzer as fuzzer
# We use the `display_tree()` method in earley parser for displaying trees.
import earleyparser as ep

# We use the chart display from cykparser
import cykparser as cykp

# We use the random choice to extract derivation trees from the parse forest.
import random

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
# Here is an example grammar for arithmetic expressions, starting at `<start>`.
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# Secondly, as per traditional implementations,
# there can only be one expansion rule for the `<start>` symbol. We work around
# this restriction by simply constructing as many charts as there are expansion
# rules, and returning all parse trees.
# 

# Let us start with the following grammar.

g1 = {
    '<S>': [
          ['<X>', '<Y>']],
    '<X>': [
          ['<X>', '<A>'],
          ['<A>', '<A>']],
    '<Y>': [
          ['<Y>', '<B>'],
          ['<B>', '<B>']],
   '<A>': [['a']],
   '<B>': [['b']],
}
g1_start = '<S>'

# We initialize our parser with the grammar, and identify the terminal and
# nonterminal productions separately. termiinal productions are those that
# are of the form `<A> ::= a` where a is a terminal symbol. Nonterminal
# productions are of the form `<A> ::= <B><C>` where `<B>` and `<C>` are
# nonterminal symbols.

class ValiantRecognizer(cykp.CYKParser):
    def __init__(self, grammar):
        self.cache = {}
        self.cell_width = 5
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.terminal_productions = [(k,r[0])
            for (k,r) in self.productions if fuzzer.is_terminal(r[0])]
        self.nonterminal_productions = [(k,r)
            for (k,r) in self.productions if not fuzzer.is_terminal(r[0])]

# Next, we define the recognizer. The idea here is that CYK algorithm formulates
# the recognition problem as a dynamic problem where the parse of a string of
# length `n` using a nonterminal `<A>` which is defined as `<A> ::= <B> <C>` is
# defined as a parse of the substring `0..x` with the nonterminal `<B>` and the
# parse of the substring `x..n` with nonterminal `<C>` where `0 < x < n`. That
# is, `<A>` parses the string if there exists such a parse with `<B>` and `<C>`
# for some `x`.
#
# We first initialize the matrix that holds the results. The `cell[i][j]`
# represents the nonterminals that can parse the substring `text[i..j]`

class ValiantRecognizer(ValiantRecognizer):
    def init_table(self, text, length):
        return [[{} for i in range(length+1)] for j in range(length+1)]

# Using it
if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    t = p.init_table('aabb', 4)
    p.print_table(t)
    print()

# We reuse the base case from the CYKParser.
# The idea is that, we look at each character in the input,
# and for each `i` in the input we identify `cell[i][i+1]` and add the
# nonterminal symbol that derives the corresponding token.

if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    txt = 'aabb'
    tbl = p.init_table(txt, len(txt))
    p.parse_1(txt, len(txt), tbl)
    p.print_table(tbl)
    print()

# Next, we define the multi-token parse. We start with multiplication of
# matrices which is the core of this algorithm. The table which we defined
# allows sets of nonterminal symbols at each cell. So, we define the
# multiplication of individual cells.
# 
# Given two sets of nonterminal symbols $$N_1$$, $$N_2$$, we have
# 
# $$ N_1 ∗ N_2 = {A_i | \exist A_j \in N_1, A_k \in N_2 such that (A_i -> A_j A_k) \in P}
#
# where $$P$$ is the set of production rules. The essential idea is, given a
# rule $$A_i -> A_j A_k $$, and the parsing of $$A_j$$ and $$A_k$$ is available,
# then mark $$A_i$$ as parsable.
# 

def multiply_subsets(N1, N2, P):
    #return {Ai:True for Ai, (Aj,Ak) in P if Aj in N1 and Ak in N2}
    Ais = {}
    for Ai, (Aj,Ak) in P:
        if Aj in N1 and Ak in N2:
            Ais[Ai] = True
    return Ais



# Let us try testing it.
if __name__ == '__main__':
    my_P = p.nonterminal_productions
    my_res = multiply_subsets({'<A>':True}, {'<A>':True}, my_P)
    print(my_res)
    my_res = multiply_subsets({'<X>':True}, {'<Y>':True}, my_P)
    print(my_res)
    print()

# Next, we can use the cell multiplication to define table multiplication.

def multiply_matrices(A, B, P):
    m = len(A)
    C = [[{} for _ in range(m)] for _ in range(m)]
    for i in range(m):
        for j in range(m):
            for k in range(m):
                N1 = A[i][k]
                if not N1: continue
                N2 = B[k][j]
                if not N2: continue
                C[i][j] |= multiply_subsets(N1, N2, P)
    return C

# Let us try testing it.
if __name__ == '__main__':
    my_P = p.nonterminal_productions
    my_A = p.parse_1('aabb', len('aabb'), tbl)
    p.print_table(my_A)
    print()
    my_A_2 = multiply_matrices(my_A, my_A, my_P)
    p.print_table(my_A_2)
    print()

# Next, we want to define how to make a union of two matrices

def union_matrices(A, B):
    if B is None: return A
    if A is None: return B
    C = [[{} for _ in range(len(A))] for _ in range(len(A))]
    for i in range(len(A)):
        for j in range(len(A)):
            for k in [l for l in A[i][j]] + [l for l in B[i][j]]:
                C[i][j][k] = True
    return C

# Let us try testing it.
if __name__ == '__main__':
    res = union_matrices(my_A, my_A_2)
    p.print_table(res)
    print()

# At this point, we are ready to define the transitive closure. We first
# define $$a^(i) = U_{j=1}^{i-1} a^{(j)} * a^{(i-j)}$$
# The base case is $$a^{(1)} = a$$

class ValiantRecognizer(ValiantRecognizer):
    def transitive_closure_i(self, A, i, P):
        if i == 1: return A
        if (str(A), i) in self.cache: return self.cache[(str(A), i)]
        # 1 to i-1
        res = [[{} for _ in range(len(A))] for _ in range(len(A))]
        for j in range(1,i):
            a, b = self.transitive_closure_i(A, j, P), self.transitive_closure_i(A, i-j, P)
            a_j = multiply_matrices(a, b, P)
            res = union_matrices(res, a_j)
        self.cache[(str(A), i)] = res
        return res

# We can now test it.

if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    # step 2 b1 = A(1)
    print('transitive closure_i', 1)
    b_1 = p.transitive_closure_i(my_A, 1, my_P)
    v=b_1
    p.print_table(v)

    # step 3.a[i=2] => b1= A(1) U b2= A(j=1)*A(i-j=1) # till j == i-1
    print('transitive closure_i', 2)
    b_2 = p.transitive_closure_i(my_A, 2, my_P)
    v = union_matrices(v,b_2)
    p.print_table(v)

    # step 3.b[i=3] => b1=A(1) U b2=A(j=1)*A(i-j=2) U b3=A(j=2)*A(i-j=1) # till j == i-1
    print('_'*80)
    p.print_table(v)
    print('_'*80)
    b_3 = p.transitive_closure_i(my_A, 3, my_P)
    v = union_matrices(v, b_3)
    p.print_table(v)
    print('_'*80)

    print('_'*80)
    b_4 = p.transitive_closure_i(my_A, 4, my_P)
    v = union_matrices(v, b_4)
    p.print_table(v)
    print('_'*80)

# Building the transitive closure builds the complete parse chart. That is,
# we can now check if the input was parsed.

class ValiantRecognizer(ValiantRecognizer):
    def transitive_closure(self, A, P, l):
        res = [[{} for _ in range(len(A))] for _ in range(len(A))]
        for i in range(1,l+1):
            a_i = self.transitive_closure_i(A, i, P)
            res = union_matrices(res, a_i)
        return res

# Testing.
if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    n = len('aabb')
    v = p.transitive_closure(my_A, my_P, n)
    print('parsed:', '<S>' in v[0][n])

# Let us hook it up.
class ValiantRecognizer(ValiantRecognizer):
    def recognize_on(self, text, start_symbol):
        n = len(text)
        tbl = self.init_table(txt, n)
        my_A = self.parse_1(text, n, tbl)
        my_P = self.nonterminal_productions
        v = self.transitive_closure(my_A, my_P, n)
        return start_symbol in v[0][n]

# Using it
if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    txt = 'aabb'
    result = p.recognize_on(txt, '<S>')
    print(result)
    print()
    txt = 'aabc'
    result = p.recognize_on(txt, '<S>')
    print(result)
    print()

    txt = 'aaabbb'
    result = p.recognize_on(txt, '<S>')
    print(result)
    print()

# ## ValiantParser
# Now, all we need to do is to add trees. Unlike GLL, GLR, and Earley, and like
# CYK, due to restricting epsilons to the start symbol, there are no infinite
# parse trees.

class ValiantParser(ValiantRecognizer):
    def extract_tree(self, table, sym, length):
        def find_break(A, B, table):
            for i,row in enumerate(table):
                for j,cell in enumerate(row):
                    # 0,2 2,4
                    if A in cell \
                            and B in table[j][length]:
                                return j
            return -1
        # identify the rules
        rules = self.grammar[sym]
        # check if any of the rules match.
        c_i, c_j, c_k = -1, -1, -1
        A_j, B_j = None, None
        for rule in rules:
            if len(rule) == 1:
                return [sym, [(rule[0], [])]]
            A, B = rule
            c_j = find_break(A, B, table)
            if c_j > 0:
                A_j, B_j = A, B

        l_table = [[table[i][j] for j in range(c_j+1)] for i in range(c_j+1)]
        l = self.extract_tree(l_table, A_j, c_j)

        r_table = [[table[i][j] for j in range(c_j,length+1)] for i in range(c_j, length+1)]
        r = self.extract_tree(r_table, B_j, c_j)
        return [sym, [l, r]]

    def parse_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        my_A = self.parse_1(text, length, table)
        my_P = self.nonterminal_productions
        ntable = self.transitive_closure(my_A, my_P, length)
        start = list(ntable[0][-1].keys())[0]
        return [self.extract_tree(ntable, start, length)]

# Using it (uses random choice, click run multiple times to get other trees).
if __name__ == '__main__':
    mystring = 'aabb'
    p = ValiantParser(g1)
    v = p.parse_on(mystring, '<S>')
    for t in v:
        print(ep.display_tree(t))

# assign display_tree

def display_tree(t):
    return ep.display_tree(t)


g2 = {
    '<S>': [
          ['<S>', '<S>'],
          ['<U>', '<S_>'],
          ['<U>', '<V>'],
          ],
    '<S_>': [
          ['<S>', '<V>']],
   '<U>': [['(']],
   '<V>': [[')']],
}
g2_start = '<S>'

# Using

if __name__ == '__main__':
    mystring = '(()(()))'
    p = ValiantParser(g2)
    v = p.parse_on(mystring, '<S>')
    for t in v:
        print(ep.display_tree(t))


# [^valiant1975]: Leslie G. Valiant "General context-free recognition in less than cubic time" 1975
# [^ebert2006]: Franziska Ebert "CFG Parsing and Boolean Matrix Multiplication" 2006
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008
