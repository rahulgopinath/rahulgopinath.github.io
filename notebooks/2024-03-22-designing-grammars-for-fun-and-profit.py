# ---
# published: true
# title: Building Grammars for Fun and Profit
# layout: post
# comments: true
# tags: grammars peg
# categories: post
# ---
# 
# TLDR; This tutorial takes you through the steps to write a
# simple context-free grammmar that can parse your custom data format.
# The Python interpreter is embedded so that you
# can work through the implementation steps.
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
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
#   in the grammar using _rules_ for expansion.
#
#   For example, `<term>` is a nonterminal symbol.
#
# * A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
#   nonterminals) that describe an expansion of a given terminal.
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

# Say you are designing a custom data format. You use this format to
# parse data from your clients or customers who are required to provide
# the data in the language you have designed. You will come across this
# requirement whenever you have a system that interacts with human beings.
# In most cases, you may be able to manage with simple well defined
# formats such as comma-sepaated values, XML or JSON. However, there may
# be cases where the customers may want something that is closer to their
# domain. In such cases, what is the best way forward? This is what this
# post will explore.
#  
# Designing a grammar can be intimidating at first, particularly if you
# have gone through one of the traditional compiler design and implementation
# courses in the university. In this post, I will attempt to convince you that
# formal grammars can be much more easier to write and work with. Furthermore,
# parsing with them can be far simpler than writing your own recursive descent
# parser from scratch, and far more secure.
#  
# The idea we explore in this post is that, rather than starting with a parser,
# a better alternative is to start with a generator (a grammar fuzzer) instead.
# 
# ## Grammar for Regular Expressions
#  
# As an example, let us say that you are building a grammar for simple 
# regular expressions. We take the simplest regular expression possible
# A single character. Let us build a generator for such simple regular
# expressions. We will return a derivation tree as the result.

import string, random

def gen_regex():
    return ('regex', [gen_alpha()])

def gen_alpha():
    return ('alpha', [(random.choice([c for c in string.printable if c not in '|*()']), [])])

# This works as expected
if __name__ == '__main__':
    t = gen_regex()

# We define a function to collapse the derivation tree

def collapse(tree):
    key, children = tree
    if not children: return key
    return ''.join([collapse(c) for c in children])

# Using it
if __name__ == '__main__':
    print(repr(collapse(t)))

# So let us try to extend our implementation  a little bit. A regular expression is not
# just a single character. It can be any number of such characters, or sequence
# of subexpressions. So, let us define that.

def gen_regex():
    return ('regex', [gen_cex()])

def gen_cex():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_alpha(), gen_cex()])
    if r == 1: return ('cex', [gen_alpha()])

def gen_alpha():
    return ('alpha', [(random.choice([c for c in string.printable if c not in '|*()']), [])])

# This again works as expected.
if __name__ == '__main__':
    t = gen_regex()
    print(repr(collapse(t)))

# Regular expressions allow one to specify alternative matching with the pipe
# symbol. That is `a|b` matches either `a` or `b`. So, let us define that.

def gen_regex():
    return ('regex', [gen_exp()])
    
def gen_exp():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_cex(), ('|', []), gen_exp()])
    if r == 1: return ('cex', [gen_cex()])

# This again works as expected.

if __name__ == '__main__':
    t = gen_regex()
    print(repr(collapse(t)))

# Next, we will implement parenthesized expressions. That is,
# `(a|b)` is a parenthesized expression that matches either `a`
# or `b`, and is considered one single expression for any meta
# character that comes after.

def gen_cex():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_unitexp(), gen_cex()])
    if r == 1: return ('cex', [gen_unitexp()])

# symmetric probabilities will exhaust the stack. So, use this
# trick to avoid that instead.

def gen_unitexp():
    r = random.randint(0,9)
    if r in [1,2,3,4,5,6,7,8,9]: return ('unitexp', [gen_alpha()])
    if r == 0: return ('unitexp', [gen_parenexp()])

def gen_parenexp():
    return ('parenexp', [('(', []), gen_regex() ,(')', [])])

# Testing it again.
if __name__ == '__main__':
    print(gen_regex())

# All that remains is to define the kleene star `*` for zero or
# more repetitions

def gen_regex():
    return ('regex', [gen_rex()])

def gen_rex():
    r = random.randint(0,1)
    if r == 0: return ('rex', [gen_exp(), ('*', [])])
    if r == 1: return ('rex', [gen_exp()])

# Testing it again.
if __name__ == '__main__':
    print(gen_regex())

# At this point, you would have a fully explored test generator that is ready to
# test any parser you would write, and can be improved upon for any extensions
# you might want. More importantly, you can easily convert the generator you
# wrote to a grammar for your data format. That is, each subroutine name
# become the name of a nonterminal symbol.
# 
# E.g. `gen_cex()` to `<cex>`
# 
# The branches (match) become rule alternatives:
# 
# E.g. `<uniexp>: [[<alpha>], [<parenexp>]]`
# 
# Sequence of procedure calls become sequences in a rule.
# 
# E.g. <parenexp>: [['(', <regex>, ')']] 
# 
# With these steps, we have the following grammar.

regex_grammar = {
    '<gen_regex>': [['<gen_rex>']],
    '<gen_rex>': [
        ['<gen_exp>', '*'],
        ['<gen_exp>']],
    '<gen_exp>': [
        ['<gen_cex>', '|', '<gen_exp>'],
        ['<gen_cex>']],
    '<gen_cex>': [
        ['<gen_unitexp>', '<gen_cex>'],
        ['<gen_unitexp>']],
    '<gen_unitexp>': [
        ['<gen_parenexp>'],
        ['<gen_alpha>']],
    '<gen_parenexp>': [
        ['(', '<gen_regex>', ')']],
    '<gen_alpha>': [[c] for c in string.printable if c not in '|*()']
}

regex_start = '<gen_regex>'

# We can now use it to parse regular expressions. Using our previously
# defined PEG parser,
import functools
class peg_parse:
    def __init__(self, grammar): self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            if text[at:].startswith(key):
                return (at + len(key), (key, []))
            else:
                return (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

# Using it
if __name__ == '__main__': 
    inrex = '(ab|cb)*d'
    print()
    f, r = peg_parse(regex_grammar).unify_key(regex_start, inrex)
    print(repr(collapse(r)), "<")

# However, there are some caveats to the grammars thus produced.
# The main caveat is that you have to be careful in how you order your rules.
# In general, build your language such that the first token produced by each of
# your rules for the same definition is different.
# This will give you LL(1) grammars, which are the easiest to use.
# 
# If the above rule can't be adhered to, and if you have two rules such that the
# match of one will be a subsequence of another, order the rules in grammar such
# that the longest match always comes first.
# 
# For example,
# ```
#  <exp> := <cex> '|' <exp>
#         | <exp>
# ```
# or equivalently
# ```
# '<exp>' : [['<cex>', '|', '<exp>'], ['<exp>']] 
# ```
# Such kind of grammars are called Parsing Expression Grammars. The idea is that
# the first rule is given priority over the other rules, and hence longest
# matching rule should come first.
