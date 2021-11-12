---
published: true
title: Intersection Between a Context Free Grammar and a Regular Grammar
layout: post
comments: true
tags: python
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.9/';</script>
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
We [previously saw](/post/2021/10/26/regular-grammar-expressions/) how to
produce a grammar that is an intersection of two regular grammars. One of the
interesting things about regular grammars is that, you can produce an
intersection between a regular grammar and a context-free grammar, and the
result will be context-free. The traditional technique for intersecting
between a CFL and an RL is to produce the PDA and the DFA equivalents of both,
and produce a product PDA. However, there is an even better way called
the Bar-Hiller construction[^barhiller1961on] that lets you compute an
intersection between a CFG and RG directly.

The essential idea is to first recognize that a right linear grammar that
encodes a regular language can be made to have a final nonterminal to expand.
The below are patterns in right linear grammars.

```
<s> := a <a>
     | b <b>
<a> := c
     | {empty}
<b> := b
```

Given such a grammar, one can convert it as below so that the last nonterminal
to be expanded is `<f>`
 
```
<s> := a <a>
     | b <b>
<a> := c <f>
     | <f>
<b> := b <f>
<f> := {empty}
```
Why do we do this? because this lets us represent the grammar as a
non-deterministic finite automation with a single start state (`<S>`) and
a single end state (`<F>`). This is required for the Bar-Hiller construction.

Next, we also convert the context-free grammar to Chomsky-Normal-Form
(actually we do not need as much restrictions, as we will see later).
The CNF looks like below.

```
<S> := <A><B>
<A> := a
     | {empty} 
<B> := b
```
The essential idea is to take all nonterminal symbols from the regular
grammar, and all nonterminal symbols from the context-free grammar, and
produce triplets which starts with a nonterminal from RG, and ends with
another nonterminal from the RG, and has a nonterminal from CFG in the
middle. E.g. `<a,A,b>`.
The intersection grammar is represented by the start symbol `<s,S,f>` where
`<s>` is the start symbol of the regular grammar, and `<f>` is the final
symbol as we discussed above. `<S>` is the start symbol of the context-free
grammar. The essential idea is that if we want to produce `<s,S,f>` then
it can only be produced if the rules can be written such that they start with
`<s>` and end with `<f>`. That is, the definition of `<s,S,f>` is as follows:

```
<s,S,f> := <s,A,x><x,B,f>
```

where `<x>` is a nonterminal symbol in the regular grammar such that it is
reachable from `<s>`, and `<f>` is reachable from `<x>`. Further, it means
that if we go from `<s>` to `<x>` by consuming a string, then that string must
also be parsable by `<A>`. In our example, this could be one rule.

```
<s,S,f> := <s,A,a><a,B,f>
```

If one of the tokens in the context-free rule is a terminal symbol, then we
get an opportunity to immediately verify our construction.
```
<s,A,a> := [<s>,a,<a>]
```
As you can see, `<A>` has one of the rules that contain a single terminal
symbol -- `a`. So, we can immediately see that the requirement `<s,A,a>`
was satisfied. That is, `<s>` goes to `<a>` by consuming `a`, and this is
witnessed by `[<s>,a,<a>]`. So, we will keep this rule in the intersection
grammar as
```
<s,A,a> := a
```
What about the second rule?
```
<s,A,a> := [<s>,{empty},<a>]
```
This however, does not work because there is no epsilon transition from `<s>`
to `<a>`. Hence, this rule is skipped in the resulting grammar.
Let us see how to implement this technique. 

We start by importing the prerequisites.

##### System Imports

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
sympy
</textarea>
</form>

##### Available Packages

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gfaultexpressions-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gfaultexpressions as gexpr
import earleyparser
import rxfuzzer
import rxcanonical
import sympy
import itertools as I

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gfaultexpressions as gexpr
import earleyparser
import rxfuzzer
import rxcanonical
import sympy
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Binary Normal Form

Next, we want to limit the number of forms of production rules that we want to
handle. Hence, we convert the context-free grammar to a normal form such that
it conforms exclusively to the following pattern.
 
1.  $$ A \rightarrow a $$
2.  $$ A \rightarrow B $$
3.  $$ A \rightarrow aB $$
4.  $$ A \rightarrow Bb $$
5.  $$ A \rightarrow BC $$
6.  $$ S \rightarrow \epsilon $$
 
That is, each production rule has at most two tokens. The new normal form is
provided by `binary_normal_form()`. Note that this is not exactly the
[Chomsky Normal Form](https://en.wikipedia.org/wiki/Chomsky_normal_form). We
do not need the full restrictions of CNF. However, our algorithms will also
work if a grammar in CNF form is given.

<!--
############
from collections import defaultdict

def new_k(k, y, x):
    return '<%s %s-%s>' % (k[1:-1], str(y), str(x))

def binary_normal_form(g, s):
    new_g = defaultdict(list)
    productions_to_process = [(k, i, 0, r) for k in g for i,r in enumerate(g[k])]
    while productions_to_process:
        (k, y, x, r), *productions_to_process =  productions_to_process
        if x > 0:
            k_ = new_k(k, y, x)
        else:
            k_ = k
        if len(r) == 0:
            new_g[k_].append(r)
        elif len(r) == 1:
            new_g[k_].append(r)
        elif len(r) == 2:
            new_g[k_].append(r)
        else:
            new_g[k_].append(r[:1] + [new_k(k, y, x+1)])
            remaining = r[1:]
            prod = (k, y, x+1, remaining)
            productions_to_process.append(prod)
    return new_g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from collections import defaultdict

def new_k(k, y, x):
    return &#x27;&lt;%s %s-%s&gt;&#x27; % (k[1:-1], str(y), str(x))

def binary_normal_form(g, s):
    new_g = defaultdict(list)
    productions_to_process = [(k, i, 0, r) for k in g for i,r in enumerate(g[k])]
    while productions_to_process:
        (k, y, x, r), *productions_to_process =  productions_to_process
        if x &gt; 0:
            k_ = new_k(k, y, x)
        else:
            k_ = k
        if len(r) == 0:
            new_g[k_].append(r)
        elif len(r) == 1:
            new_g[k_].append(r)
        elif len(r) == 2:
            new_g[k_].append(r)
        else:
            new_g[k_].append(r[:1] + [new_k(k, y, x+1)])
            remaining = r[1:]
            prod = (k, y, x+1, remaining)
            productions_to_process.append(prod)
    return new_g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us define a simple expression grammar to use as an example.

<!--
############
EXPR_GRAMMAR = {
    '<start>': [['<expr>']],
    '<expr>': [ ['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
    '<term>': [ ['<fact>', '*', '<term>'], ['<fact>', '/', '<term>'], ['<fact>']],
    '<fact>': [ ['<digits>'], ['(','<expr>',')']],
    '<digits>': [ ['<digit>','<digits>'], ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}
EXPR_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EXPR_GRAMMAR = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [ [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [ [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [ [&#x27;&lt;digits&gt;&#x27;], [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [ [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
EXPR_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We verify that our BNF converter works.

<!--
############
g, s = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
gatleast.display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, s = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is another, the grammar for JSON

<!--
############
JSON_GRAMMAR = {
        '<start>': [['<json>']],
        '<json>': [['<element>']],
        '<element>': [['<ws>', '<value>', '<ws>']],
        '<value>': [
           ['<object>'],
           ['<array>'],
           ['<string>'],
           ['<number>'],
           list('true'),
           list('false'),
           list('null')],
        '<object>': [
            ['{', '<ws>', '}'],
            ['{', '<members>', '}']],
        '<members>': [
            ['<member>'],
            ['<member>', ',', '<members>']
        ],
        '<member>': [
            ['<ws>', '<string>', '<ws>', ':', '<element>']],
        '<array>': [
            ['[', '<ws>', ']'],
            ['[', '<elements>', ']']],
        '<elements>': [
            ['<element>'],
            ['<element>', ',', '<elements>']
        ],
        '<string>': [
            ['"', '<characterz>', '"']],
        '<characterz>': [
                [],
                ['<character>', '<characterz>']],
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
        '<number>': [
            ['<int>', '<frac>', '<exp>']],
        '<int>': [
           ['<digit>'],
           ['<onenine>', '<digits>'],
           ['-', '<digits>'],
           ['-', '<onenine>', '<digits>']],
        '<digit>': [
            ['0'],
            ['<onenine>']],
        '<onenine>': [
            ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<frac>': [
            [],
            ['.', '<digits>']],
        '<exp>': [
                [],
                ['E', '<sign>', '<digits>'],
                ['e', '<sign>', '<digits>']],
        '<sign>': [[], ['+'], ['-']],
        '<ws>': [['<sp1>', '<ws>'], []],
        '<sp1>': [[' ']], ##[['\n'], ['\r'], ['\t'], ['\x08'], ['\x0c']],
        '<digits>': [
                ['<digit>'],
                ['<digit>', '<digits>']],
        '<escaped>': [
                ['\\u', '<hex>', '<hex>', '<hex>', '<hex>']],
        '<hex>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['A'], ['B'], ['C'], ['D'], ['E'],   ['F']]
}
JSON_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
JSON_GRAMMAR = {
        &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;json&gt;&#x27;]],
        &#x27;&lt;json&gt;&#x27;: [[&#x27;&lt;element&gt;&#x27;]],
        &#x27;&lt;element&gt;&#x27;: [[&#x27;&lt;ws&gt;&#x27;, &#x27;&lt;value&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;]],
        &#x27;&lt;value&gt;&#x27;: [
           [&#x27;&lt;object&gt;&#x27;],
           [&#x27;&lt;array&gt;&#x27;],
           [&#x27;&lt;string&gt;&#x27;],
           [&#x27;&lt;number&gt;&#x27;],
           list(&#x27;true&#x27;),
           list(&#x27;false&#x27;),
           list(&#x27;null&#x27;)],
        &#x27;&lt;object&gt;&#x27;: [
            [&#x27;{&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;}&#x27;],
            [&#x27;{&#x27;, &#x27;&lt;members&gt;&#x27;, &#x27;}&#x27;]],
        &#x27;&lt;members&gt;&#x27;: [
            [&#x27;&lt;member&gt;&#x27;],
            [&#x27;&lt;member&gt;&#x27;, &#x27;,&#x27;, &#x27;&lt;members&gt;&#x27;]
        ],
        &#x27;&lt;member&gt;&#x27;: [
            [&#x27;&lt;ws&gt;&#x27;, &#x27;&lt;string&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;element&gt;&#x27;]],
        &#x27;&lt;array&gt;&#x27;: [
            [&#x27;[&#x27;, &#x27;&lt;ws&gt;&#x27;, &#x27;]&#x27;],
            [&#x27;[&#x27;, &#x27;&lt;elements&gt;&#x27;, &#x27;]&#x27;]],
        &#x27;&lt;elements&gt;&#x27;: [
            [&#x27;&lt;element&gt;&#x27;],
            [&#x27;&lt;element&gt;&#x27;, &#x27;,&#x27;, &#x27;&lt;elements&gt;&#x27;]
        ],
        &#x27;&lt;string&gt;&#x27;: [
            [&#x27;&quot;&#x27;, &#x27;&lt;characterz&gt;&#x27;, &#x27;&quot;&#x27;]],
        &#x27;&lt;characterz&gt;&#x27;: [
                [],
                [&#x27;&lt;character&gt;&#x27;, &#x27;&lt;characterz&gt;&#x27;]],
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
        &#x27;&lt;number&gt;&#x27;: [
            [&#x27;&lt;int&gt;&#x27;, &#x27;&lt;frac&gt;&#x27;, &#x27;&lt;exp&gt;&#x27;]],
        &#x27;&lt;int&gt;&#x27;: [
           [&#x27;&lt;digit&gt;&#x27;],
           [&#x27;&lt;onenine&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;],
           [&#x27;-&#x27;, &#x27;&lt;digits&gt;&#x27;],
           [&#x27;-&#x27;, &#x27;&lt;onenine&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [
            [&#x27;0&#x27;],
            [&#x27;&lt;onenine&gt;&#x27;]],
        &#x27;&lt;onenine&gt;&#x27;: [
            [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;]],
        &#x27;&lt;frac&gt;&#x27;: [
            [],
            [&#x27;.&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;exp&gt;&#x27;: [
                [],
                [&#x27;E&#x27;, &#x27;&lt;sign&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;],
                [&#x27;e&#x27;, &#x27;&lt;sign&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;sign&gt;&#x27;: [[], [&#x27;+&#x27;], [&#x27;-&#x27;]],
        &#x27;&lt;ws&gt;&#x27;: [[&#x27;&lt;sp1&gt;&#x27;, &#x27;&lt;ws&gt;&#x27;], []],
        &#x27;&lt;sp1&gt;&#x27;: [[&#x27; &#x27;]], ##[[&#x27;\n&#x27;], [&#x27;\r&#x27;], [&#x27;\t&#x27;], [&#x27;\x08&#x27;], [&#x27;\x0c&#x27;]],
        &#x27;&lt;digits&gt;&#x27;: [
                [&#x27;&lt;digit&gt;&#x27;],
                [&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
        &#x27;&lt;escaped&gt;&#x27;: [
                [&#x27;\\u&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;, &#x27;&lt;hex&gt;&#x27;]],
        &#x27;&lt;hex&gt;&#x27;: [
            [&#x27;0&#x27;], [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;],
            [&#x27;a&#x27;], [&#x27;b&#x27;], [&#x27;c&#x27;], [&#x27;d&#x27;], [&#x27;e&#x27;], [&#x27;f&#x27;], [&#x27;A&#x27;], [&#x27;B&#x27;], [&#x27;C&#x27;], [&#x27;D&#x27;], [&#x27;E&#x27;],   [&#x27;F&#x27;]]
}
JSON_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We again verify that our BNF converter works.

<!--
############
g, s = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
gatleast.display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, s = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Triplet rules

As we discussed previously, we transform the grammar such that we produce
every variations of triplets with nonterminals from regular grammar starting
and ending, and nonterminal from context-free grammar in the middle.
That is, given this,

```
<S> := <A><B>
```
and given `<a>`, `<b>`, `<c>`, `<f>` as the regular nonterminals, each
reachable from previous, we produce

```
<a,S,a> := <a,A,a><a,B,a>
<a,S,b> := <a,A,a><a,B,b>
         | <a,A,b><b,B,b>
<a,S,c> := <a,A,a><a,B,c>
         | <a,A,a><c,B,c>
         | <a,A,c><c,B,c>
         | <a,A,b><b,B,c>
         | <a,A,b><c,B,c>
```
and so on.

<!--
############
def reachable_dict(g):
    gn = gatleast.reachable_dict(g)
    return {k:list(gn[k]) for k in gn}

def split_into_three(ks, kf, reaching):
    lst = []
    for k in ([ks] + reaching[ks]):
        if kf in reaching[k]:
            lst.append((ks, k, kf))
    return lst

def make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f):
    new_g1 = defaultdict(list)
    cf_reachable = reachable_dict(cf_g)
    r_reachable = reachable_dict(r_g)
    for cf_k in cf_g:
        for cf_r in cf_g[cf_k]:
            if len(cf_r) == 0:
                for r_k1 in r_g:
                    # what are reachable from r_k1 with exactly epsilon?
                    # itself!
                    r = [(r_k1, '', r_k1)]
                    new_g1[(r_k1, cf_k, r_k1)].append(r)
                    # or the final from the start.
                    if r_k1 == r_s:
                        if r_f in r_g[r_k1]:
                            r = [(r_k1, '', r_f)]
                            new_g1[(r_k1, cf_k, r_k1)].append(r)
            elif len(cf_r) == 1:
                cf_token =  cf_r[0]
                #assert fuzzer.is_terminal(cf_token) <- we also allow nonterminals
                if fuzzer.is_terminal(cf_token):
                    for r_k1 in r_g:
                        # things reachable from r_k1 with exactly cf_token -- there is just one in canonical RG.
                        for rule in r_g[r_k1]:
                            if not rule: continue
                            if rule[0] != cf_token: continue
                            r_k2 = rule[1]
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
                else:
                    for r_k1 in r_g:
                        for r_k2 in ([r_k1] + r_reachable[r_k1]):
                            # postpone checking cf_token
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
            elif len(cf_r) == 2:
                for r_k1 in r_g:
                    for r_k2 in ([r_k1] + r_reachable[r_k1]): # things reachable from r_k1
                        for a,b,c in split_into_three(r_k1, r_k2, r_reachable):
                            r = [(a, cf_r[0], b), (b, cf_r[1], c)]
                            new_g1[(a, cf_k, c)].append(r)
            else:
                assert False
    return new_g1, (r_s, cf_s, r_f)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def reachable_dict(g):
    gn = gatleast.reachable_dict(g)
    return {k:list(gn[k]) for k in gn}

def split_into_three(ks, kf, reaching):
    lst = []
    for k in ([ks] + reaching[ks]):
        if kf in reaching[k]:
            lst.append((ks, k, kf))
    return lst

def make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f):
    new_g1 = defaultdict(list)
    cf_reachable = reachable_dict(cf_g)
    r_reachable = reachable_dict(r_g)
    for cf_k in cf_g:
        for cf_r in cf_g[cf_k]:
            if len(cf_r) == 0:
                for r_k1 in r_g:
                    # what are reachable from r_k1 with exactly epsilon?
                    # itself!
                    r = [(r_k1, &#x27;&#x27;, r_k1)]
                    new_g1[(r_k1, cf_k, r_k1)].append(r)
                    # or the final from the start.
                    if r_k1 == r_s:
                        if r_f in r_g[r_k1]:
                            r = [(r_k1, &#x27;&#x27;, r_f)]
                            new_g1[(r_k1, cf_k, r_k1)].append(r)
            elif len(cf_r) == 1:
                cf_token =  cf_r[0]
                #assert fuzzer.is_terminal(cf_token) &lt;- we also allow nonterminals
                if fuzzer.is_terminal(cf_token):
                    for r_k1 in r_g:
                        # things reachable from r_k1 with exactly cf_token -- there is just one in canonical RG.
                        for rule in r_g[r_k1]:
                            if not rule: continue
                            if rule[0] != cf_token: continue
                            r_k2 = rule[1]
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
                else:
                    for r_k1 in r_g:
                        for r_k2 in ([r_k1] + r_reachable[r_k1]):
                            # postpone checking cf_token
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
            elif len(cf_r) == 2:
                for r_k1 in r_g:
                    for r_k2 in ([r_k1] + r_reachable[r_k1]): # things reachable from r_k1
                        for a,b,c in split_into_three(r_k1, r_k2, r_reachable):
                            r = [(a, cf_r[0], b), (b, cf_r[1], c)]
                            new_g1[(a, cf_k, c)].append(r)
            else:
                assert False
    return new_g1, (r_s, cf_s, r_f)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We modify our grammar display so that it knows about our triples.

<!--
############
class DisplayGrammar(gatleast.DisplayGrammar):
    def display_token(self, t):
         return repr(t) if self.is_nonterminal(t) else repr(t[1])

    def is_nonterminal(self, t):
        return fuzzer.is_nonterminal(t[1])

def display_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DisplayGrammar(gatleast.DisplayGrammar):
    def display_token(self, t):
         return repr(t) if self.is_nonterminal(t) else repr(t[1])

    def is_nonterminal(self, t):
        return fuzzer.is_nonterminal(t[1])

def display_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Remove invalid terminal transitions
Next, we remove invalid terminal transitions. That is, given

```
<s,A,a> := [<s>,a,<a>]
```
We check that `<s>` can reach `<a>` by consuming `a`. If not,
this is an invalid rule, and we remove it from the production rules.

<!--
############
def is_right_transition(a, terminal, b, r_g):
    assert fuzzer.is_terminal(terminal)
    start_a = [r for r in r_g[a] if r]
    with_terminal = [r for r in start_a if r[0] == terminal]
    ending_b = [r_rule[1] == b for r_rule in with_terminal]
    return any(ending_b)

def filter_terminal_transitions(g, r_g):
    new_g1 = defaultdict(list)
    for key in g:
        for rule in g[key]:
            if len(rule) == 1:
                a, t, b = rule[0]
                if len(t) == 0:
                    assert a == b
                    new_g1[key].append(rule)
                else:
                    terminals = [(a, t, b) for (a, t, b) in rule if fuzzer.is_terminal(t)]
                    if all(is_right_transition(a, t, b, r_g) for (a,t,b) in terminals): # all(empty) is true
                        new_g1[key].append(rule)
            else:
                terminals = [(a, t, b) for (a, t, b) in rule if fuzzer.is_terminal(t)]
                if all(is_right_transition(a, t, b, r_g) for (a,t,b) in terminals):
                    new_g1[key].append(rule)
    return new_g1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_right_transition(a, terminal, b, r_g):
    assert fuzzer.is_terminal(terminal)
    start_a = [r for r in r_g[a] if r]
    with_terminal = [r for r in start_a if r[0] == terminal]
    ending_b = [r_rule[1] == b for r_rule in with_terminal]
    return any(ending_b)

def filter_terminal_transitions(g, r_g):
    new_g1 = defaultdict(list)
    for key in g:
        for rule in g[key]:
            if len(rule) == 1:
                a, t, b = rule[0]
                if len(t) == 0:
                    assert a == b
                    new_g1[key].append(rule)
                else:
                    terminals = [(a, t, b) for (a, t, b) in rule if fuzzer.is_terminal(t)]
                    if all(is_right_transition(a, t, b, r_g) for (a,t,b) in terminals): # all(empty) is true
                        new_g1[key].append(rule)
            else:
                terminals = [(a, t, b) for (a, t, b) in rule if fuzzer.is_terminal(t)]
                if all(is_right_transition(a, t, b, r_g) for (a,t,b) in terminals):
                    new_g1[key].append(rule)
    return new_g1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Remove undefined nonterminals

At this point we may have multiple nonterminals with no rules defining them.
That is, such nonterminals can't be expanded. Hence, these can be removed.

<!--
############
def filter_rules_with_undefined_keys(g):
    cont = False
    new_g1 = defaultdict(list)
    for k in g:
        for r in g[k]:
            if len(r) == 0:
                new_g1[k].append(r)
            else:
                # only proceed if any nonterminal in the rule is defined.
                all_nts = [t for t in r if fuzzer.is_nonterminal(t[1])]
                if any(t not in g for t in all_nts): # if any undefined.
                    cont = True
                    pass
                else:
                    new_g1[k].append(r)
    return new_g1, cont

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def filter_rules_with_undefined_keys(g):
    cont = False
    new_g1 = defaultdict(list)
    for k in g:
        for r in g[k]:
            if len(r) == 0:
                new_g1[k].append(r)
            else:
                # only proceed if any nonterminal in the rule is defined.
                all_nts = [t for t in r if fuzzer.is_nonterminal(t[1])]
                if any(t not in g for t in all_nts): # if any undefined.
                    cont = True
                    pass
                else:
                    new_g1[k].append(r)
    return new_g1, cont
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Construct the full grammar
We are now ready to construct our full grammar.

<!--
############
def convert_key(k):
    p,k,q = k
    if fuzzer.is_nonterminal(k):
        return '<%s %s %s>' % (p[1:-1], k[1:-1], q[1:-1])
    else:
        return k

def intersect_cfg_and_rg(cf_g, cf_s, r_g, r_s, r_f=rxcanonical.NT_EMPTY):
    # first wrap every token in start and end states.
    new_g, new_s = make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f)

    # remove any (a, x, b) sequence where x is terminal, and a does not have a transition a x b
    new_g = filter_terminal_transitions(new_g, r_g)

    cont = True
    while cont:
        new_g1, cont = filter_rules_with_undefined_keys(new_g)
        # Now, remove any rule that refers to nonexistent keys.
        new_g = {k:new_g1[k] for k in new_g1 if new_g1[k]} # remove empty keys

    # convert keys to template
    new_g1 = {}
    for k in new_g:
        new_rs = []
        for r in new_g[k]:
            new_rs.append([convert_key(t) for t in r])
        new_g1[convert_key(k)] = new_rs

    new_g = new_g1
    return new_g, convert_key(new_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def convert_key(k):
    p,k,q = k
    if fuzzer.is_nonterminal(k):
        return &#x27;&lt;%s %s %s&gt;&#x27; % (p[1:-1], k[1:-1], q[1:-1])
    else:
        return k

def intersect_cfg_and_rg(cf_g, cf_s, r_g, r_s, r_f=rxcanonical.NT_EMPTY):
    # first wrap every token in start and end states.
    new_g, new_s = make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f)

    # remove any (a, x, b) sequence where x is terminal, and a does not have a transition a x b
    new_g = filter_terminal_transitions(new_g, r_g)

    cont = True
    while cont:
        new_g1, cont = filter_rules_with_undefined_keys(new_g)
        # Now, remove any rule that refers to nonexistent keys.
        new_g = {k:new_g1[k] for k in new_g1 if new_g1[k]} # remove empty keys

    # convert keys to template
    new_g1 = {}
    for k in new_g:
        new_rs = []
        for r in new_g[k]:
            new_rs.append([convert_key(t) for t in r])
        new_g1[convert_key(k)] = new_rs

    new_g = new_g1
    return new_g, convert_key(new_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see if our construction works.

<!--
############
expr_re = '[(]+[135]+[)]+'
rg, rs = rxcanonical.regexp_to_regular_grammar(expr_re)
rxcanonical.display_canonical_grammar(rg, rs)
string = '(11)'
re_start = '<^>'
rg[re_start] = [[rs]]
rp = earleyparser.EarleyParser(rg, parse_exceptions=False)
res = rp.recognize_on(string, re_start)
assert res
bg, bs = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
ing, ins = intersect_cfg_and_rg(bg, bs, rg, rs)
gatleast.display_grammar(ing, ins, -1)
inf = fuzzer.LimitFuzzer(ing)
for i in range(10):
    string = inf.iter_fuzz(ins, max_depth=5)
    res = rp.recognize_on(string, re_start)
    assert res
    print(string)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr_re = &#x27;[(]+[135]+[)]+&#x27;
rg, rs = rxcanonical.regexp_to_regular_grammar(expr_re)
rxcanonical.display_canonical_grammar(rg, rs)
string = &#x27;(11)&#x27;
re_start = &#x27;&lt;^&gt;&#x27;
rg[re_start] = [[rs]]
rp = earleyparser.EarleyParser(rg, parse_exceptions=False)
res = rp.recognize_on(string, re_start)
assert res
bg, bs = binary_normal_form(EXPR_GRAMMAR, EXPR_START)
ing, ins = intersect_cfg_and_rg(bg, bs, rg, rs)
gatleast.display_grammar(ing, ins, -1)
inf = fuzzer.LimitFuzzer(ing)
for i in range(10):
    string = inf.iter_fuzz(ins, max_depth=5)
    res = rp.recognize_on(string, re_start)
    assert res
    print(string)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-26-regular-grammar-expressions.py)

[^barhiller1961on]: Bar-Hiller, M. Perles, and E. Shamir. On formal properties of simple phrase structure grammars. Zeitschrift fur Phonetik Sprachwissenschaft und Kommunikationforshung, 14(2):143–172, 1961.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
