---
published: true
title: The simplest grammar fuzzer in the world
layout: post
comments: true
tags: fuzzing
categories: post
---

<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt.min.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt-stdlib.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/env/editor.js" type="text/javascript"></script>


Fuzzing is one of the key tools in a security researcher's tool box. It is simple
to write a [random fuzzer](https://www.fuzzingbook.org/html/Fuzzer.html#A-Simple-Fuzzer).

<form name='python_run_form'>
<textarea id="yourcode1" cols="40" rows="4" name='python_edit'>
import random

def fuzzer(max_length=100, chars=[chr(i) for i in range(32, 64)]):
    return ''.join([random.choice(chars) for i in range(random.randint(0,max_length))])

for i in range(10):
    print(repr(fuzzer()))
</textarea><br />
<button type="button" id="button1" name="python_run">Run</button>
<pre id="output1" class='Output' name='python_output'></pre>
<div id="mycanvas1" name='python_canvas'></div>
</form>

Unfortunately, random fuzzing is not very effective for programs that accept complex
input languages such as those that expect JSON or any other structure in their input.
For these programs, the fuzzing can be much more effective if one has a model of their
input structure. A number of such tools exist
([1](https://github.com/renatahodovan/grammarinator), [2](https://www.fuzzingbook.org/html/GrammarFuzzer.html), [3](https://github.com/MozillaSecurity/dharma), [4](https://github.com/googleprojectzero/domato)).
But how difficult is it to write your own grammar based fuzzer?

The interesting thing is that, a grammar fuzzer is essentially a parser turned inside
out. Rather than consuming, we simply output what gets compared. With that idea in mind,
let us use one of the simplest parsers -- ([A PEG parser](http://rahul.gopinath.org/2018/09/06/peg-parsing/)).


<form name='python_run_form'>
<textarea id="yourcode2" cols="40" rows="4" name='python_edit'>
import random
def unify_key(grammar, key):
   return unify_rule(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule(grammar, rule):
    return sum([unify_key(grammar, token) for token in rule], [])

print('.')
</textarea><br />
<button type="button" id="button2" name="python_run">Run</button>
<pre id="output2" class='Output' name='python_output'></pre>
<div id="mycanvas2" name='python_canvas'></div>
</form>


Now, all one needs is a grammar.
<!--div id='pycode1'></div-->
<form name='python_run_form'>
<textarea id="yourcode3" cols="40" rows="4" name='python_edit'>

grammar = {
        '&lt;start&gt;': [['&lt;json&gt;']],
        '&lt;json&gt;': [['&lt;element&gt;']],
        '&lt;element&gt;': [['&lt;ws&gt;', '&lt;value&gt;', '&lt;ws&gt;']],
        '&lt;value&gt;': [
           ['&lt;object&gt;'], ['&lt;array&gt;'], ['&lt;string&gt;'], ['&lt;number&gt;'],
           ['true'], ['false'], ['null']],
        '&lt;object&gt;': [['{', '&lt;ws&gt;', '}'], ['{', '&lt;members&gt;', '}']],
        '&lt;members&gt;': [['&lt;member&gt;', '&lt;symbol-2&gt;']],
        '&lt;member&gt;': [['&lt;ws&gt;', '&lt;string&gt;', '&lt;ws&gt;', ':', '&lt;element&gt;']],
        '&lt;array&gt;': [['[', '&lt;ws&gt;', ']'], ['[', '&lt;elements&gt;', ']']],
        '&lt;elements&gt;': [['&lt;element&gt;', '&lt;symbol-1-1&gt;']],
        '&lt;string&gt;': [['&quot;', '&lt;characters&gt;', '&quot;']],
        '&lt;characters&gt;': [['&lt;character-1&gt;']],
        '&lt;character&gt;': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['g'], ['h'], ['i'], ['j'],
            ['k'], ['l'], ['m'], ['n'], ['o'], ['p'], ['q'], ['r'], ['s'], ['t'],
            ['u'], ['v'], ['w'], ['x'], ['y'], ['z'], ['A'], ['B'], ['C'], ['D'],
            ['E'], ['F'], ['G'], ['H'], ['I'], ['J'], ['K'], ['L'], ['M'], ['N'],
            ['O'], ['P'], ['Q'], ['R'], ['S'], ['T'], ['U'], ['V'], ['W'], ['X'],
            ['Y'], ['Z'], ['!'], ['#'], ['$'], ['%'], ['&amp;'], [&quot;'&quot;], ['('], [')'],
            ['*'], ['+'], [','], ['-'], ['.'], ['/'], [':'], [';'], ['&lt;'], ['='],
            ['&gt;'], ['?'], ['@'], ['['], [']'], ['^'], ['_'], ['`'], ['{'], ['|'],
            ['}'], ['~'], [' '], ['\\&quot;'], ['\\\\'], ['\\/'], ['&lt;unicode&gt;'], ['&lt;escaped&gt;']],
        '&lt;number&gt;': [['&lt;int&gt;', '&lt;frac&gt;', '&lt;exp&gt;']],
        '&lt;int&gt;': [
           ['&lt;digit&gt;'], ['&lt;onenine&gt;', '&lt;digits&gt;'],
           ['-', '&lt;digits&gt;'], ['-', '&lt;onenine&gt;', '&lt;digits&gt;']],
        '&lt;digits&gt;': [['&lt;digit-1&gt;']],
        '&lt;digit&gt;': [['0'], ['&lt;onenine&gt;']],
        '&lt;onenine&gt;': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '&lt;frac&gt;': [[], ['.', '&lt;digits&gt;']],
        '&lt;exp&gt;': [[], ['E', '&lt;sign&gt;', '&lt;digits&gt;'], ['e', '&lt;sign&gt;', '&lt;digits&gt;']],
        '&lt;sign&gt;': [[], ['+'], ['-']],
        '&lt;ws&gt;': [['&lt;sp1&gt;', '&lt;ws&gt;'], []],
        '&lt;sp1&gt;': [[' ']], ##[['\n'], ['\r'], ['\t'], ['\x08'], ['\x0c']],
        '&lt;symbol&gt;': [[',', '&lt;members&gt;']],
        '&lt;symbol-1&gt;': [[',', '&lt;elements&gt;']],
        '&lt;symbol-2&gt;': [[], ['&lt;symbol&gt;', '&lt;symbol-2&gt;']],
        '&lt;symbol-1-1&gt;': [[], ['&lt;symbol-1&gt;', '&lt;symbol-1-1&gt;']],
        '&lt;character-1&gt;': [[], ['&lt;character&gt;', '&lt;character-1&gt;']],
        '&lt;digit-1&gt;': [['&lt;digit&gt;'], ['&lt;digit&gt;', '&lt;digit-1&gt;']],
        '&lt;escaped&gt;': [['\\u', '&lt;hex&gt;', '&lt;hex&gt;', '&lt;hex&gt;', '&lt;hex&gt;']],
        '&lt;hex&gt;': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['A'], ['B'], ['C'], ['D'], ['E'],   ['F']]
        }
print('.')
</textarea><br />
<button type="button" id="button3" name="python_run">Run</button>
<pre id="output3" class='Output' name='python_output'></pre>
<div id="mycanvas3" name='python_canvas'></div>
</form>
<!--script>
$(document).ready(function () {
$('#pycode1').next().next().find('textarea')[0].value = $('#pycode1').next()[0].innerText

});
</script-->


The driver is as follows:

<form name='python_run_form'>
<textarea id="yourcode4" cols="40" rows="4" name='python_edit'>
print(repr(''.join(unify_key('&lt;start&gt;'))))
</textarea><br />
<button type="button" id="button4" name="python_run">Run</button>
<pre id="output4" class='Output' name='python_output'></pre>
<div id="mycanvas4" name='python_canvas'></div>
</form>

This grammar fuzzer can be implemented in pretty much any programming language that supports basic data structures.

What if you want the derivation tree instead? The following modified fuzzer will get you the derivation tree which
can be used with `fuzzingbook.GrammarFuzzer.tree_to_string`


<form name='python_run_form'>
<textarea id="yourcode5" cols="40" rows="4" name='python_edit'>
def tree_to_string(tree):
    symbol, children, *_ = tree
    if children:
        return ''.join(tree_to_string(c) for c in children)
    else:
        return '' if is_nonterminal(symbol) else symbol

def unify_key(g, key):
   return (key, unify_rule(g, random.choice(g[key]))) if key in g else (key, [])

def unify_rule(g, rule):
    return [unify_key(g, token) for token in rule]

print('.')
</textarea><br />
<button type="button" id="button5" name="python_run">Run</button>
<pre id="output5" class='Output' name='python_output'></pre>
<div id="mycanvas5" name='python_canvas'></div>
</form>



Using it

<form name='python_run_form'>
<textarea id="yourcode6" cols="40" rows="4" name='python_edit'>
res = unify_key(g, '&lt;start&gt;')
print(res)
print(repr(tree_to_string(res)))
</textarea><br />
<button type="button" id="button6" name="python_run">Run</button>
<pre id="output6" class='Output' name='python_output'></pre>
<div id="mycanvas6" name='python_canvas'></div>
</form>



One problem with the above fuzzer is that it can fail to terminate the recursion. Here is an implementation that uses random expansions until a configurable depth (`max_depth`) is reached, and beyond that, uses purely non-recursive cheap expansions.

<form name='python_run_form'>
<textarea id="yourcode7" cols="40" rows="4" name='python_edit'>
class LimitFuzzer:
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
        if key not in self.grammar: return key
        if depth &gt; max_depth:
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.             grammar[key]])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return self.gen_rule(random.choice(rules), depth+1, max_depth)

    def gen_rule(self, rule, depth, max_depth):
        return ''.join(self.gen_key(token, depth, max_depth) for token in rule)

    def fuzz(self, key='&lt;start&gt;', max_depth=10):
        return self.gen_key(key=key, depth=0, max_depth=max_depth)

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
print('.')
</textarea><br />
<button type="button" id="button7" name="python_run">Run</button>
<pre id="output7" class='Output' name='python_output'></pre>
<div id="mycanvas7" name='python_canvas'></div>
</form>

Using it:

<form name='python_run_form'>
<textarea id="yourcode8" cols="40" rows="4" name='python_edit'>
gf = LimitFuzzer(grammar)
for i in range(100):
   gf.fuzz(key='&lt;start&gt;', max_depth=10)
</textarea><br />
<button type="button" id="button8" name="python_run">Run</button>
<pre id="output8" class='Output' name='python_output'></pre>
<div id="mycanvas8" name='python_canvas'></div>
</form>

