---
published: true
title: Removing Left Recursion from Context Free Grammars
layout: post
comments: true
tags: context-free-grammars left-recursion
categories: post
---

Left recursion in context-free grammars is when a nonterminal when expanded,
results in the same nonterminal symbol in the expansion as the first symbol.
If the symbol is present as the first symbol in one of the expansion rules of
the nonterminal, it is called a direct left-recursion. Below is a grammar with
direct left-recursion. The nonterminal symbols `<E>` , `<F>`, and `<Ds>` have
direct left-recursion.

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
E1 = {
 '<start>': [['<E>']],
 '<E>': [['<E>', '*', '<F>'],
         ['<E>', '/', '<F>'],
         ['<F>']],
 '<F>': [['<F>', '+', '<T>'],
         ['<F>', '-', '<T>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<Ds>']],
 '<Ds>':[['<Ds>', '<D>'], ['<D>']],
 '<D>': [[str(i)] for i in range(10)]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
E1 = {
 &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;]],
 &#x27;&lt;E&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;F&gt;&#x27;],
         [&#x27;&lt;E&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;F&gt;&#x27;],
         [&#x27;&lt;F&gt;&#x27;]],
 &#x27;&lt;F&gt;&#x27;: [[&#x27;&lt;F&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;T&gt;&#x27;],
         [&#x27;&lt;F&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;T&gt;&#x27;],
         [&#x27;&lt;T&gt;&#x27;]],
 &#x27;&lt;T&gt;&#x27;: [[&#x27;(&#x27;, &#x27;&lt;E&gt;&#x27;, &#x27;)&#x27;],
         [&#x27;&lt;Ds&gt;&#x27;]],
 &#x27;&lt;Ds&gt;&#x27;:[[&#x27;&lt;Ds&gt;&#x27;, &#x27;&lt;D&gt;&#x27;], [&#x27;&lt;D&gt;&#x27;]],
 &#x27;&lt;D&gt;&#x27;: [[str(i)] for i in range(10)]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
An indirect left-recursion occurs when the symbol is found after more than
one expansion step. Here is an indirect left-recursion.

<!--
############
E2 = {
'<start>': [['<I>']],
'<I>' : [['<Ds>']],
'<Ds>': [['<I>', '<D>'], ['<D>']],
'<D>': [[str(i)] for i in range(10)]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
E2 = {
&#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;I&gt;&#x27;]],
&#x27;&lt;I&gt;&#x27; : [[&#x27;&lt;Ds&gt;&#x27;]],
&#x27;&lt;Ds&gt;&#x27;: [[&#x27;&lt;I&gt;&#x27;, &#x27;&lt;D&gt;&#x27;], [&#x27;&lt;D&gt;&#x27;]],
&#x27;&lt;D&gt;&#x27;: [[str(i)] for i in range(10)]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here, `<I>` has an indirect left-recursion as expanding `<I>` through `<Ds>`
results in `<I>` being the first symbol again.

For context-free grammars, in many cases left-recursions are a nuisance.
During parsing, left-recursion in grammars can make simpler parsers recurse
infinitely. Hence, it is often useful to eliminate them.

It is fairly simple to eliminate them from context-free grammars. Here is
a solution.
 
#### Prerequisites
 
As before, we start with the prerequisite imports.

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
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
We need the fuzzer to generate inputs to parse and also to provide some
utilities

<!--
############
import simplefuzzer as fuzzer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
A terminal symbol has exactly one character
(Note that we disallow empty string (`''`) as a terminal symbol).

We have our grammar:

<!--
############
RG = {
 '<start>': [['<E>']],
 '<E>': [['<E>', '*', '<F>'],
         ['<E>', '/', '<F>'],
         ['<F>']],
 '<F>': [['<F>', '+', '<T>'],
         ['<F>', '-', '<T>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<I>']],
 '<I>' : [['<Ds>']],
 '<Ds>': [['<I>', '<D>'], ['<D>']],
 '<D>': [[str(i)] for i in range(10)]
}

RGstart = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
RG = {
 &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;]],
 &#x27;&lt;E&gt;&#x27;: [[&#x27;&lt;E&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;F&gt;&#x27;],
         [&#x27;&lt;E&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;F&gt;&#x27;],
         [&#x27;&lt;F&gt;&#x27;]],
 &#x27;&lt;F&gt;&#x27;: [[&#x27;&lt;F&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;T&gt;&#x27;],
         [&#x27;&lt;F&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;T&gt;&#x27;],
         [&#x27;&lt;T&gt;&#x27;]],
 &#x27;&lt;T&gt;&#x27;: [[&#x27;(&#x27;, &#x27;&lt;E&gt;&#x27;, &#x27;)&#x27;],
         [&#x27;&lt;I&gt;&#x27;]],
 &#x27;&lt;I&gt;&#x27; : [[&#x27;&lt;Ds&gt;&#x27;]],
 &#x27;&lt;Ds&gt;&#x27;: [[&#x27;&lt;I&gt;&#x27;, &#x27;&lt;D&gt;&#x27;], [&#x27;&lt;D&gt;&#x27;]],
 &#x27;&lt;D&gt;&#x27;: [[str(i)] for i in range(10)]
}

RGstart = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
First, we need to check for left recursion

<!--
############
class GrammarUtils:
    def __init__(self, grammar):
        self.grammar = grammar

    def has_direct_left_recursion(self):
        for k in self.grammar:
            for r in self.grammar[k]:
                if r and r[0] == k:
                    return True
        return False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarUtils:
    def __init__(self, grammar):
        self.grammar = grammar

    def has_direct_left_recursion(self):
        for k in self.grammar:
            for r in self.grammar[k]:
                if r and r[0] == k:
                    return True
        return False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
p = GrammarUtils(RG)
print(p.has_direct_left_recursion())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
p = GrammarUtils(RG)
print(p.has_direct_left_recursion())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, to eliminate direct left recursion for the nonterminal `<A>`
we repeat the following transformations until the direct left recursions
from `<A>` are removed.

<!--
############
class GrammarUtils(GrammarUtils):
    def remove_direct_recursion(self, A):
        # repeat this process until no left recursion remains
        while self.has_direct_left_recursion():
            Aprime = '<%s_>' % (A[1:-1])

            # Each alpha is of type A -> A alpha1
            alphas = [rule[1:] for rule in self.grammar[A]
                      if rule and rule[0] == A]

            # Each beta is a sequence of nts that does not start with A
            betas = [rule for rule in self.grammar[A]
                      if not rule or rule[0] != A]

            if not alphas: return # no direct left recursion

            # replace these with two sets of productions one set for A
            self.grammar[A] = [[Aprime]] if not betas else [
                    beta + [Aprime] for beta in betas]

            # and another set for the fresh A'
            self.grammar[Aprime] = [alpha + [Aprime]
                                       for alpha in alphas] + [[]]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarUtils(GrammarUtils):
    def remove_direct_recursion(self, A):
        # repeat this process until no left recursion remains
        while self.has_direct_left_recursion():
            Aprime = &#x27;&lt;%s_&gt;&#x27; % (A[1:-1])

            # Each alpha is of type A -&gt; A alpha1
            alphas = [rule[1:] for rule in self.grammar[A]
                      if rule and rule[0] == A]

            # Each beta is a sequence of nts that does not start with A
            betas = [rule for rule in self.grammar[A]
                      if not rule or rule[0] != A]

            if not alphas: return # no direct left recursion

            # replace these with two sets of productions one set for A
            self.grammar[A] = [[Aprime]] if not betas else [
                    beta + [Aprime] for beta in betas]

            # and another set for the fresh A&#x27;
            self.grammar[Aprime] = [alpha + [Aprime]
                                       for alpha in alphas] + [[]]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
import json
if __name__ == '__main__':
    p = GrammarUtils(RG)
    p.remove_direct_recursion('<E>')
    print(json.dumps(p.grammar, indent=4))
    p.remove_direct_recursion('<F>')
    print(p.has_direct_left_recursion())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import json
if __name__ == &#x27;__main__&#x27;:
    p = GrammarUtils(RG)
    p.remove_direct_recursion(&#x27;&lt;E&gt;&#x27;)
    print(json.dumps(p.grammar, indent=4))
    p.remove_direct_recursion(&#x27;&lt;F&gt;&#x27;)
    print(p.has_direct_left_recursion())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Removing the indirect left-recursion is a bit more trickier. The algorithm
starts by establishing some stable ordering of the nonterminals so that
they can be procesed in order. Next, we apply an algorithm called `Paull's`
algorithm [^1], which is as follows:

<!--
############
class GrammarUtils(GrammarUtils):
    def remove_left_recursion(self) :
        # Establish a topological ordering of nonterminals.
        keylst = list(self.grammar.keys())

        # For each nonterminal A_i
        for i,_ in enumerate(keylst):
            Ai = keylst[i]

            # Repeat until iteration leaves the grammar unchanged.
            # cont = True
            # while cont:
            # For each rule Ai -> alpha_i
            for alpha_i in self.grammar[Ai]:
                #   if alpha_i begins with a nonterminal Aj and j < i
                Ajs = [keylst[j] for j in range(i)]
                if alpha_i and alpha_i[0] in Ajs:
                    Aj = alpha_i[0]
                    # Let beta_i be alpha_i without leading Ai
                    beta_i = alpha_i[1:]
                    # remove rule Ai -> alpha_i
                    lst = [r for r in self.grammar[Ai] if r != alpha_i]
                    self.grammar[Ai] = lst
                    # for each rule Aj -> alpha_j
                    #   add Ai -> alpha_j beta_i
                    for alpha_j in self.grammar[Aj]:
                        self.grammar[Ai].append(alpha_j + beta_i)
            #        cont = True
            #cont = False
            self.remove_direct_recursion(Ai)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarUtils(GrammarUtils):
    def remove_left_recursion(self) :
        # Establish a topological ordering of nonterminals.
        keylst = list(self.grammar.keys())

        # For each nonterminal A_i
        for i,_ in enumerate(keylst):
            Ai = keylst[i]

            # Repeat until iteration leaves the grammar unchanged.
            # cont = True
            # while cont:
            # For each rule Ai -&gt; alpha_i
            for alpha_i in self.grammar[Ai]:
                #   if alpha_i begins with a nonterminal Aj and j &lt; i
                Ajs = [keylst[j] for j in range(i)]
                if alpha_i and alpha_i[0] in Ajs:
                    Aj = alpha_i[0]
                    # Let beta_i be alpha_i without leading Ai
                    beta_i = alpha_i[1:]
                    # remove rule Ai -&gt; alpha_i
                    lst = [r for r in self.grammar[Ai] if r != alpha_i]
                    self.grammar[Ai] = lst
                    # for each rule Aj -&gt; alpha_j
                    #   add Ai -&gt; alpha_j beta_i
                    for alpha_j in self.grammar[Aj]:
                        self.grammar[Ai].append(alpha_j + beta_i)
            #        cont = True
            #cont = False
            self.remove_direct_recursion(Ai)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it:

<!--
############
p = GrammarUtils(RG)
p.remove_left_recursion()
print(json.dumps(p.grammar, indent=4))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
p = GrammarUtils(RG)
p.remove_left_recursion()
print(json.dumps(p.grammar, indent=4))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us see if the grammar results in the right language

<!--
############
gf = fuzzer.LimitFuzzer(p.grammar)
for i in range(10):
   print(gf.iter_fuzz(key=RGstart, max_depth=10))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf = fuzzer.LimitFuzzer(p.grammar)
for i in range(10):
   print(gf.iter_fuzz(key=RGstart, max_depth=10))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^1]: Marvin C. Paull Algorithm design: a recursion transformation framework

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-10-19-remove-left-recursion.py).


