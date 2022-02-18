---
published: true
title: Specializing Context-Free Grammars for Inducing Multiple Faults
layout: post
comments: true
tags: python
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

This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)

In my previous post on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
I explained the deficiency of abstract failure inducing inputs mined using
DDSet, and showed how to overcome that by inserting that abstract (evocative)
pattern into a grammar, producing evocative grammars that guarantee that the
evocative fragment is present in any input generated.
However, what if one wants to produce inputs that contain two evocative
fragments? or wants to produce inputs that are guaranteed to contain at least
one of them? This is what we will discuss in this post.

As before, let us start with importing our required modules.

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import itertools as I

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Producing inputs with two fault inducing fragments guaranteed to be present.
From the previous post [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
we extracted two evocative subtrees

<!--
############
import ddset
import hdd
print(ddset.abstract_tree_to_str(gatleast.ETREE_DPAREN))
ddset.display_abstract_tree(gatleast.ETREE_DPAREN)
print()
print(ddset.abstract_tree_to_str(gatleast.ETREE_DZERO))
ddset.display_abstract_tree(gatleast.ETREE_DZERO)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import ddset
import hdd
print(ddset.abstract_tree_to_str(gatleast.ETREE_DPAREN))
ddset.display_abstract_tree(gatleast.ETREE_DPAREN)
print()
print(ddset.abstract_tree_to_str(gatleast.ETREE_DZERO))
ddset.display_abstract_tree(gatleast.ETREE_DZERO)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now want to produce a grammar such that any input produced from that
grammar is guaranteed to contain both evocative subtrees. First, let us
extract the corresponding grammars. Here is the first one

<!--
############
g1, s1 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, 'D1'))
gatleast.display_grammar(g1, s1)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1, s1 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, &#x27;D1&#x27;))
gatleast.display_grammar(g1, s1)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We save this for later

<!--
############
EXPR_DPAREN_S = '<start D1>'
EXPR_DPAREN_G = {
        '<start>': [['<expr>']],
        '<expr>': [['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
        '<term>': [['<factor>', '*', '<term>'], ['<factor>', '/', '<term>'], ['<factor>']],
        '<factor>': [['+', '<factor>'], ['-', '<factor>'], ['(', '<expr>', ')'], ['<integer>', '.', '<integer>'], ['<integer>']],
        '<integer>': [['<digit>', '<integer>'], ['<digit>']],
        '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<factor D1_0>': [['(', '<expr D1_1>', ')']],
        '<expr D1_1>': [['<term D1_2>']],
        '<term D1_2>': [['<factor D1_3>']],
        '<factor D1_3>': [['(', '<expr>', ')']],
        '<start D1>': [['<expr D1>']],
        '<expr D1>': [['<term D1>', '+', '<expr>'], ['<term>', '+', '<expr D1>'], ['<term D1>', '-', '<expr>'], ['<term>', '-', '<expr D1>'], ['<term D1>']],
        '<term D1>': [['<factor D1>', '*', '<term>'], ['<factor>', '*', '<term D1>'], ['<factor D1>', '/', '<term>'], ['<factor>', '/', '<term D1>'], ['<factor D1>']],
        '<factor D1>': [['+', '<factor D1>'], ['-', '<factor D1>'], ['(', '<expr D1>', ')'], ['(', '<expr D1_1>', ')']]
}


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EXPR_DPAREN_S = &#x27;&lt;start D1&gt;&#x27;
EXPR_DPAREN_G = {
        &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
        &#x27;&lt;expr&gt;&#x27;: [[&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;]],
        &#x27;&lt;term&gt;&#x27;: [[&#x27;&lt;factor&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;]],
        &#x27;&lt;factor&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;factor&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;factor&gt;&#x27;], [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;], [&#x27;&lt;integer&gt;&#x27;, &#x27;.&#x27;, &#x27;&lt;integer&gt;&#x27;], [&#x27;&lt;integer&gt;&#x27;]],
        &#x27;&lt;integer&gt;&#x27;: [[&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;integer&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;]],
        &#x27;&lt;factor D1_0&gt;&#x27;: [[&#x27;(&#x27;, &#x27;&lt;expr D1_1&gt;&#x27;, &#x27;)&#x27;]],
        &#x27;&lt;expr D1_1&gt;&#x27;: [[&#x27;&lt;term D1_2&gt;&#x27;]],
        &#x27;&lt;term D1_2&gt;&#x27;: [[&#x27;&lt;factor D1_3&gt;&#x27;]],
        &#x27;&lt;factor D1_3&gt;&#x27;: [[&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;]],
        &#x27;&lt;start D1&gt;&#x27;: [[&#x27;&lt;expr D1&gt;&#x27;]],
        &#x27;&lt;expr D1&gt;&#x27;: [[&#x27;&lt;term D1&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr D1&gt;&#x27;], [&#x27;&lt;term D1&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr D1&gt;&#x27;], [&#x27;&lt;term D1&gt;&#x27;]],
        &#x27;&lt;term D1&gt;&#x27;: [[&#x27;&lt;factor D1&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term D1&gt;&#x27;], [&#x27;&lt;factor D1&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term D1&gt;&#x27;], [&#x27;&lt;factor D1&gt;&#x27;]],
        &#x27;&lt;factor D1&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;factor D1&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;factor D1&gt;&#x27;], [&#x27;(&#x27;, &#x27;&lt;expr D1&gt;&#x27;, &#x27;)&#x27;], [&#x27;(&#x27;, &#x27;&lt;expr D1_1&gt;&#x27;, &#x27;)&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the second grammar.

<!--
############
g2, s2 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, 'Z1'))
gatleast.display_grammar(g2, s2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2, s2 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, &#x27;Z1&#x27;))
gatleast.display_grammar(g2, s2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We save this for later

<!--
############
EXPR_DZERO_S = '<start Z1>'
EXPR_DZERO_G = {
        '<start>': [['<expr>']],
        '<expr>': [['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
        '<term>': [['<factor>', '*', '<term>'], ['<factor>', '/', '<term>'], ['<factor>']],
        '<factor>': [['+', '<factor>'], ['-', '<factor>'], ['(', '<expr>', ')'], ['<integer>', '.', '<integer>'], ['<integer>']],
        '<integer>': [['<digit>', '<integer>'], ['<digit>']],
        '<digit>': [['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<term Z1_0>': [['<factor>', '/', '<term Z1_1>']],
        '<term Z1_1>': [['<factor Z1_2>']],
        '<factor Z1_2>': [['<integer Z1_3>']],
        '<integer Z1_3>': [['<digit Z1_4>']],
        '<digit Z1_4>': [['0']],
        '<start Z1>': [['<expr Z1>']],
        '<expr Z1>': [['<term Z1>', '+', '<expr>'], ['<term>', '+', '<expr Z1>'], ['<term Z1>', '-', '<expr>'], ['<term>', '-', '<expr Z1>'], ['<term Z1>']],
        '<term Z1>': [['<factor Z1>', '*', '<term>'], ['<factor>', '*', '<term Z1>'], ['<factor Z1>', '/', '<term>'], ['<factor>', '/', '<term Z1>'], ['<factor Z1>'], ['<factor>', '/', '<term Z1_1>']],
        '<factor Z1>': [['+', '<factor Z1>'], ['-', '<factor Z1>'], ['(', '<expr Z1>', ')']]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EXPR_DZERO_S = &#x27;&lt;start Z1&gt;&#x27;
EXPR_DZERO_G = {
        &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
        &#x27;&lt;expr&gt;&#x27;: [[&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;]],
        &#x27;&lt;term&gt;&#x27;: [[&#x27;&lt;factor&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;]],
        &#x27;&lt;factor&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;factor&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;factor&gt;&#x27;], [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;], [&#x27;&lt;integer&gt;&#x27;, &#x27;.&#x27;, &#x27;&lt;integer&gt;&#x27;], [&#x27;&lt;integer&gt;&#x27;]],
        &#x27;&lt;integer&gt;&#x27;: [[&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;integer&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;1&#x27;], [&#x27;2&#x27;], [&#x27;3&#x27;], [&#x27;4&#x27;], [&#x27;5&#x27;], [&#x27;6&#x27;], [&#x27;7&#x27;], [&#x27;8&#x27;], [&#x27;9&#x27;]],
        &#x27;&lt;term Z1_0&gt;&#x27;: [[&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term Z1_1&gt;&#x27;]],
        &#x27;&lt;term Z1_1&gt;&#x27;: [[&#x27;&lt;factor Z1_2&gt;&#x27;]],
        &#x27;&lt;factor Z1_2&gt;&#x27;: [[&#x27;&lt;integer Z1_3&gt;&#x27;]],
        &#x27;&lt;integer Z1_3&gt;&#x27;: [[&#x27;&lt;digit Z1_4&gt;&#x27;]],
        &#x27;&lt;digit Z1_4&gt;&#x27;: [[&#x27;0&#x27;]],
        &#x27;&lt;start Z1&gt;&#x27;: [[&#x27;&lt;expr Z1&gt;&#x27;]],
        &#x27;&lt;expr Z1&gt;&#x27;: [[&#x27;&lt;term Z1&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr Z1&gt;&#x27;], [&#x27;&lt;term Z1&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr Z1&gt;&#x27;], [&#x27;&lt;term Z1&gt;&#x27;]],
        &#x27;&lt;term Z1&gt;&#x27;: [[&#x27;&lt;factor Z1&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term Z1&gt;&#x27;], [&#x27;&lt;factor Z1&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term Z1&gt;&#x27;], [&#x27;&lt;factor Z1&gt;&#x27;], [&#x27;&lt;factor&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term Z1_1&gt;&#x27;]],
        &#x27;&lt;factor Z1&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;factor Z1&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;factor Z1&gt;&#x27;], [&#x27;(&#x27;, &#x27;&lt;expr Z1&gt;&#x27;, &#x27;)&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## And Grammars
Now, we want to combine these grammars. Remember that a gramamr has a set of
definitions that correspond to nonterminals, and each definition has a set of
rules. We start from the rules. If we want to combine two grammars, we need
to make sure that any input produced from the combined grammar is also parsed
by the original grammars. That is, any rule from the combined grammar should
have a corresponding rule in the original grammars. This gives us the
algorithm for combining two rules. First, we can only combine rules that have
similar base representation. That is, if ruleA is `[<A f1>, <B f2>, 'T']` 
where `<A>` and `<B>` are nonterminals and `T` is a terminal
and ruleB is `[<A f1>, <C f3>]`, these can't have a combination in the
combined grammar. On the other hand, if ruleB is `[<A f3>, <B f4> 'T']`
then, a combined rule of `[<A f1 & f3>, <B f2 & f4>, 'T']` can infact
represent both parent rules. That is, when combining two rules from different,
grammars, their combination is empty if they have different base
representation.

The idea for combining two definitions of nonterminals is simply using the
distributive law. A definition is simply # `A1 or B1 or C1` where `A1` etc are
rules. Now, when you want to and two defintions, you have
`and(A1 or B1 or C1, A2 or B2 or C2)` , and you want the `or` out again.
So, this becomes
```
(A1 AND A2) OR (A1 AND B2) OR (A1 AND C2) OR
(A2 AND B1) OR (A2 AND C1) OR
(B1 AND B2) OR (B1 AND C2) OR
(B2 AND C1) OR (C1 AND C2)
```

which is essentially that many rules.
### Combining tokens
If they have the same base representation, then we only have to deal with how
to combine the nonterminal symbols. The terminal symbols are exactly the same
in parent rules as well as combined rule. So, given two tokens, we can
combine them as follows. The `and` of a refined nonterminal and a base
nonterminal is always the refined nonterminal. Otherwise, it is simply an
`and()` specialization of both refinements.

<!--
############
def and_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k2
    if not s2: return k1
    if s1 == s2: return k1
    return '<%s and(%s,%s)>' % (b1, s1, s2)

def and_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return and_nonterminals(t1, t2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k2
    if not s2: return k1
    if s1 == s2: return k1
    return &#x27;&lt;%s and(%s,%s)&gt;&#x27; % (b1, s1, s2)

def and_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return and_nonterminals(t1, t2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
print(and_tokens('C', 'C'))
print(and_tokens('<A>', '<A f1>'))
print(and_tokens('<A f2>', '<A f1>'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(and_tokens(&#x27;C&#x27;, &#x27;C&#x27;))
print(and_tokens(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;A f1&gt;&#x27;))
print(and_tokens(&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;A f1&gt;&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Combining rules
Next, we define combination for rules

<!--
############
def and_rules(ruleA, ruleB):
    AandB_rule = []
    for t1,t2 in zip(ruleA, ruleB):
        AandB_rule.append(and_tokens(t1, t2))
    return AandB_rule

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_rules(ruleA, ruleB):
    AandB_rule = []
    for t1,t2 in zip(ruleA, ruleB):
        AandB_rule.append(and_tokens(t1, t2))
    return AandB_rule
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
print(and_rules(['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']))
print(and_rules(['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))
print(and_rules(['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(and_rules([&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;C&#x27;]))
print(and_rules([&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]))
print(and_rules([&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Combining rulesets

Next, our grammars may contain multiple rules that represent the same base
rule. All the rules that represent the same base rule is called a ruleset.
combining two rulesets is done by producing a new ruleset that contains all
possible pairs of rules from the parent ruleset.


<!--
############
def and_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = and_rules(ruleA, ruleB)
        rules.append(AandB_rule)
    return rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = and_rules(ruleA, ruleB)
        rules.append(AandB_rule)
    return rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
A = [['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']]
B = [['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
C = [['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
for k in and_ruleset(A, B): print(k)
print()
for k in and_ruleset(A, C): print(k)
print()
for k in and_ruleset(B, C): print(k)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
A = [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;C&#x27;]]
B = [[&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]]
C = [[&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]]
for k in and_ruleset(A, B): print(k)
print()
for k in and_ruleset(A, C): print(k)
print()
for k in and_ruleset(B, C): print(k)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define a few helper functions that collects all rulesets

<!--
############
def normalize(key):
    if gatleast.is_base_key(key): return key
    return '<%s>' % gatleast.stem(key)

def normalize_grammar(g):
    return {normalize(k):list({tuple([normalize(t) if fuzzer.is_nonterminal(t) else t for t in r]) for r in g[k]}) for k in g}

def rule_to_normalized_rule(rule):
    return [normalize(t) if fuzzer.is_nonterminal(t) else t for t in rule]

def normalized_rule_match(r1, r2):
    return rule_to_normalized_rule(r1) == rule_to_normalized_rule(r2)

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA if not normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def get_rulesets(rules):
    rulesets = {}
    for rule in rules:
        nr = tuple(rule_to_normalized_rule(rule))
        if nr not in rulesets: rulesets[nr] = []
        rulesets[nr].append(rule)
    return rulesets

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def normalize(key):
    if gatleast.is_base_key(key): return key
    return &#x27;&lt;%s&gt;&#x27; % gatleast.stem(key)

def normalize_grammar(g):
    return {normalize(k):list({tuple([normalize(t) if fuzzer.is_nonterminal(t) else t for t in r]) for r in g[k]}) for k in g}

def rule_to_normalized_rule(rule):
    return [normalize(t) if fuzzer.is_nonterminal(t) else t for t in rule]

def normalized_rule_match(r1, r2):
    return rule_to_normalized_rule(r1) == rule_to_normalized_rule(r2)

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA if not normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def get_rulesets(rules):
    rulesets = {}
    for rule in rules:
        nr = tuple(rule_to_normalized_rule(rule))
        if nr not in rulesets: rulesets[nr] = []
        rulesets[nr].append(rule)
    return rulesets
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### definition conjunction
Now, we can define the conjunction of definitions as follows.

<!--
############
def and_definitions(rulesA, rulesB):
    AandB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) & set(rulesetsB.keys())
    for k in keys:
        new_rules = and_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_definitions(rulesA, rulesB):
    AandB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) &amp; set(rulesetsB.keys())
    for k in keys:
        new_rules = and_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
expr1 = [r for k in g1 if 'expr' in k for r in g1[k]]
expr2 = [r for k in g2 if 'expr' in k for r in g2[k]]
for k in and_definitions(expr1, expr2):
    print(k)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr1 = [r for k in g1 if &#x27;expr&#x27; in k for r in g1[k]]
expr2 = [r for k in g2 if &#x27;expr&#x27; in k for r in g2[k]]
for k in and_definitions(expr1, expr2):
    print(k)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### grammar conjunction
We can now define our grammar conjunction as follows.

<!--
############
def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    for k1,k2 in I.product(g1_keys, g2_keys):
        if normalize(k1) != normalize(k2): continue
        and_key = and_tokens(k1, k2)
        g[and_key] = and_definitions(g1[k1], g2[k2])
    return g, and_tokens(s1, s2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    for k1,k2 in I.product(g1_keys, g2_keys):
        if normalize(k1) != normalize(k2): continue
        and_key = and_tokens(k1, k2)
        g[and_key] = and_definitions(g1[k1], g2[k2])
    return g, and_tokens(s1, s2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
combined_g, combined_s = gatleast.grammar_gc(and_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(combined_g, combined_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
combined_g, combined_s = gatleast.grammar_gc(and_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(combined_g, combined_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed to produce instances of both characterizing
subtrees.

<!--
############
combined_f = fuzzer.LimitFuzzer(combined_g)
for i in range(10):
    v = combined_f.iter_fuzz(key=combined_s, max_depth=10)
    assert gatleast.expr_div_by_zero(v)
    assert hdd.expr_double_paren(v)
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
combined_f = fuzzer.LimitFuzzer(combined_g)
for i in range(10):
    v = combined_f.iter_fuzz(key=combined_s, max_depth=10)
    assert gatleast.expr_div_by_zero(v)
    assert hdd.expr_double_paren(v)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Producing inputs with at least one of the two fault inducing fragments guaranteed to be present.
How do we construct grammars that are guaranteed to contain at least one of
the evocative patterns? This is actually much less complicated than `and`
The idea is simply using the distributive law. A definition is simply
`A1 or B1 or C1` as before where `A1` etc are rules.
Now, when you want to `or` two definitions, you have
`or(A1 or B1 or C1, A2 or B2 or C2)`, then it simply becomes
`A1 or B1 or C1 or A2 or B2 or C2`
At this point, our work is essentially done. All that we need to do
is to merge any rules that potentially allow us to merge. However, this
is not compulsory.
### Nonterminals
For nonterminals, it is similar to `and` except that the base cases differ.
`or` of a base nonterminal with a refined nonterminal is always the base.

<!--
############
def or_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k1
    if not s2: return k2
    if s1 == s2: return k1
    return '<%s or(%s,%s)>' % (b1, s1, s2)

def or_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return or_nonterminals(t1, t2)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k1
    if not s2: return k2
    if s1 == s2: return k1
    return &#x27;&lt;%s or(%s,%s)&gt;&#x27; % (b1, s1, s2)

def or_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return or_nonterminals(t1, t2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## rules
What rules can be merged? Only those rules can be merged that has
a single refinement difference. That is if we have
`or(<A 1> <B 5> <C>, <A 2> <B 5> <C>)`, then this merges to
`<A or(1,2)><B 5><C>`. However `or(<A 1> <B 5> <C>, <A 2> <B 6> <C>)`
is not mergeable.

<!--
############
def or_rules(ruleA, ruleB):
    pos = []
    for i,(t1,t2) in enumerate(zip(ruleA, ruleB)):
        if t1 == t2: continue
        else: pos.append(i)
    if len(pos) == 0: return [ruleA]
    elif len(pos) == 1:
        return [[or_tokens(ruleA[i], ruleB[i]) if i == pos[0] else t
                for i,t in enumerate(ruleA)]]
    else: return [ruleA, ruleB]

if __name__ == '__main__':
    a1 = ['<A 1>', '<B>','<C>']
    a2 = ['<A 2>', '<B>','<C>']
    for r in or_rules(a1, a2): print(r)
    print()
    a3 = ['<A 1>', '<B 2>','<C>']
    a4 = ['<A 1>', '<B 3>','<C>']
    for r in or_rules(a3, a4): print(r)
    print()
    a5 = ['<A 1>', '<B 2>','<C 3>']
    a6 = ['<A 1>', '<B 3>','<C>']
    for r in or_rules(a5, a6): print(r)
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_rules(ruleA, ruleB):
    pos = []
    for i,(t1,t2) in enumerate(zip(ruleA, ruleB)):
        if t1 == t2: continue
        else: pos.append(i)
    if len(pos) == 0: return [ruleA]
    elif len(pos) == 1:
        return [[or_tokens(ruleA[i], ruleB[i]) if i == pos[0] else t
                for i,t in enumerate(ruleA)]]
    else: return [ruleA, ruleB]

if __name__ == &#x27;__main__&#x27;:
    a1 = [&#x27;&lt;A 1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;,&#x27;&lt;C&gt;&#x27;]
    a2 = [&#x27;&lt;A 2&gt;&#x27;, &#x27;&lt;B&gt;&#x27;,&#x27;&lt;C&gt;&#x27;]
    for r in or_rules(a1, a2): print(r)
    print()
    a3 = [&#x27;&lt;A 1&gt;&#x27;, &#x27;&lt;B 2&gt;&#x27;,&#x27;&lt;C&gt;&#x27;]
    a4 = [&#x27;&lt;A 1&gt;&#x27;, &#x27;&lt;B 3&gt;&#x27;,&#x27;&lt;C&gt;&#x27;]
    for r in or_rules(a3, a4): print(r)
    print()
    a5 = [&#x27;&lt;A 1&gt;&#x27;, &#x27;&lt;B 2&gt;&#x27;,&#x27;&lt;C 3&gt;&#x27;]
    a6 = [&#x27;&lt;A 1&gt;&#x27;, &#x27;&lt;B 3&gt;&#x27;,&#x27;&lt;C&gt;&#x27;]
    for r in or_rules(a5, a6): print(r)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## rulesets
For `or` rulesets we first combine
both rulesets together then (optional) take one at a time,
and check if it can be merged with another.

<!--
############
def or_ruleset(rulesetA, rulesetB):
    rule,*rules = (rulesetA + rulesetB)
    current_rules = [rule]
    while rules:
        rule,*rules = rules
        new_rules = []
        modified = False
        for i,r in enumerate(current_rules):
            v =  or_rules(r, rule)
            if len(v) == 1:
                current_rules[i] = v[0]
                rule = None
                break
            else:
                continue
        if rule is not None:
            current_rules.append(rule)
    return current_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_ruleset(rulesetA, rulesetB):
    rule,*rules = (rulesetA + rulesetB)
    current_rules = [rule]
    while rules:
        rule,*rules = rules
        new_rules = []
        modified = False
        for i,r in enumerate(current_rules):
            v =  or_rules(r, rule)
            if len(v) == 1:
                current_rules[i] = v[0]
                rule = None
                break
            else:
                continue
        if rule is not None:
            current_rules.append(rule)
    return current_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
A = [['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']]
B = [['<A>', '<B f2>', 'C'], ['<A f1>', '<B f3>', 'C']]
for k in or_ruleset(A, B): print(k)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
A = [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;C&#x27;]]
B = [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f2&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]]
for k in or_ruleset(A, B): print(k)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### definition disjunction
Now, we can define the disjunction of definitions as follows.

<!--
############
def or_definitions(rulesA, rulesB):
    AorB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    keys = set(rulesetsA.keys()) | set(rulesetsB.keys())
    for k in keys:
        new_rules = or_ruleset(rulesetsA.get(k, []), rulesetsB.get(k, []))
        AorB_rules.extend(new_rules)
    return AorB_rules

if __name__ == '__main__':
    expr1 = [r for k in g1 if 'expr' in k for r in g1[k]]
    expr2 = [r for k in g2 if 'expr' in k for r in g2[k]]
    for k in or_definitions(expr1, expr2):
        print(k)
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_definitions(rulesA, rulesB):
    AorB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    keys = set(rulesetsA.keys()) | set(rulesetsB.keys())
    for k in keys:
        new_rules = or_ruleset(rulesetsA.get(k, []), rulesetsB.get(k, []))
        AorB_rules.extend(new_rules)
    return AorB_rules

if __name__ == &#x27;__main__&#x27;:
    expr1 = [r for k in g1 if &#x27;expr&#x27; in k for r in g1[k]]
    expr2 = [r for k in g2 if &#x27;expr&#x27; in k for r in g2[k]]
    for k in or_definitions(expr1, expr2):
        print(k)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### grammar disjunction

<!--
############
def or_grammars_(g1, s1, g2, s2):
    g = {}
    # now get the matching keys for each pair.
    for k in list(g1.keys()) + list(g2.keys()):
         g[k] = [[t for t in r] for r in list(set([tuple(k) for k in (g1.get(k, []) + g2.get(k, []))]))]

    # We do not actually need to use merging of rule_sets for disjunction.
    s_or = or_nonterminals(s1, s2)
    g[s_or] = g1[s1] + g2[s2]
    return g, s_or


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_grammars_(g1, s1, g2, s2):
    g = {}
    # now get the matching keys for each pair.
    for k in list(g1.keys()) + list(g2.keys()):
         g[k] = [[t for t in r] for r in list(set([tuple(k) for k in (g1.get(k, []) + g2.get(k, []))]))]

    # We do not actually need to use merging of rule_sets for disjunction.
    s_or = or_nonterminals(s1, s2)
    g[s_or] = g1[s1] + g2[s2]
    return g, s_or
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
or_g, or_s = gatleast.grammar_gc(or_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(or_g, or_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
or_g, or_s = gatleast.grammar_gc(or_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(or_g, or_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed to produce at least one of the evocative subtrees
Using it.

<!--
############
or_f = fuzzer.LimitFuzzer(or_g)
for i in range(10):
    v = or_f.iter_fuzz(key=or_s, max_depth=10)
    assert (gatleast.expr_div_by_zero(v) or hdd.expr_double_paren(v))
    print(v)
    if gatleast.expr_div_by_zero(v) == hdd.PRes.success: print('>', 1)
    if hdd.expr_double_paren(v) == hdd.PRes.success: print('>',2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
or_f = fuzzer.LimitFuzzer(or_g)
for i in range(10):
    v = or_f.iter_fuzz(key=or_s, max_depth=10)
    assert (gatleast.expr_div_by_zero(v) or hdd.expr_double_paren(v))
    print(v)
    if gatleast.expr_div_by_zero(v) == hdd.PRes.success: print(&#x27;&gt;&#x27;, 1)
    if hdd.expr_double_paren(v) == hdd.PRes.success: print(&#x27;&gt;&#x27;,2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the runnable source of this notebook can be found [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-10-multiple-fault-grammars.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-10-multiple-fault-grammars.py).


The installable python wheel `gmultiplefaults` is available [here](/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl).

