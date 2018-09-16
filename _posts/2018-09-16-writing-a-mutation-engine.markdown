---
published: true
title: A simple split-stream mutation engine in Python
layout: post
comments: true
tags: parsing
---

This post describes the implementation of a simple forking mutation-testing engine in Python. It is based on our paper [Topsy-Turvy: A Smarter and Faster Parallelization of Mutation Analysis](/publications#gopinath2016topsy).

For those who are wondering what _program-mutation_ or _mutation-analysis_ or _mutation-testing_ is all about, the idea is really simple. Given a simple program -- such as the triangle program given below.
```python
# triangle.py
import sys
def triangle(a, b, c):
    if a == b:
        if b == c:
            return 'Equilateral'
        else:
            return 'Isosceles'
    else:
        if b == c:
            return "Isosceles"
        else:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"
```
We want to ensure that the program works as advertised. What we do is to write a test suite for that, as we do below
```python
def test():
    e1 = triangle(1,1,1)
    assert e1 == 'Equilateral'
    e2 = triangle(1,2,1)
    assert e2 == 'Isosceles'
    e3 = triangle(2,2,1)
    assert e3 == 'Isosceles'
    e4 = triangle(2,1,2)
    assert e4 == 'Isosceles'
    e4 = triangle(1,2,3)
    assert e5 == 'Scalene'
    print('Success')
```
However, how do we know that the test suite we wrote was good enough? One solution is to look at coverage (any of structural coverage measures such as statement, branch, path etc.). Unfortunately, coverage is an insufficient metric. In particular, coverage does not change even if the assertions were deleted from the test suite.

[Program mutation](https://en.wikipedia.org/wiki/Mutation_testing) is one of the best methods we have for evaluating the quality of a test suite. It involves exhaustively seeding all small faults, and evaluating whether the test suite is able to catch (_kill the mutant_ in mutation terminology) each of them.
While program mutation has [a number of limitations](/publications/#gopinath2017on), it is still better than simply using the coverage to estimate quality of a test suite.

However, writing a full-featured program mutation test suite is not an easy undertaking. Further, the particular environment in which your program runs can make existing program mutation engines difficult or impossible to use. While simple [regular expression based mutant generators](https://github.com/vrthra/c-mutate) can work, such an approach has a number of problems:

* The number of stillborn mutations (mutants that do not even compile) produced
  
  Regular expression based mutant generators can produce a large quantity of these stillborn mutants which should not count toward the mutation score. These mutants need to be compiled, and eliminated individually.
* Lack of coverage-based optimization
  
  A simple optimization is to only execute test cases against mutants where the mutations are in the execution path of the test case. This however requires much additional infrastructure for executing, and collecting coverage of individual test cases, and filtering non-relevant mutants.

A simple technique called _split-stream execution_ can greatly simplify and speed up mutant execution. The idea is that, rather than startup each mutant separately, and run the entire test suite against them, execute the common (non-mutated) portion of the code first on any test case until the program execution comes to a mutation site. When the execution traverses a site of mutation, fork the execution into a different process, and continue the execution in the child process such that the child process behaves as if the mutation has happened in that particular site. The parent process on the other hand, behaves as if the mutation has not happened, and proceeds to the next mutation site. Each mutation site is one-shot. That is, the forking happens only on the first traversal.

So, how do we achieve that? A relatively easy solution is to wrap any potential mutation site in a function call, and within that function, decide whether we want to fork or not. That is, we want to transform our triangle program as below. The function is called `mutate` in the execution context `f` and takes two parameters. The first parameter is a unique id for the mutation. Here, I pass in a tuple corresponding to the line number and column offset of the mutation site. The second parameter is the result of operation. Here I let the operation proceed on the common portion. However, if needed, we can wrap the operation in a _lambda_, and decide whether to execute it or not in the child. The `verify` is again similar. It takes the assertion result, and the line number as parameters.

```python
# mutated.triangle.py

import mu
forking_context = mu.Forker()

import sys

def triangle(a, b, c):
    if f.mutate((4, 7), (a == b)):
        if forking_context.mutate((5, 11), (b == c)):
            return 'Equilateral'
        else:
            return 'Isosceles'
    elif forking_context.mutate((10, 11), (b == c)):
        return 'Isosceles'
    elif forking_context.mutate((13, 15), (a == c)):
        return 'Isosceles'
    else:
        return 'Scalene'

def test():
    e1 = triangle(1, 1, 1)
    forking_context.verify((e1 == 'Equilateral'), 20)
    e2 = triangle(1, 2, 1)
    forking_context.verify((e2 == 'Isosceles'), 22)
    e3 = triangle(2, 2, 1)
    forking_context.verify((e3 == 'Isosceles'), 24)
    e4 = triangle(2, 1, 2)
    forking_context.verify((e4 == 'Isosceles'), 26)
    e5 = triangle(1, 2, 3)
    forking_context.verify((e5 == 'Scalene'), 28)
    print('Success')

def main():
    test()
main()

forking_context.waitfor()
```
Once we have transformed our program (if you are using it for larger programs, be sure to use better variable name than `forking_context`, and it is not shadowed) all it remains is to do actual analysis
```python
# mu.py
import os
import sys
registry = {}

class Forker():
    def __init__(self):
        self.r = -1
        self.pids = []
        # all the parent assertions should match because no mutations in parent
        self.myid = '<parent>'

    def fork(self, myid):
        self.r = os.fork()
        if self.r != 0:
            self.pids.append(self.r)
        else:
            self.myid = myid
            self.pids = []

    def is_child(self):
        return self.r == 0

    def is_parent(self):
        return self.r != 0

    def waitfor(self):
        for i in self.pids:
            if i == -1: continue
            os.waitpid(i, 0)

    def mypid(self):
        return os.getpid()

    def mutate(self, myid, cond_result):
        if self.is_parent():
            # have we spawned this mutant before?
            if myid in registry: return cond_result

            # No we have not spawned.
            self.fork(myid)
            registry[myid] = result_mutate(cond_result) if self.is_child() else cond_result
            return registry[myid]
        else:
            # we are in a continuing execution of a child.
            # get what we replaced the thing at the child
            # originally if this was our mutation. Else just
            # return the original
            return registry.get(myid) or cond_result

    def verify(self, tcond, ln):
        with open(".pids/%s" % self.mypid(), 'a+') as f:
            print("%s: %s (True?) at %d" % (self.myid, str(tcond), ln) , file=f)

def result_mutate(v): return not v
```
Now, simply executing `python3 mutated.triangle.py` will execute our mutation analysis ,and leave the results under `.pids`. each pid should have at least one result that differs from the parent to indicate its killing. If not, it is still alive.

```bash
$ python3 mutated.triangle.py
$ for i in .pids/*; do echo $i; cat $i; echo; done
.pids/14370
<parent>: True (True?) at 20
<parent>: True (True?) at 22
<parent>: True (True?) at 24
<parent>: True (True?) at 26
<parent>: True (True?) at 28

.pids/14371
(4, 7): False (True?) at 20 <-- killed (e.g)
(4, 7): True (True?) at 22
(4, 7): True (True?) at 24
(4, 7): True (True?) at 26
(4, 7): True (True?) at 28

.pids/14372
(5, 11): False (True?) at 20
(5, 11): True (True?) at 22
(5, 11): True (True?) at 24
(5, 11): True (True?) at 26
(5, 11): False (True?) at 28

.pids/14373
(10, 11): True (True?) at 22
(10, 11): False (True?) at 24 
(10, 11): False (True?) at 26
(10, 11): False (True?) at 28

.pids/14374
(13, 15): False (True?) at 22
(13, 15): False (True?) at 24
(13, 15): False (True?) at 26
(13, 15): False (True?) at 28
```
Here, we can see that each `PID` has at least one (in many cases more than one) difference from the parent. Hence we have `100%` mutation score.

Now, all that remains is to see how to transform our `triangle.py` to `mutated.triangle.py`. In Python, it is relatively simple using the `astunparse` and `astmonkey` modules.
```python
import sys
from textwrap import dedent
import ast
import astunparse
from astmonkey import transformers

def slurp(src):
    with open(src) as x: return x.read()

class ForkingTransformer(ast.NodeTransformer):
    def visit_If(self, node):
        muid = (node.test.lineno, node.test.col_offset)
        node = ast.If(ast.Call(ast.Name('forking_context.mutate', None),
            [ast.Str(muid), node.test],
            []), node.body, node.orelse)
        return self.generic_visit(node)

    def visit_Assert(self, node):
        node = ast.Expr(ast.Call(ast.Name('forking_context.verify', None),
                                 [node.test, ast.Num(node.test.lineno)], []))
        return self.generic_visit(node)

def forking_transform(src):
    return astunparse.unparse(ForkingTransformer().visit(ast.parse(src)))

def main(args):
    tmpl = """
    import mu
    forking_context = mu.Forker()

    %s

    forking_context.waitfor()
    """
    t = ast.parse(slurp(args[1]))
    print(dedent(tmpl).strip() % forking_transform(t))

if __name__ == '__main__': main(sys.argv)
```
All that we are doing here is transforming _If_ nodes and _Assert_ nodes, which is sufficient for this example.
This code should be easy enough to understand. If you would like to extend it, the [greentreesnakes](https://greentreesnakes.readthedocs.io/en/latest/) is a great resource for documentation of the AST module in python.
(The `astunparse` module uses `async` as an argument, and hence is not python 3.7 ready. You may need to apply [this patch](https://github.com/simonpercivall/astunparse/commit/72bcac2fc408408c7cd07043c392fd9932714604.patch) if you are using Python 3.7)

I note that this was simply an example on how to implement a split-stream execution environment. Python does have a number of program-mutation tools, which includes [cosmic-ray](https://cosmic-ray.readthedocs.io/en/latest/), [mutpy](https://github.com/mutpy/mutpy), and [mutmut](https://pypi.org/project/mutmut/). Another is [xmutant](https://github.com/vrthra/xmutant.py) -- a rather researchy, but plain vanila mutation engine that mutates bytecodes that I wrote some time back. `xmutant.py` incorporates checking for `immortal-mutants` using random sampling. (Immortal, or equivalent mutants are mutants where the syntactic difference we injected did not result in an actual fault).
