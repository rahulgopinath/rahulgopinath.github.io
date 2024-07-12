---
published: true
title: Search Based Fuzzing -- Computing Branch Distance
layout: post
comments: true
tags: search fuzzing
categories: post
---

Search Based Fuzzing involves generating various candidate inputs for a given
program, identifying the inputs with the best score in some metric of
effectiveness and choosing them for the next iteration so that one can
iteratively improve the fitness of the given population of inputs.
In the [previous post](/post/2024/06/27/search-based-fuzzing-approach-level/)
I discussed how you can score inputs using *approach level*. 

Approach level (or approximation level) is reasonable to compute the
distance we have to traverse to reach a given node. However, in fuzzing, we
also find that just reaching a node is insufficient. In several cases, the
branch taken by an input execution determines if we can make progress. That is
given several inputs, each of which reach a given decision node, we need to
prioritize those inputs that are closest to switching to an uncovered branch.
To do this, we use what is called the *Branch Distance*. This was first
proposed by Bogdan Korel in 1990 [^korel1990]. In this post, I will discuss how to
compute branch distance for computing the fitness score of an input in
flipping a branch condition.

As before, we start by importing the prerequisites

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
<li><a href="https://rahul.gopinath.org/py/pycfg-0.0.1-py2.py3-none-any.whl">pycfg-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/08/python-controlflow/">The Python Control Flow Graph</a>".</li>
<li><a href="https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl">pydot-1.4.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl">metacircularinterpreter-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/07/python-mci/">Python Meta Circular Interpreter</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/pycfg-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import random
import simplefuzzer as fuzzer
import pycfg
import metacircularinterpreter as mci

import pydot
import textwrap as tw

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
import simplefuzzer as fuzzer
import pycfg
import metacircularinterpreter as mci

import pydot
import textwrap as tw
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given a set of variables (corresponding to an input) and a conditional,
the branch distance measures the distance to the critical branch being
true or false, where the critical branch is the branch where control flow
diverged from reaching the target. That is, if an input diverged at
a critical branch, then the distance to the conditional being true or false.
It is given by the following translation:

| Element   | Value   |
|-----------|---------|
|   Boolean | if True then 0 else K |
|   a = b   | if abs(a-b) = 0 then 0 else abs(a-b) + K  |
|   a != b  | if abs(a-b) != 0 then 0 else K            |
|   a < b   | if a-b < 0 then 0 else (a-b) + K          |
|   a <= b  | if a-b <= 0 then 0 else (a-b) + K         |
|   a > b   | if b-a >  0 then 0 else (b-a) + K         |
|   a > b   | if b-a >= 0 then 0 else (b-a) + K         |
|   a **or** b  | min(bdistance(a), bdistance(b))                     |
|   a **and** b  | bdistance(a) + bdistance(b)                         |
|   **not** a     | Negation is moved inward and propagated over a  |


K is a penalty constant which lets you fine tune the penalty of being wrong. Typically K=1

Once you have the branch distance, you need to **normalize** it to make it less than 1. A common formula used is

$$ normalize(branchD) = 1 − 1.001^{(−branchD)} $$

Another [^arcuri2011] is

$$ \frac{branchD}{branchD + \beta} $$

where $$ branchD $$ is the value to be normalized and $$ \beta $$ is a constant value you choose.

Finally, $$ fitness = approach level + normalized branch distance $$

Let us consider a few examples.

<!--
############
def test_me(x, y):
    if x == 2 * (y + 1):
        return True
    else:
        return False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def test_me(x, y):
    if x == 2 * (y + 1):
        return True
    else:
        return False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
say we have the following inputs

<!--
############
X, Y = 1, 1
v = test_me(X, Y)
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
X, Y = 1, 1
v = test_me(X, Y)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As per the above formula, the `bdistance` is

<!--
############
for (x_, y_) in [(1, 1)]:
    v = abs(x_ - 2*(y_+1))
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for (x_, y_) in [(1, 1)]:
    v = abs(x_ - 2*(y_+1))
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Can we move it forward? Let us consider a few neighbours.

<!--
############
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, as per this computation, 0, 0 is closer to flipping the branch.
let us explore the neighbours again

<!--
############
X, Y, v = 0, 0, 2
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
X, Y, v = 0, 0, 2
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
again

<!--
############
X, Y, v = -1, -1, 1
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
X, Y, v = -1, -1, 1
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
at this point, we have a zero

<!--
############
v = test_me(-2, -2)
print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = test_me(-2, -2)
print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Can we automate this approach? Interestingly, this is quite easy.
We can reuse the approach in [metacircular interpreter](/post/2019/12/07/python-mci/)
and change the semantics to conform to our requirement.

<!--
############
class BDInterpreter(mci.PySemantics):
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise mci.SynErr('walk: Not Implemented in %s' % type(node))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BDInterpreter(mci.PySemantics):
    def walk(self, node):
        if node is None: return
        res = &quot;on_%s&quot; % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise mci.SynErr(&#x27;walk: Not Implemented in %s&#x27; % type(node))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is a quick check to show that the meta-circular interpreter works expected.

<!--
############
bd = BDInterpreter({'a':10, 'b':20}, [])
r = bd.eval('a+b')
print(r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
bd = BDInterpreter({&#x27;a&#x27;:10, &#x27;b&#x27;:20}, [])
r = bd.eval(&#x27;a+b&#x27;)
print(r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, let us redefine the interesting bits according to the table we provided.
Provided below again for easy reference.

| Element   | Value   |
|-----------|---------|
|   Boolean | if True then 0 else K |
|   a = b   | if abs(a-b) = 0 then 0 else abs(a-b) + K  |
|   a != b  | if abs(a-b) != 0 then 0 else K            |
|   a < b   | if a-b < 0 then 0 else (a-b) + K          |
|   a <= b  | if a-b <= 0 then 0 else (a-b) + K         |
|   a > b   | if b-a >  0 then 0 else (b-a) + K         |
|   a > b   | if b-a >= 0 then 0 else (b-a) + K         |
|   a **or** b  | min(bdistance(a), bdistance(b))                     |
|   a **and** b  | bdistance(a) + bdistance(b)                         |
|   **not** a     | Negation is moved inward and propagated over a  |

<!--
############
import ast

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import ast
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For ease of discourse, let us consider the last one first. The idea is that if
one encounters a `not` unary, then it should be moved inward to the outermost
comparison, which gets flipped. Any `and` or `or` that is encountered gets
switched.

The same also gets applied when we want to take the `false` branch of a
conditional. So, let us create a new class, that given an expression `e`,
transforms it as equivalent to `not e`, but without the `not` in the
expression, and normalizes it. So, we need two classes that correspond to
both distributing any internal `not` and negating a given expression.

## DistributeNot

This class normalizes any `Not` by distributing it inside.
First the infrastructure.

<!--
############
class Distribute(mci.PyMCInterpreter):
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            v = getattr(self,res)(node)
            return v
        raise mci.SynErr('walk: Not Implemented in %s' % type(node))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Distribute(mci.PyMCInterpreter):
    def walk(self, node):
        if node is None: return
        res = &quot;on_%s&quot; % node.__class__.__name__.lower()
        if hasattr(self, res):
            v = getattr(self,res)(node)
            return v
        raise mci.SynErr(&#x27;walk: Not Implemented in %s&#x27; % type(node))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
When we find `module`, and `expr` there is no change, because they are
just wrapper classes

<!--
############
class Distribute(Distribute):
    def fix(self, v):
        v.lineno = 0
        v.col_offset = 0
        return v

    def on_module(self, node):
        body = []
        for p in node.body:
            v = self.walk(p)
            body.append(v)
        v = ast.Module(body, node.type_ignores)
        return self.fix(v)

    def on_expr(self, node):
        e = self.walk(node.value)
        v = ast.Expr(e)
        return self.fix(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Distribute(Distribute):
    def fix(self, v):
        v.lineno = 0
        v.col_offset = 0
        return v

    def on_module(self, node):
        body = []
        for p in node.body:
            v = self.walk(p)
            body.append(v)
        v = ast.Module(body, node.type_ignores)
        return self.fix(v)

    def on_expr(self, node):
        e = self.walk(node.value)
        v = ast.Expr(e)
        return self.fix(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need two classes, the `DistributeNot` which is responsible for
non-negated and `NegateDistributeNot` which is responsible for carrying
a negated expression.

<!--
############
class DistributeNot(Distribute): pass

class NegateDistributeNot(Distribute): pass


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DistributeNot(Distribute): pass

class NegateDistributeNot(Distribute): pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Simple things like names and constants should get translated directly by
the `DistributeNot`, but should be negated by `NegateDistributeNot`.

<!--
############
class DistributeNot(DistributeNot):
    def on_name(self, node):
        return node

    def on_constant(self, node):
        return node

class NegateDistributeNot(NegateDistributeNot):
    def on_name(self, node):
        v = ast.UnaryOp(ast.Not(), node)
        return self.fix(v)

    def on_constant(self, node):
        if node.value == True:
            v = ast.Constant(False)
            return self.fix(v)
        if node.value == False:
            v = ast.Constant(True)
            return self.fix(v)
        v = ast.UnaryOp(ast.Not(), node)
        return self.fix(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DistributeNot(DistributeNot):
    def on_name(self, node):
        return node

    def on_constant(self, node):
        return node

class NegateDistributeNot(NegateDistributeNot):
    def on_name(self, node):
        v = ast.UnaryOp(ast.Not(), node)
        return self.fix(v)

    def on_constant(self, node):
        if node.value == True:
            v = ast.Constant(False)
            return self.fix(v)
        if node.value == False:
            v = ast.Constant(True)
            return self.fix(v)
        v = ast.UnaryOp(ast.Not(), node)
        return self.fix(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Check that it works.

<!--
############
v = DistributeNot()
myast = v.parse('a')
res = v.walk(myast)
assert ast.unparse(res) == 'a'

u = NegateDistributeNot()
myast = u.parse('a')
res = u.walk(myast)
assert ast.unparse(res) == 'not a'

myast = v.parse('True')
res = v.walk(myast)
assert ast.unparse(res) == 'True'

myast = v.parse('False')
res = v.walk(myast)
assert ast.unparse(res) == 'False'

myast = u.parse('True')
res = u.walk(myast)
assert ast.unparse(res) == 'False'

myast = u.parse('False')
res = u.walk(myast)
assert ast.unparse(res) == 'True'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = DistributeNot()
myast = v.parse(&#x27;a&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;a&#x27;

u = NegateDistributeNot()
myast = u.parse(&#x27;a&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;not a&#x27;

myast = v.parse(&#x27;True&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;True&#x27;

myast = v.parse(&#x27;False&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;False&#x27;

myast = u.parse(&#x27;True&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;False&#x27;

myast = u.parse(&#x27;False&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;True&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What should happen for `not a`? It should get pushed into a
if possible. That is, `DistributeNot` should then switch
to `NegateDistributeNot`. However, if we are starting with
`NegateDistributeNot`, then it is already carrying a negation,
so it should switch to `DistributeNot`.

<!--
############
class DistributeNot(DistributeNot):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            ne = NegateDistributeNot()
            v = ne.walk(node.operand)
            return v
        else:
            return self.walk(node)

class NegateDistributeNot(NegateDistributeNot):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            dn = DistributeNot()
            v = dn.walk(node.operand)
            return v
        else:
            return self.walk(node)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DistributeNot(DistributeNot):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            ne = NegateDistributeNot()
            v = ne.walk(node.operand)
            return v
        else:
            return self.walk(node)

class NegateDistributeNot(NegateDistributeNot):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            dn = DistributeNot()
            v = dn.walk(node.operand)
            return v
        else:
            return self.walk(node)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Check that it works

<!--
############
v = DistributeNot()
u = NegateDistributeNot()

myast = v.parse('not a')
res = v.walk(myast)
assert ast.unparse(res) == 'not a'

myast = v.parse('not True')
res = v.walk(myast)
assert ast.unparse(res) == 'False'

myast = u.parse('not a')
res = u.walk(myast)
assert ast.unparse(res) == 'a'

myast = u.parse('not True')
res = u.walk(myast)
assert ast.unparse(res) == 'True'


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = DistributeNot()
u = NegateDistributeNot()

myast = v.parse(&#x27;not a&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;not a&#x27;

myast = v.parse(&#x27;not True&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;False&#x27;

myast = u.parse(&#x27;not a&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;a&#x27;

myast = u.parse(&#x27;not True&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;True&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What should happen for `a and b`? It should get turned into
`not (a and b)` which is `(not a) or (not b)`, but only
on NegateDistributeNot. For DistributeNot, there is no change.

<!--
############
class DistributeNot(DistributeNot):
    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(r)
        v = ast.BoolOp(node.op, values)
        return self.fix(v)

class NegateDistributeNot(NegateDistributeNot):
    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(r)
        newop = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        v = ast.BoolOp(newop, values)
        return self.fix(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DistributeNot(DistributeNot):
    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(r)
        v = ast.BoolOp(node.op, values)
        return self.fix(v)

class NegateDistributeNot(NegateDistributeNot):
    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(r)
        newop = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        v = ast.BoolOp(newop, values)
        return self.fix(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Check that it works

<!--
############
v = DistributeNot()
myast = v.parse('a and b')
res = v.walk(myast)
assert ast.unparse(res) == 'a and b'
myast = v.parse('a or b')
res = v.walk(myast)
assert ast.unparse(res) == 'a or b'

u = NegateDistributeNot()
myast = u.parse('a and b')
res = u.walk(myast)
assert ast.unparse(res) == 'not a or not b'
myast = u.parse('a or b')
res = u.walk(myast)
assert ast.unparse(res) == 'not a and (not b)'

myast = v.parse('not (a and b)')
res = v.walk(myast)
assert ast.unparse(res) == 'not a or not b'
myast = v.parse('not (a or b)')
res = v.walk(myast)
assert ast.unparse(res) == 'not a and (not b)'

myast = u.parse('not (a and b)')
res = u.walk(myast)
assert ast.unparse(res) == 'a and b'
myast = u.parse('not (a or b)')
res = u.walk(myast)
assert ast.unparse(res) == 'a or b'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = DistributeNot()
myast = v.parse(&#x27;a and b&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;a and b&#x27;
myast = v.parse(&#x27;a or b&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;a or b&#x27;

u = NegateDistributeNot()
myast = u.parse(&#x27;a and b&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;not a or not b&#x27;
myast = u.parse(&#x27;a or b&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;not a and (not b)&#x27;

myast = v.parse(&#x27;not (a and b)&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;not a or not b&#x27;
myast = v.parse(&#x27;not (a or b)&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;not a and (not b)&#x27;

myast = u.parse(&#x27;not (a and b)&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;a and b&#x27;
myast = u.parse(&#x27;not (a or b)&#x27;)
res = u.walk(myast)
assert ast.unparse(res) == &#x27;a or b&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The on_compare method is simply itself in `DistributeNot` because we do not
expect a `not` inside the compare. The `NegateDistributeNot` switches to
its anti operation. We also do not have to `walk` inside the comparators
because we do not expect either boolean operators or other comparators inside
comparators.

<!--
############
class DistributeNot(DistributeNot):
    def on_compare(self, node):
        return node

class NegateDistributeNot(NegateDistributeNot):
    def on_compare(self, node):
        assert len(node.ops) == 1
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            v = ast.Compare(node.left, [ast.NotEq()], node.comparators)
        elif isinstance(op, ast.NotEq):
            v = ast.Compare(node.left, [ast.Eq()], node.comparators)
        elif isinstance(op, ast.Lt):
            v =  ast.Compare(node.left, [ast.GtE()], node.comparators)
        elif isinstance(op, ast.Gt):
            v =  ast.Compare(node.left, [ast.LtE()], node.comparators)
        elif isinstance(op, ast.GtE):
            v = ast.Compare(node.left, [ast.Lt()], node.comparators)
        elif isinstance(op, ast.LtE):
            v = ast.Compare(node.left, [ast.Gt()], node.comparators)
        elif isinstance(op, ast.In):
            v = ast.Compare(node.left, [ast.NotIn()], node.comparators)
        elif isinstance(op, ast.NotIn):
            v = ast.Compare(node.left, [ast.In()], node.comparators)
        else:
            assert False
        return self.fix(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DistributeNot(DistributeNot):
    def on_compare(self, node):
        return node

class NegateDistributeNot(NegateDistributeNot):
    def on_compare(self, node):
        assert len(node.ops) == 1
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            v = ast.Compare(node.left, [ast.NotEq()], node.comparators)
        elif isinstance(op, ast.NotEq):
            v = ast.Compare(node.left, [ast.Eq()], node.comparators)
        elif isinstance(op, ast.Lt):
            v =  ast.Compare(node.left, [ast.GtE()], node.comparators)
        elif isinstance(op, ast.Gt):
            v =  ast.Compare(node.left, [ast.LtE()], node.comparators)
        elif isinstance(op, ast.GtE):
            v = ast.Compare(node.left, [ast.Lt()], node.comparators)
        elif isinstance(op, ast.LtE):
            v = ast.Compare(node.left, [ast.Gt()], node.comparators)
        elif isinstance(op, ast.In):
            v = ast.Compare(node.left, [ast.NotIn()], node.comparators)
        elif isinstance(op, ast.NotIn):
            v = ast.Compare(node.left, [ast.In()], node.comparators)
        else:
            assert False
        return self.fix(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Check that it works

<!--
############
v = NegateDistributeNot()
myast = v.parse('a > b')
res = v.walk(myast)
assert ast.unparse(res) == 'a <= b'
myast = v.parse('a <= b')
res = v.walk(myast)
assert ast.unparse(res) == 'a > b'


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = NegateDistributeNot()
myast = v.parse(&#x27;a &gt; b&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;a &lt;= b&#x27;
myast = v.parse(&#x27;a &lt;= b&#x27;)
res = v.walk(myast)
assert ast.unparse(res) == &#x27;a &gt; b&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now define branch distance conversions in `BDInterpreter` class.
we want the comparator to have access to K. So we pass in `self`.

<!--
############
from functools import reduce
class BDInterpreter(BDInterpreter):
    def on_unaryop(self, node):
        v = self.walk(node.operand)
        UnaryOP = {
        ast.Invert: lambda self, a: self.K,
        ast.Not: lambda self, a: self.K,
        ast.UAdd: lambda self, a: self.K,
        ast.USub: lambda self, a: self.K
        }
        return UnaryOP[type(node.op)](v)

    def on_compare(self, node):
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        CmpOP = {
        ast.Eq: lambda self, a, b: 0 if a == b else math.abs(a - b) + self.K,
        ast.NotEq: lambda self, a, b: 0 if a != b else math.abs(a - b) + self.K,
        ast.Lt: lambda self, a, b: 0 if a < b else (a - b) + self.K,
        ast.LtE: lambda self, a, b:  0 if a <= b else (a - b) + self.K,
        ast.Gt: lambda self, a, b: 0 if a > b else (b - a) + self.K,
        ast.GtE: lambda self, a, b:  0 if a >= b else (b - a) + self.K,
        # The following are not in traditional branch distance,
        # but we can make an informed guess.
        ast.Is: lambda self, a, b: 0 if a is b else self.K,
        ast.IsNot: lambda self, a, b:  0 if a is not b else self.K,
        ast.In: lambda self, a, b: 0 if a in b else self.K,
        ast.NotIn: lambda self, a, b: 0 if a not in b else self.K,
        }
        return CmpOP[type(op)](self, hd, tl)

    def on_boolop(self, node):
        vl = [self.walk(n) for n in node.values]
        BoolOP = {
        ast.And: lambda a, b: a + b,
        ast.Or: lambda a, b: min(a, b)
        }
        return reduce(BoolOP[type(node.op)], vl)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from functools import reduce
class BDInterpreter(BDInterpreter):
    def on_unaryop(self, node):
        v = self.walk(node.operand)
        UnaryOP = {
        ast.Invert: lambda self, a: self.K,
        ast.Not: lambda self, a: self.K,
        ast.UAdd: lambda self, a: self.K,
        ast.USub: lambda self, a: self.K
        }
        return UnaryOP[type(node.op)](v)

    def on_compare(self, node):
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        CmpOP = {
        ast.Eq: lambda self, a, b: 0 if a == b else math.abs(a - b) + self.K,
        ast.NotEq: lambda self, a, b: 0 if a != b else math.abs(a - b) + self.K,
        ast.Lt: lambda self, a, b: 0 if a &lt; b else (a - b) + self.K,
        ast.LtE: lambda self, a, b:  0 if a &lt;= b else (a - b) + self.K,
        ast.Gt: lambda self, a, b: 0 if a &gt; b else (b - a) + self.K,
        ast.GtE: lambda self, a, b:  0 if a &gt;= b else (b - a) + self.K,
        # The following are not in traditional branch distance,
        # but we can make an informed guess.
        ast.Is: lambda self, a, b: 0 if a is b else self.K,
        ast.IsNot: lambda self, a, b:  0 if a is not b else self.K,
        ast.In: lambda self, a, b: 0 if a in b else self.K,
        ast.NotIn: lambda self, a, b: 0 if a not in b else self.K,
        }
        return CmpOP[type(op)](self, hd, tl)

    def on_boolop(self, node):
        vl = [self.walk(n) for n in node.values]
        BoolOP = {
        ast.And: lambda a, b: a + b,
        ast.Or: lambda a, b: min(a, b)
        }
        return reduce(BoolOP[type(node.op)], vl)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need one more step. That is, we need to run the evaluator. In the below, we
assume that we need to take the `True` branch. Hence, we use the `normal_ast` to
find how to flip from the `False` branch. If on the other hand, you want to flip
from the `True` branch to `False` branch of the conditional, then you need the
`negated_ast`.

<!--
############
class BDInterpreter(BDInterpreter):
    def eval(self, src, K=1):
        self.K = K
        myast = self.parse(src)
        #print(ast.unparse(myast))
        normal_ast = DistributeNot().walk(myast)
        #print(ast.unparse(normal_ast))
        myast = self.parse(src)
        negated_ast = NegateDistributeNot().walk(myast)
        #print(ast.unparse(negated_ast))
        # use the negated_ast if you are using the false branch.
        return self.walk(normal_ast)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BDInterpreter(BDInterpreter):
    def eval(self, src, K=1):
        self.K = K
        myast = self.parse(src)
        #print(ast.unparse(myast))
        normal_ast = DistributeNot().walk(myast)
        #print(ast.unparse(normal_ast))
        myast = self.parse(src)
        negated_ast = NegateDistributeNot().walk(myast)
        #print(ast.unparse(negated_ast))
        # use the negated_ast if you are using the false branch.
        return self.walk(normal_ast)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try to make it run. Note that the examples would typically be present
in code as
```
if a>b:
   # target branch
   print('Hello') 
else:
   # this branch was taken.
   print('Hi') 
```

<!--
############
bd = BDInterpreter({'a':10, 'b':20}, [])
r = bd.eval('a>b')
assert r == 11
r = bd.eval('not a>b')
assert r == 0
r = bd.eval('a>b or a<(20*b)')
assert r == 0
r = bd.eval('not (a>b or a< (2 + b))')
assert r == 13

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
bd = BDInterpreter({&#x27;a&#x27;:10, &#x27;b&#x27;:20}, [])
r = bd.eval(&#x27;a&gt;b&#x27;)
assert r == 11
r = bd.eval(&#x27;not a&gt;b&#x27;)
assert r == 0
r = bd.eval(&#x27;a&gt;b or a&lt;(20*b)&#x27;)
assert r == 0
r = bd.eval(&#x27;not (a&gt;b or a&lt; (2 + b))&#x27;)
assert r == 13
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^korel1990]: Bogdan Korel "Automated software test data generation." IEEE Transactions on software engineering, 1990
[^arcuri2011]: Andrea Arcuri "It really does matter how you normalize the branch distance in search-based software testing" 2011

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-06-28-search-based-fuzzing-branch-distance.py).


