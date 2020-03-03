---
published: false
title: Combinatory parsing
layout: post
comments: true
tags: combinators, parsing, cfg
categories: post
---

Parsec introduced combinatory parsing to the wider world (although this technique seems to have been mentioned by
[Burge](https://www.amazon.com/Recursive-Programming-Techniques-Systems-programming/dp/0201144506) in 1975). The question
is, can one write a simple implementation without delving into category theory and Monads? Here is an attempt. We use the
list of successes method by wadler.

First, we define the literal parsers:

```
def Lit(c):
    def parse(instr):
        return [(instr[1:], ('Lit', c))] if instr[0] == c else []
    return parse
 ```
 
 Next, we define how two parsers can be combined one after another.
 
 ```
 def AndThen(p1, p2):
    def parse(instr):
        ret = []
        for (in1, pr1) in p1(instr):
            for (in2, pr2) in p2(in1):
                ret.append((in2, ('AndThen', [pr1, pr2])))
        return ret
    return parse
 ```
 
 Finally we define how alternatives expansions are handled.
 
 ```
 def OrElse(p1, p2):
    def parse(instr): return p1(instr) + p2(instr)
    return parse
 ```
 
 With this, our parser is complete. We only need to retrieve complete parses as below.
 
 ```
 def only_parsed(r):
    for (i, p) in r:
        if i == []: yield p
```

Let us try using it:
```
parser1 = AndThen(AndThen(Lit('a'), Lit('b')), Lit('c'))
parser2 = AndThen(Lit('a'), AndThen(Lit('b'), Lit('c')))
result = parser1(list('abc'))
result = parser2(list('abc'))

parser3 = OrElse(parser1, parser2)
result = parser3(list('abc'))
for r in only_parsed(result):
    print(r)
 ```
 
 ```
('AndThen', [('AndThen', [('Lit', 'a'), ('Lit', 'b')]), ('Lit', 'c')])
('AndThen', [('Lit', 'a'), ('AndThen', [('Lit', 'b'), ('Lit', 'c')])])
 ```
 
 This is not howver, complete. One major issue is that recursion is not implemented. One way we can
 implement recursion is to make everything lazy.
 
 ```
 def AndThen(p1, p2):
    def parse(instr):
        return [(in2, ('AndThen', [pr1, pr2]))
                for (in1, pr1) in p1()(instr)
                    for (in2, pr2) in p2()(in1)]
    return parse
```

```
def OrElse(p1, p2):
    def parse(instr): return p1()(instr) + p2()(instr)
    return parse
```

```
Open_ = lambda: Lit('(')
Close_ = lambda: Lit(')')
One_ = lambda: Lit('1')
Paren1 = lambda: AndThen(lambda: AndThen(Open_, One_), Close_)
result = Paren1()(list('(1)'))
print(result)
```

Result.
```
[([], ('AndThen', [('AndThen', [('Lit', '('), ('Lit', '1')]), ('Lit', ')')]))]
```

More complicated
```
Paren = lambda: AndThen(lambda: AndThen(Open_, lambda: OrElse(One_, Paren)), Close_)
result = Paren()(list('(((1)))'))
print(result)
```
Result
```
[([], ('AndThen', [('AndThen', [('Lit', '('), ('AndThen', [('AndThen', [('Lit', '('), ('AndThen', [('AndThen', [('Lit', '('), ('Lit', '1')]), ('Lit', ')')])]), ('Lit', ')')])]), ('Lit', ')')]))]
```

What is missing? Left recursion!.
