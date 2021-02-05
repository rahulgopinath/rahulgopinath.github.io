---
published: true
title: Simple Combinatory Parsing For Context Free Languages
layout: post
comments: true
tags: combinators, parsing, cfg
categories: post
---
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt.min.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt-stdlib.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/env/editor.js" type="text/javascript"></script>

Combinatory parsing (i.e parsing with [combinators](https://en.wikipedia.org/wiki/Combinatory_logic)) was
introduced by William H Burge in his seminal work
[Recursive Programming Techniques -- The systems programming series](https://archive.org/details/recursiveprogram0000burg)
in 1975. Unfortunately, it took until 2001 for the arrival of [Parsec](/references/#leijen2001parsec), and for combinatory
programming to be noticed by the wider world.

While Parsec is a pretty good library, it is often hard to understand for
programmers who are not familiar with Haskell. So, the question is, can
one explain the concept of simple combinatory parsing without delving to
Haskell and Monads? Here is my attempt.

The idea of combinatory parsing is really simple. We start with the smallest
parsers that do some work --- parsing single characters, then figure out how
to combine them to produce larger and larger parsers.

Note that since we are dealing with context-free parsers, ambiguity in parsing
is a part of life. Hence, we have to keep a list of possible parses at all
times. A failure to parse is then naturally represented by an empty list, and
a single parse item is a tuple that contains the remaining input as the first
element, and the parse result as the second.
This particular approach was pioneered by [Wadler](https://homepages.inf.ed.ac.uk/wadler/papers/marktoberdorf/baastad.pdf).

So, here, we start with the basic parser -- one that parses a single character
`a`.  The return values are as expected --- a single empty list for failure to
parse and a list of parses (a single element here because there is only one way
to parse `a`).


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def parse(instr):
    if instr and instr[0] == &#x27;a&#x27;:
       return [(instr[1:], [&#x27;a&#x27;])] 
    return []
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

While this is a good start, we do not want to rewrite our parser each time we
want to parse a new character. So, we define our parser generator for single
literal parsers `Lit`.
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Lit(c):
    def parse(instr):
        return [(instr[1:], [c])] if instr and instr[0] == c else []
    return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

The `Lit(c)` captures the character `c` passed in, and returns a new function
that parses specifically that literal.

We can use it as follows --- note that we need to split a string into characters
using `list` before it can be passed to the parser:

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

input_chars = list(&#x27;a&#x27;)
la = Lit(&#x27;a&#x27;)
result = la(input_chars)
for i,p in result:
    print(i, p)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

That is, the input (the first part) is completely consumed, leaving an empty
array, and the parsed result is `['a']`.
Can it parse the literal `b`?

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

input_chars = list(&#x27;b&#x27;)
la = Lit(&#x27;a&#x27;)
result = la(input_chars)
for i,p in result:
    print(i, p)

</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

which prints nothing --- that is, the parser was unable to consume any input.

We define a convenience method to get only parsed results.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def only_parsed(r):
   for (i, p) in r:
       if i == []: yield p


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Using it as follows:
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

for p in only_parsed(result):
    print(p)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


### AndThen

Next, we define how to concatenate two parsers. That is, the result from one
parser becomes the input of the next. The idea is that the first parser would
have generated a list of successful parses until different locations. The second
parser now tries to advance the location of parsing. If successful, the location
is updated. If not successful, the parse is dropped. That is, given a list of
chars `ab` and a parser that is `AndThen(Lit('a'), Lit('b'))`, `AndThen` first
applies `Lit('a')` which results in an array with a single element as the succssful
parse: `[([['b'], ['a']])]` The first elment of the item is the remaining list `['b']`.
Now, the second parser is applied on it, which takes it forward to `[([[], ['a', 'b']])]`.
If instead, we were parsing `ac`, then the result of the first parse will be the same
as before. But the second parse will not succeed. Hence this item will be dropped resulting
in an empty array.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def AndThen(p1, p2):
    def parse(instr):
        ret = []
        for (in1, pr1) in p1(instr):
            for (in2, pr2) in p2(in1):
                ret.append((in2, pr1+pr2))
        return ret
    return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

This parser can be used in the following way:

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

lab = AndThen(Lit(&#x27;a&#x27;), Lit(&#x27;b&#x27;))
result = lab(list(&#x27;ab&#x27;))
for p in only_parsed(result):
    print(p)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

### OrElse

Finally we define how alternatives expansions are handled. Each parser operates
on the input string from the beginning independently. So, the implementation is
simple. Note that it is here that the main distinguishing feature of a context
free parser compared to parsing expressions are found. We try *all* possible
ways to parse a string irrespective of whether previous rules managed to parse
it or not. Parsing expressions on the other hand, stop at the first success.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def OrElse(p1, p2):
   def parse(instr):
       return p1(instr) + p2(instr)
   return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

It can be used as follows:

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

lab = OrElse(Lit(&#x27;a&#x27;), Lit(&#x27;b&#x27;))
result = lab(list(&#x27;a&#x27;))
for p in only_parsed(result):
    print(p)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

With this, our parser is fairly usable. We only need to retrieve complete parses
as below.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

labc1 = AndThen(AndThen(Lit(&#x27;a&#x27;), Lit(&#x27;b&#x27;)), Lit(&#x27;c&#x27;))
labc2 = AndThen(Lit(&#x27;a&#x27;), AndThen(Lit(&#x27;b&#x27;), Lit(&#x27;c&#x27;)))

labc3 = OrElse(labc1, labc2)
result = labc3(list(&#x27;abc&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Note that the order in which `AndThen` is applied is not shown in the results.
This is a consequence of the way we defined `AndThen` using `pr1+pr2` deep
inside the return from the parse. If we wanted to keep the distinction, we
could have simply used `[pr1, pr2]` instead.

## Recursion
 
This is not however, complete. One major issue is that recursion is not
implemented. One way we can implement recursion is to make everything lazy.
The only difference in these implementations is how we unwrap the parsers first
i.e we use `p1()` instead of `p1`.

### AndThen

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def AndThen(p1, p2):
   def parse(instr):
       return [(in2, pr1 + pr2) for (in1, pr1) in p1()(instr) for (in2, pr2) in p2()(in1)]
   return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


### OrElse

Similar to `AndThen`, since p1 and p2 are now `lambda` calls that need to be evaluated to get the actual function.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def OrElse(p1, p2):
    def parse(instr):
        return p1()(instr) + p2()(instr)
    return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We are now ready to test our new parsers.

### Simple parenthesis language

We define a simple language to parse `(1)`. Note that we can define these either using the
`lambda` syntax or using `def`. Since it is easier to debug using `def`, and we are giving
these parsers a name anyway, we use `def`.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Open_(): return Lit(&#x27;(&#x27;)
def Close_(): return Lit(&#x27;)&#x27;)
def One_(): return Lit(&#x27;1&#x27;)
def Paren1():
    return AndThen(lambda: AndThen(Open_, One_), Close_)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We can now parse the simple expression `(1)`
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

result = Paren1()(list(&#x27;(1)&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Next, we extend our definitions to parse the recursive language with any number of parenthesis.
That is, it should be able to parse `(1)`, `((1))`, and others. As you
can see, `lambda` protects `Paren` from being evaluated too soon.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Paren():
    return AndThen(lambda: AndThen(Open_, lambda: OrElse(One_, Paren)), Close_)

result = Paren()(list(&#x27;((1))&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


Note that at this point, we do not really have a labelled parse tree. The way to add it is the following. We first define `Apply` that
can be applied at particular parse points.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Apply(f, parser):
    def parse(instr):
        return [(i,f(r)) for i,r in  parser()(instr)]
    return parse


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We can now define the function that will be accepted by `Apply`

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def to_paren(v):
    assert v[0] == &#x27;(&#x27;
    assert v[-1] == &#x27;)&#x27;
    return [(&#x27;Paren&#x27;, v[1:-1])]


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We define the actual parser for the literal `1` as below:

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def One():
    def tree(x):
        return [(&#x27;Int&#x27;, int(x[0]))]
    return Apply(tree, One_)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Similarly, we update the `paren1` parser.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Paren1():
    def parser():
        return AndThen(lambda: AndThen(Open_, One), Close_)
    return Apply(to_paren, parser)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

It is used as follows

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

result = Paren1()(list(&#x27;(1)&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Similarly we update `Paren`

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Paren():
    def parser():
        return AndThen(lambda: AndThen(Open_, lambda: OrElse(One, Paren)), Close_)
    return Apply(to_paren, parser)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Used as thus:

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

result = Paren()(list(&#x27;(((1)))&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Now, we are ready to try something adventurous. Let us allow a sequence of parenthesized ones.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Parens():
    return OrElse(Paren, lambda: AndThen(Paren, Parens))

def Paren():
    def parser():
        return AndThen(lambda: AndThen(Open_, lambda: OrElse(One, Parens)), Close_)
    return Apply(to_paren, parser)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We check if our new parser works

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

result = Paren()(list(&#x27;(((1)(1)))&#x27;))
for r in only_parsed(result):
    print(r)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

That seems to have worked!.

All this is pretty cool. But none of this looks as nice as the Parsec examples
we see. Can we apply some syntactic sugar and make it read nice? Do we have to
go for the monadic concepts to get the syntactic sugar? Never fear!
we have the solution. We simply define a class that incorporates some syntactic
sugar on top.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

class P:
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, instr):
        return self.parser()(list(instr))

    def __rshift__(self, other):
        return P(lambda: AndThen(self.parser, other.parser))

    def __or__(self, other):
        return P(lambda: OrElse(self.parser, other.parser))


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

It can be used as follows

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

one = P(lambda: Lit(&#x27;1&#x27;))
openP = P(lambda: Lit(&#x27;(&#x27;))
closeP = P(lambda: Lit(&#x27;)&#x27;))

parens = P(lambda: paren | (paren &gt;&gt; parens))
paren = P(lambda: openP &gt;&gt; (one | parens) &gt;&gt; closeP)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

v = parens(list(&#x27;((1)((1)))&#x27;))
print(v)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Apply also works with this

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

paren = P(lambda: Apply(to_paren, lambda: openP &gt;&gt; (one | parens) &gt;&gt; closeP))


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Used as follows

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

v = parens(list(&#x27;((1)((1)))&#x27;))
print(v)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Note that one has to be careful about the precedence of operators. In
particular, if you mix and match `>>` and `|`, always use parenthesis
to disambiguate.

## All together

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def Lit(c):
    def parse(instr):
        return [(instr[1:], [c])] if instr and instr[0] == c else []
    return parse

import re
def Re(r):
    def parse(instr):
        assert r[0] == &#x27;^&#x27;
        res = re.match(r, &#x27;&#x27;.join(instr))
        if res:
            (start, end) = res.span()
            return [(instr[end:], [instr[start:end]])]
        return []
    return parse

def AndThen(p1, p2):
   def parse(instr):
       return [(in2, pr1 + pr2) for (in1, pr1) in p1()(instr) for (in2, pr2) in p2()(in1)]
   return parse

def OrElse(p1, p2):
    def parse(instr):
        return p1()(instr) + p2()(instr)
    return parse

def Apply(f, parser):
    def parse(instr):
        return [(i,f(r)) for i,r in  parser()(instr)]
    return parse

class P:
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, instr):
        return self.parser()(list(instr))

    def __rshift__(self, other):
        return P(lambda: AndThen(self.parser, other.parser))

    def __or__(self, other):
        return P(lambda: OrElse(self.parser, other.parser))


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

The simple parenthesis language

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

one = P(lambda: Lit(&#x27;1&#x27;))
num = P(lambda: Apply(to_num, lambda: Re(&#x27;^[0-9]+&#x27;)))
openP = P(lambda: Lit(&#x27;(&#x27;))
closeP = P(lambda: Lit(&#x27;)&#x27;))

parens = P(lambda: paren | (paren &gt;&gt; parens))

def to_paren(v):
    assert v[0] == &#x27;(&#x27;
    assert v[-1] == &#x27;)&#x27;
    return [(&#x27;Paren&#x27;, v[1:-1])]

def to_num(v):
    return [(&#x27;Num&#x27;, v)]

paren = P(lambda: Apply(to_paren, lambda: openP &gt;&gt; (one | parens) &gt;&gt; closeP))
v = parens(list(&#x27;((1)((1)))&#x27;))
print(v)

paren = P(lambda: Apply(to_paren, lambda: openP &gt;&gt; (num | parens) &gt;&gt; closeP))
v = parens(list(&#x27;((123)((456)))&#x27;))
for m in v:
    print(m)


</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

### Remaining

What is missing at this point? Left recursion!.
However, there is something even more interesting here. If you remember my previous post about [minimal PEG parsers](/post/2018/09/06/peg-parsing/) you might notice the similarity between the `AndThen()` and `unify_rule()` and `OrElse()` and `unify_key()`. That is, in context-free combinatory parsing (unlike PEG), the `OrElse` ensures that results of multiple attempts are kept. The `AndThen` is a lighter version of the `unify_rule` in that it tries to unify two symbols at a time rather than any number of symbols. However, this should convince you that we can translate one to the other easily. That is, how to limit `OrElse` so that it does the ordered choice of PEG parsing or how to modify `unify_key` and `unify_rule` so that we have a true context free grammar parser rather than a PEG parser.
