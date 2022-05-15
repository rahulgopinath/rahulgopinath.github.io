# ---
# published: true
# title: Building Fast Fuzzers
# layout: post
# comments: true
# tags: fuzzing
# categories: post
# ---

# In a previous [post](/post/2019/05/28/simplefuzzer-01/) I disucssed a simple
# fuzzer.  While simple, the fuzzer is somewhat inefficient. This post discusses
# a way to speed it up -- by compiling.
# 
# As before, we start with a grammar.

expr_grammar = {
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

expr_start = '<start>'

# We define a simple interface for fuzzing.

class Fuzzer:
    def __init__(self, grammar):
        self.grammar = grammar

    def fuzz(self, key='<start>', max_num=None, max_depth=None):
        raise NotImplemented()

# Next, we define our limit fuzzer that we discussed in the previous post.

class LimitFuzzer(Fuzzer):
    def __init__(self, grammar):
        super().__init__(grammar)
        self.key_cost = {}
        self.cost = self.compute_cost(grammar)

# ##  Cost
# The cost of a nonterminal symbol is the minimum cost of the rules that define
# it. A terminal symbol costs a unit. The cost of a rule is the maximum cost of
# all the symbols that are in the rule.
# 
# So, we first find the cost of expansion for each grammar rule.

class LimitFuzzer(LimitFuzzer):
    def compute_cost(self, grammar):
        cost = {}
        for k in grammar:
            cost[k] = {}
            for rule in grammar[k]:
                cost[k][str(rule)] = self.expansion_cost(grammar, rule, set())
            if len(grammar[k]):
                assert len([v for v in cost[k] if v != float('inf')]) > 0
        return cost

# ### Symbol Cost

class LimitFuzzer(LimitFuzzer):
    def symbol_cost(self, grammar, symbol, seen):
        if symbol in self.key_cost: return self.key_cost[symbol]
        if symbol in seen:
            self.key_cost[symbol] = float('inf')
            return float('inf')
        v = min((self.expansion_cost(grammar, rule, seen | {symbol})
                    for rule in grammar.get(symbol, [])), default=0)
        self.key_cost[symbol] = v
        return v

# ### Rule Cost
class LimitFuzzer(LimitFuzzer):
    def expansion_cost(self, grammar, tokens, seen):
        return max((self.symbol_cost(grammar, token, seen)
                    for token in tokens if token in grammar), default=0) + 1

# ### Generating

class LimitFuzzer(LimitFuzzer):
    def nonterminals(self, rule):
        return [t for t in rule if utils.is_nt(t)]

    def iter_gen_key(self, key, max_depth):
        def get_def(t):
            if t in ASCII_MAP:
                return [random.choice(ASCII_MAP[t]), []]
            elif t and t[-1] == '+' and t[0:-1] in ASCII_MAP:
                num = random.randrange(FUZZRANGE) + 1
                val = [random.choice(ASCII_MAP[t[0:-1]]) for i in range(num)]
                return [''.join(val), []]
            elif utils.is_nt(t):
                return [t, None]
            else:
                return [t, []]

        cheap_grammar = {}
        for k in self.cost:
            rules = self.grammar[k]
            if rules:
                min_cost = min([self.cost[k][str(r)] for r in rules])
                cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]
            else:
                cheap_grammar[k] = [] # (No rules found)

        root = [key, None]
        queue = [(0, root)]
        while queue:
            (depth, item), *queue = queue
            key = item[0]
            if item[1] is not None: continue
            grammar = self.grammar if depth < max_depth else cheap_grammar
            chosen_rule = random.choice(grammar[key])
            expansion = [get_def(t) for t in chosen_rule]
            item[1] = expansion
            for t in expansion: queue.append((depth+1, t))

        return root

    def gen_key(self, key, depth, max_depth):
        if key in ASCII_MAP:
            return (random.choice(ASCII_MAP[key]), [])
        if key and key[-1] == '+' and key[0:-1] in ASCII_MAP:
            m = random.randrange(FUZZRANGE) + 1
            return (''.join([random.choice(ASCII_MAP[key[0:-1]]) for i in range(m)]), [])
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        v = self.gen_rule(random.choice(rules), depth+1, max_depth)
        return (key, v)

    def gen_rule(self, rule, depth, max_depth):
        return [self.gen_key(token, depth, max_depth) for token in rule]

    def fuzz(self, key='<start>', max_depth=10):
        return utils.tree_to_str(self.iter_gen_key(key=key, max_depth=max_depth))


# ## Compiled Fuzzer
# This grammar fuzzer is described in the paper
# [*Building Fast Fuzzers*](https://rahul.gopinath.org/publications/2019/11/18/arxiv-building/).
# The idea is to compile a grammar definition to the corresponding source code.
# Each nonterminal symbol becomes a procedure. First we define a few helpers.

class F1Fuzzer(LimitFuzzer):
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
# The complication is that we need to curtail the recursion. Hence, we define a
# cheap grammar that does not contain recursion.

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
# Translating the nonterminals of the cheap grammar is simple because there is no recursion. We simply choose a random rule to expand.

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

# ## Grammar compilation
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

    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return utils.load_src(cf_src, name + '_f1_fuzzer')

# Using it

if __name__ == '__main__':
    expr_fuzzer = F1Fuzzer(grammars.EXPR_GRAMMAR).fuzzer('expr_fuzzer')
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
# again

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
        return utils.load_src(cf_src, name + '_f1_fuzzer')

# Using it

if __name__ == '__main__':
    expr_fuzzer = F1CPSFuzzer(grammars.EXPR_GRAMMAR).fuzzer('expr_fuzzer')
    for i in range(10):
        v = expr_fuzzer.start(10)
        print(repr(v))


