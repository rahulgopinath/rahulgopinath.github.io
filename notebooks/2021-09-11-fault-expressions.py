# ---
# published: true
# title: Fault Expressions for Specializing Context-Free Grammars
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# 
# This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)
# 
# In my previous posts on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
# and [multiple faults](/post/2021/09/10/multiple-fault-grammars/) I introduced
# the evocative patterns and how to combine them using `and`. As our expressions
# keep growing in complexity, we need a better way to mange them. This post
# introduces a language for the suffixes so that we will have an easier time
# managing them.
# 
# As before, let us start with importing our required modules.

#^
# sympy

#@
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl

# The imported modules

import earleyparser
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gmultiplefaults as gmultiple

# **Note** `sympy` may not load immediately. Either click on the [run] button
# first before you click the [run all] or if you get errors, and the `sympy`
# import seems to not have been executed, try clicking on the [run] button again.

import sympy

# Our language is a simple language of boolean algebra. That is, it is the
# language of expressions in the specialization for a nonterminal such as `<A and(f1,f2)>`
# It is defined by the following grammar.

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

# Next, we need a data structure to represent the boolean language.
# First we represent our literals using `LitB` class.

class LitB:
    def __init__(self, a): self.a = a
    def __str__(self): return self.a

# There are two boolean literals. The top and the bottom. The top literal
# also (T) essentially indicates that there is no specialization of the base
# nonterminal. For e.g. `<A>` is a top literal.
# Hence, we indicate it by an empty string.

TrueB = LitB('')

# The bottom literal indicates that there are no possible members for this
# particular nonterminal. For e.g. <A _|_> indicates that this is empty.
# We indicate it by the empty symbol _|_.

FalseB = LitB('_|_')

# Next, we define the standard terms of the boolean algebra. `or(.,.)`, `and(.,.)` and `neg(.)`

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

# We then come to the actual representative class. The class is initialized by
# providing it with a boolean expression.

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

    def create_new(self, s):
        return BExpr(s)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][0]
        return bexpr

    def _simplify(self):
        return None,None

# Using it.

if __name__ == '__main__':
    b = BExpr('and(and(f1,f2),f1)')
    fuzzer.display_tree(b._tree)

# Now, we need to define how to simplify boolean expressions. For example,
# we want to simplify `and(and(f1,f2),f1)` to just `and(f1,f2)`. Since this
# is already offered by `sympy` we use that.
#
# First we define a procedure that given the parse tree, converts it to a sympy
# expression.

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

# Next, we define the reverse. Given the `sympy` expression, we define a
# procedure to convert it to the boolean data-structure.

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
            s = [self._convert_sympy_to_bexpr(a) for a in sexpr.args]
            sym_vars = sorted(s, key=str)
            assert sym_vars
            if FalseB in sym_vars:
                # if bottom is present in and, that is the result
                return FalseB
            if TrueB in sym_vars:
                # base def does not do anything in and.
                sym_vars = [s for s in sym_vars if s != TrueB]
                if not sym_vars: return TrueB
            return AndB(sym_vars)
        elif isinstance(sexpr, sympy.Or):
            a = sexpr.args[0]
            b = sexpr.args[1]
            if isinstance(a, sympy.Not):
                # F | ~F = U self._convert_sympy_to_bexpr(b)
                if str(a.args[0]) == str(b): return TrueB
            elif isinstance(b, sympy.Not):
                # F | ~F = U self._convert_sympy_to_bexpr(a)
                if str(b.args[0]) == str(a): return TrueB

            s = [self._convert_sympy_to_bexpr(a) for a in sexpr.args]
            sym_vars = sorted(s, key=str)
            assert sym_vars
            if TrueB in sym_vars:
                # if original def is present in or, that is the result
                return TrueB
            if FalseB in sym_vars:
                sym_vars = [s for s in sym_vars if s != FalseB]
                if not sym_vars: return FalseB
            return OrB(sym_vars)
        else:
            if log: print(repr(sexpr))
            assert False

# Finally, we stitch them together.

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

# Using it.

if __name__ == '__main__':
    b = BExpr('and(and(f1,f2),f1)')
    print(b.simple())

# We now need to come to one of the main reasons for the existence of
# this class. In later posts, we will see that we will need to
# recreate a given nonterminal given the basic building blocks, and
# the boolean expression of the nonterminal. So, what we will do is
# to first parse the boolean expression using `BExpr`, then use
# `sympy` to simplify (as we have shown above), then unwrap the
# `sympy` one layer at a time, noting the operator used. When we
# come to the faults (or their negations) themselves, we return
# back from negation with their definitions from the original grammars,
# and as we return from each layer, we reconstruct the required
# expression from the given nonterminal definitions (or newly built ones)>
# 
# The `get_operator()` returns the
# outer operator, `op_fst()` returns the first operator if the
# operator was a negation (and throws exception if it is used
# otherwise, and `op_fst_snd()` returns the first and second
# parameters for the outer `and` or `or`.

class BExpr(BExpr):
    def get_operator(self):
        if isinstance(self._sympy, sympy.And): return 'and'
        elif isinstance(self._sympy, sympy.Or): return 'or'
        elif isinstance(self._sympy, sympy.Not): return 'neg'
        else: return ''

    def op_fst(self):
        op = self.get_operator()
        assert op == 'neg'
        bexpr = self.create_new(None)
        bexpr._sympy = self._sympy.args[0]
        return bexpr

    def op_fst_snd(self):
        bexpr = self.create_new(None)
        bexpr._sympy = self._sympy.args[0]

        bexpr_rest = self.create_new(None)
        op = self.get_operator()

        if op == 'and':
            bexpr_rest._sympy = sympy.And(*self._sympy.args[1:])
        elif op == 'or':
            bexpr_rest._sympy = sympy.Or(*self._sympy.args[1:])
        else:
            assert False
        return bexpr, bexpr_rest

# We also define two convenience functions.

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
        bexpr = self.create_new(None)
        bexpr._sympy = sympy.Not(self._sympy).simplify()
        return bexpr

# Next, given a grammar, we need to find all undefined nonterminals that
# we need to reconstruct. This is done as follows.

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

# Usage.

if __name__ == '__main__':
    grammar ={**gmultiple.EXPR_DZERO_G,
              **gmultiple.EXPR_DPAREN_G,
              **{'<start and(D1,Z1)>': [['<expr and(D1,Z1)>']]}}
    keys = undefined_keys(grammar)
    print(keys)

# Next, we will see how to reconstruct grammars given the building blocks.
# Our `reconstruct_rules_from_bexpr()` is a recursive procedure that will take a
# given key, the corresponding refinement in terms of a `BExpr()` instance, the
# grammar containing the nonterminals, and it will attempt to reconstruct the
# key definition from the given nonterminals,

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
            else:
                return self.reconstruct_orig_bexpr(key, bexpr)

    def reconstruct_orig_bexpr(self, key, bexpr):
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

# Using

if __name__ == '__main__':
    import hdd
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

# We now define the complete reconstruction

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

# Usage

if __name__ == '__main__':
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

