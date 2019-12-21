---
published: true
title: Recursive descent parsing with Parsing Expression Grammars (PEG)
layout: post
comments: true
tags: parsing
categories: post
---

In the [previous](/2018/09/05/top-down-parsing/) post, I showed how to write a simple recursive descent parser by hand -- that is using a set of mutually recursive procedures. Actually, I lied when I said context-free. The common hand-written parsers are usually an encoding of a kind of grammar called _Parsing Expression Grammar_ or _PEG_ for short.

The difference between _PEG_ and a _CFG_ is that _PEG_ does not admit ambiguity. In particular, _PEG_ uses ordered choice in its alternatives. Due to the ordered choice, the ordering of alternatives is important.

A few interesting things about _PEG_:
* We know that _L(PEG)_ is not a subset of _L(CFG)_ (There are [languages](https://stackoverflow.com/a/46743864/1420407) that can be expressed with a _PEG_ that can not be expressed with a _CFG_ -- for example, $$a^nb^nc^n$$).
* We do not know if _L(PEG)_ is a superset of _CFL_. However, given that all [PEGs can be parsed in $$O(n)$$](https://en.wikipedia.org/wiki/Parsing_expression_grammar), and the best general _CFG_ parsers can only reach $$O(n^{(3-\frac{e}{3})})$$ due to the equivalance to boolean matrix multiplication ([Valiant 1975](/references#valiant1975general))([Lee 2002](/references#lee2002fast)). 
* We do know that _L(PEG)_ is at least as large as deterministic _CFL_.
* We also [know](https://arxiv.org/pdf/1304.3177.pdf) that an _LL(1)_ grammar can be interpreted either as a _CFG_ or a _PEG_ and it will describe the same language. Further, any _LL(k)_ grammar can be translated to _L(PEG)_, but reverse is not always true -- [it will work only if the PEG lookahead pattern can be reduced to a DFA](https://stackoverflow.com/a/46743864/1420407).

The problem with what we did in the previous post is that it is a rather naive implementation. In particular, there could be a lot of backtracking, which can make the runtime explore. One solution to that is incorporating memoization. Since we start with automatic generation of parser from a grammar (unlike previously, where we explored a handwritten parser first), we will take a slightly different tack in writing the algorithm.

The idea behind a simple _PEG_ parser is that, you try to unify the string you want to match with the corresponding key in the grammar. If the key is not present in the grammar, it is a literal, which needs to be matched with string equality.
If the key is present in the grammar, get the corresponding productions (rules) for that key,  and start unifying each rule one by one on the string to be matched.

```python
def unify_key(key, text, at):
   if key not in grammar:
       return (True, at + len(key)) if text[at:].startswith(key) else (False, at)
   rules = grammar[key]
   for rule in rules:
       res, l = unify_rule(rule, text, at)
       if res is not None: return (res, l)
   return (False, 0)
```
For unifying rules, the idea is similar. We take each token in the rule, and try to unify that token with the string to be matched. We rely on `unify_key` for doing the unification of the token. if the unification fails, we return empty handed.
```python
def unify_rule(rule, text, at):
    for token in rule:
          result, at = unify_key(token, text, at)
          if result is None: return (False, at)
    return (True, at)
 ```
When we implemented the `unify_key`, we made an important decision, which was that, we return as soon as a match was found. This is what distinguishes a `PEG` parser from a general `CFG` parser. In particular it means that rules have to be ordered.
That is, the following grammar wont work:

```ebnf
ifmatch = IF (expr) THEN stmts
        | IF (expr) THEN stmts ELSE stmts
```
It has to be written as the following so that the rule that can match the longest string will come first. 
```ebnf
ifmatch = IF (expr) THEN stmts ELSE stmts
        | IF (expr) THEN stmts
```
<!-- It is also at this place that we have the big question. Are there two rules such that given two strings, such that the order of strings by longest match is different depending on the rule chosen? If no such conflicting orders can be found given any two rules, then _PEG_s are a superset of _CFG_. On the other hand, if there exist such a pair, then _CFG_s are not a strict subset of _PEG_s.-->
If we now parse an `if` statement without else using the above grammar, such a `IF (a=b) THEN return 0`, the first rule will fail, and the parse will start for the second rule again at `IF`. This backtracking is unnecessary as one can see that `IF (a=b) THEN return 0` is already parserd by all terms in the second rule. What we want is to save the old parses so that we can simply return the already parsed result. That is,
```python
   if seen((token, text, at)):
       return old_result
```
Fortunately, Python makes this easy using `functools.lru_cache` which provides cheap memoization to functions. Adding memoizaion, and reorganizing code, we have our _PEG_ parser.

```python
import sys
import functools

term_grammar = {
    '<expr>': [
        ['<term>', '<add_op>', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '<mul_op>', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['digit']],
    '<digit>': [[str(i)] for i in list(range(10))],
    '<add_op>': [['+'], ['-']],
    '<mul_op>': [['*'], ['/']]
}

class peg_parse:
    def __init__(self, grammar):
        self.grammar = {k:[tuple(l) for l in rules] for k,rules in grammar.items()}

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

def main(to_parse):
    result = peg_parse(term_grammar).unify_key('expr', to_parse)
    assert (len(to_parse) - result[0]) == 0
    print(result[1])

if __name__ == '__main__': main(sys.argv[1])
```

What we have here is only a subset of _PEG_ grammar. A _PEG_ grammar can contain

* Sequence: e1 e2
* Ordered choice: e1 / e2
* Zero-or-more: e*
* One-or-more: e+
* Optional: e?
* And-predicate: &e -- match `e` but do not consume any input
* Not-predicate: !e

We are yet to provide _e*_, _e+_, and _e?_. However, these are only conveniences. One can easily modify any _PEG_ that uses them to use grammar rules instead. The effect of predicates on the other hand can not be easily produced.  However, the lack of predicates does not change ([Ford 2004](https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf)) the class of languages that such grammars can match, and even without the predicates, our _PEG_ can be useful for easily representing a large category of programs.

Note: This implementation will blow the stack pretty fast if we attempt to parse any expressions that are reasonably large (where some node in the derivation tree has a depth of 500) because Python provides very limited stack. One
can improve the situation slightly by inlining the `unify_rule()`.

```python
class peg_parse:
    def __init__(self, grammar):
        self.grammar = {k:[tuple(l) for l in rules] for k,rules in grammar.items()}

    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)

        rules = self.grammar[key]
        for rule in rules:
            results = []
            tfrom = at
            for part in rule:
                tfrom, res_ = self.unify_key(part, text, tfrom)
                if res_ is None:
                    l, results = tfrom, None
                    break
                results.append(res_)
            l, res = tfrom, results
            if res is not None: return l, (key, res)
        return (0, None)
```

This gets us to derivation trees with at a depth of 1000 (or more if we increase the `sys.setrecursionlimit()`). We can also turn this to a completely iterative solution if we simulate the stack (formal arguments, locals, return value) ourselves rather than relying on the Python stack frame.
