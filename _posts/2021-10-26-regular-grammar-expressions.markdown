---
published: true
title: Conjunction, Disjunction, and Complement of Regular Grammars
layout: post
comments: true
tags: python
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

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
In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/)
I showed how to produce a grammar out of regular expressions. In the
second [post](/post/2021/10/23/regular-expression-to-regular-grammar/), I
claimed that we need a regular grammar because regular grammars have more
interesting properties such as being closed under
intersection and complement. Now, the question is how do we actually do
the intersection between two regular grammars? For this post, I assume that
the regular expressions are in the canonical format as given in
[this post](/post/2021/10/24/canonical-regular-grammar/).
That is, there are only two possible rule formats $$ A \rightarrow a B $$
and $$ A \rightarrow \epsilon $$. Further, the canonical format requires that
there is only one rule in a nonterminal definition that starts with a
particular terminal symbol. Refer to
[this post](/post/2021/10/24/canonical-regular-grammar/) for how convert any
regular grammar to the canonical format.
We start with importing the prerequisites

<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<ol>
<li>sympy</li>
</ol>
<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
sympy
</textarea>
</form>
</div>
</details>

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.

<ol>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/gfaultexpressions-0.0.1-py2.py3-none-any.whl">gfaultexpressions-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl">gmultiplefaults-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl">rxregular-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl">rxcanonical-0.0.1-py2.py3-none-any.whl</a></li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
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
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gfaultexpressions as gexpr
import earleyparser
import rxfuzzer
import rxregular
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
import rxregular
import rxcanonical
import sympy
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
There are only two patterns of rules in canonical regular grammars.
 
1. $$ A \rightarrow aB $$
2. $$ A \rightarrow \epsilon $$

The idea is that when evaluating intersection of the start symbol,
pair up all rules that start with the same terminal symbol.
Only the intersection of these would exist in the resulting grammar.
The intersection of
 
```
<A1> ::= a <B1>
```
 
and
```
<A2> ::= a <B2>
```
 
is simply
 
```
<and(A1,A2)> ::= a <and(B1,B2)>
```
 
For constructing such rules, we also need to parse the boolean expressions
in the nonterminals. So, we define our grammar first.

<!--
############
import string
BEXPR_GRAMMAR = {
    '<start>': [['<', '<bexpr>', '>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexprs>', ')'],
        ['<key>']],
    '<bexprs>' : [['<bexpr>', ',', '<bexprs>'], ['<bexpr>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<key>': [['<letters>'],[rxcanonical.NT_EMPTY[1:-1]]], # epsilon is <_>
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']
    ],
    '<letter>' : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
BEXPR_GRAMMAR = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;&#x27;, &#x27;&lt;bexpr&gt;&#x27;, &#x27;&gt;&#x27;]],
    &#x27;&lt;bexpr&gt;&#x27;: [
        [&#x27;&lt;bop&gt;&#x27;, &#x27;(&#x27;, &#x27;&lt;bexprs&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;key&gt;&#x27;]],
    &#x27;&lt;bexprs&gt;&#x27; : [[&#x27;&lt;bexpr&gt;&#x27;, &#x27;,&#x27;, &#x27;&lt;bexprs&gt;&#x27;], [&#x27;&lt;bexpr&gt;&#x27;]],
    &#x27;&lt;bop&gt;&#x27; : [list(&#x27;and&#x27;), list(&#x27;or&#x27;), list(&#x27;neg&#x27;)],
    &#x27;&lt;key&gt;&#x27;: [[&#x27;&lt;letters&gt;&#x27;],[rxcanonical.NT_EMPTY[1:-1]]], # epsilon is &lt;_&gt;
    &#x27;&lt;letters&gt;&#x27;: [
        [&#x27;&lt;letter&gt;&#x27;],
        [&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;letters&gt;&#x27;]
    ],
    &#x27;&lt;letter&gt;&#x27; : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define our expression class which is used to wrap boolean
expressions and extract components of boolean expressions.

<!--
############
class BExpr(gexpr.BExpr):
    def create_new(self, e): return BExpr(e)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][1]
        return bexpr

    def as_key(self):
        s = self.simple()
        return '<%s>' % s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(gexpr.BExpr):
    def create_new(self, e): return BExpr(e)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][1]
        return bexpr

    def as_key(self):
        s = self.simple()
        return &#x27;&lt;%s&gt;&#x27; % s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it can parse boolean expressions in nonterminals.

<!--
############
strings = [
        '<1>',
        '<and(1,2)>',
        '<or(1,2)>',
        '<and(1,or(2,3,1))>',
]
for s in strings:
    e = BExpr(s)
    print(e.as_key())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
strings = [
        &#x27;&lt;1&gt;&#x27;,
        &#x27;&lt;and(1,2)&gt;&#x27;,
        &#x27;&lt;or(1,2)&gt;&#x27;,
        &#x27;&lt;and(1,or(2,3,1))&gt;&#x27;,
]
for s in strings:
    e = BExpr(s)
    print(e.as_key())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Conjunction of two regular grammars

Next, we define the conjunction of two regular grammars in the canonical
format. We will define the conjunction of two definitions, and at the end
discuss how to stitch it together for the complete grammar. The nice thing
here is that, because our grammar is in the canonical format, conjunction
disjunction and negation is really simple, and follows roughly the same
framework.

### Conjunction of nonterminal symbols

<!--
############
def and_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<and(%s,%s)>' % (k1[1:-1], k2[1:-1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_nonterminals(k1, k2):
    if k1 == k2: return k1
    return &#x27;&lt;and(%s,%s)&gt;&#x27; % (k1[1:-1], k2[1:-1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = and_nonterminals('<A>', '<B>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = and_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Conjunction of rules

We only provide conjunction for those rules whose initial terminal symbols are
the same or it is an empty rule.

<!--
############
def and_rules(r1, r2):
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = and_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_rules(r1, r2):
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = and_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We check to make sure that conjunction of rules work.

<!--
############
k, r = and_rules([], [])
print(k, r)
k, r = and_rules(['a', '<A>'], ['a', '<B>'])
print(k, r)
k, r = and_rules(['a', '<A>'], ['a', '<A>'])
print(k, r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k, r = and_rules([], [])
print(k, r)
k, r = and_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;])
print(k, r)
k, r = and_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(k, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Conjunction of definitions

<!--
############
def get_leading_terminal(rule):
    if not rule: return ''
    return rule[0]

def and_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for terminal in paired1:
        if terminal not in paired2: continue
        new_key, intersected = and_rules(paired1[terminal], paired2[terminal])
        new_rules.append(intersected)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_leading_terminal(rule):
    if not rule: return &#x27;&#x27;
    return rule[0]

def and_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for terminal in paired1:
        if terminal not in paired2: continue
        new_key, intersected = and_rules(paired1[terminal], paired2[terminal])
        new_rules.append(intersected)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Checking that conjunction of definitions work.

<!--
############
g1, s1 = rxcanonical.canonical_regular_grammar({
     '<start1>' : [['a1', '<A1>']],
     '<A1>' : [['b1', '<B1>'], ['c1', '<C1>']],
     '<B1>' : [['c1','<C1>']],
     '<C1>' : [[]]
}, '<start1>')
g2, s2 = rxcanonical.canonical_regular_grammar({
     '<start2>' : [['a1', '<A2>']],
     '<A2>' : [['b1', '<B2>'], ['d1', '<C2>']],
     '<B2>' : [['c1','<C2>'], []],
     '<C2>' : [[]]
}, '<start2>')

rules = and_definitions(g1['<start1>'], g2['<start2>'])
print(rules)
rules = and_definitions(g1['<A1>'], g2['<A2>'])
print(rules)
rules = and_definitions(g1['<B1>'], g2['<B2>'])
print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1, s1 = rxcanonical.canonical_regular_grammar({
     &#x27;&lt;start1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A1&gt;&#x27;]],
     &#x27;&lt;A1&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B1&gt;&#x27;], [&#x27;c1&#x27;, &#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;B1&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;C1&gt;&#x27; : [[]]
}, &#x27;&lt;start1&gt;&#x27;)
g2, s2 = rxcanonical.canonical_regular_grammar({
     &#x27;&lt;start2&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A2&gt;&#x27;]],
     &#x27;&lt;A2&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;d1&#x27;, &#x27;&lt;C2&gt;&#x27;]],
     &#x27;&lt;B2&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C2&gt;&#x27;], []],
     &#x27;&lt;C2&gt;&#x27; : [[]]
}, &#x27;&lt;start2&gt;&#x27;)

rules = and_definitions(g1[&#x27;&lt;start1&gt;&#x27;], g2[&#x27;&lt;start2&gt;&#x27;])
print(rules)
rules = and_definitions(g1[&#x27;&lt;A1&gt;&#x27;], g2[&#x27;&lt;A2&gt;&#x27;])
print(rules)
rules = and_definitions(g1[&#x27;&lt;B1&gt;&#x27;], g2[&#x27;&lt;B2&gt;&#x27;])
print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Disjunction of two regular grammars

For disjunction, the strategy is the same. We line up rules in both
definitions with same starting symbol, then construct the conjunction of the
nonterminal parts. Unlike conjunction, however, we do not throw away the rules
without partners in the other definition. Instead, they are added to the
resulting definition.
### Disjunction of nonterminal symbols

<!--
############
def or_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<or(%s,%s)>' % (k1[1:-1], k2[1:-1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_nonterminals(k1, k2):
    if k1 == k2: return k1
    return &#x27;&lt;or(%s,%s)&gt;&#x27; % (k1[1:-1], k2[1:-1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = or_nonterminals('<A>', '<B>')
print(k)
k = or_nonterminals('<A>', '<A>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = or_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;)
print(k)
k = or_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;A&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Disjunction of rules

We assume that the starting terminal symbol is the same for both rules.

<!--
############
def or_rules(r1, r2):
    # the initial chars are the same
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = or_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_rules(r1, r2):
    # the initial chars are the same
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = or_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We check to make sure that disjunction for rules work.

<!--
############
k, r = or_rules([], [])
print(k, r)
k, r = or_rules(['a', '<A>'], ['a', '<B>'])
print(k, r)
k, r = or_rules(['a', '<A>'], ['a', '<A>'])
print(k, r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k, r = or_rules([], [])
print(k, r)
k, r = or_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;])
print(k, r)
k, r = or_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(k, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Disjunction of definitions

<!--
############
def or_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    new_rules = []
    new_keys = []
    p0 = [c for c in paired1 if c in paired2]
    p1 = [c for c in paired1 if c not in paired2]
    p2 = [c for c in paired2 if c not in paired1]
    for terminal in p0:
        new_key, kunion = or_rules(paired1[terminal], paired2[terminal])
        new_rules.append(kunion)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules + [paired1[c] for c in p1] + [paired2[c] for c in p2]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    new_rules = []
    new_keys = []
    p0 = [c for c in paired1 if c in paired2]
    p1 = [c for c in paired1 if c not in paired2]
    p2 = [c for c in paired2 if c not in paired1]
    for terminal in p0:
        new_key, kunion = or_rules(paired1[terminal], paired2[terminal])
        new_rules.append(kunion)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules + [paired1[c] for c in p1] + [paired2[c] for c in p2]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We check that disjunction of definitions work.

<!--
############
g3, s3 = rxcanonical.canonical_regular_grammar({
     '<start3>' : [['a1', '<A3>']],
     '<A3>' : [['b1', '<B3>'], ['c1', '<C3>']],
     '<B3>' : [['c1','<C3>']],
     '<C3>' : [[]]
}, '<start3>')
g4, s4 = rxcanonical.canonical_regular_grammar({
     '<start4>' : [['a1', '<A4>']],
     '<A4>' : [['b1', '<B4>'], ['d1', '<C4>']],
     '<B4>' : [['c1','<C4>'], []],
     '<C4>' : [[]]
}, '<start4>')

rules = or_definitions(g3['<start3>'], g4['<start4>'])
print(rules)
rules = or_definitions(g3['<A3>'], g4['<A4>'])
print(rules)
rules = or_definitions(g3['<B3>'], g4['<B4>'])
print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g3, s3 = rxcanonical.canonical_regular_grammar({
     &#x27;&lt;start3&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A3&gt;&#x27;]],
     &#x27;&lt;A3&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B3&gt;&#x27;], [&#x27;c1&#x27;, &#x27;&lt;C3&gt;&#x27;]],
     &#x27;&lt;B3&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C3&gt;&#x27;]],
     &#x27;&lt;C3&gt;&#x27; : [[]]
}, &#x27;&lt;start3&gt;&#x27;)
g4, s4 = rxcanonical.canonical_regular_grammar({
     &#x27;&lt;start4&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A4&gt;&#x27;]],
     &#x27;&lt;A4&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B4&gt;&#x27;], [&#x27;d1&#x27;, &#x27;&lt;C4&gt;&#x27;]],
     &#x27;&lt;B4&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C4&gt;&#x27;], []],
     &#x27;&lt;C4&gt;&#x27; : [[]]
}, &#x27;&lt;start4&gt;&#x27;)

rules = or_definitions(g3[&#x27;&lt;start3&gt;&#x27;], g4[&#x27;&lt;start4&gt;&#x27;])
print(rules)
rules = or_definitions(g3[&#x27;&lt;A3&gt;&#x27;], g4[&#x27;&lt;A4&gt;&#x27;])
print(rules)
rules = or_definitions(g3[&#x27;&lt;B3&gt;&#x27;], g4[&#x27;&lt;B4&gt;&#x27;])
print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Complement of regular grammars

For complement, the idea is to treat each pattern separately. We take the
definition of each nonterminal separately.

1. If the nonterminal definition does not contain $$ \epsilon $$, we add `NT_EMPTY`
   to the resulting definition. If it contains, then we skip it.
2. We collect all terminal symbols that start up a rule in the definition.
   For each such rule, we add a rule that complements the nonterminal used.
   That is, given 
 
```
<A>  :=  a <B>
```

   We produce

```
<neg(A)>  :=  a <neg(B)>
```
   as one of the complement rules.

3. For every remaining terminal in the `TERMINAL_SYMBOLS`, we add a match for
   any string given by `NT_ALL_STAR` (`<.*>`).


We start by producing the complement of a single nonterminal symbol.

<!--
############
def negate_nonterminal(k): return '<neg(%s)>' % k[1:-1]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_nonterminal(k): return &#x27;&lt;neg(%s)&gt;&#x27; % k[1:-1]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = negate_nonterminal('<A>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = negate_nonterminal(&#x27;&lt;A&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Complement of a single rule

<!--
############
def negate_key_in_rule(rule):
    if len(rule) == 0: return None
    assert len(rule) != 1
    assert fuzzer.is_terminal(rule[0])
    assert fuzzer.is_nonterminal(rule[1])
    return [rule[0], negate_nonterminal(rule[1])]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_key_in_rule(rule):
    if len(rule) == 0: return None
    assert len(rule) != 1
    assert fuzzer.is_terminal(rule[0])
    assert fuzzer.is_nonterminal(rule[1])
    return [rule[0], negate_nonterminal(rule[1])]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
r = negate_key_in_rule(['a', '<A>'])
print(r)
r = negate_key_in_rule([])
print(r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
r = negate_key_in_rule([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(r)
r = negate_key_in_rule([])
print(r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Complement a definition
 
We complement a definition by applying complement to each rule in the
original definition, and adding any new rules that did not match the
original definition.

<!--
############
def negate_definition(d1, terminal_symbols=rxcanonical.TERMINAL_SYMBOLS):
    paired = {get_leading_terminal(r):r for r in d1}
    remaining_chars = [c for c in terminal_symbols if c not in paired]
    rs1 = [[c, rxcanonical.NT_EMPTY] for c in remaining_chars]
    rs2 = [[c, rxcanonical.NT_ANY_PLUS] for c in remaining_chars]
    new_rules = rs1 + rs2

    # Now, we try to negate individual rules. It starts with the same
    # character, but matches the negative.
    for rule in d1:
        r = negate_key_in_rule(rule)
        if r is not None:
            new_rules.append(r)

    # should we add empty rule match or not?
    if [] not in d1:
        new_rules.append([])
    return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_definition(d1, terminal_symbols=rxcanonical.TERMINAL_SYMBOLS):
    paired = {get_leading_terminal(r):r for r in d1}
    remaining_chars = [c for c in terminal_symbols if c not in paired]
    rs1 = [[c, rxcanonical.NT_EMPTY] for c in remaining_chars]
    rs2 = [[c, rxcanonical.NT_ANY_PLUS] for c in remaining_chars]
    new_rules = rs1 + rs2

    # Now, we try to negate individual rules. It starts with the same
    # character, but matches the negative.
    for rule in d1:
        r = negate_key_in_rule(rule)
        if r is not None:
            new_rules.append(r)

    # should we add empty rule match or not?
    if [] not in d1:
        new_rules.append([])
    return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Checking complement of a definition in an example.

<!--
############
g4, s4 = rxcanonical.canonical_regular_grammar({
     '<start4>' : [['a', '<A4>']],
     '<A4>' : [['b', '<B4>'], ['c', '<C4>']],
     '<B4>' : [['c','<C4>']],
     '<C4>' : [[]]
}, '<start4>')

rules = negate_definition(g4['<start4>'])
print(rules)
rules = negate_definition(g4['<A4>'])
print(rules)
rules = negate_definition(g4['<B4>'])
print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g4, s4 = rxcanonical.canonical_regular_grammar({
     &#x27;&lt;start4&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A4&gt;&#x27;]],
     &#x27;&lt;A4&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;B4&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;C4&gt;&#x27;]],
     &#x27;&lt;B4&gt;&#x27; : [[&#x27;c&#x27;,&#x27;&lt;C4&gt;&#x27;]],
     &#x27;&lt;C4&gt;&#x27; : [[]]
}, &#x27;&lt;start4&gt;&#x27;)

rules = negate_definition(g4[&#x27;&lt;start4&gt;&#x27;])
print(rules)
rules = negate_definition(g4[&#x27;&lt;A4&gt;&#x27;])
print(rules)
rules = negate_definition(g4[&#x27;&lt;B4&gt;&#x27;])
print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Complete

Until now, we have only produced conjunction, disjunction, and complement for
definitions. When producing these, we have introduced new nonterminals in
definitions that are not yet defined. For producing a complete grammar, we
need to define these new nonterminals too. This is what we will do in this
section. We first define a few helper procedures.

The `remove_empty_defs()` recursively removes any nonterminal that has empty
definitions. That is, of the form `"<A>" : []`. Note that it is different from
an epsilon rule which is `"<A>" : [[]]`

<!--
############
def remove_empty_key_refs(grammar, ek):
    new_grammar = {}
    for k in grammar:
        if k == ek: continue
        new_rules = []
        for r in grammar[k]:
            if ek in r:
                continue
            new_rules.append(r)
        new_grammar[k] = new_rules
    return new_grammar

def remove_empty_defs(grammar, start):
    empty = [k for k in grammar if not grammar[k]]
    while empty:
        k, *empty = empty
        grammar = remove_empty_key_refs(grammar, k)
        empty = [k for k in grammar if not grammar[k]]
    return grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def remove_empty_key_refs(grammar, ek):
    new_grammar = {}
    for k in grammar:
        if k == ek: continue
        new_rules = []
        for r in grammar[k]:
            if ek in r:
                continue
            new_rules.append(r)
        new_grammar[k] = new_rules
    return new_grammar

def remove_empty_defs(grammar, start):
    empty = [k for k in grammar if not grammar[k]]
    while empty:
        k, *empty = empty
        grammar = remove_empty_key_refs(grammar, k)
        empty = [k for k in grammar if not grammar[k]]
    return grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define `complete()` which recursively computes the complex
nonterminals that is left undefined in a grammar from the simpler
nonterminal definitions.

<!--
############
def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, for any conjunction, disjunction, or negation of grammars, we start
at the start symbol, and produce the corresponding operation in the definition
of the start symbol. Then, we check if any new new nonterminal was used in any
of the rules. If any were used, we recursively define them using the
nonterminals already present in the grammar. This is very similar to the
`ReconstructRules` from [fault expressions](/post/2021/09/11/fault-expressions/)
for context-free grammars, but is also different enough. Hence, we define a
completely new class.

<!--
############
class ReconstructRules:
    def __init__(self, grammar, all_terminal_symbols=rxcanonical.TERMINAL_SYMBOLS):
        self.grammar = grammar
        self.all_terminal_symbols = all_terminal_symbols

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules:
    def __init__(self, grammar, all_terminal_symbols=rxcanonical.TERMINAL_SYMBOLS):
        self.grammar = grammar
        self.all_terminal_symbols = all_terminal_symbols
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We start with reconstructing a single key. For example, given the two grammars
`G1` and `G2`, and their start symbols `S1`, and `S2`, to compute an intersection
of `G1 & G2`, we simply reconstruct `<and(S1,S2)>` from the two grammars, and
recursively define any undefined nonterminals.

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            key_to_reconstruct, *keys = keys
            if log: print('reconstructing:', key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception('Key found:', key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            assert bexpr.simple()
            d, s = self.reconstruct_rules_from_bexpr(bexpr)
            if log: print('simplified_to:', s)
            self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            key_to_reconstruct, *keys = keys
            if log: print(&#x27;reconstructing:&#x27;, key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception(&#x27;Key found:&#x27;, key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            assert bexpr.simple()
            d, s = self.reconstruct_rules_from_bexpr(bexpr)
            if log: print(&#x27;simplified_to:&#x27;, s)
            self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given a complex boolean expression, construct the definition for it from the
grammar rules.

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_rules_from_bexpr(self, bexpr):
        f_key = bexpr.as_key()
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == 'and':
                return self.reconstruct_and_bexpr(bexpr)
            elif operator == 'or':
                return self.reconstruct_or_bexpr(bexpr)
            elif operator == 'neg':
                return self.reconstruct_neg_bexpr(bexpr)
            else:
                assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_rules_from_bexpr(self, bexpr):
        f_key = bexpr.as_key()
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == &#x27;and&#x27;:
                return self.reconstruct_and_bexpr(bexpr)
            elif operator == &#x27;or&#x27;:
                return self.reconstruct_or_bexpr(bexpr)
            elif operator == &#x27;neg&#x27;:
                return self.reconstruct_neg_bexpr(bexpr)
            else:
                assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Produce disjunction of grammars

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
g1 = {
        '<start1>' : [['0', '<A1>']],
        '<A1>' : [['a', '<B1>']],
        '<B1>' : [['b','<C1>'], ['c', '<D1>']],
        '<C1>' : [['c', '<D1>']],
        '<D1>' : [[]],
        }
s1 = '<start1>'
g2 = {
        '<start2>' : [['0', '<A2>']],
        '<A2>' : [['a', '<B2>'], ['b', '<D2>']],
        '<B2>' : [['b', '<D2>']],
        '<D2>' : [['c', '<E2>']],
        '<E2>' : [[]],
        }
s2 = '<start2>'
s1_s2 = or_nonterminals(s1, s2)
g, s = complete({**g1, **g2}, s1_s2, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
gp2 = earleyparser.EarleyParser(g2, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    r2 = gp2.recognize_on(v, s2)
    assert r1 or r2

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;D1&gt;&#x27; : [[]],
        }
s1 = &#x27;&lt;start1&gt;&#x27;
g2 = {
        &#x27;&lt;start2&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A2&gt;&#x27;]],
        &#x27;&lt;A2&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;B2&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;D2&gt;&#x27; : [[&#x27;c&#x27;, &#x27;&lt;E2&gt;&#x27;]],
        &#x27;&lt;E2&gt;&#x27; : [[]],
        }
s2 = &#x27;&lt;start2&gt;&#x27;
s1_s2 = or_nonterminals(s1, s2)
g, s = complete({**g1, **g2}, s1_s2, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
gp2 = earleyparser.EarleyParser(g2, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    r2 = gp2.recognize_on(v, s2)
    assert r1 or r2
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Produce conjunction  of grammars

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now verify that it works.

<!--
############
g1 = {
        '<start1>' : [['0', '<A1>']],
        '<A1>' : [['a', '<B1>']],
        '<B1>' : [['b','<C1>'], ['c', '<D1>']],
        '<C1>' : [['c', '<D1>']],
        '<D1>' : [[]],
        }
s1 = '<start1>'
g2 = {
        '<start2>' : [['0', '<A2>']],
        '<A2>' : [['a', '<B2>'], ['b', '<D2>']],
        '<B2>' : [['b', '<D2>']],
        '<D2>' : [['c', '<E2>']],
        '<E2>' : [[]],
        }
s2 = '<start2>'
s1_s2 = and_nonterminals(s1, s2)
g, s = complete({**g1, **g2}, s1_s2, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
gp2 = earleyparser.EarleyParser(g2, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    r2 = gp2.recognize_on(v, s2)
    assert r1 and r2

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;D1&gt;&#x27; : [[]],
        }
s1 = &#x27;&lt;start1&gt;&#x27;
g2 = {
        &#x27;&lt;start2&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A2&gt;&#x27;]],
        &#x27;&lt;A2&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;B2&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;D2&gt;&#x27; : [[&#x27;c&#x27;, &#x27;&lt;E2&gt;&#x27;]],
        &#x27;&lt;E2&gt;&#x27; : [[]],
        }
s2 = &#x27;&lt;start2&gt;&#x27;
s1_s2 = and_nonterminals(s1, s2)
g, s = complete({**g1, **g2}, s1_s2, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
gp2 = earleyparser.EarleyParser(g2, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    r2 = gp2.recognize_on(v, s2)
    assert r1 and r2
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we come to complement.

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_neg_bexpr(self, bexpr):
        fst = bexpr.op_fst()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        neg_rules = negate_definition(d1, self.all_terminal_symbols)
        return neg_rules, f_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_neg_bexpr(self, bexpr):
        fst = bexpr.op_fst()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        neg_rules = negate_definition(d1, self.all_terminal_symbols)
        return neg_rules, f_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that negation also works.

<!--
############
g1 = {
        '<start1>' : [['0', '<A1>']],
        '<A1>' : [['a', '<B1>']],
        '<B1>' : [['b','<C1>'], ['c', '<D1>']],
        '<C1>' : [['c', '<D1>']],
        '<D1>' : [['d', rxcanonical.NT_EMPTY]],
        }
s1 = '<start1>'
s1_ = negate_nonterminal(s1)
g, s = complete({**g1, **rxcanonical.G_EMPTY, **rxcanonical.G_ANY_PLUS}, s1_, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    assert not r1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;D1&gt;&#x27; : [[&#x27;d&#x27;, rxcanonical.NT_EMPTY]],
        }
s1 = &#x27;&lt;start1&gt;&#x27;
s1_ = negate_nonterminal(s1)
g, s = complete({**g1, **rxcanonical.G_EMPTY, **rxcanonical.G_ANY_PLUS}, s1_, True)
rxcanonical.display_canonical_grammar(g, s)

gf = fuzzer.LimitFuzzer(g)
gp = earleyparser.EarleyParser(g, parse_exceptions=False)
gp1 = earleyparser.EarleyParser(g1, parse_exceptions=False)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    r = gp.recognize_on(v, s)
    assert r
    r1 = gp1.recognize_on(v, s1)
    assert not r1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-26-regular-grammar-expressions.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
