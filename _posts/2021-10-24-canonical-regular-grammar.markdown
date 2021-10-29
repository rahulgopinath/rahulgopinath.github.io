---
published: true
title: Canonical Regular Grammars
layout: post
comments: true
tags: parsing
categories: post
---
A regular grammar can in theory have rules with any of the following forms

* $$ A \rightarrow a $$
* $$ A \rightarrow a B $$
* $$ A \rightarrow a b c B $$
* $$ A \rightarrow B $$
* $$ A \rightarrow \epsilon $$

with no further restrictions. However, for working with regular grammars,
such freedom can be unwieldy. Hence, without loss of generality, we define
a canonical format for regular grammars, to which any regular grammar can
be converted to.
* $$ A \rightarrow a B $$
* $$ A \rightarrow \epsilon $$

where given a nonterminal $$A$$ and a terminal symbol $$ a $$ at most one of
its rules will start with a terminal symbol $$ a $$. That is, if the original
grammar had multiple rules that started with $$ a $$, they will be collected
into a new nonterminal symbol. Further, there will be at most one terminal
symbol in a rule. That is, if there are more terminal symbols, then we bundle
that to a new nonterminal symbol
We start with importing the prerequisites
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
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')
rxregular = import_file('rxregular', '2021-10-23-regular-expression-to-regular-grammar.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
rxfuzzer = import_file(&#x27;rxfuzzer&#x27;, &#x27;2021-10-22-fuzzing-with-regular-expressions.py&#x27;)
rxregular = import_file(&#x27;rxregular&#x27;, &#x27;2021-10-23-regular-expression-to-regular-grammar.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We start with a few common rules.
First, we define the empty rule.
 
```
<_>  := 
```

<!--
############
NT_EMPTY = '<_>'

G_EMPTY = {NT_EMPTY: [[]]}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
NT_EMPTY = &#x27;&lt;_&gt;&#x27;

G_EMPTY = {NT_EMPTY: [[]]}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We also define our `TERMINAL_SYMBOLS`

<!--
############
TERMINAL_SYMBOLS = rxfuzzer.TERMINAL_SYMBOLS

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
TERMINAL_SYMBOLS = rxfuzzer.TERMINAL_SYMBOLS
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Then, use it to define `NT_ANY_STAR`
 
```
<.*>  := . <.*>
       | <NT_EMPTY>
```

<!--
############
NT_ANY_STAR = '<.*>'

G_ANY_STAR = {
    NT_ANY_STAR: [[c, NT_ANY_STAR] for c in TERMINAL_SYMBOLS] + [[NT_EMPTY]]
}


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
NT_ANY_STAR = &#x27;&lt;.*&gt;&#x27;

G_ANY_STAR = {
    NT_ANY_STAR: [[c, NT_ANY_STAR] for c in TERMINAL_SYMBOLS] + [[NT_EMPTY]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Use it to also define `NT_ANY_PLUS`
 
```
<.+>  := . <.+>
       | . <NT_EMPTY>
```

use any_plus where possible.

<!--
############
NT_ANY_PLUS = '<.+>'

G_ANY_PLUS = {
    NT_ANY_PLUS: [[c, NT_ANY_PLUS] for c in TERMINAL_SYMBOLS] + [[c, NT_EMPTY] for c in TERMINAL_SYMBOLS]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
NT_ANY_PLUS = &#x27;&lt;.+&gt;&#x27;

G_ANY_PLUS = {
    NT_ANY_PLUS: [[c, NT_ANY_PLUS] for c in TERMINAL_SYMBOLS] + [[c, NT_EMPTY] for c in TERMINAL_SYMBOLS]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Remove degenerate rules

A degenerate rule is a rule with a format $$ A \rightarrow B $$ where $$ A $$
and $$ B $$ are nonterminals in the grammar. The way to eliminate such
nonterminals is to recursively merge the rules of $$ B $$ to the rules of $$ A $$.

<!--
############
from collections import defaultdict

def is_degenerate_rule(rule):
    return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

def remove_duplicate_rules(g):
    new_g = {}
    for k in g:
        my_rules = {str(r):r for r in g[k]}
        new_g[k] = [my_rules[k] for k in my_rules]
    return new_g

def remove_degenerate_rules(g, s):
    g = dict(g)
    drkeys = [k for k in g if any(is_degenerate_rule(r) for r in g[k])]
    while drkeys:
        drk, *drkeys = drkeys
        new_rules = []
        for r in g[drk]:
            if is_degenerate_rule(r):
                new_key = r[0]
                if new_key == drk: continue # self recursion
                new_rs = g[new_key]
                if any(is_degenerate_rule(new_r) for new_r in new_rs):
                    drkeys.append(drk)
                new_rules.extend(new_rs)
            else:
                new_rules.append(r)
        g[drk] = new_rules

    return remove_duplicate_rules(g), s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from collections import defaultdict

def is_degenerate_rule(rule):
    return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

def remove_duplicate_rules(g):
    new_g = {}
    for k in g:
        my_rules = {str(r):r for r in g[k]}
        new_g[k] = [my_rules[k] for k in my_rules]
    return new_g

def remove_degenerate_rules(g, s):
    g = dict(g)
    drkeys = [k for k in g if any(is_degenerate_rule(r) for r in g[k])]
    while drkeys:
        drk, *drkeys = drkeys
        new_rules = []
        for r in g[drk]:
            if is_degenerate_rule(r):
                new_key = r[0]
                if new_key == drk: continue # self recursion
                new_rs = g[new_key]
                if any(is_degenerate_rule(new_r) for new_r in new_rs):
                    drkeys.append(drk)
                new_rules.extend(new_rs)
            else:
                new_rules.append(r)
        g[drk] = new_rules

    return remove_duplicate_rules(g), s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
g1 = {
     '<start1>' : [['<A1>']],
     '<A1>' : [['a1', '<B1>']],
     '<B1>' : [['b1','<C1>'], ['<C1>']],
     '<C1>' : [['c1'], ['<C1>']]
}
s1 = '<start1>'
g, s = remove_degenerate_rules(g1, s1)
gatleast.display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
     &#x27;&lt;start1&gt;&#x27; : [[&#x27;&lt;A1&gt;&#x27;]],
     &#x27;&lt;A1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;B1&gt;&#x27;]],
     &#x27;&lt;B1&gt;&#x27; : [[&#x27;b1&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;], [&#x27;&lt;C1&gt;&#x27;]]
}
s1 = &#x27;&lt;start1&gt;&#x27;
g, s = remove_degenerate_rules(g1, s1)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Removing terminal sequences

A terminal sequence is a sequence of terminal symbols in a rule. For example,
in the rule
```
<A> ::= a b c <B>
```
`a b c` is a terminal sequence.
We want to replace such sequences by a new nonterminal. For example,
```
<A> ::= a <Aa>
<Aa> ::= b <Aab>
<Aab> ::= c <B>
```

<!--
############
def get_split_key(k, terminal):
    return '<%s_%s>' % (k[1:-1], terminal)

def split_multi_terminal_rule(rule, k):
    if len(rule) == 0:
        return k, [(k, [rule])]
    elif len(rule) == 1:
        assert not fuzzer.is_nonterminal(rule[0])
        return k, [(k, [rule])]
    elif len(rule) > 1:
        terminal = rule[0]
        tok = rule[1]
        if fuzzer.is_nonterminal(tok):
            assert len(rule) == 2
            return k, [(k, [rule])]
        else:
            kn, ngl = split_multi_terminal_rule(rule[1:], get_split_key(k, terminal))
            new_rule = [terminal, kn]
            return k, ([(k, [new_rule])] + ngl)
    else:
        assert False

def remove_multi_terminals(g, s):
    new_g = defaultdict(list)
    for key in g:
        for r in g[key]:
            nk, lst = split_multi_terminal_rule(r, key)
            for k, rules in lst:
                new_g[k].extend(rules)
            assert nk in new_g
    return remove_duplicate_rules(new_g), s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_split_key(k, terminal):
    return &#x27;&lt;%s_%s&gt;&#x27; % (k[1:-1], terminal)

def split_multi_terminal_rule(rule, k):
    if len(rule) == 0:
        return k, [(k, [rule])]
    elif len(rule) == 1:
        assert not fuzzer.is_nonterminal(rule[0])
        return k, [(k, [rule])]
    elif len(rule) &gt; 1:
        terminal = rule[0]
        tok = rule[1]
        if fuzzer.is_nonterminal(tok):
            assert len(rule) == 2
            return k, [(k, [rule])]
        else:
            kn, ngl = split_multi_terminal_rule(rule[1:], get_split_key(k, terminal))
            new_rule = [terminal, kn]
            return k, ([(k, [new_rule])] + ngl)
    else:
        assert False

def remove_multi_terminals(g, s):
    new_g = defaultdict(list)
    for key in g:
        for r in g[key]:
            nk, lst = split_multi_terminal_rule(r, key)
            for k, rules in lst:
                new_g[k].extend(rules)
            assert nk in new_g
    return remove_duplicate_rules(new_g), s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
g2 = {
     '<start1>' : [['a1', 'a2', 'a3', '<A1>']],
     '<A1>' : [['a1', '<B1>'],
               ['b1', 'b2']],
     '<B1>' : [['b1', 'c1', '<C1>'],
               ['b1', 'c1', '<D1>']],
     '<C1>' : [['c1'], []],
     '<D1>' : [['d1'], []]
}
s2 = '<start1>'
g, s = remove_multi_terminals(g2, s2)
gatleast.display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2 = {
     &#x27;&lt;start1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;a2&#x27;, &#x27;a3&#x27;, &#x27;&lt;A1&gt;&#x27;]],
     &#x27;&lt;A1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;B1&gt;&#x27;],
               [&#x27;b1&#x27;, &#x27;b2&#x27;]],
     &#x27;&lt;B1&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;c1&#x27;, &#x27;&lt;C1&gt;&#x27;],
               [&#x27;b1&#x27;, &#x27;c1&#x27;, &#x27;&lt;D1&gt;&#x27;]],
     &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;], []],
     &#x27;&lt;D1&gt;&#x27; : [[&#x27;d1&#x27;], []]
}
s2 = &#x27;&lt;start1&gt;&#x27;
g, s = remove_multi_terminals(g2, s2)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Fix empty rules

If there are any rules of the form $$ A \rightarrow b $$, we replace it by
$$ A \rightarrow b E $$, $$ E \rightarrow \epsilon $$.
Next, if we have rules of the form $$ A \rightarrow \epsilon $$,
and $$ B \rightarrow a A $$ then, we remove the $$ A \rightarrow \epsilon $$
and add a new rule $$ B \rightarrow a E $$
The reason for doing
this is to make sure that we have a single termination point. If you are using
NT_ANY_STAR, then make sure you run this after (or use NT_ANY_PLUS instead).

<!--
############
def fix_empty_rules(g, s):
    new_g = defaultdict(list)
    empty_keys = []
    for k in g:
        if k == NT_EMPTY: continue
        for r in g[k]:
            if len(r) == 0:
                empty_keys.append(k)
                continue
            elif len(r) == 1:
                tok = r[0]
                assert fuzzer.is_terminal(tok)
                new_g[k].append([tok, NT_EMPTY])
            else:
                new_g[k].append(r)

    new_g1 = defaultdict(list)
    for k in new_g:
        for r in new_g[k]:
            assert len(r) == 2 or k == s
            if r[1] in empty_keys:
                new_g1[k].append(r)
                new_g1[k].append([r[0], NT_EMPTY])
            else:
                new_g1[k].append(r)

    # special case.
    if s in empty_keys:
        new_g1[s].append(NT_EMPTY)

    return {**new_g1, **G_EMPTY}, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def fix_empty_rules(g, s):
    new_g = defaultdict(list)
    empty_keys = []
    for k in g:
        if k == NT_EMPTY: continue
        for r in g[k]:
            if len(r) == 0:
                empty_keys.append(k)
                continue
            elif len(r) == 1:
                tok = r[0]
                assert fuzzer.is_terminal(tok)
                new_g[k].append([tok, NT_EMPTY])
            else:
                new_g[k].append(r)

    new_g1 = defaultdict(list)
    for k in new_g:
        for r in new_g[k]:
            assert len(r) == 2 or k == s
            if r[1] in empty_keys:
                new_g1[k].append(r)
                new_g1[k].append([r[0], NT_EMPTY])
            else:
                new_g1[k].append(r)

    # special case.
    if s in empty_keys:
        new_g1[s].append(NT_EMPTY)

    return {**new_g1, **G_EMPTY}, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Collapse similar starting rules

Here, the idea is to join any set of rules of the form
$$ A \rightarrow b B $$, $$ A \rightarrow b C $$ to $$ A \rightarrow b or(B,C) $$.
First, we define how to join rules that all have the same terminal symbol
as the starting token.

<!--
############
def join_keys(keys):
    return '<or(%s)>' % ','.join([k[1:-1] for k in  keys])

def join_rules(rules):
    if len(rules) == 1: return (), rules[0]
    terminal = rules[0][0]
    assert all(r[0] == terminal for r in rules)
    keys = []
    for r in rules:
        if len(r) > 1:
            keys.append(r[1])
        else:
            keys.append('')
    new_key = join_keys(keys)
    return tuple(keys), [terminal, new_key]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def join_keys(keys):
    return &#x27;&lt;or(%s)&gt;&#x27; % &#x27;,&#x27;.join([k[1:-1] for k in  keys])

def join_rules(rules):
    if len(rules) == 1: return (), rules[0]
    terminal = rules[0][0]
    assert all(r[0] == terminal for r in rules)
    keys = []
    for r in rules:
        if len(r) &gt; 1:
            keys.append(r[1])
        else:
            keys.append(&#x27;&#x27;)
    new_key = join_keys(keys)
    return tuple(keys), [terminal, new_key]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
rules = [
        ['a', '<A>'],
        ['a', '<B>'],
        ['a', '<C>'],
]
k, new_rule = join_rules(rules)
print(k, '::=', new_rule)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rules = [
        [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;],
        [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
        [&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;],
]
k, new_rule = join_rules(rules)
print(k, &#x27;::=&#x27;, new_rule)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we split any given definition into rulesets that start wit the same
terminal symbol.

<!--
############
def definition_split_to_rulesets(d1):
    rule_sets = defaultdict(list)
    for r in d1:
        if len(r) > 0:
            assert not fuzzer.is_nonterminal(r[0]) # no degenerate rules
            rule_sets[r[0]].append(r)
        else:
            rule_sets[''].append(r)
    return rule_sets


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def definition_split_to_rulesets(d1):
    rule_sets = defaultdict(list)
    for r in d1:
        if len(r) &gt; 0:
            assert not fuzzer.is_nonterminal(r[0]) # no degenerate rules
            rule_sets[r[0]].append(r)
        else:
            rule_sets[&#x27;&#x27;].append(r)
    return rule_sets
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
rules = [
        ['a', '<A>'],
        ['a', '<B>'],
        ['b', '<C>'],
        ['b', '<D>'],
]
rule_sets = definition_split_to_rulesets(rules)
for c in rule_sets:
    print(c, rule_sets[c])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rules = [
        [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;],
        [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
        [&#x27;b&#x27;, &#x27;&lt;C&gt;&#x27;],
        [&#x27;b&#x27;, &#x27;&lt;D&gt;&#x27;],
]
rule_sets = definition_split_to_rulesets(rules)
for c in rule_sets:
    print(c, rule_sets[c])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given a list of keys, construct their `or(.)` from the
given grammar.

<!--
############
def construct_merged_keys(merge_keys, g):
    new_key = join_keys(merge_keys)
    new_def = []
    keys_to_construct = []
    for k in merge_keys:
        if not k:
            new_def.append([])
        else:
            new_def.extend(g[k])
    rsets = definition_split_to_rulesets(new_def)
    new_rules = []
    for c in rsets:
        if not c:
            new_rules.append([])
            continue
        keys_to_combine, new_rule = join_rules(rsets[c])
        new_rules.append(new_rule)
        if keys_to_combine:
            keys_to_construct.append(keys_to_combine)
    return keys_to_construct, {new_key: new_rules}


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def construct_merged_keys(merge_keys, g):
    new_key = join_keys(merge_keys)
    new_def = []
    keys_to_construct = []
    for k in merge_keys:
        if not k:
            new_def.append([])
        else:
            new_def.extend(g[k])
    rsets = definition_split_to_rulesets(new_def)
    new_rules = []
    for c in rsets:
        if not c:
            new_rules.append([])
            continue
        keys_to_combine, new_rule = join_rules(rsets[c])
        new_rules.append(new_rule)
        if keys_to_combine:
            keys_to_construct.append(keys_to_combine)
    return keys_to_construct, {new_key: new_rules}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g3 = {
     '<start1>' : [
         ['a1', '<A1>'],
         ['a1', '<A2>'],
         ['a1', '<A3>']
         ],
     '<A1>' : [['b1', '<B1>']],
     '<A2>' : [['b2', '<B1>']],
     '<A3>' : [['b3', '<B1>']],
     '<B1>' : [['b1','<C1>'],
               ['b2', '<C1>']],
     '<C1>' : [['c1'], []]
}
s3 = '<start1>'
for k in [['<A1>', '<B1>'],
          ['<A1>', '<C1>']]:
    new_keys, g = construct_merged_keys(k, g3)
    gatleast.display_grammar(g, join_keys(k))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g3 = {
     &#x27;&lt;start1&gt;&#x27; : [
         [&#x27;a1&#x27;, &#x27;&lt;A1&gt;&#x27;],
         [&#x27;a1&#x27;, &#x27;&lt;A2&gt;&#x27;],
         [&#x27;a1&#x27;, &#x27;&lt;A3&gt;&#x27;]
         ],
     &#x27;&lt;A1&gt;&#x27; : [[&#x27;b1&#x27;, &#x27;&lt;B1&gt;&#x27;]],
     &#x27;&lt;A2&gt;&#x27; : [[&#x27;b2&#x27;, &#x27;&lt;B1&gt;&#x27;]],
     &#x27;&lt;A3&gt;&#x27; : [[&#x27;b3&#x27;, &#x27;&lt;B1&gt;&#x27;]],
     &#x27;&lt;B1&gt;&#x27; : [[&#x27;b1&#x27;,&#x27;&lt;C1&gt;&#x27;],
               [&#x27;b2&#x27;, &#x27;&lt;C1&gt;&#x27;]],
     &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;], []]
}
s3 = &#x27;&lt;start1&gt;&#x27;
for k in [[&#x27;&lt;A1&gt;&#x27;, &#x27;&lt;B1&gt;&#x27;],
          [&#x27;&lt;A1&gt;&#x27;, &#x27;&lt;C1&gt;&#x27;]]:
    new_keys, g = construct_merged_keys(k, g3)
    gatleast.display_grammar(g, join_keys(k))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
defining the rule collapse.

<!--
############
def collapse_similar_starting_rules(g, s):
    new_g = defaultdict(list)
    keys_to_construct = []
    for k in g:
        rsets = definition_split_to_rulesets(g[k])
        # each ruleset will get one rule
        for c in rsets:
            keys_to_combine, new_rule = join_rules(rsets[c])
            new_g[k].append(new_rule)
            if keys_to_combine:
                keys_to_construct.append(keys_to_combine)

    seen_keys = set()
    while keys_to_construct:
        merge_keys, *keys_to_construct = keys_to_construct
        if merge_keys in seen_keys: continue
        seen_keys.add(merge_keys)
        new_keys, g_ = construct_merged_keys(merge_keys, new_g)
        new_g = {**new_g, **g_}
        keys_to_construct.extend(new_keys)
    return new_g, s


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def collapse_similar_starting_rules(g, s):
    new_g = defaultdict(list)
    keys_to_construct = []
    for k in g:
        rsets = definition_split_to_rulesets(g[k])
        # each ruleset will get one rule
        for c in rsets:
            keys_to_combine, new_rule = join_rules(rsets[c])
            new_g[k].append(new_rule)
            if keys_to_combine:
                keys_to_construct.append(keys_to_combine)

    seen_keys = set()
    while keys_to_construct:
        merge_keys, *keys_to_construct = keys_to_construct
        if merge_keys in seen_keys: continue
        seen_keys.add(merge_keys)
        new_keys, g_ = construct_merged_keys(merge_keys, new_g)
        new_g = {**new_g, **g_}
        keys_to_construct.extend(new_keys)
    return new_g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g, s = collapse_similar_starting_rules(g3, s3)
gatleast.display_grammar(g, s)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, s = collapse_similar_starting_rules(g3, s3)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Display canonical grammar
We also need the ability to compactly display a canonical regular grammar
and we define it as below.

<!--
############
from collections import defaultdict

class DisplayGrammar(gatleast.DisplayGrammar):

    def definition_rev_split_to_rulesets(self, d1):
        rule_sets = defaultdict(list)
        for r in d1:
            if len(r) > 0:
                assert not self.is_nonterminal(r[0]) # no degenerate rules
                assert self.is_nonterminal(r[1]) # no degenerate rules
                rule_sets[r[1]].append(r)
            else:
                rule_sets[''].append(r)
        return rule_sets

    def display_terminals(sefl, terminals, negate=False):
        if negate: return '[^%s]' % (''.join(terminals))
        else:
            if len(terminals) == 1:
                return terminals[0]
            return '[%s]' % (''.join(terminals))

    def display_ruleset(self, nonterminal, ruleset, pre, all_terminal_symbols=TERMINAL_SYMBOLS):
        if ruleset == [[]]:
            print('| {EMPTY}')
            return
        terminals = [t[0] for t in ruleset]
        rem_terminals = [t for t in all_terminal_symbols if t not in terminals]
        if len(terminals) <= len(rem_terminals):
            v = '%s %s' % (self.display_terminals(terminals), nonterminal)
            s = '%s|   %s' % (pre, v)
            print(s)
        else:
            if rem_terminals == []:
                v = '. %s' % nonterminal
            else:
                v = '%s %s' % (self.display_terminals(rem_terminals, negate=True), nonterminal)
            s = '%s|   %s' % (pre, v)
            print(s)

    def display_definition(self, key, r):
        if self.verbose > -1: print(key,'::=')
        rulesets = self.definition_rev_split_to_rulesets(self.grammar[key])
        for nonterminal in rulesets:
            pre = ''
            self.display_ruleset(nonterminal, rulesets[nonterminal], pre, all_terminal_symbols=TERMINAL_SYMBOLS)
        return r

    def display_unused(self, unused, verbose):
        pass

def display_canonical_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from collections import defaultdict

class DisplayGrammar(gatleast.DisplayGrammar):

    def definition_rev_split_to_rulesets(self, d1):
        rule_sets = defaultdict(list)
        for r in d1:
            if len(r) &gt; 0:
                assert not self.is_nonterminal(r[0]) # no degenerate rules
                assert self.is_nonterminal(r[1]) # no degenerate rules
                rule_sets[r[1]].append(r)
            else:
                rule_sets[&#x27;&#x27;].append(r)
        return rule_sets

    def display_terminals(sefl, terminals, negate=False):
        if negate: return &#x27;[^%s]&#x27; % (&#x27;&#x27;.join(terminals))
        else:
            if len(terminals) == 1:
                return terminals[0]
            return &#x27;[%s]&#x27; % (&#x27;&#x27;.join(terminals))

    def display_ruleset(self, nonterminal, ruleset, pre, all_terminal_symbols=TERMINAL_SYMBOLS):
        if ruleset == [[]]:
            print(&#x27;| {EMPTY}&#x27;)
            return
        terminals = [t[0] for t in ruleset]
        rem_terminals = [t for t in all_terminal_symbols if t not in terminals]
        if len(terminals) &lt;= len(rem_terminals):
            v = &#x27;%s %s&#x27; % (self.display_terminals(terminals), nonterminal)
            s = &#x27;%s|   %s&#x27; % (pre, v)
            print(s)
        else:
            if rem_terminals == []:
                v = &#x27;. %s&#x27; % nonterminal
            else:
                v = &#x27;%s %s&#x27; % (self.display_terminals(rem_terminals, negate=True), nonterminal)
            s = &#x27;%s|   %s&#x27; % (pre, v)
            print(s)

    def display_definition(self, key, r):
        if self.verbose &gt; -1: print(key,&#x27;::=&#x27;)
        rulesets = self.definition_rev_split_to_rulesets(self.grammar[key])
        for nonterminal in rulesets:
            pre = &#x27;&#x27;
            self.display_ruleset(nonterminal, rulesets[nonterminal], pre, all_terminal_symbols=TERMINAL_SYMBOLS)
        return r

    def display_unused(self, unused, verbose):
        pass

def display_canonical_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Make sure it works

<!--
############
g0, s0 = {
     '<start0>' : [['a', '<A0>']],
     '<A0>' : [['b', '<B0>'], ['c', '<C0>']],
     '<B0>' : [['c', NT_ANY_STAR]],
     '<C0>' : [['d', NT_EMPTY]]
}, '<start0>'
display_canonical_grammar(g0, s0)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g0, s0 = {
     &#x27;&lt;start0&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A0&gt;&#x27;]],
     &#x27;&lt;A0&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;B0&gt;&#x27;], [&#x27;c&#x27;, &#x27;&lt;C0&gt;&#x27;]],
     &#x27;&lt;B0&gt;&#x27; : [[&#x27;c&#x27;, NT_ANY_STAR]],
     &#x27;&lt;C0&gt;&#x27; : [[&#x27;d&#x27;, NT_EMPTY]]
}, &#x27;&lt;start0&gt;&#x27;
display_canonical_grammar(g0, s0)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 Now, all together.

<!--
############
def canonical_regular_grammar(g0, s0):
    g1, s1 = remove_degenerate_rules(g0, s0)

    g2, s2 = remove_multi_terminals(g1, s1)

    g3, s3 = collapse_similar_starting_rules(g2, s2)

    g4, s4 = fix_empty_rules(g3, s3)
    return g4, s4

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def canonical_regular_grammar(g0, s0):
    g1, s1 = remove_degenerate_rules(g0, s0)

    g2, s2 = remove_multi_terminals(g1, s1)

    g3, s3 = collapse_similar_starting_rules(g2, s2)

    g4, s4 = fix_empty_rules(g3, s3)
    return g4, s4
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
gatleast.display_grammar(g1, s1)
g, s = canonical_regular_grammar(g1, s1)
display_canonical_grammar(g, s)

print('________')

gatleast.display_grammar(g2, s2)
g, s = canonical_regular_grammar(g2, s2)
display_canonical_grammar(g, s)

print('________')
gatleast.display_grammar(g3, s3)
g, s = canonical_regular_grammar(g3, s3)
display_canonical_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gatleast.display_grammar(g1, s1)
g, s = canonical_regular_grammar(g1, s1)
display_canonical_grammar(g, s)

print(&#x27;________&#x27;)

gatleast.display_grammar(g2, s2)
g, s = canonical_regular_grammar(g2, s2)
display_canonical_grammar(g, s)

print(&#x27;________&#x27;)
gatleast.display_grammar(g3, s3)
g, s = canonical_regular_grammar(g3, s3)
display_canonical_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## A canonical regular grammar from a regular expression.


<!--
############
def regexp_to_regular_grammar(regexp):
    g1, s1 = rxregular.RegexToRGrammar().to_grammar(regexp)
    g2, s2 = canonical_regular_grammar(g1, s1)
    return g2, s2

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regexp_to_regular_grammar(regexp):
    g1, s1 = rxregular.RegexToRGrammar().to_grammar(regexp)
    g2, s2 = canonical_regular_grammar(g1, s1)
    return g2, s2
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
my_re = '(a|b|c).(de|f)'
print(my_re)
g, s = regexp_to_regular_grammar(my_re)
display_canonical_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;(a|b|c).(de|f)&#x27;
print(my_re)
g, s = regexp_to_regular_grammar(my_re)
display_canonical_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-24-canonical-regular-grammar.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
