---
published: true
title: Python Meta Circular Interpreter
layout: post
comments: true
tags: mci
---

I had previously [discussed](/post/2011/07/20/language7/) how one can implement
a programming language using big step semantics. In this post, I want to so
something similar. Here, we implement a meta-circular interpreter over Python.

A meta-circular interpreter is an interpreter for a language that is written
in that language itself. The MCI can implement a subset or superset of the host
language.

## Uses of a Meta Circular Interpreter

Why should one want to write a meta-circular interpreter? Writing such an
interpreter gives you a large amount of control over how the code is executed.
Further, it also gives you a way to track the execution as it proceeds.
Using a meta-circular interpreter, one can:

* Write a concolic interpreter that tracks the concrete execution
* Extract coverage
* Extract the control flow graph, and execution path through the graph
* Extract the call graph of execution
* Write a symbolic execution engine
* Write a taint tracker that will not be confused by indirect control flow
* Extend the host language with new features
* Reduce the capabilities exposed by the host language (e.g. no system calls).

I will be showing how to do these things in the upcoming posts. 

## The Implementation

First, we import everything we need.

```python
import string
import ast
import astunparse
import sys
import json
import builtins
from functools import reduce
import importlib
```

### The meta-circular-interpreter class

The `interpret()` method is at the heart of our interpreter. Given the AST,
It iterates through the statements, and evaluates each.

```python
class SynErr(Exception): pass

class PyMCInterpreter:
    def interpret(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise SynErr('walk: Not Implemented %s' % type(node))
```

We provide `eval()` which converts a given string to its AST, and calls
`interpret()`

```python
class PyMCInterpreter(PyMCInterpreter):
    def eval(self, src):
        return self.interpret(ast.parse(src))
```

#### The Pythonic data structures.

We reuse all Python data structures as below.

##### List(elts)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_list(self, node):
        res = []
        for p in node.elts:
            v = self.interpret(p)
            res.append(v)
        return res
```

##### Tuple(elts)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_tuple(self, node):
        res = []
        for p in node.elts:
            v = self.interpret(p)
            res.append(v)
        return res
```

##### Str(string s)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_str(self, node):
        return node.s
```

##### Number(object n)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_num(self, node):
        return node.n
```

##### Subscript(expr value, slice slice, expr_context ctx)

The tuple and list provide a means to access its elements via
subscript.

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_subscript(self, node):
        value = self.interpret(node.value)
        slic = self.interpret(node.slice)
        return value[slic]

    def on_index(self, node):
        return self.interpret(node.value)
```

##### Attribute(expr value, identifier attr, expr_context ctx)

Similar to subscript for arrays, objects provide attribute access.

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_attribute(self, node):
        obj = self.interpret(node.value)
        attr = node.attr
        return getattr(obj, attr)
```

#### Simple control flow statements

The `return`, `break` and `continue` are implemented as exceptions.

```python
class Return(Exception):
    def __init__(self, val): self.__dict__.update(locals())
class Break(Exception):
    def __init__(self): pass
class Continue(Exception):
    def __init__(self): pass
```

#### Implementation

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_return(self, node):
        raise Return(self.interpret(node.value))

    def on_break(self, node):
        raise Break(self.interpret(node.value))

    def on_continue(self, node):
        raise Continue(self.interpret(node.value))

    def on_pass(self, node):
        pass
```

#### The scope and symbol table

```python
class Sym:
    def __init__(self, table):
        self.table = [table]

    def push(self, v):
        self.table.append(v)
        return v

    def pop(self):
        return self.table.pop()

    def __getitem__(self, i):
        for t in reversed(self.table):
            if i in t:
                return t[i]
        return None

    def __setitem__(self, i, v):
        self.table[-1][i] = v

```

#### Hooking up the symbol table

```python
class PyMCInterpreter(PyMCInterpreter):
    def __init__(self, symtable, args):
        self.unaryop = {
          ast.Invert: lambda a: ~a,
          ast.Not: lambda a: not a,
          ast.UAdd: lambda a: +a,
          ast.USub: lambda a: -a
        }

        self.binop = {
          ast.Add: lambda a, b: a + b,
          ast.Sub: lambda a, b: a - b,
          ast.Mult:  lambda a, b: a * b,
          ast.MatMult:  lambda a, b: a @ b,
          ast.Div: lambda a, b: a / b,
          ast.Mod: lambda a, b: a % b,
          ast.Pow: lambda a, b: a ** b,
          ast.LShift:  lambda a, b: a << b,
          ast.RShift: lambda a, b: a >> b,
          ast.BitOr: lambda a, b: a | b,
          ast.BitXor: lambda a, b: a ^ b,
          ast.BitAnd: lambda a, b: a & b,
          ast.FloorDiv: lambda a, b: a // b
        }

        self.cmpop = {
          ast.Eq: lambda a, b: a == b,
          ast.NotEq: lambda a, b: a != b,
          ast.Lt: lambda a, b: a < b,
          ast.LtE: lambda a, b: a <= b,
          ast.Gt: lambda a, b: a > b,
          ast.GtE: lambda a, b: a >= b,
          ast.Is: lambda a, b: a is b,
          ast.IsNot: lambda a, b: a is not b,
          ast.In: lambda a, b: a in b,
          ast.NotIn: lambda a, b: a not in b
        }

        self.boolop = {
          ast.And: lambda a, b: a and b,
          ast.Or: lambda a, b: a or b
        }

        self.symtable = Sym(builtins.__dict__)
        self.symtable['sys'] = ast.Module(ast.Pass())
        setattr(self.symtable['sys'], 'argv', args)

        self.symtable.push(symtable)
```

#### The following statements use symbol table.

##### Name(identifier id, expr_context ctx)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_name(self, node):
        return self.symtable[node.id]
```
##### Assign(expr* targets, expr value)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_assign(self, node):
        value = self.interpret(node.value)
        tgts = [t.id for t in node.targets]
        if len(tgts) == 1:
            self.symtable[tgts[0]] = value
        else:
            for t,v in zip(tgts, value):
                self.symtable[t] = v
```

##### Call(expr func, expr* args, keyword* keywords)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_call(self, node):
        func = self.interpret(node.func)
        args = [self.interpret(a) for a in node.args]
        if str(type(func)) == "<class 'builtin_function_or_method'>":
            return func(*args)
        elif str(type(func)) == "<class 'type'>":
            return func(*args)
        else:
            [fname, argument, returns, fbody] = func
            argnames = [a.arg for a in argument.args]
            self.symtable.push(dict(zip(argnames, args)))
            try:
                for i in fbody:
                    res = self.interpret(i)
                return res
            except Return as e:
                return e.val
            finally:
                self.symtable.pop()
```

##### FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns, string? type_comment)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_functiondef(self, node):
        fname = node.name
        args = node.args
        returns = node.returns
        self.symtable[fname] = [fname, args, returns, node.body]
```

##### Import(alias* names)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_import(self, node):
        for im in node.names:
            if im.name == 'sys': continue
            v = importlib.import_module(im.name)
            self.symtable[im.name] = v
```

#### Arithmetics

##### Expr(expr value)
```python
class PyMCInterpreter(PyMCInterpreter):
    def on_expr(self, node):
        return self.interpret(node.value)

    def on_compare(self, node):
        hd = self.interpret(node.left)
        op = node.ops[0]
        tl = self.interpret(node.comparators[0])
        return self.cmpop[type(op)](hd, tl)

    def on_unaryop(self, node):
        return self.unaryop[type(node.op)](self.interpret(node.operand))

    def on_boolop(self, node):
        return reduce(self.boolop[type(node.op)], [self.interpret(n) for n in node.values])

    def on_binop(self, node):
        return self.binop[type(node.op)](self.interpret(node.left), self.interpret(node.right))
```

#### Other control flow operators

Only basic loops and conditionals -- `while()` and `if()` are implemented.

##### While(expr test, stmt* body, stmt* orelse)

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_while(self, node):
        while self.interpret(node.test):
            try:
                for b in node.body:
                    self.interpret(b)
            except Break:
                break
            except Continue:
                continue
```

##### If(expr test, stmt* body, stmt* orelse)

```python
class PyMCInterpreter(PyMCInterpreter):

    def on_if(self, node):
        v = self.interpret(node.test)
        body = node.body if v else node.orelse
        if body:
            res = None
            for b in body:
                res = self.interpret(b)
```

#### Modules

##### Module(stmt* body)

The complete AST is wrapped in a Module statement.

```python
class PyMCInterpreter(PyMCInterpreter):
    def on_module(self, node):
        # return value of module is the last statement
        res = None
        for p in node.body:
            res = self.interpret(p)
        return res
```


### The driver

```python
if __name__ == '__main__':
    expr = PyMCInterpreter({'__name__':'__main__'}, sys.argv[1:])
    v = expr.eval(open(sys.argv[1]).read())
    print(v)
```

### An example

```python
import sys
def triangle(a, b, c):
    if a == b:
        if b == c:
            return 'Equilateral'
        else:
            return 'Isosceless'
    else:
        if b == c:
            return "Isosceles"
        else:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"
def main(arg):
    v = arg.split(' ')
    v = triangle(int(v[0]), int(v[1]), int(v[2]))
    print(v)

if __name__ == '__main__':
    main(sys.argv[1])
    pass
```

### Usage

```shell
$ python3 interp.py triangle.py '1 2 3'
```

