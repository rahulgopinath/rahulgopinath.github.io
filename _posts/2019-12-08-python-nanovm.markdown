---
published: true
title: A tiny and incomplete Python Virtual Machine
layout: post
comments: true
tags: vm
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

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

<!--
############
import dis


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import dis
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As in the [MCI](/post/2019/12/07/python-mci/), we try to use as much of the
Python infrastructure as possible. Hence, we use the Python compiler to compile
source files into bytecode, and we only interpret the bytecode. One can
[compile](https://docs.python.org/3/library/functions.html#compile) source
strings to byte code as follows.

### Compilation

<!--
############
my_code = compile('2+v', filename='', mode='eval')


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;2+v&#x27;, filename=&#x27;&#x27;, mode=&#x27;eval&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `mode` can be one of `eval` -- which evaluates expressions, `exec` --
which executes a sequence of statements, and `single` -- which is a limited form
of `exec`. Their difference can be seen below.


#### compile(mode=eval)

<!--
############
v = 1
my_code = compile('2+v', filename='', mode='eval')
dis.dis(my_code)
print(eval(my_code))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = 1
my_code = compile(&#x27;2+v&#x27;, filename=&#x27;&#x27;, mode=&#x27;eval&#x27;)
dis.dis(my_code)
print(eval(my_code))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, the return value is the result of addition.

#### compile(mode=exec)

<!--
############
my_code = compile('2+v', filename='', mode='exec')
dis.dis(my_code)
print(eval(my_code))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;2+v&#x27;, filename=&#x27;&#x27;, mode=&#x27;exec&#x27;)
dis.dis(my_code)
print(eval(my_code))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The top of the stack is popped off on execution. That is,
it is treated as a statement. This mode is used for evaluating a series of
statements none of which will return a value when `eval()` is called.

<!--
############
try:
    my_code = compile('v=1;x=2+v', filename='', mode='eval')
except SyntaxError as e:
    print(e)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
try:
    my_code = compile(&#x27;v=1;x=2+v&#x27;, filename=&#x27;&#x27;, mode=&#x27;eval&#x27;)
except SyntaxError as e:
    print(e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
using exec

<!--
############
my_code = compile('v=1;x=2+v', filename='', mode='exec')
dis.dis(my_code)
eval(my_code)
print(x)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;v=1;x=2+v&#x27;, filename=&#x27;&#x27;, mode=&#x27;exec&#x27;)
dis.dis(my_code)
eval(my_code)
print(x)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### compile(mode=single)

The `single` mode is a restricted version of `exec`. It is applicable for a
single line *statement*, which can even be constructed by stitching multiple
statements together with semicolons.

<!--
############
try:
    my_code = compile('v=1\nx=2+v\nx', filename='', mode='single')
except SyntaxError as e:
    print(e)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
try:
    my_code = compile(&#x27;v=1\nx=2+v\nx&#x27;, filename=&#x27;&#x27;, mode=&#x27;single&#x27;)
except SyntaxError as e:
    print(e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
my_code = compile('v=1\nx=2+v\nx', filename='', mode='exec')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;v=1\nx=2+v\nx&#x27;, filename=&#x27;&#x27;, mode=&#x27;exec&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The main difference is in the return value. In the case of `exec`, the stack is
cleared before return, which means only the side effects remain.

<!--
############
my_code = compile('v=1;x=2+v;x', filename='', mode='exec')
dis.dis(my_code)
print(eval(my_code))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;v=1;x=2+v;x&#x27;, filename=&#x27;&#x27;, mode=&#x27;exec&#x27;)
dis.dis(my_code)
print(eval(my_code))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
In the case of `single`, the last value in the stack is printed before return.
As before, nothing is returned.

<!--
############
my_code = compile('v=1;x=2+v;x', filename='', mode='single')
dis.dis(my_code)
print(eval(my_code))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_code = compile(&#x27;v=1;x=2+v;x&#x27;, filename=&#x27;&#x27;, mode=&#x27;single&#x27;)
dis.dis(my_code)
print(eval(my_code))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Arithmetic operations
Next, we define all the simple arithmetic and boolean operators as below.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mathops = {
          &#x27;BINARY_ADD&#x27;: lambda a, b: a + b,
          &#x27;BINARY_SUBTRACT&#x27;: lambda a, b: a - b,
          &#x27;BINARY_MULTIPLY&#x27;:  lambda a, b: a * b,
          &#x27;BINARY_MATRIX_MULTIPLY&#x27;:  lambda a, b: a @ b,
          &#x27;BINARY_TRUE_DIVIDE&#x27;: lambda a, b: a / b,
          &#x27;BINARY_MODULO&#x27;: lambda a, b: a % b,
          &#x27;BINARY_POWER&#x27;: lambda a, b: a ** b,
          &#x27;BINARY_LSHIFT&#x27;:  lambda a, b: a &lt;&lt; b,
          &#x27;BINARY_RSHIFT&#x27;: lambda a, b: a &gt;&gt; b,
          &#x27;BINARY_OR&#x27;: lambda a, b: a | b,
          &#x27;BINARY_XOR&#x27;: lambda a, b: a ^ b,
          &#x27;BINARY_AND&#x27;: lambda a, b: a &amp; b,
          &#x27;BINARY_FLOOR_DIVIDE&#x27;: lambda a, b: a // b,
          &#x27;UNARY_POSITIVE&#x27;: lambda a: a,
          &#x27;UNARY_NEGATIVE&#x27;: lambda a: -a,
          &#x27;UNARY_NOT&#x27;: lambda a: not a,
          &#x27;UNARY_INVERT&#x27;: lambda a: ~a
        }
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Boolean operations
Similar to arithmetic operations, we define all logical operators.

<!--
############
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


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
boolops = {
        &#x27;&lt;&#x27; : lambda a, b: a &lt; b,
        &#x27;&lt;=&#x27;: lambda a, b: a &lt;= b,
        &#x27;==&#x27;: lambda a, b: a == b,
        &#x27;!=&#x27;: lambda a, b: a != b,
        &#x27;&gt;&#x27; : lambda a, b: a &gt; b,
        &#x27;&gt;=&#x27;: lambda a, b: a &gt;= b,
        &#x27;in&#x27;: lambda a, b: a in b,
        &#x27;not in&#x27;: lambda a, b: a not in b,
        &#x27;is&#x27; :lambda a, b: a is b,
        &#x27;is not&#x27;: lambda a, b: a is not b,
        }
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The `Code`
The compiled bytecode is of type `code`. 

<!--
############
print(my_code.__class__)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(my_code.__class__)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It contains the following attributes

<!--
############
print([o for o in dir(my_code) if o[0] != '_'])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print([o for o in dir(my_code) if o[0] != &#x27;_&#x27;])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Since it is a read-only data structure, and we want to modify it, we will use a
proxy class `Code` to wrap it. We copy over the minimum attributes needed.

<!--
############
class Code:
    def __init__(self, code):
        self.code = code
        self.co_consts = list(code.co_consts)
        self.co_names = list(code.co_names)
        self.co_varnames = list(code.co_varnames)
        self.opcodes = list(dis.get_instructions(self.code))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Code:
    def __init__(self, code):
        self.code = code
        self.co_consts = list(code.co_consts)
        self.co_names = list(code.co_names)
        self.co_varnames = list(code.co_varnames)
        self.opcodes = list(dis.get_instructions(self.code))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The virtual machine

As can be inferred from the `dis` output, the Python Virtual Machine is a stack
based machine. So we define a bare bones virtual machine that can use a stack
as below.

<!--
############
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


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Vm:
    def __init__(self, local=[]):
        self.stack = []
        self.block_stack = []
        self.local = local

    def i_pop_top(self, i): self.stack.pop()
    def i_load_global(self, i): self.stack.append(self.code.co_names[i])
    def i_load_name(self, i): self.stack.append(self.code.co_names[i])
    def i_store_name(self, i):
        if len(self.local) &lt; i + 1:
            assert len(self.local) == i
            self.local.append(self.stack.pop())
        else:
            self.local[i] = self.stack.pop()
    def i_load_const(self, i): self.stack.append(self.code.co_consts[i])
    def i_load_fast(self, i): self.stack.append(self.local[i])
    def i_store_fast(self, i):
        if len(self.local) &lt; i + 1:
            assert len(self.local) == i
            self.local.append(self.stack.pop())
        else:
            self.local[i] = self.stack.pop()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The return instruction is simply a pop of the stack.

<!--
############
class Vm(Vm):
    def i_return_value(self, i):
        return self.stack.pop()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Vm(Vm):
    def i_return_value(self, i):
        return self.stack.pop()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we define how a function is called. We need to extract the
function and args, and pass the execution to the called function.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
                if fn not in l: raise Exception(&#x27;Function[%s] not found&#x27; % str(fn))
                myfn = l[fn]
                v = Vm(args).bytes(myfn.__code__)
                v.i()
                self.stack.append(v.result)
            else:
                (name, myfn, p) = v[fn]
                v = Vm(args).bytes(myfn)
                v.i()
                self.stack.append(v.result)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Implementing *COMPARE_OP*

<!--
############
class Vm(Vm):
    def i_compare_op(self, opname):
        op = dis.cmp_op[opname]
        fn = boolops[op]
        nargs = 2
        args = self.stack[-nargs:]
        self.stack = self.stack[:len(self.stack)-nargs]
        v = fn(*args)
        self.stack.append(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Vm(Vm):
    def i_compare_op(self, opname):
        op = dis.cmp_op[opname]
        fn = boolops[op]
        nargs = 2
        args = self.stack[-nargs:]
        self.stack = self.stack[:len(self.stack)-nargs]
        v = fn(*args)
        self.stack.append(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Implementing jumps

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Implementing loops

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Wrappers

<!--
############
class Vm(Vm):

    def statement(self, my_str, kind='exec'):
        return self.bytes(compile(my_str, '<>', kind))

    def expr(self, my_str, kind='eval'):
        return self.bytes(compile(my_str, '<>', kind))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Vm(Vm):

    def statement(self, my_str, kind=&#x27;exec&#x27;):
        return self.bytes(compile(my_str, &#x27;&lt;&gt;&#x27;, kind))

    def expr(self, my_str, kind=&#x27;eval&#x27;):
        return self.bytes(compile(my_str, &#x27;&lt;&gt;&#x27;, kind))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Translation of bytes to corresponding functions.

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Vm(Vm):
    def bytes(self, code):
        self.fnops = {
                &#x27;LOAD_GLOBAL&#x27;: self.i_load_global,
                &#x27;LOAD_FAST&#x27;: self.i_load_fast,
                &#x27;STORE_FAST&#x27;: self.i_store_fast,
                &#x27;LOAD_NAME&#x27;: self.i_load_name,
                &#x27;STORE_NAME&#x27;: self.i_store_name,
                &#x27;LOAD_CONST&#x27;: self.i_load_const,
                &#x27;RETURN_VALUE&#x27;: self.i_return_value,
                &#x27;CALL_FUNCTION&#x27;: self.i_call_function,
                &#x27;COMPARE_OP&#x27;: self.i_compare_op,
                }
        self.jmpops = {
                &#x27;POP_JUMP_IF_TRUE&#x27;:  self.i_pop_jump_if_true,
                &#x27;POP_JUMP_IF_FALSE&#x27;: self.i_pop_jump_if_false,
                &#x27;JUMP_ABSOLUTE&#x27;: self.i_jump_absolute
                }
        self.blockops = {
                &#x27;SETUP_LOOP&#x27;: self.i_setup_loop,
                &#x27;POP_TOP&#x27;: self.i_pop_top,
                }
        self.otherops = {
                &#x27;MAKE_FUNCTION&#x27; : self.i_make_function,
                &#x27;POP_BLOCK&#x27;: self.i_pop_block,
                }
        self.code = Code(code)
        return self
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The interpreter itself

<!--
############
def log(*args):
    #print(*args)
    pass

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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def log(*args):
    #print(*args)
    pass

class Vm(Vm):
    def i(self):
        ops = self.code.opcodes
        ins = 0
        while ins &lt; len(ops):
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### A few example functions

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def my_add(a, b):
    return a + b

def gcd(a, b):
    if a&lt;b:
        c = a
        a = b
        b = c

    while b != 0 :
        c = a
        a = b
        b = c % b
    return a
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### A driver

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v = Vm().expr(&#x27;my_add(2, 3)&#x27;).i()
print(v.result)
v = Vm().expr(&#x27;gcd(12, 15)&#x27;).i()
print(v.result)

v = Vm()
v.statement(&#x27;def x(a, b): return a+b&#x27;).i()
v.expr(&#x27;x(1,2)&#x27;).i()
print(v.result)

v = Vm().expr(&#x27;(lambda a, b: a+b)(2, 3)&#x27;).i()
print(v.result)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
