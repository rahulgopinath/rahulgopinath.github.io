# ---
# published: true
# title: Simple Combinatory Parsing For Context Free Languages
# layout: post
# comments: true
# tags: combinators, parsing, cfg
# categories: post
# ---
  
# Combinatory parsing (i.e parsing with [combinators](https://en.wikipedia.org/wiki/Combinatory_logic)) was
# introduced by William H Burge in his seminal work
# [Recursive Programming Techniques -- The systems programming series](https://archive.org/details/recursiveprogram0000burg)
# in 1975. (It was called _Parsing Relations_ in that book. See page 174).
# Unfortunately, it took until 2001 for the arrival of [Parsec](/references/#leijen2001parsec), and for combinatory
# programming to be noticed by the wider world.
# 
# While Parsec is a pretty good library, it is often hard to understand for
# programmers who are not familiar with Haskell. So, the question is, can
# one explain the concept of simple combinatory parsing without delving to
# Haskell and Monads? Here is my attempt.
# 
# The idea of combinatory parsing is really simple. We start with the smallest
# parsers that do some work --- parsing single characters, then figure out how
# to combine them to produce larger and larger parsers.
# 
# Note that since we are dealing with context-free parsers, ambiguity in parsing
# is a part of life. Hence, we have to keep a list of possible parses at all
# times. A failure to parse is then naturally represented by an empty list, and
# a single parse item is a tuple that contains the remaining input as the first
# element, and the parse result as the second.
# This particular approach was pioneered by [Wadler](https://homepages.inf.ed.ac.uk/wadler/papers/marktoberdorf/baastad.pdf).
# 
# So, here, we start with the basic parser -- one that parses a single character
# `a`.  The return values are as expected --- a single empty list for failure to
# parse and a list of parses (a single element here because there is only one way
# to parse `a`).

def parse(instr):
    if instr and instr[0] == 'a':
       return [(instr[1:], ['a'])] 
    return []

# While this is a good start, we do not want to rewrite our parser each time we
# want to parse a new character. So, we define our parser generator for single
# literal parsers `Lit`.

def Lit(c):
    def parse(instr):
        return [(instr[1:], [c])] if instr and instr[0] == c else []
    return parse

# The `Lit(c)` captures the character `c` passed in, and returns a new function
# that parses specifically that literal.
# 
# We can use it as follows --- note that we need to split a string into characters
# using `list` before it can be passed to the parser:

if __name__ == '__main__':
    input_chars = list('a')
    la = Lit('a')
    result = la(input_chars)
    for i,p in result:
        print(i, p)

# That is, the input (the first part) is completely consumed, leaving an empty
# array, and the parsed result is `['a']`.
# Can it parse the literal `b`?

if __name__ == '__main__':
    input_chars = list('b')
    la = Lit('a')
    result = la(input_chars)
    for i,p in result:
        print(i, p)

# which prints nothing --- that is, the parser was unable to consume any input.
# 
# We define a convenience method to get only parsed results.

def only_parsed(r):
   for (i, p) in r:
       if i == []: yield p

# Using it as follows:

if __name__ == '__main__':
    for p in only_parsed(result):
        print(p)

# ### AndThen
# 
# Next, we define how to concatenate two parsers. That is, the result from one
# parser becomes the input of the next. The idea is that the first parser would
# have generated a list of successful parses until different locations. The second
# parser now tries to advance the location of parsing. If successful, the location
# is updated. If not successful, the parse is dropped. That is, given a list of
# chars `ab` and a parser that is `AndThen(Lit('a'), Lit('b'))`, `AndThen` first
# applies `Lit('a')` which results in an array with a single element as the successful
# parse: `[([['b'], ['a']])]` The first element of the item is the remaining list `['b']`.
# Now, the second parser is applied on it, which takes it forward to `[([[], ['a', 'b']])]`.
# If instead, we were parsing `ac`, then the result of the first parse will be the same
# as before. But the second parse will not succeed. Hence this item will be dropped resulting
# in an empty array.

def AndThen(p1, p2):
    def parse(instr):
        ret = []
        for (in1, pr1) in p1(instr):
            for (in2, pr2) in p2(in1):
                ret.append((in2, pr1+pr2))
        return ret
    return parse

# This parser can be used in the following way:

if __name__ == '__main__':
    lab = AndThen(Lit('a'), Lit('b'))
    result = lab(list('ab'))
    for p in only_parsed(result):
        print(p)

# ### OrElse
# 
# Finally we define how alternatives expansions are handled. Each parser operates
# on the input string from the beginning independently. So, the implementation is
# simple. Note that it is here that the main distinguishing feature of a context
# free parser compared to parsing expressions are found. We try *all* possible
# ways to parse a string irrespective of whether previous rules managed to parse
# it or not. Parsing expressions on the other hand, stop at the first success.
# 

def OrElse(p1, p2):
   def parse(instr):
       return p1(instr) + p2(instr)
   return parse

# It can be used as follows:

if __name__ == '__main__':
    lab = OrElse(Lit('a'), Lit('b'))
    result = lab(list('a'))
    for p in only_parsed(result):
        print(p)

# With this, our parser is fairly usable. We only need to retrieve complete parses
# as below.

if __name__ == '__main__':
    labc1 = AndThen(AndThen(Lit('a'), Lit('b')), Lit('c'))
    labc2 = AndThen(Lit('a'), AndThen(Lit('b'), Lit('c')))

    labc3 = OrElse(labc1, labc2)
    result = labc3(list('abc'))
    for r in only_parsed(result):
        print(r)

# Note that the order in which `AndThen` is applied is not shown in the results.
# This is a consequence of the way we defined `AndThen` using `pr1+pr2` deep
# inside the return from the parse. If we wanted to keep the distinction, we
# could have simply used `[pr1, pr2]` instead.
# 
# ## Recursion
#  
# This is not however, complete. One major issue is that recursion is not
# implemented. One way we can implement recursion is to make everything lazy.
# The only difference in these implementations is how we unwrap the parsers first
# i.e we use `p1()` instead of `p1`.
# 
# ### AndThen

def AndThen(p1, p2):
   def parse(instr):
       return [(in2, pr1 + pr2)
               for (in1, pr1) in p1()(instr)
               for (in2, pr2) in p2()(in1)]
   return parse
 
# ### OrElse
# 
# Similar to `AndThen`, since p1 and p2 are now `lambda` calls that need to be evaluated to get the actual function.

def OrElse(p1, p2):
    def parse(instr):
        return p1()(instr) + p2()(instr)
    return parse

# We are now ready to test our new parsers.
# 
# ### Simple parenthesis language
# 
# We define a simple language to parse `(1)`. Note that we can define these either using the
# `lambda` syntax or using `def`. Since it is easier to debug using `def`, and we are giving
# these parsers a name anyway, we use `def`.

if __name__ == '__main__':
    def Open_(): return Lit('(')
    def Close_(): return Lit(')')
    def One_(): return Lit('1')
    def Paren1():
        return AndThen(lambda: AndThen(Open_, One_), Close_)

# We can now parse the simple expression `(1)`

if __name__ == '__main__':
    result = Paren1()(list('(1)'))
    for r in only_parsed(result):
        print(r)


# Next, we extend our definitions to parse the recursive language with any number of parenthesis.
# That is, it should be able to parse `(1)`, `((1))`, and others. As you
# can see, `lambda` protects `Paren` from being evaluated too soon.

if __name__ == '__main__':
    def Paren():
        return AndThen(lambda: AndThen(Open_, lambda: OrElse(One_, Paren)), Close_)

# Using

if __name__ == '__main__':
    result = Paren()(list('((1))'))
    for r in only_parsed(result):
        print(r)

# Note that at this point, we do not really have a labeled parse tree. The way to add it is the following. We first define `Apply` that
# can be applied at particular parse points.

def Apply(f, parser):
    def parse(instr):
        return [(i,f(r)) for i,r in  parser()(instr)]
    return parse

# We can now define the function that will be accepted by `Apply`

if __name__ == '__main__':
    def to_paren(v):
        assert v[0] == '('
        assert v[-1] == ')'
        return [('Paren', v[1:-1])]

# We define the actual parser for the literal `1` as below:

if __name__ == '__main__':
    def One():
        def tree(x):
            return [('Int', int(x[0]))]
        return Apply(tree, One_)

# Similarly, we update the `paren1` parser.

if __name__ == '__main__':
    def Paren1():
        def parser():
            return AndThen(lambda: AndThen(Open_, One), Close_)
        return Apply(to_paren, parser)

# It is used as follows
if __name__ == '__main__':
    result = Paren1()(list('(1)'))
    for r in only_parsed(result):
        print(r)

# Similarly we update `Paren`

def Paren():
    def parser():
        return AndThen(lambda:
                AndThen(Open_,
                    lambda:
                    OrElse(One, Paren)), Close_)
    return Apply(to_paren, parser)

# Used thus:

if __name__ == '__main__':
    result = Paren()(list('(((1)))'))
    for r in only_parsed(result):
        print(r)

# Now, we are ready to try something adventurous. Let us allow a sequence of parenthesized ones.

if __name__ == '__main__':
    def Parens():
        return OrElse(Paren, lambda: AndThen(Paren, Parens))

    def Paren():
        def parser():
            return AndThen(lambda: AndThen(Open_, lambda: OrElse(One, Parens)), Close_)
        return Apply(to_paren, parser)

# We check if our new parser works

if __name__ == '__main__':
    result = Paren()(list('(((1)(1)))'))
    for r in only_parsed(result):
        print(r)

# That seems to have worked!.
# 
# All this is pretty cool. But none of this looks as nice as the Parsec examples
# we see. Can we apply some syntactic sugar and make it read nice? Do we have to
# go for the monadic concepts to get the syntactic sugar? Never fear!
# we have the solution. We simply define a class that incorporates some syntactic
# sugar on top.

class P:
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, instr):
        return self.parser()(list(instr))

    def __rshift__(self, other):
        return P(lambda: AndThen(self.parser, other.parser))

    def __or__(self, other):
        return P(lambda: OrElse(self.parser, other.parser)) 

# It can be used as follows

if __name__ == '__main__':
    one = P(lambda: Lit('1'))
    openP = P(lambda: Lit('('))
    closeP = P(lambda: Lit(')'))

    parens = P(lambda: paren | (paren >> parens))
    paren = P(lambda: openP >> (one | parens) >> closeP) 

    v = parens(list('((1)((1)))'))
    print(v)

# Apply also works with this

if __name__ == '__main__':
    paren = P(lambda: Apply(to_paren, lambda: openP >> (one | parens) >> closeP))

 
# Used as follows

if __name__ == '__main__':
    v = parens(list('((1)((1)))'))
    print(v)

# Note that one has to be careful about the precedence of operators. In
# particular, if you mix and match `>>` and `|`, always use parenthesis
# to disambiguate.
# 

# We also define a regular expression matcher for completeness

import re
def Re(r):
    def parse(instr):
        assert r[0] == '^'
        res = re.match(r, ''.join(instr))
        if res:
            (start, end) = res.span()
            return [(instr[end:], [instr[start:end]])]
        return []
    return parse

 
# ### The simple parenthesis language

if __name__ == '__main__':
    one = P(lambda: Lit('1'))
    num = P(lambda: Apply(to_num, lambda: Re('^[0-9]+')))
    openP = P(lambda: Lit('('))
    closeP = P(lambda: Lit(')'))

    parens = P(lambda: paren | (paren >> parens))

    def to_paren(v):
        assert v[0] == '('
        assert v[-1] == ')'
        return [('Paren', v[1:-1])]

    def to_num(v):
        return [('Num', v)]

    paren = P(lambda: Apply(to_paren, lambda: openP >> (one | parens) >> closeP))
    v = parens(list('((1)((1)))'))
    print(v)

    paren = P(lambda: Apply(to_paren, lambda: openP >> (num | parens) >> closeP))
    v = parens(list('((123)((456)))'))
    for m in v:
        print(m)


# ### Remaining
# 
# What is missing at this point? Left recursion!.
# However, there is something even more interesting here. If you remember my
# previous post about [minimal PEG parsers](/post/2018/09/06/peg-parsing/) you
# might notice the similarity between the `AndThen()` and `unify_rule()`
# and `OrElse()` and `unify_key()`.
# That is, in context-free combinatory parsing (unlike PEG), the `OrElse`
# ensures that results of multiple attempts are kept. The `AndThen` is a lighter
# version of the `unify_rule` in that it tries to unify two symbols at a time
# rather than any number of symbols. However, this should convince you that we
# can translate one to the other easily. That is, how to limit `OrElse` so that
# it does the ordered choice of PEG parsing or how to modify `unify_key` and
# `unify_rule` so that we have a true context free grammar parser rather than a
# PEG parser.

