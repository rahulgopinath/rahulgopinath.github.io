# ---
# published: true
# title: Efficient Matching with Regular Expressions
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---
# 
# In the previous posts, I talked about converting a regular grammar to a
# deterministic regular grammar (DRG) equivalent to a DFA and mentioned that
# it was one of the ways to ensure that there is no exponential worstcase
# for regular expression matching. However, this is not the only way to
# avoid exponential worstcase due to backtracking for regular expressions.
# A possible solution is the [Thompson algorithm described here](https://swtch.com/~rsc/regexp/regexp1.html).
# The idea is that, rather than backtracking, for any given NFA, parallely
# track all possible threads. The idea here is that, for a given regular
# expression with size n, excluding parenthesis, an NFA with n states is
# sufficient to represent it. Furthermore, given n states in an NFA, one
# never needs to track more than n parallel threads while parsing. I
# recently found a rather elegant and tiny implementation of this in Python
# [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).
# This is an attempt to document my understanding of this code.
# 
# We start with importing the prerequisites

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import earleyparser

# Note my [post](/post/2020/03/02/combinatory-parsing/) on simple combinatory
# parsing. This construction is similar in spirit to that idea. The essential
# idea is that a given node should be able to accept or reject a given sequence
# of characters. So, let us take the simplest case: A literal such as `a`.
# We represent the literal by a function that accepts the character, and returns
# back a node in the NFA. The idea is that this NFA can accept or reject the
# remaining string. So, it needs a continuation, which is given as the next
# state. The NFA will continue with the next state only if the parsing of the
# current symbol succeeds. So we have an inner function `parse` that does that.

def Lit(char):
    def node(nxtstate):
        def parse(c: str):
            return [nxtstate] if char == c else []
        return parse
    return node

# An accepting node is a node that requires no input. It is a simple sentinel

accepting = Lit(None)('ACCEPT')

# Next, we define our matching algorithm. The idea is to start with the
# constructed NFA as the single thread, feed it our string, and check whether
# the result contains the accepted state.

def match(rex, instr):
    nfa = rex(accepting)
    states = [nfa]
    for c in instr:
        states = list(set([a for state in states for a in state(c)]))
    return any('ACCEPT' in state(None) for state in states)

# Let us test this.

if __name__ == '__main__':
    X = Lit('X')
    assert match(X, 'X')
    assert not match(X, 'Y')

# Next, we want to match two regular expressions. We define AndThen that
# sequences two regular expressions. The idea is to construct the NFA from the
# end, where we will connect `rex1() -> rex2() -> nxtstate`
# Note that we are constructing the NFA in the `node()` function.
# That is, the `node()` is given the next state to move
# into on successful parse (i.e `nxtstate`). We connect the nxtstate to the
# end of rex2 by passing it as an argument. The node rex2 is then connected to
# rex1 by passing the resultant state as the next state to rex1.
# The functions are expanded to make it easy to understand. The node may aswell
# have had rex1(rex2(nxtstate)) as the return value.

def AndThen(rex1, rex2):
    def node(nxtstate):
        state2 = rex2(nxtstate)
        state1 = rex1(state2)
        def parse(c: str):
            return state1(c)
        return parse
    return node

# Let us test this.

if __name__ == '__main__':
    Y = Lit('Y')
    XY = AndThen(X,Y)
    YX = AndThen(Y, X)
    assert match(XY,'XY')
    assert not match(YX, 'XY')

# Next, we want to match alternations. As before we define the node function,
# and inside it the parse function. The important point here is that we want to
# pass on the next state if either of the parses succeed.

def OrElse(rex1, rex2):
    def node(nxtstate):
        state1, state2 = rex1(nxtstate), rex2(nxtstate)
        def parse(c: str):
            return state1(c) + state2(c)
        return parse
    return node

# Let us test this.

if __name__ == '__main__':
    Z = Lit('Z')
    X_Y = OrElse(X,Y)
    Y_X = OrElse(X,Y)
    ZX_Y = AndThen(Z, OrElse(X,Y))
    assert match(X_Y, 'X')
    assert match(Y_X, 'Y')
    assert not match(X_Y, 'Z')
    assert match(ZX_Y, 'ZY')

# Finally, the Star is defined similar to OrElse. Note that unlike the context
# free grammar, we do not allow unrestricted recursion. We only allow tail
# recursion in the star form.

def Star(re):
    def node(nxtstate):
        def parse(c: str):
            return nxtstate(c) + re(parse)(c)
        return parse
    return node

# Let us test this.

if __name__ == '__main__':
    Z_ = Star(Lit('Z'))
    assert match(Z_, '')
    assert match(Z_, 'Z')
    assert not match(Z_, 'ZA')

# We also define an epsilon expression.

def Epsilon():
    def node(state):
        def parse(c: str):
            return state(c)
        return parse
    return node

# Let us test this.

if __name__ == '__main__':
    E__ = Epsilon()
    assert match(E__, '')

# We can have quite complicated expressions. Again, test suite from
# [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).

if __name__ == '__main__':
    complicated = AndThen(Star(OrElse(AndThen(Lit('a'), Lit('b')), AndThen(Lit('a'), AndThen(Lit('x'), Lit('y'))))), Lit('z'))
    assert not match(complicated, '')
    assert match(complicated, 'z')
    assert match(complicated, 'abz')
    assert not match(complicated, 'ababaxyab')
    assert match(complicated, 'ababaxyabz')
    assert not match(complicated, 'ababaxyaxz')


# What about constructing regular expression literals? For that let us start
# with a simplified grammar

import string

TERMINAL_SYMBOLS = list(string.digits +
                        string.ascii_letters)

RE_GRAMMAR = {
    '<start>' : [
        ['<regex>']
    ],
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
        ['<regexplus>'],
    ],
    '<unitexp>': [
        ['<alpha>'],
        ['<parenexp>'],
    ],
    '<parenexp>': [
        ['(', '<regex>', ')'],
    ],
    '<regexstar>': [
        ['<unitexp>', '*'],
    ],
    '<singlechars>': [
        ['<singlechar>', '<singlechars>'],
        ['<singlechar>'],
    ],
    '<singlechar>': [
        ['<char>'],
    ],
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
    assert match(l, 'a')

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
    assert match(l, 'ab')

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
    assert match(l, 'a')
    assert match(l, 'b')
    assert match(l, 'c')
    my_re = 'ab|c'
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    l = RegexToLiteral().convert_regex(parsed_expr)
    assert match(l, 'ab')
    assert match(l, 'c')
    assert not match(l, 'a')
    my_re = 'ab|'
    parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
    l = RegexToLiteral().convert_regex(parsed_expr)
    assert match(l, 'ab')
    assert match(l, '')
    assert not match(l, 'a')


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
    print(l)
    assert match(l, 'b')
    assert match(l, 'ab')
    assert not match(l, 'abb')
    assert match(l, 'aab')

#  Wrapping everything up.
class RegexToLiteral(RegexToLiteral):
    def match(self, re, instring):
        lit = self.to_re(re)
        return match(lit, instring)

# check it has worked
if __name__ == '__main__':
    my_re = 'a*b'
    assert RegexToLiteral().match(my_re, 'ab')

# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).
#  
