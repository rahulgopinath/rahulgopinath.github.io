# ---
# published: true
# title: A Fast Grammar Fuzzer by Compiling the Grammar
# layout: post
# comments: true
# tags: fuzzing
# categories: post
# ---

# In a previous [post](/post/2019/05/28/simplefuzzer-01/) I disucssed a simple
# fuzzer.  While simple, the fuzzer is somewhat inefficient. This post discusses
# a way to speed it up -- by compiling.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer

# As before, we start with a grammar.

EXPR_GRAMMAR = {
    "<start>": [["<expr>"]],
    "<expr>": [
        ["<term>", "+", "<expr>"],
        ["<term>", "-", "<expr>"],
        ["<term>"]],
    "<term>": [
        ["<factor>", "*", "<term>"],
        ["<factor>", "/", "<term>"],
        ["<factor>"]],
    "<factor>": [
        ["+", "<factor>"],
        ["-", "<factor>"],
        ["(", "<expr>", ")"],
        ["<integer>", ".", "<integer>"],
        ["<integer>"]],
    "<integer>": [
        ["<digit>", "<integer>"],
        ["<digit>"]],
    "<digit>": [["0"], ["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"], ["8"], ["9"]]
}

EXPR_START = '<start>'


# ## Compiled Fuzzer
# 
# This grammar fuzzer is described in the paper
# [*Building Fast Fuzzers*](https://rahul.gopinath.org/publications/2019/11/18/arxiv-building/).
# The idea is to compile a grammar definition to the corresponding source code.
# Each nonterminal symbol becomes a procedure. First we define a few helpers.

class F1Fuzzer(fuzzer.LimitFuzzer):
    def add_indent(self, string, indent):
        return '\n'.join([indent + i for i in string.split('\n')])

    # used for escaping inside strings
    def esc(self, t):
        t = t.replace('\\', '\\\\')
        t = t.replace('\n', '\\n')
        t = t.replace('\r', '\\r')
        t = t.replace('\t', '\\t')
        t = t.replace('\b', '\\b')
        t = t.replace('\v', '\\v')
        t = t.replace('"', '\\"')
        return t

    def esc_char(self, t):
        assert len(t) == 1
        t = t.replace('\\', '\\\\')
        t = t.replace('\n', '\\n')
        t = t.replace('\r', '\\r')
        t = t.replace('\t', '\\t')
        t = t.replace('\b', '\\b')
        t = t.replace('\v', '\\v')
        t = t.replace("'", "\\'")
        return t

    def k_to_s(self, k): return k[1:-1].replace('-', '_')

# ## Cheap grammar compilation
# 
# In the prevous [post](/post/2019/05/28/simplefuzzer-01/), I described how we
# shift  to a cheap grammar when we exhaust our budget. We use the same thing
# here. That is, at some point we need to curtail the recursion. Hence, we
# define the cheap grammar that does not contain recursion. The idea is that
# if we go byeond a given depth, we switch to choosing rules from the
# non-recursive grammar (cheap grammar).

class F1Fuzzer(F1Fuzzer):
    def cheap_grammar(self):
        cheap_grammar = {}
        for k in self.cost:
            rules = self.grammar[k]
            if rules:
                min_cost = min([self.cost[k][str(r)] for r in rules])
                cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]
            else:
                cheap_grammar[k] = [] # (No rules found)
        return cheap_grammar

# ### Translation
# 
# Translating the nonterminals of the cheap grammar is simple because there is
# no recursion. We simply choose a random rule to expand.

class F1Fuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
gen_%s_cheap()''' % (self.k_to_s(token)))
            else:
                res.append('''\
result.append("%s")''' % self.esc(token))
        return '\n'.join(res)


    def gen_alt_src_cheap(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append('''
def gen_%(name)s_cheap():
    val = random.randrange(%(nrules)s)''' % {
            'name':self.k_to_s(key),
            'nrules':len(rules)})
        for i, rule in enumerate(rules):
            result.append('''\
    if val == %d:
%s
        return''' % (i, self.add_indent(self.gen_rule_src_cheap(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

# ## Main grammar compilation
# 
# For recursive grammars, we need to verify that the depth of recursion is not
# beyond what is specified. If it has gone beyond the maximum specified depth,
# we expand the cheap grammar instead.

class F1Fuzzer(F1Fuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
gen_%s(max_depth, next_depth)''' % (self.k_to_s(token)))
            else:
                res.append('''\
result.append("%s")''' % self.esc(token))
        return '\n'.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append('''
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth > max_depth:
        gen_%(name)s_cheap()
        return
    val = random.randrange(%(nrules)s)''' % {
            'name':self.k_to_s(key),
            'nrules':len(rules)})
        for i, rule in enumerate(rules):
            result.append('''\
    if val == %d:
%s
        return''' % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

# The driver

import types
class F1Fuzzer(F1Fuzzer):
    def gen_main_src(self):
        return '''
import random
result = []
def start(max_depth):
    gen_start(max_depth)
    v = ''.join(result)
    result.clear()
    return v
        '''

    def gen_fuzz_src(self):
        result = []
        cheap_grammar = self.cheap_grammar()
        for key in cheap_grammar:
            result.append(self.gen_alt_src_cheap(key, cheap_grammar))
        for key in self.grammar:
            result.append(self.gen_alt_src(key, self.grammar))
        return '\n'.join(result)

    def fuzz_src(self, key='<start>'):
        result = [self.gen_fuzz_src(),
                  self.gen_main_src()]
        return ''.join(result)

    def load_src(self, src, mn):
        module = types.ModuleType(mn)
        exec(src, module.__dict__)
        return module

    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return self.load_src(cf_src, name + '_f1_fuzzer')

# Using it

if __name__ == '__main__':
    expr_fuzzer = F1Fuzzer(EXPR_GRAMMAR).fuzzer('expr_fuzzer')
    for i in range(10):
        v = expr_fuzzer.start(10)
        print(v)

# ## A Problem -- Recursion

# A problem with the compiled grammar fuzzer is that it relies on recursion,
# and Python limits the recursion depth arbitrarily (starting with just 1000).
# Hence, we ned a solution that allows us to go past that depth.
# 
# We discussed [here](/post/2022/04/17/python-iterative-copy/) how to use
# generators as a continuation passing trampoline. We use the same technique
# again. The basi technique is to turn every function call into a `yield`
# statement, and return the generator. A loop then translates activates
# and traverses these generators.

class F1CPSFuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
yield gen_%s_cheap()''' % (self.k_to_s(token)))
            else:
                res.append('''\
result.append("%s")''' % self.esc(token))
        return '\n'.join(res)


    def gen_alt_src_cheap(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append('''
def gen_%(name)s_cheap():
    val = random.randrange(%(nrules)s)''' % {
            'name':self.k_to_s(key),
            'nrules':len(rules)})
        for i, rule in enumerate(rules):
            result.append('''\
    if val == %d:
%s
        return''' % (i, self.add_indent(self.gen_rule_src_cheap(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

class F1CPSFuzzer(F1CPSFuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
yield gen_%s(max_depth, next_depth)''' % (self.k_to_s(token)))
            else:
                res.append('''\
result.append("%s")''' % self.esc(token))
        return '\n'.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append('''
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth > max_depth:
        yield gen_%(name)s_cheap()
        return
    val = random.randrange(%(nrules)s)''' % {
            'name':self.k_to_s(key),
            'nrules':len(rules)})
        for i, rule in enumerate(rules):
            result.append('''\
    if val == %d:
%s
        return''' % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

class F1CPSFuzzer(F1CPSFuzzer):
    def gen_main_src(self):
        return '''
def cpstrampoline(gen):
    stack = [gen]
    ret = None
    while stack:
        try:
            value, ret = ret, None
            res = stack[-1].send(value)
            if res is not None:
                stack.append(res)
        except StopIteration as e:
            stack.pop()
            ret = e.value
    return ret

import random
result = []
def start(max_depth):
    cpstrampoline(gen_start(max_depth))
    v = ''.join(result)
    result.clear()
    return v
        '''

    def gen_fuzz_src(self):
        result = []
        cheap_grammar = self.cheap_grammar()
        for key in cheap_grammar:
            result.append(self.gen_alt_src_cheap(key, cheap_grammar))
        for key in self.grammar:
            result.append(self.gen_alt_src(key, self.grammar))
        return '\n'.join(result)

    def fuzz_src(self, key='<start>'):
        result = [self.gen_fuzz_src(),
                  self.gen_main_src()]
        return ''.join(result)
    
    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return self.load_src(cf_src, name + '_f1_fuzzer')

# Using it

if __name__ == '__main__':
    expr_fuzzer = F1CPSFuzzer(EXPR_GRAMMAR).fuzzer('expr_fuzzer')
    for i in range(10):
        v = expr_fuzzer.start(10)
        print(repr(v))


