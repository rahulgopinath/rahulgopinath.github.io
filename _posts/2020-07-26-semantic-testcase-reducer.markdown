---
published: false
title: Semantic Testcase Reducer
layout: post
comments: true
tags: deltadebug, testcase reducer, cfg, generator
categories: post
---
Previously, we had [discussed](/post/2019/12/03/ddmin/) how delta-debugging worked, and I had explained at that time that when it comes
to preserving semantics, the only options are either custom passes such as CReduce or commandeering the generator as done by Hypothesis.
Of the two, the Hypothesis approach is actually more generalizable to arbitrary generators. Hence we will look at how it is done.

```
import random
import string
import sys
random.seed(int(sys.argv[1]))

class SimpleFuzzer:
    def __init__(self, grammar):
        self.grammar = grammar


    def tree_to_str(self, tree):
        name, children = tree
        if not children: return name
        return ''.join(self.tree_to_str(c) for c in children)


    def select(self, lst):
        return random.choice(lst)

    def unify_key(self, key):
        if not key in self.grammar:
            return (key, [])
        return (key, self.unify_rule(self.select(self.grammar[key])))

    def unify_rule(self, rule):
        return [self.unify_key(token) for token in rule]

    def fuzz(self, key):
        v = self.unify_key(key)
        return self.tree_to_str(v)

class ComplexFuzzer(SimpleFuzzer):
    def __init__(self, grammar):
        self.grammar = grammar
        self.vars = []
        self._vars = []

    def unify_rule(self, rule):
        ret = []
        for token_ in rule:
            if isinstance(token_, tuple):
                token = token_[0]
                fns = token_[1]
            else:
                token = token_
                fns = {}
            pre = fns.get('pre', lambda s, t, x: x())
            post = fns.get('post', lambda s, x: x)
            val = pre(self, token, lambda: self.unify_key(token))
            v = post(self, val)
            ret.append(v)
        return ret

def defining_var(o, val):
    v = o.tree_to_str(val)
    o._vars.append(v)
    return val

def defined_var(o, token, val):
    assert token == '<var>'
    #v = val()
    if not o.vars:
        return ('00', [])
    else:
        return (o.select(o.vars, '000'), [])

def sync(o, val):
    o.vars.extend(o._vars)
    o._vars.clear()
    return val

class ChoiceFuzzer(ComplexFuzzer):
    def __init__(self, grammar, choices):
        self.grammar = grammar
        self.vars = []
        self._vars = []
        self.choices = choices
        self.default = {
                '<start>': 'a=0;\n',
                '<assignments>': 'a=0;\n',
                '<assign>': 'a=0',
                '<assign>': 'a=0',
                '<expr>': '0',
                '<digit>': '0',
                '<var>': '0'
                }

    def unify_key(self, key):
        def stem(k): return '<%s>' % k[1:-1].split()[0]
        if not key in self.grammar:
            return (key, [])
        default = self.default[stem(key)]
        return (key, self.unify_rule(self.select(self.grammar[key], default)))

    def select(self, lst, default):
        return self.choices.choice(lst, default)

grammar = {
        '<start>' : [[ '<assignments>' ]],
        '<assignments>': [['<assign>', (';\n', {'post':sync})], ['<assign>', (';\n', {'post':sync}), '<assignments>']],
        '<assign>': [[('<var>', {'post':defining_var}), ' = ', '<expr>']],
        '<expr>': [
            ['<expr>', ' + ', '<expr>'],
            ['<expr>', ' - ', '<expr>'],
            ['(', '<expr>', ')'],
            [('<var>', {'pre':defined_var})],
            ['<digit>']],
        '<digit>': [['0'], ['1']],
        '<var>': [[i] for i in string.ascii_lowercase]
}


class ChoiceSeq:
    def __init__(self, ints=None):
        self.index = -1
        if ints is None:
            self.ints = []
            self.choose_new = True
        else:
            self.ints = ints
            self.choose_new = False

    def i(self):
        if self.choose_new:
            self.index += 1
            self.ints.append(random.randrange(10))
            return self.ints[self.index]
        else:
            self.index += 1
            return self.ints[self.index]

    def choice(self, lst, default):
        v = self.i()
        if v == -1:
            return default
        else:
            return lst[v % len(lst)]

grammar = {
        '<start>' : [[ '<assignments>' ]],
        '<assignments>': [['<assign>', (';\n', {'post':sync})], ['<assign>', (';\n', {'post':sync}), '<assignments>']],
        '<assign>': [[('<var>', {'post':defining_var}), ' = ', '<expr>']],
        '<expr>': [
            ['<expr 1>', ' + ', '<expr 1>'],
            ['<expr 1>', ' - ', '<expr 1>'],
            ['(', '<expr 1>', ')'],
            [('<var>', {'pre':defined_var})],
            ['<digit>']],
        '<digit>': [['0'], ['1']],
        '<var>': [[i] for i in string.ascii_lowercase],

        '<expr 1>': [
            ['<expr 2>', ' + ', '<expr 2>'],
            ['<expr 2>', ' - ', '<expr 2>'],
            ['(', '<expr 2>', ')'],
            [('<var>', {'pre':defined_var})],
            ['<digit>']],

        '<expr 2>': [
            [('<var>', {'pre':defined_var})],
            ['<digit>']],
}

def pred(v):
    if '((' in v and '))' in v:
        return True
    return False

def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        if i > 0:
            stitched =  instr[:i-1] + [-1] + instr[i+part_len:]
        else:
            stitched =  instr[:i] + [-1] + instr[i+part_len+1:]
        if causal(stitched): return i, stitched
    return -1, instr

def ddmin(cur_str, causal_fn):
    start, part_len = 0, len(cur_str) // 2
    while part_len >= 1:
        start, cur_str = remove_check_each_fragment(cur_str, start, part_len, causal_fn)
        if start != -1:
            if not [i for i in cur_str if i != -1]: return ''
        else:
            start, part_len = 0, part_len // 2
    return cur_str


choices = ChoiceSeq()

c1 = ChoiceFuzzer(grammar, choices)
v1 = c1.fuzz('<start>')
#print(pred(v1), "\n", v1)
#print(c1.vars)
#print(c1.choices.ints)

choices = ChoiceSeq(c1.choices.ints)
c2 = ChoiceFuzzer(grammar, choices)
v2 = c2.fuzz('<start>')
#print(pred(v2), "\n", v2)
#print(c2.vars)
#print(c2.choices.ints)

# print(repr(v1), repr(v2))
assert v1 == v2
#print(c2.choices.ints)


def causal(ints):
    choices = ChoiceSeq(ints)
    cf = ChoiceFuzzer(grammar, choices)
    try:
        #print(ints)
        v = cf.fuzz('<start>')
        #print(v)
        p = pred(v)
        #print(p)
        return p
    except IndexError:
        # print('no')
        return False

if pred(v2):
    newv = ddmin(c1.choices.ints, causal)
    choices = ChoiceSeq(newv)
    cf = ChoiceFuzzer(grammar, choices)
    # print(c1.choices.ints)
    print('original:', v1, len(c1.choices.ints))

    while True:
        newv = ddmin(cf.choices.ints, causal)
        if len(newv) >= len(cf.choices.ints):
            break
        #print(len(newv))
        cf = ChoiceFuzzer(grammar, ChoiceSeq(newv))

    cf = ChoiceFuzzer(grammar, ChoiceSeq(newv))
    print('minimal:', cf.fuzz('<start>'), len(newv))
    print(cf.choices.ints)

```
