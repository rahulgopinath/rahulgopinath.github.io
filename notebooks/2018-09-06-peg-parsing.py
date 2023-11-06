# ---
# published: true
# title: Recursive descent parsing with Parsing Expression (PEG) and Context Free (CFG) Grammars
# layout: post
# comments: true
# tags: parsing
# categories: post
# ---
 
# In the [previous](/post/2018/09/05/top-down-parsing/) post, I showed how to
# write a simple recursive descent parser by hand -- that is using a set of
# mutually recursive procedures. Actually, I lied when I said context-free.
# The common hand-written parsers are usually an encoding of a kind of grammar
# called _Parsing Expression Grammar_ or _PEG_ for short.

# The difference between _PEG_ and a _CFG_ is that _PEG_ does not admit
# ambiguity. In particular, _PEG_ uses ordered choice in its alternatives.
# Due to the ordered choice, the ordering of alternatives is important.

# A few interesting things about _PEG_:
# * We know that _L(PEG)_ is not a subset of _L(CFG)_ (There are [languages](https://stackoverflow.com/a/46743864/1420407) that can be expressed with a _PEG_ that can not be expressed with a _CFG_ -- for example, $$a^nb^nc^n$$).
# * We do not know if _L(PEG)_ is a superset of _CFL_. However, given that all [PEGs can be parsed in $$O(n)$$](https://en.wikipedia.org/wiki/Parsing_expression_grammar), and the best general _CFG_ parsers can only reach $$O(n^{(3-\frac{e}{3})})$$ due to the equivalence to boolean matrix multiplication[^valiant1975general] [^lee2002fast]. 
# * We do know that _L(PEG)_ is at least as large as deterministic _CFL_.
# * We also [know](https://arxiv.org/pdf/1304.3177.pdf) that an _LL(1)_ grammar can be interpreted either as a _CFG_ or a _PEG_ and it will describe the same language. Further, any _LL(k)_ grammar can be translated to _L(PEG)_, but reverse is not always true -- [it will work only if the PEG lookahead pattern can be reduced to a DFA](https://stackoverflow.com/a/46743864/1420407).
# 
# The problem with what we did in the previous post is that it is a rather naive implementation. In particular, there could be a lot of backtracking, which can make the runtime explode. One solution to that is incorporating memoization. Since we start with automatic generation of parser from a grammar (unlike previously, where we explored a handwritten parser first), we will take a slightly different tack in writing the algorithm.
# 
# ## PEG Recognizer
# 
# The idea behind a simple _PEG_ recognizer is that, you try to unify the string you want to match with the corresponding key in the grammar. If the key is not present in the grammar, it is a literal, which needs to be matched with string equality.
# If the key is present in the grammar, get the corresponding productions (rules) for that key,  and start unifying each rule one by one on the string to be matched.

def unify_key(grammar, key, text):
    if key not in grammar:
        return text[len(key):] if text.startswith(key) else None 
    rules = grammar[key]
    for rule in rules:
        l = unify_rule(grammar, rule, text)
        if l is not None: return l
    return None

# For unifying rules, the idea is similar. We take each token in the rule, and try to unify that token with the string to be matched. We rely on `unify_key` for doing the unification of the token. if the unification fails, we return empty handed.

def unify_rule(grammar, rule, text):
    for token in rule:
        text = unify_key(grammar, token, text)
        if text is None: return None
    return text

# Let us define a grammar to test it out.
term_grammar = {
    '<expr>': [
        ['<term>', '<add_op>', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '<mul_op>', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [[str(i)] for i in list(range(10))],
    '<add_op>': [['+'], ['-']],
    '<mul_op>': [['*'], ['/']]
}

# The driver:

if __name__ == '__main__':
    to_parse = '1+2'
    rest = unify_key(term_grammar, '<expr>', to_parse)
    assert rest == ''
    to_parse = '1%2'
    result = unify_key(term_grammar, '<expr>', to_parse)
    assert result == '%2'

# ## PEG Parser
# When we implemented the `unify_key`, we made an important decision, which was that, we return as soon as a match was found. This is what distinguishes a `PEG` parser from a general `CFG` parser. In particular it means that rules have to be ordered.
# That is, the following grammar wont work:
# 
# ```ebnf
# ifmatch = IF (expr) THEN stmts
#         | IF (expr) THEN stmts ELSE stmts
# ```
# It has to be written as the following so that the rule that can match the longest string will come first. 
# ```ebnf
# ifmatch = IF (expr) THEN stmts ELSE stmts
#         | IF (expr) THEN stmts
# ```
# If we now parse an `if` statement without else using the above grammar, such a `IF (a=b) THEN return 0`, the first rule will fail, and the parse will start for the second rule again at `IF`. This backtracking is unnecessary as one can see that `IF (a=b) THEN return 0` is already parsed by all terms in the second rule. What we want is to save the old parses so that we can simply return the already parsed result. That is,
# 
# ```python
#    if seen((token, text, at)):
#        return old_result
# ```
# Fortunately, Python makes this easy using `functools.lru_cache` which
# provides cheap memoization to functions. Adding memoizaion, saving results, and reorganizing code, we have our _PEG_ parser.

import sys
import functools

class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    @functools.lru_cache(maxsize=None)
    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

# The driver:

if __name__ == '__main__':
    to_parse = '1+2'
    result = peg_parse(term_grammar).unify_key('<expr>', to_parse)
    assert (len(to_parse) - result[0]) == 0
    print(result[1])

# What we have here is only a subset of _PEG_ grammar. A _PEG_ grammar can contain
# 
# * Sequence: e1 e2
# * Ordered choice: e1 / e2
# * Zero-or-more: e*
# * One-or-more: e+
# * Optional: e?
# * And-predicate: &e -- match `e` but do not consume any input
# * Not-predicate: !e
# 
# We are yet to provide _e*_, _e+_, and _e?_. However, these are only conveniences. One can easily modify any _PEG_ that uses them to use grammar rules instead. The effect of predicates on the other hand can not be easily produced.  However, the lack of predicates does not change[^ford2004parsing] the class of languages that such grammars can match, and even without the predicates, our _PEG_ can be useful for easily representing a large category of programs.
# 
# Note: This implementation will blow the stack pretty fast if we attempt to parse any expressions that are reasonably large (where some node in the derivation tree has a depth of 500) because Python provides very limited stack. One can improve the situation slightly by inlining the `unify_rule()`.

class peg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, at=0):
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)

        rules = self.grammar[key]
        for rule in rules:
            results = []
            tfrom = at
            for part in rule:
                tfrom, res_ = self.unify_key(part, text, tfrom)
                if res_ is None:
                    l, results = tfrom, None
                    break
                results.append(res_)
            l, res = tfrom, results
            if res is not None: return l, (key, res)
        return (0, None)

# This gets us to derivation trees with at a depth of 1000 (or more if we increase the `sys.setrecursionlimit()`). We can also turn this to a completely iterative solution if we simulate the stack (formal arguments, locals, return value) ourselves rather than relying on the Python stack frame.
# 
# ## Context Free Parser
# 
# It is fairly easy to turn this parser into a context-free grammar parser instead. The main idea is to keep a list of parse points, and advance them one at a time.
 
class cfg_parse:
    def __init__(self, grammar):
        self.grammar = grammar

    def unify_key(self, key, text, tfrom):
        if key not in self.grammar:
            if text[tfrom:].startswith(key):
                return [(tfrom + len(key), (key, []))]
            else:
                return []
        else:
            tfroms_ = []
            rules = self.grammar[key]
            for rule in rules:
                new_tfroms = self.unify_rule(rule, text, tfrom)
                for at, nt in new_tfroms:
                    tfroms_.append((at, (key, nt)))
            return tfroms_
        assert False

    def unify_rule(self, parts, text, tfrom):
        tfroms = [(tfrom, [])]
        for part in parts:
            new_tfroms = []
            for at, nt in tfroms:
                tfs = self.unify_key(part, text, at)
                for at_, nt_ in tfs:
                    new_tfroms.append((at_, nt + [nt_]))
            tfroms = new_tfroms
        return tfroms
# Driver

if __name__ == '__main__':
    to_parse = '1+2'
    p = cfg_parse(term_grammar)
    result = p.unify_key('<expr>', to_parse, 0)
    for l,res in result:
        if l == len(to_parse):
            print(res)

# Let us define a simple viewer

def display_treeb(node, level=0, c='-'):
    key, children = node
    if children:
        display_treeb(children[0], level + 1, c='/')
    print(' ' * 4 * level + c+'> ' + key + '|')
    if len(children) > 1:
        display_treeb(children[1], level + 1, c='\\')

# Driver

if __name__ == '__main__':
    to_parse = '1+2'
    p = cfg_parse(term_grammar)
    result = p.unify_key('<expr>', to_parse, 0)
    for l,res in result:
        if l == len(to_parse):
            display_treeb(res)


# The above can only work with binary trees. Here is another that can work with all trees.

def display_tree(node, level=0, c='-'):
    key, children = node
    print(' ' * 4 * level + c+'> ' + key)
    for c in children:
        display_tree(c, level + 1, c='+')

# Using
if __name__ == '__main__':
    to_parse = '1+2+3+4*5/6'
    p = cfg_parse(term_grammar)
    result = p.unify_key('<expr>', to_parse, 0)
    for l,res in result:
        if l == len(to_parse):
            display_tree(res)


# This implementation is quite limited in that we have lost the ability to memoize (can be added back), and can not handle left recursion. See the [Earley parser](https://www.fuzzingbook.org/html/Parser.html) for a parser without these drawbacks.
# 
# Note: I recently found a very tiny PEG parser described [here](https://news.ycombinator.com/item?id=3202505).
#  
# [^valiant1975general]: Valiant, Leslie G. "General context-free recognition in less than cubic time." Journal of computer and system sciences 10.2 (1975): 308-315. 
# 
# [^lee2002fast]: Lee, Lillian. "Fast context-free grammar parsing requires fast boolean matrix multiplication." Journal of the ACM (JACM) 49.1 (2002): 1-15.
# 
# [^ford2004parsing]: Ford, Bryan. "Parsing expression grammars: a recognition-based syntactic foundation." Proceedings of the 31st ACM SIGPLAN-SIGACT symposium on Principles of programming languages. 2004.  <https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf>

