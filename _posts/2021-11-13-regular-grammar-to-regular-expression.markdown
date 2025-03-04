---
published: true
title: Converting a Regular Grammar to a Regular Expression
layout: post
comments: true
tags: parsing
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
This post shows you how to convert a regular grammar to a regular expression
directly -- that is, without first creating an NFA or a DFA.
Converting a regular grammar to a regular expression is fairly easy
We only need to follow a fairly fixed set of rules.
 
1. First, we make sure that we have a start symbol, and a single symbol
   that represents the nonterminal in the grammar.
2. Next, we combine any production rules that end with the same nonterminal
   into a regular expression rule with a regular expression prefix, and the
   nonterminal suffix.
3. Next, we handle any self repetitions by using Kleene star expressions
4. Finally, we start removing nonterminals one by one until we are left with
   the regular expression that takes us from start to stop.
We start with importing the prerequisites

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
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">iFuzzing With Regular Expressions</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxregular-0.0.1-py2.py3-none-any.whl">rxregular-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/23/regular-expression-to-regular-grammar/">Regular Expression to Regular Grammar</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxcanonical-0.0.1-py2.py3-none-any.whl">rxcanonical-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/24/canonical-regular-grammar/">Converting a Regular Expression to DFA using Regular Grammar</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
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
import rxcanonical

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxcanonical
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a grammar for our use.

<!--
############
R_GRAMMAR = {"<S>": [["a", "<A>"]],
    "<A>" : [
        [rxcanonical.NT_EMPTY],
        ["b","<S>"],
        ["b","<A>"],
        ["a","<B>"],
    ],
    "<B>" : [
        ["b",rxcanonical.NT_EMPTY],
        ["a","<S>"]
    ],
    rxcanonical.NT_EMPTY : [[]]}
R_START = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
R_GRAMMAR = {&quot;&lt;S&gt;&quot;: [[&quot;a&quot;, &quot;&lt;A&gt;&quot;]],
    &quot;&lt;A&gt;&quot; : [
        [rxcanonical.NT_EMPTY],
        [&quot;b&quot;,&quot;&lt;S&gt;&quot;],
        [&quot;b&quot;,&quot;&lt;A&gt;&quot;],
        [&quot;a&quot;,&quot;&lt;B&gt;&quot;],
    ],
    &quot;&lt;B&gt;&quot; : [
        [&quot;b&quot;,rxcanonical.NT_EMPTY],
        [&quot;a&quot;,&quot;&lt;S&gt;&quot;]
    ],
    rxcanonical.NT_EMPTY : [[]]}
R_START = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Ensuring start and stop
The grammar should have one start symbol
and exactly one stop symbol which is NT_EMPTY
So, what we do is, whenever we have a rule that contains
just a terminal symbol, we append the NT_EMPTY symbol
to the rule. Thus NT_EMPTY symbol becomes the final
nontermainal to be expanded.

<!--
############
def fix_grammar(g, empty_nt=rxcanonical.NT_EMPTY):
    new_g = {}
    new_g[empty_nt] = [[]]
    for k in g:
        new_rules = []
        for rule in g[k]:
            if len(rule) == 1:
                if fuzzer.is_nonterminal(rule[0]):
                    assert rule[0] == empty_nt
                    new_rules.append(rule)
                else:
                    new_rules.append([rule[0], empty_nt])
            else:
                new_rules.append(rule)
        new_g[k] = new_rules
    return new_g

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def fix_grammar(g, empty_nt=rxcanonical.NT_EMPTY):
    new_g = {}
    new_g[empty_nt] = [[]]
    for k in g:
        new_rules = []
        for rule in g[k]:
            if len(rule) == 1:
                if fuzzer.is_nonterminal(rule[0]):
                    assert rule[0] == empty_nt
                    new_rules.append(rule)
                else:
                    new_rules.append([rule[0], empty_nt])
            else:
                new_rules.append(rule)
        new_g[k] = new_rules
    return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing it.

<!--
############
g = fix_grammar(R_GRAMMAR)
gatleast.display_grammar(g, R_START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = fix_grammar(R_GRAMMAR)
gatleast.display_grammar(g, R_START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define an `is_nonterminal` that knows about regular expressions.

<!--
############
def is_nonterminal(item):
    if not isinstance(item, str): return False
    return fuzzer.is_nonterminal(item)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_nonterminal(item):
    if not isinstance(item, str): return False
    return fuzzer.is_nonterminal(item)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, given a rule, we want to split it into a regex part and a nonterminal part.

<!--
############
def split_regex_prefix(rule):
    prefix = 0
    for token in rule:
        if is_nonterminal(token): break
        else: prefix += 1
    return rule[:prefix], rule[prefix:]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def split_regex_prefix(rule):
    prefix = 0
    for token in rule:
        if is_nonterminal(token): break
        else: prefix += 1
    return rule[:prefix], rule[prefix:]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Prefix Regex
Next, what we want to do is to consolidate rules that have same nonterminals
to a single rule with a regular expression prefix, and the nonterminal suffix.
That is:

```
convert <A> := a <B> | b <B> to (a|b) <B>
```

<!--
############
def produce_prefix_regex(rules, grammar, empty_nt=rxcanonical.NT_EMPTY):
    lnt_hash = {}
    has_epsilon = False
    has_emptykey = False
    for rule in rules:
        if rule == []:
            has_epsilon = True
            continue
        if rule == [empty_nt]:
            has_emptykey = True
            continue
        prefix, lnt = split_regex_prefix(rule)
        assert len(prefix) == 1
        knt = lnt[0]
        if knt not in lnt_hash: lnt_hash[knt] = []
        lnt_hash[knt].append(prefix[0])

    new_rules = []
    if has_epsilon: new_rules.append([])
    if has_emptykey: new_rules.append([empty_nt])

    for lnt in lnt_hash:
        if len(lnt_hash[lnt]) > 1:
            rex = ("or", *lnt_hash[lnt])
            new_rules.append([rex, lnt])
        else:
            rex = lnt_hash[lnt][0]
            new_rules.append([rex, lnt])
    return new_rules

def g_produce_prefix_regex(grammar):
    new_grammar = {}
    for k in grammar:
        new_rules = produce_prefix_regex(grammar[k], grammar)
        new_grammar[k] = new_rules
    return new_grammar

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def produce_prefix_regex(rules, grammar, empty_nt=rxcanonical.NT_EMPTY):
    lnt_hash = {}
    has_epsilon = False
    has_emptykey = False
    for rule in rules:
        if rule == []:
            has_epsilon = True
            continue
        if rule == [empty_nt]:
            has_emptykey = True
            continue
        prefix, lnt = split_regex_prefix(rule)
        assert len(prefix) == 1
        knt = lnt[0]
        if knt not in lnt_hash: lnt_hash[knt] = []
        lnt_hash[knt].append(prefix[0])

    new_rules = []
    if has_epsilon: new_rules.append([])
    if has_emptykey: new_rules.append([empty_nt])

    for lnt in lnt_hash:
        if len(lnt_hash[lnt]) &gt; 1:
            rex = (&quot;or&quot;, *lnt_hash[lnt])
            new_rules.append([rex, lnt])
        else:
            rex = lnt_hash[lnt][0]
            new_rules.append([rex, lnt])
    return new_rules

def g_produce_prefix_regex(grammar):
    new_grammar = {}
    for k in grammar:
        new_rules = produce_prefix_regex(grammar[k], grammar)
        new_grammar[k] = new_rules
    return new_grammar
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 Using it.

<!--
############
print()
rgrammar = fix_grammar(R_GRAMMAR)
new_rgrammar = g_produce_prefix_regex(rgrammar)
gatleast.display_grammar(new_rgrammar, R_START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
rgrammar = fix_grammar(R_GRAMMAR)
new_rgrammar = g_produce_prefix_regex(rgrammar)
gatleast.display_grammar(new_rgrammar, R_START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Recursion (Repetition)
When there is recursion, that is a rule contains a nonterminal
that is the same as the nonterminal we are defining, we need to
convert that to a kleene star, and add it in front of every other rule.
That is,
```
A -> b B
   | c C
   | a A
```
becomes

```
A -> a* b B
   | a* c C
```

<!--
############
def refine(rule):
    prefix, nts = split_regex_prefix(rule)
    if len(nts) == 1:
        return [("concat", *prefix), nts[0]]
    elif len(nts) == 0:
        return prefix
    else:
        assert False

def make_self_loops_to_star(rules, nt):
    recursive_rules = [r for r in rules if r and r[-1] == nt]
    if not recursive_rules: return rules
    assert len(recursive_rules) == 1
    r_rule = recursive_rules[0]
    assert r_rule[1] == nt
    new_rules = []
    for r in rules:
        if r == r_rule: continue
        nr = refine([("star", r_rule[0]), *r])
        new_rules.append(nr)
    return new_rules

def g_make_self_loops_to_star(g):
    new_g = {}
    for k in g:
        rules = make_self_loops_to_star(g[k], k)
        new_g[k] = rules
    return new_g

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def refine(rule):
    prefix, nts = split_regex_prefix(rule)
    if len(nts) == 1:
        return [(&quot;concat&quot;, *prefix), nts[0]]
    elif len(nts) == 0:
        return prefix
    else:
        assert False

def make_self_loops_to_star(rules, nt):
    recursive_rules = [r for r in rules if r and r[-1] == nt]
    if not recursive_rules: return rules
    assert len(recursive_rules) == 1
    r_rule = recursive_rules[0]
    assert r_rule[1] == nt
    new_rules = []
    for r in rules:
        if r == r_rule: continue
        nr = refine([(&quot;star&quot;, r_rule[0]), *r])
        new_rules.append(nr)
    return new_rules

def g_make_self_loops_to_star(g):
    new_g = {}
    for k in g:
        rules = make_self_loops_to_star(g[k], k)
        new_g[k] = rules
    return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 Using it.

<!--
############
print()
new_rgrammar2 = g_make_self_loops_to_star(new_rgrammar)
gatleast.display_grammar(new_rgrammar2, R_START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
new_rgrammar2 = g_make_self_loops_to_star(new_rgrammar)
gatleast.display_grammar(new_rgrammar2, R_START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we start eliminating nonterminals from the grammar one by one.
The idea is to choose a single nonterminal to be eliminated, and find where
it is being used. For each such rules, replace that rule with a set of rules
with the same prefix, and the rules of the nonterminal being eliminated as the
suffix. That is, given
```
A -> b B
  |  c D
B -> e E 
  |  f F
```
Eliminating B will result in

```
A -> b e E       # new
  |  b f F       # new
  |  c D
# B -> e E 
#  |  f F
```

<!--
############
def flatten_rule(rule, grammar, nt, empty_nt=rxcanonical.NT_EMPTY):
    # find the prefix without nonterminal
    prefix, nts = split_regex_prefix(rule)
    assert len(nts) <= 1
    if not nts: return [prefix]
    if nts[0] == nt: # recursion
        assert False
        return [rule]
    if nts[0] == empty_nt: # dont expand empty key
        return [rule]
    new_suffixes = grammar[nts[0]]
    return [refine(prefix+r) for r in new_suffixes]


def eliminate_nt(grammar, nt, empty_nt=rxcanonical.NT_EMPTY):
    new_g = {}
    for k in grammar:
        if k == nt: continue
        new_rules = []
        for r in grammar[k]:
            if len(r) == 0:
                # E -> \e
                assert k == empty_nt
                new_rules.append(r)
            elif len(r) == 1:
                # S -> E
                assert r[0] == empty_nt
                new_rules.append(r)
            elif len(r) == 2:
                if r[1] == nt:
                    rs = flatten_rule(r, grammar, k)
                    new_rules.extend(rs)
                else:
                    new_rules.append(r)
            else: assert False
        new_g[k] = new_rules
    return new_g


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def flatten_rule(rule, grammar, nt, empty_nt=rxcanonical.NT_EMPTY):
    # find the prefix without nonterminal
    prefix, nts = split_regex_prefix(rule)
    assert len(nts) &lt;= 1
    if not nts: return [prefix]
    if nts[0] == nt: # recursion
        assert False
        return [rule]
    if nts[0] == empty_nt: # dont expand empty key
        return [rule]
    new_suffixes = grammar[nts[0]]
    return [refine(prefix+r) for r in new_suffixes]


def eliminate_nt(grammar, nt, empty_nt=rxcanonical.NT_EMPTY):
    new_g = {}
    for k in grammar:
        if k == nt: continue
        new_rules = []
        for r in grammar[k]:
            if len(r) == 0:
                # E -&gt; \e
                assert k == empty_nt
                new_rules.append(r)
            elif len(r) == 1:
                # S -&gt; E
                assert r[0] == empty_nt
                new_rules.append(r)
            elif len(r) == 2:
                if r[1] == nt:
                    rs = flatten_rule(r, grammar, k)
                    new_rules.extend(rs)
                else:
                    new_rules.append(r)
            else: assert False
        new_g[k] = new_rules
    return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g = dict(new_rgrammar2)
new_g = eliminate_nt(g, '<A>')
gatleast.display_grammar(new_g, R_START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = dict(new_rgrammar2)
new_g = eliminate_nt(g, &#x27;&lt;A&gt;&#x27;)
gatleast.display_grammar(new_g, R_START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Regular grammar to regex

Eliminate each nonterminal one by one to get our expression.

<!--
############
def convert_rex(rex):
    if rex[0] == 'or':
        return '|'.join([convert_rex(r) for r in rex[1:]])
    elif rex[0] == 'concat':
        return ''.join([convert_rex(r) for r in rex[1:]])
    elif rex[0] == 'star':
        v = convert_rex(rex[1])
        if rex[1][0] not in ['concat', 'star', 'or']:
            return "%s*" % v
        return "(%s)*" % v
    else:
        return rex


def rg_to_regex(grammar, start_nt, empty_nt=rxcanonical.NT_EMPTY):
    fixedg = fix_grammar(grammar)
    new_rgrammar = g_produce_prefix_regex(fixedg)
    new_rgrammar2 = g_make_self_loops_to_star(new_rgrammar)

    keys = [k for k in grammar if k not in [start_nt, empty_nt]]

    g = dict(new_rgrammar2)
    for k in keys:
        g_ = eliminate_nt(g, k, empty_nt)
        g = g_
        g_ = g_produce_prefix_regex(g)
        g = g_
        g_ = g_make_self_loops_to_star(g)
        g = g_
        g_ = g_produce_prefix_regex(g)
        g = g_
    g_ = g_produce_prefix_regex(g)
    assert len(g_[start_nt]) == 1
    rex_rule = g_[start_nt][0]
    assert rex_rule[1] == empty_nt
    return convert_rex(rex_rule[0])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def convert_rex(rex):
    if rex[0] == &#x27;or&#x27;:
        return &#x27;|&#x27;.join([convert_rex(r) for r in rex[1:]])
    elif rex[0] == &#x27;concat&#x27;:
        return &#x27;&#x27;.join([convert_rex(r) for r in rex[1:]])
    elif rex[0] == &#x27;star&#x27;:
        v = convert_rex(rex[1])
        if rex[1][0] not in [&#x27;concat&#x27;, &#x27;star&#x27;, &#x27;or&#x27;]:
            return &quot;%s*&quot; % v
        return &quot;(%s)*&quot; % v
    else:
        return rex


def rg_to_regex(grammar, start_nt, empty_nt=rxcanonical.NT_EMPTY):
    fixedg = fix_grammar(grammar)
    new_rgrammar = g_produce_prefix_regex(fixedg)
    new_rgrammar2 = g_make_self_loops_to_star(new_rgrammar)

    keys = [k for k in grammar if k not in [start_nt, empty_nt]]

    g = dict(new_rgrammar2)
    for k in keys:
        g_ = eliminate_nt(g, k, empty_nt)
        g = g_
        g_ = g_produce_prefix_regex(g)
        g = g_
        g_ = g_make_self_loops_to_star(g)
        g = g_
        g_ = g_produce_prefix_regex(g)
        g = g_
    g_ = g_produce_prefix_regex(g)
    assert len(g_[start_nt]) == 1
    rex_rule = g_[start_nt][0]
    assert rex_rule[1] == empty_nt
    return convert_rex(rex_rule[0])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g = dict(R_GRAMMAR)
rx = rg_to_regex(g, R_START)
print(rx)
import re
rf = fuzzer.LimitFuzzer(R_GRAMMAR)
for i in range(10):
    v = rf.fuzz(R_START)
    assert re.match(rx, v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = dict(R_GRAMMAR)
rx = rg_to_regex(g, R_START)
print(rx)
import re
rf = fuzzer.LimitFuzzer(R_GRAMMAR)
for i in range(10):
    v = rf.fuzz(R_START)
    assert re.match(rx, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-11-13-regular-grammar-to-regular-expression.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-11-13-regular-grammar-to-regular-expression.py).


The installable python wheel `rgtorx` is available [here](/py/rgtorx-0.0.1-py2.py3-none-any.whl).

