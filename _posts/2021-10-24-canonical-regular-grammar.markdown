---
published: true
title: Canonical Regualar Grammars
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
rxfuzzer = import_file(&#x27;rxfuzzer&#x27;, &#x27;2021-10-22-fuzzing-with-regular-expressions.py&#x27;)
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

    new_g = defaultdict(list)
    for k in g:
        my_rules = {str(r):r for r in g[k]}
        new_g[k] = [my_rules[k] for k in my_rules]
    return new_g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
from collections import defaultdict

def is_degenerate_rule(rule):
    return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

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

    new_g = defaultdict(list)
    for k in g:
        my_rules = {str(r):r for r in g[k]}
        new_g[k] = [my_rules[k] for k in my_rules]
    return new_g, s
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
    return new_g, s

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
    return new_g, s
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
## Add empty rule
If there are any rules of the form $$ A \rightarrow b $$, we replace it by
$$ A \rightarrow b E $$, $$ E \rightarrow \epsilon $$. The reason for doing
this is to make sure that we have a single termination point.

<!--
############
EMPTY_NT = '<_>'
def add_empty_rule(g, s):
    new_g = defaultdict(list)
    new_g[EMPTY_NT] = [[]]
    for k in g:
        for r in g[k]:
            if len(r) == 1:
                tok = r[0]
                assert fuzzer.is_terminal(tok)
                new_g[k].append([tok, EMPTY_NT])
            else:
                new_g[k].append(r)
    return new_g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
EMPTY_NT = &#x27;&lt;_&gt;&#x27;
def add_empty_rule(g, s):
    new_g = defaultdict(list)
    new_g[EMPTY_NT] = [[]]
    for k in g:
        for r in g[k]:
            if len(r) == 1:
                tok = r[0]
                assert fuzzer.is_terminal(tok)
                new_g[k].append([tok, EMPTY_NT])
            else:
                new_g[k].append(r)
    return new_g, s
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
 Now, all together.

<!--
############
def canonical_regular_grammar(g0, s0):
    g1, s1 = remove_degenerate_rules(g0, s0)

    #
    g2, s2 = remove_multi_terminals(g1, s1)
    g3, s3 = add_empty_rule(g2, s2)
    #

    g4, s4 = collapse_similar_starting_rules(g3, s3)
    return g4, s4

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def canonical_regular_grammar(g0, s0):
    g1, s1 = remove_degenerate_rules(g0, s0)

    #
    g2, s2 = remove_multi_terminals(g1, s1)
    g3, s3 = add_empty_rule(g2, s2)
    #

    g4, s4 = collapse_similar_starting_rules(g3, s3)
    return g4, s4
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g, s = canonical_regular_grammar(g1, s1)
gatleast.display_grammar(g, s)

g, s = canonical_regular_grammar(g2, s2)
gatleast.display_grammar(g, s)

g, s = canonical_regular_grammar(g3, s3)
gatleast.display_grammar(g, s)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, s = canonical_regular_grammar(g1, s1)
gatleast.display_grammar(g, s)

g, s = canonical_regular_grammar(g2, s2)
gatleast.display_grammar(g, s)

g, s = canonical_regular_grammar(g3, s3)
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
