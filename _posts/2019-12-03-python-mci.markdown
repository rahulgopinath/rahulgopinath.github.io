---
published: true
title: Python Meta Circular Interpteter
layout: post
comments: true
tags: mci
---

A meta-circular interpreter is an interpteter for a language that is written in that language itself. The
MCI can implement a subset or superset of the host language.

### Uses of a Meta Circular Interpreter

Why should one want to write a meta-circular interpteter? Writing such an interpteter gives you
a large amount of control over how the code is executed. Further, it also gives you a way to track
the execution as it proceeds. Using a meta-circular interpteter, one can:

* Write a concolic interpteter that tracks the concrete execution
* Extract coverage
* Extract the control flow graph, and execution path through the graph
* Extract the call graph of execution
* Write a symbolc execution engine
* Write a taint tracker that will not be confused by indirect control flow
* Extend the host language with new features
* Reduce the capabilities exposed by the host language (e.g. no system calls).

I will be showing how to do these things in the upcoming posts. 

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


### The MCI class

```python
class ExprInterpreter:
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise Exception('walk: Not Implemented %s' % type(node))
```

### Implementations of various statements.

```python
class ExprInterpreter(ExprInterpreter):
    def on_module(self, node):
        """
        Module(stmt* body)
        """
        # return value of module is the last statement
        res = None
        for p in node.body:
            res = self.walk(p)
        return res

    def on_list(self, node):
        """
        List(elts)
        """
        res = []
        for p in node.elts:
            v = self.walk(p)
            res.append(v)
        return res

    def on_tuple(self, node):
        """
        Tuple(elts)
        """
        res = []
        for p in node.elts:
            v = self.walk(p)
            res.append(v)
        return res

    def on_str(self, node):
        """
        Str(string s) -- a string as a pyobject
        """
        return node.s

    def on_num(self, node):
        """
        Num(object n) -- a number as a PyObject.
        """
        return node.n

    def on_index(self, node):
        return self.walk(node.value)

    def on_attribute(self, node):
        """
         | Attribute(expr value, identifier attr, expr_context ctx)
        """
        obj = self.walk(node.value)
        attr = node.attr
        return getattr(obj, attr)

    def on_subscript(self, node):
        """
         | Subscript(expr value, slice slice, expr_context ctx)
        """
        value = self.walk(node.value)
        slic = self.walk(node.slice)
        return value[slic]

    def on_name(self, node):
        """
        Name(identifier id, expr_context ctx)
        """
        return self.symtable[node.id]

    def on_expr(self, node):
        """
        Expr(expr value)
        """
        return self.walk(node.value)

    def on_compare(self, node):
        """
        Compare(expr left, cmpop* ops, expr* comparators)
        >>> expr = ExprInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('a < b')
        True
        >>> expr.eval('a > b')
        False
        """
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        return self.cmpop[type(op)](hd, tl)

    def on_unaryop(self, node):
        """
        UnaryOp(unaryop op, expr operand)
        >>> expr = ExprInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('-a')
        -1
        """
        return self.unaryop[type(node.op)](self.walk(node.operand))

    def on_boolop(self, node):
        """
        Boolop(boolop op, expr* values)
        >>> expr = ExprInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('a and b')
        2
        """
        return reduce(self.boolop[type(node.op)], [self.walk(n) for n in node.values])


    def on_binop(self, node):
        """
        BinOp(expr left, operator op, expr right)
        >>> expr = ExprInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('a + b')
        3
        """
        return self.binop[type(node.op)](self.walk(node.left), self.walk(node.right))
```

### Some of the control flow statements are modelled as exceptions.

```python
class Return(Exception):
    def __init__(self, val): self.__dict__.update(locals())
class Break(Exception):
    def __init__(self): pass
class Continue(Exception):
    def __init__(self): pass
```

#### Using them

```python
class ExprInterpreter(ExprInterpreter):
    def on_return(self, node):
        raise Return(self.walk(node.value))

    def on_break(self, node):
        """FP Stye dummy"""
        raise Break(self.walk(node.value))

    def on_continue(self, node):
        raise Continue(self.walk(node.value))

    def on_pass(self, node):
        pass
```

### The assignment


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

### Hooking up the symbol table

```python
class ExprInterpreter(ExprInterpreter):
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

#### Using it.

```python
class ExprInterpreter(ExprInterpreter):

    def on_assign(self, node):
        """
        Assign(expr* targets, expr value)
        """
        value = self.walk(node.value)
        tgts = [t.id for t in node.targets]
        if len(tgts) == 1:
            self.symtable[tgts[0]] = value
        else:
            for t,v in zip(tgts, value):
                self.symtable[t] = v

    def on_import(self, node):
        """
        Import(alias* names)
        """
        for im in node.names:
            if im.name == 'sys': continue
            v = importlib.import_module(im.name)
            self.symtable[im.name] = v
            
    def on_call(self, node):
        func = self.walk(node.func)
        args = [self.walk(a) for a in node.args]
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
                    res = self.walk(i)
                return res
            except Return as e:
                return e.val
            finally:
                self.symtable.pop()
```

```python
class ExprInterpreter(ExprInterpreter):
    def on_while(self, node):
        """
        While(expr test, stmt* body, stmt* orelse)
        """
        while self.walk(node.test):
            try:
                for b in node.body:
                    self.walk(b)
            except Break:
                break
            except Continue:
                continue

    def on_if(self, node):
        """
        If(expr test, stmt* body, stmt* orelse)
        """
        v = self.walk(node.test)
        body = node.body if v else node.orelse
        if body:
            res = None
            for b in body:
                res = self.walk(b)

    def on_functiondef(self, node):
        fname = node.name
        args = node.args
        returns = node.returns
        self.symtable[fname] = [fname, args, returns, node.body]
```

### The evaluator

```python
    def eval(self, src):
        return self.walk(ast.parse(src))
```

### The driver

```python
if __name__ == '__main__':
    expr = ExprInterpreter({'__name__':'__main__'}, sys.argv[1:]) #json.loads(sys.argv[2])
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
