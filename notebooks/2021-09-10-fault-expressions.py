# ---
# published: true
# title: Fault Expressions
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In my previous posts on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
# and [multiple faults](/post/2021/09/10/multiiple-fault-grammars/) I introduced
# the evocative patterns and how to combine them using `and`. As our expressions
# keep growing in complexity, we need a better way to mange them. This post
# introduces a language for the suffixes so that we will have an easier time
# managing them.
# 
# As before, let us start with importing our required modules.

#@mpmath-1.2.1-py3-none-any.whl
#@sympy-1.8-py3-none-any.whl

import sympy

# Our language is a simple language of boolean algebra. That is, it is the
# langauge of expressions in the specialization for a nonterminal such as `<A and(f1,f2)>`
# It is defined by the following grammar.

import string
BEXPR_GRAMMAR = {
    '<start>': [['<bexpr>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexpr>', ',', '<bexpr>', ')'],
        ['<bop>',  '(', '<bexpr>', ',', '<bexpr>', ')'],
        ['<bop>', '(', '<bexpr>', ')'],
        ['<fault>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<fault>': [['<letters>'], []],
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']],
    '<letter>': [[i] for i in (string.ascii_lowercase + string.ascii_uppercase + string.digits) + '_+*.-']
}
BEXPR_START = '<start>'

# We need the ability to parse any expressions. So, let us load the parser

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

# The parser

earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')

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

# Next, we define the standard teerms of the boolean algebra. `or(.,.)`, `and(.,.)` and `neg(.)`

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

# Next, we come to the actual representative class.

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

    def simple(self):
        if self._simple is None:
            self._simple = str(self._convert_sympy_to_bexpr(self._sympy))
        return self._simple

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR, canonical=True)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][0]
        return bexpr

    def with_key(self, k):
        s = self.simple()
        if s: return '<%s %s>' % (gatleast.stem(k), s)
        return normalize(k)

    def _simplify(self):
        e0, defs = self._convert_to_sympy(self._tree)
        e1 = sympy.to_dnf(e0)
        e2 = self._convert_sympy_to_bexpr(e1)
        v = str(e2)
        my_keys = [k for k in defs]
        for k in my_keys:
            del defs[k]
        return v, e1

    def is_neg_sym(self):
        op = self.get_operator()
        if op != 'neg': return False
        if not isinstance(self._sympy.args[0], sympy.Symbol): return False
        return True

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

    def negate(self):
        bexpr = BExpr(None)
        bexpr._sympy = sympy.Not(self._sympy).simplify()
        return bexpr

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

def disj(k1, k2, simplify=False):
    if k1 == k2: return k1
    if not refinement(k1): return k1
    if not refinement(k2): return k2
    b = BExpr('or(%s,%s)' % (refinement(k1), refinement(k2)))
    return b.with_key(k1)

def conj(k1, k2, simplify=False):
    if k1 == k2: return k1
    if not refinement(k1): return k2
    if not refinement(k2): return k1
    b = BExpr('and(%s,%s)' % (refinement(k1), refinement(k2)))
    return b.with_key(k1)

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

def reconstruct_neg_bexpr(grammar, key, bexpr):
    fst = bexpr.op_fst()
    base_grammar, base_start = normalize_grammar(grammar), normalize(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    g1, saved_keys, undef_keys  = remove_unused(g1_, s1)
    g, s, r = negate_grammar_(g1, s1, base_grammar, base_start)
    assert s in g, s
    g = {**grammar, **g1, **g, **saved_keys}
    return g, s, undefined_keys(g)

def reconstruct_and_bexpr(grammar, key, bexpr):
    fst, snd = bexpr.op_fst_snd()
    f_key = bexpr.with_key(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    if fst == snd: # or of same keys is same
        print(f_key)
        g = {**grammar, **g1_}
        g[f_key] = g[s1]
        return g, f_key, undefined_keys(g)
    g1, saved_keys1, undef_keys1  = remove_unused(g1_, s1)
    g2_, s2, r2 = reconstruct_rules_from_bexpr(key, snd, grammar)
    g2, saved_keys2, undef_keys2  = remove_unused(g2_, s2)
    g, s, r = and_grammars_(g1, s1, g2, s2)
    assert s in g
    g = {**grammar, **g1, **g2, **g, **saved_keys1, **saved_keys2}
    assert f_key in g, f_key
    return g, s, undefined_keys(g)

def reconstruct_or_bexpr(grammar, key, bexpr):
    fst, snd = bexpr.op_fst_snd()
    f_key = bexpr.with_key(key)
    g1_, s1, r1 = reconstruct_rules_from_bexpr(key, fst, grammar)
    assert fst.with_key(key) in g1_
    if fst == snd: # and of same keys is same
        g = {**grammar, **g1_}
        g[f_key] = g[s1]
        return g, f_key, undefined_keys(g)
    g1, saved_keys1, undef_keys1  = remove_unused(g1_, s1)
    g2_, s2, r2 = reconstruct_rules_from_bexpr(key, snd, grammar)
    assert snd.with_key(key) in g2_
    g2, saved_keys2, undef_keys2  = remove_unused(g2_, s2)
    g, s, r = or_grammars_(g1, s1, g2, s2)
    assert s in g
    g = {**grammar, **g1, **g2, **g, **saved_keys1, **saved_keys2}
    assert f_key in g, (f_key, s)
    return g, s, undefined_keys(g)


def reconstruct_rules_from_bexpr(key, bexpr, grammar):
    f_key = bexpr.with_key(key)
    if f_key in grammar:
        return grammar, f_key, []
    else:
        new_grammar = grammar
        operator = bexpr.get_operator()
        if operator == 'and':
            return reconstruct_and_bexpr(grammar, key, bexpr)
        elif operator == 'or':
            return reconstruct_or_bexpr(grammar, key, bexpr)
        elif operator == 'neg':
            return reconstruct_neg_bexpr(grammar, key, bexpr)
        elif operator == '':
            # probably we have a negation
            assert False
            #return reconstruct_neg_fault(grammar, key, bexpr)
        else:
            assert False

def reconstruct_key(refined_key, grammar, log=False):
    keys = [refined_key]
    defined = set()
    while keys:
        if log: print(len(keys))
        key_to_reconstruct, *keys = keys
        if log: print('reconstructing:', key_to_reconstruct)
        if key_to_reconstruct in defined:
            raise Exception('Key found:', key_to_reconstruct)
        defined.add(key_to_reconstruct)
        bexpr = BExpr(refinement(key_to_reconstruct))
        nrek = normalize(key_to_reconstruct)
        if bexpr.simple():
            nkey = bexpr.with_key(key_to_reconstruct)
            if log: print('simplified_to:', nkey)
            grammar, s, refs = reconstruct_rules_from_bexpr(nrek, bexpr, grammar)
        else:
            nkey = nrek # base key
        assert nkey in grammar
        grammar[key_to_reconstruct] = grammar[nkey]
        keys = undefined_keys(grammar)
    return grammar


def find_reachable_keys_unchecked(grammar, key, reachable_keys=None, found_so_far=None):
    if reachable_keys is None: reachable_keys = {}
    if found_so_far is None: found_so_far = set()

    for rule in grammar.get(key, []):
        for token in rule:
            if not fuzzer.is_nonterminal(token): continue
            if token in found_so_far: continue
            found_so_far.add(token)
            if token in reachable_keys:
                for k in reachable_keys[token]:
                    found_so_far.add(k)
            else:
                keys = find_reachable_keys_unchecked(grammar, token, reachable_keys, found_so_far)
                # reachable_keys[token] = keys <- found_so_far contains results from earlier
    return found_so_far

def reachable_dict_unchecked(grammar):
    reachable = {}
    for key in grammar:
        keys = find_reachable_keys_unchecked(grammar, key, reachable)
        reachable[key] = keys
    return reachable

def complete(grammar, start, log=False):
    keys = undefined_keys(grammar)
    reachable_keys = reachable_dict_unchecked(grammar)
    for key in keys:
        if key not in reachable_keys[start]: continue
        grammar = reconstruct_key(key, grammar, log)
    grammar_, start_ = grammar_gc(grammar, start)
    return grammar_, start_

# Usage

if __name__ == '__main__':
    g_, s_ = complete(g, s)
    gf = fuzzer.LimitFuzzer(g_)
    for i in range(10):
        print(gf.iter_fuzz(key=s_, max_depth=10))
