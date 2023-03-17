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
#  **Note.** This implementation is thoroughly unoptimized.
#  
# Valiant's parer is a general context-free parser, and like [CYK](/post/2023/01/10/cyk-parser/) and [Earley](/post/2021/02/06/earley-parsing/), it
# operates on a chart. The claim to fame of Valiant's parser is that it showed
# how to *transform* recognition of general-context free languages to an
# instance of Boolean Matrix Multiplication. That is, if you have a good matrix
# multiplication algorithm, you can use it to improve the speed of context-free
# language recognition. In fact, while previously known algorithms such as CYK
# and Earley were $$O(n^3)$$ in the worst case, Valiant's algorithm showed how
# recognition could be done in $$O(n^{2.81})$$ time using [Strassen's](https://en.wikipedia.org/wiki/Strassen_algorithm) matrix
# multiplication algorithm (This post uses the traditional multiplication
# algorithm, but improved algorithms can be substituted at the
# `multiply_matrices()` function ).
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
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# Secondly, as per traditional implementations,
# there can only be one expansion rule for the start ymbol.

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

# ## ValiantRecognizer
# We initialize our recognizer with the grammar, and identify the terminal and
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

# Next, we define the recognizer. Like in CYK, the idea here is that the
# algorithm formulates
# the recognition problem as a problem where the parse of a string of
# length `n` using a nonterminal `<A>` which is defined as `<A> ::= <B> <C>` is
# defined as a parse of the substring `0..x` with the nonterminal `<B>` and the
# parse of the substring `x..n` with nonterminal `<C>` where `0 < x < n`. That
# is, `<A>` parses the string if there exists such a parse with `<B>` and `<C>`
# for some `x`.
#
# ### Initialize the table
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

# ### Matrix multiplication
# Next, we define the multi-token parse. We start with multiplication of
# matrices which is the core of this algorithm. The table which we defined
# allows sets of nonterminal symbols at each cell. So, we define the
# multiplication of individual cells.
# 
# Given two sets of nonterminal symbols $$N_1$$, $$N_2$$, we have
#  
# $$ N_1 ∗ N_2 = \{ A_i | \exists A_j \in N_1, A_k \in N_2 : (A_i -> A_j A_k) \in P \} $$
#  
# where $$P$$ is the set of production rules. The essential idea is, given a
# rule $$A_i -> A_j A_k $$, and the parsing of $$A_j$$ and $$A_k$$ is available,
# then mark $$A_i$$ as parsable.
#  

def multiply_subsets(N1, N2, P):
    return {Ai:True for Ai, (Aj,Ak) in P if Aj in N1 and Ak in N2}



# Let us try testing it.
if __name__ == '__main__':
    my_P = p.nonterminal_productions
    # <X> -> <A> <A>
    my_res = multiply_subsets({'<A>':True}, {'<A>':True}, my_P)
    print(my_res)
    # <S> -> <X> <Y>
    my_res = multiply_subsets({'<X>':True}, {'<Y>':True}, my_P)
    print(my_res)
    print()

# Next, we can use the cell multiplication to define table multiplication.
# Note that we do not do transformation into boolean matrices here.

def multiply_matrices(A, B, P):
    m = len(A)
    C = [[{} for _ in range(m)] for _ in range(m)]
    for i in range(m):
        for j in range(m):
            for k in range(m):
                C[i][j] |= multiply_subsets(A[i][k], B[k][j], P)
    return C

# **If we want to convert to boolean matrices given matrices $$a$$ and $$b$$:**,
# we start by computing $$ h = |N|$$ where $$N$$
# is the set of nonterminals. We start with matrix $$a$$.
# Next, we generate $$h$$ matrices one for each nonterminal $$k \in N$$.
# Let us call such a matrix $$M_k$$. We fill it in this way:
# If nonterminal $$k$$ is present in the cell $$(i,j)$$ of $$a$$,
# the corresponding cell in $$M_k$$ will be `true`, and `false` otherwise.
# We do the same for matrix $$b$$, getting $$2*h$$ boolean matrices.
#  
# Let us call these $$M_k^a$$ and $$M_k^b$$ where $$k$$ indicates the nonterminal.
#  
# Next, we pair each matrix from $$M_k^a$$ and $$M_k^b$$ for each $$k \in N$$
# obtaining $$h^2$$ pairs, and compute the boolean matrix multiplication of each
# pairs. We address each as $$r(l,m)$$ where $$l \in N$$ and $$m \in N$$.
#  
# In the final matrix $$c = a * b$$, for the cell $$c(i,j)$$ it will contain the
# nonterminal $$p \in N$$ iff there exist l,m such that a rule $$ p -> l m $$
# exists, and the matrix $$r(l,m)$$ contains $$1$$ in cell $$(i,j)$$.
# **TODO**.

# Let us try testing it.
if __name__ == '__main__':
    my_P = p.nonterminal_productions
    my_A = p.parse_1('aabb', len('aabb'), tbl)
    p.print_table(my_A)
    print()
    my_A_2 = multiply_matrices(my_A, my_A, my_P)
    p.print_table(my_A_2)
    print()

# ### Matrix union
# Next, we want to define how to make a union of two matrices

def union_matrices(A, B):
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

# ### Transitive relation
# Valiant showed that we can compute the [transitive relation](https://en.wikipedia.org/wiki/Transitive_closure)
# -- *parsable in i steps* -- can be computed using matrix multiplication.
# For a matrix $$ a^{(i)} $$, the relation is given by:
#  
#  $$a^{(i)} = U_{j=1}^{i-1} a^{(j)} * a^{(i-j)}$$ when $$ i > 1 $$
#   
#  $$a^{(1)} = a$$ when $$ i = 1 $$
#  
#  The intuition here is that if we have a 4 letter input, it may be parsed by
#  splitting into 1+3, 2+2, or 3+1. So, we compute
#  $$ a^{(1)}$$*$$a^{(3)} U a^{(2)}$$*$$a^{(2)} U a^{(3)}$$*$$a^{(1)} $$.
#   
#  At this point, we are ready to define the transitive relation.

class ValiantRecognizer(ValiantRecognizer):
    def parsed_in_steps(self, A, i, P):
        if i == 1: return A
        if (str(A), i) in self.cache: return self.cache[(str(A), i)]
        # 1 to i-1
        res = [[{} for _ in range(len(A))] for _ in range(len(A))]
        for j in range(1,i):
            a = self.parsed_in_steps(A, j, P)
            b = self.parsed_in_steps(A, i-j, P)
            a_j = multiply_matrices(a, b, P)
            res = union_matrices(res, a_j)
        self.cache[(str(A), i)] = res
        return res

# We can now test it.
# step 2 `b1 = A(1)`

if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    print('steps_i', 1)
    b_1 = p.parsed_in_steps(my_A, 1, my_P)
    v=b_1
    p.print_table(v)

# step 3.a `[i=2] => b1= A(1) U b2= A(j=1)*A(i-j=1)` -- till `j == i-1`
if __name__ == '__main__':
    print('steps_i', 2)
    b_2 = p.parsed_in_steps(my_A, 2, my_P)
    v = union_matrices(v,b_2)
    p.print_table(v)

# step 3.b `[i=3] => b1=A(1) U b2=A(j=1)*A(i-j=2) U b3=A(j=2)*A(i-j=1)` -- till `j == i-1`
if __name__ == '__main__':
    b_3 = p.parsed_in_steps(my_A, 3, my_P)
    v = union_matrices(v, b_3)
    p.print_table(v)
    print()

    b_4 = p.parsed_in_steps(my_A, 4, my_P)
    v = union_matrices(v, b_4)
    p.print_table(v)
    print()

# ### Transitive closure
# Valiant further showed that the transitive closure of all these matrices,
# that is
#  
# $$ a^{+} = a^{(1)} U a^{(2)} ... $$
#  
# is the parse matrix.
# That is, building the transitive closure builds the complete parse chart.
# We can now check if the input was parsed.

class ValiantRecognizer(ValiantRecognizer):
    def transitive_closure(self, A, P, l):
        res = [[{} for _ in range(len(A))] for _ in range(len(A))]
        for i in range(1,l+1):
            a_i = self.parsed_in_steps(A, i, P)
            res = union_matrices(res, a_i)
        return res

# Testing.
if __name__ == '__main__':
    p = ValiantRecognizer(g1)
    n = len('aabb')
    v = p.transitive_closure(my_A, my_P, n)
    print('parsed:', g1_start in v[0][n])

# ### Recognize
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
    result = p.recognize_on(txt, g1_start)
    print(result)
    print()
    txt = 'aabc'
    result = p.recognize_on(txt, g1_start)
    print(result)
    print()

    txt = 'aaabbb'
    result = p.recognize_on(txt, g1_start)
    print(result)
    print()

# ## ValiantParser
# **Note:** The **recognizer** works well, but the tree extraction is naive.
#   
# At this point, we have the *recognition matrix*. To make this into a true
# parser, similar to CYK, we can add back pointers. However, Ruzzo[^ruzzo1979on]
# showed that if we have the CYK or Valiant recognition matrix (both are same)
# we can extract a parse tree in at most $$ O(log(n))$$ slower than the recognizer.
# Here, we implement a naive algorithm that just shows how we can extract a
# single tree.
#  
# ### Extracting trees
# Unlike GLL, GLR, and Earley, and like
# CYK, due to restricting epsilons to the start symbol, there are no infinite
# parse trees. Furthermore, we only pick the first available tree. This can be
# trivially extended if needed.
#  
# The basic idea here is that, given a rule $$ S -> A B $$ that parsed text
# $$W$$, and we find $$S$$ in the recognition matrix, the nonterminal $$B$$ that
# helped in parsing $$W$$ has to be found in the same column as that of $$S$$.
# So, we look through the final column and generate a list of tuples where the
# tuple has the format `(idx, nonterminal)` where `idx` is the point where $$B$$
# started parsing from. At this point, if we look at the column `idx-1`, then at
# the top of the column (in 0th row) there has to be the nonterminal $$A$$ that
# is on the other side of the rule.

def find_breaks(table, sym, P):
    rules = [(l, (m, n)) for (l, (m, n)) in P if l == sym]
    # get the last column.
    if not table: return [] # terminal symbol
    m = len(table)
    last_column = [row[m-1] for row in table]
    assert sym in last_column[0]

    # Now, identify the index, and nonterminal
    tuples = []
    for idx, cell in enumerate(last_column):
        for k in cell: # cell is {k:true}*
            tuples.append((idx, k))
    # remove start symbol
    B_tuples = [(idx, k) for (idx,k) in tuples if k != sym or idx != 0]
    A_tuples = []
    for idx, B_k in B_tuples:
        B_rules = [(d, (l, r)) for d,(l,r) in rules if r == B_k]
        A_cell_ = table[0][idx]
        A_rules = [(idx, (l, r)) for d,(l,r) in B_rules if l in A_cell_]
        if A_rules: # we found a parse.
            A_tuples.extend(A_rules)

    return A_tuples

# Testing it
if __name__ == '__main__':
    print()
    t = find_breaks(v, g1_start, my_P)
    print(t)

# Incorporating the breaks in tree.

class ValiantParser(ValiantRecognizer):
    def extract_tree(self, table, sym, text):
        length = len(table)
        possible_breaks = find_breaks(table, sym, self.nonterminal_productions)
        if not possible_breaks: return [sym, [(text, [])]]
        c_j, (A_j, B_j) = random.choice(possible_breaks)

        l_table = [[table[i][j] for j in range(c_j+1)]
                   for i in range(c_j+1)]

        r_table = [[table[i][j] for j in range(c_j, length)]
                   for i in range(c_j, length)]

        l = self.extract_tree(l_table, A_j, text[0:c_j])

        r = self.extract_tree(r_table, B_j, text[c_j:])
        return [sym, [l, r]]

# ### Parse
# Adding the extract tree

class ValiantParser(ValiantParser):
    def parse_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        my_A = self.parse_1(text, length, table)
        my_P = self.nonterminal_productions
        ntable = self.transitive_closure(my_A, my_P, length)
        if start_symbol not in ntable[0][-1]: return []
        return [self.extract_tree(ntable, start_symbol, text)]

# Using it (uses random choice, click run multiple times to get other trees).
if __name__ == '__main__':
    mystring = 'aabb'
    p = ValiantParser(g1)
    v = p.parse_on(mystring, g1_start)
    for t in v:
        print(ep.display_tree(t))

# assign display_tree

def display_tree(t):
    return ep.display_tree(t)

# Let us do a final test

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
    v = p.parse_on(mystring, g2_start)
    for t in v:
        print(display_tree(t))


# [^valiant1975]: Leslie G. Valiant "General context-free recognition in less than cubic time" 1975
# [^ebert2006]: Franziska Ebert "CFG Parsing and Boolean Matrix Multiplication" 2006
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008
# [^ruzzo1979on]: Ruzzo, Walter L. "On the complexity of general context-free language parsing and recognition." 1979
