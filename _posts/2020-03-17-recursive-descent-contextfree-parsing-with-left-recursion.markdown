---
published: true
title: Recursive Descent Context Free Parsing with Left Recursion
layout: post
comments: true
tags: recursivedescent, parsing, cfg, leftrecursion
categories: post
---
Previously, we had [discussed](/post/2018/09/06/peg-parsing/) how a simple PEG parser, and a CFG parser can be constructed. At that time, I had mentioned that left-recursion was still to be implemented. Here is one way to implement left recursion correctly for the CFG parser.

For ease of reference, here was our original parser.
```python
class cfg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, tfroms):
        tfroms_ = []
        if key not in self.grammar:
            for ttill, tkey in tfroms:
                if text[ttill:].startswith(key):
                    tfroms_.append((ttill + len(key), (tkey + [key])))
                else:
                    continue
        else:
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfroms)
                tfroms_.extend(new_tfroms)
        return tfroms_

    def unify_rule(self, parts, text, tfroms):
        if not tfroms: return []
        for part in parts:
            tfroms = self.unify_key(part, text, tfroms)
        return tfroms

def main(to_parse):
    result = cfg_parse(term_grammar).unify_key('<expr>', to_parse, [(0, [])])
    for till in result:
        print(till)

if __name__ == '__main__':
    main(sys.argv[1])
```
This will of course fail when given a grammar such as below:
```python
import string
grammar = {
    "<start>": [ ["<E>"] ],
    "<E>": [
        ["<E>", "+", "<E>"],
        ["<E>", "-", "<E>"],
        ["<E>", "*", "<E>"],
        ["<E>", "/", "<E>"],
        ["(", "<E>", ")"],
        ["<digits>"],
        ],
    "<digits>": [["<digits>", "<digit>"], ["<digit>"]],
    "<digit>": [[str(i)] for i in string.digits]
}
```
The problem here is that `<E>` is left recursive. So, a naive implementation such as above does not know when to stop recursing when
it tries to unify `<E>`. The solution here is to look for *any* means to identify that the recursion has gone on longer than necessary.
Here is one such technique. The idea is to look at the minimum number of characters necessary to complete parsing if we use a 
particular rule. If the rule requires more characters than what is present in the input string, then we know not to use that rule. 

### Implementation

First, we compute the minimum length of each nonterminal statically. The minimum length of a nonterminal is defined as the length of minimum number of terminal symbols needed to satisfy that nonterminal from the grammar. The length of a terminal is obviously the length of that terminal symbol. From this definition, the minimum length of a nonterminal is the minimum of the minimum lengths of
any of the rules corresponding to it. The minimum length of a rule is the sum of the minimum lengths of each of its token symbols.

```python
import math
class cfg_parse:
    def __init__(self, grammar):
        self.grammar = grammar
        self.min_len = {k: self._key_minlength(k, set()) for k in grammar}

    def _rule_minlength(self, rule, seen):
        return sum([self._key_minlength(k, seen) for k in rule])

    def _key_minlength(self, key, seen):
        if key not in self.grammar: return len(key)
        if key in seen: return math.inf
        return min([self._rule_minlength(r, seen | {key}) for r in self.grammar[key]])
```
The length of multiple keys can be computed as follows
```python
class cfg_parse(cfg_parse):
    def len_of_parts(self, parts):
        return self._rule_minlength(parts, set())
```
Now, all it remains is to intelligently stop parsing whenever the minimum length of the remaining parts
to parse becomes larger than the length of the remaining text.
```python
class cfg_parse(cfg_parse):
    def unify_key(self, key, text, tfroms, min_len):
        tfroms_ = []
        if key not in self.grammar:
            for ttill, tkey in tfroms:
                if text[ttill:].startswith(key):
                    tfroms_.append((ttill + len(key), (tkey + [key])))
                else:
                    continue
        else:
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfroms, min_len)
                tfroms_.extend(new_tfroms)
        return tfroms_

    def unify_rule(self, parts, text, tfroms, min_len):
        new_tfroms = []
        for tfrom in tfroms:
            till,_k = tfrom
            tfs = [tfrom]
            for i,part in enumerate(parts):
                len_of_remaining = self.len_of_parts(parts[i+1:]) + min_len
                if not tfs or len_of_remaining + till >= len(text):
                    tfs = []
                    break
                tfs = self.unify_key(part, text, tfs, len_of_remaining)
            new_tfroms.extend(tfs)
        return new_tfroms
```
The driver
```python
import sys
def main(to_parse):
    p = cfg_parse(grammar)
    result = p.unify_key('<start>', to_parse, [(0, [])], 0)
    for l,till in result:
        if l == len(to_parse):
            print(till)

if __name__ == '__main__':
    main(sys.argv[1])
```
Usage:
It correctly accepts valid strings
```shell
$ python3  cfgparse.py '112*(4+(3-4))'
['1', '1', '2', '*', '(', '4', '+', '(', '3', '-', '4', ')', ')']
```
and correctly rejects invalid ones
```shell
$ python3  cfgparse.py '112(4+(3-4))'
```
We still need to make this into a parser. This can be done by storing a better datastructure in the second part of the list of successful parses.
