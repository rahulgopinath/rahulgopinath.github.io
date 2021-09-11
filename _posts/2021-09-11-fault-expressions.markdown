---
published: true
title: Fault Expressions
layout: post
comments: true
tags: python
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.8/';</script>
<script src="/resources/pyodide/full/3.8/pyodide.js"></script>
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
In my previous posts on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
and [multiple faults](/post/2021/09/10/multiple-fault-grammars/) I introduced
the evocative patterns and how to combine them using `and`. As our expressions
keep growing in complexity, we need a better way to mange them. This post
introduces a language for the suffixes so that we will have an easier time
managing them.

As before, let us start with importing our required modules.

<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
"mpmath-1.2.1-py3-none-any.whl"
"sympy-1.8-py3-none-any.whl"
</textarea>
</form>

<!--
############
import sympy

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sympy
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
**Note** `sympy` may not load immediately. Either click on the [run] button
first before you click the [run all] or if you get errors, and the `sympy`
import seems to not have been executed, try clicking on the [run] button again.
Our language is a simple language of boolean algebra. That is, it is the
language of expressions in the specialization for a nonterminal such as `<A and(f1,f2)>`
It is defined by the following grammar.

<!--
############
import string



BEXPR_GRAMMAR = {
    '<start>': [['<bexpr>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexprs>', ')'],
        ['<fault>']],
    '<bexprs>' : [['<bexpr>', ',', '<bexprs>'], ['<bexpr>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<fault>': [['<letters>'], []],
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']],
    '<letter>': [[i] for i in (
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits) + '_+*.-']
}
BEXPR_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string



BEXPR_GRAMMAR = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;bexpr&gt;&#x27;]],
    &#x27;&lt;bexpr&gt;&#x27;: [
        [&#x27;&lt;bop&gt;&#x27;, &#x27;(&#x27;, &#x27;&lt;bexprs&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;fault&gt;&#x27;]],
    &#x27;&lt;bexprs&gt;&#x27; : [[&#x27;&lt;bexpr&gt;&#x27;, &#x27;,&#x27;, &#x27;&lt;bexprs&gt;&#x27;], [&#x27;&lt;bexpr&gt;&#x27;]],
    &#x27;&lt;bop&gt;&#x27; : [list(&#x27;and&#x27;), list(&#x27;or&#x27;), list(&#x27;neg&#x27;)],
    &#x27;&lt;fault&gt;&#x27;: [[&#x27;&lt;letters&gt;&#x27;], []],
    &#x27;&lt;letters&gt;&#x27;: [
        [&#x27;&lt;letter&gt;&#x27;],
        [&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;letters&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[i] for i in (
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits) + &#x27;_+*.-&#x27;]
}
BEXPR_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need the ability to parse any expressions. So, let us load the parser

<!--
############
import sys, imp

def make_module(modulesource, sourcestr, modname):
    codeobj = compile(modulesource, sourcestr, 'exec')
    newmodule = imp.new_module(modname)
    exec(codeobj, newmodule.__dict__)
    return newmodule

def import_file(name, location):
    if "pyodide" in sys.modules:
        import pyodide
        github_repo = 'https://raw.githubusercontent.com/'
        my_repo =  'rahulgopinath/rahulgopinath.github.io'
        module_loc = github_repo + my_repo + '/master/notebooks/%s' % location
        module_str = pyodide.open_url(module_loc).getvalue()
    else:
        module_loc = './notebooks/%s' % location
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys, imp

def make_module(modulesource, sourcestr, modname):
    codeobj = compile(modulesource, sourcestr, &#x27;exec&#x27;)
    newmodule = imp.new_module(modname)
    exec(codeobj, newmodule.__dict__)
    return newmodule

def import_file(name, location):
    if &quot;pyodide&quot; in sys.modules:
        import pyodide
        github_repo = &#x27;https://raw.githubusercontent.com/&#x27;
        my_repo =  &#x27;rahulgopinath/rahulgopinath.github.io&#x27;
        module_loc = github_repo + my_repo + &#x27;/master/notebooks/%s&#x27; % location
        module_str = pyodide.open_url(module_loc).getvalue()
    else:
        module_loc = &#x27;./notebooks/%s&#x27; % location
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The parser

<!--
############
earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
gmultiple = import_file('gmultiple', '2021-09-10-multiple-fault-grammars.py')
hdd = import_file('hdd', '2019-12-04-hdd.py')
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
gmultiple = import_file(&#x27;gmultiple&#x27;, &#x27;2021-09-10-multiple-fault-grammars.py&#x27;)
hdd = import_file(&#x27;hdd&#x27;, &#x27;2019-12-04-hdd.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we need a data structure to represent the boolean language.
First we represent our literals using `LitB` class.

<!--
############
class LitB:
    def __init__(self, a): self.a = a
    def __str__(self): return self.a

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class LitB:
    def __init__(self, a): self.a = a
    def __str__(self): return self.a
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
There are two boolean literals. The top and the bottom. The top literal
also (T) essentially indicates that there is no specialization of the base
nonterminal. For e.g. `<A>` is a top literal.
Hence, we indicate it by an empty string.

<!--
############
TrueB = LitB('')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
TrueB = LitB(&#x27;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The bottom literal indicates that there are no possible members for this
particular nonterminal. For e.g. <A _|_> indicates that this is empty.
We indicate it by the empty symbol _|_.

<!--
############
FalseB = LitB('_|_')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
FalseB = LitB(&#x27;_|_&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the standard terms of the boolean algebra. `or(.,.)`, `and(.,.)` and `neg(.)`

<!--
############
class OrB:
    def __init__(self, a): self.l = a
    def __str__(self): return 'or(%s)' % ','.join(sorted([str(s) for s in self.l]))
class AndB:
    def __init__(self, a): self.l = a
    def __str__(self): return 'and(%s)' % ','.join(sorted([str(s) for s in self.l]))
class NegB:
    def __init__(self, a): self.a = a
    def __str__(self): return 'neg(%s)' % str(self.a)
class B:
    def __init__(self, a): self.a = a
    def __str__(self): return str(self.a)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class OrB:
    def __init__(self, a): self.l = a
    def __str__(self): return &#x27;or(%s)&#x27; % &#x27;,&#x27;.join(sorted([str(s) for s in self.l]))
class AndB:
    def __init__(self, a): self.l = a
    def __str__(self): return &#x27;and(%s)&#x27; % &#x27;,&#x27;.join(sorted([str(s) for s in self.l]))
class NegB:
    def __init__(self, a): self.a = a
    def __str__(self): return &#x27;neg(%s)&#x27; % str(self.a)
class B:
    def __init__(self, a): self.a = a
    def __str__(self): return str(self.a)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We then come to the actual representative class. The class is initialized by
providing it with a boolean expression.

<!--
############
class BExpr:
    def __init__(self, s):
        if s is not None:
            self._s = s
            self._tree = self._parse(s)
            self._simple, self._sympy = self._simplify()
        else: # create
            self._s = None
            self._tree = None
            self._simple = None
            self._sympy = None

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][0]
        return bexpr

    def _simplify(self):
        return None,None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr:
    def __init__(self, s):
        if s is not None:
            self._s = s
            self._tree = self._parse(s)
            self._simple, self._sympy = self._simplify()
        else: # create
            self._s = None
            self._tree = None
            self._simple = None
            self._sympy = None

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][0]
        return bexpr

    def _simplify(self):
        return None,None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
b = BExpr('and(and(f1,f2),f1)')
fuzzer.display_tree(b._tree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
b = BExpr(&#x27;and(and(f1,f2),f1)&#x27;)
fuzzer.display_tree(b._tree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we need to define how to simplify boolean expressions. For example,
we want to simplify `and(and(f1,f2),f1)` to just `and(f1,f2)`. Since this
is already offered by `sympy` we use that.
First we define a procedure that given the parse tree, converts it to a sympy
expression.

<!--
############
class BExpr(BExpr):
    def _convert_to_sympy(self, bexpr_tree, symargs=None):
        def get_op(node):
            assert node[0] == '<bop>', node[0]
            return ''.join([i[0] for i in node[1]])
        if symargs is None:
            symargs = {}
        name, children = bexpr_tree
        assert name == '<bexpr>', name
        if len(children) == 1: # fault node
            name = fuzzer.tree_to_string(children[0])
            if not name: return None, symargs
            if name not in symargs:
                symargs[name] = sympy.symbols(name)
            return symargs[name], symargs
        else:
            operator = get_op(children[0])
            if operator == 'and':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.And(*[a for a,_ in sp]), symargs

            elif operator == 'or':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.Or(*[a for a,_ in sp]), symargs

            elif operator == 'neg':
                if children[2][0] == '<bexprs>':
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                assert len(res) == 1
                a,_ = self._convert_to_sympy(res[0], symargs)
                return sympy.Not(a), symargs
            else:
                assert False

    def _flatten(self, bexprs):
        assert bexprs[0] == '<bexprs>'
        if len(bexprs[1]) == 1:
            return [bexprs[1][0]]
        else:
            assert len(bexprs[1]) == 3
            a = bexprs[1][0]
            comma = bexprs[1][1]
            rest = bexprs[1][2]
            return [a] + self._flatten(rest)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(BExpr):
    def _convert_to_sympy(self, bexpr_tree, symargs=None):
        def get_op(node):
            assert node[0] == &#x27;&lt;bop&gt;&#x27;, node[0]
            return &#x27;&#x27;.join([i[0] for i in node[1]])
        if symargs is None:
            symargs = {}
        name, children = bexpr_tree
        assert name == &#x27;&lt;bexpr&gt;&#x27;, name
        if len(children) == 1: # fault node
            name = fuzzer.tree_to_string(children[0])
            if not name: return None, symargs
            if name not in symargs:
                symargs[name] = sympy.symbols(name)
            return symargs[name], symargs
        else:
            operator = get_op(children[0])
            if operator == &#x27;and&#x27;:
                if children[2][0] == &#x27;&lt;bexprs&gt;&#x27;:
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.And(*[a for a,_ in sp]), symargs

            elif operator == &#x27;or&#x27;:
                if children[2][0] == &#x27;&lt;bexprs&gt;&#x27;:
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                sp = [self._convert_to_sympy(a, symargs) for a in res]
                return sympy.Or(*[a for a,_ in sp]), symargs

            elif operator == &#x27;neg&#x27;:
                if children[2][0] == &#x27;&lt;bexprs&gt;&#x27;:
                    res = self._flatten(children[2])
                else:
                    res = [children[2]]
                assert len(res) == 1
                a,_ = self._convert_to_sympy(res[0], symargs)
                return sympy.Not(a), symargs
            else:
                assert False

    def _flatten(self, bexprs):
        assert bexprs[0] == &#x27;&lt;bexprs&gt;&#x27;
        if len(bexprs[1]) == 1:
            return [bexprs[1][0]]
        else:
            assert len(bexprs[1]) == 3
            a = bexprs[1][0]
            comma = bexprs[1][1]
            rest = bexprs[1][2]
            return [a] + self._flatten(rest)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define the reverse. Given the `sympy` expression, we define a
procedure to convert it to the boolean data-structure.

<!--
############
class BExpr(BExpr):
    def _convert_sympy_to_bexpr(self, sexpr, log=False):
        if isinstance(sexpr, sympy.Symbol):
            return B(str(sexpr))
        elif isinstance(sexpr, sympy.Not):
            return NegB(self._convert_sympy_to_bexpr(sexpr.args[0]))
        elif isinstance(sexpr, sympy.And):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return FalseB # F & ~F == _|_
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return FalseB # F & ~F == _|_
            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if FalseB in sym_vars: return FalseB # if bottom is present in and, that is the result
            if TrueB in sym_vars:
                sym_vars = [s for s in sym_vars if s != TrueB] # base def does not do anything in and.
                if not sym_vars: return TrueB
            return AndB(sym_vars)
        elif isinstance(sexpr, sympy.Or):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(b)
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(a)

            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if TrueB in sym_vars: return TrueB # if original def is present in or, that is the result
            if FalseB in sym_vars:
                sym_vars = [s for s in sym_vars if s != FalseB]
                if not sym_vars: return FalseB
            return OrB(sym_vars)
        else:
            if log: print(repr(sexpr))
            assert False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(BExpr):
    def _convert_sympy_to_bexpr(self, sexpr, log=False):
        if isinstance(sexpr, sympy.Symbol):
            return B(str(sexpr))
        elif isinstance(sexpr, sympy.Not):
            return NegB(self._convert_sympy_to_bexpr(sexpr.args[0]))
        elif isinstance(sexpr, sympy.And):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return FalseB # F &amp; ~F == _|_
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return FalseB # F &amp; ~F == _|_
            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if FalseB in sym_vars: return FalseB # if bottom is present in and, that is the result
            if TrueB in sym_vars:
                sym_vars = [s for s in sym_vars if s != TrueB] # base def does not do anything in and.
                if not sym_vars: return TrueB
            return AndB(sym_vars)
        elif isinstance(sexpr, sympy.Or):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                if str(a.args[0]) == str(b): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(b)
            elif isinstance(b, sympy.Not):
                if str(b.args[0]) == str(a): return TrueB # F | ~F = U self._convert_sympy_to_bexpr(a)

            sym_vars = sorted([self._convert_sympy_to_bexpr(a) for a in sexpr.args], key=str)
            assert sym_vars
            if TrueB in sym_vars: return TrueB # if original def is present in or, that is the result
            if FalseB in sym_vars:
                sym_vars = [s for s in sym_vars if s != FalseB]
                if not sym_vars: return FalseB
            return OrB(sym_vars)
        else:
            if log: print(repr(sexpr))
            assert False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we stitch them together.

<!--
############
class BExpr(BExpr):
    def simple(self):
        if self._simple is None:
            self._simple = str(self._convert_sympy_to_bexpr(self._sympy))
        return self._simple

    def _simplify(self):
        e0, defs = self._convert_to_sympy(self._tree)
        e1 = sympy.to_dnf(e0)
        e2 = self._convert_sympy_to_bexpr(e1)
        v = str(e2)
        my_keys = [k for k in defs]
        for k in my_keys:
            del defs[k]
        return v, e1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(BExpr):
    def simple(self):
        if self._simple is None:
            self._simple = str(self._convert_sympy_to_bexpr(self._sympy))
        return self._simple

    def _simplify(self):
        e0, defs = self._convert_to_sympy(self._tree)
        e1 = sympy.to_dnf(e0)
        e2 = self._convert_sympy_to_bexpr(e1)
        v = str(e2)
        my_keys = [k for k in defs]
        for k in my_keys:
            del defs[k]
        return v, e1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
b = BExpr('and(and(f1,f2),f1)')
print(b.simple())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
b = BExpr(&#x27;and(and(f1,f2),f1)&#x27;)
print(b.simple())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now need to come to one of the main reasons for the existence of
this class. In later posts, we will see that we will need to
recreate a given nonterminal given the basic building blocks, and
the boolean expression of the nonterminal. So, what we will do is
to first parse the boolean expression using `BExpr`, then use
`sympy` to simplify (as we have shown above), then unwrap the
`sympy` one layer at a time, noting the operator used. When we
come to the faults (or their negations) themselves, we return
back from negation with their definitions from the original grammars,
and as we return from each layer, we reconstruct the required
expression from the given nonterminal definitions (or newly built ones)>

The `get_operator()` returns the
outer operator, `op_fst()` returns the first operator if the
operator was a negation (and throws exception if it is used
otherwise, and `op_fst_snd()` returns the first and second
parameters for the outer `and` or `or`.

<!--
############
class BExpr(BExpr):
    def get_operator(self):
        if isinstance(self._sympy, sympy.And): return 'and'
        elif isinstance(self._sympy, sympy.Or): return 'or'
        elif isinstance(self._sympy, sympy.Not): return 'neg'
        else: return ''

    def op_fst(self):
        op = self.get_operator()
        assert op == 'neg'
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]
        return bexpr

    def op_fst_snd(self):
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]

        bexpr_rest = BExpr(None)
        op = self.get_operator()

        if op == 'and':
            bexpr_rest._sympy = sympy.And(*self._sympy.args[1:])
        elif op == 'or':
            bexpr_rest._sympy = sympy.Or(*self._sympy.args[1:])
        else:
            assert False
        return bexpr, bexpr_rest

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(BExpr):
    def get_operator(self):
        if isinstance(self._sympy, sympy.And): return &#x27;and&#x27;
        elif isinstance(self._sympy, sympy.Or): return &#x27;or&#x27;
        elif isinstance(self._sympy, sympy.Not): return &#x27;neg&#x27;
        else: return &#x27;&#x27;

    def op_fst(self):
        op = self.get_operator()
        assert op == &#x27;neg&#x27;
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]
        return bexpr

    def op_fst_snd(self):
        bexpr = BExpr(None)
        bexpr._sympy = self._sympy.args[0]

        bexpr_rest = BExpr(None)
        op = self.get_operator()

        if op == &#x27;and&#x27;:
            bexpr_rest._sympy = sympy.And(*self._sympy.args[1:])
        elif op == &#x27;or&#x27;:
            bexpr_rest._sympy = sympy.Or(*self._sympy.args[1:])
        else:
            assert False
        return bexpr, bexpr_rest
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define two convenience functions.

<!--
############
class BExpr(BExpr):
    def with_key(self, k):
        s = self.simple()
        if s:
            return '<%s %s>' % (gatleast.stem(k), s)
        else:
            # this bexpr does not contain an expression.
            # So return the basic key
            return normalize(k)

    def negate(self):
        bexpr = BExpr(None)
        bexpr._sympy = sympy.Not(self._sympy).simplify()
        return bexpr

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(BExpr):
    def with_key(self, k):
        s = self.simple()
        if s:
            return &#x27;&lt;%s %s&gt;&#x27; % (gatleast.stem(k), s)
        else:
            # this bexpr does not contain an expression.
            # So return the basic key
            return normalize(k)

    def negate(self):
        bexpr = BExpr(None)
        bexpr._sympy = sympy.Not(self._sympy).simplify()
        return bexpr
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, given a grammar, we need to find all undefined nonterminals that
we need to reconstruct. This is done as follows.

<!--
############
def find_all_nonterminals(g):
    lst = []
    for k in g:
        for r in g[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    lst.append(t)
    return list(sorted(set(lst)))

def undefined_keys(grammar):
    keys = find_all_nonterminals(grammar)
    return [k for k in keys if k not in grammar]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_all_nonterminals(g):
    lst = []
    for k in g:
        for r in g[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    lst.append(t)
    return list(sorted(set(lst)))

def undefined_keys(grammar):
    keys = find_all_nonterminals(grammar)
    return [k for k in keys if k not in grammar]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage.

<!--
############
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **{'<start and(D1,Z1)>': [['<expr and(D1,Z1)>']]}}
keys = undefined_keys(grammar)
print(keys)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **{&#x27;&lt;start and(D1,Z1)&gt;&#x27;: [[&#x27;&lt;expr and(D1,Z1)&gt;&#x27;]]}}
keys = undefined_keys(grammar)
print(keys)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we will see how to reconstruct grammars given the building blocks.
Our `reconstruct_rules_from_bexpr()` is a recursive procedure that will take a
given key, the corresponding refinement in terms of a `BExpr()` instance, the
grammar containing the nonterminals, and it will attempt to reconstruct the
key definition from the given nonterminals,

<!--
############
class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

    def reconstruct_rules_from_bexpr(self, key, bexpr):
        f_key = bexpr.with_key(key)
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == 'and':
                return self.reconstruct_and_bexpr(key, bexpr)
            elif operator == 'or':
                return self.reconstruct_or_bexpr(key, bexpr)
            elif operator == 'neg':
                return self.reconstruct_neg_bexpr(key, bexpr)
            elif operator == '':
                assert False
            else:
                assert False

    def reconstruct_neg_bexpr(self, key, bexpr):
        assert False

    def reconstruct_and_bexpr(self, key, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.with_key(key)
        d1, s1 = self.reconstruct_rules_from_bexpr(key, fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(key, snd)
        and_rules = gmultiple.and_definitions(d1, d2)
        return and_rules, f_key

    def reconstruct_or_bexpr(self, key, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.with_key(key)
        d1, s1 = self.reconstruct_rules_from_bexpr(key, fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(key, snd)
        or_rules = gmultiple.or_definitions(d1, d2)
        return or_rules, f_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

    def reconstruct_rules_from_bexpr(self, key, bexpr):
        f_key = bexpr.with_key(key)
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == &#x27;and&#x27;:
                return self.reconstruct_and_bexpr(key, bexpr)
            elif operator == &#x27;or&#x27;:
                return self.reconstruct_or_bexpr(key, bexpr)
            elif operator == &#x27;neg&#x27;:
                return self.reconstruct_neg_bexpr(key, bexpr)
            elif operator == &#x27;&#x27;:
                assert False
            else:
                assert False

    def reconstruct_neg_bexpr(self, key, bexpr):
        assert False

    def reconstruct_and_bexpr(self, key, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.with_key(key)
        d1, s1 = self.reconstruct_rules_from_bexpr(key, fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(key, snd)
        and_rules = gmultiple.and_definitions(d1, d2)
        return and_rules, f_key

    def reconstruct_or_bexpr(self, key, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.with_key(key)
        d1, s1 = self.reconstruct_rules_from_bexpr(key, fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(key, snd)
        or_rules = gmultiple.or_definitions(d1, d2)
        return or_rules, f_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
my_bexpr = BExpr('and(D1,Z1)')
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **hdd.EXPR_GRAMMAR}
rr = ReconstructRules(grammar)
d1, s1 = rr.reconstruct_rules_from_bexpr('<start>', my_bexpr)
grammar[s1] = d1
remaining = undefined_keys(grammar)
print(d1,s1)
print("remaining:", remaining)
rr = ReconstructRules({**grammar, **{s1:d1}})
d2, s2 = rr.reconstruct_rules_from_bexpr(remaining[0], my_bexpr)
grammar[s2] = d2
remaining = undefined_keys(grammar)
print(d2,s2)
print("remaining:", remaining)

my_bexpr = BExpr('or(D1,Z1)')
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **hdd.EXPR_GRAMMAR}
rr = ReconstructRules(grammar)
d1, s1 = rr.reconstruct_rules_from_bexpr('<start>', my_bexpr)
grammar[s1] = d1
remaining = undefined_keys(grammar)
print(d1,s1)
print("remaining:", remaining)
rr = ReconstructRules({**grammar, **{s1:d1}})
d2, s2  = rr.reconstruct_rules_from_bexpr(remaining[0], my_bexpr)
grammar[s2] = d2
remaining = undefined_keys(grammar)
print(d2,s2)
print("remaining:", remaining)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_bexpr = BExpr(&#x27;and(D1,Z1)&#x27;)
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **hdd.EXPR_GRAMMAR}
rr = ReconstructRules(grammar)
d1, s1 = rr.reconstruct_rules_from_bexpr(&#x27;&lt;start&gt;&#x27;, my_bexpr)
grammar[s1] = d1
remaining = undefined_keys(grammar)
print(d1,s1)
print(&quot;remaining:&quot;, remaining)
rr = ReconstructRules({**grammar, **{s1:d1}})
d2, s2 = rr.reconstruct_rules_from_bexpr(remaining[0], my_bexpr)
grammar[s2] = d2
remaining = undefined_keys(grammar)
print(d2,s2)
print(&quot;remaining:&quot;, remaining)

my_bexpr = BExpr(&#x27;or(D1,Z1)&#x27;)
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **hdd.EXPR_GRAMMAR}
rr = ReconstructRules(grammar)
d1, s1 = rr.reconstruct_rules_from_bexpr(&#x27;&lt;start&gt;&#x27;, my_bexpr)
grammar[s1] = d1
remaining = undefined_keys(grammar)
print(d1,s1)
print(&quot;remaining:&quot;, remaining)
rr = ReconstructRules({**grammar, **{s1:d1}})
d2, s2  = rr.reconstruct_rules_from_bexpr(remaining[0], my_bexpr)
grammar[s2] = d2
remaining = undefined_keys(grammar)
print(d2,s2)
print(&quot;remaining:&quot;, remaining)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now define the complete reconstruction

<!--
############
class ReconstructRules(ReconstructRules):
    def reconstruct_key(self, refined_key, log=False):
        keys = [refined_key]
        defined = set()
        while keys:
            if log: print(len(keys))
            key_to_reconstruct, *keys = keys
            if log: print('reconstructing:', key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception('Key found:', key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(gatleast.refinement(key_to_reconstruct))
            nrek = gmultiple.normalize(key_to_reconstruct)
            if bexpr.simple():
                nkey = bexpr.with_key(key_to_reconstruct)
                if log: print('simplified_to:', nkey)
                d, s = self.reconstruct_rules_from_bexpr(nrek, bexpr)
                self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            else:
                nkey = nrek # base key
            keys = undefined_keys(self.grammar)
        return self.grammar, refined_key


def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = gatleast.grammar_gc(rr.reconstruct_key(start, log))
    return grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules(ReconstructRules):
    def reconstruct_key(self, refined_key, log=False):
        keys = [refined_key]
        defined = set()
        while keys:
            if log: print(len(keys))
            key_to_reconstruct, *keys = keys
            if log: print(&#x27;reconstructing:&#x27;, key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception(&#x27;Key found:&#x27;, key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(gatleast.refinement(key_to_reconstruct))
            nrek = gmultiple.normalize(key_to_reconstruct)
            if bexpr.simple():
                nkey = bexpr.with_key(key_to_reconstruct)
                if log: print(&#x27;simplified_to:&#x27;, nkey)
                d, s = self.reconstruct_rules_from_bexpr(nrek, bexpr)
                self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            else:
                nkey = nrek # base key
            keys = undefined_keys(self.grammar)
        return self.grammar, refined_key


def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = gatleast.grammar_gc(rr.reconstruct_key(start, log))
    return grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G}
g_, s_ = complete(grammar, '<start and(D1,Z1)>')
gf = fuzzer.LimitFuzzer(g_)
for i in range(10):
    v = gf.iter_fuzz(key=s_, max_depth=10)
    assert gatleast.expr_div_by_zero(v) and hdd.expr_double_paren(v)
    print(v)

grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G}
g_, s_ = complete(grammar, '<start or(D1,Z1)>')
gf = fuzzer.LimitFuzzer(g_)
for i in range(10):
    v = gf.iter_fuzz(key=s_, max_depth=10)
    assert gatleast.expr_div_by_zero(v) or hdd.expr_double_paren(v)
    print(v)
    if gatleast.expr_div_by_zero(v) == hdd.PRes.success: print('>', 1)
    if hdd.expr_double_paren(v) == hdd.PRes.success: print('>',2)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G}
g_, s_ = complete(grammar, &#x27;&lt;start and(D1,Z1)&gt;&#x27;)
gf = fuzzer.LimitFuzzer(g_)
for i in range(10):
    v = gf.iter_fuzz(key=s_, max_depth=10)
    assert gatleast.expr_div_by_zero(v) and hdd.expr_double_paren(v)
    print(v)

grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G}
g_, s_ = complete(grammar, &#x27;&lt;start or(D1,Z1)&gt;&#x27;)
gf = fuzzer.LimitFuzzer(g_)
for i in range(10):
    v = gf.iter_fuzz(key=s_, max_depth=10)
    assert gatleast.expr_div_by_zero(v) or hdd.expr_double_paren(v)
    print(v)
    if gatleast.expr_div_by_zero(v) == hdd.PRes.success: print(&#x27;&gt;&#x27;, 1)
    if hdd.expr_double_paren(v) == hdd.PRes.success: print(&#x27;&gt;&#x27;,2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
