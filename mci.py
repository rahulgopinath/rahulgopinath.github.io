#!/usr/bin/env python3
import string
import ast
import sys
import json
import builtins
from functools import reduce

class PyMCInterpreter:
    """
    The meta circular python Exprinterpreter
    >>> i = PyMCInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
    >>> i.eval('a+b')
    3
    """
    def __init__(self, symtable):
        # unaryop = Invert | Not | UAdd | USub
        self.unaryop = {
          ast.Invert: lambda a: ~a,
          ast.Not: lambda a: not a,
          ast.UAdd: lambda a: +a,
          ast.USub: lambda a: -a
        }

        # operator = Add | Sub | Mult | MatMult | Div | Mod | Pow | LShift | RShift | BitOr | BitXor | BitAnd | FloorDiv
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

        # cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn
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

        # boolop = And | Or
        self.boolop = {
          ast.And: lambda a, b: a and b,
          ast.Or: lambda a, b: a or b
        }

        self.symtable = builtins.__dict__

        self.symtable.update(symtable)

    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise Exception('walk: Not Implemented %s' % type(node))

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

    def on_nameconstant(self, node):
        """
        NameConstant(singleton value)
        """
        return node.value

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
        >>> expr = PyMCInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
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
        >>> expr = PyMCInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('-a')
        -1
        """
        return self.unaryop[type(node.op)](self.walk(node.operand))

    def on_boolop(self, node):
        """
        Boolop(boolop op, expr* values)
        >>> expr = PyMCInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('a and b')
        2
        """
        return reduce(self.boolop[type(node.op)], [self.walk(n) for n in node.values])


    def on_binop(self, node):
        """
        BinOp(expr left, operator op, expr right)
        >>> expr = PyMCInterpreter(dict(zip(string.ascii_lowercase, range(1,26))))
        >>> expr.eval('a + b')
        3
        """
        return self.binop[type(node.op)](self.walk(node.left), self.walk(node.right))

    def on_call(self, node):
        func = self.walk(node.func)
        args = [self.walk(a) for a in node.args]
        return func(*args)

    def eval(self, src):
        return self.walk(ast.parse(src))

if __name__ == '__main__':
    defs = {}
    if len(sys.argv) > 2:
        defs = json.loads(sys.argv[2])
    expr = PyMCInterpreter(defs)
    v = expr.eval(sys.argv[1])
    print(v)

