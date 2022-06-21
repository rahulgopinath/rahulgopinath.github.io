---
published: true
title: A Fast Grammar Fuzzer by Compiling the Grammar
layout: post
comments: true
tags: fuzzing
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

<script src="/resources/js/graphviz/index.min.js"></script>
<script>
// From https://github.com/hpcc-systems/hpcc-js-wasm
// Hosted for teaching.
var hpccWasm = window["@hpcc-js/wasm"];
function display_dot(dot_txt, div) {
    hpccWasm.graphviz.layout(dot_txt, "svg", "dot").then(svg => {
        div.innerHTML = svg;
    });
}
window.display_dot = display_dot
// from js import display_dot
</script>

<script src="/resources/pyodide/full/3.9/pyodide.js"></script>
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
In a previous [post](/post/2019/05/28/simplefuzzer-01/) I disucssed a simple
fuzzer.  While simple, the fuzzer is somewhat inefficient. This post discusses
a way to speed it up -- by compiling.

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, we start with a grammar.

<!--
############
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


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EXPR_GRAMMAR = {
    &quot;&lt;start&gt;&quot;: [[&quot;&lt;expr&gt;&quot;]],
    &quot;&lt;expr&gt;&quot;: [
        [&quot;&lt;term&gt;&quot;, &quot;+&quot;, &quot;&lt;expr&gt;&quot;],
        [&quot;&lt;term&gt;&quot;, &quot;-&quot;, &quot;&lt;expr&gt;&quot;],
        [&quot;&lt;term&gt;&quot;]],
    &quot;&lt;term&gt;&quot;: [
        [&quot;&lt;factor&gt;&quot;, &quot;*&quot;, &quot;&lt;term&gt;&quot;],
        [&quot;&lt;factor&gt;&quot;, &quot;/&quot;, &quot;&lt;term&gt;&quot;],
        [&quot;&lt;factor&gt;&quot;]],
    &quot;&lt;factor&gt;&quot;: [
        [&quot;+&quot;, &quot;&lt;factor&gt;&quot;],
        [&quot;-&quot;, &quot;&lt;factor&gt;&quot;],
        [&quot;(&quot;, &quot;&lt;expr&gt;&quot;, &quot;)&quot;],
        [&quot;&lt;integer&gt;&quot;, &quot;.&quot;, &quot;&lt;integer&gt;&quot;],
        [&quot;&lt;integer&gt;&quot;]],
    &quot;&lt;integer&gt;&quot;: [
        [&quot;&lt;digit&gt;&quot;, &quot;&lt;integer&gt;&quot;],
        [&quot;&lt;digit&gt;&quot;]],
    &quot;&lt;digit&gt;&quot;: [[&quot;0&quot;], [&quot;1&quot;], [&quot;2&quot;], [&quot;3&quot;], [&quot;4&quot;], [&quot;5&quot;], [&quot;6&quot;], [&quot;7&quot;], [&quot;8&quot;], [&quot;9&quot;]]
}

EXPR_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Compiled Fuzzer

This grammar fuzzer is described in the paper
[*Building Fast Fuzzers*](/publications/2019/11/18/arxiv-building/).
The idea is to compile a grammar definition to the corresponding source code.
Each nonterminal symbol becomes a procedure. First we define a few helpers.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def symbol_cost(grammar, symbol, seen, cache):
    if symbol in seen: return float(&#x27;inf&#x27;)
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We are going to compile the grammar, which will
become a source file that we load separately. To ensure that we do not
descend into quoting hell, we transform the grammar so that we store the
character bytes rather than the terminals as strings.

<!--
############
def transform_bytes(grammar):
   new_g = {}
   for k in grammar:
       new_g[k] = [
               [t if fuzzer.is_nonterminal(t) else ord(t) for t in r]
               for r in grammar[k]]
   return new_g

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def transform_bytes(grammar):
   new_g = {}
   for k in grammar:
       new_g[k] = [
               [t if fuzzer.is_nonterminal(t) else ord(t) for t in r]
               for r in grammar[k]]
   return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
g = transform_bytes(EXPR_GRAMMAR)
for k in g:
    print(k)
    for r in g[k]:
        print('  ', r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = transform_bytes(EXPR_GRAMMAR)
for k in g:
    print(k)
    for r in g[k]:
        print(&#x27;  &#x27;, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the class.

<!--
############
class F1Fuzzer(fuzzer.LimitFuzzer):
    def __init__(self, grammar):
        self.grammar = transform_bytes(grammar)
        self.cost = compute_cost(self.grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1Fuzzer(fuzzer.LimitFuzzer):
    def __init__(self, grammar):
        self.grammar = transform_bytes(grammar)
        self.cost = compute_cost(self.grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Convenience methods

<!--
############
class F1Fuzzer(F1Fuzzer):
    def add_indent(self, string, indent):
        return '\n'.join([indent + i for i in string.split('\n')])

    def k_to_s(self, k): return k[1:-1].replace('-', '_')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1Fuzzer(F1Fuzzer):
    def add_indent(self, string, indent):
        return &#x27;\n&#x27;.join([indent + i for i in string.split(&#x27;\n&#x27;)])

    def k_to_s(self, k): return k[1:-1].replace(&#x27;-&#x27;, &#x27;_&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Cheap grammar compilation

In the previous [post](/post/2019/05/28/simplefuzzer-01/), I described how we
shift  to a cheap grammar when we exhaust our budget. We use the same thing
here. That is, at some point we need to curtail the recursion. Hence, we
define the cheap grammar that does not contain recursion. The idea is that
if we go beyond a given depth, we switch to choosing rules from the
non-recursive grammar (cheap grammar).

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The cheap grammar from expr grammar

<!--
############
expr_cg = F1Fuzzer(EXPR_GRAMMAR).cheap_grammar()
for k in expr_cg:
    print(k)
    for r in expr_cg[k]:
        print('   ', r)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr_cg = F1Fuzzer(EXPR_GRAMMAR).cheap_grammar()
for k in expr_cg:
    print(k)
    for r in expr_cg[k]:
        print(&#x27;   &#x27;, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Translation

Translating the nonterminals of the cheap grammar is simple because there is
no recursion. We simply choose a random rule to expand.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1Fuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
gen_%s_cheap()&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
result.append(%d)&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)


    def gen_alt_src_cheap(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s_cheap():
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
%s
        return&#x27;&#x27;&#x27; % (i, self.add_indent(
            self.gen_rule_src_cheap(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src_cheap('<expr>',
        transform_bytes(EXPR_GRAMMAR))
print(src)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src_cheap(&#x27;&lt;expr&gt;&#x27;,
        transform_bytes(EXPR_GRAMMAR))
print(src)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Main grammar compilation

For recursive grammars, we need to verify that the depth of recursion is not
beyond what is specified. If it has gone beyond the maximum specified depth,
we expand the cheap grammar instead.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1Fuzzer(F1Fuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
gen_%s(max_depth, next_depth)&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
result.append(%d)&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth &gt; max_depth:
        gen_%(name)s_cheap()
        return
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
%s
        return&#x27;&#x27;&#x27; % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src('<expr>',
        transform_bytes(EXPR_GRAMMAR))
print(src)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
src = F1Fuzzer(EXPR_GRAMMAR).gen_alt_src(&#x27;&lt;expr&gt;&#x27;,
        transform_bytes(EXPR_GRAMMAR))
print(src)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The complete driver

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import types
class F1Fuzzer(F1Fuzzer):
    def gen_main_src(self):
        return &#x27;&#x27;&#x27;
import random
result = []
def start(max_depth):
    gen_start(max_depth)
    v = &#x27;&#x27;.join([chr(i) for i in result])
    result.clear()
    return v
        &#x27;&#x27;&#x27;

    def gen_fuzz_src(self):
        result = []
        cheap_grammar = self.cheap_grammar()
        for key in cheap_grammar:
            result.append(self.gen_alt_src_cheap(key, cheap_grammar))
        for key in self.grammar:
            result.append(self.gen_alt_src(key, self.grammar))
        return &#x27;\n&#x27;.join(result)

    def fuzz_src(self, key=&#x27;&lt;start&gt;&#x27;):
        result = [self.gen_fuzz_src(),
                  self.gen_main_src()]
        return &#x27;&#x27;.join(result)

    def load_src(self, src, mn):
        module = types.ModuleType(mn)
        exec(src, module.__dict__)
        return module

    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return self.load_src(cf_src, name + &#x27;_f1_fuzzer&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
expr_fuzzer = F1Fuzzer(EXPR_GRAMMAR).fuzzer('expr_fuzzer')
for i in range(10):
    v = expr_fuzzer.start(10)
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr_fuzzer = F1Fuzzer(EXPR_GRAMMAR).fuzzer(&#x27;expr_fuzzer&#x27;)
for i in range(10):
    v = expr_fuzzer.start(10)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## A Problem -- Recursion
A problem with the compiled grammar fuzzer is that it relies on recursion,
and Python limits the recursion depth arbitrarily (starting with just 1000).
Hence, we need a solution that allows us to go past that depth.

We discussed [here](/post/2022/04/17/python-iterative-copy/) how to use
generators as a continuation passing trampoline. We use the same technique
again. The basic technique is to turn every function call into a `yield`
statement, and return the generator. A loop then translates activates
and traverses these generators.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1CPSFuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
yield gen_%s_cheap()&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
result.append(%d)&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)


    def gen_alt_src_cheap(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s_cheap():
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
%s
        return&#x27;&#x27;&#x27; % (i, self.add_indent(self.gen_rule_src_cheap(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)

class F1CPSFuzzer(F1CPSFuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
yield gen_%s(max_depth, next_depth)&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
result.append(%d)&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth &gt; max_depth:
        yield gen_%(name)s_cheap()
        return
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
%s
        return&#x27;&#x27;&#x27; % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)

class F1CPSFuzzer(F1CPSFuzzer):
    def gen_main_src(self):
        return &#x27;&#x27;&#x27;
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
    v = &#x27;&#x27;.join([chr(i) for i in result])
    result.clear()
    return v
        &#x27;&#x27;&#x27;

    def gen_fuzz_src(self):
        result = []
        cheap_grammar = self.cheap_grammar()
        for key in cheap_grammar:
            result.append(self.gen_alt_src_cheap(key, cheap_grammar))
        for key in self.grammar:
            result.append(self.gen_alt_src(key, self.grammar))
        return &#x27;\n&#x27;.join(result)

    def fuzz_src(self, key=&#x27;&lt;start&gt;&#x27;):
        result = [self.gen_fuzz_src(),
                  self.gen_main_src()]
        return &#x27;&#x27;.join(result)

    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return self.load_src(cf_src, name + &#x27;_f1_fuzzer&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Example

<!--
############
src = F1CPSFuzzer(EXPR_GRAMMAR).fuzz_src('<start>')
print(src)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
src = F1CPSFuzzer(EXPR_GRAMMAR).fuzz_src(&#x27;&lt;start&gt;&#x27;)
print(src)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need to redefine our cost computation which is recursive.

<!--
############
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


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def symbol_cost_cps(grammar, symbol, seen, cache):
    if symbol in seen: return float(&#x27;inf&#x27;)
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
expr_fuzzer = F1CPSFuzzer(EXPR_GRAMMAR).fuzzer('expr_fuzzer')
for i in range(10):
    v = expr_fuzzer.start(10)
    print(repr(v))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr_fuzzer = F1CPSFuzzer(EXPR_GRAMMAR).fuzzer(&#x27;expr_fuzzer&#x27;)
for i in range(10):
    v = expr_fuzzer.start(10)
    print(repr(v))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is a useful trick. But what if we do not want to use the generator hack?
Turns out, there is an easier solution. The idea is to wrap the remaining
computation as a continuation and return. In our case, we modify this
technique slightly.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1LFuzzer(F1Fuzzer):
    def gen_rule_src_cheap(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
lambda: gen_%s_cheap(),&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
lambda: result.append(%d),&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)


    def gen_alt_src_cheap(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s_cheap():
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
        return [%s]&#x27;&#x27;&#x27; % (i, self.add_indent(self.gen_rule_src_cheap(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)

class F1LFuzzer(F1LFuzzer):
    def gen_rule_src(self, rule, key, i, grammar):
        res = []
        for token in rule:
            if token in grammar:
                res.append(&#x27;&#x27;&#x27;\
lambda: gen_%s(max_depth, next_depth),&#x27;&#x27;&#x27; % (self.k_to_s(token)))
            else:
                res.append(&#x27;&#x27;&#x27;\
lambda: result.append(%d),&#x27;&#x27;&#x27; % token)
        return &#x27;\n&#x27;.join(res)

    def gen_alt_src(self, key, grammar):
        rules = grammar[key]
        result = []
        result.append(&#x27;&#x27;&#x27;
def gen_%(name)s(max_depth, depth=0):
    next_depth = depth + 1
    if depth &gt; max_depth:
        return [lambda: gen_%(name)s_cheap()]
    val = random.randrange(%(nrules)s)&#x27;&#x27;&#x27; % {
            &#x27;name&#x27;:self.k_to_s(key),
            &#x27;nrules&#x27;:len(rules)})
        for i, rule in enumerate(rules):
            result.append(&#x27;&#x27;&#x27;\
    if val == %d:
        return [%s]&#x27;&#x27;&#x27; % (i, self.add_indent(self.gen_rule_src(rule, key, i, grammar),&#x27;        &#x27;)))
        return &#x27;\n&#x27;.join(result)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now define our trampoline, which is different from previous.

<!--
############
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
            stack = res + stack
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F1LFuzzer(F1LFuzzer):
    def gen_main_src(self):
        return &#x27;&#x27;&#x27;
def trampoline(gen):
    ret = None
    stack = gen
    while stack:
        cur, *stack = stack
        res = cur()
        if res is not None:
            stack = res + stack
    return

import random
result = []
def start(max_depth):
    trampoline(gen_start(max_depth))
    v = &#x27;&#x27;.join([chr(i) for i in result])
    result.clear()
    return v
        &#x27;&#x27;&#x27;

    def gen_fuzz_src(self):
        result = []
        cheap_grammar = self.cheap_grammar()
        for key in cheap_grammar:
            result.append(self.gen_alt_src_cheap(key, cheap_grammar))
        for key in self.grammar:
            result.append(self.gen_alt_src(key, self.grammar))
        return &#x27;\n&#x27;.join(result)

    def fuzz_src(self, key=&#x27;&lt;start&gt;&#x27;):
        result = [self.gen_fuzz_src(),
                  self.gen_main_src()]
        return &#x27;&#x27;.join(result)

    def fuzzer(self, name):
        cf_src = self.fuzz_src()
        return self.load_src(cf_src, name + &#x27;_f1_fuzzer&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
f = F1LFuzzer(EXPR_GRAMMAR)
expr_fuzzer = f.fuzzer('expr_fuzzer')
for i in range(10):
    v = expr_fuzzer.start(10)
    print(repr(v))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
f = F1LFuzzer(EXPR_GRAMMAR)
expr_fuzzer = f.fuzzer(&#x27;expr_fuzzer&#x27;)
for i in range(10):
    v = expr_fuzzer.start(10)
    print(repr(v))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-05-15-compiled-fuzzer.py).


