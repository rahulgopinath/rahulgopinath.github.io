---
published: true
title: Specializing Context-Free Grammars for Inducing Faults
layout: post
comments: true
tags: python
categories: post
---

## Contents
{:.no_toc}

1. TOC
{:toc}

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

This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)

In my previous post on [DDSet](/post/2020/08/03/simple-ddset/) I explained how
one can abstract failure inducing inputs. The idea is that given an input such
as `'1+((2*3/4))'` which induces a
failure in the program, one can extract a [minimal](/post/2019/12/04/hdd/)
failure inducing input such as say `'((4))'`, which can again be abstracted to
produce the expression `((<expr>))` which precisely defines the fault
inducing input. Such an input is quite useful for the developers to understand
why a failure occurred.

However, such inputs are insufficient from a testing perspective. For example,
such a pattern fails to capture the contexts in which the doubled parenthesis
can appear, and hence induce the failure. That is, how do we use the
pattern `((<expr>))` to produce inputs such as `'1+((2*3/4))'`? This is what
this post will discuss.

Note that the guarantee of inducing failures is statistical. That is, the
abstract input is mined by evaluating produced
inputs for failure a fixed (configurable) number of times. It is possible that
some rare inputs may still fail to induce the failure. Since abstract possibly
failure inducing inputs is a mouthful, let us call these abstract failure
inducing inputs **evocative patterns** for short. In this post, we will see
how to transform such an **evocative pattern** to an **evocative grammar** that is
guaranteed to produce *evocative inputs* (that is, each input contains an
**evocative fragment** and the derivation tree of the input contains an
**evocative subtree**) in all contexts that are guaranteed (statistically) to
induce failures.

As before, let us start with importing our required modules.

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.

<ol>
<li><a href="https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl</a></li>
<li><a href="https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl">https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl</a></li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import hdd
import simplefuzzer as fuzzer
import ddset

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import hdd
import simplefuzzer as fuzzer
import ddset
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The imported modules
We import the following modules
We have our input that causes the failure.

<!--
############
my_input = '1+((2*3/4))'
assert hdd.expr_double_paren(my_input) == hdd.PRes.success

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_input = &#x27;1+((2*3/4))&#x27;
assert hdd.expr_double_paren(my_input) == hdd.PRes.success
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We first parse the input

<!--
############
import earleyparser
expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
parsed_expr = list(expr_parser.parse_on(my_input, hdd.EXPR_START))[0]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import earleyparser
expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
parsed_expr = list(expr_parser.parse_on(my_input, hdd.EXPR_START))[0]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Then reduce input

<!--
############
reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, extract the abstract pattern.

<!--
############
evocative_pattern = ddset.ddset_abstract(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
ddset.display_abstract_tree(evocative_pattern)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
evocative_pattern = ddset.ddset_abstract(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
ddset.display_abstract_tree(evocative_pattern)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
However, it does not actually tell you in what all
circumstances the failure can be reproduced. The problem is that it
represents a *complete* abstract input. The only general part here is
`<expr>` between the doubled parenthesis. So, it tells us that we can
produce `((1))`, `((2 + 3))` etc. but these are not the only possible
errors. Indeed, our original error: '1+((2*3/4))' does not fit this
template. So, how can we rectify this limitation?
# A grammar that produces at least one evocative fragment per input generated.
The basic idea is that if we can find an *abstract subtree* of the 
evocative pattern derivation tree, such that the presence of this abstract
subtree in the input guarantees the failure, then we can modify the grammar
such that this abstract subtree is always present (we call the abstract
subtree an **evocative subtree**). That is, for any input
from such a grammar, at least one instance of the evocative 
subtree will be present. This is fairly easy to do if the generated tree
contains a nonterminal of the same kind as that of the top node of the evocative subtree.
Simply replace that node with the evocative subtree, and fill in the
abstract nonterminals in the evocative subtree with concrete expansions.
## Reachable Grammar

On the other hand, this gives us an idea. What if we modify the grammar
such that at least one instance of such a nonterminal is present? Such
a grammar is called the `reachable_grammar`.
To produce a reaching grammar, first we need to find what nonterminals are
reachable from the expansion of a given nonterminal.
A nonterminal `<A>` is reachable from another nonterminal `<B>` if and only
if one of the expansion rules for `<B>` contains the nonterminal `<A>` or
it is reachable from one of the nonterminals in the expansion rules of `<B>`
Note that it is not enough to be the same nonterminal. That is, (for e.g.)
`<A>` is not # reachable from `<A>` if expansion rules of `<A>` contain only
terminal symbols.

<!--
############
def find_reachable_keys(grammar, key, reachable_keys=None, found_so_far=None):
    if reachable_keys is None: reachable_keys = {}
    if found_so_far is None: found_so_far = set()

    for rule in grammar[key]:
        for token in rule:
            if not fuzzer.is_nonterminal(token): continue
            if token in found_so_far: continue
            found_so_far.add(token)
            if token in reachable_keys:
                for k in reachable_keys[token]:
                    found_so_far.add(k)
            else:
                keys = find_reachable_keys(grammar, token, reachable_keys, found_so_far)
    return found_so_far

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_reachable_keys(grammar, key, reachable_keys=None, found_so_far=None):
    if reachable_keys is None: reachable_keys = {}
    if found_so_far is None: found_so_far = set()

    for rule in grammar[key]:
        for token in rule:
            if not fuzzer.is_nonterminal(token): continue
            if token in found_so_far: continue
            found_so_far.add(token)
            if token in reachable_keys:
                for k in reachable_keys[token]:
                    found_so_far.add(k)
            else:
                keys = find_reachable_keys(grammar, token, reachable_keys, found_so_far)
    return found_so_far
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
for key in hdd.EXPR_GRAMMAR:
    keys = find_reachable_keys(hdd.EXPR_GRAMMAR, key, {})
    print(key, keys)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for key in hdd.EXPR_GRAMMAR:
    keys = find_reachable_keys(hdd.EXPR_GRAMMAR, key, {})
    print(key, keys)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now collect it in a data structure for easier access

<!--
############
def reachable_dict(grammar):
    reachable = {}
    for key in grammar:
        keys = find_reachable_keys(grammar, key, reachable)
        reachable[key] = keys
    return reachable

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def reachable_dict(grammar):
    reachable = {}
    for key in grammar:
        keys = find_reachable_keys(grammar, key, reachable)
        reachable[key] = keys
    return reachable
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, if we want to know the nonterminals that are reachable from `<integer>`,
we can simply do

<!--
############
reaching = reachable_dict(hdd.EXPR_GRAMMAR)
print(reaching['<integer>'])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
reaching = reachable_dict(hdd.EXPR_GRAMMAR)
print(reaching[&#x27;&lt;integer&gt;&#x27;])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, only `<digit>` and `<integer>` are reachable from the expansion of
nonterminal `<integer>`
## Reachable positions.
Next, given an evocative subtree, we want to find what tokens of the grammar
can actually embed such a subtree. We call the top node of an evocative
subtree its characterizing node, and the nonterminal the characterizing
nonterminal of the evocative subtree.

<!--
############
def get_reachable_positions(rule, fkey, reachable):
    positions = []
    for i, token in enumerate(rule):
        if not fuzzer.is_nonterminal(token): continue
        if fkey == token or fkey in reachable[token]:
            positions.append(i)
    return positions

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_reachable_positions(rule, fkey, reachable):
    positions = []
    for i, token in enumerate(rule):
        if not fuzzer.is_nonterminal(token): continue
        if fkey == token or fkey in reachable[token]:
            positions.append(i)
    return positions
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Say we assume that `<factor>` is the characterizing nonterminal. Here are the
locations in grammar where one can embed the evocative subtree.

<!--
############
for k in hdd.EXPR_GRAMMAR:
    print(k)
    for rule in hdd.EXPR_GRAMMAR[k]:
        v = get_reachable_positions(rule, '<factor>', reaching)
        print('\t', rule, v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for k in hdd.EXPR_GRAMMAR:
    print(k)
    for rule in hdd.EXPR_GRAMMAR[k]:
        v = get_reachable_positions(rule, &#x27;&lt;factor&gt;&#x27;, reaching)
        print(&#x27;\t&#x27;, rule, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Insertion Grammar
Given the insertion locations, can we produce a grammar such that we can
*guarantee* that *at least one* instance of evocative subtree can be inserted?
To do that, all we need to guarantee is that the start node in any derivation
tree can *reach* the characterizing nonterminal.
For now, let us call our fault `F1`. Let us indicate that our start symbol
guarantees reachability of characterizing nonterminal by specializing it. So, our new
start symbol is `<start F1>`

Next, for the start symbol to guarantee reachability to characterizing nonterminal,
all that we need to ensure is that *all* the expansion rules of start can
reach the characterizing nonterminal. On the other hand, for a guarantee that an
expansion rule can reach the characterizing nonterminal, all that is required is that
one of the nonterminals in that rule guarantees reachability.
We start with a few helper functions

<!--
############
def tsplit(token):
    assert token[0], token[-1] == ('<', '>')
    front, *back = token[1:-1].split(None, 1)
    return front, ' '.join(back)

def refinement(token):
    return tsplit(token)[1].strip()

def is_refined_key(key):
    assert fuzzer.is_nonterminal(key)
    return (' ' in key)

def is_base_key(key):
    return not is_refined_key(key)

def stem(token):
    return tsplit(token)[0].strip()

def normalize(token):
    assert fuzzer.is_nonterminal(token)
    if is_base_key(token): return token
    return '<%s>' % stem(token)

def refine_base_key(k, prefix):
    assert fuzzer.is_nonterminal(k)
    assert is_base_key(k)
    return '<%s %s>' % (stem(k), prefix)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def tsplit(token):
    assert token[0], token[-1] == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)
    front, *back = token[1:-1].split(None, 1)
    return front, &#x27; &#x27;.join(back)

def refinement(token):
    return tsplit(token)[1].strip()

def is_refined_key(key):
    assert fuzzer.is_nonterminal(key)
    return (&#x27; &#x27; in key)

def is_base_key(key):
    return not is_refined_key(key)

def stem(token):
    return tsplit(token)[0].strip()

def normalize(token):
    assert fuzzer.is_nonterminal(token)
    if is_base_key(token): return token
    return &#x27;&lt;%s&gt;&#x27; % stem(token)

def refine_base_key(k, prefix):
    assert fuzzer.is_nonterminal(k)
    assert is_base_key(k)
    return &#x27;&lt;%s %s&gt;&#x27; % (stem(k), prefix)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Defining the `reachable_key()`

<!--
############
def reachable_key(grammar, key, cnodesym, suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # skip this rule because we can not embed the fault here.
            continue
        else:
            # at each position, insert the cnodesym
            for pos in positions:
                new_rule = [refine_base_key(t, suffix)
                            if pos == p else t for p,t in enumerate(rule)]
                my_rules.append(new_rule)
    return (refine_base_key(key, suffix), my_rules)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def reachable_key(grammar, key, cnodesym, suffix, reachable):
    rules = grammar[key]
    my_rules = []
    for rule in grammar[key]:
        positions = get_reachable_positions(rule, cnodesym, reachable)
        if not positions:
            # skip this rule because we can not embed the fault here.
            continue
        else:
            # at each position, insert the cnodesym
            for pos in positions:
                new_rule = [refine_base_key(t, suffix)
                            if pos == p else t for p,t in enumerate(rule)]
                my_rules.append(new_rule)
    return (refine_base_key(key, suffix), my_rules)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It is used as follows

<!--
############
for key in hdd.EXPR_GRAMMAR:
    fk, rules = reachable_key(hdd.EXPR_GRAMMAR, key, '<factor>', 'F1', reaching)
    print(fk)
    for r in rules:
        print('    ', r)
    print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for key in hdd.EXPR_GRAMMAR:
    fk, rules = reachable_key(hdd.EXPR_GRAMMAR, key, &#x27;&lt;factor&gt;&#x27;, &#x27;F1&#x27;, reaching)
    print(fk)
    for r in rules:
        print(&#x27;    &#x27;, r)
    print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Pattern Grammar
Next, we need to ensure that our evocative subtree can form a unique subtree.
For that, all we need to do is that all nodes in the subtree are named uniquely.
Not all nodes in the evocative subtree needs unique names however. DDSet
produces trees such that some nodes in the tree are left abstract. We leave
these with the original node names.

<!--
############
def mark_unique_name(symbol, suffix, i):
    return '<%s %s_%s>' % (symbol[1:-1], suffix, str(i))

def mark_unique_nodes(node, suffix, counter=None):
    if counter is None: counter = [0]
    symbol, children, *abstract = node
    if ddset.is_node_abstract(node): # we don't markup further
        return node
    if fuzzer.is_nonterminal(symbol):
        i = counter[0]
        counter[0] += 1
        cs = [mark_unique_nodes(c, suffix, counter) for c in children]
        return (mark_unique_name(symbol, suffix, i), cs, *abstract)
    else:
        assert not children
        return (symbol, children, *abstract)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def mark_unique_name(symbol, suffix, i):
    return &#x27;&lt;%s %s_%s&gt;&#x27; % (symbol[1:-1], suffix, str(i))

def mark_unique_nodes(node, suffix, counter=None):
    if counter is None: counter = [0]
    symbol, children, *abstract = node
    if ddset.is_node_abstract(node): # we don&#x27;t markup further
        return node
    if fuzzer.is_nonterminal(symbol):
        i = counter[0]
        counter[0] += 1
        cs = [mark_unique_nodes(c, suffix, counter) for c in children]
        return (mark_unique_name(symbol, suffix, i), cs, *abstract)
    else:
        assert not children
        return (symbol, children, *abstract)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
unique_pattern_tree = mark_unique_nodes(evocative_pattern, 'F1')
ddset.display_abstract_tree(unique_pattern_tree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
unique_pattern_tree = mark_unique_nodes(evocative_pattern, &#x27;F1&#x27;)
ddset.display_abstract_tree(unique_pattern_tree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can extract a unique pattern grammar from this tree.

<!--
############
def unique_cnode_to_grammar(tree, grammar=None):
    if grammar is None: grammar = {}
    if ddset.is_node_abstract(tree): return grammar, normalize(tree[0])
    name, children, *rest = tree
    tokens = []
    if name not in grammar: grammar[name] = []
    for c in children:
        n, cs, *rest = c
        tokens.append(n)
        if fuzzer.is_nonterminal(n):
            unique_cnode_to_grammar(c, grammar)
    grammar[name].append(tokens)
    return grammar, tree[0]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def unique_cnode_to_grammar(tree, grammar=None):
    if grammar is None: grammar = {}
    if ddset.is_node_abstract(tree): return grammar, normalize(tree[0])
    name, children, *rest = tree
    tokens = []
    if name not in grammar: grammar[name] = []
    for c in children:
        n, cs, *rest = c
        tokens.append(n)
        if fuzzer.is_nonterminal(n):
            unique_cnode_to_grammar(c, grammar)
    grammar[name].append(tokens)
    return grammar, tree[0]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can convert this to grammar, but first, to display the grammar properly, we
define `display_grammar()`

<!--
############
class DisplayGrammar:
    def __init__(self, grammar, verbose=0):
        self.grammar = grammar
        self.verbose = verbose

    def is_nonterminal(self, key):
        return fuzzer.is_nonterminal(key)

    def display_token(self, t):
        return t if self.is_nonterminal(t) else repr(t)

    def display_rule(self, rule, pre):
        if self.verbose > -2:
            v = (' '.join([self.display_token(t) for t in rule]))
            s = '%s|   %s' % (pre, v)
            print(s)

    def display_definition(self, key, rule_count):
        if self.verbose > -2: print(key,'::=')
        for rule in self.grammar[key]:
            rule_count += 1
            if self.verbose > 1:
                pre = rule_count
            else:
                pre = ''
            self.display_rule(rule, pre)
        return rule_count

    def recurse_grammar(self, grammar, key, order, undefined=None):
        undefined = undefined or {}
        rules = sorted(grammar[key])
        old_len = len(order)
        for rule in rules:
            for token in rule:
                if not self.is_nonterminal(token): continue
                if token not in grammar:
                    if token in undefined:
                        undefined[token].append(key)
                    else:
                        undefined[token] = [key]
                    continue
                if token not in order:
                    order.append(token)
        new = order[old_len:]
        for ckey in new:
            self.recurse_grammar(grammar, ckey, order, undefined)
        return undefined


    def sort_grammar(self, grammar, start_symbol):
        order = [start_symbol]
        undefined = self.recurse_grammar(grammar, start_symbol, order)
        return order, [k for k in self.grammar if k not in order], undefined

    def display_unused(self, not_used, r):
        if not_used and self.verbose > -1:
            print('[not_used]')
            for key in not_used:
                r = self.display_definition(key, r)
                if self.verbose > 0:
                    print(k, r)

    def display_undefined(self, undefined):
        if undefined and self.verbose > -1:
            print('[undefined keys]')
            for key in undefined:
                if self.verbose == 0:
                    print(key)
                else:
                    print(key, 'defined in')
                    for k in undefined[key]: print(' ', k)

    def display_summary(self, k, r):
        if self.verbose > -1:
            print('keys:', k, 'rules:', r)

    def display(self, start):
        rule_count, key_count = 0, 0
        order, not_used, undefined = self.sort_grammar(self.grammar, start)
        print('[start]:', start)
        for key in order:
            key_count += 1
            rule_count = self.display_definition(key, rule_count)
            if self.verbose > 0:
                print(key_count, rule_count)

        self.display_unused(not_used, rule_count)
        self.display_undefined(undefined)
        self.display_summary(key_count, rule_count)


def display_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)

if __name__ == '__main__':
    g,s = unique_cnode_to_grammar(unique_pattern_tree)
    display_grammar(g,s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DisplayGrammar:
    def __init__(self, grammar, verbose=0):
        self.grammar = grammar
        self.verbose = verbose

    def is_nonterminal(self, key):
        return fuzzer.is_nonterminal(key)

    def display_token(self, t):
        return t if self.is_nonterminal(t) else repr(t)

    def display_rule(self, rule, pre):
        if self.verbose &gt; -2:
            v = (&#x27; &#x27;.join([self.display_token(t) for t in rule]))
            s = &#x27;%s|   %s&#x27; % (pre, v)
            print(s)

    def display_definition(self, key, rule_count):
        if self.verbose &gt; -2: print(key,&#x27;::=&#x27;)
        for rule in self.grammar[key]:
            rule_count += 1
            if self.verbose &gt; 1:
                pre = rule_count
            else:
                pre = &#x27;&#x27;
            self.display_rule(rule, pre)
        return rule_count

    def recurse_grammar(self, grammar, key, order, undefined=None):
        undefined = undefined or {}
        rules = sorted(grammar[key])
        old_len = len(order)
        for rule in rules:
            for token in rule:
                if not self.is_nonterminal(token): continue
                if token not in grammar:
                    if token in undefined:
                        undefined[token].append(key)
                    else:
                        undefined[token] = [key]
                    continue
                if token not in order:
                    order.append(token)
        new = order[old_len:]
        for ckey in new:
            self.recurse_grammar(grammar, ckey, order, undefined)
        return undefined


    def sort_grammar(self, grammar, start_symbol):
        order = [start_symbol]
        undefined = self.recurse_grammar(grammar, start_symbol, order)
        return order, [k for k in self.grammar if k not in order], undefined

    def display_unused(self, not_used, r):
        if not_used and self.verbose &gt; -1:
            print(&#x27;[not_used]&#x27;)
            for key in not_used:
                r = self.display_definition(key, r)
                if self.verbose &gt; 0:
                    print(k, r)

    def display_undefined(self, undefined):
        if undefined and self.verbose &gt; -1:
            print(&#x27;[undefined keys]&#x27;)
            for key in undefined:
                if self.verbose == 0:
                    print(key)
                else:
                    print(key, &#x27;defined in&#x27;)
                    for k in undefined[key]: print(&#x27; &#x27;, k)

    def display_summary(self, k, r):
        if self.verbose &gt; -1:
            print(&#x27;keys:&#x27;, k, &#x27;rules:&#x27;, r)

    def display(self, start):
        rule_count, key_count = 0, 0
        order, not_used, undefined = self.sort_grammar(self.grammar, start)
        print(&#x27;[start]:&#x27;, start)
        for key in order:
            key_count += 1
            rule_count = self.display_definition(key, rule_count)
            if self.verbose &gt; 0:
                print(key_count, rule_count)

        self.display_unused(not_used, rule_count)
        self.display_undefined(undefined)
        self.display_summary(key_count, rule_count)


def display_grammar(grammar, start, verbose=0):
    DisplayGrammar(grammar, verbose).display(start)

if __name__ == &#x27;__main__&#x27;:
    g,s = unique_cnode_to_grammar(unique_pattern_tree)
    display_grammar(g,s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define `pattern_grammar()` that wraps both calls.

<!--
############
def pattern_grammar(cnode, fname):
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    return pattern_g, pattern_s, unique_pattern_tree

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def pattern_grammar(cnode, fname):
    unique_pattern_tree = mark_unique_nodes(cnode, fname)
    pattern_g, pattern_s = unique_cnode_to_grammar(unique_pattern_tree)
    return pattern_g, pattern_s, unique_pattern_tree
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
pattern_g,pattern_s, t = pattern_grammar(evocative_pattern, 'F1')
display_grammar(pattern_g, pattern_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
pattern_g,pattern_s, t = pattern_grammar(evocative_pattern, &#x27;F1&#x27;)
display_grammar(pattern_g, pattern_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We define a procedure to reverse our pattern grammar to ensure we can
get back our tree.

<!--
############
def pattern_grammar_to_tree(g, s):
    rules = g[s]
    assert len(rules) == 1
    return (s, [pattern_grammar_to_tree(g,t) if t in g else (t, []) for t in rules[0]])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def pattern_grammar_to_tree(g, s):
    rules = g[s]
    assert len(rules) == 1
    return (s, [pattern_grammar_to_tree(g,t) if t in g else (t, []) for t in rules[0]])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The tree can be recovered thus.

<!--
############
c_tree = pattern_grammar_to_tree(pattern_g,pattern_s)
fuzzer.display_tree(c_tree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
c_tree = pattern_grammar_to_tree(pattern_g,pattern_s)
fuzzer.display_tree(c_tree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given the reaching grammar and the pattern grammar, we can combine them to
produce the complete grammar

<!--
############
def reachable_grammar(grammar, start, cnodesym, suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = reachable_key(grammar, key, cnodesym, suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def reachable_grammar(grammar, start, cnodesym, suffix, reachable):
    new_grammar = {}
    s_key = None
    for key in grammar:
        fk, rules = reachable_key(grammar, key, cnodesym, suffix, reachable)
        assert fk not in new_grammar
        if key == start: s_key = fk
        new_grammar[fk] = rules
    return new_grammar, s_key
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
evocative_subtree = evocative_pattern[1][0][1][0][1][0]
my_key_f = evocative_subtree[0]
reaching = reachable_dict(hdd.EXPR_GRAMMAR)
reach_g, reach_s = reachable_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, my_key_f, 'F1', reaching)
display_grammar(reach_g, reach_s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
evocative_subtree = evocative_pattern[1][0][1][0][1][0]
my_key_f = evocative_subtree[0]
reaching = reachable_dict(hdd.EXPR_GRAMMAR)
reach_g, reach_s = reachable_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, my_key_f, &#x27;F1&#x27;, reaching)
display_grammar(reach_g, reach_s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here, you will notice a problem:
There are a few nonterminals such as `<integer F1>` that do not have a
definition. That is, it has no expansion (not even empty expansion). So,
any rule that uses it will also by definition have no possible expansions.
This has consequences during generation, forcing us to abandon partially
constructed trees. Hence, we define a `grammar_gc()`
## Cleanup of the grammar
Let us make sure that we are operating on a copy of the grammar.

<!--
############
def copy_grammar(g):
    return {k:[[t for t in r] for r in g[k]] for k in g}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def copy_grammar(g):
    return {k:[[t for t in r] for r in g[k]] for k in g}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we find the empty keys in the grammar that do not have a definition.

<!--
############
def find_empty_keys(g):
    return [k for k in g if not g[k]]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_empty_keys(g):
    return [k for k in g if not g[k]]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we need to remove such empty definitions, which also means any rules that
refer to the corresponding nonterminals also have to be removed. The
`remove_nonterminal` function takes a nonterminal, and removes its references
from the given grammar.

<!--
############
def remove_nonterminal(nt, g):
    new_g = {}
    for k_ in g:
        if k_ == nt: continue
        new_rules = []
        for rule in g[k_]:
            if any(t == nt for t in rule): continue
            new_rules.append(rule)
        new_g[k_] = new_rules
    return new_g

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def remove_nonterminal(nt, g):
    new_g = {}
    for k_ in g:
        if k_ == nt: continue
        new_rules = []
        for rule in g[k_]:
            if any(t == nt for t in rule): continue
            new_rules.append(rule)
        new_g[k_] = new_rules
    return new_g
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
When removing a rule, it can also happen that the corresponding nonterminal
may be left with no further rules. Hence, we need to
define finding and removing empty nonterminals from the grammar recursively.

<!--
############
def remove_empty_nonterminals(g):
    new_g = copy_grammar(g)
    removed_keys = []
    empty_keys = find_empty_keys(new_g)
    while empty_keys:
        for k in empty_keys:
            removed_keys.append(k)
            new_g = remove_nonterminal(k, new_g)
        empty_keys = find_empty_keys(new_g)
    return new_g, removed_keys

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def remove_empty_nonterminals(g):
    new_g = copy_grammar(g)
    removed_keys = []
    empty_keys = find_empty_keys(new_g)
    while empty_keys:
        for k in empty_keys:
            removed_keys.append(k)
            new_g = remove_nonterminal(k, new_g)
        empty_keys = find_empty_keys(new_g)
    return new_g, removed_keys
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
These gives us the `grammar_gc()`

<!--
############
def grammar_gc(g):
    grammar, start = g
    new_grammar, removed = remove_empty_nonterminals(grammar)
    return new_grammar, start

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def grammar_gc(g):
    grammar, start = g
    new_grammar, removed = remove_empty_nonterminals(grammar)
    return new_grammar, start
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point we are ready to define our `atleast_one_fault_grammar()`

<!--
############
def atleast_one_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, t = pattern_grammar(cnode, fname)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = refine_base_key(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return combined_grammar, reach_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def atleast_one_fault_grammar(grammar, start_symbol, cnode, fname):
    key_f = cnode[0]
    pattern_g, pattern_s, t = pattern_grammar(cnode, fname)

    reachable_keys = reachable_dict(grammar)
    reach_g, reach_s = reachable_grammar(grammar, start_symbol, key_f, fname, reachable_keys)

    combined_grammar = {**grammar, **pattern_g, **reach_g}
    reaching_sym = refine_base_key(key_f, fname)
    combined_grammar[reaching_sym] = reach_g[reaching_sym] + pattern_g[pattern_s]

    return combined_grammar, reach_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The new grammar is as follows

<!--
############
g, s = grammar_gc(atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, evocative_subtree, 'F1'))
display_grammar(g, s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g, s = grammar_gc(atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, evocative_subtree, &#x27;F1&#x27;))
display_grammar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed to produce at least one instance of the characterizing node.

<!--
############
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    assert hdd.expr_double_paren(v)
    print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = gf.iter_fuzz(key=s, max_depth=10)
    assert hdd.expr_double_paren(v)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This seems to work. However, there is a wrinkle. Note that we set the
evocative subtree as this subtree `pattern[1][0][1][0][1][0]`, which is a
`<factor>` node. But why not any of the other subtrees? for example, why not
`evocative_pattern` itself? Indeed, the effectiveness of
our specialized grammar is dependent on finding as small a evocative subtree
as possible that fully captures the fault. So, how do we automate it?
The idea is fairly simple. We start from the root of the evocative pattern.
We know that this pattern fully captures the predicate. That is, any valid input
generated from this pattern by filling in the abstract nodes is (statistically)
guaranteed to produce the failure. Next, we move to the children of this node.
If the node is abstract, we return immediately. If however, the child is not
abstract, we let the child be the evocative subtree, and try to reproduce the
failure. If the failure is not reproduced, we move to the next child. If the
failure is reproduced we recurse deeper into the current child.

<!--
############
def find_evocative_subtree(fault_tree, grammar, start, fn):
    if ddset.is_node_abstract(fault_tree): return None
    if not fuzzer.is_nonterminal(fault_tree[0]): return None
    g, s = grammar_gc(atleast_one_fault_grammar(grammar, start, fault_tree, 'F1'))
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        string = gf.iter_fuzz(key=s, max_depth=10)
        rval = fn(string)
        if rval == hdd.PRes.failed:
            return None
        elif rval == hdd.PRes.invalid:
            continue
        else:
            continue

    node, children, rest = fault_tree
    for c in children:
        v = find_evocative_subtree(c, grammar, start, fn)
        if v is not None:
            return v
    return fault_tree


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def find_evocative_subtree(fault_tree, grammar, start, fn):
    if ddset.is_node_abstract(fault_tree): return None
    if not fuzzer.is_nonterminal(fault_tree[0]): return None
    g, s = grammar_gc(atleast_one_fault_grammar(grammar, start, fault_tree, &#x27;F1&#x27;))
    gf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        string = gf.iter_fuzz(key=s, max_depth=10)
        rval = fn(string)
        if rval == hdd.PRes.failed:
            return None
        elif rval == hdd.PRes.invalid:
            continue
        else:
            continue

    node, children, rest = fault_tree
    for c in children:
        v = find_evocative_subtree(c, grammar, start, fn)
        if v is not None:
            return v
    return fault_tree
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Usage

<!--
############
etree = find_evocative_subtree(evocative_pattern, hdd.EXPR_GRAMMAR, hdd.EXPR_START, hdd.expr_double_paren)
ddset.display_abstract_tree(etree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
etree = find_evocative_subtree(evocative_pattern, hdd.EXPR_GRAMMAR, hdd.EXPR_START, hdd.expr_double_paren)
ddset.display_abstract_tree(etree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, we found the correct evocative subtree. We can confirm this by
comparing it against the subtree we identified manually.

<!--
############
ddset.display_abstract_tree(evocative_subtree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ddset.display_abstract_tree(evocative_subtree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We save this subtree for later use.

<!--
############
ETREE_DPAREN = ('<factor>',
        [('(', [], {'abstract': False}),
         ('<expr>',
             [('<term>',
                 [('<factor>',
                     [('(', [], {'abstract': False}),
                      ('<expr>', [('<term>',
                          [('<factor>',
                              [('<integer>',
                                  [('<digit>',
                                      [('4', [],
                                          {'abstract': False})],
                                      {'abstract': False})],
                                  {'abstract': False})],
                              {'abstract': False})],
                          {'abstract': False})],
                          {'abstract': True}),
                      (')', [],
                          {'abstract': False})],
                      {'abstract': False})],
                 {'abstract': False})],
             {'abstract': False}),
         (')', [], {'abstract': False})], {'abstract': False})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ETREE_DPAREN = (&#x27;&lt;factor&gt;&#x27;,
        [(&#x27;(&#x27;, [], {&#x27;abstract&#x27;: False}),
         (&#x27;&lt;expr&gt;&#x27;,
             [(&#x27;&lt;term&gt;&#x27;,
                 [(&#x27;&lt;factor&gt;&#x27;,
                     [(&#x27;(&#x27;, [], {&#x27;abstract&#x27;: False}),
                      (&#x27;&lt;expr&gt;&#x27;, [(&#x27;&lt;term&gt;&#x27;,
                          [(&#x27;&lt;factor&gt;&#x27;,
                              [(&#x27;&lt;integer&gt;&#x27;,
                                  [(&#x27;&lt;digit&gt;&#x27;,
                                      [(&#x27;4&#x27;, [],
                                          {&#x27;abstract&#x27;: False})],
                                      {&#x27;abstract&#x27;: False})],
                                  {&#x27;abstract&#x27;: False})],
                              {&#x27;abstract&#x27;: False})],
                          {&#x27;abstract&#x27;: False})],
                          {&#x27;abstract&#x27;: True}),
                      (&#x27;)&#x27;, [],
                          {&#x27;abstract&#x27;: False})],
                      {&#x27;abstract&#x27;: False})],
                 {&#x27;abstract&#x27;: False})],
             {&#x27;abstract&#x27;: False}),
         (&#x27;)&#x27;, [], {&#x27;abstract&#x27;: False})], {&#x27;abstract&#x27;: False})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is another evocative pattern, but we define a different predicate.

<!--
############
def expr_div_by_zero(input_str):
    if '/0)' in input_str: return hdd.PRes.success
    else: return hdd.PRes.failed

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def expr_div_by_zero(input_str):
    if &#x27;/0)&#x27; in input_str: return hdd.PRes.success
    else: return hdd.PRes.failed
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Check the assertion

<!--
############
my_input2 = '1+((2*3)/0)'
assert expr_div_by_zero(my_input2) == hdd.PRes.success

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_input2 = &#x27;1+((2*3)/0)&#x27;
assert expr_div_by_zero(my_input2) == hdd.PRes.success
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We first parse the input as before

<!--
############
parsed_expr2 = list(expr_parser.parse_on(my_input2, hdd.EXPR_START))[0]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
parsed_expr2 = list(expr_parser.parse_on(my_input2, hdd.EXPR_START))[0]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Then reduce input

<!--
############
reduced_expr_tree2 = hdd.perses_reduction(parsed_expr2, hdd.EXPR_GRAMMAR, expr_div_by_zero)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
reduced_expr_tree2 = hdd.perses_reduction(parsed_expr2, hdd.EXPR_GRAMMAR, expr_div_by_zero)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, extract the evocative pattern.

<!--
############
evocative_pattern2 = ddset.ddset_abstract(reduced_expr_tree2, hdd.EXPR_GRAMMAR, expr_div_by_zero)
ddset.display_abstract_tree(evocative_pattern2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
evocative_pattern2 = ddset.ddset_abstract(reduced_expr_tree2, hdd.EXPR_GRAMMAR, expr_div_by_zero)
ddset.display_abstract_tree(evocative_pattern2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Then extract the evocative subtree

<!--
############
etree2 = find_evocative_subtree(evocative_pattern2, hdd.EXPR_GRAMMAR, hdd.EXPR_START, expr_div_by_zero)
ddset.display_abstract_tree(etree2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
etree2 = find_evocative_subtree(evocative_pattern2, hdd.EXPR_GRAMMAR, hdd.EXPR_START, expr_div_by_zero)
ddset.display_abstract_tree(etree2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
prettyprinting

<!--
############
import pprint
def display_var(v):
    pp = pprint.PrettyPrinter(indent=1)
    pp.pprint(v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pprint
def display_var(v):
    pp = pprint.PrettyPrinter(indent=1)
    pp.pprint(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
using

<!--
############
display_var(etree2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
display_var(etree2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We save this evocative pattern for later use.

<!--
############
ETREE_DZERO = ('<term>',
 [('<factor>',
   [('<integer>',
     [('<digit>', [('2', [], {'abstract': False})], {'abstract': False})],
     {'abstract': False})],
   {'abstract': True}),
  ('/', [], {'abstract': False}),
  ('<term>',
   [('<factor>',
     [('<integer>',
       [('<digit>', [('0', [], {'abstract': False})], {'abstract': False})],
       {'abstract': False})],
     {'abstract': False})],
   {'abstract': False})],
 {'abstract': False})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ETREE_DZERO = (&#x27;&lt;term&gt;&#x27;,
 [(&#x27;&lt;factor&gt;&#x27;,
   [(&#x27;&lt;integer&gt;&#x27;,
     [(&#x27;&lt;digit&gt;&#x27;, [(&#x27;2&#x27;, [], {&#x27;abstract&#x27;: False})], {&#x27;abstract&#x27;: False})],
     {&#x27;abstract&#x27;: False})],
   {&#x27;abstract&#x27;: True}),
  (&#x27;/&#x27;, [], {&#x27;abstract&#x27;: False}),
  (&#x27;&lt;term&gt;&#x27;,
   [(&#x27;&lt;factor&gt;&#x27;,
     [(&#x27;&lt;integer&gt;&#x27;,
       [(&#x27;&lt;digit&gt;&#x27;, [(&#x27;0&#x27;, [], {&#x27;abstract&#x27;: False})], {&#x27;abstract&#x27;: False})],
       {&#x27;abstract&#x27;: False})],
     {&#x27;abstract&#x27;: False})],
   {&#x27;abstract&#x27;: False})],
 {&#x27;abstract&#x27;: False})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The new grammar is as follows

<!--
############
g2, s2 = grammar_gc(atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, etree2, 'F2'))
display_grammar(g2, s2)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2, s2 = grammar_gc(atleast_one_fault_grammar(hdd.EXPR_GRAMMAR, hdd.EXPR_START, etree2, &#x27;F2&#x27;))
display_grammar(g2, s2)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This grammar is now guaranteed to produce at least one instance of a divide by zero.

<!--
############
gf2 = fuzzer.LimitFuzzer(g2)
for i in range(10):
    v = gf2.iter_fuzz(key=s2, max_depth=10)
    assert expr_div_by_zero(v)
    print(v)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gf2 = fuzzer.LimitFuzzer(g2)
for i in range(10):
    v = gf2.iter_fuzz(key=s2, max_depth=10)
    assert expr_div_by_zero(v)
    print(v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we have the ability to guarantee that a evocative 
fragment is present in any inputs produced. In later posts I will discuss how
combine multiple such fragments together using `and`, `or` or `negation`. I
will also discuss how to ensure `at most` one fragment in the input and
`exactly` one fragment or `exactly n` fragments.
As before, the runnable source of this notebook can be found [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-09-fault-inducing-grammar.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
