---
published: false
title: Recursive descent parsing with Parsing Expression Grammars (PEG)
layout: post
comments: true
tags: parsing
---

In the [previous](/2018/09/05/top-down-parsing/) post, I showed how to write a simple context-free language parser by hand using recursive descent -- that is using a set of mutually recursive procedures. Actually, I lied when I said context-free. The common hand-written parsers are usually an encoding of a kind of grammar called _Parsing Expression Grammar_ or _PEG_ for short.

The difference between _PEG_ and a _CFG_ is that
* _PEG_ does not admit ambiguity. In particular, _PEG_ uses ordered choice in its alternatives.
* Due to the ordered choice, the ordering of alternatives is important.

A few interesting things about _PEG_:
* We know that _L(PEG)_ is not a subset of _L(CFG)_ (There are [languages](https://stackoverflow.com/a/46743864/1420407) that can be expressed with a _PEG_ that can not be expressed with a _CFG_).
* We do not know if _L(PEG)_ is a superset of _CFL_. However, given that all [PEGs can be parsed in O(n)](https://en.wikipedia.org/wiki/Parsing_expression_grammar), and the best general _CFG_ parsers can only reach _O(n^2.31)_ due to the equivalance to boolean matrix multiplication ([Valiant 1975](/references#valiant1975general))([Lee 2002](/references#lee2002fast)). 
* We do know that _L(PEG)_ is at least as large as deterministic _CFL_.
* We also [know](https://arxiv.org/pdf/1304.3177.pdf) that an _LL(1)_ grammar can be interpreted either as a _CFG_ or a _PEG_ and it will describe the same language. Further, any _LL(k)_ grammar can be translated to _L(PEG)_, but reverse is not always true -- [it will work only if the PEG lookahead pattern can be reduced to a DFA](https://stackoverflow.com/a/46743864/1420407).


```python
def match_rule(rule, text, at):
    if literal(rule):
       return (text[at:].starts_with(rule), len(rule))
    tokens = split(rule)
    for token in tokens:
        result, l = match_token(token, text, at)
        if not result: return False
        at += l
    return (True, len)

def match_token(token, text, at):
    rules = grammar[token]
    for rule in rules:
        res, l = match_rule(rule, text, at)
        if res: return (res, l)
    return (False, 0)
```


```python
import sys
import functools

term_grammar = {
    'expr': [
        ['term', 'add_op', 'expr'],
        ['term']],
    'term': [
        ['fact', 'mul_op', 'term'],
        ['fact']],
    'fact': [
        ['digits'],
        ['(','expr',')']],
    'digits': [
        ['digit','digits'],
        ['digit']],
    'digit': [[str(i)] for i in list(range(10))],
    'add_op': [['+'], ['-']],
    'mul_op': [['*'], ['/']]
}

class peg_parse:
    def __init__(self, grammar):
        self.grammar = {k:[tuple(l) for l in rules] for k,rules in grammar.items()}

    def literal_match(self, part, text, tfrom):
        return (tfrom + len(part), (part, [])) if text[tfrom:].startswith(part) else (tfrom, None)

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, tfrom=0):
        rules = self.grammar[key]
        rets = (self.unify_line(rule, text, tfrom) for rule in rules)
        tfrom, res = next((ret for ret in rets if ret[1] is not None), (tfrom, None))
        return (tfrom, (key, res) if res is not None else None)

    @functools.lru_cache(maxsize=None)
    def unify_line(self, parts, text, tfrom):
        def is_symbol(v): return v in self.grammar

        results = []
        for part in parts:
            tfrom, res = (self.unify_key if is_symbol(part) else self.literal_match)(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

def main(to_parse):
    result = peg_parse(term_grammar).unify_key('expr', to_parse)
    assert (len(to_parse) - result[0]) == 0
    print(result[1])

if __name__ == '__main__': main(sys.argv[1])
```
