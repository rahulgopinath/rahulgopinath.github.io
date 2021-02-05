---
published: true
title: Recursive descent parsing with Parsing Expression Grammars (PEG)
layout: post
comments: true
tags: parsing
categories: post
---
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt.min.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/skulpt-stdlib.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/env/editor.js" type="text/javascript"></script>

In the [previous](/post/2018/09/05/top-down-parsing/) post, I showed how to write a simple recursive descent parser by hand -- that is using a set of mutually recursive procedures. Actually, I lied when I said context-free. The common hand-written parsers are usually an encoding of a kind of grammar called _Parsing Expression Grammar_ or _PEG_ for short.

The difference between _PEG_ and a _CFG_ is that _PEG_ does not admit ambiguity. In particular, _PEG_ uses ordered choice in its alternatives. Due to the ordered choice, the ordering of alternatives is important.

A few interesting things about _PEG_:
* We know that _L(PEG)_ is not a subset of _L(CFG)_ (There are [languages](https://stackoverflow.com/a/46743864/1420407) that can be expressed with a _PEG_ that can not be expressed with a _CFG_ -- for example, $$a^nb^nc^n$$).
* We do not know if _L(PEG)_ is a superset of _CFL_. However, given that all [PEGs can be parsed in $$O(n)$$](https://en.wikipedia.org/wiki/Parsing_expression_grammar), and the best general _CFG_ parsers can only reach $$O(n^{(3-\frac{e}{3})})$$ due to the equivalence to boolean matrix multiplication[^valiant1975general][^lee2002fast]. 
* We do know that _L(PEG)_ is at least as large as deterministic _CFL_.
* We also [know](https://arxiv.org/pdf/1304.3177.pdf) that an _LL(1)_ grammar can be interpreted either as a _CFG_ or a _PEG_ and it will describe the same language. Further, any _LL(k)_ grammar can be translated to _L(PEG)_, but reverse is not always true -- [it will work only if the PEG lookahead pattern can be reduced to a DFA](https://stackoverflow.com/a/46743864/1420407).

The problem with what we did in the previous post is that it is a rather naive implementation. In particular, there could be a lot of backtracking, which can make the runtime explore. One solution to that is incorporating memoization. Since we start with automatic generation of parser from a grammar (unlike previously, where we explored a handwritten parser first), we will take a slightly different tack in writing the algorithm.

The idea behind a simple _PEG_ parser is that, you try to unify the string you want to match with the corresponding key in the grammar. If the key is not present in the grammar, it is a literal, which needs to be matched with string equality.
If the key is present in the grammar, get the corresponding productions (rules) for that key,  and start unifying each rule one by one on the string to be matched.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unify_key(key, text, at):
    if key not in grammar:
        return (True, at + len(key)) if text[at:].startswith(key) else (False, at)
    rules = grammar[key]
    for rule in rules:
        res, l = unify_rule(rule, text, at)
        if res is not None: return (res, l)
    return (False, 0)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For unifying rules, the idea is similar. We take each token in the rule, and try to unify that token with the string to be matched. We rely on `unify_key` for doing the unification of the token. if the unification fails, we return empty handed.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unify_rule(rule, text, at):
    for token in rule:
          result, at = unify_key(token, text, at)
          if result is None: return (False, at)
    return (True, at)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 ```
When we implemented the `unify_key`, we made an important decision, which was that, we return as soon as a match was found. This is what distinguishes a `PEG` parser from a general `CFG` parser. In particular it means that rules have to be ordered.
That is, the following grammar wont work:

```ebnf
ifmatch = IF (expr) THEN stmts
        | IF (expr) THEN stmts ELSE stmts
```
It has to be written as the following so that the rule that can match the longest string will come first. 
```ebnf
ifmatch = IF (expr) THEN stmts ELSE stmts
        | IF (expr) THEN stmts
```
<!-- It is also at this place that we have the big question. Are there two rules such that given two strings, such that the order of strings by longest match is different depending on the rule chosen? If no such conflicting orders can be found given any two rules, then _PEG_s are a superset of _CFG_. On the other hand, if there exist such a pair, then _CFG_s are not a strict subset of _PEG_s.-->
If we now parse an `if` statement without else using the above grammar, such a `IF (a=b) THEN return 0`, the first rule will fail, and the parse will start for the second rule again at `IF`. This backtracking is unnecessary as one can see that `IF (a=b) THEN return 0` is already parsed by all terms in the second rule. What we want is to save the old parses so that we can simply return the already parsed result. That is,

```python
   if seen((token, text, at)):
       return old_result
```
Fortunately, Python makes this easy using `functools.lru_cache` which provides cheap memoization to functions. Adding memoizaion, and reorganizing code, we have our _PEG_ parser.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
import functools

term_grammar = {
    '&lt;expr&gt;': [
        ['&lt;term&gt;', '&lt;add_op&gt;', '&lt;expr&gt;'],
        ['&lt;term&gt;']],
    '&lt;term&gt;': [
        ['&lt;fact&gt;', '&lt;mul_op&gt;', '&lt;term&gt;'],
        ['&lt;fact&gt;']],
    '&lt;fact&gt;': [
        ['&lt;digits&gt;'],
        ['(','&lt;expr&gt;',')']],
    '&lt;digits&gt;': [
        ['&lt;digit&gt;','&lt;digits&gt;'],
        ['&lt;digit&gt;']],
    '&lt;digit&gt;': [[str(i)] for i in list(range(10))],
    '&lt;add_op&gt;': [['+'], ['-']],
    '&lt;mul_op&gt;': [['*'], ['/']]
}

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

</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

The driver:
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = '1+2'
result = peg_parse(term_grammar).unify_key('<expr>', to_parse)
assert (len(to_parse) - result[0]) == 0
print(result[1])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

What we have here is only a subset of _PEG_ grammar. A _PEG_ grammar can contain

* Sequence: e1 e2
* Ordered choice: e1 / e2
* Zero-or-more: e*
* One-or-more: e+
* Optional: e?
* And-predicate: &e -- match `e` but do not consume any input
* Not-predicate: !e

We are yet to provide _e*_, _e+_, and _e?_. However, these are only conveniences. One can easily modify any _PEG_ that uses them to use grammar rules instead. The effect of predicates on the other hand can not be easily produced.  However, the lack of predicates does not change[^ford2004parsing]  the class of languages that such grammars can match, and even without the predicates, our _PEG_ can be useful for easily representing a large category of programs.

Note: This implementation will blow the stack pretty fast if we attempt to parse any expressions that are reasonably large (where some node in the derivation tree has a depth of 500) because Python provides very limited stack. One
can improve the situation slightly by inlining the `unify_rule()`.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

This gets us to derivation trees with at a depth of 1000 (or more if we increase the `sys.setrecursionlimit()`). We can also turn this to a completely iterative solution if we simulate the stack (formal arguments, locals, return value) ourselves rather than relying on the Python stack frame.

### Context Free.

It is fairly easy to turn this parser into a context-free grammar parser instead. The main idea is to keep a list of parse points, and advance them one at a time.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Driver

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
to_parse = '1+2'
p = cfg_parse(term_grammar)
result = p.unify_key('&lt;expr&gt;', to_parse, 0)
for l,res in result:
    if l == len(to_parse):
        print(res)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

This implementation is quite limited in that we have lost the ability to memoize (can be added back), and can not handle left recursion. See the [Earley parser](https://www.fuzzingbook.org/html/Parser.html) for a parser without these drawbacks.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>


[^valiant1975general]: Valiant, Leslie G. "General context-free recognition in less than cubic time." Journal of computer and system sciences 10.2 (1975): 308-315. 

[^lee2002fast]:Lee, Lillian. "Fast context-free grammar parsing requires fast boolean matrix multiplication." Journal of the ACM (JACM) 49.1 (2002): 1-15.

[^ford2004parsing]: Ford, Bryan. "Parsing expression grammars: a recognition-based syntactic foundation." Proceedings of the 31st ACM SIGPLAN-SIGACT symposium on Principles of programming languages. 2004.  <https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf>

