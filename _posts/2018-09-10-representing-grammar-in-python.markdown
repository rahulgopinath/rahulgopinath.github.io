---
published: true
title: Representing a Grammar in Python
layout: post
comments: true
tags: parsing
categories: post
---

In the [previous](/post/2018/09/05/top-down-parsing/) [posts](/post/2018/09/06/peg-parsing/), I described how can write a parser. For doing that, I made use of a grammar written as a python data structure, with the assumption that it can be loaded as a JSON file if necessary. The grammar looks like this:
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

<!--
############
term_grammar = {
    'expr': [
        ['term', '+', 'expr'],
        ['term', '-', 'expr'],

        ['term']],
    'term': [
        ['fact', '*', 'term'],
        ['fact', '/', 'term'],
        ['fact']],
    'fact': [
        ['digits'],
        ['(','expr',')']],
    'digits': [
        ['digit','digits'],
        ['digit']],
    'digit': [[str(i)] for i in range(10)],
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
term_grammar = {
    &#x27;expr&#x27;: [
        [&#x27;term&#x27;, &#x27;+&#x27;, &#x27;expr&#x27;],
        [&#x27;term&#x27;, &#x27;-&#x27;, &#x27;expr&#x27;],

        [&#x27;term&#x27;]],
    &#x27;term&#x27;: [
        [&#x27;fact&#x27;, &#x27;*&#x27;, &#x27;term&#x27;],
        [&#x27;fact&#x27;, &#x27;/&#x27;, &#x27;term&#x27;],
        [&#x27;fact&#x27;]],
    &#x27;fact&#x27;: [
        [&#x27;digits&#x27;],
        [&#x27;(&#x27;,&#x27;expr&#x27;,&#x27;)&#x27;]],
    &#x27;digits&#x27;: [
        [&#x27;digit&#x27;,&#x27;digits&#x27;],
        [&#x27;digit&#x27;]],
    &#x27;digit&#x27;: [[str(i)] for i in range(10)],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
However, this is somewhat unsatisfying. There are too many distracting syntactic elements in the code, making it difficult to see where each elements are. What we want is a better representation. Indeed, one better representation is to lose one level of nesting, and instead, parse the string for terminals and non-terminals. The following representation uses a single string for a single production, and a list for all alternative productions for a key.

<!--
############
term_grammar = {
    'expr': ['{term} + {expr}', '{term} - {expr}', 'term'],
    'term': ['{fact} * {fact}', '{fact} / {fact}', '{fact}'],
    'fact': ['{digits}','({expr})'],
    'digits': ['{digit}{digits}','{digit}'],
    'digit': [str(i) for i in range(10)],
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
term_grammar = {
    &#x27;expr&#x27;: [&#x27;{term} + {expr}&#x27;, &#x27;{term} - {expr}&#x27;, &#x27;term&#x27;],
    &#x27;term&#x27;: [&#x27;{fact} * {fact}&#x27;, &#x27;{fact} / {fact}&#x27;, &#x27;{fact}&#x27;],
    &#x27;fact&#x27;: [&#x27;{digits}&#x27;,&#x27;({expr})&#x27;],
    &#x27;digits&#x27;: [&#x27;{digit}{digits}&#x27;,&#x27;{digit}&#x27;],
    &#x27;digit&#x27;: [str(i) for i in range(10)],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Since we are using the string interpolation in Python, one can recover the non-terminal symbols given any of the productions as follows using the `parse` method.

<!--
############
def nonterminals(production):
    return set(i[1] for i in string.Formatter().parse(production) if i[1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def nonterminals(production):
    return set(i[1] for i in string.Formatter().parse(production) if i[1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
But is there a better way? Ideally, one would like to define the grammar like one defines the class, so that it feels part of the language.
One mechanism we can (ab)use is the type annotations. Specifically in `Python 3.7` one can use the postponed evaluation of annotations to accomplish a DSL as below, with grammar keys as attributes of the grammar class.
```python
class expr(grammar):
    start: '{expr}'
    expr: '{term} + {term}' | '{term} - {term}'
    term: '{factor} * {term}' | 'factor / {term}'
    factor: '( {expr} )' | '{integer}'
    integer: '{digit} {integer}' | '{digit}'
    digit: '0' | '1' | '2'
```
The annotations lets us access the types of each class as a string, that can be evaluated separately. The `grammar` class is defined as follows:

<!--
############
import string
import ast

class grammar:
    def alternatives(self, k):
        def strings(v):
            return [v.right.s] + strings(v.left) if isinstance(v, ast.BinOp) else [v.s]
        return strings(ast.parse(self.production(k), mode='eval').body)

    def nonterminals(self, expansion):
        return set(i[1] for i in string.Formatter().parse(expansion) if i[1])

    def production(self, k):
        return self.__annotations__[k]

    def keys(self):
        return self.__annotations__.keys()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
import ast

class grammar:
    def alternatives(self, k):
        def strings(v):
            return [v.right.s] + strings(v.left) if isinstance(v, ast.BinOp) else [v.s]
        return strings(ast.parse(self.production(k), mode=&#x27;eval&#x27;).body)

    def nonterminals(self, expansion):
        return set(i[1] for i in string.Formatter().parse(expansion) if i[1])

    def production(self, k):
        return self.__annotations__[k]

    def keys(self):
        return self.__annotations__.keys()
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
from __future__ import annotations

class expr(grammar):
    start: '{expr}'
    expr: '{term} + {term}' | '{term} - {term}'
    term: '{factor} * {term}' | 'factor / {term}'
    factor: '( {expr} )' | '{integer}'
    integer: '{digit} {integer}' | '{digit}'
    digit: '0' | '1' | '2'
"""
exec(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
s = &quot;&quot;&quot;
from __future__ import annotations

class expr(grammar):
    start: &#x27;{expr}&#x27;
    expr: &#x27;{term} + {term}&#x27; | &#x27;{term} - {term}&#x27;
    term: &#x27;{factor} * {term}&#x27; | &#x27;factor / {term}&#x27;
    factor: &#x27;( {expr} )&#x27; | &#x27;{integer}&#x27;
    integer: &#x27;{digit} {integer}&#x27; | &#x27;{digit}&#x27;
    digit: &#x27;0&#x27; | &#x27;1&#x27; | &#x27;2&#x27;
&quot;&quot;&quot;
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
        print("\t| %s\t\t # %s" % (alt.strip(), e.nonterminals(alt)))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
e = expr()
for i in e.keys():
    print(i, &quot;::= &quot;)
    for alt in  e.alternatives(i):
        print(&quot;\t| %s\t\t # %s&quot; % (alt.strip(), e.nonterminals(alt)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
