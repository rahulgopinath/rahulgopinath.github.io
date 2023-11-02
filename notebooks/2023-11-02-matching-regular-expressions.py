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

# The imported modules

import simplefuzzer as fuzzer

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

# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-02-matching-regular-expressions.py).
#  
