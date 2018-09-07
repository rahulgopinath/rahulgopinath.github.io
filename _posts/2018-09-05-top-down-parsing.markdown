---
published: true
title: How hard is parsing a context-free language? - recursive descent parsing by hand
layout: post
comments: true
tags: parsing
---

How hard is parsing a context-free<sup id="a1">[1](#f1)</sup> language? In this post, I will try to provide
an overview of one of the simplest parsing techniques of all -- recusrive descent parsing by hand.

This type of parsing uses mutually recursive procedures to parse a subset of context-free languages
using a top-down approach. Hence, this kind of parsing is also called a top-down recursive descent
parser. The grammar is restricted to only those rules that can be expressed without recursion in the
left-most term.

Here is a simple grammar for a language that can parse nested expressions, with the restriction that
the expressions elements can only be `1` and only addition is supported for simplicity.

```ebnf
E = T "+" E
  | T
T = "1"
  | "(" E ")"
```

This grammar can parse expressions such as `1`, `1+1`, `1+1+1+1` etc.

To start parsing, we need a bit of infrastructure. In particular, we need the ability to tell where
we are currently (`cur_position`), the ability to backtrack to a previous position, and the ability
to tell when the input is complete. I use global variables for ease of discussion, and to avoid having
to commit too much to _Python_ syntax and semantics. Use the mechanisms available in your language to
modularize your parser.

```python
my_input = None
cur_position = 0

def pos_cur():
    return cur_position

def pos_set(i):
    global cur_position
    cur_position = i

def pos_eof():
    return pos_cur() == len(my_input)
```
We also need the ability to extract the `next token` (in this case, the next element in the input array).
```python
def next_token():
    i = pos_cur()
    if i+1 > len(my_input): return None
    pos_set(i+1)
    return my_input[i]
```
Another convenience we use is the ability to `match` a token to a given symbol.
```python
def match(t):
    return next_token() == t
```

Once we have all these, the core part of parsing is two procedures. The first tries to match a sequence
of terms one by one. If the match succeeds, then we return success. If not, then we signal failure and exit.
```python
def do_seq(seq_terms):
   for t in seq_terms:
       if not t(): return False
   return True
```

The other corresponds to the alternatives for each production. If any alternative succeeds, then the parsing succeeds.
```python
def do_alt(alt_terms):
    for t in alt_terms:
        o_pos = pos_cur()
        if t(): return True
        pos_set(o_pos)
    return False
```
With this, we are now ready to write our parser. Since we are writing a top-down recursive descent parser, we
start with the axiom rule `E` which contains two alternatives.
```python
# E = ...
#   | ...
def E():
    return do_alt([E_1, E_2])
```
Both `E_1` and `E_2` are simple sequential rules
```python
# E = T + E
def E_1():
    return do_seq([T, PLUS, E])
# E = T
def E_2():
    return do_seq([T])
```
Defining `T` is similar
```python
# T = ...
#   | ...
def T():
    return do_alt([T_1, T_2])
```
And each alternative in `T` gets defined correspondingly.
```python
# T = 1
def T_1():
    return match('1')
# T = ( E )
def T_2():
    return do_seq([P_OPEN,E,P_CLOSE])
```
We also need terminals, which is again simple enough
```python
def PLUS():
    return match('+')
def P_OPEN():
    return match('(')
def P_CLOSE():
    return match(')')
```
The only thing that remains is to define the parser
```python
def parse(i):
    global my_input
    my_input = i
    assert E()
    assert pos_eof()
```

Using it:
```pycon
>>> import tdrd
>>> tdrd.parse('1+1')
>>> tdrd.parse('1+(1+1)+1')
```
The interesting part is that, our infrastructure can be readily turned to
parse much more complex grammars, with almost one-to-one rewriting of each rule. For example,
here is a slightly more complex grammar:
```ebnf
term = fact mul_op term
     | fact

fact =  digits
     | "(" expr ")"

digits = digit digits
      | digit

digit = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
add_op = "+" | "-"
mul_op = "*" | "/"
```
Its conversion is almost automatic
```python
def expr():     return do_alt([expr_1, expr_2])
def expr_1():   return do_seq([term, add_op, expr])
def expr_2():   return do_seq([term])

def term():     return do_alt([term_1, term_2])
def term_1():   return do_seq([fact, mul_op, term])
def term_2():   return do_seq([fact])

def fact():     return do_alt([fact_1, fact_2])
def fact_1():   return do_seq([digits])
def fact_2():   return do_seq([lambda: match('('), expr, lambda: match(')')])

def digits():   return do_alt([digits_1, digits_2])
def digits_1(): return do_seq([digit, digits])
def digits_2(): return do_seq([digit])

def add_op():   return do_alt([lambda: match('+'), lambda: match('-')])
def mul_op():   return do_alt([lambda: match('*'), lambda: match('/')])

# note that list comprehensions will not work here due to closure of i
def digit():    return do_alt(map(lambda i: lambda: match(str(i)), range(10)))
```

Using it:
```pycon
>>> import tdrd
>>> tdrd.parse('12*3+(12/13)')
```

Indeed, it is close enough to automatic, that we can make it fully automatic. We first define the
grammar as a datastructure for convenience. I hope I dont need to convince you that I could have
easily loaded it as a `JSON` file, or even parsed the BNF myself if necessary from an external file.
```python
grammar = {
        "expr": [["term", "add_op", "expr"], ["term"]],
        "term": [["fact", "mul_op", "term"], ["fact"]],
        "fact": [["digits"], ["(", "expr", ")"]],
        "digits": [["digit", "digits"], ["digit"]],
        "digit": [[str(i)] for i in list(range(10))],
        "add_op": [["+"], ["-"]],
        "mul_op": [["*"], ["/"]]
}
```
Using the grammar just means that we have to slightly modify our core procedures.
```python
def do_seq(seq_terms):
   for t in seq_terms:
       if not do_alt(t): return False
   return True

def do_alt(key):
    if key not in grammar: return match(key)
    alt_terms = grammar[key]
    for ts in alt_terms:
        o_pos = pos_cur()
        if do_seq(ts): return True
        pos_set(o_pos)
    return False

def parse(i):
    global my_input
    my_input = i
    do_alt('expr')
    assert pos_eof()
```
Using it is same as before:
```pycon
>>> import tdrd
>>> tdrd.parse('12*3+(12/13)')
```
Briging it all together, place these in `tdrd.py`
```python
class g_parse:
    def __init__(self, g): self._g = g

    def remain(self): return self._len - self._i

    def next_token(self):
        try: return None if self._i + 1 > self._len else self._str[self._i]
        finally: self._i += 1

    def match(self, t): return self.next_token() == t

    def is_nt(self, key): return key in self._g

    def do_seq(self, seq_terms): return all(self.do_alt(t) for t in seq_terms)

    def _try(self, fn):
        o_pos = self._i
        if fn(): return True
        self._i = o_pos

    def do_alt(self, key):
        if not self.is_nt(key): return self.match(key)
        return any(self._try(lambda: self.do_seq(ts)) for ts in self._g[key])

    def parse(self, i):
        self._str, self._len, self._i = i, len(i), 0
        self.do_alt('expr')
        assert self.remain() == 0

if __name__ == '__main__':
    my_grammar = {
            "expr": [
                ["term", "add_op", "expr"],
                ["term"]],
            "term": [
                ["fact", "mul_op", "term"],
                ["fact"]],
            "fact": [
                ["digits"],
                ["(", "expr", ")"]],
            "digits": [
                ["digit", "digits"],
                ["digit"]],
            "digit": [[str(i)] for i in list(range(10))],
            "add_op": [["+"], ["-"]],
            "mul_op": [["*"], ["/"]]}

    import sys
    g_parse(my_grammar).parse(sys.argv[1])
```
Which can be used as
```bash
$ python3 tdrd.py '123+11+(3*(2))+1'
```
Of course, one usually wants to do something with the parsed output. However, given that the procedures are organized in a top-down fashion, saving the resulting expressions is relatively trivial.


<b id="f1">1</b> 1: The parser we create is not really interpreting the grammar as a _Context-Free Grammar_. Rather, it uses the grammar as if it is written using another formalism called _Parsing Expression Grammar_. However, an important subclass of context-free languages in real world -- _LL(*)_ -- can be completely represented using _PEG_. Hence, the title is not completely wrong.
[$\hookleftarrow$](#a1)

