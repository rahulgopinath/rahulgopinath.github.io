---
published: true
title: Specializing Grammars for Not Inducing A Fault
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
evocative fragment is present in any input generated. In this post, I will show
how to do the opposite. That is, how to generate grammars that guarantee that
evocative fragments are not present.
As before, let us start with importing our required modules.

<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
"mpmath-1.2.1-py3-none-any.whl"
"sympy-1.8-py3-none-any.whl"
</textarea>
</form>

<!--
############
import sys, imp
import itertools as I
import sympy

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
import sympy

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
gmultiple = import_file('gmultiple', '2021-09-10-multiple-fault-grammars.py')
gexpr = import_file('gexpr', '2021-09-11-fault-expressions.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
hdd = import_file(&#x27;hdd&#x27;, &#x27;2019-12-04-hdd.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
ddset = import_file(&#x27;ddset&#x27;, &#x27;2020-08-03-simple-ddset.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
gmultiple = import_file(&#x27;gmultiple&#x27;, &#x27;2021-09-10-multiple-fault-grammars.py&#x27;)
gexpr = import_file(&#x27;gexpr&#x27;, &#x27;2021-09-11-fault-expressions.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
# A grammar with no fault inducing fragments.
We saw how to insert a single evocative pattern into a grammar.
A similar procedure can be used to make sure that no evocative
fragments are present in inputs generated by given grammar.
The idea is as follows.
## Unreachable Grammar
We start with the `get_reachable_positions()` output. If we can ensure
that no nonterminals in the reachable_positions can actually produce a fault
inducing fragment, then we are done. So, given the `get_reachable_positions`
we can produce the unreachable grammar.

For ease of discussion, we name a
nonterminal E that is guaranteed to not produce fault tree `F` as `<E neg(F)>`.
That is, a tree that starts from <start neg(F)> is guaranteed not to contain
the fault tree `F`.
So, the definition of `<E neg(F)` is simple enough given the characterizing
node of the fault tree, and the corresponding reaching positions in the
grammar.
For each expansion rule of `<E>`, we have to make sure that it does not lead
to `F`. So rules for `<E>` that did not have reachable positions corresponding
to characterizing node of `F` can be directly added to `<E neg(F)>`. Next,
for any rule that contained reachable positions, for all such positions, we
specialize the nonterminal in that position by `neg(F)`. This gives us the
unreachable grammar.

<!--
############
def negate_suffix(fault):
    assert fault
    return 'neg(%s)' % fault

def unreachable_key(grammar, key, cnodesym, negated_suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = gatleast.get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # not embeddable here. We can add this rule.
            my_rules.append(rule)
        else:
            new_rule = [gatleast.refine_base_key(t, negated_suffix)
                    if p in positions else t for p,t in enumerate(rule)]
            my_rules.append(new_rule)
    return (gatleast.refine_base_key(key, negated_suffix), my_rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_suffix(fault):
    assert fault
    return &#x27;neg(%s)&#x27; % fault

def unreachable_key(grammar, key, cnodesym, negated_suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = gatleast.get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # not embeddable here. We can add this rule.
            my_rules.append(rule)
        else:
            new_rule = [gatleast.refine_base_key(t, negated_suffix)
                    if p in positions else t for p,t in enumerate(rule)]
            my_rules.append(new_rule)
    return (gatleast.refine_base_key(key, negated_suffix), my_rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
reaching = gatleast.reachable_dict(hdd.EXPR_GRAMMAR)
for key in hdd.EXPR_GRAMMAR:
    fk, rules = unreachable_key(hdd.EXPR_GRAMMAR, key, '<factor>',
                                negate_suffix('F1'), reaching)
    print(fk)
    for r in rules:
        print('    ', r)
    print()


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
reaching = gatleast.reachable_dict(hdd.EXPR_GRAMMAR)
for key in hdd.EXPR_GRAMMAR:
    fk, rules = unreachable_key(hdd.EXPR_GRAMMAR, key, &#x27;&lt;factor&gt;&#x27;,
                                negate_suffix(&#x27;F1&#x27;), reaching)
    print(fk)
    for r in rules:
        print(&#x27;    &#x27;, r)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we can define unreachable grammar using it.

<!--
############
def unreachable_grammar(grammar, start, cnodesym, negated_suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = unreachable_key(grammar, key, cnodesym, negated_suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unreachable_grammar(grammar, start, cnodesym, negated_suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = unreachable_key(grammar, key, cnodesym, negated_suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Negated pattern grammar.

For negated pattern grammars, there are two parts. The first part is for
pattern rules. The idea is to make sure that we can produce any but not the
specific pattern in the current expansion. Next, we also need to make sure
that the original fault is not reachable from any of the nonterminals.

<!--
############
def negate_nonterminal(k):
    return '<%s %s>' % (gatleast.stem(k), negate_suffix(gatleast.refinement(k)))

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA
                if not gmultiple.normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def unmatch_a_refined_rule_in_pattern_grammar(refined_rule):
    negated_rules = []
    for pos,token in enumerate(refined_rule):
        if not fuzzer.is_nonterminal(token): continue
        if gatleast.is_base_key(token): continue
        r = [negate_nonterminal(t) if i==pos else t for i,t in enumerate(refined_rule)]
        negated_rules.append(r)
    return negated_rules

def unmatch_definition_in_pattern_grammar(refined_rules, base_rules):
    # Given the set of rules, we take one rule at a time,
    # and generate the negated rule set from that.
    negated_rules_refined = []
    for ruleR in refined_rules:
        neg_rules = unmatch_a_refined_rule_in_pattern_grammar(ruleR)
        negated_rules_refined.extend(neg_rules)

    # Finally, we need to add the other non-matching rules to the pattern def.
    negated_rules_base = rule_normalized_difference(base_rules, refined_rules)

    return negated_rules_refined + negated_rules_base


def unmatch_pattern_grammar(pattern_grammar, pattern_start, base_grammar):
    negated_grammar = {}
    for l_key in pattern_grammar:
        l_rule = pattern_grammar[l_key][0]
        nl_key = negate_nonterminal(l_key)
        # find all rules that do not match, and add to negated_grammar,
        normal_l_key = gmultiple.normalize(l_key)
        base_rules = base_grammar[normal_l_key]
        refined_rules = pattern_grammar[l_key]

        negated_rules = unmatch_definition_in_pattern_grammar(refined_rules,
                                                              base_rules)
        negated_grammar[nl_key] = negated_rules
    return {**negated_grammar, **pattern_grammar} , negate_nonterminal(pattern_start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_nonterminal(k):
    return &#x27;&lt;%s %s&gt;&#x27; % (gatleast.stem(k), negate_suffix(gatleast.refinement(k)))

def rule_normalized_difference(rulesA, rulesB):
    rem_rulesA = rulesA
    for ruleB in rulesB:
        rem_rulesA = [rA for rA in rem_rulesA
                if not gmultiple.normalized_rule_match(rA, ruleB)]
    return rem_rulesA

def unmatch_a_refined_rule_in_pattern_grammar(refined_rule):
    negated_rules = []
    for pos,token in enumerate(refined_rule):
        if not fuzzer.is_nonterminal(token): continue
        if gatleast.is_base_key(token): continue
        r = [negate_nonterminal(t) if i==pos else t for i,t in enumerate(refined_rule)]
        negated_rules.append(r)
    return negated_rules

def unmatch_definition_in_pattern_grammar(refined_rules, base_rules):
    # Given the set of rules, we take one rule at a time,
    # and generate the negated rule set from that.
    negated_rules_refined = []
    for ruleR in refined_rules:
        neg_rules = unmatch_a_refined_rule_in_pattern_grammar(ruleR)
        negated_rules_refined.extend(neg_rules)

    # Finally, we need to add the other non-matching rules to the pattern def.
    negated_rules_base = rule_normalized_difference(base_rules, refined_rules)

    return negated_rules_refined + negated_rules_base


def unmatch_pattern_grammar(pattern_grammar, pattern_start, base_grammar):
    negated_grammar = {}
    for l_key in pattern_grammar:
        l_rule = pattern_grammar[l_key][0]
        nl_key = negate_nonterminal(l_key)
        # find all rules that do not match, and add to negated_grammar,
        normal_l_key = gmultiple.normalize(l_key)
        base_rules = base_grammar[normal_l_key]
        refined_rules = pattern_grammar[l_key]

        negated_rules = unmatch_definition_in_pattern_grammar(refined_rules,
                                                              base_rules)
        negated_grammar[nl_key] = negated_rules
    return {**negated_grammar, **pattern_grammar} , negate_nonterminal(pattern_start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
pattern_g,pattern_s, t = gatleast.pattern_grammar(gatleast.ETREE_DPAREN, 'F1')
nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_g,
                                               pattern_s, hdd.EXPR_GRAMMAR)
gatleast.display_grammar(nomatch_g, nomatch_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
pattern_g,pattern_s, t = gatleast.pattern_grammar(gatleast.ETREE_DPAREN, &#x27;F1&#x27;)
nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_g,
                                               pattern_s, hdd.EXPR_GRAMMAR)
gatleast.display_grammar(nomatch_g, nomatch_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, for negated pattern grammars, not only do we need to make sure that the
pattern is not directly matchable, but also that the pattern cannot be
embedded. For that we simply conjunct it with `neg(F1)`

<!--
############
def and_suffix(k1, suffix):
    if gatleast.is_base_key(k1):
        return '<%s %s>' % (gatleast.stem(k1), suffix)
    return '<%s and(%s,%s)>' % (gatleast.stem(k1), gatleast.refinement(k1), suffix)

def negate_pattern_grammar(pattern_grammar, pattern_start, base_grammar, nfault_suffix):
    reachable_keys = gatleast.reachable_dict(base_grammar)
    nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_grammar,
                                                   pattern_start, base_grammar)

    new_grammar = {}

    my_key = gmultiple.normalize(pattern_start)
    # which keys can reach pattern_start?
    keys_that_can_reach_fault = [k for k in reachable_keys
                                if my_key in reachable_keys[k]]
    #for k in keys_that_can_reach_fault: assert my_key in reachable_keys[k]
    new_g = {}
    for k in nomatch_g:
        new_rules = []
        for rule in nomatch_g[k]:
            new_rule = [and_suffix(t, nfault_suffix)
                        if t in keys_that_can_reach_fault else t for t in rule]
            new_rules.append(new_rule)
        new_g[k] = new_rules
    return new_g, negate_nonterminal(pattern_start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_suffix(k1, suffix):
    if gatleast.is_base_key(k1):
        return &#x27;&lt;%s %s&gt;&#x27; % (gatleast.stem(k1), suffix)
    return &#x27;&lt;%s and(%s,%s)&gt;&#x27; % (gatleast.stem(k1), gatleast.refinement(k1), suffix)

def negate_pattern_grammar(pattern_grammar, pattern_start, base_grammar, nfault_suffix):
    reachable_keys = gatleast.reachable_dict(base_grammar)
    nomatch_g, nomatch_s = unmatch_pattern_grammar(pattern_grammar,
                                                   pattern_start, base_grammar)

    new_grammar = {}

    my_key = gmultiple.normalize(pattern_start)
    # which keys can reach pattern_start?
    keys_that_can_reach_fault = [k for k in reachable_keys
                                if my_key in reachable_keys[k]]
    #for k in keys_that_can_reach_fault: assert my_key in reachable_keys[k]
    new_g = {}
    for k in nomatch_g:
        new_rules = []
        for rule in nomatch_g[k]:
            new_rule = [and_suffix(t, nfault_suffix)
                        if t in keys_that_can_reach_fault else t for t in rule]
            new_rules.append(new_rule)
        new_g[k] = new_rules
    return new_g, negate_nonterminal(pattern_start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
nomatch_g, nomatch_s = negate_pattern_grammar(pattern_g, pattern_s,
                                            hdd.EXPR_GRAMMAR, 'neg(F1)')
# next we need to conjunct
gatleast.display_grammar(nomatch_g, nomatch_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nomatch_g, nomatch_s = negate_pattern_grammar(pattern_g, pattern_s,
                                            hdd.EXPR_GRAMMAR, &#x27;neg(F1)&#x27;)
# next we need to conjunct
gatleast.display_grammar(nomatch_g, nomatch_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we can now define our 1negated_grammar()`
The new grammar is as follows

<!--
############
def no_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, tr = gatleast.pattern_grammar(cnode, fname)
    negated_suffix = negate_suffix(fname)
    nomatch_g, nomatch_s = negate_pattern_grammar(pattern_g,
                                pattern_s, grammar, negated_suffix)

    reachable_keys = gatleast.reachable_dict(grammar)
    reach_g, reach_s = gatleast.reachable_grammar(grammar,
                                start_symbol, key_f, fname, reachable_keys)
    unreach_g, unreach_s = unreachable_grammar(grammar,
                                start_symbol, key_f, negated_suffix, reachable_keys)

    combined_grammar = {**grammar, **nomatch_g, **reach_g, **unreach_g}
    unreaching_sym = gatleast.refine_base_key(key_f, negated_suffix)
    combined_grammar[unreaching_sym] = nomatch_g[nomatch_s]

    return combined_grammar, unreach_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def no_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, tr = gatleast.pattern_grammar(cnode, fname)
    negated_suffix = negate_suffix(fname)
    nomatch_g, nomatch_s = negate_pattern_grammar(pattern_g,
                                pattern_s, grammar, negated_suffix)

    reachable_keys = gatleast.reachable_dict(grammar)
    reach_g, reach_s = gatleast.reachable_grammar(grammar,
                                start_symbol, key_f, fname, reachable_keys)
    unreach_g, unreach_s = unreachable_grammar(grammar,
                                start_symbol, key_f, negated_suffix, reachable_keys)

    combined_grammar = {**grammar, **nomatch_g, **reach_g, **unreach_g}
    unreaching_sym = gatleast.refine_base_key(key_f, negated_suffix)
    combined_grammar[unreaching_sym] = nomatch_g[nomatch_s]

    return combined_grammar, unreach_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We cant add `unreach_g[unreaching_sym]` to `combined_grammar[unreaching_sym]`
because it will then match
```
[['<factor neg(F1)>',
        [['(', []],
         ['<expr neg(F1)>',
             [['<term neg(F1)>',
                 [['<factor neg(F1)>',
                     [['(', []],
                      ['<expr neg(F1)>', ],
                      [')', []]]]]]]],
         [')',    []]]]]
```
Using it.

<!--
############
cnode = gatleast.ETREE_DPAREN
g, s = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, cnode, 'F1'))
gatleast.display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cnode = gatleast.ETREE_DPAREN
g, s = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, cnode, &#x27;F1&#x27;))
gatleast.display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed not to produce any instance of the characterizing node.

<!--
############
failed = []
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    t = gf.iter_gen_key(key=s, max_depth=10)
    v = fuzzer.tree_to_string(t)
    # this will not necessarily work. Can you identify why?
    if hdd.expr_double_paren(v) != hdd.PRes.failed:
        failed.append((v,t))
    print(v)
print(len(failed))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
failed = []
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    t = gf.iter_gen_key(key=s, max_depth=10)
    v = fuzzer.tree_to_string(t)
    # this will not necessarily work. Can you identify why?
    if hdd.expr_double_paren(v) != hdd.PRes.failed:
        failed.append((v,t))
    print(v)
print(len(failed))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The problem here is that our evocative pattern did not fully capture the behavior
of `hdd.expr_double_paren`. Rather, it only captured the essence of a single
input that contained a doubled parenthesis. In this case, `((4))`. We would
have a different evocative pattern if we had started with say `((4)+(1))`.

For simplicity, let us construct another function that checks the double
parenthesis we abstracted.

<!--
############
import re
def check_doubled_paren(val):
    while '((' in val and '))' in val:
        val = re.sub(r'[^()]+','X', val)
        if '((X))' in val:
            return hdd.PRes.success
        val = val.replace(r'(X)', '')
    return hdd.PRes.failed

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import re
def check_doubled_paren(val):
    while &#x27;((&#x27; in val and &#x27;))&#x27; in val:
        val = re.sub(r&#x27;[^()]+&#x27;,&#x27;X&#x27;, val)
        if &#x27;((X))&#x27; in val:
            return hdd.PRes.success
        val = val.replace(r&#x27;(X)&#x27;, &#x27;&#x27;)
    return hdd.PRes.failed
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Checks

<!--
############
assert check_doubled_paren('((1))') == hdd.PRes.success
assert check_doubled_paren('((1)+(2))') == hdd.PRes.failed

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
assert check_doubled_paren(&#x27;((1))&#x27;) == hdd.PRes.success
assert check_doubled_paren(&#x27;((1)+(2))&#x27;) == hdd.PRes.failed
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now we can try the grammar again.

<!--
############
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    t = gf.iter_gen_key(key=s, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert check_doubled_paren(v) == hdd.PRes.failed
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    t = gf.iter_gen_key(key=s, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert check_doubled_paren(v) == hdd.PRes.failed
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Negation of full evocative expressions
Negation of a single pattern is useful, but we may also want
to negate larger expressions such as say `neg(or(and(f1,f2),f3))`
## Nonterminals
Let us start with negating nonterminals.

<!--
############
def negate_refinement(ref):
    return 'neg(%s)' % ref

def negate_nonterminal(key):
    stem, refinement = gatleast.tsplit(key)
    assert refinement
    return '<%s %s>' % (stem, negate_refinement(refinement))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_refinement(ref):
    return &#x27;neg(%s)&#x27; % ref

def negate_nonterminal(key):
    stem, refinement = gatleast.tsplit(key)
    assert refinement
    return &#x27;&lt;%s %s&gt;&#x27; % (stem, negate_refinement(refinement))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Negating a rule

Negating a rule produces as many rules as there are specialized
nonterminals in that rule.

<!--
############
def specialized_positions(rule):
    positions = []
    for i,t in enumerate(rule):
        if not gatleast.is_nonterminal(t):
            continue
        if gatleast.is_base_key(t):
            continue
        positions.append(i)
    return positions

def negate_rule(rule):
    positions = specialized_positions(rule)
    new_rules = []
    for p in positions:
        new_rule = [negate_nonterminal(t)
                        if i == p else t for i,t in enumerate(rule)]
        new_rules.append(new_rule)
    return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def specialized_positions(rule):
    positions = []
    for i,t in enumerate(rule):
        if not gatleast.is_nonterminal(t):
            continue
        if gatleast.is_base_key(t):
            continue
        positions.append(i)
    return positions

def negate_rule(rule):
    positions = specialized_positions(rule)
    new_rules = []
    for p in positions:
        new_rule = [negate_nonterminal(t)
                        if i == p else t for i,t in enumerate(rule)]
        new_rules.append(new_rule)
    return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Negation of a ruleset

negation of a ruleset is based on boolean algebra.
say a definition is `S = R1 | R2 | R3` then,
`neg(S)` is `neg(R1) & neg(R2) & neg(R3)`. Since each
`neg(R)` results in multiple `r` we apply distributive
law. That is,
`(r1|r2|r3) & (r4|r5|r6) & (r7|r8|r9)`
This gives r1&r4&r7 | r1&r4&r8 | etc.

<!--
############
def and_all_rules_to_one(rules):
    new_rule, *rules = rules
    while rules:
        r,*rules = rules
        new_rule = gmultiple.and_rules(new_rule, r)
    return new_rule

def negate_ruleset(rules):
    negated_rules_set = [negate_rule(ruleR) for ruleR in rules]
    negated_rules = []
    for rules in I.product(*negated_rules_set):
        r = and_all_rules_to_one(rules)
        negated_rules.append(r)
    return negated_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def and_all_rules_to_one(rules):
    new_rule, *rules = rules
    while rules:
        r,*rules = rules
        new_rule = gmultiple.and_rules(new_rule, r)
    return new_rule

def negate_ruleset(rules):
    negated_rules_set = [negate_rule(ruleR) for ruleR in rules]
    negated_rules = []
    for rules in I.product(*negated_rules_set):
        r = and_all_rules_to_one(rules)
        negated_rules.append(r)
    return negated_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Negation of a definition.
Negating a defintion adds any rules in the base that is not
part of the specialized definition. Then, we negate each
ruleset. Further, each nonterminal in rule is conjuncted
ith the specialization.

<!--
############
def negate_definition(specialized_key, rules, grammar):
    refined_rulesets = gmultiple.get_rulesets(refined_rules)
    base_key = gmultiple.normalize(specialized_key)
    base_rules = grammar[base_key]
    refinement = gatleast.refinement(specialized_key)

    # todo -- check if refined_rulesets key is in the right format.
    negated_rules = [r for r in base_rules if r not in refined_rulesets]

    for rule_rep in refined_rulesets:
        new_nrules = negate_ruleset(refined_rulesets[rule_rep])
        negated_rules.extend(new_nrules)

    conj_negated_rules = []
    for rule in negated_rules:
        conj_rule = [gmultiple.and_suffix(t, refinement)
                        if gatleast.is_nonterminal(t) else t for t in rule]
        conj_negated_rules.append(conj_rule)

    return conj_negated_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_definition(specialized_key, rules, grammar):
    refined_rulesets = gmultiple.get_rulesets(refined_rules)
    base_key = gmultiple.normalize(specialized_key)
    base_rules = grammar[base_key]
    refinement = gatleast.refinement(specialized_key)

    # todo -- check if refined_rulesets key is in the right format.
    negated_rules = [r for r in base_rules if r not in refined_rulesets]

    for rule_rep in refined_rulesets:
        new_nrules = negate_ruleset(refined_rulesets[rule_rep])
        negated_rules.extend(new_nrules)

    conj_negated_rules = []
    for rule in negated_rules:
        conj_rule = [gmultiple.and_suffix(t, refinement)
                        if gatleast.is_nonterminal(t) else t for t in rule]
        conj_negated_rules.append(conj_rule)

    return conj_negated_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Construction of a grammar negation.
At this point, we are ready to construct a negated grammar.
For negated grammars, we can simply return the grammar and negated start
and let the reconstruction happen in `complete()`

<!--
############
def negate_grammar_(grammar, start):
    nstart = negate_nonterminal(start)
    return grammar, nstart

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def negate_grammar_(grammar, start):
    nstart = negate_nonterminal(start)
    return grammar, nstart
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 We extend ReconstructRules with negation

<!--
############
def get_base_grammar(g):
    return {k:g[k] for k in g if gatleast.is_base_key(k)}

class ReconstructRules(gexpr.ReconstructRules):
    def reconstruct_neg_bexpr(self, key, bexpr):
        fst = bexpr.op_fst()
        base_grammar = get_base_grammar(self.grammar)
        f_key = bexpr.with_key(key)
        # if bexpr is not complex, that is, either f1 or neg(f1)
        # then f_key should bw in grammar.
        assert '(' not in f_key and ')' not in f_key
        # else, reconstruct.
        d, s = self.reconstruct_rules_from_bexpr(key, fst)
        d1, s1 = negate_definition(d, s, base_grammar)
        return d1, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_base_grammar(g):
    return {k:g[k] for k in g if gatleast.is_base_key(k)}

class ReconstructRules(gexpr.ReconstructRules):
    def reconstruct_neg_bexpr(self, key, bexpr):
        fst = bexpr.op_fst()
        base_grammar = get_base_grammar(self.grammar)
        f_key = bexpr.with_key(key)
        # if bexpr is not complex, that is, either f1 or neg(f1)
        # then f_key should bw in grammar.
        assert &#x27;(&#x27; not in f_key and &#x27;)&#x27; not in f_key
        # else, reconstruct.
        d, s = self.reconstruct_rules_from_bexpr(key, fst)
        d1, s1 = negate_definition(d, s, base_grammar)
        return d1, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We redefine `complete()`

<!--
############
def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = gatleast.grammar_gc(rr.reconstruct_key(start, log))
    return grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def complete(grammar, start, log=False):
    rr = ReconstructRules(grammar)
    grammar, start = gatleast.grammar_gc(rr.reconstruct_key(start, log))
    return grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
A better check for div by zero

<!--
############
cnode = gatleast.ETREE_DPAREN
g1, s1 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, 'D1'))
g2, s2 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, 'Z1'))
grammar ={**hdd.EXPR_GRAMMAR, **g1,**g2}
g_, s_ = complete(grammar, '<start neg(or(D1,Z1))>')
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed and check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cnode = gatleast.ETREE_DPAREN
g1, s1 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, &#x27;D1&#x27;))
g2, s2 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, &#x27;Z1&#x27;))
grammar ={**hdd.EXPR_GRAMMAR, **g1,**g2}
g_, s_ = complete(grammar, &#x27;&lt;start neg(or(D1,Z1))&gt;&#x27;)
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed and check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
