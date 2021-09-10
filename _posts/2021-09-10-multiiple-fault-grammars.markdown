---
published: true
title: Specializing Grammars for Inducing Multiple Faults
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
In my previous post on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
I explained the deficiency of abstract failure inducing inputs mined using
DDSet, and showed how to overcome that by inserting that abstract (evocative)
pattern into a grammar, producing evocative grammars that guarantee that the
evocative fragment is present in any input generated.
However, what if one wants to produce inputs that contain two evocative
fragments? This is what we will discuss in this post.

As before, let us start with importing our required modules.

<!--
############
import sys, imp
import itertools as I

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
import itertools as I

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
We import the following modules

<!--
############
earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
hdd = import_file('hdd', '2019-12-04-hdd.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
ddset = import_file('ddset', '2020-08-03-simple-ddset.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
hdd = import_file(&#x27;hdd&#x27;, &#x27;2019-12-04-hdd.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
ddset = import_file(&#x27;ddset&#x27;, &#x27;2020-08-03-simple-ddset.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# Produing inputs with two fault inducing fragments guaranteed to be present.
From the previous post [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
we extracted two evocative subtrees

<!--
############
print(ddset.abstract_tree_to_str(gatleast.ETREE_DPAREN))
ddset.display_abstract_tree(gatleast.ETREE_DPAREN)
print()
print(ddset.abstract_tree_to_str(gatleast.ETREE_DZERO))
ddset.display_abstract_tree(gatleast.ETREE_DZERO)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(ddset.abstract_tree_to_str(gatleast.ETREE_DPAREN))
ddset.display_abstract_tree(gatleast.ETREE_DPAREN)
print()
print(ddset.abstract_tree_to_str(gatleast.ETREE_DZERO))
ddset.display_abstract_tree(gatleast.ETREE_DZERO)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now want to produce a grammar such that any input produced from that
grammar is guaranteed to contain both evocative subtrees. First, let us
extract the corresponding grammars. Here is the first one

<!--
############
g1, s1 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, 'D1'))
gatleast.display_grammar(g1, s1)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1, s1 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, &#x27;D1&#x27;))
gatleast.display_grammar(g1, s1)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the second grammar.

<!--
############
g2, s2 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, 'Z1'))
gatleast.display_grammar(g2, s2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2, s2 = gatleast.grammar_gc(gatleast.atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, &#x27;Z1&#x27;))
gatleast.display_grammar(g2, s2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we want to combine these grammars. Remember that a gramamr has a set of
definitions that correspond to nonterminals, and each definition has a set of
rules. We start from the rules. If we want to combine two grammars, we need
to make sure that any input produced from the combined grammar is also parsed
by the original grammars. That is, any rule from the combined grammar should
have a corresponding rule in the original grammars. This gives us the
algorithm for combining two rules. First, we can only combine rules that have
similar base representation. That is, if ruleA is `[<A f1>, <B f2>, 'T']` 
where `<A>` and `<B>` are nonterminals and `T` is a terminal
and ruleB is `[<A f1>, <C f3>]`, these can't have a combination in the
combined grammar. On the other hand, if ruleB is `[<A f3>, <B f4> 'T']`
then, a combined rule of `[<A f1 & f3>, <B f2 & f4>, 'T']` can infact
represent both parent rules. That is, when combining two rules from different,
grammars, their combination is empty if they have different base
representation.
## Combining tokens
If they have the same base representation, then we only have to deal with how
to combine the nonterminal symbols. The terminal symbols are exactly the same
in parent rules as well as combined rule. So, given two tokens, we can
combine them as follows.

<!--
############
def and_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k2
    if not s2: return k1
    if s1 == s2: return k1
    return '<%s and(%s,%s)>' % (b1, s1, s2)

def and_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return and_nonterminals(t1, t2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_nonterminals(k1, k2):
    b1, s1 = gatleast.tsplit(k1)
    b2, s2 = gatleast.tsplit(k2)
    assert b1 == b2
    if not s1: return k2
    if not s2: return k1
    if s1 == s2: return k1
    return &#x27;&lt;%s and(%s,%s)&gt;&#x27; % (b1, s1, s2)

def and_tokens(t1, t2):
    if not fuzzer.is_nonterminal(t1): return t1
    return and_nonterminals(t1, t2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
print(and_tokens('C', 'C'))
print(and_tokens('<A>', '<A f1>'))
print(and_tokens('<A f2>', '<A f1>'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(and_tokens(&#x27;C&#x27;, &#x27;C&#x27;))
print(and_tokens(&#x27;&lt;A&gt;&#x27;, &#x27;&lt;A f1&gt;&#x27;))
print(and_tokens(&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;A f1&gt;&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Combining rules
Next, we define combination for rules

<!--
############
def and_rules(ruleA, ruleB):
    AandB_rule = []
    for t1,t2 in zip(ruleA, ruleB):
        AandB_rule.append(and_tokens(t1, t2))
    return AandB_rule

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_rules(ruleA, ruleB):
    AandB_rule = []
    for t1,t2 in zip(ruleA, ruleB):
        AandB_rule.append(and_tokens(t1, t2))
    return AandB_rule
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
print(and_rules(['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']))
print(and_rules(['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))
print(and_rules(['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(and_rules([&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;C&#x27;]))
print(and_rules([&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]))
print(and_rules([&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Combining rulesets

Next, our grammars may contain multiple rules that represent the same base
rule. All the rules that represent the same base rule is called a ruleset.
combining two rulesets is done by producing a new ruleset that contains all
possible pairs of rules from the parent ruleset.

<!--
############
def and_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = and_rules(ruleA, ruleB)
        rules.append(AandB_rule)
    return rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_ruleset(rulesetA, rulesetB):
    rules = []
    for ruleA,ruleB in I.product(rulesetA, rulesetB):
        AandB_rule = and_rules(ruleA, ruleB)
        rules.append(AandB_rule)
    return rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
A = [['<A>', '<B f1>', 'C'], ['<A f1>', '<B>', 'C']]
B = [['<A f2>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
C = [['<A f1>', '<B f1>', 'C'], ['<A f1>', '<B f3>', 'C']]
for k in and_ruleset(A, B): print(k)
print()
for k in and_ruleset(A, C): print(k)
print()
for k in and_ruleset(B, C): print(k)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
A = [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;C&#x27;]]
B = [[&#x27;&lt;A f2&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]]
C = [[&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f1&gt;&#x27;, &#x27;C&#x27;], [&#x27;&lt;A f1&gt;&#x27;, &#x27;&lt;B f3&gt;&#x27;, &#x27;C&#x27;]]
for k in and_ruleset(A, B): print(k)
print()
for k in and_ruleset(A, C): print(k)
print()
for k in and_ruleset(B, C): print(k)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we define a few helper functions that collects all rulesets

<!--
############
def normalize(key):
    if gatleast.is_base_key(key): return key
    return '<%s>' % gatleast.stem(key)

def normalize_grammar(g):
    return {normalize(k):list({tuple([normalize(t) if fuzzer.is_nonterminal(t) else t for t in r]) for r in g[k]}) for k in g}

def rule_to_normalized_rule(rule):
    return [normalize(t) if fuzzer.is_nonterminal(t) else t for t in rule]

def normalized_rule_match(r1, r2):
    return rule_to_normalized_rule(r1) == rule_to_normalized_rule(r2)

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA if not normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def get_rulesets(rules):
    rulesets = {}
    for rule in rules:
        nr = tuple(rule_to_normalized_rule(rule))
        if nr not in rulesets: rulesets[nr] = []
        rulesets[nr].append(rule)
    return rulesets

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def normalize(key):
    if gatleast.is_base_key(key): return key
    return &#x27;&lt;%s&gt;&#x27; % gatleast.stem(key)

def normalize_grammar(g):
    return {normalize(k):list({tuple([normalize(t) if fuzzer.is_nonterminal(t) else t for t in r]) for r in g[k]}) for k in g}

def rule_to_normalized_rule(rule):
    return [normalize(t) if fuzzer.is_nonterminal(t) else t for t in rule]

def normalized_rule_match(r1, r2):
    return rule_to_normalized_rule(r1) == rule_to_normalized_rule(r2)

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA if not normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def get_rulesets(rules):
    rulesets = {}
    for rule in rules:
        nr = tuple(rule_to_normalized_rule(rule))
        if nr not in rulesets: rulesets[nr] = []
        rulesets[nr].append(rule)
    return rulesets
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## definition combinations
Now, we can define the combination of definitions as follows.

<!--
############
def and_definitions(rulesA, rulesB):
    AandB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) & set(rulesetsB.keys())
    for k in keys:
        new_rules = and_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_definitions(rulesA, rulesB):
    AandB_rules = []
    rulesetsA, rulesetsB = get_rulesets(rulesA), get_rulesets(rulesB)
    # drop any rules that are not there in both.
    keys = set(rulesetsA.keys()) &amp; set(rulesetsB.keys())
    for k in keys:
        new_rules = and_ruleset(rulesetsA[k], rulesetsB[k])
        AandB_rules.extend(new_rules)
    return AandB_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
expr1 = [r for k in g1 if 'expr' in k for r in g1[k]]
expr2 = [r for k in g2 if 'expr' in k for r in g2[k]]
for k in and_definitions(expr1, expr2):
    print(k)
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr1 = [r for k in g1 if &#x27;expr&#x27; in k for r in g1[k]]
expr2 = [r for k in g2 if &#x27;expr&#x27; in k for r in g2[k]]
for k in and_definitions(expr1, expr2):
    print(k)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## grammar combination
We can now define our grammar combination as follows.

<!--
############
def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    for k1,k2 in I.product(g1_keys, g2_keys):
        if normalize(k1) != normalize(k2): continue
        and_key = and_tokens(k1, k2)
        g[and_key] = and_definitions(g1[k1], g2[k2])
    return g, and_tokens(s1, s2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_grammars_(g1, s1, g2, s2):
    g1_keys = g1.keys()
    g2_keys = g2.keys()
    g = {**g1, **g2}
    for k1,k2 in I.product(g1_keys, g2_keys):
        if normalize(k1) != normalize(k2): continue
        and_key = and_tokens(k1, k2)
        g[and_key] = and_definitions(g1[k1], g2[k2])
    return g, and_tokens(s1, s2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
combined_g, combined_s = gatleast.grammar_gc(and_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(combined_g, combined_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
combined_g, combined_s = gatleast.grammar_gc(and_grammars_(g1, s1, g2, s2))
gatleast.display_grammar(combined_g, combined_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed not to produce any instance of the characterizing node.
Using it.

<!--
############
combined_f = fuzzer.LimitFuzzer(combined_g)
for i in range(10):
    v = combined_f.iter_fuzz(key=combined_s, max_depth=10)
    assert gatleast.expr_div_by_zero(v)
    assert hdd.expr_double_paren(v)
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
combined_f = fuzzer.LimitFuzzer(combined_g)
for i in range(10):
    v = combined_f.iter_fuzz(key=combined_s, max_depth=10)
    assert gatleast.expr_div_by_zero(v)
    assert hdd.expr_double_paren(v)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the runnable source of this notebook can be found [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-10-multiple-fault-grammars.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
