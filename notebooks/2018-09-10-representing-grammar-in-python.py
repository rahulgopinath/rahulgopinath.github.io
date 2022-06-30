# ---
# published: true
# title: Representing a Grammar in Python
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---
# 
# In the [previous](/post/2018/09/05/top-down-parsing/) [posts](/post/2018/09/06/peg-parsing/), I described how can write a parser. For doing that, I made use of a grammar written as a python data structure, with the assumption that it can be loaded as a JSON file if necessary. The grammar looks like this:

term_grammar = {
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],

        ['<term>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [[str(i)] for i in range(10)],
}

# However, this is somewhat unsatisfying. There are too many distracting syntactic elements in the code, making it difficult to see where each elements are. What we want is a better representation. Indeed, one better representation is to lose one level of nesting, and instead, parse the string for terminals and non-terminals. The following representation uses a single string for a single rule, and a list for all alternative rules for a key.

term_grammar = {
    '<expr>': ['<term> + <expr}', '<term> - <expr>', '<term>'],
    '<term>': ['<fact> * <fact}', '<fact> / <fact>', '<fact>'],
    '<fact>': ['<digits>','(<expr>)'],
    '<digits>': ['{digit}{digits}','{digit}'],
    '<digit>': [str(i) for i in range(10)],
}

# But is there a better way? Ideally, one would like to define the grammar like one defines the class, so that it feels part of the language.

# One mechanism we can (ab)use is the type annotations. Specifically in `Python 3.7` one can use the postponed evaluation of annotations to accomplish a DSL as below, with grammar keys as attributes of the Grammar class.
#
# ```python
# class expr(Grammar):
#     start: '<expr>'
#     expr: '<term> + <term>' | '<term> - <term>'
#     term: '<factor} * <term>' | '<factor> / <term>'
#     factor: '( <expr> )' | '<integer>'
#     integer: '<digit> <integer}' | '<digit>'
#     digit: '0' | '1' | '2'
#
# ```
# The annotations lets us access the types of each class as a string, that can be evaluated separately. The `Grammar` class is defined as follows:

import string
import ast
import re

RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')

class Grammar:
    def alternatives(self, k):
        def strings(v):
            if isinstance(v, ast.BinOp):
                return [self._parse_rule(v.right.s)] + strings(v.left) 
            else: return [self._parse_rule(v.s)]
        return strings(ast.parse(self.rules(k[1:-1]), mode='eval').body)

    def _parse_rule(self, rule):
        return [token for token in re.split(RE_NONTERMINAL, rule) if token]

    def rules(self, k):
        return self.__annotations__[k]

    def keys(self):
        return ['<%s>' % k for k in self.__annotations__.keys()]

# Unfortunately, to be able to use the annotation feature,
# we need to place import `from __future__ import annotations` at the top of the
# file. So, while we can do that in practice, it is difficult to do that in this
# blog post form. Hence, I put the contents of my grammar into a string, and
# evaluate that string instead.

if __name__ == '__main__':
    s = """
from __future__ import annotations

class expr(Grammar):
    start: '<expr>'
    expr: '<term> + <term>' | '<term> - <term>'
    term: '<factor> * <term>' | '<factor> / <term>'
    factor: '( <expr> )' | '<integer>'
    integer: '<digit> <integer>' | '<digit>'
    digit: '0' | '1' | '2'
"""
    exec(s)

# Given all this, to print the grammar in a readable form is simply:
if __name__ == '__main__':
    e = expr()
    for i in e.keys():
        print(i, "::= ")
        for alt in  e.alternatives(i):
            print("\t| %s\t\t" % alt)

# We need to make our grammar available in the standard format. So, let us
# define such an accessor.

class Grammar(Grammar):
    @classmethod
    def create(cls, grammar=None, start=None):
        slf = cls()
        my_grammar = {k:[alt for alt in slf.alternatives(k)]
                for k in slf.keys()}
        my_grammar = slf.update(my_grammar, grammar, start)
        slf.grammar = my_grammar
        if start is not None:
            slf.start = start
        return slf

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        return {**my_grammar, **grammar}
# Using
if __name__ == '__main__':
    exec(s) 
    e = expr.create()
    print(e.grammar)

# This works well. Let us extend our grammar with a few convenience methods.
# For example, we want to specify separate processing if the nonterminal starts
# with a meta character such as `+`, `*`, `$` or `@`.
# We define any nonterminal that starts with `*` to mean zero or more of its
# nonterminal without the meta character.

class Grammar(Grammar):
    def is_nonterminal(self, k):
        return (k[0], k[-1]) == ('<', '>')

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        new_g = {**my_grammar, **grammar}
        new_keys = set()
        for k in new_g:
            for alt in new_g[k]:
                for t in alt:
                    if self.is_nonterminal(t) and t[1] in '+*$@':
                        new_keys.add(t)

        for k in new_keys:
            if k[1] == '*':
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], []]
            elif  k[1] == '+':
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], [ok]]

        return new_g

# Usage
if __name__ == '__main__':
    s = """
from __future__ import annotations

class expr(Grammar):
    start: '<expr>'
    expr: '<term> + <term>' | '<term> - <term>'
    term: '<factor> * <term>' | '<factor> / <term>'
    factor: '( <expr> )' | '<integer>'
    integer: '<*digit>'
    digit: '0' | '1' | '2'
"""

    exec(s) 
    e = expr.create()
    print(e.grammar)

