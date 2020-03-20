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

    def unify_key(self, key, text, tfrom):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom)
                for at, nt in new_tfroms:
                    tfroms_.append((at, (key, nt)))
            return tfroms_
        assert False

    def unify_rule(self, parts, text, tfrom):
        tfroms = [(tfrom, [])]
        for part in parts:
            new_tfroms = []
            for at, nt in tfroms:
                tfs = self.unify_key(part, text, at)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms

def main(to_parse):
    p = cfg_parse(term_grammar)
    result = p.unify_key('<start>', to_parse, 0)
    for l,till in result:
        if l == len(to_parse):
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
any of the rules corresponding to it. The minimum length of a rule is the sum of the minimum lengths of each of its token symbols. If the same symbol is encountered again while computing, we return `infinity`.

(Another way to think about the minimum length is as the length of the minimal string produced when the grammar is used as a producer starting from the given nonterminal. The reason for `infinity` for recursion becomes clear --- the producer cannot terminate.).

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
        return sum(self.min_len.get(p, len(p)) for p in parts)
```
Now, all it remains is to intelligently stop parsing whenever the minimum length of the remaining parts
to parse becomes larger than the length of the remaining text.
```python
class cfg_parse(cfg_parse):
    def unify_key(self, key, text, tfrom, min_length):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom, min_length)
                for at, nt in new_tfroms:
                    tfroms_.append((at, (key, nt)))
            return tfroms_
        assert False

    def unify_rule(self, parts, text, tfrom, min_len):
        tfroms = [(tfrom, [])]
        for i,part in enumerate(parts):
            len_of_remaining = self.len_of_parts(parts[i+1:]) + min_len
            new_tfroms = []
            for at, nt in tfroms:
                if len_of_remaining + at >= len(text):
                    continue
                tfs = self.unify_key(part, text, at, len_of_remaining)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms
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
('<start>', [('<E>', [('<E>', [('<digits>', [('<digits>', [('<digits>', [('<digit>', [('1', [])])]), ('<digit>', [('1', [])])]), ('<digit>', [('2', [])])])]), ('*', []), ('<E>', [('(', []), ('<E>', [('<E>', [('<digits>', [('<digit>', [('4', [])])])]), ('+', []), ('<E>', [('(', []), ('<E>', [('<E>', [('<digits>', [('<digit>', [('3', [])])])]), ('-', []), ('<E>', [('<digits>', [('<digit>', [('4', [])])])])]), (')', [])])]), (')', [])])])])
```
and correctly rejects invalid ones
```shell
$ python3  cfgparse.py '112(4+(3-4))'
```
Note that our implementation relies on there being a minimal length. What if there are empty string derivations? Unfortunately, our parser can fail in these scenarios:

```python
ABgrammar = {
        '<start>': [['<A>']],
        '<A>': [
            ['<A>', '<B>'],
            ['a']],
        '<B>': [['b'], ['']]
}

Agrammar = {
        '<start>': [['<A>']],
        '<A>': [['<A>'], ['a']],
}
```
The issue is empty strings causing the minimal length to be zero. So, we are unable to make progress. One option
is to completely remove empty strings from the grammar. While that is a better option than refactoring out left
recursion, it is a bit unsatisfying. Is there a better way?

Another option is to look for a different stopping condition. The idea is that in left recursion, the left recursions
always have to make progress (the non-progress-making left recursions can be generated from the single progress making
left recursion, so we can discard the non-progress-making left recursions). That means that one would never
have more number of recursions of the same key than there are remaining letters. Here is an attempt to implement this
stopping condition.
```python
import copy
class cfg_parse(cfg_parse):
    def unify_key(self, key, text, tfrom, min_len, seen):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom, min_len, seen)
                tfroms_.extend(new_tfroms)
            return tfroms_

    def unify_rule(self, parts, text, tfrom, min_len, seen):
        tfroms = [tfrom]
        for i,part in enumerate(parts):
            len_of_remaining = self.len_of_parts(parts[i+1:]) + min_len
            new_tfroms = []

            if self.len_of_parts(parts[i+1:]) == 0:
                if part in seen and (seen[part][0] + seen[part][1]) > len(text):
                    # each call to a left recursion should consume at least
                    # one token. So, if we count from where the left
                    # recursion originally started (todo),
                    # that + #recursions should be <= len(text)
                    return []

            for at, nt in tfroms:
                # if current parse + the minimum required length is > length of
                # text then no more parsing. (progress)
                if at + len_of_remaining > len(text):
                    continue

                # if the remaining parts have a minimum length zero, then
                # we wont be able to use our progress to curtail the recursion.
                # so use the number of recursions instead.
                if self.len_of_parts(parts[i+1:]) == 0:
                    my_seen = copy.deepcopy(seen)
                    if part in my_seen:
                        my_seen[part][1] += 1
                    else:
                        my_seen[part] = [at, 0]
                else:
                    my_seen = {}
                tfs = self.unify_key(part, text, at, len_of_remaining, my_seen)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms
```
This seems to work. However, one question remains unanswered. One could in
principle use the second stopping condition on its own, without the first one.
So, why use the first stopping condition at all? The reason is that, in my
experiments at least, the second condition is much more expensive than the first
So, we only use the second when we absolutely need to.


### PEG parser

Can we apply the same technique on a PEG parser? Here is one implementation

```python
import math
import sys
import functools
import string

expr_grammar = {
    "<start>": [ ["<E>"] ],
    "<E>": [
        ["<E>", "+", "<E>"],
        ["<E>", "-", "<E>"],
        ["<E>", "*", "<E>"],
        ["<E>", "/", "<E>"],
        ["(", "<E>", ")"],
        ["<digits>"],
        ],
    "<digits>": [["<digit>", "<digits>"], ["<digit>"]],
    "<digit>": [[str(i)] for i in string.digits]
}

class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar
        self.grammar = grammar
        self.min_len = {k: self._key_minlength(k, set()) for k in grammar}

    def _rule_minlength(self, rule, seen):
        return sum([self._key_minlength(k, seen) for k in rule])

    def _key_minlength(self, key, seen):
        if key not in self.grammar: return len(key)
        if key in seen: return math.inf
        return min([self._rule_minlength(r, seen | {key}) for r in self.grammar[key]])

    def len_of_parts(self, parts):
        return sum(self.min_len.get(p, len(p)) for p in parts)
        
    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at, min_len):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at, min_len)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom, min_len):
        results = []
        for i,part in enumerate(parts):
            len_of_remaining = self.len_of_parts(parts[i+1:]) + min_len
            if len_of_remaining + tfrom >= len(text):
                return tfrom, None
            tfrom, res = self.unify_key(part, text, tfrom, len_of_remaining)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

def main(to_parse):
    p = peg_parse(expr_grammar)
    result = p.unify_key('<start>', to_parse, 0, 0)
    assert (len(to_parse) - result[0]) == 0
    print(result[1])

if __name__ == '__main__': main(sys.argv[1])                                                                                      
```
Using it:
```shell
$ python3 peg.py '123+(45+1)'
('<start>', [('<E>', [('<E>', [('<digits>', [('<digit>', [('1', [])]), ('<digits>', [('<digit>', [('2', [])]), ('<digits>', [('<digit>', [('3', [])])])])])]), ('+', []), ('<E>', [('(', []), ('<E>', [('<E>', [('<digits>', [('<digit>', [('4', [])]), ('<digits>', [('<digit>', [('5', [])])])])]), ('+', []), ('<E>', [('<digits>', [('<digit>', [('1', [])])])])]), (')', [])])])])
```

