# ---
# published: true
# title: Python Meta Circular Interpreter
# layout: post
# comments: true
# tags: mci
# categories: post
# ---
# 
# I had previously [discussed](/post/2011/07/20/language7/) how one can implement
# a programming language using big step semantics. In this post, I want to so
# something similar. Here, we implement a meta-circular interpreter over Python.
# The code is available [here](/resources/posts/mci.py).
# 
# A meta-circular interpreter is an interpreter for a language that is written
# in that language itself. The MCI can implement a subset or superset of the host
# language.
# 
# ## Uses of a Meta Circular Interpreter
# 
# Why should one want to write a meta-circular interpreter? Writing such an
# interpreter gives you a large amount of control over how the code is executed.
# Further, it also gives you a way to track the execution as it proceeds.
# Using the same machinery as the meta-circular interpreter, one can:
# 
# * Write a concolic interpreter that tracks the concrete execution
# * Extract coverage
# * Extract the control flow graph, and execution path through the graph
# * Extract the call graph of execution
# * Write a symbolic execution engine
# * Write a taint tracker that will not be confused by indirect control flow
# * Extend the host language with new features
# * Reduce the capabilities exposed by the host language (e.g. no system calls).
# 
# I will be showing how to do these things in the upcoming posts. 
# 
# ## The Implementation (tested in Python 3.6.8)
# 
# First, we import everything we need.


import string
import ast
import sys
import builtins
from functools import reduce
import importlib


# The basic idea is to make use of the Python infrastructure as much as possible. That is,
# we do not want to implement things that are not related to the actual interpretation.
# Hence, we use the Python parsing infrastructure exposed by the `ast` module that parses
# Python source files, and returns back the AST. AST (Abstract Syntax Tree) as the name
# indicates is a data structure in the format of a tree.
# 
# Once we have the AST, we simply walk the tree, and interpret the statements as we find them.
# 
# 
# ### The meta-circular-interpreter class
# 
# The `walk()` method is at the heart of our interpreter. Given the AST,
# It iterates through the statements, and evaluates each by invoking the corresponding method.
# If the method is not implemented, it raises a `SynErr` which is derived from `SyntaxError`.


class SynErr(SyntaxError): pass

class PyMCInterpreter:
    def walk(self, node):
        if node is None: return
        res = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, res):
            return getattr(self,res)(node)
        raise SynErr('walk: Not Implemented in %s' % type(node))


# We provide `eval()` which converts a given string to its AST, and calls
# `walk()`. It is possible to write a parser of our own, as I have [shown before](/2018/09/06/peg-parsing/)
# which can get us the AST. However, as I mentioned earlier, we use the Python infrastructure where possible.


class PyMCInterpreter(PyMCInterpreter):
    def eval(self, src):
        return self.walk(ast.parse(src))


# #### The Pythonic data structures.
# 
# We need to define data. For the primitive data types, we only implement `string` and `number` for now.
# These are trivial as it is a direct translation of the AST values.
# 
# ##### Str(string s)


class PyMCInterpreter(PyMCInterpreter):
    def on_str(self, node):
        return node.s


# ##### Number(object n)


class PyMCInterpreter(PyMCInterpreter):
    def on_num(self, node):
        return node.n


# ##### Constant(constant value, string? kind)

class PyMCInterpreter(PyMCInterpreter):
    def on_constant(self, node):
        return node.value

# #### Containers
# 
# Essentially, we want to be able to make use of all pythonic
# container data structures such as lists, tuples, sets and
# dictionaries. For demonstration, however, we have implemented
# only list and tuple.
# 
# Unlike the primitives, the containers may be defined such that
# the values inside them are result of evaluating some expression.
# Hence, we first `walk()` the elements, and add the results.
# 
# ##### List(elts)


class PyMCInterpreter(PyMCInterpreter):
    def on_list(self, node):
        res = []
        for p in node.elts:
            v = self.walk(p)
            res.append(v)
        return res


# ##### Tuple(elts)


class PyMCInterpreter(PyMCInterpreter):
    def on_tuple(self, node):
        res = []
        for p in node.elts:
            v = self.walk(p)
            res.append(v)
        return res

# Containers provide the ability to access their contained items via `Subscript`.
# 
# ##### Subscript(expr value, slice slice, expr_context ctx)
# 
# The tuple and list provide a means to access its elements via
# subscript. The subscript requires a special `Index` value as input, which is also defined below.


class PyMCInterpreter(PyMCInterpreter):
    def on_subscript(self, node):
        value = self.walk(node.value)
        slic = self.walk(node.slice)
        return value[slic]

    def on_index(self, node):
        return self.walk(node.value)


# ##### Attribute(expr value, identifier attr, expr_context ctx)
# 
# Similar to subscript for arrays, objects provide attribute access.


class PyMCInterpreter(PyMCInterpreter):
    def on_attribute(self, node):
        obj = self.walk(node.value)
        attr = node.attr
        return getattr(obj, attr)


# #### Simple control flow statements

# The `return`, `break` and `continue` are implemented as exceptions.


class Return(Exception):
    def __init__(self, val): self.__dict__.update(locals())
    
class Break(Exception):
    def __init__(self): pass

class Continue(Exception):
    def __init__(self): pass


# #### Implementation


class PyMCInterpreter(PyMCInterpreter):
    def on_return(self, node):
        raise Return(self.walk(node.value))

    def on_break(self, node):
        raise Break(self.walk(node.value))

    def on_continue(self, node):
        raise Continue(self.walk(node.value))

    def on_pass(self, node):
        pass


# The difference between `break` and `continue` is in how they are handled in the
# loop statemens as in `While` below. The `return` is handled in the `Call` part.
# 
# #### Major control flow statements
# 
# Only basic loops and conditionals -- `while()` and `if()` are implemented.
# 
# ##### While(expr test, stmt* body, stmt* orelse)
#
# Implementing the `While` loop is fairly straight forward. The `while.body` is
# a list of statements that need to be interpreted if the `while.test` is `True`.
# The `break` and `continue` statements provide a way to either stop the execution
# or to restart it.
# 
# As can be seen, these are *statements* rather than *expressions*, which means that
# their return value is not important. Hence, we do not return anything.


class PyMCInterpreter(PyMCInterpreter):
    def on_while(self, node):
        while self.walk(node.test):
            try:
                for b in node.body:
                    self.walk(b)
            except Break:
                break
            except Continue:
                continue

# ##### If(expr test, stmt* body, stmt* orelse)
# 
# The `If` statement is similar to `While`. We check `if.test` and if `True`,
# execute the `if.body`. If `False`, we execute the `if.orelse`.


class PyMCInterpreter(PyMCInterpreter):

    def on_if(self, node):
        v = self.walk(node.test)
        body = node.body if v else node.orelse
        if body:
            res = None
            for b in body:
                res = self.walk(b)


# #### The scope and symbol table
# 
# Now we come to a slightly more complex part. We want to define a symbol table. The reason
# this is complicated is that the symbol table interacts with the scope, which is a
# nested data structrue, and we need to provide a way to look up symbols in enclosing
# scopes. We have a choice to make here. Essentially, what variables do the calling
# program have access to? Historically, the most common conventions are [lexical and
# dynamic scoping](https://en.wikipedia.org/wiki/Scope_(computer_science)#Lexical_scoping_vs._dynamic_scoping).
# The most intuitive is the lexical scoping convention. Hence, we implement lexical scoping,
# but with a restriction: If we modify a variable in parent scopes, then the new variable is
# created in current scope.


class Scope:
    def __init__(self, parent=None, table=None):
        self.table = table
        self.children = []
        self.parent = parent

    def new_child(table):
        return Scope(parent=self, table=table)

    def __setitem__(self, i, v):
        # choice here. We can check and set then named variable (if any)
        # in parent scopes. See `nonlocal` in Python
        self.table[i] = v

    def __getitem__(self, i):
        if i in self.table: return self.table[i]
        if self.parent is None: return None
        return self.parent[i]


# #### Hooking up the symbol table
# 
# We allow the user to load a pre-defined symbol table. We
# have a choice to make here. Should we allow access to the
# Python default symbol table? and if we do, what should form
# the root? The Python symbol table or what the user supplied?
# 
# Here, we assume that the default Python symbol table is the
# root.
# 
# We will discuss the OP statements later.


class PyMCInterpreter(PyMCInterpreter):
    def __init__(self, symtable, args):
        self.unaryop = UnaryOP
        self.binop = BinOP
        self.cmpop = CmpOP
        self.boolop = BoolOP

        self.symtable = Scope(parent=None, table=builtins.__dict__)
        self.symtable['sys'] = ast.Module(ast.Pass())
        setattr(self.symtable['sys'], 'argv', args)

        self.symtable = Scope(parent=self.symtable, table=symtable)


# #### The following statements use symbol table.
# 
# ##### Name(identifier id, expr_context ctx)
# 
# Retrieving a referenced symbol is simple enough.


class PyMCInterpreter(PyMCInterpreter):
    def on_name(self, node):
        return self.symtable[node.id]

# ##### Assign(expr* targets, expr value)
# 
# Python allows multi-target assignments. The problem is that, the type of the `value` received may be different based on
# whether the statement is multi-target or single-target. Hence, we split both kinds.


class PyMCInterpreter(PyMCInterpreter):
    def on_assign(self, node):
        value = self.walk(node.value)
        tgts = [t.id for t in node.targets]
        if len(tgts) == 1:
            self.symtable[tgts[0]] = value
        else:
            for t,v in zip(tgts, value):
                self.symtable[t] = v


# ##### Call(expr func, expr* args, keyword* keywords)
# 
# During function calls, we need to make sure that the functions that
# are implemented in C are proxied directly.
# 
# For others, we want to correctly bind the arguments and create a
# new scope. The big question is how should the scopes be nested.
# We use lexical scopes. So, we recover the symbol table used at the
# time of definition, use it for the call, and reset it back to the
# current one after the call.
# 
# Note that we handle the `return` exception here.
 

class PyMCInterpreter(PyMCInterpreter):
    def on_call(self, node):
        func = self.walk(node.func)
        args = [self.walk(a) for a in node.args]
        if str(type(func)) == "<class 'builtin_function_or_method'>":
            return func(*args)
        elif str(type(func)) == "<class 'type'>":
            return func(*args)
        else:
            [fname, argument, returns, fbody, symtable] = func
            argnames = [a.arg for a in argument.args]
            defs= dict(zip(argnames, args))
            oldsyms = self.symtable
            self.symtable = Scope(parent=symtable, table=defs)
            try:
                for i in fbody:
                    res = self.walk(i)
                return res
            except Return as e:
                return e.val
            finally:
                self.symtable = oldsyms

# ##### FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns, string? type_comment)
# 
# The function definition itself is quite simple. We simply update the symbol table with the given values.
# Note that because we implement *lexical scoping*, we have to maintain the scoping references during creation.


class PyMCInterpreter(PyMCInterpreter):
    def on_functiondef(self, node):
        fname = node.name
        args = node.args
        returns = node.returns
        self.symtable[fname] = [fname, args, returns, node.body, self.symtable]


# ##### Import(alias* names)
# 
# Import is similar to a definition except that we want to update the symbol table
# with predefined values.


class PyMCInterpreter(PyMCInterpreter):
    def on_import(self, node):
        for im in node.names:
            if im.name == 'sys': continue
            v = importlib.import_module(im.name)
            self.symtable[im.name] = v


# #### Arithmetic Expressions
# 
# The arithmetic expressions are proxied directly to corresponding Python operators.
# 
# ##### Expr(expr value)

UnaryOP = {
          ast.Invert: lambda a: ~a,
          ast.Not: lambda a: not a,
          ast.UAdd: lambda a: +a,
          ast.USub: lambda a: -a
}

BinOP = {
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

CmpOP = {
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

BoolOP = {
          ast.And: lambda a, b: a and b,
          ast.Or: lambda a, b: a or b
}

class PyMCInterpreter(PyMCInterpreter):
    def on_expr(self, node):
        return self.walk(node.value)

    def on_compare(self, node):
        hd = self.walk(node.left)
        op = node.ops[0]
        tl = self.walk(node.comparators[0])
        return self.cmpop[type(op)](hd, tl)

    def on_unaryop(self, node):
        return self.unaryop[type(node.op)](self.walk(node.operand))

    def on_boolop(self, node):
        return reduce(self.boolop[type(node.op)], [self.walk(n) for n in node.values])

    def on_binop(self, node):
        return self.binop[type(node.op)](self.walk(node.left), self.walk(node.right))


# #### Modules
# 
# ##### Module(stmt* body)
# 
# The complete AST is wrapped in a Module statement.


class PyMCInterpreter(PyMCInterpreter):
    def on_module(self, node):
        # return value of module is the last statement
        res = None
        for p in node.body:
            res = self.walk(p)
        return res

# ### The driver
# 
# ```python
# if __name__ == '__main__':
#     expr = PyMCInterpreter({'__name__':'__main__'}, sys.argv[1:]) #json.loads(sys.argv[2])
#     v = expr.eval(open(sys.argv[1]).read())
#     print(v)
# ```

# ### An example

triangle_py = """\
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
"""

# ### Usage
#
# ```shell
# $ python3 interp.py triangle.py '1 2 3'
# ```

if __name__ == '__main__':
    expr = PyMCInterpreter({'__name__':'__main__'}, ['triangle_py', '1 2 3'])
    v = expr.eval(triangle_py)
    print(v)
