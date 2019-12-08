---
published: false
title: A tiny and incomplete Python Virtual Machine
layout: post
comments: true
tags: vm
---


This post shows how to implement a very tiny Python virtual machine that will allow us to implement useful tools such as taint analysis later.
For more complete implementations, refer to the [AOSA Book](https://www.aosabook.org/en/500L/a-python-interpreter-written-in-python.html) or more complete and current [Byterun](https://github.com/nedbat/byterun).

```python
import dis

DEBUG = True
def log(*x):
    if DEBUG: print(*x)

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

class Code:
    def __init__(self, code):
        self.code = code
        self.co_consts = list(code.co_consts)
        self.co_names = list(code.co_names)
        self.co_varnames = list(code.co_varnames)
        self.opcodes = list(dis.get_instructions(self.code))

class Vm:
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

    def i_return_value(self, i):
        return self.stack.pop()

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

    def i_compare_op(self, opname):
        op = dis.cmp_op[opname]
        fn = boolops[op]
        nargs = 2
        args = self.stack[-nargs:]
        self.stack = self.stack[:len(self.stack)-nargs]
        v = fn(*args)
        self.stack.append(v)

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

    def __init__(self, local=[]):
        self.stack = []
        self.block_stack = []
        self.local = local

    def statement(self, my_str, kind='exec'):
        log(kind,my_str)
        return self.bytes(compile(my_str, '<>', kind))

    def expr(self, my_str, kind='eval'):
        log(kind, my_str)
        return self.bytes(compile(my_str, '<>', kind))

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
A driver
        
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
