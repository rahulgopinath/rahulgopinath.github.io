---
published: true
title: The simplest grammar fuzzer in the world
layout: post
comments: true
tags: fuzzing
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.8/';</script>
<script src="/resources/pyodide/full/3.8/pyodide.js"></script>
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/pyodide/js/env/editor.js" type="text/javascript"></script>

**Important:** [Pyodide](https://pyodide.readthedocs.io/en/latest/) takes time to initialize.
Initialization completion is indicated by a red border around *Run all* button.
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
Fuzzing is one of the key tools in a security researcher's tool box. It is simple
to write a [random fuzzer](https://www.fuzzingbook.org/html/Fuzzer.html#A-Simple-Fuzzer).

<!--
############
import random

def fuzzer(max_length=100, chars=[chr(i) for i in range(32, 64)]):
    return ''.join([random.choice(chars) for i in range(random.randint(0,max_length))])

if __name__ == '__main__':
    for i in range(10):
        print(repr(fuzzer()))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random

def fuzzer(max_length=100, chars=[chr(i) for i in range(32, 64)]):
    return &#x27;&#x27;.join([random.choice(chars) for i in range(random.randint(0,max_length))])

if __name__ == &#x27;__main__&#x27;:
    for i in range(10):
        print(repr(fuzzer()))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
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

<!--
############
import random
def unify_key_inv(grammar, key):
   return unify_rule_inv(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule_inv(grammar, rule):
    return sum([unify_key_inv(grammar, token) for token in rule], [])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
def unify_key_inv(grammar, key):
   return unify_rule_inv(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule_inv(grammar, rule):
    return sum([unify_key_inv(grammar, token) for token in rule], [])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, all one needs is a grammar.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
        &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;json&gt;&#x27;]],
        &#x27;&lt;json&gt;&#x27;: [[&#x27;&lt;element&gt;&#x27;]],
        &#x27;&lt;element&gt;&#x27;: [[&#x27;&lt;ws&gt;&#x27;, &#x27;&lt;value&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;]],
        &#x27;&lt;value&gt;&#x27;: [
           [&#x27;&lt;object&gt;&#x27;], [&#x27;&lt;array&gt;&#x27;], [&#x27;&lt;string&gt;&#x27;], [&#x27;&lt;number&gt;&#x27;],
           [&#x27;true&#x27;], [&#x27;false&#x27;], [&#x27;null&#x27;]],
        &#x27;&lt;object&gt;&#x27;: [[&#x27;{&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;}&#x27;], [&#x27;{&#x27;, &#x27;&lt;members&gt;&#x27;, &#x27;}&#x27;]],
        &#x27;&lt;members&gt;&#x27;: [[&#x27;&lt;member&gt;&#x27;, &#x27;&lt;symbol-2&gt;&#x27;]],
        &#x27;&lt;member&gt;&#x27;: [[&#x27;&lt;ws&gt;&#x27;, &#x27;&lt;string&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;element&gt;&#x27;]],
        &#x27;&lt;array&gt;&#x27;: [[&#x27;[&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;]&#x27;], [&#x27;[&#x27;, &#x27;&lt;elements&gt;&#x27;, &#x27;]&#x27;]],
        &#x27;&lt;elements&gt;&#x27;: [[&#x27;&lt;element&gt;&#x27;, &#x27;&lt;symbol-1-1&gt;&#x27;]],
        &#x27;&lt;string&gt;&#x27;: [[&#x27;&quot;&#x27;, &#x27;&lt;characters&gt;&#x27;, &#x27;&quot;&#x27;]],
        &#x27;&lt;characters&gt;&#x27;: [[&#x27;&lt;character-1&gt;&#x27;]],
        &#x27;&lt;character&gt;&#x27;: [
            [&#x27;0&#x27;], [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;],
            [&#x27;a&#x27;], [&#x27;b&#x27;], [&#x27;c&#x27;], [&#x27;d&#x27;], [&#x27;e&#x27;], [&#x27;f&#x27;], [&#x27;g&#x27;], [&#x27;h&#x27;], [&#x27;i&#x27;], [&#x27;j&#x27;],
            [&#x27;k&#x27;], [&#x27;l&#x27;], [&#x27;m&#x27;], [&#x27;n&#x27;], [&#x27;o&#x27;], [&#x27;p&#x27;], [&#x27;q&#x27;], [&#x27;r&#x27;], [&#x27;s&#x27;], [&#x27;t&#x27;],
            [&#x27;u&#x27;], [&#x27;v&#x27;], [&#x27;w&#x27;], [&#x27;x&#x27;], [&#x27;y&#x27;], [&#x27;z&#x27;], [&#x27;A&#x27;], [&#x27;B&#x27;], [&#x27;C&#x27;], [&#x27;D&#x27;],
            [&#x27;E&#x27;], [&#x27;F&#x27;], [&#x27;G&#x27;], [&#x27;H&#x27;], [&#x27;I&#x27;], [&#x27;J&#x27;], [&#x27;K&#x27;], [&#x27;L&#x27;], [&#x27;M&#x27;], [&#x27;N&#x27;],
            [&#x27;O&#x27;], [&#x27;P&#x27;], [&#x27;Q&#x27;], [&#x27;R&#x27;], [&#x27;S&#x27;], [&#x27;T&#x27;], [&#x27;U&#x27;], [&#x27;V&#x27;], [&#x27;W&#x27;], [&#x27;X&#x27;],
            [&#x27;Y&#x27;], [&#x27;Z&#x27;], [&#x27;!&#x27;], [&#x27;#&#x27;], [&#x27;$&#x27;], [&#x27;%&#x27;], [&#x27;&amp;&#x27;], [&quot;&#x27;&quot;], [&#x27;(&#x27;], [&#x27;)&#x27;],
            [&#x27;*&#x27;], [&#x27;+&#x27;], [&#x27;,&#x27;], [&#x27;-&#x27;], [&#x27;.&#x27;], [&#x27;/&#x27;], [&#x27;:&#x27;], [&#x27;;&#x27;], [&#x27;&lt;&#x27;], [&#x27;=&#x27;],
            [&#x27;&gt;&#x27;], [&#x27;?&#x27;], [&#x27;@&#x27;], [&#x27;[&#x27;], [&#x27;]&#x27;], [&#x27;^&#x27;], [&#x27;_&#x27;], [&#x27;`&#x27;], [&#x27;{&#x27;], [&#x27;|&#x27;],
            [&#x27;}&#x27;], [&#x27;~&#x27;], [&#x27; &#x27;], [&#x27;\\&quot;&#x27;], [&#x27;\\\\&#x27;], [&#x27;\\/&#x27;], [&#x27;&lt;escaped&gt;&#x27;]],
        &#x27;&lt;number&gt;&#x27;: [[&#x27;&lt;int&gt;&#x27;, &#x27;&lt;frac&gt;&#x27;, &#x27;&lt;exp&gt;&#x27;]],
        &#x27;&lt;int&gt;&#x27;: [
           [&#x27;&lt;digit&gt;&#x27;], [&#x27;&lt;onenine&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;],
           [&#x27;-&#x27;, &#x27;&lt;digits&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;onenine&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;digits&gt;&#x27;: [[&#x27;&lt;digit-1&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;&lt;onenine&gt;&#x27;]],
        &#x27;&lt;onenine&gt;&#x27;: [[&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;]],
        &#x27;&lt;frac&gt;&#x27;: [[], [&#x27;.&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;exp&gt;&#x27;: [[], [&#x27;E&#x27;, &#x27;&lt;sign&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;], [&#x27;e&#x27;, &#x27;&lt;sign&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;sign&gt;&#x27;: [[], [&#x27;+&#x27;], [&#x27;-&#x27;]],
        &#x27;&lt;ws&gt;&#x27;: [[&#x27;&lt;sp1&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;], []],
        &#x27;&lt;sp1&gt;&#x27;: [[&#x27; &#x27;]], ##[[&#x27;\n&#x27;], [&#x27;\r&#x27;], [&#x27;\t&#x27;], [&#x27;\x08&#x27;], [&#x27;\x0c&#x27;]],
        &#x27;&lt;symbol&gt;&#x27;: [[&#x27;,&#x27;, &#x27;&lt;members&gt;&#x27;]],
        &#x27;&lt;symbol-1&gt;&#x27;: [[&#x27;,&#x27;, &#x27;&lt;elements&gt;&#x27;]],
        &#x27;&lt;symbol-2&gt;&#x27;: [[], [&#x27;&lt;symbol&gt;&#x27;, &#x27;&lt;symbol-2&gt;&#x27;]],
        &#x27;&lt;symbol-1-1&gt;&#x27;: [[], [&#x27;&lt;symbol-1&gt;&#x27;, &#x27;&lt;symbol-1-1&gt;&#x27;]],
        &#x27;&lt;character-1&gt;&#x27;: [[], [&#x27;&lt;character&gt;&#x27;, &#x27;&lt;character-1&gt;&#x27;]],
        &#x27;&lt;digit-1&gt;&#x27;: [[&#x27;&lt;digit&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;digit-1&gt;&#x27;]],
        &#x27;&lt;escaped&gt;&#x27;: [[&#x27;\\u&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;]],
        &#x27;&lt;hex&gt;&#x27;: [
            [&#x27;0&#x27;], [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;],
            [&#x27;a&#x27;], [&#x27;b&#x27;], [&#x27;c&#x27;], [&#x27;d&#x27;], [&#x27;e&#x27;], [&#x27;f&#x27;], [&#x27;A&#x27;], [&#x27;B&#x27;], [&#x27;C&#x27;], [&#x27;D&#x27;], [&#x27;E&#x27;],   [&#x27;F&#x27;]]
        }
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver is as follows:

<!--
############
print(repr(''.join(unify_key_inv(grammar, '<start>'))))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(repr(&#x27;&#x27;.join(unify_key_inv(grammar, &#x27;&lt;start&gt;&#x27;))))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar fuzzer can be implemented in pretty much any programming language
that supports basic data structures.
What if you want the derivation tree instead? The following modified fuzzer
will get you the derivation tree which
can be used with `fuzzingbook.GrammarFuzzer.tree_to_string`

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_nonterminal(v):
    return (v[0], v[-1]) == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)

def tree_to_string(tree):
    symbol, children, *_ = tree
    if children:
        return &#x27;&#x27;.join(tree_to_string(c) for c in children)
    else:
        return &#x27;&#x27; if is_nonterminal(symbol) else symbol

def unify_key_inv_t(g, key):
   return (key, unify_rule_inv_t(g, random.choice(g[key]))) if key in g else (key, [])

def unify_rule_inv_t(g, rule):
    return [unify_key_inv_t(g, token) for token in rule]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
res = unify_key_inv_t(grammar, '<start>')
print(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
res = unify_key_inv_t(grammar, &#x27;&lt;start&gt;&#x27;)
print(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The corresponding string is

<!--
############
print(repr(tree_to_string(res)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(repr(tree_to_string(res)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
One problem with the above fuzzer is that it can fail to terminate the
recursion. Here is an implementation that uses random expansions until
a configurable depth (`max_depth`) is reached, and beyond that, uses
purely non-recursive cheap expansions.

<!--
############
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
        if depth > max_depth:
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
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
        self.cost = self.compute_cost(grammar)

    def compute_cost(self, grammar):
        cost = {}
        for k in grammar:
            cost[k] = {}
            for rule in grammar[k]:
                cost[k][str(rule)] = self.expansion_cost(grammar, rule, set())
        return cost

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LimitFuzzer:
    def symbol_cost(self, grammar, symbol, seen):
        if symbol in self.key_cost: return self.key_cost[symbol]
        if symbol in seen:
            self.key_cost[symbol] = float(&#x27;inf&#x27;)
            return float(&#x27;inf&#x27;)
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
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return self.gen_rule(random.choice(rules), depth+1, max_depth)

    def gen_rule(self, rule, depth, max_depth):
        return &#x27;&#x27;.join(self.gen_key(token, depth, max_depth) for token in rule)

    def fuzz(self, key=&#x27;&lt;start&gt;&#x27;, max_depth=10):
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it:

<!--
############
gf = LimitFuzzer(grammar)
for i in range(100):
   print(gf.fuzz(key='<start>', max_depth=10))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf = LimitFuzzer(grammar)
for i in range(100):
   print(gf.fuzz(key=&#x27;&lt;start&gt;&#x27;, max_depth=10))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Iterative fuzzer
One of the problems with the above fuzzer is that we use the Python stack to
keep track of the expansion tree. Unfortunately, Python is really limited in
terms of the usable stack depth. This can make it hard to generate deeply
nested trees. One alternative solution is to handle the stack management
ourselves as we show next.
First, we define an iterative version of the tree_to_string function called `iter_tree_to_str()` as below.

<!--
############
def modifiable(tree):
    name, children, *rest = tree
    if not is_nt(name): return [name, []]
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def modifiable(tree):
    name, children, *rest = tree
    if not is_nt(name): return [name, []]
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
    return &#x27;&#x27;.join(expanded)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
You can use it as follows:

<!--
############
print(iter_tree_to_str(('<start>', [('<json>', [('<element>', [('<ws>', [('<sp1>', [(' ', [])]), ('<ws>', [])]), ('<value>', [('null', [])]), ('<ws>', [])])])])))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(iter_tree_to_str((&#x27;&lt;start&gt;&#x27;, [(&#x27;&lt;json&gt;&#x27;, [(&#x27;&lt;element&gt;&#x27;, [(&#x27;&lt;ws&gt;&#x27;, [(&#x27;&lt;sp1&gt;&#x27;, [(&#x27; &#x27;, [])]), (&#x27;&lt;ws&gt;&#x27;, [])]), (&#x27;&lt;value&gt;&#x27;, [(&#x27;null&#x27;, [])]), (&#x27;&lt;ws&gt;&#x27;, [])])])])))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we add the `iter_gen_key()` to `LimitFuzzer`

<!--
############
class LimitFuzzer(LimitFuzzer):
    def iter_gen_key(self, key, max_depth):
        def get_def(t):
            if is_nonterminal(t):
                return [t, None]
            else:
                return [t, []]

        cheap_grammar = {}
        for k in self.cost:
            # should we minimize it here? We simply avoid infinities
            rules = self.grammar[k]
            min_cost = min([self.cost[k][str(r)] for r in rules])
            #grammar[k] = [r for r in grammar[k] if self.cost[k][str(r)] == float('inf')]
            cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]

        root = [key, None]
        queue = [(0, root)]
        while queue:
            # get one item to expand from the queue
            (depth, item), *queue = queue
            key = item[0]
            if item[1] is not None: continue
            grammar = self.grammar if depth < max_depth else cheap_grammar
            chosen_rule = random.choice(grammar[key])
            expansion = [get_def(t) for t in chosen_rule]
            item[1] = expansion
            for t in expansion: queue.append((depth+1, t))
        return root

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LimitFuzzer(LimitFuzzer):
    def iter_gen_key(self, key, max_depth):
        def get_def(t):
            if is_nonterminal(t):
                return [t, None]
            else:
                return [t, []]

        cheap_grammar = {}
        for k in self.cost:
            # should we minimize it here? We simply avoid infinities
            rules = self.grammar[k]
            min_cost = min([self.cost[k][str(r)] for r in rules])
            #grammar[k] = [r for r in grammar[k] if self.cost[k][str(r)] == float(&#x27;inf&#x27;)]
            cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]

        root = [key, None]
        queue = [(0, root)]
        while queue:
            # get one item to expand from the queue
            (depth, item), *queue = queue
            key = item[0]
            if item[1] is not None: continue
            grammar = self.grammar if depth &lt; max_depth else cheap_grammar
            chosen_rule = random.choice(grammar[key])
            expansion = [get_def(t) for t in chosen_rule]
            item[1] = expansion
            for t in expansion: queue.append((depth+1, t))
        return root
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we ensure that the iterative gen_key can be called by defining `iter_fuzz()`.

<!--
############
class LimitFuzzer(LimitFuzzer):
    def iter_fuzz(self, key='<start>', max_depth=10):
        self._s = self.iter_gen_key(key=key, max_depth=max_depth)
        return iter_tree_to_str(self._s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LimitFuzzer(LimitFuzzer):
    def iter_fuzz(self, key=&#x27;&lt;start&gt;&#x27;, max_depth=10):
        self._s = self.iter_gen_key(key=key, max_depth=max_depth)
        return iter_tree_to_str(self._s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
gf = LimitFuzzer(grammar)
for i in range(10):
   print(gf.iter_fuzz(key='<start>', max_depth=100))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf = LimitFuzzer(grammar)
for i in range(10):
   print(gf.iter_fuzz(key=&#x27;&lt;start&gt;&#x27;, max_depth=100))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2019-05-28-simplefuzzer-01.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
