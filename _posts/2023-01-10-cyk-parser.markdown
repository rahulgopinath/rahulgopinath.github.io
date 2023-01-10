---
published: true
title: CYK Parser
layout: post
comments: true
tags: parsing, gll
categories: post
---
TLDR; This tutorial is a complete implementation of CYK Parser in Python[^grune2008parsing]
The Python interpreter is embedded so that you can work through the
implementation steps.
 
A CYK parser is a general context-free parser. 
It uses dynamic # programming to fill in a chart. Unlike Earley, GLL and GLR
parsers, it requires the grammar to be in the Chomsky normal form, which
allows at most two symbols on the right hand side of any production.
In particular, all the rules have to conform to
$$ A -> BC $$
$$ A -> a $$
$$ S -> \epsilon $$
Where A,B, and C are nonterminal symbols, a is a terminal symbol, S is the
start symbol, and $\epsilon$ is the empty string.
 
We [previously discussed](/post/2021/02/06/earley-parsing/) 
Earley parser which is a general context-free parser. CYK
parser is another general context-free parser that is capable of parsing
strings that conform to **any** given context-free grammar.
 
Similar to Earley, GLR, GLL, and other general context-free parsers, the worst
case for CYK parsing is $$ O(n^3) $$ . However, unlike those parsers, the best
case is also $$ O(n^3) $$ for all grammars.
 
## Synopsis
```python
import cykparser as P
my_grammar = {'<start>': [['1', '<A>'],
                          ['2']
                         ],
              '<A>'    : [['a']]}
my_parser = P.compile_grammar(my_grammar)
for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
    print(P.format_parsetree(tree))
```

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
## Definitions
For this post, we use the following terms:
 
* The _alphabet_ is the set all of symbols in the input language. For example,
  in this post, we use all ASCII characters as alphabet.

* A _terminal_ is a single alphabet symbol. Note that this is slightly different
  from usual definitions (done here for ease of parsing). (Usually a terminal is
  a contiguous sequence of symbols from the alphabet. However, both kinds of
  grammars have a one to one correspondence, and can be converted easily.)

  For example, `x` is a terminal symbol.

* A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
  in the grammar using _rules_ for expansion.

  For example, `<term>` is a nonterminal in the below grammar.

* A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
  nonterminals) that describe an expansion of a given terminal. A rule is
  also called an _alternative_ expansion.

  For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.

* A _production_ is a combination of a nonterminal and one of its productions.

  For example `<expr>: [<term>+<expr>]` is a production.

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

* The *yield* of a tree is the string resulting from collapsing that tree.

* An *epsilon* rule matches an empty string.

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
We use the `display_tree()` method in earley parser for displaying trees.

<!--
############
import earleyparser as ep

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import earleyparser as ep
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We use the random choice to extract derivation trees from the parse forest.

<!--
############
import random

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
Here is an example grammar for arithmetic expressions, starting at `<start>`.
A terminal symbol has exactly one character
(Note that we disallow empty string (`''`) as a terminal symbol).
Secondly, as per traditional implementations,
there can only be one expansion rule for the `<start>` symbol. We work around
this restriction by simply constructing as many charts as there are expansion
rules, and returning all parse trees.

Let us start with the following grammar.

<!--
############
g1 = {
    '<S>': [
          ['<A>', '<B>'],
          ['<B>', '<C>'],
          ['c']],
   '<A>': [
        ['a']],
   '<B>': [
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
    &#x27;&lt;S&gt;&#x27;: [
          [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;],
          [&#x27;&lt;B&gt;&#x27;, &#x27;&lt;C&gt;&#x27;],
          [&#x27;c&#x27;]],
   &#x27;&lt;A&gt;&#x27;: [
        [&#x27;a&#x27;]],
   &#x27;&lt;B&gt;&#x27;: [
        [&#x27;b&#x27;]],
   &#x27;&lt;C&gt;&#x27;: [
        [&#x27;c&#x27;]],
}
g1_start = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We initialize our parser with the grammar, and identify the terminal and
nonterminal productions separately. termiinal productions are those that
are of the form `<A> ::= a` where a is a terminal symbol. Nonterminal
productions are of the form `<A>` ::= <B><C>` where `<B>` and `<C>` are
nonterminal symbols.

<!--
############
class CYKParser(ep.Parser):
    def __init__(self, grammar, log=True):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.terminal_productions = [(k,r[0]) for (k,r) in self.productions if fuzzer.is_terminal(r[0])]
        self.nonterminal_productions = [(k,r) for (k,r) in self.productions if not fuzzer.is_terminal(r[0])]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CYKParser(ep.Parser):
    def __init__(self, grammar, log=True):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.terminal_productions = [(k,r[0]) for (k,r) in self.productions if fuzzer.is_terminal(r[0])]
        self.nonterminal_productions = [(k,r) for (k,r) in self.productions if not fuzzer.is_terminal(r[0])]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the recognizer. The idea here is that CYK algorithm formulates
the recognition problem as a dynamic problem where the parse of a string of
length `n` using a nonterminal `<A>` which is defined as `<A> ::= <B> <C>` is
defined as a parse of the substring `0..x` with the nonterminal `<B>` and the
parse of the substring `x..n` with nonterminal `<C>` where `0 < x < n`. That
is, `<A>` parses the string if there exists such a parse with `<B>` and `<C>`
for some `x`.
We first initialize the matrix that holds the results. The `cell[i][j]`
represents the nonterminals that can parse the substring `text[i..j]`

<!--
############
class CYKParser(CYKParser):
    def init_table(self, text, length):
        return [[{} for i in range(length+1)] for j in range(length+1)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CYKParser(CYKParser):
    def init_table(self, text, length):
        return [[{} for i in range(length+1)] for j in range(length+1)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
So, we first define the base case, when a single input token matches one of
the terminal symbols. In that case, we look at each character in the input,
and for each `i` in the input we identify `cell[i][i+1]` and add the
nonterminal symbol that derives the corresponding token.

<!--
############
class CYKParser(CYKParser):
    def parse_1(self, text, length, table):
        for s in range(0,length):
            for (key, terminal) in self.terminal_productions:
                if text[s] == terminal:
                    table[s][s+1][key] = True
        return table

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CYKParser(CYKParser):
    def parse_1(self, text, length, table):
        for s in range(0,length):
            for (key, terminal) in self.terminal_productions:
                if text[s] == terminal:
                    table[s][s+1][key] = True
        return table
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the multi-token parse. The idea is to build the table
incrementally. We have already indicated in the table which nonterminals parse
a single token. Next, we find all nonterminals that parse two tokens, then
using that, we find all nonterminals that can parse three tokens etc.

<!--
############
class CYKParser(CYKParser):
    def parse_n(self, text, l, length, table):
        # check substrings starting at s, with length l
        for s in range(0, length-l+1):

            # partition the substring at p (l = 1 less than the length of substring)
            for p in range(1, l):
                for (k, [R_b, R_c]) in self.nonterminal_productions: # R_a -> R_b R_c:
                    if R_b in table[s][p] :
                        if R_c in table[s+p][s+l]: #l - p - 1
                            table[s][s+l][k] = True
        return table

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CYKParser(CYKParser):
    def parse_n(self, text, l, length, table):
        # check substrings starting at s, with length l
        for s in range(0, length-l+1):

            # partition the substring at p (l = 1 less than the length of substring)
            for p in range(1, l):
                for (k, [R_b, R_c]) in self.nonterminal_productions: # R_a -&gt; R_b R_c:
                    if R_b in table[s][p] :
                        if R_c in table[s+p][s+l]: #l - p - 1
                            table[s][s+l][k] = True
        return table
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We combine everything together. At the end, we check if the start_symbol can
parse the given tokens by checking (0, n) in the table.

<!--
############
class CYKParser(CYKParser):
    def recognize_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        self.parse_1(text, length, table)
        for l in range(2,length+1): # l is the length of the sub-string
            self.parse_n(text, l, length, table)
        return start_symbol in table[0][-1]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class CYKParser(CYKParser):
    def recognize_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        self.parse_1(text, length, table)
        for l in range(2,length+1): # l is the length of the sub-string
            self.parse_n(text, l, length, table)
        return start_symbol in table[0][-1]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
mystring = 'bc'
p = CYKParser(g1)
v = p.recognize_on(mystring, '<S>')
print(v)

mystring = 'cb'
p = CYKParser(g1)
v = p.recognize_on(mystring, '<S>')
print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;bc&#x27;
p = CYKParser(g1)
v = p.recognize_on(mystring, &#x27;&lt;S&gt;&#x27;)
print(v)

mystring = &#x27;cb&#x27;
p = CYKParser(g1)
v = p.recognize_on(mystring, &#x27;&lt;S&gt;&#x27;)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-01-10-cyk-parser.py).


