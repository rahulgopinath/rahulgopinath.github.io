---
published: true
title: How hard is parsing a context-free language? LL(k) - top-down recursive descent parsing by hand
layout: post
comments: true
tags: parsing
---

How hard is parsing a context-free language? In this post, I will try to provide
an overview of one of the simplest parsing techniques of all -- LL(k).

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
cur_position = 0

def pos_cur():
    return cur_position

def pos_set(i):
    global cur_position
    cur_position = i

def pos_eof():
    return pos_cur() == len(input)
```
We also need the ability to extract the `next token` (in this case, the next element in the input array).
```python
def next_token():
    i = pos_cur()
    pos_set(i+1)
    return input[i]
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
       if not t(): return false
   return true
```

The other corresponds to the alternatives for each production. If any alternative succeeds, then the parsing succeeds.
```python
def do_alt(alt_terms):
    for t in alt_terms:
        o_pos = pos_cur()
        if t(): return true
        pos_set(o_pos)
    return false
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
# E = T "+" E
def E_1():
    return do_seq([T, PLUS, E])
# E = T
def E_1():
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
def T_1():
    return match('1')
def T_2():
    return match('0')
```
The only thing that remains is `PLUS`, which is again simple enough
```python
def PLUS():
    return match('+')
```
