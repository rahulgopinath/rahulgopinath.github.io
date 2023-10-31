---
published: true
title: Regular Expression to Regular Grammar
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
In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/), we
discussed how to produce a grammar out of regular expressions. This is
useful to make the regular expression a generator of matching inputs. However,
one detail is unsatisfying. The grammar produced is a context-free grammar.
Regular expressions actually correspond to regular grammars (which
are strictly less powerful than context-free grammars).
For reference, a context-free grammar is a grammar where the rules are of
the form $$ A \rightarrow \alpha $$ where $$A$$ is a single nonterminal symbol
and $$ \alpha $$ is any sequence of terminal or nonterminal symbols
including $$\epsilon$$ (empty).
A regular grammar on the other hand, is a grammar where the rules can take one
of the following forms:
* $$ A \rightarrow a $$
* $$ A \rightarrow a B $$
* $$ A \rightarrow \epsilon $$

where $$ A $$  and $$ B $$ are nonterminal symbols, $$ a $$ is a terminal
symbol, and $$ \epsilon $$ is the empty string.
So, why is producing a context-free grammar instead of regular grammar
unsatisfying? Because such regular grammars have more interesting properties
such as being closed under intersection and complement. By using a
context-free grammar, we miss out on such properties.
Hence, it would be really good if we could
translate the regular expression directly into a regular grammar. This is what
we will do in this post.
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
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">iFuzzing With Regular Expressions</a>".</li>
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
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import earleyparser
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxfuzzer
import itertools as I
import sympy

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import earleyparser
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxfuzzer
import itertools as I
import sympy
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We want to produce regular grammars directly from regular expressions.

 
## Union of Regular Grammars

Given two regular grammars such that their nonterminals do not overlap,
we need to produce a union grammar.
The idea is that you only need to modify the start symbol such that
the definition of the new start symbol is a combination of starts from both
grammars.

<!--
############
def key_intersection(g1, g2):
    return [k for k in g1 if k in g2]

def union_nonterminals(k, s): return '<or(%s,%s)>' % (k[1:-1], s[1:-1])

def union_grammars(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_s = union_nonterminals(s1, s2)
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def key_intersection(g1, g2):
    return [k for k in g1 if k in g2]

def union_nonterminals(k, s): return &#x27;&lt;or(%s,%s)&gt;&#x27; % (k[1:-1], s[1:-1])

def union_grammars(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_s = union_nonterminals(s1, s2)
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1 = 'a1(b1(c1)|b1)'
g1 = {
        '<start1>' : [['<A1>']],
        '<A1>' : [['a1', '<B1>']],
        '<B1>' : [['b1','<C1>'], ['b1']],
        '<C1>' : [['c1']]
        }
my_re2 = 'a2(b2)|a2'
g2 = {
        '<start2>' : [['<A2>']],
        '<A2>' : [['a2', '<B2>'], ['a2']],
        '<B2>' : [['b2']]
        }
g, s = union_grammars(g1, '<start1>', g2, '<start2>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1, v) or re.match(my_re2, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1 = &#x27;a1(b1(c1)|b1)&#x27;
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b1&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;b1&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;]]
        }
my_re2 = &#x27;a2(b2)|a2&#x27;
g2 = {
        &#x27;&lt;start2&gt;&#x27; : [[&#x27;&lt;A2&gt;&#x27;]],
        &#x27;&lt;A2&gt;&#x27; : [[&#x27;a2&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;a2&#x27;]],
        &#x27;&lt;B2&gt;&#x27; : [[&#x27;b2&#x27;]]
        }
g, s = union_grammars(g1, &#x27;&lt;start1&gt;&#x27;, g2, &#x27;&lt;start2&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1, v) or re.match(my_re2, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Concatenation of Regular Grammars

Next, given two regular grammars $$G1$$ and $$G2$$ such that
their nonterminals do not overlap, producing a concatenation grammar is as
follows: We collect all terminating rules from $$G1$$ which looks like
$$ A \rightarrow a $$ where
$$ a $$ is a terminal symbol. We then transform them to $$ A \rightarrow a S2 $$
where $$ S2 $$ is the start symbol of $$G2$$. If $$ \epsilon $$ was present in
one of the rules of $$G1$$, then we simply produce $$ A \rightarrow S2 $$.
 
We start with catenation of nonterminals.

<!--
############
def catenate_nonterminals(k, s): return '<%s.%s>' % (k[1:-1], s[1:-1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def catenate_nonterminals(k, s): return &#x27;&lt;%s.%s&gt;&#x27; % (k[1:-1], s[1:-1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define what happens when we catenate a nontrminal to a rule.
It returns any new keys created, along with the new rule

<!--
############
def catenate_rule_to_key(rule, s2):
    if len(rule) == 0: # epsilon
        return [], [s2]
    elif len(rule) == 1:
        if not fuzzer.is_nonterminal(rule[0]):
            return [], rule + [s2]
        else: # degenerate
            return [rule[0]], [catenate_nonterminals(rule[0], s2)]
    else:
        return [rule[1]], [rule[0], catenate_nonterminals(rule[1], s2)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def catenate_rule_to_key(rule, s2):
    if len(rule) == 0: # epsilon
        return [], [s2]
    elif len(rule) == 1:
        if not fuzzer.is_nonterminal(rule[0]):
            return [], rule + [s2]
        else: # degenerate
            return [rule[0]], [catenate_nonterminals(rule[0], s2)]
    else:
        return [rule[1]], [rule[0], catenate_nonterminals(rule[1], s2)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we define our regular catenation of two grammars.

<!--
############
def catenate_grammar(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_g = {}
    keys = [s1]
    seen_keys = set()

    while keys:
        k, *keys = keys
        if k in seen_keys: continue
        seen_keys.add(k)

        new_rules = []
        for r in g1[k]:
            uks, new_rule = catenate_rule_to_key(r, s2)
            new_rules.append(new_rule)
            keys.extend(uks)

        k_ = catenate_nonterminals(k, s2)
        new_g[k_] = new_rules
    ks = catenate_nonterminals(s1, s2)
    return {**g2, **new_g}, ks

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def catenate_grammar(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_g = {}
    keys = [s1]
    seen_keys = set()

    while keys:
        k, *keys = keys
        if k in seen_keys: continue
        seen_keys.add(k)

        new_rules = []
        for r in g1[k]:
            uks, new_rule = catenate_rule_to_key(r, s2)
            new_rules.append(new_rule)
            keys.extend(uks)

        k_ = catenate_nonterminals(k, s2)
        new_g[k_] = new_rules
    ks = catenate_nonterminals(s1, s2)
    return {**g2, **new_g}, ks
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re3 = '1(2(3|5))'
g3 = {
        '<start3>' : [['1', '<A3>']],
        '<A3>' : [['2', '<B3>']],
        '<B3>' : [['3'], ['5']]
        }
my_re4 = 'a(b(c|d)|b)'
g4 = {
        '<start4>' : [['a', '<A4>']],
        '<A4>' : [['b', '<B4>'], ['b']],
        '<B4>' : [['c'], ['d']]
        }
g, s = catenate_grammar(g3, '<start3>', g4, '<start4>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re3 + my_re4, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re3 = &#x27;1(2(3|5))&#x27;
g3 = {
        &#x27;&lt;start3&gt;&#x27; : [[&#x27;1&#x27;, &#x27;&lt;A3&gt;&#x27;]],
        &#x27;&lt;A3&gt;&#x27; : [[&#x27;2&#x27;, &#x27;&lt;B3&gt;&#x27;]],
        &#x27;&lt;B3&gt;&#x27; : [[&#x27;3&#x27;], [&#x27;5&#x27;]]
        }
my_re4 = &#x27;a(b(c|d)|b)&#x27;
g4 = {
        &#x27;&lt;start4&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A4&gt;&#x27;]],
        &#x27;&lt;A4&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;B4&gt;&#x27;], [&#x27;b&#x27;]],
        &#x27;&lt;B4&gt;&#x27; : [[&#x27;c&#x27;], [&#x27;d&#x27;]]
        }
g, s = catenate_grammar(g3, &#x27;&lt;start3&gt;&#x27;, g4, &#x27;&lt;start4&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re3 + my_re4, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Kleene Plus of Regular Grammars
Given a nonterminal symbol and the grammar in which it is defined, the
Kleene plus is simply a regular concatenation of the nontrerminal with
itself (recursive), with a regular union of its nonterminal's rules. The small
difference here from regular concatenation is that, when we concatenate the
nonterminal with itself, we do not need to check for disjointness of
nonterminals, because the definitions of other nonterminals are exactly the
same. Further, $$G2$$ is never used in the algorithm except in the final
grammar.

<!--
############
def regular_kleeneplus(g1, s1):
    s1plus = '<%s.>' % s1[1:-1]
    gn, sn = catenate_grammar(g1, s1, g1, s1plus, verify=False)
    gn[s1plus] = gn[sn]
    gn[s1plus].extend(g1[s1])
    return gn, s1plus

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regular_kleeneplus(g1, s1):
    s1plus = &#x27;&lt;%s.&gt;&#x27; % s1[1:-1]
    gn, sn = catenate_grammar(g1, s1, g1, s1plus, verify=False)
    gn[s1plus] = gn[sn]
    gn[s1plus].extend(g1[s1])
    return gn, s1plus
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1plus = '(%s)+' % my_re1
g, s = regular_kleeneplus(g1, '<start1>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1plus, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1plus = &#x27;(%s)+&#x27; % my_re1
g, s = regular_kleeneplus(g1, &#x27;&lt;start1&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1plus, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Kleene Star of Regular Grammars
For Kleene Star, add $$ \epsilon $$ to the language of Kleene Plus.

<!--
############
def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    if [] not in g[s]: g[s].append([])
    return g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    if [] not in g[s]: g[s].append([])
    return g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1star = '(%s)+' % my_re1
g, s = regular_kleenestar(g1, '<start1>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert (re.match(my_re1star, v) or v == ''), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1star = &#x27;(%s)+&#x27; % my_re1
g, s = regular_kleenestar(g1, &#x27;&lt;start1&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert (re.match(my_re1star, v) or v == &#x27;&#x27;), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we have all operations  necessary to convert a regular
expression to a regular grammar directly. We first define the class

<!--
############
class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
 <cex>   ::= <exp>
           | <exp> <cex> 
```

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_exp(child)
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            g, s = catenate_grammar(g1, s1, g2, key2)
            return g, s
        else:
            return g1, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_exp(child)
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            g, s = catenate_grammar(g1, s1, g2, key2)
            return g, s
        else:
            return g1, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
  <regex> ::= <cex>
            | <cex> `|` <regex>
```

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_cex(child)
        if not children: return g1, s1
        if len(children) == 2:
            g2, s2 = self.convert_regex(children[1])
            g, s = union_grammars(g1, s1, g2, s2)
            return g, s
        else:
            assert len(children) == 1
            g1[s1].append([])
            return g1, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_cex(child)
        if not children: return g1, s1
        if len(children) == 2:
            g2, s2 = self.convert_regex(children[1])
            g, s = union_grammars(g1, s1, g2, s2)
            return g, s
        else:
            assert len(children) == 1
            g1[s1].append([])
            return g1, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
   <regexplus> ::= <unitexp> `+`
```

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleeneplus(g, s)

    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleenestar(g, s)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleeneplus(g, s)

    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleenestar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re = 'x(a|b|c)+'
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;x(a|b|c)+&#x27;
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, the grammar may still contain degenerate rules
of the form $$ A \rightarrow B $$. We need to clean that up so
that rules follow one of $$ A \rightarrow a B $$ or $$ A \rightarrow a $$ 
or $$ A \rightarrow \epsilon $$.

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def is_degenerate_rule(self, rule):
        return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

    def cleanup_regular_grammar(self, g, s):
        # assumes no cycle
        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                new_rules = []
                new_g[k] = new_rules
                for r in g[k]:
                    if self.is_degenerate_rule(r):
                        new_r = g[r[0]]
                        if self.is_degenerate_rule(new_r): cont = True
                        new_rules.extend(new_r)
                    else:
                        new_rules.append(r)
            return new_g, s

    def to_grammar(self, my_re):
        parsed = self.parse(my_re)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        grammar, start = self.convert_regex(children[0])
        return self.cleanup_regular_grammar(grammar, start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def is_degenerate_rule(self, rule):
        return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

    def cleanup_regular_grammar(self, g, s):
        # assumes no cycle
        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                new_rules = []
                new_g[k] = new_rules
                for r in g[k]:
                    if self.is_degenerate_rule(r):
                        new_r = g[r[0]]
                        if self.is_degenerate_rule(new_r): cont = True
                        new_rules.extend(new_r)
                    else:
                        new_rules.append(r)
            return new_g, s

    def to_grammar(self, my_re):
        parsed = self.parse(my_re)
        key, children = parsed
        assert key == &#x27;&lt;start&gt;&#x27;
        assert len(children) == 1
        grammar, start = self.convert_regex(children[0])
        return self.cleanup_regular_grammar(grammar, start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re = '(a|b|c)+(de|f)*'
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;(a|b|c)+(de|f)*&#x27;
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py).


The installable python wheel `rxregular` is available [here](/py/rxregular-0.0.1-py2.py3-none-any.whl).

