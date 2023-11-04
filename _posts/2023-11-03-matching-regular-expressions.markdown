---
published: true
title: Efficient Matching with Regular Expressions
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
In the previous posts, I talked about converting a regular grammar to a
deterministic regular grammar (DRG) equivalent to a DFA and mentioned that
it was one of the ways to ensure that there is no exponential wort-case
for regular expression matching. However, this is not the only way to
avoid exponential worst-case due to backtracking in regular expressions.
A possible solution is the [Thompson algorithm described here](https://swtch.com/~rsc/regexp/regexp1.html).
The idea is that, rather than backtracking, for any given NFA,
track all possible threads in parallel. This raises a question. Is the number
of such parallel threads bounded?

Given a regular expression with size n, excluding parenthesis,
can be represented by an NFA with n states. Furthermore, any given parsing
thread can contain no information other than the current node.
That is, for an NFA with n states one
never needs to track more than n parallel threads while parsing.
I recently found a rather elegant and tiny implementation of this in Python
[here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).
This is an attempt to document my understanding of this code.
 
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
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">Fuzzing With Regular Expressions</a>".</li>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import earleyparser

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import earleyparser
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Functional Implementation

Here is the Python implementation from [here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py)
slightly modified to look similar to my [post](/post/2020/03/02/combinatory-parsing/)
on simple combinatory parsing. I also name the anonymous lambdas to make it
easier to understand.
 
The basic idea is to first construct the NFA processing graph, then let the
string processing take place through the graph. Each node (state in NFA) in
the graph requires no more information than the nodes to transition to on
given input tokens to accept or reject the remaining string. This is leveraged
in the match function below, where based on the current input token, all the
states are queried to identify the next state. The main point of the NFA is
that we need to maintain at most `n` states in our processing list at any time
where n is the number of nodes in the NFA. That is, for each input symbol, we
have a constant number of states to query.

The most important thing to understand in this algorithm for NFA graph
construction is that we start the construction from the end, that is the
accepting state. Then, as each node is constructed, new node is linked to
next nodes in processing. The second most important thing to understand this
algorithm for regular expression matching is that, each node represents the
starting state for the remaining string. That is, we can query next nodes to
check if the current remaining string will be accepted or rejected.

### Match

<!--
############
def match(rex, input_tokens):
    states = {rex(accepting)}
    for token in input_tokens:
        states = {a for state in states for a in state(token)}
    return any('ACCEPT' in state(None) for state in states)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(rex, input_tokens):
    states = {rex(accepting)}
    for token in input_tokens:
        states = {a for state in states for a in state(token)}
    return any(&#x27;ACCEPT&#x27; in state(None) for state in states)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we build our NFA graph.

### Lit
Let us take the simplest case: A literal such as `a`.
We represent the literal by a function that accepts the character, and returns
back a state in the NFA. The idea is that this NFA can accept or reject the
remaining string. So, it needs a continuation, which is given as the next
state. The NFA will continue with the next state only if the parsing of the
current symbol succeeds. So we have an inner function `parse` that does that.

<!--
############
def Lit(token):
    def node(rnfa):
        def parse(c: str): return [rnfa] if token == c else []
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Lit(token):
    def node(rnfa):
        def parse(c: str): return [rnfa] if token == c else []
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
An accepting state is just a sentinel, and we define it with `Lit`.

<!--
############
accepting = Lit(None)('ACCEPT')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
accepting = Lit(None)(&#x27;ACCEPT&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Epsilon

An epsilon matches nothing. That is, it passes any string it receives
without modification to the next state.
(It could also be written as `lambda s: return s`)

<!--
############
def Epsilon():
    def node(state):
        def parse(c: str): return state(c)
        return parse
    return node


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Epsilon():
    def node(state):
        def parse(c: str): return state(c)
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### AndThen

AndThen is a meta construction that concatenates two regular expressions.
It accepts the given string if the given regular expressions (`rex1`, `rex2`)
accepts the given string when placed end to end.
The `rnfa` is the node to connect to after nodes represented by
`rex1 -> rex2`.
That is, the final NFA should look like `[rex1]->[rex2]->rnfa`.

Note: I use a `[]` to represent a node, and no `[]` when I specify the
remaining NFA. For example, `[xxx]` represents the node in the NFA, while
`xxx` is the NFA starting with the node `xxx`

 
From the perspective of the node `[rex1]`, it can accept the remaining string
if its own matching succeeds on the given string and the remaining string can
be matched by the NFA `rex2(rnfa)` i.e, the NFA produced by calling `rex2`
with argument `rnfa`. That is, `[rex1]->rex2(rnfa)`,
which is same as `rex1(rex2(rnfa))` --- the NFA constructed by calling the
function sequence `rex1(rex2(rnfa))`.
 
The functions are expanded to make it easy to understand. The node may as well
have had `rex1(rex2(rnfa))` as the return value.

<!--
############
def AndThen(rex1, rex2):
    def node(rnfa):
        state1 = rex1(rex2(rnfa))
        def parse(c: str): return state1(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def AndThen(rex1, rex2):
    def node(rnfa):
        state1 = rex1(rex2(rnfa))
        def parse(c: str): return state1(c)
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### OrElse

The OrElse construction allows either one of the regular expressions to
match the given symbol. That is, we are trying to represent parallel
processing of `[rex1] -> rnfa || [rex2] -> rnfa`, or equivalently
`rex1(rnfa) || rex2(rnfa)`.

<!--
############
def OrElse(rex1, rex2):
    def node(rnfa):
        state1, state2 = rex1(rnfa), rex2(rnfa)
        def parse(c: str): return state1(c) + state2(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def OrElse(rex1, rex2):
    def node(rnfa):
        state1, state2 = rex1(rnfa), rex2(rnfa)
        def parse(c: str): return state1(c) + state2(c)
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Star
Finally, the Star is defined similar to OrElse. Note that unlike the context
free grammar, we do not allow unrestricted recursion. We only allow tail
recursion in the star form.
In Star, we are trying to represent
`rnfa || [rex] -> [Star(rex)] -> rnfa`.
Since the `parse` is a function that closes
over the passed in `rex` and `rnfa`, we can use that directly. That is
`Star(rex)(rnfa) == parse`. Hence, this becomes 
`rnfa || [rex] -> parse`, which is written equivalently as
`rnfa || rex(parse)`.

<!--
############
def Star(rex):
    def node(rnfa):
        def parse(c: str): return rnfa(c) + rex(parse)(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Star(rex):
    def node(rnfa):
        def parse(c: str): return rnfa(c) + rex(parse)(c)
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
X = Lit('X')
Y = Lit('Y')
Z = Lit('Z')
X_Y = OrElse(X,Y)
Y_X = OrElse(X,Y)
ZX_Y = AndThen(Z, OrElse(X,Y))
assert not match(X, 'XY')
assert match(X_Y, 'X')
assert match(Y_X, 'Y')
assert not match(X_Y, 'Z')
assert match(ZX_Y, 'ZY')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
X = Lit(&#x27;X&#x27;)
Y = Lit(&#x27;Y&#x27;)
Z = Lit(&#x27;Z&#x27;)
X_Y = OrElse(X,Y)
Y_X = OrElse(X,Y)
ZX_Y = AndThen(Z, OrElse(X,Y))
assert not match(X, &#x27;XY&#x27;)
assert match(X_Y, &#x27;X&#x27;)
assert match(Y_X, &#x27;Y&#x27;)
assert not match(X_Y, &#x27;Z&#x27;)
assert match(ZX_Y, &#x27;ZY&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Object Based Implementation

This machinery is a bit complex to understand due to the multiple levels of
closures. I have found such constructions easier to understand if I think of
them in terms of objects. So, here is an attempt.
First, the Re class that defines the interface.

<!--
############
class Re:
    def trans(self, rnfa): pass
    def parse(self, c: str): pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Re:
    def trans(self, rnfa): pass
    def parse(self, c: str): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Match
The match is slightly modified to account for the new Re interface.

<!--
############
def match(rex, instr):
    states = {rex.trans(accepting)}
    for c in instr:
        states = {a for state in states for a in state.parse(c)}
    return any('ACCEPT' in state.parse(None) for state in states)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(rex, instr):
    states = {rex.trans(accepting)}
    for c in instr:
        states = {a for state in states for a in state.parse(c)}
    return any(&#x27;ACCEPT&#x27; in state.parse(None) for state in states)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Lit
We separate out the construction of object, connecting it to the remaining
NFA (`trans`)

<!--
############
class Lit(Re):
    def __init__(self, char): self.char = char

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return [self.rnfa] if self.char == c else []

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Lit(Re):
    def __init__(self, char): self.char = char

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return [self.rnfa] if self.char == c else []
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
An accepting node is a node that requires no input. It is a simple sentinel

<!--
############
accepting = Lit(None).trans('ACCEPT')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
accepting = Lit(None).trans(&#x27;ACCEPT&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define our matching algorithm. The idea is to start with the
constructed NFA as the single thread, feed it our string, and check whether
the result contains the accepted state.
Let us test this.

<!--
############
X = Lit('X')
assert match(X, 'X')
assert not match(X, 'Y')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
X = Lit(&#x27;X&#x27;)
assert match(X, &#x27;X&#x27;)
assert not match(X, &#x27;Y&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### AndThen

<!--
############
class AndThen(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def trans(self, rnfa):
        state2 = self.rex2.trans(rnfa)
        self.state1 = self.rex1.trans(state2)
        return self

    def parse(self, c: str):
        return self.state1.parse(c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class AndThen(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def trans(self, rnfa):
        state2 = self.rex2.trans(rnfa)
        self.state1 = self.rex1.trans(state2)
        return self

    def parse(self, c: str):
        return self.state1.parse(c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
Y = Lit('Y')
XY = AndThen(X,Y)
YX = AndThen(Y, X)
assert match(XY,'XY')
assert not match(YX, 'XY')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Y = Lit(&#x27;Y&#x27;)
XY = AndThen(X,Y)
YX = AndThen(Y, X)
assert match(XY,&#x27;XY&#x27;)
assert not match(YX, &#x27;XY&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### OrElse

Next, we want to match alternations.
The important point here is that we want to
pass on the next state if either of the parses succeed.

<!--
############
class OrElse(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def trans(self, rnfa):
        self.state1, self.state2 = self.rex1.trans(rnfa), self.rex2.trans(rnfa)
        return self

    def parse(self, c: str):
        return self.state1.parse(c) + self.state2.parse(c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class OrElse(Re):
    def __init__(self, rex1, rex2): self.rex1, self.rex2 = rex1, rex2

    def trans(self, rnfa):
        self.state1, self.state2 = self.rex1.trans(rnfa), self.rex2.trans(rnfa)
        return self

    def parse(self, c: str):
        return self.state1.parse(c) + self.state2.parse(c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
Z = Lit('Z')
X_Y = OrElse(X,Y)
Y_X = OrElse(X,Y)
ZX_Y = AndThen(Z, OrElse(X,Y))
assert match(X_Y, 'X')
assert match(Y_X, 'Y')
assert not match(X_Y, 'Z')
assert match(ZX_Y, 'ZY')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Z = Lit(&#x27;Z&#x27;)
X_Y = OrElse(X,Y)
Y_X = OrElse(X,Y)
ZX_Y = AndThen(Z, OrElse(X,Y))
assert match(X_Y, &#x27;X&#x27;)
assert match(Y_X, &#x27;Y&#x27;)
assert not match(X_Y, &#x27;Z&#x27;)
assert match(ZX_Y, &#x27;ZY&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Star
Star now becomes much easier to understand.

<!--
############
class Star(Re):
    def __init__(self, re): self.re = re

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return self.rnfa.parse(c) + self.re.trans(self).parse(c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Star(Re):
    def __init__(self, re): self.re = re

    def trans(self, rnfa):
        self.rnfa = rnfa
        return self

    def parse(self, c: str):
        return self.rnfa.parse(c) + self.re.trans(self).parse(c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
Z_ = Star(Lit('Z'))
assert match(Z_, '')
assert match(Z_, 'Z')
assert not match(Z_, 'ZA')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Z_ = Star(Lit(&#x27;Z&#x27;))
assert match(Z_, &#x27;&#x27;)
assert match(Z_, &#x27;Z&#x27;)
assert not match(Z_, &#x27;ZA&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Epsilon

We also define an epsilon expression.

<!--
############
class Epsilon(Re):
    def trans(self, state):
        self.state = state
        return self

    def parse(self, c: str):
        return self.state.parse(c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Epsilon(Re):
    def trans(self, state):
        self.state = state
        return self

    def parse(self, c: str):
        return self.state.parse(c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us test this.

<!--
############
E__ = Epsilon()
assert match(E__, '')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
E__ = Epsilon()
assert match(E__, &#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can have quite complicated expressions. Again, test suite from
[here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).

<!--
############
complicated = AndThen(Star(OrElse(AndThen(Lit('a'), Lit('b')), AndThen(Lit('a'), AndThen(Lit('x'), Lit('y'))))), Lit('z'))
assert not match(complicated, '')
assert match(complicated, 'z')
assert match(complicated, 'abz')
assert not match(complicated, 'ababaxyab')
assert match(complicated, 'ababaxyabz')
assert not match(complicated, 'ababaxyaxz')


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
complicated = AndThen(Star(OrElse(AndThen(Lit(&#x27;a&#x27;), Lit(&#x27;b&#x27;)), AndThen(Lit(&#x27;a&#x27;), AndThen(Lit(&#x27;x&#x27;), Lit(&#x27;y&#x27;))))), Lit(&#x27;z&#x27;))
assert not match(complicated, &#x27;&#x27;)
assert match(complicated, &#x27;z&#x27;)
assert match(complicated, &#x27;abz&#x27;)
assert not match(complicated, &#x27;ababaxyab&#x27;)
assert match(complicated, &#x27;ababaxyabz&#x27;)
assert not match(complicated, &#x27;ababaxyaxz&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What about constructing regular expression literals? For that let us start
with a simplified grammar

<!--
############
import string

TERMINAL_SYMBOLS = list(string.digits +
                        string.ascii_letters)

RE_GRAMMAR = {
    '<start>' : [ ['<regex>'] ],
    '<regex>' : [
        ['<cex>', '|', '<regex>'],
        ['<cex>', '|'],
        ['<cex>']
    ],
    '<cex>' : [
        ['<exp>', '<cex>'],
        ['<exp>']
    ],
    '<exp>': [
        ['<unitexp>'],
        ['<regexstar>'],
        ['<regexplus>'],
    ],
    '<unitexp>': [
        ['<alpha>'],
        ['<parenexp>'],
    ],
    '<parenexp>': [ ['(', '<regex>', ')'], ],
    '<regexstar>': [ ['<unitexp>', '*'], ],
    '<alpha>' : [[c] for c in TERMINAL_SYMBOLS]
}
RE_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string

TERMINAL_SYMBOLS = list(string.digits +
                        string.ascii_letters)

RE_GRAMMAR = {
    &#x27;&lt;start&gt;&#x27; : [ [&#x27;&lt;regex&gt;&#x27;] ],
    &#x27;&lt;regex&gt;&#x27; : [
        [&#x27;&lt;cex&gt;&#x27;, &#x27;|&#x27;, &#x27;&lt;regex&gt;&#x27;],
        [&#x27;&lt;cex&gt;&#x27;, &#x27;|&#x27;],
        [&#x27;&lt;cex&gt;&#x27;]
    ],
    &#x27;&lt;cex&gt;&#x27; : [
        [&#x27;&lt;exp&gt;&#x27;, &#x27;&lt;cex&gt;&#x27;],
        [&#x27;&lt;exp&gt;&#x27;]
    ],
    &#x27;&lt;exp&gt;&#x27;: [
        [&#x27;&lt;unitexp&gt;&#x27;],
        [&#x27;&lt;regexstar&gt;&#x27;],
        [&#x27;&lt;regexplus&gt;&#x27;],
    ],
    &#x27;&lt;unitexp&gt;&#x27;: [
        [&#x27;&lt;alpha&gt;&#x27;],
        [&#x27;&lt;parenexp&gt;&#x27;],
    ],
    &#x27;&lt;parenexp&gt;&#x27;: [ [&#x27;(&#x27;, &#x27;&lt;regex&gt;&#x27;, &#x27;)&#x27;], ],
    &#x27;&lt;regexstar&gt;&#x27;: [ [&#x27;&lt;unitexp&gt;&#x27;, &#x27;*&#x27;], ],
    &#x27;&lt;alpha&gt;&#x27; : [[c] for c in TERMINAL_SYMBOLS]
}
RE_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is ofcourse a very limited grammar that only supports basic
regular expression operations concatenation, alternation, and star.
We can use earley parser for parsing any given regular expressions

<!--
############
my_re = '(ab|c)*'
re_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(re_parser.parse_on(my_re, RE_START))[0]
fuzzer.display_tree(parsed_expr)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;(ab|c)*&#x27;
re_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(re_parser.parse_on(my_re, RE_START))[0]
fuzzer.display_tree(parsed_expr)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us define the basic machinary. The parse function parses
the regexp string to an AST, and to_re converts the AST
to the regexp structure.

<!--
############
class RegexToLiteral:
    def __init__(self, all_terminal_symbols=TERMINAL_SYMBOLS):
        self.parser = earleyparser.EarleyParser(RE_GRAMMAR)
        self.counter = 0
        self.all_terminal_symbols = all_terminal_symbols

    def parse(self, inex):
        parsed_expr = list(self.parser.parse_on(inex, RE_START))[0]
        return parsed_expr

    def to_re(self, inex):
        parsed = self.parse(inex)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        lit = self.convert_regex(children[0])
        return lit

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral:
    def __init__(self, all_terminal_symbols=TERMINAL_SYMBOLS):
        self.parser = earleyparser.EarleyParser(RE_GRAMMAR)
        self.counter = 0
        self.all_terminal_symbols = all_terminal_symbols

    def parse(self, inex):
        parsed_expr = list(self.parser.parse_on(inex, RE_START))[0]
        return parsed_expr

    def to_re(self, inex):
        parsed = self.parse(inex)
        key, children = parsed
        assert key == &#x27;&lt;start&gt;&#x27;
        assert len(children) == 1
        lit = self.convert_regex(children[0])
        return lit
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The unit expression may e an alpha or a parenthesised expression.

<!--
############
class RegexToLiteral(RegexToLiteral):
    def convert_unitexp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<alpha>':
            return self.convert_alpha(children[0])
        elif key == '<parenexp>':
            return self.convert_regexparen(children[0])
        else:
            assert False
        assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def convert_unitexp(self, node):
        _key, children = node
        key = children[0][0]
        if key == &#x27;&lt;alpha&gt;&#x27;:
            return self.convert_alpha(children[0])
        elif key == &#x27;&lt;parenexp&gt;&#x27;:
            return self.convert_regexparen(children[0])
        else:
            assert False
        assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The alpha gets converted to a Lit.

<!--
############
class RegexToLiteral(RegexToLiteral):
    def convert_alpha(self, node):
        key, children = node
        assert key == '<alpha>'
        return Lit(children[0][0])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def convert_alpha(self, node):
        key, children = node
        assert key == &#x27;&lt;alpha&gt;&#x27;
        return Lit(children[0][0])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
check it has worked

<!--
############
my_re = 'a'
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, '<unitexp>'))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_unitexp(parsed_expr)
print(l)
assert match(l, 'a')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;a&#x27;
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;unitexp&gt;&#x27;))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_unitexp(parsed_expr)
print(l)
assert match(l, &#x27;a&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we write the exp and cex conversions. cex gets turned into AndThen

<!--
############
class RegexToLiteral(RegexToLiteral):
    def convert_exp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<unitexp>':
            return self.convert_unitexp(children[0])
        elif key == '<regexstar>':
            return self.convert_regexstar(children[0])
        else:
            assert False
        assert False

    def convert_cex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_exp(child)
        if children:
            child, *children = children
            lit2 = self.convert_cex(child)
            lit = AndThen(lit,lit2)
        return lit

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def convert_exp(self, node):
        _key, children = node
        key = children[0][0]
        if key == &#x27;&lt;unitexp&gt;&#x27;:
            return self.convert_unitexp(children[0])
        elif key == &#x27;&lt;regexstar&gt;&#x27;:
            return self.convert_regexstar(children[0])
        else:
            assert False
        assert False

    def convert_cex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_exp(child)
        if children:
            child, *children = children
            lit2 = self.convert_cex(child)
            lit = AndThen(lit,lit2)
        return lit
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
check it has worked

<!--
############
my_re = 'ab'
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, '<cex>'))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_cex(parsed_expr)
print(l)
assert match(l, 'ab')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;ab&#x27;
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;cex&gt;&#x27;))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_cex(parsed_expr)
print(l)
assert match(l, &#x27;ab&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 Next, we write the regex, which gets converted to OrElse

<!--
############
class RegexToLiteral(RegexToLiteral):
    def convert_regexparen(self, node):
        key, children = node
        assert len(children) == 3
        return self.convert_regex(children[1])

    def convert_regex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_cex(child)
        if children:
            if len(children) == 1: # epsilon
                assert children[0][0] == '|'
                lit = OrElse(lit, Epsilon())
            else:
                pipe, child, *children = children
                assert pipe[0] == '|'
                lit2 = self.convert_regex(child)
                lit = OrElse(lit, lit2)
        return lit

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def convert_regexparen(self, node):
        key, children = node
        assert len(children) == 3
        return self.convert_regex(children[1])

    def convert_regex(self, node):
        key, children = node
        child, *children = children
        lit = self.convert_cex(child)
        if children:
            if len(children) == 1: # epsilon
                assert children[0][0] == &#x27;|&#x27;
                lit = OrElse(lit, Epsilon())
            else:
                pipe, child, *children = children
                assert pipe[0] == &#x27;|&#x27;
                lit2 = self.convert_regex(child)
                lit = OrElse(lit, lit2)
        return lit
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
check it has worked

<!--
############
my_re = 'a|b|c'
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_regex(parsed_expr)
print(l)
assert match(l, 'a')
assert match(l, 'b')
assert match(l, 'c')
my_re = 'ab|c'
parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
l = RegexToLiteral().convert_regex(parsed_expr)
assert match(l, 'ab')
assert match(l, 'c')
assert not match(l, 'a')
my_re = 'ab|'
parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
l = RegexToLiteral().convert_regex(parsed_expr)
assert match(l, 'ab')
assert match(l, '')
assert not match(l, 'a')


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;a|b|c&#x27;
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;regex&gt;&#x27;))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_regex(parsed_expr)
print(l)
assert match(l, &#x27;a&#x27;)
assert match(l, &#x27;b&#x27;)
assert match(l, &#x27;c&#x27;)
my_re = &#x27;ab|c&#x27;
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;regex&gt;&#x27;))[0]
l = RegexToLiteral().convert_regex(parsed_expr)
assert match(l, &#x27;ab&#x27;)
assert match(l, &#x27;c&#x27;)
assert not match(l, &#x27;a&#x27;)
my_re = &#x27;ab|&#x27;
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;regex&gt;&#x27;))[0]
l = RegexToLiteral().convert_regex(parsed_expr)
assert match(l, &#x27;ab&#x27;)
assert match(l, &#x27;&#x27;)
assert not match(l, &#x27;a&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally the Star.

<!--
############
class RegexToLiteral(RegexToLiteral):
    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        lit = self.convert_unitexp(children[0])
        return Star(lit)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        lit = self.convert_unitexp(children[0])
        return Star(lit)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
check it has worked

<!--
############
my_re = 'a*b'
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, '<regex>'))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_regex(parsed_expr)
print(l)
assert match(l, 'b')
assert match(l, 'ab')
assert not match(l, 'abb')
assert match(l, 'aab')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;a*b&#x27;
print(my_re)
regex_parser = earleyparser.EarleyParser(RE_GRAMMAR)
parsed_expr = list(regex_parser.parse_on(my_re, &#x27;&lt;regex&gt;&#x27;))[0]
fuzzer.display_tree(parsed_expr)
l = RegexToLiteral().convert_regex(parsed_expr)
print(l)
assert match(l, &#x27;b&#x27;)
assert match(l, &#x27;ab&#x27;)
assert not match(l, &#x27;abb&#x27;)
assert match(l, &#x27;aab&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 Wrapping everything up.

<!--
############
class RegexToLiteral(RegexToLiteral):
    def match(self, re, instring):
        lit = self.to_re(re)
        return match(lit, instring)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToLiteral(RegexToLiteral):
    def match(self, re, instring):
        lit = self.to_re(re)
        return match(lit, instring)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
check it has worked

<!--
############
my_re = 'a*b'
assert RegexToLiteral().match(my_re, 'ab')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;a*b&#x27;
assert RegexToLiteral().match(my_re, &#x27;ab&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).
 

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).


