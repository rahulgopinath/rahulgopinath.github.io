# ---
# published: false
# title: CYK Parser
# layout: post
# comments: true
# tags: parsing, gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of CYK Parser in Python[^grune2008parsing]
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#  
# A CYK parser is a general context-free parser. 
# It uses dynamic # programming to fill in a chart. Unlike Earley, GLL and GLR
# parsers, it requires the grammar to be in the Chomsky normal form, which
# allows at most two symbols on the right hand side of any production.
# In particular, all the rules have to conform to
#
# $$ A -> BC $$
# $$ A -> a $$
# $$ S -> \epsilon $$
#
# Where A,B, and C are nonterminal symbols, a is a terminal symbol, S is the
# start symbol, and $\epsilon$ is the empty string.
#  
# We [previously discussed](/post/2021/02/06/earley-parsing/) 
# Earley parser which is a general context-free parser. CYK
# parser is another general context-free parser that is capable of parsing
# strings that conform to **any** given context-free grammar.
#  
# Similar to Earley, GLR, GLL, and other general context-free parsers, the worst
# case for CYK parsing is $$ O(n^3) $$ . However, unlike those parsers, the best
# case is also $$ O(n^3) $$ for all grammars.
#  
# ## Synopsis
#
# ```python
# import cykparser as P
# my_grammar = {'<start>': [['1', '<A>'],
#                           ['2']
#                          ],
#               '<A>'    : [['a']]}
# my_parser = P.compile_grammar(my_grammar)
# for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
#     print(P.format_parsetree(tree))
# ```

# ## Definitions
# For this post, we use the following terms:
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

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities
import simplefuzzer as fuzzer
# We use the `display_tree()` method in earley parser for displaying trees.
import earleyparser as ep

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
          ['<A>', '<B>'],
          ['<B>', '<C>'],
          ['c']],
   '<A>': [
        ['a']],
   '<B>': [
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

class CYKParser(ep.Parser):
    def __init__(self, grammar, log=True):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.terminal_productions = [(k,r[0]) for (k,r) in self.productions if fuzzer.is_terminal(r[0])]
        self.nonterminal_productions = [(k,r) for (k,r) in self.productions if not fuzzer.is_terminal(r[0])]

    def recognize_on(self, text, start_symbol):
        length = len(text)
        # table[i][j] represents the substring[i..j]
        self.table = [[{} for i in range(length+1)] for j in range(length+1)]

        for s in range(0,length):
            for (key, terminal) in self.terminal_productions: # rule R_a -> c:
                if text[s] == terminal:
                    self.table[s][s+1][key] = True

        for l in range(2,length+1): #l is the length of the sub-string
            # check substrings starting at s, with length l
            for s in range(0,length-l+1):
                # partition the substring at p (l = 1 less than the length of substring)
                for p in range(1, l):
                    for (k, [R_b, R_c]) in self.nonterminal_productions: # R_a -> R_b R_c:
                        if R_b in self.table[s][p] :
                            if R_c in self.table[s+p][s+l]: #l - p - 1
                                self.table[s][s+l][k] = True

        return start_symbol in self.table[0][-1]

# ## A few more examples
if __name__ == '__main__':
    mystring = 'bc'
    p = CYKParser(g1)
    v = p.recognize_on(mystring, '<S>')
    print(v)

# We assign format parse tree so that we can refer to it from this module

def format_parsetree(t):
    return ep.format_parsetree(t)

# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

