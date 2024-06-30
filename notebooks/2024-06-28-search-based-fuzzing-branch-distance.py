# ---
# published: true
# title: Search Based Fuzzing -- Computing Branch Distance
# layout: post
# comments: true
# tags: search fuzzing
# categories: post
# ---
# 
# Search Based Fuzzing involves generating various candidate inputs for a given
# program, identifying the inputs with the best score in some metric of
# effectiveness and choosing them for the next iteration so that one can
# iteratively improve the fitness of the given population of inputs.
# In the [previous post](/post/2024/06/27/search-based-fuzzing-approach-level/)
# I discussed how you can score inputs using *approach level*. 
# 
# Approach level (or approximation level) is reasonable to compute the
# distance we have to traverse to reach a given node. However, in fuzzing, we
# also find that just reaching a node is insufficient. In several cases, the
# branch taken by an input execution determines if we can make progress. That is
# given several inputs, each of which reach a given decision node, we need to
# prioritize those inputs that are closest to switching to an uncovered branch.
# To do this, we use what is called the *Branch Distance*. This was first
# proposed by Tracey et al[^tracey1998]. In this post, I will discuss how to
# compute branch distance for computing the fitness score of an input in
# flipping a branch condition.
# 
# As before, we start by importing the prerequisites

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pycfg-0.0.1-py2.py3-none-any.whl 
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl

import random
import simplefuzzer as fuzzer
import pycfg
import metacircularinterpreter as mci

import pydot
import textwrap as tw

# Given a set of variables (corresponding to an input) and a conditional,
# the branch distance measures the distance to the critical branch being
# true or false, where the critical branch is the branch where control flow
# diverged from reaching the target. That is, if an input diverged at
# a critical branch, then the distance to the conditional being true or false.
# It is given by the following translation:
# 
# | Element   | Value   |
# |-----------|---------|
# |   Boolean | if True then 0 else K |
# |   a = b   | if abs(a-b) = 0 then 0 else abs(a-b) + K  |
# |   a != b  | if abs(a-b) != 0 then 0 else K            |
# |   a < b   | if a-b < 0 then 0 else (a-b) + K          |
# |   a <= b  | if a-b <= 0 then 0 else (a-b) + K         |
# |   a > b   | if b-a >  0 then 0 else (b-a) + K         |
# |   a > b   | if b-a >= 0 then 0 else (b-a) + K         |
# |   a **or** b  | min(bdistance(a), bdistance(b))                     |
# |   a **and** b  | bdistance(a) + bdistance(b)                         |
# |   **not** a     | Negation is moved inward and propagated over a  |
# 
# 
# K is a penalty constant which lets you fine tune the penalty of being wrong. Typically K=1
# 
# Once you have the branch distance, you need to **normalize** it to make it less than 1. A common formula used is
# 
# $$ normalize(branchD) = 1 − 1.001^{(−branchD)} $$
# 
# Another [^arcuri2011] is
# 
# $$ \frac{branchD}{branchD + \beta} $$
# 
# where $$ branchD $$ is the value to be normalized and $$ \beta $$ is a constant value you choose.
# 
# Finally, $$ fitness = approach level + normalized branch distance $$
# 
# Let us consider a few examples.
 
def test_me(x, y):
    if x == 2 * (y + 1):
        return True
    else:
        return False

# say we have the following inputs
if __name__ == '__main__':
    X, Y = 1, 1
    v = test_me(X, Y)
    print(v)

# As per the above formula, the `bdistance` is
if __name__ == '__main__':
    for (x_, y_) in [(1, 1)]:
        v = abs(x_ - 2*(y_+1))
        print(v)

# Can we move it forward? Let us consider a few neighbours.
if __name__ == '__main__':
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

if __name__ == '__main__':
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

if __name__ == '__main__':
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

if __name__ == '__main__':
    v = test_me(-2, -2)
    print(v)

# Can we automate this approach? Interestingly, this is quite easy.
# We can reuse the approach in [metacircular interpreter](/post/2019/12/07/python-mci/)
# and change the semantics to conform to our requirement.

class BDInterpreter(mci.PySemantics):
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise mci.SynErr('walk: Not Implemented in %s' % type(node))


# Here is a quick check to show that the meta-circular interpreter works expected.

if __name__ == '__main__':
    bd = BDInterpreter({'a':10, 'b':20}, [])
    r = bd.eval('a+b')
    print(r)

# Next, let us redefine the interesting bits according to the table we provided.
# Provided below again for easy reference.
# 
# | Element   | Value   |
# |-----------|---------|
# |   Boolean | if True then 0 else K |
# |   a = b   | if abs(a-b) = 0 then 0 else abs(a-b) + K  |
# |   a != b  | if abs(a-b) != 0 then 0 else K            |
# |   a < b   | if a-b < 0 then 0 else (a-b) + K          |
# |   a <= b  | if a-b <= 0 then 0 else (a-b) + K         |
# |   a > b   | if b-a >  0 then 0 else (b-a) + K         |
# |   a > b   | if b-a >= 0 then 0 else (b-a) + K         |
# |   a **or** b  | min(bdistance(a), bdistance(b))                     |
# |   a **and** b  | bdistance(a) + bdistance(b)                         |
# |   **not** a     | Negation is moved inward and propagated over a  |

import ast

# For ease of discourse, let us consider the last one first. The idea is that if
# one encounters a `not` unary, then it should be moved inward to the outermost
# comparison, which gets flipped. Any `and` or `or` that is encountered gets
# switched.
# 
# The same also gets applied when we want to take the `false` branch of a
# conditional. So, let us create a new class, that given an expression `e`,
# transforms it as equivalent to `not e`, but without the `not` in the
# expression, and normalizes it. So, we need two classes that correspond to
# both distributing any internal `not` and negating a given expression.
# 
# ## DistributeNot
# 
# This class normalizes any `Not` by distributing it inside.
# First the infrastructure.

class Distribute(mci.PyMCInterpreter):
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            v = getattr(self,res)(node)
            return v
        raise mci.SynErr('walk: Not Implemented in %s' % type(node))


# When we find `module`, and `expr` there is no change, because they are
# just wrapper classes
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

# We need two classes, the `DistributeNot` which is responsible for
# non-negated and `NegateDistributeNot` which is responsible for carrying
# a negated expression.

class DistributeNot(Distribute): pass

class NegateDistributeNot(Distribute): pass


# Simple things like names and constants should get translated directly by
# the `DistributeNot`, but should be negated by `NegateDistributeNot`.
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

# Check that it works.

if __name__ == '__main__':
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

# What should happen for `not a`? It should get pushed into a
# if possible. That is, `DistributeNot` should then switch
# to `NegateDistributeNot`. However, if we are starting with
# `NegateDistributeNot`, then it is already carrying a negation,
# so it should switch to `DistributeNot`.

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

# Check that it works
if __name__ == '__main__':
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


# What should happen for `a and b`? It should get turned into
# `not (a and b)` which is `(not a) or (not b)`, but only
# on NegateDistributeNot. For DistributeNot, there is no change.

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

# Check that it works
if __name__ == '__main__':
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

# The on_compare method is simply itself in `DistributeNot` because we do not
# expect a `not` inside the compare. The `NegateDistributeNot` switches to
# its anti operation. We also do not have to `walk` inside the comparators
# because we do not expect either boolean operators or other comparators inside
# comparators.

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

# Check that it works
if __name__ == '__main__':
    v = NegateDistributeNot()
    myast = v.parse('a > b')
    res = v.walk(myast)
    assert ast.unparse(res) == 'a <= b'
    myast = v.parse('a <= b')
    res = v.walk(myast)
    assert ast.unparse(res) == 'a > b'


# We can now define branch distance conversions in `BDInterpreter` class.
# we want the comparator to have access to K. So we pass in `self`.

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

# We need one more step. That is, we need to run the evaluator. In the below, we
# assume that we need to take the `True` branch. Hence, we use the `normal_ast` to
# find how to flip from the `False` branch. If on the other hand, you want to flip
# from the `True` branch to `False` branch of the conditional, then you need the
# `negated_ast`.

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

# Let us try to make it run. Note that the examples would typically be present
# in code as
# ```
# if a>b:
#    # target branch
#    print('Hello') 
# else:
#    # this branch was taken.
#    print('Hi') 
# ```

if __name__ == '__main__':
    bd = BDInterpreter({'a':10, 'b':20}, [])
    r = bd.eval('a>b')
    assert r == 11
    r = bd.eval('not a>b')
    assert r == 0
    r = bd.eval('a>b or a<(20*b)')
    assert r == 0
    r = bd.eval('not (a>b or a< (2 + b))')
    assert r == 13

# [^tracey1998]: Tracey, Nigel, et al. "An automated framework for structural test-data generation." IEEE International Conference on Automated Software Engineering, 1998.
# [^arcuri2011]: Andrea Arcuri "It really does matter how you normalize the branch distance in search-based software testing" 2011

