---
published: true
title: Recursive descent parsing with Parsing Expression (PEG) and Context Free (CFG) Grammars
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
In the [previous](/post/2018/09/05/top-down-parsing/) post, I showed how to
write a simple recursive descent parser by hand -- that is using a set of
mutually recursive procedures. Actually, I lied when I said context-free.
The common hand-written parsers are usually an encoding of a kind of grammar
called _Parsing Expression Grammar_ or _PEG_ for short.
The difference between _PEG_ and a _CFG_ is that _PEG_ does not admit
ambiguity. In particular, _PEG_ uses ordered choice in its alternatives.
Due to the ordered choice, the ordering of alternatives is important.
A few interesting things about _PEG_:
* We know that _L(PEG)_ is not a subset of _L(CFG)_ (There are [languages](https://stackoverflow.com/a/46743864/1420407) that can be expressed with a _PEG_ that can not be expressed with a _CFG_ -- for example, $$a^nb^nc^n$$).
* We do not know if _L(PEG)_ is a superset of _CFL_. However, given that all [PEGs can be parsed in $$O(n)$$](https://en.wikipedia.org/wiki/Parsing_expression_grammar), and the best general _CFG_ parsers can only reach $$O(n^{(3-\frac{e}{3})})$$ due to the equivalence to boolean matrix multiplication[^valiant1975general] [^lee2002fast]. 
* We do know that _L(PEG)_ is at least as large as deterministic _CFL_.
* We also [know](https://arxiv.org/pdf/1304.3177.pdf) that an _LL(1)_ grammar can be interpreted either as a _CFG_ or a _PEG_ and it will describe the same language. Further, any _LL(k)_ grammar can be translated to _L(PEG)_, but reverse is not always true -- [it will work only if the PEG lookahead pattern can be reduced to a DFA](https://stackoverflow.com/a/46743864/1420407).

The problem with what we did in the previous post is that it is a rather naive implementation. In particular, there could be a lot of backtracking, which can make the runtime explode. One solution to that is incorporating memoization. Since we start with automatic generation of parser from a grammar (unlike previously, where we explored a handwritten parser first), we will take a slightly different tack in writing the algorithm.

## PEG Recognizer

The idea behind a simple _PEG_ recognizer is that, you try to unify the string you want to match with the corresponding key in the grammar. If the key is not present in the grammar, it is a literal, which needs to be matched with string equality.
If the key is present in the grammar, get the corresponding productions (rules) for that key,  and start unifying each rule one by one on the string to be matched.

<!--
############
def unify_key(grammar, key, text):
    if key not in grammar:
        return text[len(key):] if text.startswith(key) else None
    rules = grammar[key]
    for rule in rules:
        l = unify_rule(grammar, rule, text)
        if l is not None: return l
    return None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unify_key(grammar, key, text):
    if key not in grammar:
        return text[len(key):] if text.startswith(key) else None
    rules = grammar[key]
    for rule in rules:
        l = unify_rule(grammar, rule, text)
        if l is not None: return l
    return None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For unifying rules, the idea is similar. We take each token in the rule, and try to unify that token with the string to be matched. We rely on `unify_key` for doing the unification of the token. if the unification fails, we return empty handed.

<!--
############
def unify_rule(grammar, rule, text):
    for token in rule:
        text = unify_key(grammar, token, text)
        if text is None: return None
    return text

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unify_rule(grammar, rule, text):
    for token in rule:
        text = unify_key(grammar, token, text)
        if text is None: return None
    return text
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us define a grammar to test it out.

<!--
############
term_grammar = {
    '<expr>': [
        ['<term>', '<add_op>', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '<mul_op>', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [[str(i)] for i in list(range(10))],
    '<add_op>': [['+'], ['-']],
    '<mul_op>': [['*'], ['/']]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
term_grammar = {
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;term&gt;&#x27;, &#x27;&lt;add_op&gt;&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [
        [&#x27;&lt;fact&gt;&#x27;, &#x27;&lt;mul_op&gt;&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[str(i)] for i in list(range(10))],
    &#x27;&lt;add_op&gt;&#x27;: [[&#x27;+&#x27;], [&#x27;-&#x27;]],
    &#x27;&lt;mul_op&gt;&#x27;: [[&#x27;*&#x27;], [&#x27;/&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver:

<!--
############
to_parse = '1+2'
rest = unify_key(term_grammar, '<expr>', to_parse)
assert rest == ''
to_parse = '1%2'
result = unify_key(term_grammar, '<expr>', to_parse)
assert result == '%2'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = &#x27;1+2&#x27;
rest = unify_key(term_grammar, &#x27;&lt;expr&gt;&#x27;, to_parse)
assert rest == &#x27;&#x27;
to_parse = &#x27;1%2&#x27;
result = unify_key(term_grammar, &#x27;&lt;expr&gt;&#x27;, to_parse)
assert result == &#x27;%2&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## PEG Parser
When we implemented the `unify_key`, we made an important decision, which was that, we return as soon as a match was found. This is what distinguishes a `PEG` parser from a general `CFG` parser. In particular it means that rules have to be ordered.
That is, the following grammar wont work:

```ebnf
ifmatch = IF (expr) THEN stmts
        | IF (expr) THEN stmts ELSE stmts
```
It has to be written as the following so that the rule that can match the longest string will come first. 
```ebnf
ifmatch = IF (expr) THEN stmts ELSE stmts
        | IF (expr) THEN stmts
```
If we now parse an `if` statement without else using the above grammar, such a `IF (a=b) THEN return 0`, the first rule will fail, and the parse will start for the second rule again at `IF`. This backtracking is unnecessary as one can see that `IF (a=b) THEN return 0` is already parsed by all terms in the second rule. What we want is to save the old parses so that we can simply return the already parsed result. That is,

```python
   if seen((token, text, at)):
       return old_result
```
Fortunately, Python makes this easy using `functools.lru_cache` which
provides cheap memoization to functions. Adding memoizaion, saving results, and reorganizing code, we have our _PEG_ parser.

<!--
############
import sys
import functools

class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
import functools

class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver:

<!--
############
to_parse = '1+2'
result = peg_parse(term_grammar).unify_key('<expr>', to_parse)
assert (len(to_parse) - result[0]) == 0
print(result[1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = &#x27;1+2&#x27;
result = peg_parse(term_grammar).unify_key(&#x27;&lt;expr&gt;&#x27;, to_parse)
assert (len(to_parse) - result[0]) == 0
print(result[1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What we have here is only a subset of _PEG_ grammar. A _PEG_ grammar can contain

* Sequence: e1 e2
* Ordered choice: e1 / e2
* Zero-or-more: e*
* One-or-more: e+
* Optional: e?
* And-predicate: &e -- match `e` but do not consume any input
* Not-predicate: !e

We are yet to provide _e*_, _e+_, and _e?_. However, these are only conveniences. One can easily modify any _PEG_ that uses them to use grammar rules instead. The effect of predicates on the other hand can not be easily produced.  However, the lack of predicates does not change[^ford2004parsing] the class of languages that such grammars can match, and even without the predicates, our _PEG_ can be useful for easily representing a large category of programs.

Note: This implementation will blow the stack pretty fast if we attempt to parse any expressions that are reasonably large (where some node in the derivation tree has a depth of 500) because Python provides very limited stack. One can improve the situation slightly by inlining the `unify_rule()`.

<!--
############
class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)

        rules = self.grammar[key]
        for rule in rules:
            results = []
            tfrom = at
            for part in rule:
                tfrom, res_ = self.unify_key(part, text, tfrom)
                if res_ is None:
                    l, results = tfrom, None
                    break
                results.append(res_)
            l, res = tfrom, results
            if res is not None: return l, (key, res)
        return (0, None)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)

        rules = self.grammar[key]
        for rule in rules:
            results = []
            tfrom = at
            for part in rule:
                tfrom, res_ = self.unify_key(part, text, tfrom)
                if res_ is None:
                    l, results = tfrom, None
                    break
                results.append(res_)
            l, res = tfrom, results
            if res is not None: return l, (key, res)
        return (0, None)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This gets us to derivation trees with at a depth of 1000 (or more if we increase the `sys.setrecursionlimit()`). We can also turn this to a completely iterative solution if we simulate the stack (formal arguments, locals, return value) ourselves rather than relying on the Python stack frame.

## Context Free Parser

It is fairly easy to turn this parser into a context-free grammar parser instead. The main idea is to keep a list of parse points, and advance them one at a time.

<!--
############
class cfg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, tfrom):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom)
                for at, nt in new_tfroms:
                    tfroms_.append((at, (key, nt)))
            return tfroms_
        assert False

    def unify_rule(self, parts, text, tfrom):
        tfroms = [(tfrom, [])]
        for part in parts:
            new_tfroms = []
            for at, nt in tfroms:
                tfs = self.unify_key(part, text, at)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class cfg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, tfrom):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom)
                for at, nt in new_tfroms:
                    tfroms_.append((at, (key, nt)))
            return tfroms_
        assert False

    def unify_rule(self, parts, text, tfrom):
        tfroms = [(tfrom, [])]
        for part in parts:
            new_tfroms = []
            for at, nt in tfroms:
                tfs = self.unify_key(part, text, at)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Driver

<!--
############
to_parse = '1+2'
p = cfg_parse(term_grammar)
result = p.unify_key('<expr>', to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        print(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = &#x27;1+2&#x27;
p = cfg_parse(term_grammar)
result = p.unify_key(&#x27;&lt;expr&gt;&#x27;, to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        print(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us define a simple viewer

<!--
############
def display_treeb(node, level=0, c='-'):
    key, children = node
    if children:
        display_treeb(children[0], level + 1, c='/')
    print(' ' * 4 * level + c+'> ' + key + '|')
    if len(children) > 1:
        display_treeb(children[1], level + 1, c='\\')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def display_treeb(node, level=0, c=&#x27;-&#x27;):
    key, children = node
    if children:
        display_treeb(children[0], level + 1, c=&#x27;/&#x27;)
    print(&#x27; &#x27; * 4 * level + c+&#x27;&gt; &#x27; + key + &#x27;|&#x27;)
    if len(children) &gt; 1:
        display_treeb(children[1], level + 1, c=&#x27;\\&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Driver

<!--
############
to_parse = '1+2'
p = cfg_parse(term_grammar)
result = p.unify_key('<expr>', to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        display_treeb(res)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = &#x27;1+2&#x27;
p = cfg_parse(term_grammar)
result = p.unify_key(&#x27;&lt;expr&gt;&#x27;, to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        display_treeb(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The above can only work with binary trees. Here is another that can work with all trees.

<!--
############
def display_tree(node, level=0, c='-'):
    key, children = node
    print(' ' * 4 * level + c+'> ' + key)
    for c in children:
        display_tree(c, level + 1, c='+')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def display_tree(node, level=0, c=&#x27;-&#x27;):
    key, children = node
    print(&#x27; &#x27; * 4 * level + c+&#x27;&gt; &#x27; + key)
    for c in children:
        display_tree(c, level + 1, c=&#x27;+&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
to_parse = '1+2+3+4*5/6'
p = cfg_parse(term_grammar)
result = p.unify_key('<expr>', to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        display_tree(res)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = &#x27;1+2+3+4*5/6&#x27;
p = cfg_parse(term_grammar)
result = p.unify_key(&#x27;&lt;expr&gt;&#x27;, to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This implementation is quite limited in that we have lost the ability to memoize (can be added back), and can not handle left recursion. See the [Earley parser](https://www.fuzzingbook.org/html/Parser.html) for a parser without these drawbacks.

**Note**: I recently found a very tiny PEG parser described [here](https://news.ycombinator.com/item?id=3202505).

**Note**: It has been five years since I wrote this post, and I have had some
time to better understand the research behind PEG, CFG, LR(k), and LL(k).
At this point, I would say that this parser is an implementation of the
TDPL (Top Down Parsing Language) from Alexander Birman in 1970[^birman1970].
The main difference between TDPL and PEG is that PEG allows a few convenience
operators such as `*`, `+`, `?`, `&`, `!` and grouping which are taken from
EBNF and regular expression syntax. However, the resulting language is
equivalent in recognition power to TDPL and GTDPL[^ford2004parsing], and PEGs
can be reduced to GTDPL, which in turn can be reduced to TDPL.

However, more importantly, the language expressed with PEG grammars coincide
with the language expressed by Context Free Grammars within the LL(1) set.
That is, the algorithm expressed below should actually be considered an LL(1)
parser when the grammar is LL(1). That is, any rule in a given definition
can be unambiguously chosen based only on the next token in the stream. This
is important because in the literature, LL(1) parsing requires computation of
*first* sets. This parser shows you how to do LL(1) parsing without parse
tables.
 
[^valiant1975general]: Valiant, Leslie G. "General context-free recognition in less than cubic time." Journal of computer and system sciences 10.2 (1975): 308-315. 

[^lee2002fast]: Lee, Lillian. "Fast context-free grammar parsing requires fast boolean matrix multiplication." Journal of the ACM (JACM) 49.1 (2002): 1-15.

[^ford2004parsing]: Ford, Bryan. "Parsing expression grammars: a recognition-based syntactic foundation." Proceedings of the 31st ACM SIGPLAN-SIGACT symposium on Principles of programming languages. 2004.  <https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf>

[^birman1970]:  Birman, Alexander (1970). The TMG Recognition Schema. ACM Digital Library (phd). Princeton University. 

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2018-09-06-peg-parsing.py).


The installable python wheel `pegparser` is available [here](/py/pegparser-0.0.1-py2.py3-none-any.whl).

