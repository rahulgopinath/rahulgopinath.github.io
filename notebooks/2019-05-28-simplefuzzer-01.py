# ---
# published: true
# title: The simplest grammar fuzzer in the world
# layout: post
# comments: true
# tags: fuzzing
# categories: post
# ---

# Fuzzing is one of the key tools in a security researcher's tool box. It is simple
# to write a [random fuzzer](https://www.fuzzingbook.org/html/Fuzzer.html#A-Simple-Fuzzer).

import random

def fuzzer(max_length=100, chars=[chr(i) for i in range(32, 64)]):
    return ''.join([random.choice(chars) for i in range(random.randint(0,max_length))])

# 
if __name__ == '__main__':
    for i in range(10):
        print(repr(fuzzer()))

# Unfortunately, random fuzzing is not very effective for programs that accept complex
# input languages such as those that expect JSON or any other structure in their input.
# For these programs, the fuzzing can be much more effective if one has a model of their
# input structure. A number of such tools exist
# ([1](https://github.com/renatahodovan/grammarinator), [2](https://www.fuzzingbook.org/html/GrammarFuzzer.html), [3](https://github.com/MozillaSecurity/dharma), [4](https://github.com/googleprojectzero/domato)).
# But how difficult is it to write your own grammar based fuzzer?

# The interesting thing is that, a grammar fuzzer is essentially a parser turned inside
# out. Rather than consuming, we simply output what gets compared. With that idea in mind,
# let us use one of the simplest parsers -- ([A PEG parser](http://rahul.gopinath.org/2018/09/06/peg-parsing/)).


import random
def unify_key_inv(grammar, key):
   return unify_rule_inv(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule_inv(grammar, rule):
    return sum([unify_key_inv(grammar, token) for token in rule], [])

# Now, all one needs is a grammar.

grammar = {
        '<start>': [['<json>']],
        '<json>': [['<element>']],
        '<element>': [['<ws>', '<value>', '<ws>']],
        '<value>': [
           ['<object>'], ['<array>'], ['<string>'], ['<number>'],
           ['true'], ['false'], ['null']],
        '<object>': [['{', '<ws>', '}'], ['{', '<members>', '}']],
        '<members>': [['<member>', '<symbol-2>']],
        '<member>': [['<ws>', '<string>', '<ws>', ':', '<element>']],
        '<array>': [['[', '<ws>', ']'], ['[', '<elements>', ']']],
        '<elements>': [['<element>', '<symbol-1-1>']],
        '<string>': [['"', '<characters>', '"']],
        '<characters>': [['<character-1>']],
        '<character>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['g'], ['h'], ['i'], ['j'],
            ['k'], ['l'], ['m'], ['n'], ['o'], ['p'], ['q'], ['r'], ['s'], ['t'],
            ['u'], ['v'], ['w'], ['x'], ['y'], ['z'], ['A'], ['B'], ['C'], ['D'],
            ['E'], ['F'], ['G'], ['H'], ['I'], ['J'], ['K'], ['L'], ['M'], ['N'],
            ['O'], ['P'], ['Q'], ['R'], ['S'], ['T'], ['U'], ['V'], ['W'], ['X'],
            ['Y'], ['Z'], ['!'], ['#'], ['$'], ['%'], ['&'], ["'"], ['('], [')'],
            ['*'], ['+'], [','], ['-'], ['.'], ['/'], [':'], [';'], ['<'], ['='],
            ['>'], ['?'], ['@'], ['['], [']'], ['^'], ['_'], ['`'], ['{'], ['|'],
            ['}'], ['~'], [' '], ['\\"'], ['\\\\'], ['\\/'], ['<escaped>']],
        '<number>': [['<int>', '<frac>', '<exp>']],
        '<int>': [
           ['<digit>'], ['<onenine>', '<digits>'],
           ['-', '<digits>'], ['-', '<onenine>', '<digits>']],
        '<digits>': [['<digit-1>']],
        '<digit>': [['0'], ['<onenine>']],
        '<onenine>': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<frac>': [[], ['.', '<digits>']],
        '<exp>': [[], ['E', '<sign>', '<digits>'], ['e', '<sign>', '<digits>']],
        '<sign>': [[], ['+'], ['-']],
        '<ws>': [['<sp1>', '<ws>'], []],
        '<sp1>': [[' ']], ##[['\n'], ['\r'], ['\t'], ['\x08'], ['\x0c']],
        '<symbol>': [[',', '<members>']],
        '<symbol-1>': [[',', '<elements>']],
        '<symbol-2>': [[], ['<symbol>', '<symbol-2>']],
        '<symbol-1-1>': [[], ['<symbol-1>', '<symbol-1-1>']],
        '<character-1>': [[], ['<character>', '<character-1>']],
        '<digit-1>': [['<digit>'], ['<digit>', '<digit-1>']],
        '<escaped>': [['\\u', '<hex>', '<hex>', '<hex>', '<hex>']],
        '<hex>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['A'], ['B'], ['C'], ['D'], ['E'],   ['F']]
        }

# The driver is as follows:

if __name__ == '__main__':
    print(repr(''.join(unify_key_inv(grammar, '<start>'))))

# This grammar fuzzer can be implemented in pretty much any programming language
# that supports basic data structures.
# What if you want the derivation tree instead? The following modified fuzzer
# will get you the derivation tree which
# can be used with `fuzzingbook.GrammarFuzzer.tree_to_string`

def is_terminal(v):
    return (v[0], v[-1]) != ('<', '>')

def is_nonterminal(v):
    return (v[0], v[-1]) == ('<', '>')

def tree_to_string(tree):
    symbol, children, *_ = tree
    if children:
        return ''.join(tree_to_string(c) for c in children)
    else:
        return '' if is_nonterminal(symbol) else symbol

def unify_key_inv_t(g, key):
   return (key, unify_rule_inv_t(g, random.choice(g[key]))) if key in g else (key, [])

def unify_rule_inv_t(g, rule):
    return [unify_key_inv_t(g, token) for token in rule]

# Using it

if __name__ == '__main__':
    res = unify_key_inv_t(grammar, '<start>')
    print(res)

# We now want a way to display this tree. We can do that as follows
# We first define a simple option holder class.


class O:
    def __init__(self, **keys): self.__dict__.update(keys)

# We can now define our default drawing options for displaying a tree.
# The default options include the vertical (|), the horizontal (--)
# and the how the last line is represented (+)

OPTIONS   = O(V='|', H='-', L='+', J = '+')

def format_node(node):
    key = node[0]
    if key and (key[0], key[-1]) ==  ('<', '>'): return key
    return repr(key)

def get_children(node):
    return node[1]

# We want to display the tree. This is simply `display_tree`.

def display_tree(node, format_node=format_node, get_children=get_children,
                 options=OPTIONS):
    print(format_node(node))
    for line in format_tree(node, format_node, get_children, options):
        print(line)

# The `display_tree` calls `format_tree` which is defined as follows

def format_tree(node, format_node, get_children, options, prefix=''):
    children = get_children(node)
    if not children: return
    *children, last_child = children
    for child in children:
        next_prefix = prefix + options.V + '   '
        yield from format_child(child, next_prefix, format_node, get_children,
                                options, prefix, False)
    last_prefix = prefix + '    '
    yield from format_child(last_child, last_prefix, format_node, get_children,
                            options, prefix, True)

def format_child(child, next_prefix, format_node, get_children, options,
                 prefix, last):
    sep = (options.L if last else options.J)
    yield prefix + sep + options.H + ' ' + format_node(child)
    yield from format_tree(child, format_node, get_children, options, next_prefix)

# We can now show the tree
if __name__ == '__main__':
    display_tree(res)

# The corresponding string is

if __name__ == '__main__':
    print(repr(tree_to_string(res)))

# One problem with the above fuzzer is that it can fail to terminate the
# recursion. So, what we want to do is to limit unbounded recursion to a fixed
# depth. Beyond that fixed depth, we want to only expand those rules that are
# guaranteed to terminate.
#  
# For that, we define the cost of expansion for each symbol in a grammar.
# A symbol costs as much as the cost of the least cost rule expansion.

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

# A rule costs as much as the cost of expansion of the most costliest symbol
# in that rule + 1.

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


# Here is an implementation that uses random expansions until
# a configurable depth (`max_depth`) is reached, and beyond that, uses
# purely non-recursive cheap expansions.

class LimitFuzzer:

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return key
        if depth > max_depth:
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
            assert clst[0][0] != float('inf')
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return self.gen_rule(random.choice(rules), depth+1, max_depth)

    def gen_rule(self, rule, depth, max_depth):
        return ''.join(self.gen_key(token, depth, max_depth) for token in rule)

    def fuzz(self, key='<start>', max_depth=10):
        return self.gen_key(key=key, depth=0, max_depth=max_depth)

    def __init__(self, grammar):
        self.grammar = grammar
        self.key_cost = {}
        self.cost = compute_cost(grammar)
        self.cheap_grammar = {}
        for k in self.cost:
            # should we minimize it here? We simply avoid infinities
            rules = self.grammar[k]
            min_cost = min([self.cost[k][str(r)] for r in rules])
            #grammar[k] = [r for r in grammar[k] if self.cost[k][str(r)] == float('inf')]
            self.cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]

# Using it:

if __name__ == '__main__':
    gf = LimitFuzzer(grammar)
    for i in range(100):
       print(gf.fuzz(key='<start>', max_depth=10))


# ## Iterative fuzzer

# One of the problems with the above fuzzer is that we use the Python stack to
# keep track of the expansion tree. Unfortunately, Python is really limited in
# terms of the usable stack depth. This can make it hard to generate deeply
# nested trees. One alternative solution is to handle the stack management
# ourselves as we show next.

# First, we define an iterative version of the tree_to_string function called `iter_tree_to_str()` as below.
def modifiable(tree):
    name, children, *rest = tree
    if not is_nonterminal(name): return [name, []]
    else:
      return [name, [modifiable(c) for c in children]]

def iter_tree_to_str(tree_):
    tree = modifiable(tree_)
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if is_nonterminal(key):
            #assert children # not necessary
            to_expand = children + to_expand
        else:
            assert not children
            expanded.append(key)
    return ''.join(expanded)

# You can use it as follows:
if __name__ == '__main__':
    print(iter_tree_to_str(('<start>', [('<json>', [('<element>', [('<ws>', [('<sp1>', [(' ', [])]), ('<ws>', [])]), ('<value>', [('null', [])]), ('<ws>', [])])])])))

# Next, we add the `iter_gen_key()` to `LimitFuzzer`

class LimitFuzzer(LimitFuzzer):
    def iter_gen_key(self, key, max_depth):
        def get_def(t):
            if is_nonterminal(t):
                return [t, None]
            else:
                return [t, []]

        root = [key, None]
        queue = [(0, root)]
        while queue:
            # get one item to expand from the queue
            (depth, item), *queue = queue
            key = item[0]
            if item[1] is not None: continue
            grammar = self.grammar if depth < max_depth else self.cheap_grammar
            chosen_rule = random.choice(grammar[key])
            expansion = [get_def(t) for t in chosen_rule]
            item[1] = expansion
            for t in expansion: queue.append((depth+1, t))
        return root

# Finally, we ensure that the iterative gen_key can be called by defining `iter_fuzz()`.

class LimitFuzzer(LimitFuzzer):
    def iter_fuzz(self, key='<start>', max_depth=10):
        self._s = self.iter_gen_key(key=key, max_depth=max_depth)
        return iter_tree_to_str(self._s)

# Using it

if __name__ == '__main__':
    gf = LimitFuzzer(grammar)
    for i in range(10):
       print(gf.iter_fuzz(key='<start>', max_depth=100))


# The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2019-05-28-simplefuzzer-01.py)
