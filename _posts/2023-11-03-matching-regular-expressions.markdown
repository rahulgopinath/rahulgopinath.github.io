---
published: true
title: Efficient Matching with Regular Expressions
layout: post
comments: true
tags: parsing
categories: post
---
In the previous posts, I talked about converting a regular grammar to a
deterministic regular grammar (DRG) equivalent to a DFA and mentioned that
it was one of the ways to ensure that there is no exponential worstcase
for regular expression matching. However, this is not the only way to
avoid exponential worstcase due to backtracking for regular expressions.
A possible solution is the [Thompson algorithm described here](https://swtch.com/~rsc/regexp/regexp1.html).
The idea is that, rather than backtracking, for any given NFA, parallely
track all possible threads. The idea here is that, for a given regular
expression with size n, excluding parenthesis, an NFA with n states is
sufficient to represent it. Furthermore, given n states in an NFA, one
never needs to track more than n parallel threads while parsing. I
recently found a rather elegant and tiny implementation of this in Python
[here](https://github.com/darius/sketchbook/blob/master/regex/nfa.py).
This is an attempt to document my understanding of this code.

We start with importing the prerequisites

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
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

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
Note my [post](/post/2020/03/02/combinatory-parsing/) on simple combinatory
parsing. This construction is similar in spirit to that idea. The essential
idea is that a given node should be able to accept or reject a given sequence
of characters. So, let us take the simplest case: A literal such as `a`.
We represent the literal by a function that accepts the character, and returns
back a node in the NFA. The idea is that this NFA can accept or reject the
remaining string. So, it needs a continuation, which is given as the next
state. The NFA will continue with the next state only if the parsing of the
current symbol succeeds. So we have an inner function `parse` that does that.

<!--
############
def Lit(char):
    def node(nxtstate):
        def parse(c: str):
            return [nxtstate] if char == c else []
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Lit(char):
    def node(nxtstate):
        def parse(c: str):
            return [nxtstate] if char == c else []
        return parse
    return node
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
An accepting node is a node that requires no input. It is a simple sentinel

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
Next, we define our matching algorithm. The idea is to start with the
constructed NFA as the single thread, feed it our string, and check whether
the result contains the accepted state.

<!--
############
def match(rex, instr):
    nfa = rex(accepting)
    states = [nfa]
    for c in instr:
        states = list(set([a for state in states for a in state(c)]))
    return any('ACCEPT' in state(None) for state in states)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(rex, instr):
    nfa = rex(accepting)
    states = [nfa]
    for c in instr:
        states = list(set([a for state in states for a in state(c)]))
    return any(&#x27;ACCEPT&#x27; in state(None) for state in states)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
Next, we want to match two regular expressions. We define AndThen that
sequences two regular expressions. The idea is to construct the NFA from the
end, where we will connect `rex1() -> rex2() -> nxtstate`
Note that we are constructing the NFA in the `node()` function.
That is, the `node()` is given the next state to move
into on successful parse (i.e `nxtstate`). We connect the nxtstate to the
end of rex2 by passing it as an argument. The node rex2 is then connected to
rex1 by passing the resultant state as the next state to rex1.
The functions are expanded to make it easy to understand. The node may aswell
have had rex1(rex2(nxtstate)) as the return value.

<!--
############
def AndThen(rex1, rex2):
    def node(nxtstate):
        state2 = rex2(nxtstate)
        state1 = rex1(state2)
        def parse(c: str):
            return state1(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def AndThen(rex1, rex2):
    def node(nxtstate):
        state2 = rex2(nxtstate)
        state1 = rex1(state2)
        def parse(c: str):
            return state1(c)
        return parse
    return node
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
Next, we want to match alternations. As before we define the node function,
and inside it the parse function. The important point here is that we want to
pass on the next state if either of the parses succeed.

<!--
############
def OrElse(rex1, rex2):
    def node(nxtstate):
        state1, state2 = rex1(nxtstate), rex2(nxtstate)
        def parse(c: str):
            return state1(c) + state2(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def OrElse(rex1, rex2):
    def node(nxtstate):
        state1, state2 = rex1(nxtstate), rex2(nxtstate)
        def parse(c: str):
            return state1(c) + state2(c)
        return parse
    return node
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
Finally, the Star is defined similar to OrElse. Note that unlike the context
free grammar, we do not allow unrestricted recursion. We only allow tail
recursion in the star form.

<!--
############
def Star(re):
    def node(nxtstate):
        def parse(c: str):
            return nxtstate(c) + re(parse)(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Star(re):
    def node(nxtstate):
        def parse(c: str):
            return nxtstate(c) + re(parse)(c)
        return parse
    return node
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
We also define an epsilon expression.

<!--
############
def Epsilon():
    def node(state):
        def parse(c: str):
            return state(c)
        return parse
    return node

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Epsilon():
    def node(state):
        def parse(c: str):
            return state(c)
        return parse
    return node
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
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).
 

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-03-matching-regular-expressions.py).


