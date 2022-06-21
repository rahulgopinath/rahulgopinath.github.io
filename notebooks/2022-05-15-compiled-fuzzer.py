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


# # Compiled Fuzzer
# 
# This grammar fuzzer is described in the paper
# [*Building Fast Fuzzers*](/publications/2019/11/18/arxiv-building/).
# The idea is to compile a grammar definition to the corresponding source code.
# Each nonterminal symbol becomes a procedure. First we define a few helpers.

def symbol_cost(grammar, symbol, seen, cache):
    if symbol in seen: return float('inf')
    lst = []
    for rule in grammar.get(symbol, []):
        if symbol in cache and str(rule) in cache[symbol]:
            lst.append(cache[symbol][str(rule)])
        else:
            lst.append(expansion_cost(grammar, rule, seen | {symbol}, cache))
    v = min(lst, default=0)
    return v

def expansion_cost(grammar, tokens, seen, cache):
    return max((symbol_cost(grammar, token, seen, cache)
                for token in tokens if token in grammar), default=0) + 1

def compute_cost(grammar):
    rule_cost = {}
    for k in grammar:
        rule_cost[k] = {}
        for rule in grammar[k]:
            rule_cost[k][str(rule)] = expansion_cost(grammar, rule, set(), rule_cost)
    return rule_cost

# We are going to compile the grammar, which will
# become a source file that we load separately. To ensure that we do not
# descend into quoting hell, we transform the grammar so that we store the
# character bytes rather than the terminals as strings.

def transform_bytes(grammar):
   new_g = {}
   for k in grammar:
       new_g[k] = [
               [t if fuzzer.is_nonterminal(t) else ord(t) for t in r]
               for r in grammar[k]]
   return new_g

# Usage

if __name__ == '__main__':
    g = transform_bytes(EXPR_GRAMMAR)
    for k in g:
        print(k)
        for r in g[k]:
            print('  ', r)

# Next, we define the class.
class F1Fuzzer(fuzzer.LimitFuzzer):
    def __init__(self, grammar):
        self.grammar = transform_bytes(grammar)
        self.cost = compute_cost(self.grammar)

# Convenience methods
class F1Fuzzer(F1Fuzzer):
    def add_indent(self, string, indent):
        return '\n'.join([indent + i for i in string.split('\n')])

    def k_to_s(self, k): return k[1:-1].replace('-', '_')

# ## Cheap grammar compilation
# 
# In the previous [post](/post/2019/05/28/simplefuzzer-01/), I described how we
# shift  to a cheap grammar when we exhaust our budget. We use the same thing
# here. That is, at some point we need to curtail the recursion. Hence, we
# define the cheap grammar that does not contain recursion. The idea is that
# if we go beyond a given depth, we switch to choosing rules from the
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

# The cheap grammar from expr grammar

if __name__ == '__main__':
    expr_cg = F1Fuzzer(EXPR_GRAMMAR).cheap_grammar()
    for k in expr_cg:
        print(k)
        for r in expr_cg[k]:
            print('   ', r)


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
result.append(%d)''' % token)
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
        return''' % (i, self.add_indent(
            self.gen_rule_src_cheap(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

# Usage

if __name__ == '__main__':
    src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src_cheap('<expr>',
            transform_bytes(EXPR_GRAMMAR))
    print(src)


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
result.append(%d)''' % token)
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

# Usage

if __name__ == '__main__':
    src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src('<expr>',
            transform_bytes(EXPR_GRAMMAR))
    print(src)

# The complete driver

import types
class F1Fuzzer(F1Fuzzer):
    def gen_main_src(self):
        return '''
import random
result = []
def start(max_depth):
    gen_start(max_depth)
    v = ''.join([chr(i) for i in result])
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
# Hence, we need a solution that allows us to go past that depth.
# 
# We discussed [here](/post/2022/04/17/python-iterative-copy/) how to use
# generators as a continuation passing trampoline. We use the same technique
# again. The basic technique is to turn every function call into a `yield`
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
result.append(%d)''' % token)
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
result.append(%d)''' % token)
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
    v = ''.join([chr(i) for i in result])
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

# Example

if __name__ == '__main__':
    src = F1CPSFuzzer(EXPR_GRAMMAR).fuzz_src('<start>')
    print(src)

# We also need to redefine our cost computation which is recursive.

def symbol_cost_cps(grammar, symbol, seen, cache):
    if symbol in seen: return float('inf')
    lst = []
    for rule in grammar.get(symbol, []):
        if symbol in cache and str(rule) in cache[symbol]:
            lst.append(cache[symbol][str(rule)])
        else:
            e = yield expansion_cost_cps(grammar, rule, seen | {symbol}, cache)
            lst.append(e)
    v = min(lst, default=0)
    return v

def expansion_cost_cps(grammar, tokens, seen, cache):
    lst = []
    for token in tokens:
        if token not in grammar: continue
        s = yield symbol_cost_cps(grammar, token, seen, cache)
        lst.append(s)
    return max(lst, default=0) + 1

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

def compute_cost_cps(grammar):
    rule_cost = {}
    for k in grammar:
        rule_cost[k] = {}
        for rule in grammar[k]:
            e = cpstrampoline(expansion_cost_cps(grammar, rule, set(), rule_cost))
            rule_cost[k][str(rule)] = e
    return rule_cost

class F1CPSFuzzer(F1CPSFuzzer):
    def __init__(self, grammar):
        self.grammar = transform_bytes(grammar)
        self.cost = compute_cost_cps(self.grammar)


# Using it

if __name__ == '__main__':
    expr_fuzzer = F1CPSFuzzer(EXPR_GRAMMAR).fuzzer('expr_fuzzer')
    for i in range(10):
        v = expr_fuzzer.start(10)
        print(repr(v))

# This is a useful trick. But what if we do not want to use the generator hack?
# Turns out, there is an easier solution. The idea is to wrap the remaining
# computation as a continuation and return. In our case, we modify this
# technique slightly.

class F1LFuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
lambda: gen_%s_cheap(),''' % (self.k_to_s(token)))
            else:
                res.append('''\
lambda: result.append(%d),''' % token)
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
        return [%s]''' % (i, self.add_indent(self.gen_rule_src_cheap(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

class F1LFuzzer(F1LFuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append('''\
lambda: gen_%s(max_depth, next_depth),''' % (self.k_to_s(token)))
            else:
                res.append('''\
lambda: result.append(%d),''' % token)
        return '\n'.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append('''
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth > max_depth:
        return [lambda: gen_%(name)s_cheap()]
    val = random.randrange(%(nrules)s)''' % {
            'name':self.k_to_s(key),
            'nrules':len(rules)})
        for i, rule in enumerate(rules):
            result.append('''\
    if val == %d:
        return [%s]''' % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),'        ')))
        return '\n'.join(result)

# We now define our trampoline, which is different from previous.

class F1LFuzzer(F1LFuzzer):
    def gen_main_src(self):
        return '''
def trampoline(gen):
    ret = None
    stack = gen
    while stack:
        cur, *stack = stack
        res = cur()
        if res is not None:
            stack.extend(res)
    return

import random
result = []
def start(max_depth):
    trampoline(gen_start(max_depth))
    v = ''.join([chr(i) for i in result])
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

# Using
if __name__ == '__main__':
    f = F1LFuzzer(EXPR_GRAMMAR)
    s = f.fuzz_src()
    print(s)
    expr_fuzzer = f.fuzzer('expr_fuzzer')
    for i in range(10):
        v = expr_fuzzer.start(10)
        print(repr(v))

