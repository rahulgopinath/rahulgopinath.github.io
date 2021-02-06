---
published: true
title: A tiny and incomplete Python Virtual Machine
layout: post
comments: true
tags: vm
categories: post
---

*Tested in Python 3.6.8*

In the [previous post](/post/2019/12/07/python-mci/), I described how one can write
an interpreter for the Python language in Python. However, Python itself is not
implemented as a direct interpreter for the AST. Rather, Python AST is compiled
first, and turned to its own byte code. The byte code is interpreted by the
Python virtual machine. The Python virtual machine is implemented in C in the
case of CPython, in Java in the case of Jython, in WASM for Pyodide, and in
(reduced) Python in the case of PyPy.

The reason to use a virtual machine rather than directly interpreting the AST is
that, a large number of the higher level constructs map to a much smaller number
of lower level constructs. The lower level language (the bytecode) is also easier
to optimize, and is relatively more stable than the higher level language.

For our purposes, the lower level language also allows us to get away with
implementing our analysis techniques (such as taint analysis --- to be discussed
in later posts) on a much smaller number of primitives.

This post shows how to implement a very tiny Python virtual machine.
For more complete implementations, refer to the
[AOSA Book](https://www.aosabook.org/en/500L/a-python-interpreter-written-in-python.html)
or more complete and current [Byterun](https://github.com/nedbat/byterun) or
[my fork of byterun](https://github.com/vrthra-forks/bytevm).

We start as usual by importing the prerequisite packages. In the case of our
virtual machine, we have only the `dis` module to import. This module allows us
to disassemble Python bytecode from the compiled bytecode. Note that the package
[xdis](https://pypi.org/project/xdis/) may be a better module here (it is a drop
in replacement).

```python
import dis
```

As in the [MCI](/post/2019/12/07/python-mci/), we try to use as much of the
Python infrastructure as possible. Hence, we use the Python compiler to compile
source files into bytecode, and we only interpret the bytecode. One can
[compile](https://docs.python.org/3/library/functions.html#compile) source
strings to byte code as follows.

### Compilation

```python
my_code = compile('2+v', filename='', mode='eval')
```

The `mode` can be one of `eval` -- which evaluates expressions, `exec` --
which executes a sequence of statements, and `single` -- which is a limited form
of `exec`. Their difference can be seen below.


#### compile(mode=eval)

```python
>>> v = 1
>>> my_code = compile('2+v', filename='', mode='eval')
>>> dis.dis(my_code)
  1           0 LOAD_CONST               0 (2)
              2 LOAD_NAME                0 (v)
              4 BINARY_ADD
              6 RETURN_VALUE
>>> eval(my_code)
3
```

That is, the return value is the result of addition.

#### compile(mode=exec)

```python
>>> my_code = compile('2+v', filename='', mode='exec')
>>> dis.dis(my_code)
  1           0 LOAD_CONST               0 (2)
              2 LOAD_NAME                0 (v)
              4 BINARY_ADD
              6 POP_TOP
              8 LOAD_CONST               1 (None)
             10 RETURN_VALUE
>>> eval(my_code)
>>> 
```
The top of the stack is popped off on execution. That is,
it is treated as a statement. This mode is used for evaluating a series of
statements none of which will return a value when `eval()` is called.

```python
>>> my_code = compile('v=1;x=2+v', filename='', mode='eval')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "", line 1
    v=1;x=2+v
     ^
SyntaxError: invalid syntax
>>> my_code = compile('v=1;x=2+v', filename='', mode='exec')
>>> dis.dis(my_code)
  1           0 LOAD_CONST               0 (1)
              2 STORE_NAME               0 (v)
              4 LOAD_CONST               1 (2)
              6 LOAD_NAME                0 (v)
              8 BINARY_ADD
             10 STORE_NAME               1 (x)
             12 LOAD_CONST               2 (None)
             14 RETURN_VALUE
>>> eval(my_code)
>>> x
3
```

#### compile(mode=single)

The `single` mode is a restricted version of `exec`. It is applicable for a
single line *statement*, which can even be constructed by stitching multiple
statements together with semicolons.

```python
>>> my_code = compile('v=1\nx=2+v\nx', filename='', mode='single')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "", line 1
    v=1
      ^
SyntaxError: multiple statements found while compiling a single statement
>>> my_code = compile('v=1\nx=2+v\nx', filename='', mode='exec')
```

The main difference is in the return value. In the case of `exec`, the stack is
cleared before return, which means only the side effects remain.

```python
>>> my_code = compile('v=1;x=2+v;x', filename='', mode='exec')
>>> dis.dis(my_code)
  1           0 LOAD_CONST               0 (1)
              2 STORE_NAME               0 (v)
              4 LOAD_CONST               1 (2)
              6 LOAD_NAME                0 (v)
              8 BINARY_ADD
             10 STORE_NAME               1 (x)
             12 LOAD_NAME                1 (x)
             14 POP_TOP
             16 LOAD_CONST               2 (None)
             18 RETURN_VALUE
>>> eval(my_code)
```

In the case of `single`, the last value in the stack is printed before return.
As before, nothing is returned.

```python
>>> my_code = compile('v=1;x=2+v;x', filename='', mode='single')
>>> dis.dis(my_code)
  1           0 LOAD_CONST               0 (1)
              2 STORE_NAME               0 (v)
              4 LOAD_CONST               1 (2)
              6 LOAD_NAME                0 (v)
              8 BINARY_ADD
             10 STORE_NAME               1 (x)
             12 LOAD_NAME                1 (x)
             14 PRINT_EXPR
             16 LOAD_CONST               2 (None)
             18 RETURN_VALUE
>>> eval(my_code)
3
```

### Arithmetic operations

Next, we define all the simple arithmetic and boolean operators as below.

```python
mathops = {
          'BINARY_ADD': lambda a, b: a + b,
          'BINARY_SUBTRACT': lambda a, b: a - b,
          'BINARY_MULTIPLY':  lambda a, b: a * b,
          'BINARY_MATRIX_MULTIPLY':  lambda a, b: a @ b,
          'BINARY_TRUE_DIVIDE': lambda a, b: a / b,
          'BINARY_MODULO': lambda a, b: a % b,
          'BINARY_POWER': lambda a, b: a ** b,
          'BINARY_LSHIFT':  lambda a, b: a << b,
          'BINARY_RSHIFT': lambda a, b: a >> b,
          'BINARY_OR': lambda a, b: a | b,
          'BINARY_XOR': lambda a, b: a ^ b,
          'BINARY_AND': lambda a, b: a & b,
          'BINARY_FLOOR_DIVIDE': lambda a, b: a // b,
          'UNARY_POSITIVE': lambda a: a,
          'UNARY_NEGATIVE': lambda a: -a,
          'UNARY_NOT': lambda a: not a,
          'UNARY_INVERT': lambda a: ~a
        }
```

### Boolean operations

Similar to arithmetic operations, we define all logical operators.

```python
boolops = {
        '<' : lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '>' : lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
        'in': lambda a, b: a in b,
        'not in': lambda a, b: a not in b,
        'is' :lambda a, b: a is b,
        'is not': lambda a, b: a is not b,
        }
```

### The `Code`

The compiled bytecode is of type `code`. 

```python
>>> my_code.__class__
<class 'code'>
```

It contains the following attributes

```python
>>> [o for o in dir(my_code) if o[0] != '_']
['co_argcount', 'co_cellvars', 'co_code', 'co_consts', 'co_filename', 
'co_firstlineno', 'co_flags', 'co_freevars', 'co_kwonlyargcount', 
'co_lnotab', 'co_name', 'co_names', 'co_nlocals', 'co_stacksize', 
'co_varnames']
```


Since it is a read-only data structure, and we want to modify it, we will use a
proxy class `Code` to wrap it. We copy over the minimum attributes needed.

```python
class Code:
    def __init__(self, code):
        self.code = code
        self.co_consts = list(code.co_consts)
        self.co_names = list(code.co_names)
        self.co_varnames = list(code.co_varnames)
        self.opcodes = list(dis.get_instructions(self.code))
```

### The virtual machine

As can be inferred from the `dis` output, the Python Virtual Machine is a stack
based machine. So we define a bare bones virtual machine that can use a stack
as below.

```python
class Vm:
    def __init__(self, local=[]):
        self.stack = []
        self.block_stack = []
        self.local = local

    def i_pop_top(self, i): self.stack.pop()
    def i_load_global(self, i): self.stack.append(self.code.co_names[i])
    def i_load_name(self, i): self.stack.append(self.code.co_names[i])
    def i_store_name(self, i):
        if len(self.local) < i + 1:
            assert len(self.local) == i
            self.local.append(self.stack.pop())
        else:
            self.local[i] = self.stack.pop()
    def i_load_const(self, i): self.stack.append(self.code.co_consts[i])
    def i_load_fast(self, i): self.stack.append(self.local[i])
    def i_store_fast(self, i):
        if len(self.local) < i + 1:
            assert len(self.local) == i
            self.local.append(self.stack.pop())
        else:
            self.local[i] = self.stack.pop()
```

The return instruction is simply a pop of the stack.
   
```python
class Vm(Vm):
    def i_return_value(self, i):
        return self.stack.pop()
```

Now, we define how a function is called. We need to extract the
function and args, and pass the execution to the called function.

```python
class Vm(Vm):
    def i_call_function(self, i):
        nargs = i + 1
        fn, *args = self.stack[-nargs:]
        self.stack = self.stack[:len(self.stack)-nargs]
        if type(fn) == tuple:
            qname, myfn_code, p = fn
            v = Vm(args).bytes(myfn_code)
            v.i()
            self.stack.append(v.result)
        elif fn in self.code.co_names:
            v = dict(zip(self.code.co_names, self.local))
            if fn not in v:
                l = {**globals(), **locals()}
                if fn not in l: raise Exception('Function[%s] not found' % str(fn))
                myfn = l[fn]
                v = Vm(args).bytes(myfn.__code__)
                v.i()
                self.stack.append(v.result)
            else:
                (name, myfn, p) = v[fn]
                v = Vm(args).bytes(myfn)
                v.i()
                self.stack.append(v.result)
```


Implementing *COMPARE_OP*

```python
class Vm(Vm):
    def i_compare_op(self, opname):
        op = dis.cmp_op[opname]
        fn = boolops[op]
        nargs = 2
        args = self.stack[-nargs:]
        self.stack = self.stack[:len(self.stack)-nargs]
        v = fn(*args)
        self.stack.append(v)
```

Implementing jumps

```python
class Vm(Vm):

    def i_pop_jump_if_true(self, i, ins):
        v = self.stack.pop()
        if v: return i // 2
        return ins + 1

    def i_pop_jump_if_false(self, i, ins):
        v = self.stack.pop()
        if not v: return i // 2
        return ins + 1

    def i_jump_absolute(self, i, ins):
        # each instruction is two bytes long
        return i // 2
```

Implementing loops

```python
class Vm(Vm):
    def i_setup_loop(self, i):
        # not sure.
        self.block_stack.append(i)

    def i_pop_block(self, i):
        # not sure.
        self.block_stack.pop()

    def i_make_function(self, i):
        p = None
        if i == 0x01:
            # tuple of default args in positional order
            p = self.stack.pop()
        elif i == 0x02:
            # a dict of kw only args and vals
            p = self.stack.pop()
        elif i == 0x04:
            # an annotation dict
            p = self.stack.pop()
        elif i == 0x08:
            # closure
            p = self.stack.pop()
        qname = self.stack.pop()
        code = self.stack.pop()
        self.stack.append((qname, code, p))
```

Wrappers

```python
class Vm(Vm):

    def statement(self, my_str, kind='exec'):
        return self.bytes(compile(my_str, '<>', kind))

    def expr(self, my_str, kind='eval'):
        return self.bytes(compile(my_str, '<>', kind))
```

Translation of bytes to corresponding functions.

```python
class Vm(Vm):
    def bytes(self, code):
        self.fnops = {
                'LOAD_GLOBAL': self.i_load_global,
                'LOAD_FAST': self.i_load_fast,
                'STORE_FAST': self.i_store_fast,
                'LOAD_NAME': self.i_load_name,
                'STORE_NAME': self.i_store_name,
                'LOAD_CONST': self.i_load_const,
                'RETURN_VALUE': self.i_return_value,
                'CALL_FUNCTION': self.i_call_function,
                'COMPARE_OP': self.i_compare_op,
                }
        self.jmpops = {
                'POP_JUMP_IF_TRUE':  self.i_pop_jump_if_true,
                'POP_JUMP_IF_FALSE': self.i_pop_jump_if_false,
                'JUMP_ABSOLUTE': self.i_jump_absolute
                }
        self.blockops = {
                'SETUP_LOOP': self.i_setup_loop,
                'POP_TOP': self.i_pop_top,
                }
        self.otherops = {
                'MAKE_FUNCTION' : self.i_make_function,
                'POP_BLOCK': self.i_pop_block,
                }
        self.code = Code(code)
        return self
```

The interpreter itself

```python
class Vm(Vm):
    def i(self):
        ops = self.code.opcodes
        ins = 0
        while ins < len(ops):
            i = ops[ins]
            log(ins,i.opname, i.arg, i.is_jump_target)
            if i.opname in mathops:
                fn = mathops[i.opname]
                nargs = fn.__code__.co_argcount
                args = self.stack[-nargs:]
                self.stack = self.stack[:len(self.stack)-nargs]
                v = fn(*args)
                self.stack.append(v)
            elif i.opname in self.fnops:
                fn = self.fnops[i.opname]
                self.result = fn(i.arg)
            elif i.opname in self.jmpops:
                fn = self.jmpops[i.opname]
                ins = fn(i.arg, ins)
                assert ops[i.arg//2].is_jump_target
                continue
            elif i.opname in self.blockops:
                fn = self.blockops[i.opname]
                fn(i.arg)
            elif i.opname in self.otherops:
                fn = self.otherops[i.opname]
                fn(i.arg)
            else:
                assert False
            ins += 1
        return self

    def result():
        return self.result
```

### A few example functions
        
```python
def my_add(a, b):
    return a + b

def gcd(a, b):
    if a<b:
        c = a
        a = b
        b = c

    while b != 0 :
        c = a
        a = b
        b = c % b
    return a
```

### A driver

```python
v = Vm().expr('my_add(2, 3)').i()
print(v.result)
v = Vm().expr('gcd(12, 15)').i()
print(v.result)

v = Vm()
v.statement('def x(a, b): return a+b').i()
v.expr('x(1,2)').i()
print(v.result)

v = Vm().expr('(lambda a, b: a+b)(2, 3)').i()
print(v.result)

```
