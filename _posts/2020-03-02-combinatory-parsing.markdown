---
published: true
title: Simple combinatory parsing
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
input, and the parse tree (In this case, a single literal). We use a closure to capture the particular literal we are trying to parse.

```python
def Lit(c):
    def parse(instr):
        return [(instr[1:], ('Lit', c))] if instr[0] == c else []
    return parse
```
We can use it as follows:
```python
la = Lit('a')
result = parser1(list('a'))
for i,p in result:
  print(i, p)
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

### AndThen

Next, we define how to concatenate two parsers. That is, the result from one parser
become the input of the next. The idea is that the first parser would have generated a list
of successful parses until different locations, and the second parser has to operate on the
remaining.

```python
def AndThen(p1, p2):
    def parse(instr):
        ret = []
        for (in1, pr1) in p1(instr):
            for (in2, pr2) in p2(in1):
                ret.append((in2, ('AndThen', [pr1, pr2])))
        return ret
    return parse
```
This parser can be used in the following way:
```python
la = AndThen(Lit('a'), Lit('b'))
result = parser1(list('ab'))
for p in only_parsed(result):
    print(p)
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
parser1 = AndThen(AndThen(Lit('a'), Lit('b')), Lit('c'))
parser2 = AndThen(Lit('a'), AndThen(Lit('b'), Lit('c')))
result = parser1(list('abc'))
result = parser2(list('abc'))

parser3 = OrElse(parser1, parser2)
result = parser3(list('abc'))
for r in only_parsed(result):
    print(r)
 ```
 The result looks like below.
 ```python
('AndThen', [('AndThen', [('Lit', 'a'), ('Lit', 'b')]), ('Lit', 'c')])
('AndThen', [('Lit', 'a'), ('AndThen', [('Lit', 'b'), ('Lit', 'c')])])
 ```
 
## Recursion
 
This is not howver, complete. One major issue is that recursion is not implemented. One way we can
implement recursion is to make everything lazy.
 
### AndThen
 
```python
def AndThen(p1, p2):
   def parse(instr):
       return [(in2, ('AndThen', [pr1, pr2]))
                for (in1, pr1) in p1()(instr)
                    for (in2, pr2) in p2()(in1)]
   return parse
```
Note that p1 and p2 are now `lambda` calls that need to be evaluated to get the actual function.

### OrElse

```python
def OrElse(p1, p2):
    def parse(instr): return p1()(instr) + p2()(instr)
    return parse
```

We define a simple language to parse `(1)`

```python
Open_ = lambda: Lit('(')
Close_ = lambda: Lit(')')
One_ = lambda: Lit('1')
Paren1 = lambda: AndThen(lambda: AndThen(Open_, One_), Close_)
```
We can now parse the simple expression `(1)`
```python
result = Paren1()(list('(1)'))
print(result)
```

The result is as follows
```python
[([], ('AndThen', [('AndThen', [('Lit', '('), ('Lit', '1')]), ('Lit', ')')]))]
```

Now, we define the recursive language for parsing `((1))` with any number of parenthesis. As you
can see, `lambda` protects `Paren` from being evaluated too soon.

```python
Paren = lambda: AndThen(lambda: AndThen(Open_, lambda: OrElse(One_, Paren)), Close_)
result = Paren()(list('(((1)))'))
print(result)
```
Result
```python
[([], ('AndThen', [('AndThen', [('Lit', '('), ('AndThen', [('AndThen', [('Lit', '('), ('AndThen', [('AndThen', [('Lit', '('), ('Lit', '1')]), ('Lit', ')')])]), ('Lit', ')')])]), ('Lit', ')')]))]
```

Note that at this point, we do not really have a labelled parse tree. The way to add it is the following. We first define `Apply` that
can be applied at particular parse points.

```python
def Apply(f, parser):
    def parse(instr):
        return [(i,f(r)) for i,r in  parser(instr)]
    return parse
```
We can now define the function that will be accepted by `Apply`
```python
def to_paren(v):
    return ('paren', v)
```
It is used as follows
```python
Paren1 = lambda: Apply(to_paren, AndThen(lambda: AndThen(Open_, One_), Close_))
result = Paren1()(list('(1)'))
print(result)
```
The `to_paren` understands how to convert the unlabelled nodes at `Paren` to the AST node. For now, we simply mark it as a `paren` node, but one can also go ahead and remove the wrapped parenthesis inside `AndThen` and convert it to AST.

What is missing at this point? Left recursion!.
