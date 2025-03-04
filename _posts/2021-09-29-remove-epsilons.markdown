---
published: true
title: Remove Empty (Epsilon) Rules From a Context-Free Grammar.
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
In the previous post about [uniform random sampling from grammars](https://rahul.gopinath.org/post/2021/07/27/random-sampling-from-context-free-grammar/),
I mentioned that the algorithm expects an *epsilon-free* grammar. That is,
the grammar should contain no empty rules. Unfortunately, empty rules are
quite useful for describing languages. For example, to specify that we need
zero or more white space characters, the following definition of `<spaceZ>`
is the ideal representation.

<!--
############
grammar = {
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        []
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &quot;&lt;spaceZ&gt;&quot;: [
        [ &quot;&lt;space&gt;&quot;, &quot;&lt;spaceZ&gt;&quot; ],
        []
    ],
    &quot;&lt;space&gt;&quot;: [
        [&#x27; &#x27;],
        [&#x27;\t&#x27;],
        [&#x27;\n&#x27;]
    ]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
So, what can we do? In fact, it is possible to transform the grammar such that
it no longer contain epsilon rules. The idea is that any rule that references
a nonterminal that can be empty can be represented by skipping in a duplicate
rule. When there are multiple such empty-able nonterminals, you need to
produce every combination of skipping them.
But first, let us tackle an easier task. We want to remove those nonterminals
that exclusively represent an empty string. E.g.

<!--
############
emptyG = {
    "<start>": [
        ["<spaceZ>"]
            ],
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        ['<empty>']
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ],
    '<empty>': [[]]
}
emptyS = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
emptyG = {
    &quot;&lt;start&gt;&quot;: [
        [&quot;&lt;spaceZ&gt;&quot;]
            ],
    &quot;&lt;spaceZ&gt;&quot;: [
        [ &quot;&lt;space&gt;&quot;, &quot;&lt;spaceZ&gt;&quot; ],
        [&#x27;&lt;empty&gt;&#x27;]
    ],
    &quot;&lt;space&gt;&quot;: [
        [&#x27; &#x27;],
        [&#x27;\t&#x27;],
        [&#x27;\n&#x27;]
    ],
    &#x27;&lt;empty&gt;&#x27;: [[]]
}
emptyS = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also load a few prerequisites

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
<li><a href="https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl">cfgrandomsample-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/07/27/random-sampling-from-context-free-grammar/">Uniform Random Sampling of Strings from Context-Free Grammar</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import cfgrandomsample as grandom
import itertools as I

import sympy

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import cfgrandomsample as grandom
import itertools as I

import sympy
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Remove empty keys
First, we implement removing empty keys that have empty expansions.
In the above `<empty>` is such a key.
Note that we still need an empty expansion inside the definition. i.e `[[]]`.
Leaving `<empty>` without an expansion, i.e. `[]` means that `<empty>` can't
be expanded, and hence we will have an invalid grammar.
That is, `<empty>: []` is not a valid definition.

<!--
############
class GrammarShrinker:
    def __init__(self, grammar, start):
        self.grammar, self.start = grammar, start

    def remove_empty_rule_keys(self):
        while True:
            keys_to_delete = []
            for key in self.grammar:
                if key == self.start: continue
                if self.grammar[key] == [[]]:
                    keys_to_delete.append(key)
            if not keys_to_delete: break
            self.grammar = {k:[[t for t in r if t not in keys_to_delete]
                for r in self.grammar[k]]
                    for k in self.grammar if k not in keys_to_delete}
        return self.grammar

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker:
    def __init__(self, grammar, start):
        self.grammar, self.start = grammar, start

    def remove_empty_rule_keys(self):
        while True:
            keys_to_delete = []
            for key in self.grammar:
                if key == self.start: continue
                if self.grammar[key] == [[]]:
                    keys_to_delete.append(key)
            if not keys_to_delete: break
            self.grammar = {k:[[t for t in r if t not in keys_to_delete]
                for r in self.grammar[k]]
                    for k in self.grammar if k not in keys_to_delete}
        return self.grammar
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gatleast.display_grammar(emptyG, emptyS)
gs = GrammarShrinker(emptyG, emptyS)
newG, newS = gs.remove_empty_rule_keys(), emptyS
gatleast.display_grammar(newG, newS)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gatleast.display_grammar(emptyG, emptyS)
gs = GrammarShrinker(emptyG, emptyS)
newG, newS = gs.remove_empty_rule_keys(), emptyS
gatleast.display_grammar(newG, newS)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now we are ready to tackle the more complex part: That of removing epsilon
rules. First, we need to identify such rules that can become empty, and
hence the corresponding keys that can become empty.
## Finding empty (epsilon) rules
The idea is as follows, We keep a set of nullable nonterminals. For each
rule, we check if all the tokens in the rule are nullable (i.e in the nullable
set). If all are (i.e `all(t in my_epsilons for t in r)`), then, this rule
is nullable. If there are `any` nullable rules for a key, then the key is
nullable. We process these keys until there are no more new keys.

<!--
############
def find_epsilons(g):
    q = [k for k in g if [] in g[k]]
    my_epsilons = set(q)
    while q:
        ekey, *q = q
        nq = [k for k in g if any(all(t in my_epsilons for t in r) for r in g[k])
                if k not in my_epsilons]
        my_epsilons.update(nq)
        q += nq
    return my_epsilons

class GrammarShrinker(GrammarShrinker):
    def find_empty_keys(self):
        return find_epsilons(self.grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_epsilons(g):
    q = [k for k in g if [] in g[k]]
    my_epsilons = set(q)
    while q:
        ekey, *q = q
        nq = [k for k in g if any(all(t in my_epsilons for t in r) for r in g[k])
                if k not in my_epsilons]
        my_epsilons.update(nq)
        q += nq
    return my_epsilons

class GrammarShrinker(GrammarShrinker):
    def find_empty_keys(self):
        return find_epsilons(self.grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gs = GrammarShrinker(newG, newS)
e_keys = gs.find_empty_keys()
print('Emptyable keys:')
for key in e_keys:
    print('',key)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(newG, newS)
e_keys = gs.find_empty_keys()
print(&#x27;Emptyable keys:&#x27;)
for key in e_keys:
    print(&#x27;&#x27;,key)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now that we can find epsilon rules, we need generate all combinations of
the corresponding keys, so that we can generate corresponding rules.
The idea is that for any given rule with nullable nonterminals in it,
you need to generate all combinations of possible rules where some of
such nonterminals are missing. That is, if given
`[<A> <E1> <B> <E2> <C> <E3>]`, you need to generate these rules.
```
[<A> <E1> <B> <E2> <C> <E3>]
[<A> <B> <E2> <C> <E3>]
[<A> <B> <C> <E3>]
[<A> <B> <C>]
[<A> <E1> <B> <C> <E3>]
[<A> <E1> <B> <C>]
[<A> <E1> <B> <E2> <C>]
```

<!--
############
class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            for a in I.combinations(positions, n):
                combinations.append(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            if new_rule:
                new_rules.append(new_rule)
        return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            for a in I.combinations(positions, n):
                combinations.append(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            if new_rule:
                new_rules.append(new_rule)
        return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gs = GrammarShrinker(newG, newS)
zrule = ['<A>', '<E1>', '<B>', '<E2>', '<C>', '<E3>']
print('Rule to produce combinations:', zrule)
ekeys = ['<E1>', '<E2>', '<E3>']
comb = gs.rule_combinations(zrule, ekeys)
for c in comb:
    print('', c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(newG, newS)
zrule = [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;E1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;&lt;E2&gt;&#x27;, &#x27;&lt;C&gt;&#x27;, &#x27;&lt;E3&gt;&#x27;]
print(&#x27;Rule to produce combinations:&#x27;, zrule)
ekeys = [&#x27;&lt;E1&gt;&#x27;, &#x27;&lt;E2&gt;&#x27;, &#x27;&lt;E3&gt;&#x27;]
comb = gs.rule_combinations(zrule, ekeys)
for c in comb:
    print(&#x27;&#x27;, c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try a larger grammar. This is the JSON grammar.

<!--
############
jsonG = {
    "<start>": [["<json>"]],
    "<json>": [["<element>"]],
    "<element>": [["<ws>", "<value>", "<ws>"]],
    "<value>": [["<object>"], ["<array>"], ["<string>"], ["<number>"],
                ["true"], ["false"],
                ["null"]],
    "<object>": [["{", "<ws>", "}"], ["{", "<members>", "}"]],
    "<members>": [["<member>", "<symbol-2>"]],
    "<member>": [["<ws>", "<string>", "<ws>", ":", "<element>"]],
    "<array>": [["[", "<ws>", "]"], ["[", "<elements>", "]"]],
    "<elements>": [["<element>", "<symbol-1-1>"]],
    "<string>": [["\"", "<characters>", "\""]],
    "<characters>": [["<character-1>"]],
    "<character>": [["0"], ["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"],
                    ["8"], ["9"], ["a"], ["b"], ["c"], ["d"], ["e"], ["f"],
                    ["g"], ["h"], ["i"], ["j"], ["k"], ["l"], ["m"], ["n"],
                    ["o"], ["p"], ["q"], ["r"], ["s"], ["t"], ["u"], ["v"],
                    ["w"], ["x"], ["y"], ["z"], ["A"], ["B"], ["C"], ["D"],
                    ["E"], ["F"], ["G"], ["H"], ["I"], ["J"], ["K"], ["L"],
                    ["M"], ["N"], ["O"], ["P"], ["Q"], ["R"], ["S"], ["T"],
                    ["U"], ["V"], ["W"], ["X"], ["Y"], ["Z"], ["!"], ["#"],
                    ["$"], ["%"], ["&"], ["\""], ["("], [")"], ["*"], ["+"],
                    [","], ["-"], ["."], ["/"], [":"], [";"], ["<"], ["="],
                    [">"], ["?"], ["@"], ["["], ["]"], ["^"], ["_"], ["`"],
                    ["{"], ["|"], ["}"], ["~"], [" "], ["<esc>"]],
    "<esc>": [["\\","<escc>"]],
    "<escc>": [["\\"],["b"],["f"], ["n"], ["r"],["t"],["\""]],
    "<number>": [["<int>", "<frac>", "<exp>"]],
    "<int>": [["<digit>"], ["<onenine>", "<digits>"], ["-", "<digits>"],
              ["-", "<onenine>", "<digits>"]],
    "<digits>": [["<digit-1>"]],
    "<digit>": [["0"], ["<onenine>"]],
    "<onenine>": [["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"], ["8"],
                  ["9"]],
    "<frac>": [[], [".", "<digits>"]],
    "<exp>": [[], ["E", "<sign>", "<digits>"], ["e", "<sign>", "<digits>"]],
    "<sign>": [[], ["+"], ["-"]],
    "<ws>": [["<sp1>", "<ws>"], []],
    "<sp1>": [[" "],["\n"],["\t"],["\r"]],
    "<symbol>": [[",", "<members>"]],
    "<symbol-1>": [[",", "<elements>"]],
    "<symbol-2>": [[], ["<symbol>", "<symbol-2>"]],
    "<symbol-1-1>": [[], ["<symbol-1>", "<symbol-1-1>"]],
    "<character-1>": [[], ["<character>", "<character-1>"]],
    "<digit-1>": [["<digit>"], ["<digit>", "<digit-1>"]]
}
jsonS = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
jsonG = {
    &quot;&lt;start&gt;&quot;: [[&quot;&lt;json&gt;&quot;]],
    &quot;&lt;json&gt;&quot;: [[&quot;&lt;element&gt;&quot;]],
    &quot;&lt;element&gt;&quot;: [[&quot;&lt;ws&gt;&quot;, &quot;&lt;value&gt;&quot;, &quot;&lt;ws&gt;&quot;]],
    &quot;&lt;value&gt;&quot;: [[&quot;&lt;object&gt;&quot;], [&quot;&lt;array&gt;&quot;], [&quot;&lt;string&gt;&quot;], [&quot;&lt;number&gt;&quot;],
                [&quot;true&quot;], [&quot;false&quot;],
                [&quot;null&quot;]],
    &quot;&lt;object&gt;&quot;: [[&quot;{&quot;, &quot;&lt;ws&gt;&quot;, &quot;}&quot;], [&quot;{&quot;, &quot;&lt;members&gt;&quot;, &quot;}&quot;]],
    &quot;&lt;members&gt;&quot;: [[&quot;&lt;member&gt;&quot;, &quot;&lt;symbol-2&gt;&quot;]],
    &quot;&lt;member&gt;&quot;: [[&quot;&lt;ws&gt;&quot;, &quot;&lt;string&gt;&quot;, &quot;&lt;ws&gt;&quot;, &quot;:&quot;, &quot;&lt;element&gt;&quot;]],
    &quot;&lt;array&gt;&quot;: [[&quot;[&quot;, &quot;&lt;ws&gt;&quot;, &quot;]&quot;], [&quot;[&quot;, &quot;&lt;elements&gt;&quot;, &quot;]&quot;]],
    &quot;&lt;elements&gt;&quot;: [[&quot;&lt;element&gt;&quot;, &quot;&lt;symbol-1-1&gt;&quot;]],
    &quot;&lt;string&gt;&quot;: [[&quot;\&quot;&quot;, &quot;&lt;characters&gt;&quot;, &quot;\&quot;&quot;]],
    &quot;&lt;characters&gt;&quot;: [[&quot;&lt;character-1&gt;&quot;]],
    &quot;&lt;character&gt;&quot;: [[&quot;0&quot;], [&quot;1&quot;], [&quot;2&quot;], [&quot;3&quot;], [&quot;4&quot;], [&quot;5&quot;], [&quot;6&quot;], [&quot;7&quot;],
                    [&quot;8&quot;], [&quot;9&quot;], [&quot;a&quot;], [&quot;b&quot;], [&quot;c&quot;], [&quot;d&quot;], [&quot;e&quot;], [&quot;f&quot;],
                    [&quot;g&quot;], [&quot;h&quot;], [&quot;i&quot;], [&quot;j&quot;], [&quot;k&quot;], [&quot;l&quot;], [&quot;m&quot;], [&quot;n&quot;],
                    [&quot;o&quot;], [&quot;p&quot;], [&quot;q&quot;], [&quot;r&quot;], [&quot;s&quot;], [&quot;t&quot;], [&quot;u&quot;], [&quot;v&quot;],
                    [&quot;w&quot;], [&quot;x&quot;], [&quot;y&quot;], [&quot;z&quot;], [&quot;A&quot;], [&quot;B&quot;], [&quot;C&quot;], [&quot;D&quot;],
                    [&quot;E&quot;], [&quot;F&quot;], [&quot;G&quot;], [&quot;H&quot;], [&quot;I&quot;], [&quot;J&quot;], [&quot;K&quot;], [&quot;L&quot;],
                    [&quot;M&quot;], [&quot;N&quot;], [&quot;O&quot;], [&quot;P&quot;], [&quot;Q&quot;], [&quot;R&quot;], [&quot;S&quot;], [&quot;T&quot;],
                    [&quot;U&quot;], [&quot;V&quot;], [&quot;W&quot;], [&quot;X&quot;], [&quot;Y&quot;], [&quot;Z&quot;], [&quot;!&quot;], [&quot;#&quot;],
                    [&quot;$&quot;], [&quot;%&quot;], [&quot;&amp;&quot;], [&quot;\&quot;&quot;], [&quot;(&quot;], [&quot;)&quot;], [&quot;*&quot;], [&quot;+&quot;],
                    [&quot;,&quot;], [&quot;-&quot;], [&quot;.&quot;], [&quot;/&quot;], [&quot;:&quot;], [&quot;;&quot;], [&quot;&lt;&quot;], [&quot;=&quot;],
                    [&quot;&gt;&quot;], [&quot;?&quot;], [&quot;@&quot;], [&quot;[&quot;], [&quot;]&quot;], [&quot;^&quot;], [&quot;_&quot;], [&quot;`&quot;],
                    [&quot;{&quot;], [&quot;|&quot;], [&quot;}&quot;], [&quot;~&quot;], [&quot; &quot;], [&quot;&lt;esc&gt;&quot;]],
    &quot;&lt;esc&gt;&quot;: [[&quot;\\&quot;,&quot;&lt;escc&gt;&quot;]],
    &quot;&lt;escc&gt;&quot;: [[&quot;\\&quot;],[&quot;b&quot;],[&quot;f&quot;], [&quot;n&quot;], [&quot;r&quot;],[&quot;t&quot;],[&quot;\&quot;&quot;]],
    &quot;&lt;number&gt;&quot;: [[&quot;&lt;int&gt;&quot;, &quot;&lt;frac&gt;&quot;, &quot;&lt;exp&gt;&quot;]],
    &quot;&lt;int&gt;&quot;: [[&quot;&lt;digit&gt;&quot;], [&quot;&lt;onenine&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;-&quot;, &quot;&lt;digits&gt;&quot;],
              [&quot;-&quot;, &quot;&lt;onenine&gt;&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;digits&gt;&quot;: [[&quot;&lt;digit-1&gt;&quot;]],
    &quot;&lt;digit&gt;&quot;: [[&quot;0&quot;], [&quot;&lt;onenine&gt;&quot;]],
    &quot;&lt;onenine&gt;&quot;: [[&quot;1&quot;], [&quot;2&quot;], [&quot;3&quot;], [&quot;4&quot;], [&quot;5&quot;], [&quot;6&quot;], [&quot;7&quot;], [&quot;8&quot;],
                  [&quot;9&quot;]],
    &quot;&lt;frac&gt;&quot;: [[], [&quot;.&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;exp&gt;&quot;: [[], [&quot;E&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;e&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;sign&gt;&quot;: [[], [&quot;+&quot;], [&quot;-&quot;]],
    &quot;&lt;ws&gt;&quot;: [[&quot;&lt;sp1&gt;&quot;, &quot;&lt;ws&gt;&quot;], []],
    &quot;&lt;sp1&gt;&quot;: [[&quot; &quot;],[&quot;\n&quot;],[&quot;\t&quot;],[&quot;\r&quot;]],
    &quot;&lt;symbol&gt;&quot;: [[&quot;,&quot;, &quot;&lt;members&gt;&quot;]],
    &quot;&lt;symbol-1&gt;&quot;: [[&quot;,&quot;, &quot;&lt;elements&gt;&quot;]],
    &quot;&lt;symbol-2&gt;&quot;: [[], [&quot;&lt;symbol&gt;&quot;, &quot;&lt;symbol-2&gt;&quot;]],
    &quot;&lt;symbol-1-1&gt;&quot;: [[], [&quot;&lt;symbol-1&gt;&quot;, &quot;&lt;symbol-1-1&gt;&quot;]],
    &quot;&lt;character-1&gt;&quot;: [[], [&quot;&lt;character&gt;&quot;, &quot;&lt;character-1&gt;&quot;]],
    &quot;&lt;digit-1&gt;&quot;: [[&quot;&lt;digit&gt;&quot;], [&quot;&lt;digit&gt;&quot;, &quot;&lt;digit-1&gt;&quot;]]
}
jsonS = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Extract combinations.

<!--
############
gs = GrammarShrinker(jsonG, jsonS)
ekeys = gs.find_empty_keys()
print('Emptyable:', ekeys)
zrule = jsonG['<member>'][0]
print('Rule to produce combinations:', zrule)
comb = gs.rule_combinations(zrule, ekeys)
for c in comb:
    print('', c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(jsonG, jsonS)
ekeys = gs.find_empty_keys()
print(&#x27;Emptyable:&#x27;, ekeys)
zrule = jsonG[&#x27;&lt;member&gt;&#x27;][0]
print(&#x27;Rule to produce combinations:&#x27;, zrule)
comb = gs.rule_combinations(zrule, ekeys)
for c in comb:
    print(&#x27;&#x27;, c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here comes the last part, which stitches all these together.

<!--
############
class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        self.remove_empty_rule_keys()
        e_keys = self.find_empty_keys()
        for e_key in e_keys:
            positions = [i for i,r in enumerate(self.grammar[e_key]) if not r]
            for index in positions:
                del self.grammar[e_key][index]
            assert self.grammar[e_key]

        for key in self.grammar:
            rules_hash = {}
            for rule in self.grammar[key]:
                # find e_key positions.
                combs = self.rule_combinations(rule, e_keys)
                for nrule in combs:
                    rules_hash[str(nrule)] = nrule
            self.grammar[key] = [rules_hash[k] for k in rules_hash]


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        self.remove_empty_rule_keys()
        e_keys = self.find_empty_keys()
        for e_key in e_keys:
            positions = [i for i,r in enumerate(self.grammar[e_key]) if not r]
            for index in positions:
                del self.grammar[e_key][index]
            assert self.grammar[e_key]

        for key in self.grammar:
            rules_hash = {}
            for rule in self.grammar[key]:
                # find e_key positions.
                combs = self.rule_combinations(rule, e_keys)
                for nrule in combs:
                    rules_hash[str(nrule)] = nrule
            self.grammar[key] = [rules_hash[k] for k in rules_hash]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using the complete epsilon remover.

<!--
############
gs = GrammarShrinker(jsonG, jsonS)
gs.remove_epsilon_rules()
gatleast.display_grammar(gs.grammar, gs.start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(jsonG, jsonS)
gs.remove_epsilon_rules()
gatleast.display_grammar(gs.grammar, gs.start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now count the strings produced by the epsilon free grammar

<!--
############
rscfg = grandom.RandomSampleCFG(gs.grammar)
max_len = 5
rscfg.produce_shared_forest(gs.start, max_len)
for i in range(10):
    v, tree = rscfg.random_sample(gs.start, 5)
    string = fuzzer.tree_to_string(tree)
    print("mystring:", repr(string), "at:", v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rscfg = grandom.RandomSampleCFG(gs.grammar)
max_len = 5
rscfg.produce_shared_forest(gs.start, max_len)
for i in range(10):
    v, tree = rscfg.random_sample(gs.start, 5)
    string = fuzzer.tree_to_string(tree)
    print(&quot;mystring:&quot;, repr(string), &quot;at:&quot;, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the runnable source of this notebook is [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-29-remove-epsilons.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-29-remove-epsilons.py).


The installable python wheel `cfgremoveepsilon` is available [here](/py/cfgremoveepsilon-0.0.1-py2.py3-none-any.whl).

