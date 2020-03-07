---
published: true
title: Simple Combinatory Parsing For Context Free Languages
layout: post
comments: true
tags: combinators, parsing, cfg
categories: post
---

[Parsec](https://www.cs.nott.ac.uk/~pszgmh/pearl.pdf) introduced combinatory parsing to the wider world
(although this technique seems to have been mentioned by
[Burge](https://www.amazon.com/Recursive-Programming-Techniques-Systems-programming/dp/0201144506) in 1975).
The question is, can one write a simple implementation without delving into category theory and Monads?
Here is an attempt.

### Lit

The idea is simple. Start with the basic item -- a parser that parses a single character. We use the list of successes method by [Wadler](https://homepages.inf.ed.ac.uk/wadler/papers/marktoberdorf/baastad.pdf). That is, failure is represented
by an empty list. A successful parse of a character is represented by a single element list with the remaining
input, and the parse tree (In this case, a single literal). We use a closure to capture the particular literal we are trying to parse. Note that we store the parsed literal as a single character in an array, which makes it easier to manipulate in Python (as you will see later).

```python
def Lit(c):
    def parse(instr):
        return [(instr[1:], [c])] if instr[0] == c else []
    return parse
```
We can use it as follows:
```python
la = Lit('a')
result = la(list('a'))
for i,p in result:
    print(i, p)
```
Which prints
```python
[] ['a']
```

We define a convenience method to get only parsed results.

```python
def only_parsed(r):
   for (i, p) in r:
       if i == []: yield p
```
Using it as follows:
```python
for p in only_parsed(result):
    print(p)
```
which prints
```python
['a']
```

### AndThen

Next, we define how to concatenate two parsers. That is, the result from one parser
become the input of the next. The idea is that the first parser would have generated a list
of successful parses until different locations, and the second parser has to operate on the
remaining. The parse results are arrays and can be simply concatenated together.

```python
def AndThen(p1, p2):
    def parse(instr):
        return [(in2, pr1+pr2)
             for (in1, pr1) in p1(instr)
                  for (in2, pr2) in p2(in1)]
    return parse
```
This parser can be used in the following way:
```python
lab = AndThen(Lit('a'), Lit('b'))
result = lab(list('ab'))
for p in only_parsed(result):
    print(p)
```
which prints
```python
['a', 'b']
```

### OrElse

Finally we define how alternatives expansions are handled. Each parser operates on the
input string from the beginning independently. So, the implementation is simple.
```python
def OrElse(p1, p2):
   def parse(instr):
       return p1(instr) + p2(instr)
   return parse
``` 

With this, our parser is complete. We only need to retrieve complete parses as below.
```python
labc1 = AndThen(AndThen(Lit('a'), Lit('b')), Lit('c'))
labc2 = AndThen(Lit('a'), AndThen(Lit('b'), Lit('c')))
result = labc1(list('abc'))
result = labc2(list('abc'))

labc3 = OrElse(labc1, labc2)
result = labc3(list('abc'))
for r in only_parsed(result):
    print(r)
```
The result looks like below.
```python
['a', 'b', 'c']
['a', 'b', 'c']
```
Note that the order in which `AndThen` is applied is not shown in the results. This is a consequence
of the way we defined `AndThen` using `pr1+pr2` deep inside the return from the parse. If we wanted
to keep the distinction, we could have simply used `[pr1, pr2]` instead.

## Recursion
 
This is not howver, complete. One major issue is that recursion is not implemented. One way we can
implement recursion is to make everything lazy. The only difference in these implementations is how
we unwrap the parsers first i.e we use `p1()` instead of `p1`.

### AndThen

```python
def AndThen(p1, p2):
   def parse(instr):
       return [(in2, pr1 + pr2) for (in1, pr1) in p1()(instr) for (in2, pr2) in p2()(in1)]
   return parse
```

### OrElse

Similar to `AndThen`, since p1 and p2 are now `lambda` calls that need to be evaluated to get the actual function.

```python
def OrElse(p1, p2):
    def parse(instr):
        return p1()(instr) + p2()(instr)
    return parse
```
We are now ready to test our new parsers.

### Simple parenthesis language

We define a simple language to parse `(1)`. Note that we can define these either using the
`lambda` syntax or using `def`. Since it is easier to debug using `def`, and we are giving
these parsers a name anyway, we use `def`.

```python
def Open_(): return Lit('(')
def Close_(): return Lit(')')
def One_(): return Lit('1')
def Paren1():
    return AndThen(lambda: AndThen(Open_, One_), Close_)
```
We can now parse the simple expression `(1)`
```python
result = Paren1()(list('(1)'))
for r in only_parsed(result):
    print(r)
```
The result is as follows
```python
['(', '1', ')']
```

Next, we extend our definitions to parse the recursive language with any number of parenthesis.
That is, it should be able to parse `(1)`, `((1))`, and others. As you
can see, `lambda` protects `Paren` from being evaluated too soon.

```python
def Paren():
    return AndThen(lambda: AndThen(Open_, lambda: OrElse(One_, Paren)), Close_)

result = Paren()(list('((1))'))
for r in only_parsed(result):
    print(r)
```
Result
```python
['(', '(', '1', ')', ')']
```

Note that at this point, we do not really have a labelled parse tree. The way to add it is the following. We first define `Apply` that
can be applied at particular parse points.

```python
def Apply(f, parser):
    def parse(instr):
        return [(i,f(r)) for i,r in  parser()(instr)]
    return parse
```
We can now define the function that will be accepted by `Apply`
```python
def to_paren(v):
    assert v[0] == '('
    assert v[-1] == ')'
    return [('Paren', v[1:-1])]
```

We define the actual parser for the literal `1` as below:
```python
def One():
    def tree(x):
        return [('Int', int(x[0]))]
    return Apply(tree, One_)
```
Similarly, we update the `paren` parsers.
```python
def Paren1():
    return Apply(to_paren, lambda: AndThen(lambda: AndThen(Open_, One), Close_))
```
It is used as follows
```python
result = Paren1()(list('(1)'))
for r in only_parsed(result):
    print(r)
```
Which results in
```python
[('Paren', [('Int', 1)])]
```
Similarly we update `Paren`
```python
def Paren():
    return Apply(to_paren, lambda: AndThen(lambda: AndThen(Open_, lambda: OrElse(One, Paren)), Close_))
```
Used as thus:
```
result = Paren()(list('(((1)))'))
for r in only_parsed(result):
    print(r)
```
results in
```python
[('Paren', [('Paren', [('Paren', [('Int', 1)])])])]
```
Now, we are ready to try something adventurous. Let us allow a sequence of parenthesized ones.
```python
def Parens():
    return OrElse(Paren, lambda: AndThen(Paren, Parens))

def Paren():
    def parser():
        return AndThen(lambda: AndThen(Open_, lambda: OrElse(One, Parens)), Close_)
    return Apply(to_paren, parser)
```
We check if our new parser works
```python
result = Paren()(list('(((1)(1)))'))
for r in only_parsed(result):
    print(r)
```
This results in
```python
[('Paren', [('Paren', [('Paren', [('Int', 1)]), ('Paren', [('Int', 1)])])])]
```
That seems to have worked!.

### Remaining

What is missing at this point? Left recursion!.
However, there is something even more interesting here. If you remember my previous post about [minimal PEG parsers](/post/2018/09/06/peg-parsing/) you might notice the similarity between the `AndThen()` and `unify_rule()` and `OrElse()` and `unify_key()`. That is, in combinatory parsing (unlike PEG), the `OrElse` ensures that results of multiple attempts are kept. The `AndThen` is a lighter version of the `unify_rule` in that it tries to unify two symbols at a time rather than any number of symbols. However, this should convince you that we can translate one to the other easily. That is, how to limit `OrElse` so that it does the ordered choice of PEG parsing or how to modify `unify_key` and `unify_rule` so that we have a true context free grammar parser rather than a PEG parser.
