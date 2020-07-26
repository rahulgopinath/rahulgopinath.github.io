---
published: true
title: Semantic Testcase Reducer
layout: post
comments: true
tags: deltadebug, testcase reducer, cfg, generator
categories: post
---
Previously, we had [discussed](/post/2019/12/03/ddmin/) how delta-debugging worked, and I had explained at that time that when it comes
to preserving semantics, the only options are either custom passes such as [CReduce](http://embed.cs.utah.edu/creduce/)
or commandeering the generator as done by [Hypothesis](https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis-python/src/hypothesis/internal/conjecture/shrinker.py).
Of the two, the Hypothesis approach is actually more generalizable to arbitrary generators. Hence we will look at how it is done. For ease
of naming, I will call this approach the _generator reduction_ approach. Note that we use the simple `delta debug` on the choice sequences.
This is different from `Hypothesis` in that `Hypothesis` uses a number of custom passes rather than `delta debug`. For further information
on Hypothesis, please see the [paper](https://drmaciver.github.io/papers/reduction-via-generation-preview.pdf) _Test-Case Reduction via Test-Case Generation:Insights From the Hypothesis Reducer_ by _David R. MacIver_ and _Alastair F. Donaldson_ at ECOOP 2020.

For the _generator reduction_ to work, we need a generator in the first place. So, we start with a rather simple generator that we discussed
[previously](/post/2019/05/28/simplefuzzer-01/).

```python
class LimitFuzzer:
    def tree_to_str(self, tree):
        name, children = tree
        if not children: return name
        return ''.join(self.tree_to_str(c) for c in children)

    def select(self, lst):
        return random.choice(lst)

    def symbol_cost(self, grammar, symbol, seen):
        if symbol in self.key_cost: return self.key_cost[symbol]
        if symbol in seen:
            self.key_cost[symbol] = float('inf')
            return float('inf')
        v = min((self.expansion_cost(grammar, rule, seen | {symbol})
                    for rule in grammar.get(symbol, [])), default=0)
        self.key_cost[symbol] = v
        return v

    def expansion_cost(self, grammar, tokens, seen):
        return max((self.symbol_cost(grammar, token, seen)
                    for token in tokens if token in grammar), default=0) + 1

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return (key, self.gen_rule(self.select(rules), depth+1, max_depth))

    def gen_rule(self, rule, depth, max_depth):
        return [self.gen_key(token, depth, max_depth) for token in rule]

    def fuzz(self, key='<start>', max_depth=10):
        return self.tree_to_str(self.gen_key(key=key, depth=0, max_depth=max_depth))

    def __init__(self, grammar):
        self.grammar = grammar
        self.key_cost = {}
        self.cost = self.compute_cost(grammar)

    def compute_cost(self, grammar):
        cost = {}
        for k in grammar:
            cost[k] = {}
            for rule in grammar[k]:
                cost[k][str(rule)] = self.expansion_cost(grammar, rule, set())
        return cost
```

The driver is as follows. Note that the grammar describes a simple assignment language.

```python
if __name__ == '__main__':
    import random
    import string
    import sys
    random.seed(int(sys.argv[1]))

    assignment_grammar = {
            '<start>' : [[ '<assignments>' ]],
            '<assignments>': [['<assign>'], ['<assign>', ';\n', '<assignments>']],
            '<assign>': [['<var>', ' = ', '<expr>']],
            '<expr>': [
                ['<expr>', ' + ', '<expr>'],
                ['<expr>', ' - ', '<expr>'],
                ['(', '<expr>', ')'],
                ['<var>'],
                ['<digit>']],
            '<digit>': [['0'], ['1']],
            '<var>': [[i] for i in string.ascii_lowercase]
    }
    print(LimitFuzzer(assignment_grammar).fuzz('<start>'))
```
Running it.
```bash
$ python3 lf.py 5
o = (h) + r - 0 + i - f - 1 + 0 + 0 - 1 + (0) + j - 1 - f + (((0)) + 1) - (((w))) + (p - a + m - l + s) - b + 0 - l - 1 + 1;
s = ((c + (1) - ((1)) - ((0))));
p = 1 + 1 - (u) + e + k + 1 - 0 - l + j + t - 1 - w - (i)
```
As you can see, the context free grammar `assignment_grammar` generates assignment expressions. However, it tends to
use variables before they are defined. We want to avoid that. That is a context sensitive feature, which we incorporate
by a small modification to the fuzzer as follows:

```python
class ComplexFuzzer(LimitFuzzer):
    def __init__(self, grammar):
        def cfg(g):
            return {k: [self.cfg_rule(r) for r in g[k]] for k in g}
        super().__init__(cfg(grammar))
        self.cfg_grammar = self.grammar
        self.grammar = grammar
        self.vars = []
        self._vars = []

    def cfg_rule(self, rule):
        return [t[0] if isinstance(t, tuple) else t for t in rule]

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule) for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return (key, self.gen_rule(self.select(rules), depth+1, max_depth))

    def gen_rule(self, rule, depth, max_depth):
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
            val = pre(self, token, lambda: self.gen_key(token, depth, max_depth))
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
        return (o.select(o.vars), [])

def sync(o, val):
    o.vars.extend(o._vars)
    o._vars.clear()
    return val
```
As you can see, we now allow only defined variables to be used for later expansion. Note that the modifications assume the knowledge of the `<var>` 
key in the grammar defined in the driver.

The driver now includes a context sensitive grammar.
```python
if __name__ == '__main__':
    import random
    import string
    import sys
    random.seed(int(sys.argv[1]))
    assignment_grammar = {
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
    c = ComplexFuzzer(assignment_grammar)
    print(c.fuzz('<start>'))
    print(c.vars)
```
Running it
```bash
$ python3   lf.py 6 
b = 1 - (((00) + 00 - 0)) + 1 - 0;
c = (b);
y = (0 + (b) + 0) - (1 - ((0)));
d = 1;

['b', 'c', 'y', 'd']
```
As you can see, the variables used are only those that were defined earlier. So, how do we minimize such a generated string?

For the answer, we need to modify our fuzzer a bit more. We need to make it take a stream of integers which are interpreted
as the choices at each step.

```python
class ChoiceFuzzer(ComplexFuzzer):
    def __init__(self, grammar, choices):
        self.grammar = grammar
        self.vars = []
        self._vars = []
        self.choices = choices

    def select(self, lst):
        return self.choices.choice(lst)
```
The choice sequence both keeps track of all choices made, and also allows one to reuse previous choices.
```python
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

    def choice(self, lst):
        return lst[self.i() % len(lst)]
```
The driver is as follows
```python
if __name__ == '__main__':
    import random
    import string
    import sys
    random.seed(int(sys.argv[1]))
    assignment_grammar = {
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
    choices = ChoiceSeq()

    c = ChoiceFuzzer(assignment_grammar, choices)
    print(c.fuzz('<start>'))
    print(c.vars)
    print(c.choices.ints)
```
Running it
```bash
$ python3   lf.py 6
e = (1) + 1 + 00 + 00 - 00 + 00 - 0 + 1;
f = 1 - e - 1 + 1 + e - e + e + 1 - 1 - e - e;
e = e;
c = 1;
d = (f + 0 + e - e + (e));

['e', 'f', 'e', 'c', 'd']
[9, 1, 7, 4, 0, 0, 2, 9, 7, 5, 5, 0, 4, 7, 3, 6, 8, 8, 1, 3, 9, 8, 4, 9, 1, 6, 5, 1, 5, 6, 4, 7, 1, 3, 4, 1, 0, 9, 3, 5, 7, 3, 8, 9, 8, 0, 5, 3, 9, 6, 4, 5, 9, 1, 1, 8, 8, 3, 1, 9, 4, 4, 3, 6, 7, 3, 2, 9, 3, 8, 0, 3, 2, 0, 5, 8, 9, 9, 4, 5, 6, 8, 6, 4, 2, 7, 0, 2]
```
As you can see, the choice sequence is printed out at the end. The same sequence can be used later, to produce the same string. We use this
in the next step. Now, all that we need is to hook up the predicate for ddmin, and its definitions.

First, the traditional `ddmin` that works on independent deltas that we defined in the previous [post](/post/2019/12/03/ddmin/).

```python
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        stitched =  instr[:i] + instr[i+part_len:]
        if causal(stitched): return i, stitched
    return -1, instr

def ddmin(cur_str, causal_fn):
    start, part_len = 0, len(cur_str) // 2
    while part_len >= 1:
        start, cur_str = remove_check_each_fragment(cur_str, start, part_len, causal_fn)
        if start != -1:
            if not cur_str: return ''
        else:
            start, part_len = 0, part_len // 2
    return cur_str
```
The ddmin now operates on choice sequences. So we need to convert them back to string
```python
def ints_to_string(grammar, ints):
    choices = ChoiceSeq(ints)
    cf = ChoiceFuzzer(grammar, choices)
    try:
        return cf.fuzz('<start>')
    except IndexError:
        return None
```
We also need our predicate. Note that we specialcase `None` in case the `ints_to_string` cannot successfully produce a value.
```python
def pred(v):
    if v is None: return False

    if '((' in v and '))' in v:
        return True
    return False
```
Now, the driver is as follows. The driver tries to minimize the string if predicate returns true.
```python
if __name__ == '__main__':
    import random
    import string
    import sys
    random.seed(int(sys.argv[1]))
    assignment_grammar = {
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
    choices = ChoiceSeq()

    c = ChoiceFuzzer(assignment_grammar, choices)
    val = c.fuzz('<start>')
    
    causal_fn = lambda ints: pred(ints_to_string(assignment_grammar, ints))

    if pred(val):
        newv = ddmin(c.choices.ints, causal_fn)
        choices = ChoiceSeq(newv)
        cf = ChoiceFuzzer(assignment_grammar, choices)
        print('original:', val, len(c.choices.ints))

        while True:
            newv = ddmin(cf.choices.ints, causal_fn)
            if len(newv) >= len(cf.choices.ints):
                break
            cf = ChoiceFuzzer(assignment_grammar, ChoiceSeq(newv))

        cf = ChoiceFuzzer(assignment_grammar, ChoiceSeq(newv))
        print('minimal:', cf.fuzz('<start>'), len(newv))
        print(cf.choices.ints)
```
Using it
```bash
$ python3   lf.py 1
original: e = (((00 - (00 + 00) - 0))) - (1);
f = e + e - e + ((e)) + e + (0) + e - (1);
g = f;
j = (e);
 61
minimal: d = ((00));
 7
[6, 0, 8, 3, 7, 7, 8]
```
As you can see, the original string that is a `61` choice long sequence has become reduced to an `8` choice long sequence, with a corresponding
decrease in the string length. At this point, note that it is fairly magick how the approach performs. In particular, as soon as an edit is made,
the remaining choices are not interpreted as in the original string. What if we help the reducer by specifying an `NOP` that allows one to delete
chunks with a chance for the remaining string to be interpreted similarly?

The idea is to delete a sequence of values and replace it by a single `-1` value which will cause the choice fuzzer to interpret it as fill in
with default value. The `ddmin` is modified as follows:

```python
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        if i > 0:
            stitched =  instr[:i-1] + [-1] + instr[i+part_len:]
        else:
            stitched =  instr[:i] + [-1] + instr[i+part_len+1:]
        if causal(stitched): return i, stitched
    return -1, instr
```
As you can see, a `[-1]` is inserted in place of the deleted squences. Now, we need to get our fuzzer to understand the `-1` value.
We add defaults to each nonterminal, and modify the `select` function to take a default value.
```python
class ChoiceFuzzer(ComplexFuzzer):
    def __init__(self, grammar, choices):
        super().__init__(grammar)
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

    def select(self, lst, default):
        return self.choices.choice(lst, default)

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule) for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        default = self.default[key]
```
The choice sequence now returns the `default` when it sees the `-1` value.
```python
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
            
 def defined_var(o, token, val):
    assert token == '<var>'
    if not o.vars:
        return ('00', [])
    else:
        return (o.select(o.vars, '000'), [])
```
These are all the modifications that we require.
Using it:
```bash
$ python3   lfm.py 1
original: e = (((00 - (00 + 00) - 0))) - (1);
f = e + e - e + ((e)) + e + (0) + e - (1);
g = f;
j = (e);
 61
minimal: 0 = ((0));
a=0;
 8
[2, 9, 1, -1, 7, 7, -1, -1]
```
How does this modification fare against the original without modification?
```bash
$ python3   lf.py 5
original: i = (00) + ((00) + 00 - 1 - 0 + 00 - ((00 - 1) - ((00)))) + 00 + 00 + ((1));
 40
minimal: d = ((1));
 8
[2, 2, 0, 3, 2, 2, 4, 5]
$ python3   lfm.py 5
original: i = (00) + ((00) + 00 - 1 - 0 + 00 - ((00 - 1) - ((00)))) + 00 + 00 + ((1));
 40
minimal: i = 0 + 0 + 0 + ((0));
 13
[9, 4, 5, 8, 0, -1, 0, -1, 0, -1, 2, 2, -1]

```
another
```bash
$ python3   lf.py 9 
original: e = ((00 + (1) + 00 + 0));
h = ((e)) - (e) - 1 - e - 1 - 1 - 0 + e - ((0 + 1)) - 1 - e + e - e + 1 - e;
 71
minimal: e = ((00 + 1 + 0));
j = 1;
 18
[7, 9, 5, 4, 2, 2, 0, 5, 8, 9, 1, 9, 6, 6, 1, 9, 9, 3]
$ python3   lfm.py 9
original: e = ((00 + (1) + 00 + 0));
h = ((e)) - (e) - 1 - e - 1 - 1 - 0 + e - ((0 + 1)) - 1 - e + e - e + 1 - e;
 71
minimal: e = ((0));
a=0;
 8
[7, 9, 5, 4, 2, 2, -1, -1]
```
Another
```bash
$ python3   lf.py 16
original: e = 00 - (1 - 00 + 0 + (0) + 00 + 0);
j = ((0)) + e;
 33
minimal: a = ((00));
 7
[0, 2, 9, 0, 7, 7, 3]
$ python3   lfm.py 16
original: e = 00 - (1 - 00 + 0 + (0) + 00 + 0);
j = ((0)) + e;
 33
minimal: 0 = 0 - 0 + 0;
a = ((0));
 15
[5, 7, 7, -1, 0, 6, -1, -1, -1, 2, 9, 0, 7, 7, -1]
```
As you can see, there does not seem to be a lot of advantage in using an `NOP`. How does this compare against the custom passes of Hypothesis? This is
something that needs to be found.
