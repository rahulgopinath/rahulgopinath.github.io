---
published: true
title: Search Based Fuzzing with Branch Distance
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
proposed by Tracey et al[^tracey1998]. In this post, I will discuss how to
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
# That is, as per this computation, 0, 0 is closer to flipping the branch.
# let us explore the neighbours again
X, Y, v = 0, 0, 2
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
# again
X, Y, v = -1, -1, 1
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
# at this point, we have a zero
v = test_me(-2, -2)
print(v)

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
# That is, as per this computation, 0, 0 is closer to flipping the branch.
# let us explore the neighbours again
X, Y, v = 0, 0, 2
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
# again
X, Y, v = -1, -1, 1
minxy = [(X, Y, v)]
xs = [X-1, X, X+1]
ys = [Y-1, Y, Y+1]
for (x_, y_) in zip(xs, ys):
    v_ = abs(x_ - 2*(y_+1))
    print(v_)
    minxy.append((x_, y_, v_))
print(minxy)
# at this point, we have a zero
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
Let us now run it and see.

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

BoolOP = {
          ast.And: lambda a, b: a + b,
          ast.Or: lambda a, b: min(a, b)
}

UnaryOP = {
          ast.Invert: lambda a: ~a,
          ast.Not: None, # should not exist
          ast.UAdd: lambda a: +a,
          ast.USub: lambda a: -a
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import ast

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

BoolOP = {
          ast.And: lambda a, b: a + b,
          ast.Or: lambda a, b: min(a, b)
}

UnaryOP = {
          ast.Invert: lambda a: ~a,
          ast.Not: None, # should not exist
          ast.UAdd: lambda a: +a,
          ast.USub: lambda a: -a
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now insert these into our `BDInterpreter` class.

<!--
############
from functools import reduce
class BDInterpreter(BDInterpreter):
    def unaryop(self, val): return UnaryOP[val]
    def cmpop(self, val): return CmpOP[val]
    def boolop(self, val): return BoolOP[val]

    def on_unaryop(self, node):
        return self.unaryop(type(node.op))(self.walk(node.operand))

    # we want the comparator to have access to K. So we pass in `self`.
    def on_compare(self, node):
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        return self.cmpop(type(op))(self, hd, tl)

    def on_boolop(self, node):
        return reduce(self.boolop(type(node.op)), [self.walk(n) for n in node.values])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from functools import reduce
class BDInterpreter(BDInterpreter):
    def unaryop(self, val): return UnaryOP[val]
    def cmpop(self, val): return CmpOP[val]
    def boolop(self, val): return BoolOP[val]

    def on_unaryop(self, node):
        return self.unaryop(type(node.op))(self.walk(node.operand))

    # we want the comparator to have access to K. So we pass in `self`.
    def on_compare(self, node):
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        return self.cmpop(type(op))(self, hd, tl)

    def on_boolop(self, node):
        return reduce(self.boolop(type(node.op)), [self.walk(n) for n in node.values])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need one more step. That is, if we find a `Not`, we need to distributed it
inside, inverting any comparisons. For that, we need a Normalizer class

<!--
############
class BDInterpreter(BDInterpreter):
    def eval(self, src, K=1):
        self.K = K
        return self.walk(self.normalize(self.parse(src)))

    def normalize(self, myast):
        return Normalizer().walk(myast)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BDInterpreter(BDInterpreter):
    def eval(self, src, K=1):
        self.K = K
        return self.walk(self.normalize(self.parse(src)))

    def normalize(self, myast):
        return Normalizer().walk(myast)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Normalizer

This class normalizes any `Not` by distributing it inside.
First the infrastructure.

<!--
############
class Normalizer(mci.PyMCInterpreter):
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            v = getattr(self,res)(node)
            return v
        raise mci.SynErr('walk: Not Implemented in %s' % type(node))

    def on_module(self, node):
        body = []
        for p in node.body:
            v = self.walk(p)
            body.append(v)
        v = ast.Module(body, node.type_ignores)
        ast.fix_missing_locations(v)
        return v

    def on_expr(self, node):
        v = ast.Expr(self.walk(node.value))
        ast.fix_missing_locations(v)
        return v

    def on_compare(self, node):
        # nothing to do, because we do not expect a `not`
        # inside the compare.
        return node

    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(v)
        v = ast.BoolOp(node.op, values)
        ast.fix_missing_locations(v)
        return v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Normalizer(mci.PyMCInterpreter):
    def walk(self, node):
        if node is None: return
        res = &quot;on_%s&quot; % node.__class__.__name__.lower()
        if hasattr(self, res):
            v = getattr(self,res)(node)
            return v
        raise mci.SynErr(&#x27;walk: Not Implemented in %s&#x27; % type(node))

    def on_module(self, node):
        body = []
        for p in node.body:
            v = self.walk(p)
            body.append(v)
        v = ast.Module(body, node.type_ignores)
        ast.fix_missing_locations(v)
        return v

    def on_expr(self, node):
        v = ast.Expr(self.walk(node.value))
        ast.fix_missing_locations(v)
        return v

    def on_compare(self, node):
        # nothing to do, because we do not expect a `not`
        # inside the compare.
        return node

    def on_boolop(self, node):
        values = []
        for v in node.values:
            r = self.walk(v)
            values.append(v)
        v = ast.BoolOp(node.op, values)
        ast.fix_missing_locations(v)
        return v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
if there is a not, then transform the inner nodes.

<!--
############
class Normalizer(Normalizer):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            v = self.convert_not(node.operand)
            ast.fix_missing_locations(v)
            return v
        else:
            return ast.UnaryOp(node.op, node.operand)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Normalizer(Normalizer):
    def on_unaryop(self, node):
        if isinstance(node.op, ast.Not):
            v = self.convert_not(node.operand)
            ast.fix_missing_locations(v)
            return v
        else:
            return ast.UnaryOp(node.op, node.operand)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, the actual conversion if `Not` is found

<!--
############
class Normalizer(Normalizer):
    def convert_compare(self, node):
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
        ast.fix_missing_locations(v)
        return v

    def convert_boolop(self, node):
        nots = [self.convert_not(v) for v in node.values]
        if isinstance(node.op, ast.Or):
            return ast.BoolOp(ast.And(), nots)
        elif isinstance(node.op, ast.And):
            return ast.BoolOp(ast.Or(), nots)
        else:
            assert False

    def convert_not(self, node):
        if isinstance(node, ast.Compare):
            return self.convert_compare(node)
        elif isinstance(node, ast.BoolOp):
            return self.convert_boolop(node)
        assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Normalizer(Normalizer):
    def convert_compare(self, node):
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
        ast.fix_missing_locations(v)
        return v

    def convert_boolop(self, node):
        nots = [self.convert_not(v) for v in node.values]
        if isinstance(node.op, ast.Or):
            return ast.BoolOp(ast.And(), nots)
        elif isinstance(node.op, ast.And):
            return ast.BoolOp(ast.Or(), nots)
        else:
            assert False

    def convert_not(self, node):
        if isinstance(node, ast.Compare):
            return self.convert_compare(node)
        elif isinstance(node, ast.BoolOp):
            return self.convert_boolop(node)
        assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try to make it run

<!--
############
bd = BDInterpreter({'a':10, 'b':20}, [])
r = bd.eval('not a>b')
assert r == 0
r = bd.eval('a>b')
assert r == 11
r = bd.eval('a>b or a<(20*b)')
assert r == 0
r = bd.eval('not (a>b or a< (2 + b))')
assert r == 13


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
bd = BDInterpreter({&#x27;a&#x27;:10, &#x27;b&#x27;:20}, [])
r = bd.eval(&#x27;not a&gt;b&#x27;)
assert r == 0
r = bd.eval(&#x27;a&gt;b&#x27;)
assert r == 11
r = bd.eval(&#x27;a&gt;b or a&lt;(20*b)&#x27;)
assert r == 0
r = bd.eval(&#x27;not (a&gt;b or a&lt; (2 + b))&#x27;)
assert r == 13
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^tracey1998]: Tracey, Nigel, et al. "An automated framework for structural test-data generation." IEEE International Conference on Automated Software Engineering, 1998.
[^arcuri2011]: Andrea Arcuri "It really does matter how you normalize the branch distance in search-based software testing" 2011

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2024-06-28-search-based-fuzzing-branch-distance.py).


