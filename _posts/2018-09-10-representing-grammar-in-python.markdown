---
published: true
title: Representing a Grammar in Python
layout: post
comments: true
tags: parsing
categories: post
---

In the [previous](/post/2018/09/05/top-down-parsing/) [posts](/post/2018/09/06/peg-parsing/), I described how can write a parser. For doing that, I made use of a grammar written as a python data structure, with the assumption that it can be loaded as a JSON file if necessary. The grammar looks like this:

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

<!--
############
term_grammar = {
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],

        ['<term>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [[str(i)] for i in range(10)],
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
term_grammar = {
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;],

        [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [
        [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[str(i)] for i in range(10)],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
However, this is somewhat unsatisfying. There are too many distracting syntactic elements in the code, making it difficult to see where each elements are. What we want is a better representation. Indeed, one better representation is to lose one level of nesting, and instead, parse the string for terminals and non-terminals. The following representation uses a single string for a single rule, and a list for all alternative rules for a key.

<!--
############
term_grammar = {
    '<expr>': ['<term> + <expr}', '<term> - <expr>', '<term>'],
    '<term>': ['<fact> * <fact}', '<fact> / <fact>', '<fact>'],
    '<fact>': ['<digits>','(<expr>)'],
    '<digits>': ['{digit}{digits}','{digit}'],
    '<digit>': [str(i) for i in range(10)],
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
term_grammar = {
    &#x27;&lt;expr&gt;&#x27;: [&#x27;&lt;term&gt; + &lt;expr}&#x27;, &#x27;&lt;term&gt; - &lt;expr&gt;&#x27;, &#x27;&lt;term&gt;&#x27;],
    &#x27;&lt;term&gt;&#x27;: [&#x27;&lt;fact&gt; * &lt;fact}&#x27;, &#x27;&lt;fact&gt; / &lt;fact&gt;&#x27;, &#x27;&lt;fact&gt;&#x27;],
    &#x27;&lt;fact&gt;&#x27;: [&#x27;&lt;digits&gt;&#x27;,&#x27;(&lt;expr&gt;)&#x27;],
    &#x27;&lt;digits&gt;&#x27;: [&#x27;{digit}{digits}&#x27;,&#x27;{digit}&#x27;],
    &#x27;&lt;digit&gt;&#x27;: [str(i) for i in range(10)],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
But is there a better way? Ideally, one would like to define the grammar like one defines the class, so that it feels part of the language.
One mechanism we can (ab)use is the type annotations. Specifically in `Python 3.7` one can use the postponed evaluation of annotations to accomplish a DSL as below, with grammar keys as attributes of the Grammar class.
```python
class expr(Grammar):
    start: '<expr>'
    expr: '<term> + <term>' | '<term> - <term>'
    term: '<factor} * <term>' | '<factor> / <term>'
    factor: '( <expr> )' | '<integer>'
    integer: '<digit> <integer}' | '<digit>'
    digit: '0' | '1' | '2'
```
The annotations lets us access the types of each class as a string, that can be evaluated separately. The `Grammar` class is defined as follows:

<!--
############
import string
import ast
import re

RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')

class Grammar:
    def alternatives(self, k):
        def strings(v):
            if isinstance(v, ast.BinOp):
                return [self._parse_rule(v.right.s)] + strings(v.left)
            else: return [self._parse_rule(v.s)]
        return strings(ast.parse(self.rules(k[1:-1]), mode='eval').body)

    def _parse_rule(self, rule):
        return [token for token in re.split(RE_NONTERMINAL, rule) if token]

    def rules(self, k):
        return self.__annotations__[k]

    def keys(self):
        return ['<%s>' % k for k in self.__annotations__.keys()]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
import ast
import re

RE_NONTERMINAL = re.compile(r&#x27;(&lt;[^&lt;&gt; ]*&gt;)&#x27;)

class Grammar:
    def alternatives(self, k):
        def strings(v):
            if isinstance(v, ast.BinOp):
                return [self._parse_rule(v.right.s)] + strings(v.left)
            else: return [self._parse_rule(v.s)]
        return strings(ast.parse(self.rules(k[1:-1]), mode=&#x27;eval&#x27;).body)

    def _parse_rule(self, rule):
        return [token for token in re.split(RE_NONTERMINAL, rule) if token]

    def rules(self, k):
        return self.__annotations__[k]

    def keys(self):
        return [&#x27;&lt;%s&gt;&#x27; % k for k in self.__annotations__.keys()]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Unfortunately, to be able to use the annotation feature,
we need to place import `from __future__ import annotations` at the top of the
file. So, while we can do that in practice, it is difficult to do that in this
blog post form. Hence, I put the contents of my grammar into a string, and
evaluate that string instead.

<!--
############
s = """
 __future__ import annotations

s expr(Grammar):
start: '<expr>'
expr: '<term> + <term>' | '<term> - <term>'
term: '<factor> * <term>' | '<factor> / <term>'
factor: '( <expr> )' | '<integer>'
integer: '<digit> <integer>' | '<digit>'
digit: '0' | '1' | '2'

exec(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;
 __future__ import annotations

s expr(Grammar):
start: &#x27;&lt;expr&gt;&#x27;
expr: &#x27;&lt;term&gt; + &lt;term&gt;&#x27; | &#x27;&lt;term&gt; - &lt;term&gt;&#x27;
term: &#x27;&lt;factor&gt; * &lt;term&gt;&#x27; | &#x27;&lt;factor&gt; / &lt;term&gt;&#x27;
factor: &#x27;( &lt;expr&gt; )&#x27; | &#x27;&lt;integer&gt;&#x27;
integer: &#x27;&lt;digit&gt; &lt;integer&gt;&#x27; | &#x27;&lt;digit&gt;&#x27;
digit: &#x27;0&#x27; | &#x27;1&#x27; | &#x27;2&#x27;

exec(s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given all this, to print the grammar in a readable form is simply:

<!--
############
e = expr()
for i in e.keys():
    print(i, "::= ")
    for alt in  e.alternatives(i):
        print("\t| %s\t\t" % alt)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
e = expr()
for i in e.keys():
    print(i, &quot;::= &quot;)
    for alt in  e.alternatives(i):
        print(&quot;\t| %s\t\t&quot; % alt)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need to make our grammar available in the standard format. So, let us
define such an accessor.

<!--
############
class Grammar(Grammar):
    @classmethod
    def create(cls, grammar=None, start=None):
        slf = cls()
        my_grammar = {k:[alt for alt in slf.alternatives(k)]
                for k in slf.keys()}
        my_grammar = slf.update(my_grammar, grammar, start)
        slf.grammar = my_grammar
        if start is not None:
            slf.start = start
        return slf

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        return {**my_grammar, **grammar}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Grammar(Grammar):
    @classmethod
    def create(cls, grammar=None, start=None):
        slf = cls()
        my_grammar = {k:[alt for alt in slf.alternatives(k)]
                for k in slf.keys()}
        my_grammar = slf.update(my_grammar, grammar, start)
        slf.grammar = my_grammar
        if start is not None:
            slf.start = start
        return slf

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        return {**my_grammar, **grammar}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
exec(s)
e = expr.create()
print(e.grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
exec(s)
e = expr.create()
print(e.grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This works well. Let us extend our grammar with a few convenience methods.
For example, we want to specify separate processing if the nonterminal starts
with a meta character such as `+`, `*`, `$` or `@`.
We define any nonterminal that starts with `*` to mean zero or more of its
nonterminal without the meta character.

<!--
############
class Grammar(Grammar):
    def is_nonterminal(self, k):
        return (k[0], k[-1]) == ('<', '>')

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        new_g = {**my_grammar, **grammar}
        new_keys = set()
        for k in new_g:
            for alt in new_g[k]:
                for t in alt:
                    if self.is_nonterminal(t) and t[1] in '+*$@':
                        new_keys.add(t)

        for k in new_keys:
            if k[1] == '*':
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], []]
            elif  k[1] == '+':
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], [ok]]

        return new_g

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Grammar(Grammar):
    def is_nonterminal(self, k):
        return (k[0], k[-1]) == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)

    def update(self, my_grammar, grammar, start):
        if grammar is None: grammar = {}
        new_g = {**my_grammar, **grammar}
        new_keys = set()
        for k in new_g:
            for alt in new_g[k]:
                for t in alt:
                    if self.is_nonterminal(t) and t[1] in &#x27;+*$@&#x27;:
                        new_keys.add(t)

        for k in new_keys:
            if k[1] == &#x27;*&#x27;:
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], []]
            elif  k[1] == &#x27;+&#x27;:
                ok = k[0] + k[2:]
                new_g[k] = [[ok, k], [ok]]

        return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
s = """
 __future__ import annotations

s expr(Grammar):
start: '<expr>'
expr: '<term> + <term>' | '<term> - <term>'
term: '<factor> * <term>' | '<factor> / <term>'
factor: '( <expr> )' | '<integer>'
integer: '<*digit>'
digit: '0' | '1' | '2'


exec(s)
e = expr.create()
print(e.grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;
 __future__ import annotations

s expr(Grammar):
start: &#x27;&lt;expr&gt;&#x27;
expr: &#x27;&lt;term&gt; + &lt;term&gt;&#x27; | &#x27;&lt;term&gt; - &lt;term&gt;&#x27;
term: &#x27;&lt;factor&gt; * &lt;term&gt;&#x27; | &#x27;&lt;factor&gt; / &lt;term&gt;&#x27;
factor: &#x27;( &lt;expr&gt; )&#x27; | &#x27;&lt;integer&gt;&#x27;
integer: &#x27;&lt;*digit&gt;&#x27;
digit: &#x27;0&#x27; | &#x27;1&#x27; | &#x27;2&#x27;


exec(s)
e = expr.create()
print(e.grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2018-09-10-representing-grammar-in-python.py).


