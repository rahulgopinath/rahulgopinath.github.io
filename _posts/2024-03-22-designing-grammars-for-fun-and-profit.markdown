---
published: true
title: Building Grammars for Fun and Profit
layout: post
comments: true
tags: grammars peg
categories: post
---

TLDR; This tutorial takes you through the steps to write a
simple context-free grammmar that can parse your custom data format.
The Python interpreter is embedded so that you
can work through the implementation steps.

## Definitions
For this post, we use the following terms as we have defiend  previously:
* The _alphabet_ is the set all of symbols in the input language. For example,
  in this post, we use all ASCII characters as alphabet.
 
* A _terminal_ is a single alphabet symbol.
  For example, `x` is a terminal symbol.
* A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
  in the grammar using _rules_ for expansion.
  For example, `<term>` is a nonterminal symbol.
* A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
  nonterminals) that describe an expansion of a given terminal.
  For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.
* A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.
  For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the nonterminal `<digits>`
* A _context-free grammar_ is  composed of a set of nonterminals and
  corresponding definitions that define the structure of the nonterminal.
  The grammar given below is an example context-free grammar.
* A terminal _derives_ a string if the string contains only the symbols in the
  terminal. A nonterminal derives a string if the corresponding definition
  derives the string. A definition derives the  string if one of the rules in
  the definition derives the string. A rule derives a string if the sequence
  of terms that make up the rule can derive the string, deriving one substring
  after another contiguously (also called parsing).
* A *derivation tree* is an ordered tree that describes how an input string is
  derived by the given start symbol. Also called a *parse tree*.
 
* A derivation tree can be collapsed into its string equivalent. Such a string
  can be parsed again by the nonterminal at the root node of the derivation
  tree such that at least one of the resulting derivation trees would be the
  same as the one we started with.

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
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import math
import random

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import math
import random
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Say you are designing a custom data format. You use this format to
parse data from your clients or customers who are required to provide
the data in the language you have designed. You will come across this
requirement whenever you have a system that interacts with human beings.
In most cases, you may be able to manage with simple well defined
formats such as comma-sepaated values, XML or JSON. However, there may
be cases where the customers may want something that is closer to their
domain. In such cases, what is the best way forward? This is what this
post will explore.
 
Designing a grammar can be intimidating at first, particularly if you
have gone through one of the traditional compiler design and implementation
courses in the university. In this post, I will attempt to convince you that
formal grammars can be much more easier to write and work with. Furthermore,
parsing with them can be far simpler than writing your own recursive descent
parser from scratch, and far more secure.
 
The idea we explore in this post is that, rather than starting with a parser,
a better alternative is to start with a generator (a grammar fuzzer) instead.

## Grammar for Regular Expressions
 
As an example, let us say that you are building a grammar for simple 
regular expressions. We take the simplest regular expression possible
A single character. Let us build a generator for such simple regular
expressions. We will return a derivation tree as the result.

<!--
############
import string, random

ALPHABET = [c for c in string.printable if c not in '|*()']

def gen_regex():
    return ('regex', [gen_alpha()])

def gen_alpha():
    return ('alpha', [(random.choice(ALPHABET), [])])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string, random

ALPHABET = [c for c in string.printable if c not in &#x27;|*()&#x27;]

def gen_regex():
    return (&#x27;regex&#x27;, [gen_alpha()])

def gen_alpha():
    return (&#x27;alpha&#x27;, [(random.choice(ALPHABET), [])])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This works as expected

<!--
############
t = gen_regex()
print(t)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
t = gen_regex()
print(t)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a function to collapse the derivation tree

<!--
############
def collapse(tree):
    key, children = tree
    if not children: return key
    return ''.join([collapse(c) for c in children])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def collapse(tree):
    key, children = tree
    if not children: return key
    return &#x27;&#x27;.join([collapse(c) for c in children])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
print(repr(collapse(t)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(repr(collapse(t)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
So let us try to extend our implementation  a little bit. A regular expression is not
just a single character. It can be any number of such characters, or sequence
of subexpressions. So, let us define that.

<!--
############
def gen_regex():
    return ('regex', [gen_cex()])

def gen_cex():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_alpha(), gen_cex()])
    if r == 1: return ('cex', [gen_alpha()])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gen_regex():
    return (&#x27;regex&#x27;, [gen_cex()])

def gen_cex():
    r = random.randint(0,1)
    if r == 0: return (&#x27;cex&#x27;, [gen_alpha(), gen_cex()])
    if r == 1: return (&#x27;cex&#x27;, [gen_alpha()])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This again works as expected.

<!--
############
t = gen_regex()
print(repr(collapse(t)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
t = gen_regex()
print(repr(collapse(t)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Regular expressions allow one to specify alternative matching with the pipe
symbol. That is `a|b` matches either `a` or `b`. So, let us define that.

<!--
############
def gen_regex():
    return ('regex', [gen_exp()])

def gen_exp():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_cex(), ('|', []), gen_exp()])
    if r == 1: return ('cex', [gen_cex()])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gen_regex():
    return (&#x27;regex&#x27;, [gen_exp()])

def gen_exp():
    r = random.randint(0,1)
    if r == 0: return (&#x27;cex&#x27;, [gen_cex(), (&#x27;|&#x27;, []), gen_exp()])
    if r == 1: return (&#x27;cex&#x27;, [gen_cex()])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This again works as expected.

<!--
############
t = gen_regex()
print(repr(collapse(t)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
t = gen_regex()
print(repr(collapse(t)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we will implement parenthesized expressions. That is,
`(a|b)` is a parenthesized expression that matches either `a`
or `b`, and is considered one single expression for any meta
character that comes after.

<!--
############
def gen_cex():
    r = random.randint(0,1)
    if r == 0: return ('cex', [gen_unitexp(), gen_cex()])
    if r == 1: return ('cex', [gen_unitexp()])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gen_cex():
    r = random.randint(0,1)
    if r == 0: return (&#x27;cex&#x27;, [gen_unitexp(), gen_cex()])
    if r == 1: return (&#x27;cex&#x27;, [gen_unitexp()])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
symmetric probabilities will exhaust the stack. So, use this
trick to avoid that instead.

<!--
############
def gen_unitexp():
    r = random.randint(0,9)
    if r in [1,2,3,4,5,6,7,8,9]: return ('unitexp', [gen_alpha()])
    if r == 0: return ('unitexp', [gen_parenexp()])

def gen_parenexp():
    return ('parenexp', [('(', []), gen_regex() ,(')', [])])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gen_unitexp():
    r = random.randint(0,9)
    if r in [1,2,3,4,5,6,7,8,9]: return (&#x27;unitexp&#x27;, [gen_alpha()])
    if r == 0: return (&#x27;unitexp&#x27;, [gen_parenexp()])

def gen_parenexp():
    return (&#x27;parenexp&#x27;, [(&#x27;(&#x27;, []), gen_regex() ,(&#x27;)&#x27;, [])])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing it again.

<!--
############
t = gen_regex()
print(repr(collapse(t)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
t = gen_regex()
print(repr(collapse(t)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
All that remains is to define the kleene star `*` for zero or
more repetitions

<!--
############
def gen_regex():
    return ('regex', [gen_rex()])

def gen_rex():
    r = random.randint(0,1)
    if r == 0: return ('rex', [gen_exp(), ('*', [])])
    if r == 1: return ('rex', [gen_exp()])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def gen_regex():
    return (&#x27;regex&#x27;, [gen_rex()])

def gen_rex():
    r = random.randint(0,1)
    if r == 0: return (&#x27;rex&#x27;, [gen_exp(), (&#x27;*&#x27;, [])])
    if r == 1: return (&#x27;rex&#x27;, [gen_exp()])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing it again.

<!--
############
t = gen_regex()
print(repr(collapse(t)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
t = gen_regex()
print(repr(collapse(t)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, you would have a fully explored test generator that is ready to
test any parser you would write, and can be improved upon for any extensions
you might want. More importantly, you can easily convert the generator you
wrote to a grammar for your data format. That is, each subroutine name
become the name of a nonterminal symbol.

E.g. `gen_cex()` to `<cex>`

The branches (match) become rule alternatives:

E.g. `<uniexp>: [[<alpha>], [<parenexp>]]`

Sequence of procedure calls become sequences in a rule.

E.g. <parenexp>: [['(', <regex>, ')']] 

With these steps, we have the following grammar.

<!--
############
regex_grammar = {
    '<gen_regex>': [['<gen_rex>']],
    '<gen_rex>': [
        ['<gen_exp>', '*'],
        ['<gen_exp>']],
    '<gen_exp>': [
        ['<gen_cex>', '|', '<gen_exp>'],
        ['<gen_cex>']],
    '<gen_cex>': [
        ['<gen_unitexp>', '<gen_cex>'],
        ['<gen_unitexp>']],
    '<gen_unitexp>': [
        ['<gen_parenexp>'],
        ['<gen_alpha>']],
    '<gen_parenexp>': [
        ['(', '<gen_regex>', ')']],
    '<gen_alpha>': [[c] for c in string.printable if c not in '|*()']
}

regex_start = '<gen_regex>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
regex_grammar = {
    &#x27;&lt;gen_regex&gt;&#x27;: [[&#x27;&lt;gen_rex&gt;&#x27;]],
    &#x27;&lt;gen_rex&gt;&#x27;: [
        [&#x27;&lt;gen_exp&gt;&#x27;, &#x27;*&#x27;],
        [&#x27;&lt;gen_exp&gt;&#x27;]],
    &#x27;&lt;gen_exp&gt;&#x27;: [
        [&#x27;&lt;gen_cex&gt;&#x27;, &#x27;|&#x27;, &#x27;&lt;gen_exp&gt;&#x27;],
        [&#x27;&lt;gen_cex&gt;&#x27;]],
    &#x27;&lt;gen_cex&gt;&#x27;: [
        [&#x27;&lt;gen_unitexp&gt;&#x27;, &#x27;&lt;gen_cex&gt;&#x27;],
        [&#x27;&lt;gen_unitexp&gt;&#x27;]],
    &#x27;&lt;gen_unitexp&gt;&#x27;: [
        [&#x27;&lt;gen_parenexp&gt;&#x27;],
        [&#x27;&lt;gen_alpha&gt;&#x27;]],
    &#x27;&lt;gen_parenexp&gt;&#x27;: [
        [&#x27;(&#x27;, &#x27;&lt;gen_regex&gt;&#x27;, &#x27;)&#x27;]],
    &#x27;&lt;gen_alpha&gt;&#x27;: [[c] for c in string.printable if c not in &#x27;|*()&#x27;]
}

regex_start = &#x27;&lt;gen_regex&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now use it to parse regular expressions. Using our previously
defined PEG parser,

<!--
############
import functools
class peg_parse:
    def __init__(self, grammar): self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            if text[at:].startswith(key):
                return (at + len(key), (key, []))
            else:
                return (at, None)
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
import functools
class peg_parse:
    def __init__(self, grammar): self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            if text[at:].startswith(key):
                return (at + len(key), (key, []))
            else:
                return (at, None)
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
Using it

<!--
############
inrex = '(ab|cb)*d'
print()
f, r = peg_parse(regex_grammar).unify_key(regex_start, inrex)
print(repr(collapse(r)))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
inrex = &#x27;(ab|cb)*d&#x27;
print()
f, r = peg_parse(regex_grammar).unify_key(regex_start, inrex)
print(repr(collapse(r)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
However, there are some caveats to the grammars thus produced.
The main caveat is that you have to be careful in how you order your rules.
In general, build your language such that the first token produced by each of
your rules for the same definition is different.
This will give you LL(1) grammars, which are the easiest to use.

If the above rule can't be adhered to, and if you have two rules such that the
match of one will be a subsequence of another, order the rules in grammar such
that the longest match always comes first.

For example,
```
 <exp> := <cex> '|' <exp>
        | <exp>
```
or equivalently
```
'<exp>' : [['<cex>', '|', '<exp>'], ['<exp>']] 
```
Such kind of grammars are called Parsing Expression Grammars. The idea is that
the first rule is given priority over the other rules, and hence longest
matching rule should come first.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-03-22-designing-grammars-for-fun-and-profit.py).


