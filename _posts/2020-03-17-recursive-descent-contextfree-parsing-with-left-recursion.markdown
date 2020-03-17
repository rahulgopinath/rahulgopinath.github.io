---
published: true
title: Recursive Descent Context Free Parsing with Left Recursion
layout: post
comments: true
tags: recursivedescent, parsing, cfg, leftrecursion
categories: post
---

The basic idea is to count the length of remaining terminal symbols to obtain the minimum length needed for each rule.

Ouf grammar
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
The implementation
```python
import math
import sys

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

    def len_of_parts(self, parts):
        v = sum([self.min_len[p] if p in self.grammar else len(p) for p in parts])
        return v
```
The driver
```python
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
```shell
$ python3  cfgparse.py '112*(4+(3-4))'
['1', '1', '2', '*', '(', '4', '+', '(', '3', '-', '4', ')', ')']
```
