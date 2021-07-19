---
published: true
title: Error Correcting Earley Parser
layout: post
comments: true
tags: parsing, error correcting, context-free
categories: post
---

We talked about Earley parsers [previously](/post/2021/02/06/earley-parsing/).
One of the interesting things about Earley parsers is that it also forms the
basis of best known general context-free error correcting parser. A parser is
error correcting if it is able to parse corrupt inputs that only partially
conform to a given grammar. For example, given a JSON input such as

```
'[{"abc":[]'
```

The error correcting parser will be able to supply the input that is
necessary to make the input valid. In this case, it will supply `}]`.
The algorithm is minimal error correcting if the correction provided is
minimal in some sense. For example, if the correction is `, "":[]}]`, the
correction is not minimal.

The particular algorithm we will be examining is
the minimum distance error correcting parser by Aho et al.[^aho1972minimum].

There are two parts to this algorithm. The first is the idea of a
covering grammar that parses any corrupt input and the second is the
extraction of the best possible parse from the corresponding parse forest.

Aho et al. uses Earley parser for their error correcting parser. So, we will
follow in their foot steps.
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
import sys
if "pyodide" in sys.modules:
    import pyodide
    github_repo = 'https://raw.githubusercontent.com/'
    my_repo = 'rahulgopinath/rahulgopinath.github.io'
    earley_module_str = pyodide.open_url(github_repo + my_repo +
            '/master/notebooks/2021-02-06-earley-parsing.py')
    pyodide.eval_code(earley_module_str.getvalue(), globals())
else:
    # caution: this is a horrible temporary hack to load a local file with
    # hyphens, and make it available in the current namespace.
    # Dont use it in production.
    __vars__ = vars(__import__('2021-02-06-earley-parsing'))
    globals().update({k:__vars__[k] for k in __vars__ if k not in ['__name__']})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
if &quot;pyodide&quot; in sys.modules:
    import pyodide
    github_repo = &#x27;https://raw.githubusercontent.com/&#x27;
    my_repo = &#x27;rahulgopinath/rahulgopinath.github.io&#x27;
    earley_module_str = pyodide.open_url(github_repo + my_repo +
            &#x27;/master/notebooks/2021-02-06-earley-parsing.py&#x27;)
    pyodide.eval_code(earley_module_str.getvalue(), globals())
else:
    # caution: this is a horrible temporary hack to load a local file with
    # hyphens, and make it available in the current namespace.
    # Dont use it in production.
    __vars__ = vars(__import__(&#x27;2021-02-06-earley-parsing&#x27;))
    globals().update({k:__vars__[k] for k in __vars__ if k not in [&#x27;__name__&#x27;]})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Covering Grammar

The idea from Aho et al. is to first transform the given grammar into a
*covering grammar*. A grammar $$G_2$$ covers another grammar $$G_1$$ if
all productions in $$G_1$$ have a one to one correspondence to some production
in $$G_2$$, and a string that is parsed by $$G_1$$ is guaranteed to be parsed
by $$G_2$$, and all the parses from $$G_1$$ are guaranteed to exist in the set
of parses from $$G_2$$ (with the given homomorphism of productions).

So, we first construct a covering grammar that can handle any corruption of
input, with the additional property that there will be a parse of the corrupt
string which contains **the minimum number of modifications needed** such that
if they are applied on the string, it will make it parsed by the original
grammar.

### First, we load the prerequisites


<!--
############
import string
import random
import itertools as I

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
import random
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The following is our grammar and its start symbol.

<!--
############
grammar = {
    '<start>': [['<expr>']],
    '<expr>': [ ['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
    '<term>': [ ['<fact>', '*', '<term>'], ['<fact>', '/', '<term>'], ['<fact>']],
    '<fact>': [ ['<digits>'], ['(','<expr>',')']],
    '<digits>': [ ['<digit>','<digits>'], ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}
START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [ [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [ [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [ [&#x27;&lt;digits&gt;&#x27;], [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [ [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The grammar can be printed as follows.

<!--
############
def print_g(g, rmax=lambda x: len(x) > 3, nmax=100):
    stop = False
    for i, k in enumerate(g):
        if i > nmax:
            print('...')
            break
        print(k)
        srules = [' '.join([repr(k) for k in rule]) for rule in g[k]]
        lrules = [len(r) for r in srules if rmax(r)]
        if lrules:
            for srule in srules:
                print('|  ', srule)
        else:
            print('|  ','| '.join(srules))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def print_g(g, rmax=lambda x: len(x) &gt; 3, nmax=100):
    stop = False
    for i, k in enumerate(g):
        if i &gt; nmax:
            print(&#x27;...&#x27;)
            break
        print(k)
        srules = [&#x27; &#x27;.join([repr(k) for k in rule]) for rule in g[k]]
        lrules = [len(r) for r in srules if rmax(r)]
        if lrules:
            for srule in srules:
                print(&#x27;|  &#x27;, srule)
        else:
            print(&#x27;|  &#x27;,&#x27;| &#x27;.join(srules))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For example,

<!--
############
print_g(grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print_g(grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the (slightly simplified -- not all space characters are terminals) JSON grammar

<!--
############
json_grammar = {
    "<start>": [ ["<json>"] ],
    "<json>": [ ["<element>"] ],
    "<value>": [
        ["<object>"],
        ["<array>"],
        ["<string>"],
        ["<number>"],
        ["true"],
        ["false"],
        ["null"],
    ],
    "<object>": [
        ["{", "<ws>", "<members>", "<ws>", "}"],
        ["{", "<ws>", "}"]
        ],
    "<members>": [
        ["<member>", ",", "<members>"],
        ["<member>"]
    ],
    "<member>": [ ["<ws>", "<string>", "<ws>", ":", "<element>"] ],
    "<array>": [
        ["[", "<ws>", "]"],
        ["[", "<elements>", "]"],
    ],
    "<elements>": [ ["<element>", ",", "<elements>"], ["<element>"], ],
    "<element>": [ ["<ws>", "<value>", "<ws>"], ],
    "<string>": [ ["\"","<characters>","\""] ],
    "<characters>": [ ["<character>", "<characters>"], [] ],
    "<character>":  [[s] for s in string.printable if s not in {"\"", "\\"}] +
    [["\\", "<escape>"]],
    "<escape>": [[c] for c in '"\\/bfnrt"'] + [["u", "<hex>", "<hex>", "<hex>", "<hex>"]],
    "<hex>": [
        ["<digit>" ],
        ["a"], ["b"], ["c"], ["d"], ["e"], ["f"],
        ["A"], ["B"], ["C"], ["D"], ["E"], ["F"]
    ],
    "<number>": [ ["<integer>", "<fraction>", "<exponent>"] ],
    "<integer>": [
        ["<onenine>","<digits>"],
        ["<digit>"],
        ["-","<digit>"],
        ["-", "<onenine>","<digits>"],
    ],
    "<digits>": [ ["<digit>", "<digits>"], ["<digit>"], ],
    "<digit>": [ ["0"], ["<onenine>"], ],
    "<onenine>": [ ["1"],  ["2"],  ["3"],  ["4"],  ["5"], ["6"],  ["7"],  ["8"],  ["9"] ],
    "<fraction>": [ [".", "<digits>"], [] ],
    "<exponent>" :[ ["E", "<sign>", "<digits>"], ["e", "<sign>", "<digits>"], [] ],
    "<sign>": [ ["+"], ["-"], [] ],
    "<ws>": [ [" ", "<ws>"], [] ]
}

json_start = '<start>'


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
json_grammar = {
    &quot;&lt;start&gt;&quot;: [ [&quot;&lt;json&gt;&quot;] ],
    &quot;&lt;json&gt;&quot;: [ [&quot;&lt;element&gt;&quot;] ],
    &quot;&lt;value&gt;&quot;: [
        [&quot;&lt;object&gt;&quot;],
        [&quot;&lt;array&gt;&quot;],
        [&quot;&lt;string&gt;&quot;],
        [&quot;&lt;number&gt;&quot;],
        [&quot;true&quot;],
        [&quot;false&quot;],
        [&quot;null&quot;],
    ],
    &quot;&lt;object&gt;&quot;: [
        [&quot;{&quot;, &quot;&lt;ws&gt;&quot;, &quot;&lt;members&gt;&quot;, &quot;&lt;ws&gt;&quot;, &quot;}&quot;],
        [&quot;{&quot;, &quot;&lt;ws&gt;&quot;, &quot;}&quot;]
        ],
    &quot;&lt;members&gt;&quot;: [
        [&quot;&lt;member&gt;&quot;, &quot;,&quot;, &quot;&lt;members&gt;&quot;],
        [&quot;&lt;member&gt;&quot;]
    ],
    &quot;&lt;member&gt;&quot;: [ [&quot;&lt;ws&gt;&quot;, &quot;&lt;string&gt;&quot;, &quot;&lt;ws&gt;&quot;, &quot;:&quot;, &quot;&lt;element&gt;&quot;] ],
    &quot;&lt;array&gt;&quot;: [
        [&quot;[&quot;, &quot;&lt;ws&gt;&quot;, &quot;]&quot;],
        [&quot;[&quot;, &quot;&lt;elements&gt;&quot;, &quot;]&quot;],
    ],
    &quot;&lt;elements&gt;&quot;: [ [&quot;&lt;element&gt;&quot;, &quot;,&quot;, &quot;&lt;elements&gt;&quot;], [&quot;&lt;element&gt;&quot;], ],
    &quot;&lt;element&gt;&quot;: [ [&quot;&lt;ws&gt;&quot;, &quot;&lt;value&gt;&quot;, &quot;&lt;ws&gt;&quot;], ],
    &quot;&lt;string&gt;&quot;: [ [&quot;\&quot;&quot;,&quot;&lt;characters&gt;&quot;,&quot;\&quot;&quot;] ],
    &quot;&lt;characters&gt;&quot;: [ [&quot;&lt;character&gt;&quot;, &quot;&lt;characters&gt;&quot;], [] ],
    &quot;&lt;character&gt;&quot;:  [[s] for s in string.printable if s not in {&quot;\&quot;&quot;, &quot;\\&quot;}] +
    [[&quot;\\&quot;, &quot;&lt;escape&gt;&quot;]],
    &quot;&lt;escape&gt;&quot;: [[c] for c in &#x27;&quot;\\/bfnrt&quot;&#x27;] + [[&quot;u&quot;, &quot;&lt;hex&gt;&quot;, &quot;&lt;hex&gt;&quot;, &quot;&lt;hex&gt;&quot;, &quot;&lt;hex&gt;&quot;]],
    &quot;&lt;hex&gt;&quot;: [
        [&quot;&lt;digit&gt;&quot; ],
        [&quot;a&quot;], [&quot;b&quot;], [&quot;c&quot;], [&quot;d&quot;], [&quot;e&quot;], [&quot;f&quot;],
        [&quot;A&quot;], [&quot;B&quot;], [&quot;C&quot;], [&quot;D&quot;], [&quot;E&quot;], [&quot;F&quot;]
    ],
    &quot;&lt;number&gt;&quot;: [ [&quot;&lt;integer&gt;&quot;, &quot;&lt;fraction&gt;&quot;, &quot;&lt;exponent&gt;&quot;] ],
    &quot;&lt;integer&gt;&quot;: [
        [&quot;&lt;onenine&gt;&quot;,&quot;&lt;digits&gt;&quot;],
        [&quot;&lt;digit&gt;&quot;],
        [&quot;-&quot;,&quot;&lt;digit&gt;&quot;],
        [&quot;-&quot;, &quot;&lt;onenine&gt;&quot;,&quot;&lt;digits&gt;&quot;],
    ],
    &quot;&lt;digits&gt;&quot;: [ [&quot;&lt;digit&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;&lt;digit&gt;&quot;], ],
    &quot;&lt;digit&gt;&quot;: [ [&quot;0&quot;], [&quot;&lt;onenine&gt;&quot;], ],
    &quot;&lt;onenine&gt;&quot;: [ [&quot;1&quot;],  [&quot;2&quot;],  [&quot;3&quot;],  [&quot;4&quot;],  [&quot;5&quot;], [&quot;6&quot;],  [&quot;7&quot;],  [&quot;8&quot;],  [&quot;9&quot;] ],
    &quot;&lt;fraction&gt;&quot;: [ [&quot;.&quot;, &quot;&lt;digits&gt;&quot;], [] ],
    &quot;&lt;exponent&gt;&quot; :[ [&quot;E&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;e&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;], [] ],
    &quot;&lt;sign&gt;&quot;: [ [&quot;+&quot;], [&quot;-&quot;], [] ],
    &quot;&lt;ws&gt;&quot;: [ [&quot; &quot;, &quot;&lt;ws&gt;&quot;], [] ]
}

json_start = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, constructing a covering grammar proceeds as follows.
First, we take each terminal symbol in the given grammar. For example, the
below contains all terminal symbols from our `grammar`

<!--
############
Symbols = [t for k in grammar for alt in grammar[k] for t in alt if not is_nt(t)]
print(len(Symbols))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Symbols = [t for k in grammar for alt in grammar[k] for t in alt if not is_nt(t)]
print(len(Symbols))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we consider the following corruptions of the valid input:

* The input symbol being considered may have been deleted
* The input symbol being considered may have some junk value in front
* The input symbol may have been mistakenly written as something else.

A moment's reflection should convince you that a covering grammar only needs
to handle these three cases (In fact, only the first two cases are sufficient
but we add the third because it is also a _simple_ mutation).

The main idea is that we replace the given terminal symbol with an equivalent
nonterminal that lets you make these mistakes. So, we first define that
nonterminal that corresponds to each terminal symbol.

<!--
############
This_sym_str = '<$ [%s]>'

def This_sym(t):
    return  This_sym_str % t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
This_sym_str = &#x27;&lt;$ [%s]&gt;&#x27;

def This_sym(t):
    return  This_sym_str % t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
print(This_sym('a'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(This_sym(&#x27;a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define a convenience function that when given a rule, translates the
terminal symbols in that rule to the above nonterminal symbol.

<!--
############
def translate_terminal(t):
    if is_nt(t): return t
    return This_sym(t)

def translate_terminals(g):
    return {k:[[translate_terminal(t) for t in alt] for alt in g[k]] for k in g}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def translate_terminal(t):
    if is_nt(t): return t
    return This_sym(t)

def translate_terminals(g):
    return {k:[[translate_terminal(t) for t in alt] for alt in g[k]] for k in g}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
print_g(translate_terminals(grammar), lambda x: len(x) > 9)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print_g(translate_terminals(grammar), lambda x: len(x) &gt; 9)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
How are these nonterminals defined? Each nonterminal has the following
expansion rules

```
<$ [a]> -> a
         | <$.+> a
         | <$>
         | <$![a]>
```

That is, each nonterminal that corresponds to a terminal symbol has the
following expansions:

1. it matches the original terminal symbol
2. there is some junk before the terminal symbol. So, match and discard
that junk before matching the terminal symbol
-- `<$.+>` matches any number of any symbols. These are the corresponding
nonterminals names

<!--
############
Any_one = '<$.>'
Any_plus = '<$.+>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_one = &#x27;&lt;$.&gt;&#x27;
Any_plus = &#x27;&lt;$.+&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
3. the terminal symbol was deleted. So, skip this terminal symbol by matching
empty (`<$>`)

<!--
############
Empty = '<$>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Empty = &#x27;&lt;$&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
4. the input symbol was a mistake. That is, it matches any input symbol other
than the expected input symbol `a` -- `<$![a]>`. We have to define as many
nonterminals as there are terminal symbols again. So, we define a function.

<!--
############
Any_not_str = '<$![%s]>'
def Any_not(t): return Any_not_str % t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_not_str = &#x27;&lt;$![%s]&gt;&#x27;
def Any_not(t): return Any_not_str % t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Note:** It could be possible to completely remove `Any_not` by simply using
`Any_one` instead. The idea is that if Any_one matches a symbol, we apply a
single penalty, and if it matches the current symbol (thus becoming a NOP),
the use of this rule would be penalized, and hence not extracted. This will
reduce the grammar size overhead.

What happens if there is junk after parsing? We take care of that by wrapping
the start symbol as follows

```
<$corrupt_start> -> <start>
                  | <start> <$.+>
```

<!--
############
def corrupt_start(old_start):
    return '<@# %s>' % old_start[1:-1]

def new_start(old_start):
    return '<@ %s>' % old_start[1:-1]

def add_start(old_start):
    g_ = {}
    c_start = corrupt_start(old_start)
    g_[c_start] = [[old_start], [old_start, Any_plus]]
    return g_, c_start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def corrupt_start(old_start):
    return &#x27;&lt;@# %s&gt;&#x27; % old_start[1:-1]

def new_start(old_start):
    return &#x27;&lt;@ %s&gt;&#x27; % old_start[1:-1]

def add_start(old_start):
    g_ = {}
    c_start = corrupt_start(old_start)
    g_[c_start] = [[old_start], [old_start, Any_plus]]
    return g_, c_start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It is used as follows

<!--
############
g, c = add_start(START)
print(g)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, c = add_start(START)
print(g)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally we are ready to augment the original given grammar so that what we
have is a covering grammar. We first extract the symbols used, then produce
the nonterminal `Any_one` that correspond to any symbol match. Next,
we use `Any_not` to produce an any symbol except match. We then have a
`Empty` to match the absence of the nonterminal.

<!--
############
def augment_grammar(g, start, symbols=None):
    if symbols is None:
        symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[k] for k in symbols]}
    Match_any_sym_plus = {Any_plus: [[Any_one], [Any_plus, Any_one]]}


    Match_any_sym_except = {}
    for kk in symbols:
        Match_any_sym_except[Any_not(kk)] = [[k] for k in symbols if k != kk]
    Match_empty = {Empty: [[]]}

    Match_a_sym = {}
    for kk in symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(start)
    return {**start_g,
            **g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_any_sym_plus,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def augment_grammar(g, start, symbols=None):
    if symbols is None:
        symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[k] for k in symbols]}
    Match_any_sym_plus = {Any_plus: [[Any_one], [Any_plus, Any_one]]}


    Match_any_sym_except = {}
    for kk in symbols:
        Match_any_sym_except[Any_not(kk)] = [[k] for k in symbols if k != kk]
    Match_empty = {Empty: [[]]}

    Match_a_sym = {}
    for kk in symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(start)
    return {**start_g,
            **g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_any_sym_plus,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the augmented grammar

<!--
############
covering_grammar, covering_start = augment_grammar(grammar, START)
print_g(covering_grammar, lambda x: len(x) > 20)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar, covering_start = augment_grammar(grammar, START)
print_g(covering_grammar, lambda x: len(x) &gt; 20)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the augmented grammar for JSON

<!--
############
json_covering_grammar, json_covering_start = augment_grammar(json_grammar, json_start)
print_g(json_covering_grammar, lambda x: len(x) > 9)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
json_covering_grammar, json_covering_start = augment_grammar(json_grammar, json_start)
print_g(json_covering_grammar, lambda x: len(x) &gt; 9)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we are ready to check the covering properties of our grammar.

<!--
############
class SimpleExtractor:
    def __init__(self, parser, text, start_symbol):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol)
        starts = [s for s in states if s.finished()]
        if cursor < len(text) or not starts:
            raise SyntaxError("at " + repr(cursor))
        self.my_forest = parser.parse_forest(parser.table, starts)

    def extract_a_node(self, forest_node):
        name, paths = forest_node
        if not paths:
            return ((name, 0, 1), []), (name, [])
        cur_path, i, l = self.choose_path(paths)
        child_nodes = []
        pos_nodes = []
        for s, kind, chart in cur_path:
            f = self.parser.forest(s, kind, chart)
            postree, ntree = self.extract_a_node(f)
            child_nodes.append(ntree)
            pos_nodes.append(postree)

        return ((name, i, l), pos_nodes), (name, child_nodes)

    def choose_path(self, arr):
        l = len(arr)
        i = 0
        return arr[i], i, l

    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SimpleExtractor:
    def __init__(self, parser, text, start_symbol):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol)
        starts = [s for s in states if s.finished()]
        if cursor &lt; len(text) or not starts:
            raise SyntaxError(&quot;at &quot; + repr(cursor))
        self.my_forest = parser.parse_forest(parser.table, starts)

    def extract_a_node(self, forest_node):
        name, paths = forest_node
        if not paths:
            return ((name, 0, 1), []), (name, [])
        cur_path, i, l = self.choose_path(paths)
        child_nodes = []
        pos_nodes = []
        for s, kind, chart in cur_path:
            f = self.parser.forest(s, kind, chart)
            postree, ntree = self.extract_a_node(f)
            child_nodes.append(ntree)
            pos_nodes.append(postree)

        return ((name, i, l), pos_nodes), (name, child_nodes)

    def choose_path(self, arr):
        l = len(arr)
        i = 0
        return arr[i], i, l

    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a `tree_to_str_fix() that indicates the corrections produced.

<!--
############
def tree_to_str_fix(tree):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if is_nt(key):
            if key[:2] == '<$' and key[2] != ' ':
                # Empty Any_one Any_plus
                if key == Any_plus: # start
                    expanded.append('')
                elif key == Empty:
                    assert False
                    expanded.append('{del}')
                elif key.startswith(Any_not_str[0:4]): # <$![.]>
                    k = key[4]
                    expanded.append(k)
                else:
                    assert False
            elif key[:2] == '<$' and key[2] == ' ' and len(children) == 1 and children[0][0] == Empty:
                assert key[3] == '['
                assert key[5] == ']'
                expanded.append(key[4])
            else:
                to_expand = list(children) + list(to_expand)
        else:
            assert not children
            expanded.append(key)
    return ''.join(expanded)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def tree_to_str_fix(tree):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if is_nt(key):
            if key[:2] == &#x27;&lt;$&#x27; and key[2] != &#x27; &#x27;:
                # Empty Any_one Any_plus
                if key == Any_plus: # start
                    expanded.append(&#x27;&#x27;)
                elif key == Empty:
                    assert False
                    expanded.append(&#x27;{del}&#x27;)
                elif key.startswith(Any_not_str[0:4]): # &lt;$![.]&gt;
                    k = key[4]
                    expanded.append(k)
                else:
                    assert False
            elif key[:2] == &#x27;&lt;$&#x27; and key[2] == &#x27; &#x27; and len(children) == 1 and children[0][0] == Empty:
                assert key[3] == &#x27;[&#x27;
                assert key[5] == &#x27;]&#x27;
                expanded.append(key[4])
            else:
                to_expand = list(children) + list(to_expand)
        else:
            assert not children
            expanded.append(key)
    return &#x27;&#x27;.join(expanded)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a `tree_to_str_delta() that indicates the corrections produced.

<!--
############
def tree_to_str_delta(tree):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if is_nt(key):
            if key[:2] == '<$' and key[2] != ' ':
                # Empty Any_one Any_plus
                if key == Any_plus: # start
                    expanded.append('{s/%s//}' % repr(tree_to_str((key, children, *rest))))
                elif key == Empty:
                    assert False
                    expanded.append('{del}')
                elif key.startswith(Any_not_str[0:4]): # <$![.]>
                    k = key[4]
                    expanded.append('{s/%s/%s/}' % (repr(tree_to_str((key, children, *rest))), k))
                else:
                    assert False
            elif key[:2] == '<$' and key[2] == ' ' and len(children) == 1 and children[0][0] == Empty:
                expanded.append('{missing %s}' % repr(key[4:5]))
            else:
                to_expand = list(children) + list(to_expand)
        else:
            assert not children
            expanded.append(key)
    return ''.join(expanded)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def tree_to_str_delta(tree):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if is_nt(key):
            if key[:2] == &#x27;&lt;$&#x27; and key[2] != &#x27; &#x27;:
                # Empty Any_one Any_plus
                if key == Any_plus: # start
                    expanded.append(&#x27;{s/%s//}&#x27; % repr(tree_to_str((key, children, *rest))))
                elif key == Empty:
                    assert False
                    expanded.append(&#x27;{del}&#x27;)
                elif key.startswith(Any_not_str[0:4]): # &lt;$![.]&gt;
                    k = key[4]
                    expanded.append(&#x27;{s/%s/%s/}&#x27; % (repr(tree_to_str((key, children, *rest))), k))
                else:
                    assert False
            elif key[:2] == &#x27;&lt;$&#x27; and key[2] == &#x27; &#x27; and len(children) == 1 and children[0][0] == Empty:
                expanded.append(&#x27;{missing %s}&#x27; % repr(key[4:5]))
            else:
                to_expand = list(children) + list(to_expand)
        else:
            assert not children
            expanded.append(key)
    return &#x27;&#x27;.join(expanded)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
cstring = '1+1'
ie = SimpleExtractor(EarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = ie.extract_a_tree()
    print(format_parsetree(tree))
    print("string:", cstring, "unparsed:", tree_to_str_fix(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cstring = &#x27;1+1&#x27;
ie = SimpleExtractor(EarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = ie.extract_a_tree()
    print(format_parsetree(tree))
    print(&quot;string:&quot;, cstring, &quot;unparsed:&quot;, tree_to_str_fix(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, the covering grammar can *recognize* the input, but we have no
guarantee that it will only parse the input corresponding to the original
grammar.
What about an error?

<!--
############
cstring = '1+1+'
ie2 = SimpleExtractor(EarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = ie2.extract_a_tree()
    print(format_parsetree(tree))
    print("string:", cstring, "fixed:", tree_to_str_fix(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cstring = &#x27;1+1+&#x27;
ie2 = SimpleExtractor(EarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = ie2.extract_a_tree()
    print(format_parsetree(tree))
    print(&quot;string:&quot;, cstring, &quot;fixed:&quot;, tree_to_str_fix(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, we can parse corrupt inputs, but the inputs that we parse are
not necessarily the smallest. The next step is how to extract
the minimally corrupt parse.

## The minimally corrupt parse.

First, we need to modify the Earley parser so that it can keep track of the
penalties. We essentially assign a penalty if any of the following us used.

* Any use of <$.> : Any_one --- note, Any_plus gets +1 automatically
* Any use of <$>  : Empty
* Any use of <$ !{.}>  : Any_not

For getting this to work, we have to reengineer our nullable nonterminals,
keeping track of the corruptions introduced.

<!--
############
def nullable_ex(g):
    nullable_keys = {k:(1 if k == Empty else 0) for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys.keys())

    g_cur_ = rem_terminals(g)
    g_cur = {k:[(alt, 0) for alt in g_cur_[k]] for k in g_cur_}
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            if k in nullable_keys: continue
            g_alts = []
            for alt, penalty in g_cur[k]:
                # find the instances of nxt, then sum up the penalties
                # then update the penalties.
                penalty_ = len([t for t in alt if t == nxt]) * nullable_keys[nxt]
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys[k] = penalty + penalty_
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append((alt_, penalty + penalty_))
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def nullable_ex(g):
    nullable_keys = {k:(1 if k == Empty else 0) for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys.keys())

    g_cur_ = rem_terminals(g)
    g_cur = {k:[(alt, 0) for alt in g_cur_[k]] for k in g_cur_}
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            if k in nullable_keys: continue
            g_alts = []
            for alt, penalty in g_cur[k]:
                # find the instances of nxt, then sum up the penalties
                # then update the penalties.
                penalty_ = len([t for t in alt if t == nxt]) * nullable_keys[nxt]
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys[k] = penalty + penalty_
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append((alt_, penalty + penalty_))
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is how it is used

<!--
############
print(nullable_ex(grammar))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable_ex(grammar))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
covering grammar

<!--
############
print(nullable_ex(covering_grammar))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable_ex(covering_grammar))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 JSON covering grammar

<!--
############
print(nullable_ex(json_covering_grammar))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable_ex(json_covering_grammar))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we attach our nullable function to our parser.

<!--
############
class ErrorCorrectingEarleyParser(EarleyParser):
    def __init__(self, grammar, log = False, **kwargs):
        self._grammar = grammar
        self.epsilon = nullable_ex(grammar)
        self.log = log

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ErrorCorrectingEarleyParser(EarleyParser):
    def __init__(self, grammar, log = False, **kwargs):
        self._grammar = grammar
        self.epsilon = nullable_ex(grammar)
        self.log = log
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need to keep track of penalty. The first place is
in the `complete`, where we propagate a penalty to the parent
if the sate being completed resulted in a penalty

<!--
############
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        for st in parent_states:
            s = st.advance()
            s.penalty += state.penalty
            col.add(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        for st in parent_states:
            s = st.advance()
            s.penalty += state.penalty
            col.add(s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we also need to account for the fact that some of our
corrections are empty, which contains their own penalties.
So, we hook it up to `predict`.

<!--
############
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def predict(self, col, sym, state):
        for alt in self._grammar[sym]:
            col.add(self.create_state(sym, tuple(alt), 0, col))
        if sym in self.epsilon:
            s = state.advance()
            s.penalty += self.epsilon[sym]
            col.add(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def predict(self, col, sym, state):
        for alt in self._grammar[sym]:
            col.add(self.create_state(sym, tuple(alt), 0, col))
        if sym in self.epsilon:
            s = state.advance()
            s.penalty += self.epsilon[sym]
            col.add(s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
So, how do we hook up the penalty for corrections? We do that in
the penalized states as below. We also make sure that the
penalties are propagated.

<!--
############
class ECState(State):
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        if self.name ==  Empty:
            self.penalty = 1
        elif self.name == Any_one:
            self.penalty = 1
        elif self.name.startswith(Any_not_str[0:4]): # <$![.]>
            self.penalty = 1
        else:
            self.penalty = 0

    def copy(self):
        s = ECState(self.name, self.expr, self.dot, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

    def advance(self):
        s = ECState(self.name, self.expr, self.dot + 1, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ECState(State):
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        if self.name ==  Empty:
            self.penalty = 1
        elif self.name == Any_one:
            self.penalty = 1
        elif self.name.startswith(Any_not_str[0:4]): # &lt;$![.]&gt;
            self.penalty = 1
        else:
            self.penalty = 0

    def copy(self):
        s = ECState(self.name, self.expr, self.dot, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

    def advance(self):
        s = ECState(self.name, self.expr, self.dot + 1, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we come to adding a state to the column. If you remember from
the [earley parser](/post/2021/02/06/earley-parsing/) post, the uniqueness
check in the `add` prevents unbounded left recursion for nonterminals that
allow empty expansion.
There is one complication here. We need to keep track of the minimum penalty
that a state incurred. In particular, any time we find a less corrupt parse,
we need to use that penalty. Now, simply updating the penalty of the state
will not work because child states from the previous state with the higher
penalty also needs to be updated. So, to force the issue, we simply append
the new state to the columns state list. We can ignore that that current
state column state list contains a higher penalty state because at the end,
the forest builder looks for states with the lowest penalty.

<!--
############
class ECColumn(Column):
    def add(self, state):
        if state in self._unique:
            if self._unique[state].penalty > state.penalty:
                self._unique[state] = state
                self.states.append(state)
                state.e_col = self
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ECColumn(Column):
    def add(self, state):
        if state in self._unique:
            if self._unique[state].penalty &gt; state.penalty:
                self._unique[state] = state
                self.states.append(state)
                state.e_col = self
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need to hook up our new column and state to Earley parser.

<!--
############
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def create_column(self, i, tok):
        return ECColumn(i, tok)

    def create_state(self, sym, alt, num, col):
        return ECState(sym, alt, num, col)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def create_column(self, i, tok):
        return ECColumn(i, tok)

    def create_state(self, sym, alt, num, col):
        return ECState(sym, alt, num, col)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we hook up our simple extractor to choose the lowest cost path.

<!--
############
class SimpleExtractorEx(SimpleExtractor):
    def __init__(self, parser, text, start_symbol):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol)
        starts = [s for s in states if s.finished()]
        if cursor < len(text) or not starts:
            raise SyntaxError("at " + repr(cursor))
        for start in starts:
            print(start.expr, "correction length:", start.penalty)
        # now choose th smallest.
        my_starts = sorted(starts, key=lambda x: x.penalty)
        print('Choosing smallest penalty:', my_starts[0].penalty)
        self.my_forest = parser.parse_forest(parser.table, [my_starts[0]])

    def choose_path(self, arr):
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == 'n']
        return sum([s.penalty for s in states])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SimpleExtractorEx(SimpleExtractor):
    def __init__(self, parser, text, start_symbol):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol)
        starts = [s for s in states if s.finished()]
        if cursor &lt; len(text) or not starts:
            raise SyntaxError(&quot;at &quot; + repr(cursor))
        for start in starts:
            print(start.expr, &quot;correction length:&quot;, start.penalty)
        # now choose th smallest.
        my_starts = sorted(starts, key=lambda x: x.penalty)
        print(&#x27;Choosing smallest penalty:&#x27;, my_starts[0].penalty)
        self.my_forest = parser.parse_forest(parser.table, [my_starts[0]])

    def choose_path(self, arr):
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == &#x27;n&#x27;]
        return sum([s.penalty for s in states])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is how we use it.

<!--
############
cstring = '1+1+'
se = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = se.extract_a_tree()
    print(repr(cstring), "fixed:", repr(tree_to_str(tree)))
    print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cstring = &#x27;1+1+&#x27;
se = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar), cstring, covering_start)
for i in range(1):
    tree = se.extract_a_tree()
    print(repr(cstring), &quot;fixed:&quot;, repr(tree_to_str(tree)))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Caution, this command can take time. 10 seconds in Mac Book Pro.

<!--
############
All_ASCII = [i for i in string.printable if i not in '\n\r\t\x0b\x0c']
covering_grammar, covering_start = augment_grammar(grammar, START, symbols=All_ASCII)
ie4 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar), 'x+y', covering_start)
for i in range(1):
    tree = ie4.extract_a_tree()
    print(tree_to_str_fix(tree))
    print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
All_ASCII = [i for i in string.printable if i not in &#x27;\n\r\t\x0b\x0c&#x27;]
covering_grammar, covering_start = augment_grammar(grammar, START, symbols=All_ASCII)
ie4 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar), &#x27;x+y&#x27;, covering_start)
for i in range(1):
    tree = ie4.extract_a_tree()
    print(tree_to_str_fix(tree))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Why is this so slow? One reason is that, for conceptual clarity, and
generality, we opted to expand two terms from the original paper.
For example, we chose set Any_one: `<$.>` as well as
Any_not_str: `<$![.]>` as nonterminal symbols. This means that
to match `<$.>`, (say we have $$T$$ terminal symbols,) we have to carry
an extra $$T$$ symbols per each symbol -- essentially giving us $$T^2$$
extra matches to perform. For matching `<$![.]>`, the situation is worse,
we have to carry $$T^2$$ symbols per each terminal, giving $$T^3$$
matches per original terminal symbol.

Fortunately, there is an optimization possible here. We can set the
Any_one: `.` and Any_not(a): `!a` to be terminal symbols, and fix the
terminal match so that we match any character on `.` and except the given
character (e.g. `a`) on `!a`. What we lose there is generality. That is, the
augmented context-free grammar will no longer be usable by other parsers
(unless they are augmented got match regular expressions).
We modify our Earley parser to expect these. First our strings.

<!--
############
Any_term = '$.'

Any_not_term = '!%s'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_term = &#x27;$.&#x27;

Any_not_term = &#x27;!%s&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now our parser.

<!--
############
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def match_terminal(self, rex, input_term):
        if len(rex) > 1:
            if rex == Any_term: return True
            if rex[0] == Any_not_term[0]: return rex[1] != input_term # Any not
            return False
        else: return rex == input_term # normal

    def scan(self, col, state, letter):
        if self.match_terminal(letter, col.letter):
            my_expr = list(state.expr)
            if my_expr[state.dot] == '$.':
                my_expr[state.dot] = col.letter
            elif my_expr[state.dot][0] == '!' and len(my_expr[state.dot]) > 1:
                my_expr[state.dot] = col.letter
            else:
                assert my_expr[state.dot] == col.letter
            s = state.advance()
            s.expr = tuple(my_expr)
            col.add(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ErrorCorrectingEarleyParser(ErrorCorrectingEarleyParser):
    def match_terminal(self, rex, input_term):
        if len(rex) &gt; 1:
            if rex == Any_term: return True
            if rex[0] == Any_not_term[0]: return rex[1] != input_term # Any not
            return False
        else: return rex == input_term # normal

    def scan(self, col, state, letter):
        if self.match_terminal(letter, col.letter):
            my_expr = list(state.expr)
            if my_expr[state.dot] == &#x27;$.&#x27;:
                my_expr[state.dot] = col.letter
            elif my_expr[state.dot][0] == &#x27;!&#x27; and len(my_expr[state.dot]) &gt; 1:
                my_expr[state.dot] = col.letter
            else:
                assert my_expr[state.dot] == col.letter
            s = state.advance()
            s.expr = tuple(my_expr)
            col.add(s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Our grammars are augmented this way.

<!--
############
def augment_grammar_ex(g, start, symbols=None):
    if symbols is None:
        symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[Any_term]]}
    Match_any_sym_plus = {Any_plus: [[Any_one], [Any_plus, Any_one]]}


    Match_any_sym_except = {}
    for kk in symbols:
        Match_any_sym_except[Any_not(kk)] = [[Any_not_term % kk]]
    Match_empty = {Empty: [[]]}

    Match_a_sym = {}
    for kk in symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(start)
    return {**start_g,
            **g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_any_sym_plus,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def augment_grammar_ex(g, start, symbols=None):
    if symbols is None:
        symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[Any_term]]}
    Match_any_sym_plus = {Any_plus: [[Any_one], [Any_plus, Any_one]]}


    Match_any_sym_except = {}
    for kk in symbols:
        Match_any_sym_except[Any_not(kk)] = [[Any_not_term % kk]]
    Match_empty = {Empty: [[]]}

    Match_a_sym = {}
    for kk in symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(start)
    return {**start_g,
            **g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_any_sym_plus,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START)
print_g(covering_grammar_ex, lambda x: len(x) > 100)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START)
print_g(covering_grammar_ex, lambda x: len(x) &gt; 100)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing x+y

<!--
############
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar,
        START,
        symbols=[i for i in string.printable if i not in '\n\r\t\x0b\x0c'])
ie5 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_ex),
        'x+y',
        covering_start_ex)
for i in range(1):
    tree = ie5.extract_a_tree()
    print(tree_to_str_delta(tree))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar,
        START,
        symbols=[i for i in string.printable if i not in &#x27;\n\r\t\x0b\x0c&#x27;])
ie5 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_ex),
        &#x27;x+y&#x27;,
        covering_start_ex)
for i in range(1):
    tree = ie5.extract_a_tree()
    print(tree_to_str_delta(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing x+1

<!--
############
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar,
        START,
        symbols=[i for i in string.printable if i not in '\n\r\t\x0b\x0c'])
ie5 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_ex),
        'x+1',
        covering_start_ex)
for i in range(1):
    tree = ie5.extract_a_tree()
    print(tree_to_str_delta(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar,
        START,
        symbols=[i for i in string.printable if i not in &#x27;\n\r\t\x0b\x0c&#x27;])
ie5 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_ex),
        &#x27;x+1&#x27;,
        covering_start_ex)
for i in range(1):
    tree = ie5.extract_a_tree()
    print(tree_to_str_delta(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
cstring = '[{"abc":[]'
covering_grammar_json, covering_start_json = augment_grammar_ex(json_grammar, json_start)
ie6 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_json),
        cstring,
        covering_start_json)
print_g(covering_grammar_json, lambda x: len(x) > 100)
for i in range(1):
    tree = ie6.extract_a_tree()
    print(tree)
    print(format_parsetree(tree))
    print(repr(cstring), ":Fix:", repr(tree_to_str_fix(tree)))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cstring = &#x27;[{&quot;abc&quot;:[]&#x27;
covering_grammar_json, covering_start_json = augment_grammar_ex(json_grammar, json_start)
ie6 = SimpleExtractorEx(ErrorCorrectingEarleyParser(covering_grammar_json),
        cstring,
        covering_start_json)
print_g(covering_grammar_json, lambda x: len(x) &gt; 100)
for i in range(1):
    tree = ie6.extract_a_tree()
    print(tree)
    print(format_parsetree(tree))
    print(repr(cstring), &quot;:Fix:&quot;, repr(tree_to_str_fix(tree)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Note that the algorithm for recognition is $$O(n^3)$$. This is a consequence
of the fact that our covering grammar is simply a context-free grammar, and
as you can see, there is only a constant size increase in the grammar $$(|G|+ |T|^3)$$
where $$|G|$$ is the original size, and $$|T|$$ is the number of terminals.

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-02-22-error-correcting-earley-parsing.py).

[^aho1972minimum]: Alfred V. Aho and Thomas G. Peterson, A Minimum Distance Error-Correcting Parser for Context-Free Languages, SIAM Journal on Computing, 1972 <https://doi.org/10.1137/0201022>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
