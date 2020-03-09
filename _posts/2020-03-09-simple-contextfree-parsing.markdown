---
published: false
title: Simple Combinatory Parsing For Context Free Languages
layout: post
comments: true
tags: parsing, cfg
categories: post
---

```python
import sys

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
        ['<digit>']],
    '<digit>': [[str(i)] for i in list(range(10))],
    '<add_op>': [['+'], ['-']],
    '<mul_op>': [['*'], ['/']]
}

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
