---
published: true
title: Conjunction, Disjunction, and Negation Regular Grammars
layout: post
comments: true
tags: python
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.9/';</script>
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
In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/)
I showed how to produce a grammar out of regular expressions. In the
second [post](/post/2021/10/23/regular-expression-to-regular-grammar/), I
claimed that we need a regular grammar because regular grammars have more
interesting properties such as being closed under
intersection and complement. Now, the question is how do we actually do
the intersection between two regular grammars? For this post, I assume that
the regular expressions are in the canonical format as given in
[this post](/post/2021/10/24/canonical-regular-grammar/).
That is, there are only two possible rule formats $$ A \rightarrow a B $$
and $$ A \rightarrow \epsilon $$. Further, the canonical format requires that
there is only one rule in a nonterminal definition that starts with a
particular terminal symbol. Refer to
[this post](/post/2021/10/24/canonical-regular-grammar/) for how convert any
regular grammar to the canonical format.
We start with importing the prerequisites

<!--
############
import sys, imp, pprint, string

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
        with open(module_loc, encoding='utf8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys, imp, pprint, string

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
        with open(module_loc, encoding=&#x27;utf8&#x27;) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We import the following modules

<!--
############
earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
gexpr = import_file('gexpr', '2021-09-11-fault-expressions.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')
rxcanonical = import_file('rxcanonical', '2021-10-24-canonical-regular-grammar.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
gexpr = import_file(&#x27;gexpr&#x27;, &#x27;2021-09-11-fault-expressions.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
rxfuzzer = import_file(&#x27;rxfuzzer&#x27;, &#x27;2021-10-22-fuzzing-with-regular-expressions.py&#x27;)
rxcanonical = import_file(&#x27;rxcanonical&#x27;, &#x27;2021-10-24-canonical-regular-grammar.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
There are only two patterns of rules in canonical regular grammars.
1. $$ A \rightarrow aB $$
3. $$ A \rightarrow \epsilon $$
The idea is that when evaluating intersection of the start symbol,
pair up all rules that start with the same terminal symbol.
Only the intersecion of these would exist in the resulting grammar.
The intersection of
```
<A1> ::= a <B1>
```
and
```
<A2> ::= a <B2>
```
is simply
```
<and(A1,A2)> ::= a <and(B1,B2)>
```
For constructing such rules, we also need to parse the boolean expressions
in the nonterminals. So, we define our grammar first.

<!--
############
import string
EMPTY_NT = '<_>'
BEXPR_GRAMMAR = {
    '<start>': [['<', '<bexpr>', '>']],
    '<bexpr>': [
        ['<bop>', '(', '<bexprs>', ')'],
        ['<key>']],
    '<bexprs>' : [['<bexpr>', ',', '<bexprs>'], ['<bexpr>']],
    '<bop>' : [list('and'), list('or'), list('neg')],
    '<key>': [['<letters>'],[EMPTY_NT[1:-1]]], # epsilon is <_>
    '<letters>': [
        ['<letter>'],
        ['<letter>', '<letters>']
    ],
    '<digits>': [
        ['<digit>'],
        ['<digit>', '<digits>']],
    '<digit>': [[i] for i in (string.digits)],
    '<letter>' : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
EMPTY_NT = &#x27;&lt;_&gt;&#x27;
BEXPR_GRAMMAR = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;&#x27;, &#x27;&lt;bexpr&gt;&#x27;, &#x27;&gt;&#x27;]],
    &#x27;&lt;bexpr&gt;&#x27;: [
        [&#x27;&lt;bop&gt;&#x27;, &#x27;(&#x27;, &#x27;&lt;bexprs&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;key&gt;&#x27;]],
    &#x27;&lt;bexprs&gt;&#x27; : [[&#x27;&lt;bexpr&gt;&#x27;, &#x27;,&#x27;, &#x27;&lt;bexprs&gt;&#x27;], [&#x27;&lt;bexpr&gt;&#x27;]],
    &#x27;&lt;bop&gt;&#x27; : [list(&#x27;and&#x27;), list(&#x27;or&#x27;), list(&#x27;neg&#x27;)],
    &#x27;&lt;key&gt;&#x27;: [[&#x27;&lt;letters&gt;&#x27;],[EMPTY_NT[1:-1]]], # epsilon is &lt;_&gt;
    &#x27;&lt;letters&gt;&#x27;: [
        [&#x27;&lt;letter&gt;&#x27;],
        [&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;letters&gt;&#x27;]
    ],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[i] for i in (string.digits)],
    &#x27;&lt;letter&gt;&#x27; : [[i] for i in (string.digits + string.ascii_lowercase + string.ascii_uppercase)]
}
BEXPR_START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need the set of all terminal symbols. We define it as follows

<!--
############
TERMINAL_SYMBOLS = list('abcdefg') #list(string.digits + string.ascii_lowercase + string.ascii_uppercase)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
TERMINAL_SYMBOLS = list(&#x27;abcdefg&#x27;) #list(string.digits + string.ascii_lowercase + string.ascii_uppercase)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define our expression class

<!--
############
class BExpr(gexpr.BExpr):
    def create_new(self, e): return BExpr(e)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][1]
        return bexpr

    def as_key(self):
        s = self.simple()
        return '<%s>' % s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class BExpr(gexpr.BExpr):
    def create_new(self, e): return BExpr(e)

    def _parse(self, k):
        bexpr_parser = earleyparser.EarleyParser(BEXPR_GRAMMAR)
        bparse_tree = list(bexpr_parser.parse_on(k, start_symbol=BEXPR_START))[0]
        bexpr = bparse_tree[1][1]
        return bexpr

    def as_key(self):
        s = self.simple()
        return &#x27;&lt;%s&gt;&#x27; % s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
strings = [
        '<1>',
        '<and(1,2)>',
        '<or(1,2)>',
        '<and(1,or(2,3,1))>',
]
for s in strings:
    e = BExpr(s)
    print(e.as_key())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
strings = [
        &#x27;&lt;1&gt;&#x27;,
        &#x27;&lt;and(1,2)&gt;&#x27;,
        &#x27;&lt;or(1,2)&gt;&#x27;,
        &#x27;&lt;and(1,or(2,3,1))&gt;&#x27;,
]
for s in strings:
    e = BExpr(s)
    print(e.as_key())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Conjuction of two regular grammars

Next, we define the conjunction of two regular grammars in the canonical
format. We will define the conjunction of two definitions, and at the end
discuss how to stitch it together for the complete grammar. The nice thing
here is that, because our grammar is in the canonical format, conjunction
disjunction and negation is really simple, and follows roughtly the same
framework.

### Nonterminals symbols

<!--
############
def and_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<and(%s,%s)>' % (k1[1:-1], k2[1:-1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_nonterminals(k1, k2):
    if k1 == k2: return k1
    return &#x27;&lt;and(%s,%s)&gt;&#x27; % (k1[1:-1], k2[1:-1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = and_nonterminals('<A>', '<B>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = and_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The rules

We only provide conjunction for those rules whose initial chars are the same
or it is an empty rule.

<!--
############
def and_rules(r1, r2):
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = and_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_rules(r1, r2):
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = and_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k, r = and_rules([], [])
print(k, r)
k, r = and_rules(['a', '<A>'], ['a', '<B>'])
print(k, r)
k, r = and_rules(['a', '<A>'], ['a', '<A>'])
print(k, r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k, r = and_rules([], [])
print(k, r)
k, r = and_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;])
print(k, r)
k, r = and_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(k, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The Definition

<!--
############
def get_leading_terminal(rule):
    if not rule: return ''
    return rule[0]

def and_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for terminal in paired1:
        if terminal not in paired2: continue
        new_key, intersected = and_rules(paired1[terminal], paired2[terminal])
        new_rules.append(intersected)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_leading_terminal(rule):
    if not rule: return &#x27;&#x27;
    return rule[0]

def and_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    # only those that can be parsed by both are allowed
    new_rules = []
    new_keys = []
    for terminal in paired1:
        if terminal not in paired2: continue
        new_key, intersected = and_rules(paired1[terminal], paired2[terminal])
        new_rules.append(intersected)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
g1 = {
     '<start1>' : [['a1', '<A1>']],
     '<A1>' : [['b1', '<B1>'], ['c1', '<C1>']],
     '<B1>' : [['c1','<C1>']],
     '<C1>' : [[]]
}
g2 = {
     '<start2>' : [['a1', '<A2>']],
     '<A2>' : [['b1', '<B2>'], ['d1', '<C2>']],
     '<B2>' : [['c1','<C2>'], []],
     '<C2>' : [[]]
}

rules = and_definitions(g1['<start1>'], g2['<start2>'])
print(rules)
rules = and_definitions(g1['<A1>'], g2['<A2>'])
print(rules)
rules = and_definitions(g1['<B1>'], g2['<B2>'])
print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
     &#x27;&lt;start1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A1&gt;&#x27;]],
     &#x27;&lt;A1&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B1&gt;&#x27;], [&#x27;c1&#x27;, &#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;B1&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;C1&gt;&#x27; : [[]]
}
g2 = {
     &#x27;&lt;start2&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A2&gt;&#x27;]],
     &#x27;&lt;A2&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;d1&#x27;, &#x27;&lt;C2&gt;&#x27;]],
     &#x27;&lt;B2&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C2&gt;&#x27;], []],
     &#x27;&lt;C2&gt;&#x27; : [[]]
}

rules = and_definitions(g1[&#x27;&lt;start1&gt;&#x27;], g2[&#x27;&lt;start2&gt;&#x27;])
print(rules)
rules = and_definitions(g1[&#x27;&lt;A1&gt;&#x27;], g2[&#x27;&lt;A2&gt;&#x27;])
print(rules)
rules = and_definitions(g1[&#x27;&lt;B1&gt;&#x27;], g2[&#x27;&lt;B2&gt;&#x27;])
print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Disjunction of two regular grammars

For disjunction, the strategy is the same.
### Disjunction of nonterminal symbols

<!--
############
def or_nonterminals(k1, k2):
    if k1 == k2: return k1
    return '<or(%s,%s)>' % (k1[1:-1], k2[1:-1])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_nonterminals(k1, k2):
    if k1 == k2: return k1
    return &#x27;&lt;or(%s,%s)&gt;&#x27; % (k1[1:-1], k2[1:-1])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = or_nonterminals('<A>', '<B>')
print(k)
k = or_nonterminals('<A>', '<A>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = or_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;)
print(k)
k = or_nonterminals(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;A&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Disjunction of rules

<!--
############
def or_rules(r1, r2):
    # the initial chars are the same
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = or_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_rules(r1, r2):
    # the initial chars are the same
    if not r1:
        assert not r2
        return None, [] # epsilon
    assert r1[0] == r2[0]
    assert len(r1) != 1
    assert len(r2) != 1
    nk = or_nonterminals(r1[1], r2[1])
    return nk, [r1[0], nk]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k, r = and_rules([], [])
print(k, r)
k, r = or_rules(['a', '<A>'], ['a', '<B>'])
print(k, r)
k, r = or_rules(['a', '<A>'], ['a', '<A>'])
print(k, r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k, r = and_rules([], [])
print(k, r)
k, r = or_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;])
print(k, r)
k, r = or_rules([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(k, r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Disjunction of definitions

<!--
############
def or_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    new_rules = []
    new_keys = []
    p0 = [c for c in paired1 if c in paired2]
    p1 = [c for c in paired1 if c not in paired2]
    p2 = [c for c in paired2 if c not in paired1]
    for terminal in p0:
        new_key, kunion = or_rules(paired1[terminal], paired2[terminal])
        new_rules.append(kunion)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules + [paired1[c] for c in p1] + [paired2[c] for c in p2]

if __name__ == '__main__':
    g3 = {
         '<start3>' : [['a1', '<A3>']],
         '<A3>' : [['b1', '<B3>'], ['c1', '<C3>']],
         '<B3>' : [['c1','<C3>']],
         '<C3>' : [[]]
    }
    g4 = {
         '<start4>' : [['a1', '<A4>']],
         '<A4>' : [['b1', '<B4>'], ['d1', '<C4>']],
         '<B4>' : [['c1','<C4>'], []],
         '<C4>' : [[]]
    }

    rules = or_definitions(g3['<start3>'], g4['<start4>'])
    print(rules)
    rules = or_definitions(g3['<A3>'], g4['<A4>'])
    print(rules)
    rules = or_definitions(g3['<B3>'], g4['<B4>'])
    print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def or_definitions(d1, d2):
    # first find the rules with same starting terminal symbol.
    paired1 = {get_leading_terminal(r):r for r in d1}
    paired2 = {get_leading_terminal(r):r for r in d2}
    new_rules = []
    new_keys = []
    p0 = [c for c in paired1 if c in paired2]
    p1 = [c for c in paired1 if c not in paired2]
    p2 = [c for c in paired2 if c not in paired1]
    for terminal in p0:
        new_key, kunion = or_rules(paired1[terminal], paired2[terminal])
        new_rules.append(kunion)
        if new_key is not None:
            new_keys.append(new_key)
    return new_rules + [paired1[c] for c in p1] + [paired2[c] for c in p2]

if __name__ == &#x27;__main__&#x27;:
    g3 = {
         &#x27;&lt;start3&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A3&gt;&#x27;]],
         &#x27;&lt;A3&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B3&gt;&#x27;], [&#x27;c1&#x27;, &#x27;&lt;C3&gt;&#x27;]],
         &#x27;&lt;B3&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C3&gt;&#x27;]],
         &#x27;&lt;C3&gt;&#x27; : [[]]
    }
    g4 = {
         &#x27;&lt;start4&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;A4&gt;&#x27;]],
         &#x27;&lt;A4&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B4&gt;&#x27;], [&#x27;d1&#x27;, &#x27;&lt;C4&gt;&#x27;]],
         &#x27;&lt;B4&gt;&#x27; : [[&#x27;c1&#x27;,&#x27;&lt;C4&gt;&#x27;], []],
         &#x27;&lt;C4&gt;&#x27; : [[]]
    }

    rules = or_definitions(g3[&#x27;&lt;start3&gt;&#x27;], g4[&#x27;&lt;start4&gt;&#x27;])
    print(rules)
    rules = or_definitions(g3[&#x27;&lt;A3&gt;&#x27;], g4[&#x27;&lt;A4&gt;&#x27;])
    print(rules)
    rules = or_definitions(g3[&#x27;&lt;B3&gt;&#x27;], g4[&#x27;&lt;B4&gt;&#x27;])
    print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Negation

<!--
############
def negate_nonterminal(k): return '<neg(%s)>' % k[1:-1]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_nonterminal(k): return &#x27;&lt;neg(%s)&gt;&#x27; % k[1:-1]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
k = negate_nonterminal('<A>')
print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
k = negate_nonterminal(&#x27;&lt;A&gt;&#x27;)
print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Negate a single rule

<!--
############
def negate_key_in_rule(rule):
    if len(rule) == 0: return None
    assert len(rule) != 1
    assert fuzzer.is_terminal(rule[0])
    assert fuzzer.is_nonterminal(rule[1])
    return [rule[0], negate_nonterminal(rule[1])]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_key_in_rule(rule):
    if len(rule) == 0: return None
    assert len(rule) != 1
    assert fuzzer.is_terminal(rule[0])
    assert fuzzer.is_nonterminal(rule[1])
    return [rule[0], negate_nonterminal(rule[1])]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Ensure that it works

<!--
############
r = negate_key_in_rule(['a', '<A>'])
print(r)
r = negate_key_in_rule([])
print(r)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
r = negate_key_in_rule([&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;])
print(r)
r = negate_key_in_rule([])
print(r)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Negate a definition

<!--
############
def negate_definition(d1, terminal_symbols=TERMINAL_SYMBOLS):
    # for negating a definition, we negate each ruleset
    # separately, and add any characters that were left
    # over.
    # what about presence of epsilon rule? An epsilon
    # rule adds just one element to the language. An
    # empty string. So, we will not match that single
    # element.

    # Now, for those characters that are not matched by
    # any of the leading chars in rules, we can match
    # anything else after the char.
    paired = {get_leading_terminal(r):r for r in d1}
    remaining_chars = [c for c in terminal_symbols if c not in paired]
    new_rules = [[c, '<.*>'] for c in remaining_chars]

    # Now, we try to negate individual rules. It starts with the same
    # character, but matches the negative.
    for rule in d1:
        r = negate_key_in_rule(rule)
        if r is not None:
            new_rules.append(r)

    # should we add emtpy rule match or not?
    if [] not in d1:
        new_rules.append([])
    return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_definition(d1, terminal_symbols=TERMINAL_SYMBOLS):
    # for negating a definition, we negate each ruleset
    # separately, and add any characters that were left
    # over.
    # what about presence of epsilon rule? An epsilon
    # rule adds just one element to the language. An
    # empty string. So, we will not match that single
    # element.

    # Now, for those characters that are not matched by
    # any of the leading chars in rules, we can match
    # anything else after the char.
    paired = {get_leading_terminal(r):r for r in d1}
    remaining_chars = [c for c in terminal_symbols if c not in paired]
    new_rules = [[c, &#x27;&lt;.*&gt;&#x27;] for c in remaining_chars]

    # Now, we try to negate individual rules. It starts with the same
    # character, but matches the negative.
    for rule in d1:
        r = negate_key_in_rule(rule)
        if r is not None:
            new_rules.append(r)

    # should we add emtpy rule match or not?
    if [] not in d1:
        new_rules.append([])
    return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
g4 = {
     '<start3>' : [['a', '<A3>']],
     '<A3>' : [['b', '<B3>'], ['c', '<C3>']],
     '<B3>' : [['c','<C3>']],
     '<C3>' : [[]]
}

rules = negate_definition(g4['<start3>'])
print(rules)
rules = negate_definition(g4['<A3>'])
print(rules)
rules = negate_definition(g4['<B3>'])
print(rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g4 = {
     &#x27;&lt;start3&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A3&gt;&#x27;]],
     &#x27;&lt;A3&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;B3&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;C3&gt;&#x27;]],
     &#x27;&lt;B3&gt;&#x27; : [[&#x27;c&#x27;,&#x27;&lt;C3&gt;&#x27;]],
     &#x27;&lt;C3&gt;&#x27; : [[]]
}

rules = negate_definition(g4[&#x27;&lt;start3&gt;&#x27;])
print(rules)
rules = negate_definition(g4[&#x27;&lt;A3&gt;&#x27;])
print(rules)
rules = negate_definition(g4[&#x27;&lt;B3&gt;&#x27;])
print(rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Complete
Now, stitching it all together

<!--
############
class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

    def reconstruct_rules_from_bexpr(self, bexpr):
        f_key = bexpr.as_key()
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == 'and':
                return self.reconstruct_and_bexpr(bexpr)
            elif operator == 'or':
                return self.reconstruct_or_bexpr(bexpr)
            elif operator == 'neg':
                return self.reconstruct_neg_bexpr(bexpr)
            else:
                return self.reconstruct_orig_bexpr(bexpr)

    def reconstruct_orig_bexpr(self, bexpr):
        assert False

    def reconstruct_neg_bexpr(self, bexpr):
        assert False

    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key

    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key

    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            if log: print(len(keys))
            key_to_reconstruct, *keys = keys
            if log: print('reconstructing:', key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception('Key found:', key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            nrek = key_to_reconstruct
            if bexpr.simple():
                nkey = bexpr.as_key()
                if log: print('simplified_to:', nkey)
                d, s = self.reconstruct_rules_from_bexpr(bexpr)
                self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            else:
                nkey = nrek # base key
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct

def remove_empty_key_refs(grammar, ek):
    new_grammar = {}
    for k in grammar:
        if k == ek: continue
        new_rules = []
        for r in grammar[k]:
            if ek in r:
                continue
            new_rules.append(r)
        new_grammar[k] = new_rules
    return new_grammar


def remove_empty_defs(grammar, start):
    empty = [k for k in grammar if not grammar[k]]
    while empty:
        k, *empty = empty
        grammar = remove_empty_key_refs(grammar, k)
        empty = [k for k in grammar if not grammar[k]]
    return grammar, start

def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ReconstructRules:
    def __init__(self, grammar):
        self.grammar = grammar

    def reconstruct_rules_from_bexpr(self, bexpr):
        f_key = bexpr.as_key()
        if f_key in self.grammar:
            return self.grammar[f_key], f_key
        else:
            operator = bexpr.get_operator()
            if operator == &#x27;and&#x27;:
                return self.reconstruct_and_bexpr(bexpr)
            elif operator == &#x27;or&#x27;:
                return self.reconstruct_or_bexpr(bexpr)
            elif operator == &#x27;neg&#x27;:
                return self.reconstruct_neg_bexpr(bexpr)
            else:
                return self.reconstruct_orig_bexpr(bexpr)

    def reconstruct_orig_bexpr(self, bexpr):
        assert False

    def reconstruct_neg_bexpr(self, bexpr):
        assert False

    def reconstruct_and_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        assert fst != snd
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        and_rules = and_definitions(d1, d2)
        return and_rules, f_key

    def reconstruct_or_bexpr(self, bexpr):
        fst, snd = bexpr.op_fst_snd()
        f_key = bexpr.as_key()
        d1, s1 = self.reconstruct_rules_from_bexpr(fst)
        assert fst != snd
        d2, s2 = self.reconstruct_rules_from_bexpr(snd)
        or_rules = or_definitions(d1, d2)
        return or_rules, f_key

    def reconstruct_key(self, key_to_construct, log=False):
        keys = [key_to_construct]
        defined = set()
        while keys:
            if log: print(len(keys))
            key_to_reconstruct, *keys = keys
            if log: print(&#x27;reconstructing:&#x27;, key_to_reconstruct)
            if key_to_reconstruct in defined:
                raise Exception(&#x27;Key found:&#x27;, key_to_reconstruct)
            defined.add(key_to_reconstruct)
            bexpr = BExpr(key_to_reconstruct)
            nrek = key_to_reconstruct
            if bexpr.simple():
                nkey = bexpr.as_key()
                if log: print(&#x27;simplified_to:&#x27;, nkey)
                d, s = self.reconstruct_rules_from_bexpr(bexpr)
                self.grammar = {**self.grammar, **{key_to_reconstruct:d}}
            else:
                nkey = nrek # base key
            keys = gexpr.undefined_keys(self.grammar)
        return self.grammar, key_to_construct

def remove_empty_key_refs(grammar, ek):
    new_grammar = {}
    for k in grammar:
        if k == ek: continue
        new_rules = []
        for r in grammar[k]:
            if ek in r:
                continue
            new_rules.append(r)
        new_grammar[k] = new_rules
    return new_grammar


def remove_empty_defs(grammar, start):
    empty = [k for k in grammar if not grammar[k]]
    while empty:
        k, *empty = empty
        grammar = remove_empty_key_refs(grammar, k)
        empty = [k for k in grammar if not grammar[k]]
    return grammar, start

def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = rr.reconstruct_key(start, log)
    grammar, start = remove_empty_defs(grammar, start)
    return grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
my_re1 = 'a1(b1(c1)|b1)'
g_empty = {EMPTY_NT: [[]]}
g1 = {
        '<start1>' : [['0', '<A1>']],
        '<A1>' : [['a', '<B1>']],
        '<B1>' : [['b','<C1>'], ['b', '<D1>']],
        '<C1>' : [['c1', '<D1>']],
        '<D1>' : [[]],
        }
s1 = '<start1>'
my_re2 = 'a2(b2)|a2'
g2 = {
        '<start2>' : [['0', '<A2>']],
        '<A2>' : [['a', '<B2>'], ['a2', '<D2>']],
        '<B2>' : [['b', '<D2>']],
        '<D2>' : [[]],
        }
s2 = '<start2>'
s1_s2 = and_nonterminals(s1, s2)
g, s = complete({**g1, **g2, **g_empty}, s1_s2, True)
gatleast.display_grammar(g,s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1 = &#x27;a1(b1(c1)|b1)&#x27;
g_empty = {EMPTY_NT: [[]]}
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;, &#x27;&lt;D1&gt;&#x27;]],
        &#x27;&lt;D1&gt;&#x27; : [[]],
        }
s1 = &#x27;&lt;start1&gt;&#x27;
my_re2 = &#x27;a2(b2)|a2&#x27;
g2 = {
        &#x27;&lt;start2&gt;&#x27; : [[&#x27;0&#x27;, &#x27;&lt;A2&gt;&#x27;]],
        &#x27;&lt;A2&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;a2&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;B2&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;D2&gt;&#x27;]],
        &#x27;&lt;D2&gt;&#x27; : [[]],
        }
s2 = &#x27;&lt;start2&gt;&#x27;
s1_s2 = and_nonterminals(s1, s2)
g, s = complete({**g1, **g2, **g_empty}, s1_s2, True)
gatleast.display_grammar(g,s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-26-regular-grammar-expressions.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
