# ---
# published: true
# title: Efficient Matching with Regular Expressions
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---

# In the previous posts, I talked about converting a regular grammar to a
# deterministic regular grammar (DRG) equivalent to a DFA and mentioned that
# it was one of the ways to ensure that there is no exponential wort-case
# for regular expression matching. However, this is not the only way to
# avoid exponential worst-case due to backtracking in regular expressions.
# A possible solution is the [Thompson algorithm described here](https://swtch.com/~rsc/regexp/regexp1.html).
# The idea is that, rather than backtracking, for any given NFA,
# track all possible threads in parallel. This raises a question. Is the number
# of such parallel threads bounded?
# 
# Given a regular expression with size n, excluding parenthesis,
# can be represented by an NFA with n states. Furthermore, any given parsing
# thread can contain no information other than the current node.
# That is, for an NFA with n states one
# never needs to track more than n parallel threads while parsing.
# I recently found a rather elegant and tiny implementation of this in Python
# [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).
# This is an attempt to document my understanding of this code.
#  
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import earleyparser

# ## Functional Implementation
# 
# Here is the Python implementation from [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py)
# slightly modified to look similar to my [post](/post/2020/03/02/combinatory-parsing/)
# on simple combinatory parsing. I also name the anonymous lambdas to make it
# easier to understand.
#  
# The basic idea is to first construct the NFA processing graph, then let the
# string processing take place through the graph. Each node (state in NFA) in
# the graph requires no more information than the nodes to transition to on
# given input tokens to accept or reject the remaining string. This is leveraged
# in the match function below, where based on the current input token, all the
# states are queried to identify the next state. The main point of the NFA is
# that we need to maintain at most `n` states in our processing list at any time
# where n is the number of nodes in the NFA. That is, for each input symbol, we
# have a constant number of states to query.
# 
# The most important thing to understand in this algorithm for NFA graph
# construction is that we start the construction from the end, that is the
# accepting state. Then, as each node is constructed, new node is linked to
# next nodes in processing. The second most important thing to understand this
# algorithm for regular expression matching is that, each node represents the
# starting state for the remaining string. That is, we can query next nodes to
# check if the current remaining string will be accepted or rejected.
# 
# ### Match

def match(rex, input_tokens):
    states = {rex(accepting)}
    for token in input_tokens:
        states = {a for state in states for a in state(token)}
    return any('ACCEPT' in state(None) for state in states)

# Next, we build our NFA graph.
# 
# ### Lit
# Let us take the simplest case: A literal such as `a`.
# We represent the literal by a function that accepts the character, and returns
# back a state in the NFA. The idea is that this NFA can accept or reject the
# remaining string. So, it needs a continuation, which is given as the next
# state. The NFA will continue with the next state only if the parsing of the
# current symbol succeeds. So we have an inner function `parse` that does that.

def Lit(token):
    def node(rnfa):
        def parse(c: str): return [rnfa] if token == c else []
        return parse
    return node

# An accepting state is just a sentinel, and we define it with `Lit`.

accepting = Lit(None)('ACCEPT')

# ### Epsilon
# 
# An epsilon matches nothing. That is, it passes any string it receives
# without modification to the next state.
# (It could also be written as `lambda s: return s`)

def Epsilon():
    def node(state):
        def parse(c: str): return state(c)
        return parse
    return node


# ### AndThen
# 
# AndThen is a meta construction that concatenates two regular expressions.
# It accepts the given string if the given regular expressions (`rex1`, `rex2`)
# accepts the given string when placed end to end.
# The `rnfa` is the node to connect to after nodes represented by
# `rex1 -> rex2`.
# That is, the final NFA should look like `[rex1]->[rex2]->rnfa`.
# 
# Note: I use a `[]` to represent a node, and no `[]` when I specify the
# remaining NFA. For example, `[xxx]` represents the node in the NFA, while
# `xxx` is the NFA starting with the node `xxx`
# 
#  
# From the perspective of the node `[rex1]`, it can accept the remaining string
# if its own matching succeeds on the given string and the remaining string can
# be matched by the NFA `rex2(rnfa)` i.e, the NFA produced by calling `rex2`
# with argument `rnfa`. That is, `[rex1]->rex2(rnfa)`,
# which is same as `rex1(rex2(rnfa))` --- the NFA constructed by calling the
# function sequence `rex1(rex2(rnfa))`.
#  
# The functions are expanded to make it easy to understand. The node may as well
# have had `rex1(rex2(rnfa))` as the return value.

def AndThen(rex1, rex2):
    def node(rnfa):
        state1 = rex1(rex2(rnfa))
        def parse(c: str): return state1(c)
        return parse
    return node

# ### OrElse
# 
# The OrElse construction allows either one of the regular expressions to
# match the given symbol. That is, we are trying to represent parallel
# processing of `[rex1] -> rnfa || [rex2] -> rnfa`, or equivalently
# `rex1(rnfa) || rex2(rnfa)`.

def OrElse(rex1, rex2):
    def node(rnfa):
        state1, state2 = rex1(rnfa), rex2(rnfa)
        def parse(c: str): return state1(c) + state2(c)
        return parse
    return node

# ### Star
#
# Finally, the Star is defined similar to OrElse. Note that unlike the context
# free grammar, we do not allow unrestricted recursion. We only allow tail
# recursion in the star form.
# In Star, we are trying to represent
# `rnfa || [rex] -> [Star(rex)] -> rnfa`.
# Since the `parse` is a function that closes
# over the passed in `rex` and `rnfa`, we can use that directly. That is
# `Star(rex)(rnfa) == parse`. Hence, this becomes 
# `rnfa || [rex] -> parse`, which is written equivalently as
# `rnfa || rex(parse)`.

def Star(rex):
    def node(rnfa):
        def parse(c: str): return rnfa(c) + rex(parse)(c)
        return parse
    return node

# Let us test this.

if __name__ == '__main__':
    X = Lit('X')
    Y = Lit('Y')
    Z = Lit('Z')
    X_Y = OrElse(X,Y)
    Y_X = OrElse(X,Y)
    ZX_Y = AndThen(Z, OrElse(X,Y))
    assert match(Star(X), '')
    assert match(Star(X), 'X')
    assert match(Star(X), 'XX')
    assert not match(Star(X), 'XY')
    assert not match(X, 'XY')
    assert match(X_Y, 'X')
    assert match(Y_X, 'Y')
    assert not match(X_Y, 'Z')
    assert match(ZX_Y, 'ZY')
    Z_XY_XY = AndThen(Z, Star(AndThen(X,Y)))
    assert not match(X, 'XY')
    assert match(X_Y, 'X')
    assert match(Y_X, 'Y')
    assert not match(X_Y, 'Z')
    assert match(ZX_Y, 'ZY')
    assert match(Z_XY_XY, 'Z')
    assert match(Z_XY_XY, 'ZXY')
    assert match(Z_XY_XY, 'ZXYXY')


# In the interest of code golfing, here is how to compress it. We use the
# self application combinator `mkrec`, and use `mkrec(lambda _: ... _(_) ...)`
# pattern

def lit_(token): return lambda nfa: lambda c: [nfa] if token == c else []
def epsilon_(): return lambda state: state
def andthen_(rex1, rex2): return lambda nfa: rex1(rex2(nfa))
def orelse_(re1, re2): return lambda nfa: lambda c: re1(nfa)(c)+ re2(nfa)(c)
def mkrec(f): return f(f)
def star_(r): return lambda nfa: mkrec(lambda _: lambda c: nfa(c) + r(_(_))(c))

def match_(rex, ts, states = None):
    if states is None: states = {rex(lit_(None)('ACCEPT'))}
    if not ts: return any('ACCEPT' in state(None) for state in states)
    return match_(rex, ts[1:], {a for state in states for a in state(ts[0])})

# Testing it out
if __name__ == '__main__':
    X = lit_('X')
    Y = lit_('Y')
    Z = lit_('Z')
    assert match_(star_(X), '')
    assert match_(star_(X), 'X')
    assert match_(star_(X), 'XX')
    assert not match_(star_(X), 'XY')
    X_Y = orelse_(X,Y)
    Y_X = orelse_(X,Y)
    ZX_Y = andthen_(Z, orelse_(X,Y))
    Z_XY_XY = andthen_(Z, star_(andthen_(X,Y)))
    assert not match_(X, 'XY')
    assert match_(X_Y, 'X')
    assert match_(Y_X, 'Y')
    assert not match_(X_Y, 'Z')
    assert match_(ZX_Y, 'ZY')
    assert match_(Z_XY_XY, 'Z')
    assert match_(Z_XY_XY, 'ZXY')
    assert match_(Z_XY_XY, 'ZXYXY')

# ## Easier Regular Literals
# Typing constructors such as Lit every time you want to match a single token
# is not very friendly. Can we make them a bit better?

def easier_re(expr):
    if isinstance(expr, str):
        return Lit(expr)
    elif isinstance(expr, list):
        e, *expr = expr
        rex = easier_re(e)
        while expr:
            e, *expr = expr
            rex = AndThen(rex, easier_re(e))
        return rex
    elif isinstance(expr, tuple):
        e, *expr = expr
        rex = easier_re(e)
        while expr:
            e, *expr = expr
            rex = OrElse(rex, easier_re(e))
        return rex
    elif isinstance(expr, dict):
        e, *expr = list(expr.items())
        assert e[0] == '*'
        rex = Star(easier_re(e[1]))
        return rex

# Using it.
if __name__ == '__main__':
    complicated = easier_re([{'*': (['a','b'], ['a','x','y'])}, 'z'])
    print(repr(complicated))
    assert not match(complicated, '')
    assert match(complicated, 'z')
    assert match(complicated, 'abz')
    assert not match(complicated, 'ababaxyab')
    assert match(complicated, 'ababaxyabz')
    assert not match(complicated, 'ababaxyaxz')



# ## Object Based Implementation
# 
# This machinery is a bit complex to understand due to the multiple levels of
# closures. I have found such constructions easier to understand if I think of
# them in terms of objects. So, here is an attempt.
# First, the Re class that defines the interface.

class Re:
    def trans(self, rnfa): pass
    def parse(self, c: str): pass

# ### Match
# The match is slightly modified to account for the new Re interface.

class Re(Re):
    def match(self, instr):
        states = {self.trans(accepting)}
        for c in instr:
            states = {a for state in states for a in state.parse(c)}
        return any('ACCEPT' in state.parse(None) for state in states)

# ### Lit
# We separate out the construction of object, connecting it to the remaining
# NFA (`trans`)

class Lit(Re):
    def __init__(self, char): self.char = char
    
    def __repr__(self): return self.char

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return [self.rnfa] if self.char == c else []

# An accepting node is a node that requires no input. It is a simple sentinel

accepting = Lit(None).trans('ACCEPT')

# Next, we define our matching algorithm. The idea is to start with the
# constructed NFA as the single thread, feed it our string, and check whether
# the result contains the accepted state.

# Let us test this.

if __name__ == '__main__':
    X = Lit('X')
    assert X.match('X')
    assert not X.match('Y')

# ### AndThen

class AndThen(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def __repr__(self): return "(%s)" % ''.join([repr(self.rex1), repr(self.rex2)])

    def trans(self, rnfa):
        state2 = self.rex2.trans(rnfa)
        self.state1 = self.rex1.trans(state2)
        return self

    def parse(self, c: str):
        return self.state1.parse(c)

# Let us test this.

if __name__ == '__main__':
    Y = Lit('Y')
    XY = AndThen(X,Y)
    YX = AndThen(Y, X)
    assert XY.match('XY')
    assert not YX.match('XY')

# ### OrElse
# 
# Next, we want to match alternations.
# The important point here is that we want to
# pass on the next state if either of the parses succeed.

class OrElse(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def __repr__(self): return "%s" % ('|'.join([repr(self.rex1), repr(self.rex2)]))

    def trans(self, rnfa):
        self.state1, self.state2 = self.rex1.trans(rnfa), self.rex2.trans(rnfa)
        return self

    def parse(self, c: str):
        return self.state1.parse(c) + self.state2.parse(c)

# Let us test this.

if __name__ == '__main__':
    Z = Lit('Z')
    X_Y = OrElse(X,Y)
    Y_X = OrElse(X,Y)
    ZX_Y = AndThen(Z, OrElse(X,Y))
    assert X_Y.match('X')
    assert Y_X.match('Y')
    assert not X_Y.match('Z')
    assert ZX_Y.match('ZY')

# ### Star
# Star now becomes much easier to understand.

class Star(Re):
    def __init__(self, re): self.re = re

    def __repr__(self): return "(%s)*" % repr(self.re)

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return self.rnfa.parse(c) + self.re.trans(self).parse(c)

# Let us test this.

if __name__ == '__main__':
    Z_ = Star(Lit('Z'))
    assert Z_.match('')
    assert Z_.match('Z')
    assert not Z_.match('ZA')

# ### Epsilon
# 
# We also define an epsilon expression.

class Epsilon(Re):
    def trans(self, state):
        self.state = state
        return self

    def parse(self, c: str):
        return self.state.parse(c)

# Let us test this.

if __name__ == '__main__':
    E__ = Epsilon()
    assert E__.match('')

# We can have quite complicated expressions. Again, test suite from
# [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).

if __name__ == '__main__':
    complicated = AndThen(Star(OrElse(AndThen(Lit('a'), Lit('b')), AndThen(Lit('a'), AndThen(Lit('x'), Lit('y'))))), Lit('z'))
    assert not complicated.match('')
    assert complicated.match('z')
    assert complicated.match('abz')
    assert not complicated.match('ababaxyab')
    assert complicated.match('ababaxyabz')
    assert not complicated.match('ababaxyaxz')

    # Note: (|a)* causes pathological behavior, a problem with Thompsons matchers.
    pathological = Star(OrElse(Epsilon(), Lit('a')))
    # assert pathological.match('a')

# ## Parser

# What about constructing regular expression literals? For that let us start
# with a simplified grammar

import string

TERMINAL_SYMBOLS = list(string.digits +
                        string.ascii_letters)

RE_GRAMMAR = {
    '<start>' : [ ['<regex>'] ],
    '<regex>' : [
        ['<cex>', '|', '<regex>'],
        ['<cex>', '|'],
        ['<cex>']
    ],
    '<cex>' : [
        ['<exp>', '<cex>'],
        ['<exp>']
    ],
    '<exp>': [
        ['<unitexp>'],
        ['<regexstar>'],
    ],
    '<unitexp>': [
        ['<alpha>'],
        ['<parenexp>'],
    ],
    '<parenexp>': [ ['(', '<regex>', ')'], ],
    '<regexstar>': [ ['<unitexp>', '*'], ],
    '<alpha>' : [[c] for c in TERMINAL_SYMBOLS]
}
RE_START = '<start>'

# This is ofcourse a very limited grammar that only supports basic
# regular expression operations concatenation, alternation, and star.
# We can use earley parser for parsing any given regular expressions

if __name__ == '__main__':
    my_re = '(ab|c)*'
    re_parser = earleyparser.EarleyParser(RE_GRAMMAR)
    parsed_expr = list(re_parser.parse_on(my_re, RE_START))[0]
    fuzzer.display_tree(parsed_expr)

# Let us define the basic machinary. The parse function parses
# the regexp string to an AST, and to_re converts the AST
# to the regexp structure.
class RegexToLiteral:
    def __init__(self, all_terminal_symbols=TERMINAL_SYMBOLS):
        self.parser = earleyparser.EarleyParser(RE_GRAMMAR)
        self.counter = 0
        self.all_terminal_symbols = all_terminal_symbols

    def parse(self, inex):
        parsed_expr = list(self.parser.parse_on(inex, RE_START))[0]
        return parsed_expr

    def to_re(self, inex):
        parsed = self.parse(inex)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        lit = self.convert_regex(children[0])
        return lit

# The unit expression may e an alpha or a parenthesised expression.

class RegexToLiteral(RegexToLiteral):
    def convert_unitexp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<alpha>':
            return self.convert_alpha(children[0])
        elif key == '<parenexp>':
            return self.convert_regexparen(children[0])
        else:
            assert False
        assert False

# The alpha gets converted to a Lit.

class RegexToLiteral(RegexToLiteral):
    def convert_alpha(self, node):
        key, children = node
        assert key == '<alpha>'
        return Lit(children[0][0])

# check it has worked

if __name__ == '__main__':
    my_re = 'a'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    l = RegexToLiteral().convert_unitexp(parsed_expr)
    print(l)
    assert l.match('a')

# Next, we write the exp and cex conversions. cex gets turned into AndThen

class RegexToLiteral(RegexToLiteral):
    def convert_exp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<unitexp>':
            return self.convert_unitexp(children[0])
        elif key == '<regexstar>':
            return self.convert_regexstar(children[0])
        else:
            assert False
        assert False

    def convert_cex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_exp(child)
        if children:
            child, *children = children
            lit2 = self.convert_cex(child)
            lit = AndThen(lit,lit2)
        return lit

# check it has worked
if __name__ == '__main__':
    my_re = 'ab'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<cex>'))[0]
    fuzzer.display_tree(parsed_expr)
    l = RegexToLiteral().convert_cex(parsed_expr)
    print(l)
    assert l.match('ab')

#  Next, we write the regex, which gets converted to OrElse

class RegexToLiteral(RegexToLiteral):
    def convert_regexparen(self, node):
        key, children = node
        assert len(children) == 3
        return self.convert_regex(children[1])

    def convert_regex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_cex(child)
        if children:
            if len(children) == 1: # epsilon
                assert children[0][0] == '|'
                lit = OrElse(lit, Epsilon()) 
            else:
                pipe, child, *children = children
                assert pipe[0] == '|'
                lit2 = self.convert_regex(child)
                lit = OrElse(lit, lit2) 
        return lit

# check it has worked
if __name__ == '__main__':
    my_re = 'a|b|c'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    fuzzer.display_tree(parsed_expr)
    l = RegexToLiteral().convert_regex(parsed_expr)
    print(l)
    assert l.match('a')
    assert l.match('b')
    assert l.match('c')
    my_re = 'ab|c'
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    l = RegexToLiteral().convert_regex(parsed_expr)
    assert l.match('ab')
    assert l.match('c')
    assert not l.match('a')
    my_re = 'ab|'
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    l = RegexToLiteral().convert_regex(parsed_expr)
    assert l.match('ab')
    assert l.match('')
    assert not l.match('a')


# Finally the Star.

class RegexToLiteral(RegexToLiteral):
    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        lit = self.convert_unitexp(children[0])
        return Star(lit)

# check it has worked
if __name__ == '__main__':
    my_re = 'a*b'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    fuzzer.display_tree(parsed_expr)
    l = RegexToLiteral().convert_regex(parsed_expr)
    assert l.match('b')
    assert l.match('ab')
    assert not l.match('abb')
    assert l.match('aab')

#  Wrapping everything up.
class RegexToLiteral(RegexToLiteral):
    def __init__(self, rex, all_terminal_symbols=TERMINAL_SYMBOLS):
        self.parser = earleyparser.EarleyParser(RE_GRAMMAR)
        self.counter = 0
        self.all_terminal_symbols = all_terminal_symbols
        self.lit = self.to_re(rex)

    def match(self, instring):
        return self.lit.match(instring)

# check it has worked
if __name__ == '__main__':
    my_re = RegexToLiteral('a*b')
    assert my_re.match('ab')

# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).
#  
