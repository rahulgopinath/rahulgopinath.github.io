---
published: true
title: Specializing Context-Free Grammars for Not Inducing A Fault
layout: post
comments: true
tags: python
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

<script src="/resources/js/graphviz/index.min.js"></script>
<script>
// From https://github.com/hpcc-systems/hpcc-js-wasm
// Hosted for teaching.
var hpccWasm = window["@hpcc-js/wasm"];
function display_dot(dot_txt, div) {
    hpccWasm.graphviz.layout(dot_txt, "svg", "dot").then(svg => {
        div.innerHTML = svg;
    });
}
window.display_dot = display_dot
// from js import display_dot
</script>

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

This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)

In my previous post on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
I explained the deficiency of abstract failure inducing inputs mined using
DDSet, and showed how to overcome that by inserting that abstract (evocative)
pattern into a grammar, producing evocative grammars that guarantee that the
evocative fragment is present in any input generated. In this post, I will show
how to do the opposite. That is, how to generate grammars that guarantee that
evocative fragments are not present.
As before, let us start with importing our required modules.

<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<ol>
<li>sympy</li>
</ol>
<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
sympy
</textarea>
</form>
</div>
</details>

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">earleyparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/02/06/earley-parsing/">Earley Parser</a>".</li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">hdd-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/12/04/hdd/">Hierarchical Delta Debugging</a>".</li>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">ddset-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/08/03/simple-ddset/">Simple DDSet</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl">gmultiplefaults-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/10/multiple-fault-grammars/">Specializing Context-Free Grammars for Inducing Multiple Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gfaultexpressions-0.0.1-py2.py3-none-any.whl">gfaultexpressions-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/11/fault-expressions/">Fault Expressions for Specializing Context-Free Grammars</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gfaultexpressions-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import hdd
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gmultiplefaults as gmultiple

import sympy
import itertools as I

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import hdd
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gmultiplefaults as gmultiple

import sympy
import itertools as I
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
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For unmatching a refined rule in a pattern grammar, we simply can look at
refinements necessary, and produce rules such that each produced rule will
*not* match the pattern at a specific point. No further restrictions on
the rule is necessary. So, we can use the base nonterminal there.

<!--
############
def unmatch_a_refined_rule_in_pattern_grammar(refined_rule):
    negated_rules = []
    for pos,token in enumerate(refined_rule):
        if not fuzzer.is_nonterminal(token): continue
        if gatleast.is_base_key(token): continue
        r = [negate_nonterminal(t) if i==pos else
                (gmultiple.normalize(t) if fuzzer.is_nonterminal(t) else t)
                for i,t in enumerate(refined_rule)]
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
def unmatch_a_refined_rule_in_pattern_grammar(refined_rule):
    negated_rules = []
    for pos,token in enumerate(refined_rule):
        if not fuzzer.is_nonterminal(token): continue
        if gatleast.is_base_key(token): continue
        r = [negate_nonterminal(t) if i==pos else
                (gmultiple.normalize(t) if fuzzer.is_nonterminal(t) else t)
                for i,t in enumerate(refined_rule)]
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

def base_rep(t):
    if fuzzer.is_nonterminal(t):
        return gmultiple.normalize(t)
    return t

def negate_pattern_grammar(pattern_grammar, pattern_start, base_grammar,
        nfault_suffix):
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
                        if base_rep(t) in keys_that_can_reach_fault
                        else t for t in rule]
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

def base_rep(t):
    if fuzzer.is_nonterminal(t):
        return gmultiple.normalize(t)
    return t

def negate_pattern_grammar(pattern_grammar, pattern_start, base_grammar,
        nfault_suffix):
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
                        if base_rep(t) in keys_that_can_reach_fault
                        else t for t in rule]
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
At this point, we can now define our `negated_grammar()`
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

    # We cant add `unreach_g[unreaching_sym]` directly to
    # `combined_grammar[unreaching_sym]` because it will then match
    # ```
    # [['<factor neg(F1)>',
    #         [['(', []],
    #          ['<expr neg(F1)>',
    #              [['<term neg(F1)>',
    #                  [['<factor neg(F1)>',
    #                      [['(', []],
    #                       ['<expr neg(F1)>', ],
    #                       [')', []]]]]]]],
    #          [')',    []]]]]
    # ```
    # So, what we will do, is to make sure that the combined rules do not either
    # reach the negated patterns nor do the match the negated patterns.

    anded_defs = gmultiple.and_definitions(unreach_g[unreaching_sym],
                                            nomatch_g[nomatch_s])

    combined_grammar[unreaching_sym] = anded_defs

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

    # We cant add `unreach_g[unreaching_sym]` directly to
    # `combined_grammar[unreaching_sym]` because it will then match
    # ```
    # [[&#x27;&lt;factor neg(F1)&gt;&#x27;,
    #         [[&#x27;(&#x27;, []],
    #          [&#x27;&lt;expr neg(F1)&gt;&#x27;,
    #              [[&#x27;&lt;term neg(F1)&gt;&#x27;,
    #                  [[&#x27;&lt;factor neg(F1)&gt;&#x27;,
    #                      [[&#x27;(&#x27;, []],
    #                       [&#x27;&lt;expr neg(F1)&gt;&#x27;, ],
    #                       [&#x27;)&#x27;, []]]]]]]],
    #          [&#x27;)&#x27;,    []]]]]
    # ```
    # So, what we will do, is to make sure that the combined rules do not either
    # reach the negated patterns nor do the match the negated patterns.

    anded_defs = gmultiple.and_definitions(unreach_g[unreaching_sym],
                                            nomatch_g[nomatch_s])

    combined_grammar[unreaching_sym] = anded_defs

    return combined_grammar, unreach_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
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
However, as you can see the grammar is not complete. For completing the
grammar We need to rely on `reconstruction` that we discussed in the last post.
Aside: Let us construct another function that checks the double
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
## Negation of full evocative expressions
Negation of a single pattern is useful, but we may also want
to negate larger expressions such as say `neg(or(and(f1,f2),f3))`. However, we
do not need to implement the complete negation as before. Instead, we can rely
on the fact that our evocative expressions are simply boolean expressions.
That is, expressions such `neg(or(A,B))` can be simplified as
`and(neg(A),neg(B))` and `neg(and(A,B))` can be simplified as
`or(neg(A),neg(B))`. This means that we do not need to implement the negation
beyond negating simple faults.
Here is an example of how it works.

<!--
############
import gfaultexpressions as gexpr
cnode = gatleast.ETREE_DPAREN
g1, s1 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, 'D1'))
g2, s2 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, 'Z1'))
grammar ={**hdd.EXPR_GRAMMAR, **g1,**g2}
g_, s_ = gexpr.complete(grammar, '<start neg(or(D1,Z1))>')
gatleast.display_grammar(g_,s_)
print()
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed and check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)

g_, s_ = gexpr.complete(grammar, '<start neg(and(D1,Z1))>')
gatleast.display_grammar(g_,s_)
print()
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed or check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import gfaultexpressions as gexpr
cnode = gatleast.ETREE_DPAREN
g1, s1 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DPAREN, &#x27;D1&#x27;))
g2, s2 = gatleast.grammar_gc(no_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, gatleast.ETREE_DZERO, &#x27;Z1&#x27;))
grammar ={**hdd.EXPR_GRAMMAR, **g1,**g2}
g_, s_ = gexpr.complete(grammar, &#x27;&lt;start neg(or(D1,Z1))&gt;&#x27;)
gatleast.display_grammar(g_,s_)
print()
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed and check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)

g_, s_ = gexpr.complete(grammar, &#x27;&lt;start neg(and(D1,Z1))&gt;&#x27;)
gatleast.display_grammar(g_,s_)
print()
gf = fuzzer.LimitFuzzer(g_)
for i in range(100):
    t = gf.iter_gen_key(key=s_, max_depth=10)
    v = fuzzer.tree_to_string(t)
    assert gatleast.expr_div_by_zero(v) == hdd.PRes.failed or check_doubled_paren(v) == hdd.PRes.failed, (v, t)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-12-negated-fault-grammars.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-12-negated-fault-grammars.py).


The installable python wheel `gnegatedfaults` is available [here](/py/gnegatedfaults-0.0.1-py2.py3-none-any.whl).

