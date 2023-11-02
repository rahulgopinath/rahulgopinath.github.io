---
published: true
title: Minimizing a Deterministic Regular Grammar or a DFA
layout: post
comments: true
tags: parsing
categories: post
---
A [deterministic regular grammar](/post/2021/10/24/canonical-regular-grammar/)
is a DFA (Deterministic Finite Automaton) represented as a regular grammar.
Such a grammar can have rules of the following format:
* $$ A \rightarrow a B $$
* $$ S \rightarrow E $$
* $$ E \rightarrow \epsilon $$

where given a nonterminal $$A$$ and a terminal symbol $$ a $$ at most one of
its rules will start with a terminal symbol $$ a $$.
Secondly, the $$ \epsilon $$ is attached to the $$ E $$ symbol, which is the
only termination point. If the language contains $$ \epsilon $$, then the
single degenerate rule, $$ S \rightarrow E $$ is added to the rules.
As you can see, each node has at most one
transition for a given terminal symbol. Hence, this canonical form is
equivalent to a deterministic finite state automation (**DFA**).

A deterministic regular grammar (also a DFA) is useful in many applications.
However, in most applications where a such a grammar can be used
(i.e., parsing and fuzzing) the performance of algorithms can be improved much
further by minimizing the grammar such that it has the smallest size possible
for the language it represents. This post tackles how to minimize a DFA using
the Hopcroft algorithm [^:hopcroft1971].

We start with importing the prerequisites

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

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
<li><a href="https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl">gatleastsinglefault-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/09/09/fault-inducing-grammar/">Specializing Context-Free Grammars for Inducing Faults</a>".</li>
<li><a href="https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl">rxfuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2021/10/22/fuzzing-with-regular-expressions/">iFuzzing With Regular Expressions</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/rxfuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>
The imported modules

<!--
############
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxfuzzer


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import rxfuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Minimization of the Regular Grammar

We assume that we have a DFA that is represented as a grammar where the
states in the DFA are nonterminal symbols in the grammar and terminals are
the transitions. However, this DFA is not necessarily minimal. That is,
thre could be duplicate nonterminal symbols that could behave exactly alike.
That is, if we take two such states as start symbols of the grammar, then
the strings accepted by such an grammars would be exactly the same. So, the
idea behind minimizing a regular grammar is to identify nonterminals that are
duplicates of each other
 
Interestingly, Brzozowski [:^brzozowski1963] observed that if you reverse the
arrows in the DFA, resulting in an NFA, and then convert the NFA to DFA, then
do this again, the resulting DFA is minimal. However, this can have
exponential worst case complexity (but can be much faster in common patterns).
Hence, we look at a more common algorithm for minimization.
The Hopcroft algorithm [:^hopcroft1971]  is based on partition refinement.

The idea is as follows:
1. Mark the start state and all final states
2. Collect all pairs of nonterminals from the grammar
2. while there are pairs to be marked 
   a. for each nonmarked pairs p,q do
      i. for each symbol a in alphabet do 
         * if the pair delta(p, a) and delta(q, a) is marked, mark p,q
3. Construct the reduced grammar by merging unmarked groups of pairs.
We start with a matrix nonterminals, and iteratively refine them. We start by
initializing our data structure.

<!--
############
class DRGMinimize:
    def __init__(self, g, s, alphabet=None):
        self.grammar, self.start = g, s
        self.final = self.final_states()
        if alphabet is None:
            self.alphabet = self.get_alphabet()
        else:
            self.alphabet = alphabet
        self.init_pairs()

    def final_states(self):
        return {key:None
                for key in self.grammar
                for rule in self.grammar[key]
                if not rule}

    def get_alphabet(self):
        return {t:None
                for k in self.grammar
                for rule in self.grammar[k]
                for t in rule
                     if not fuzzer.is_nonterminal(t)}

    def init_pairs(self):
        self.pairs = {}
        for k in self.grammar:
            for l in self.grammar:
                if k == l: continue
                x = tuple(sorted([k,l]))
                if x in self.pairs: continue
                if k in self.final:
                    if l in self.final:
                        self.pairs[x] = None
                    else:
                        self.pairs[x] = '' # Distinguished
                else:
                    if l in self.final:
                        self.pairs[x] = '' # Distinguished
                    else:
                        self.pairs[x] = None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DRGMinimize:
    def __init__(self, g, s, alphabet=None):
        self.grammar, self.start = g, s
        self.final = self.final_states()
        if alphabet is None:
            self.alphabet = self.get_alphabet()
        else:
            self.alphabet = alphabet
        self.init_pairs()

    def final_states(self):
        return {key:None
                for key in self.grammar
                for rule in self.grammar[key]
                if not rule}

    def get_alphabet(self):
        return {t:None
                for k in self.grammar
                for rule in self.grammar[k]
                for t in rule
                     if not fuzzer.is_nonterminal(t)}

    def init_pairs(self):
        self.pairs = {}
        for k in self.grammar:
            for l in self.grammar:
                if k == l: continue
                x = tuple(sorted([k,l]))
                if x in self.pairs: continue
                if k in self.final:
                    if l in self.final:
                        self.pairs[x] = None
                    else:
                        self.pairs[x] = &#x27;&#x27; # Distinguished
                else:
                    if l in self.final:
                        self.pairs[x] = &#x27;&#x27; # Distinguished
                    else:
                        self.pairs[x] = None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we want to update the markings. To improve the performance, we define
a datastruture to keep the transitions from states.

<!--
############
class DRGMinimize(DRGMinimize):
    def _transitions(self):
        transitions = {}
        for k in self.grammar:
            transitions[k] = {a:None for a in self.alphabet}
            for r in self.grammar[k]:
                if not r or len(r) != 2: continue
                transitions[k][r[0]] = r[1]
        return transitions

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DRGMinimize(DRGMinimize):
    def _transitions(self):
        transitions = {}
        for k in self.grammar:
            transitions[k] = {a:None for a in self.alphabet}
            for r in self.grammar[k]:
                if not r or len(r) != 2: continue
                transitions[k][r[0]] = r[1]
        return transitions
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We are now ready to update our markings.

<!--
############
class DRGMinimize(DRGMinimize):
    def get_key(self, a, b): return tuple(sorted([a, b]))

    def update_markings(self):
        transitions  = self._transitions()
        while True:
            found_new_marks = False
            unmarked_pairs = [p for p in self.pairs if self.pairs[p] is None]
            for (ka,kb) in unmarked_pairs:
                dA, dB = transitions[ka], transitions[kb]
                for alpha in self.alphabet:
                    delta_key_pair = self.get_key(dA[alpha], dB[alpha])
                    # is delta pair marked? if so, we can mark the original pair
                    if self.pairs.get(delta_key_pair) is None: continue
                    self.pairs[(ka, kb)] = alpha
                    found_new_marks = True
                    break
            if not found_new_marks: break

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DRGMinimize(DRGMinimize):
    def get_key(self, a, b): return tuple(sorted([a, b]))

    def update_markings(self):
        transitions  = self._transitions()
        while True:
            found_new_marks = False
            unmarked_pairs = [p for p in self.pairs if self.pairs[p] is None]
            for (ka,kb) in unmarked_pairs:
                dA, dB = transitions[ka], transitions[kb]
                for alpha in self.alphabet:
                    delta_key_pair = self.get_key(dA[alpha], dB[alpha])
                    # is delta pair marked? if so, we can mark the original pair
                    if self.pairs.get(delta_key_pair) is None: continue
                    self.pairs[(ka, kb)] = alpha
                    found_new_marks = True
                    break
            if not found_new_marks: break
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g = {
        '<A>' : [['a', '<B>'],
                 ['b', '<D>']],
        '<B>' : [['b', '<E>'],
                 ['a', '<C>']],
        '<C>' : [
            ['a', '<B>'],
            ['b', '<E>'],
            []],
        '<D>' : [['b', '<E>'],
                 ['a', '<C>']],
        '<E>' : [
            ['a', '<E>'],
            ['b', '<E>'],
            []],
        }
s = '<A>'
m = DRGMinimize(g, s)
m.update_markings()
for (a,b) in m.pairs:
    print(a,b, m.pairs[(a,b)])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = {
        &#x27;&lt;A&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
                 [&#x27;b&#x27;, &#x27;&lt;D&gt;&#x27;]],
        &#x27;&lt;B&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
                 [&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;]],
        &#x27;&lt;C&gt;&#x27; : [
            [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
            [&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
            []],
        &#x27;&lt;D&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
                 [&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;]],
        &#x27;&lt;E&gt;&#x27; : [
            [&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;],
            [&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
            []],
        }
s = &#x27;&lt;A&gt;&#x27;
m = DRGMinimize(g, s)
m.update_markings()
for (a,b) in m.pairs:
    print(a,b, m.pairs[(a,b)])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, all that remains to be done is to merge the nonterminals in the
pairs which are indistinguished. That is, the value is `None`.

<!--
############
class DRGMinimize(DRGMinimize):
    def to_name(self, k, indistinguished):
        if k not in indistinguished: return k
        ik_ = sorted(set(indistinguished[k]))
        return '<(%s)>' % '|'.join([a[1:-1] for a in ik_])

    def minimized_grammar(self):
        self.update_markings()
        partitions = {}
        unmarked_pairs = [p for p in self.pairs if self.pairs[p] is None]
        for (ka, kb) in unmarked_pairs:
            if ka not in partitions: partitions[ka] = []
            partitions[ka].extend([ka, kb])
            if kb not in partitions: partitions[kb] = []
            partitions[kb].extend([ka, kb])

        new_g = {}
        for k in self.grammar:
            ik = self.to_name(k, partitions)
            if ik not in new_g: new_g[ik] = []
            new_rules = new_g[ik]

            for r in self.grammar[k]:
                new_r = [self.to_name(t, partitions) for t in r]
                if new_r not in new_rules: new_rules.append(new_r)

        new_s = self.to_name(self.start, partitions)
        return new_g, new_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class DRGMinimize(DRGMinimize):
    def to_name(self, k, indistinguished):
        if k not in indistinguished: return k
        ik_ = sorted(set(indistinguished[k]))
        return &#x27;&lt;(%s)&gt;&#x27; % &#x27;|&#x27;.join([a[1:-1] for a in ik_])

    def minimized_grammar(self):
        self.update_markings()
        partitions = {}
        unmarked_pairs = [p for p in self.pairs if self.pairs[p] is None]
        for (ka, kb) in unmarked_pairs:
            if ka not in partitions: partitions[ka] = []
            partitions[ka].extend([ka, kb])
            if kb not in partitions: partitions[kb] = []
            partitions[kb].extend([ka, kb])

        new_g = {}
        for k in self.grammar:
            ik = self.to_name(k, partitions)
            if ik not in new_g: new_g[ik] = []
            new_rules = new_g[ik]

            for r in self.grammar[k]:
                new_r = [self.to_name(t, partitions) for t in r]
                if new_r not in new_rules: new_rules.append(new_r)

        new_s = self.to_name(self.start, partitions)
        return new_g, new_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
g = {
        '<A>' : [['a', '<B>'],
                 ['b', '<D>']],
        '<B>' : [['b', '<E>'],
                 ['a', '<C>']],
        '<C>' : [
            ['a', '<B>'],
            ['b', '<E>'],
            []],
        '<D>' : [['b', '<E>'],
                 ['a', '<C>']],
        '<E>' : [
            ['a', '<E>'],
            ['b', '<E>'],
            []],
        }
s = '<A>'
m = DRGMinimize(g, s)
newg, news = m.minimized_grammar()
gatleast.display_grammar(newg, news)

print()
g = {
        '<a>': [['0', '<b>'], ['1', '<c>']],
        '<b>': [['1', '<d>'], ['0', '<a>']],
        '<c>': [['1', '<f>'], ['0', '<e>'], []],
        '<d>': [['1', '<f>'], ['0', '<e>'], []],
        '<e>': [['1', '<f>'], ['0', '<e>'], []],
        '<f>': [['1', '<f>'], ['0', '<f>']],
        }
s = '<a>'
m = DRGMinimize(g, s)
g1, s1 = m.minimized_grammar()
gatleast.display_grammar(g1, s1)

print()
g = {
        '<A>' : [['a', '<C>'], ['b', '<B>']],
        '<B>' : [['a', '<A>'], ['b', '<C>']],
        '<C>' : [['a', '<A>'], ['b', '<D>']],
        '<D>' : [['a', '<E>'], ['b', '<H>']],
        '<E>' : [['a', '<E>'], ['b', '<F>']],
        '<F>' : [['a', '<E>'], ['b', '<G>']],
        '<G>' : [['a', '<E>'], ['b', '<H>']],
        '<H>' : [['a', '<I>'], ['b', '<L>']],
        '<I>' : [['a', '<I>'], ['b', '<J>']],
        '<J>' : [['a', '<I>'], ['b', '<K>']],
        '<K>' : [['a', '<I>'], ['b', '<L>']],
        '<L>' : [['a', '<L>'], ['b', '<L>'], []],
        }
s = '<A>'
m = DRGMinimize(g, s)
g1, s1 = m.minimized_grammar()
gatleast.display_grammar(g1, s1)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g = {
        &#x27;&lt;A&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
                 [&#x27;b&#x27;, &#x27;&lt;D&gt;&#x27;]],
        &#x27;&lt;B&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
                 [&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;]],
        &#x27;&lt;C&gt;&#x27; : [
            [&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;],
            [&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
            []],
        &#x27;&lt;D&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
                 [&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;]],
        &#x27;&lt;E&gt;&#x27; : [
            [&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;],
            [&#x27;b&#x27;, &#x27;&lt;E&gt;&#x27;],
            []],
        }
s = &#x27;&lt;A&gt;&#x27;
m = DRGMinimize(g, s)
newg, news = m.minimized_grammar()
gatleast.display_grammar(newg, news)

print()
g = {
        &#x27;&lt;a&gt;&#x27;: [[&#x27;0&#x27;, &#x27;&lt;b&gt;&#x27;], [&#x27;1&#x27;, &#x27;&lt;c&gt;&#x27;]],
        &#x27;&lt;b&gt;&#x27;: [[&#x27;1&#x27;, &#x27;&lt;d&gt;&#x27;], [&#x27;0&#x27;, &#x27;&lt;a&gt;&#x27;]],
        &#x27;&lt;c&gt;&#x27;: [[&#x27;1&#x27;, &#x27;&lt;f&gt;&#x27;], [&#x27;0&#x27;, &#x27;&lt;e&gt;&#x27;], []],
        &#x27;&lt;d&gt;&#x27;: [[&#x27;1&#x27;, &#x27;&lt;f&gt;&#x27;], [&#x27;0&#x27;, &#x27;&lt;e&gt;&#x27;], []],
        &#x27;&lt;e&gt;&#x27;: [[&#x27;1&#x27;, &#x27;&lt;f&gt;&#x27;], [&#x27;0&#x27;, &#x27;&lt;e&gt;&#x27;], []],
        &#x27;&lt;f&gt;&#x27;: [[&#x27;1&#x27;, &#x27;&lt;f&gt;&#x27;], [&#x27;0&#x27;, &#x27;&lt;f&gt;&#x27;]],
        }
s = &#x27;&lt;a&gt;&#x27;
m = DRGMinimize(g, s)
g1, s1 = m.minimized_grammar()
gatleast.display_grammar(g1, s1)

print()
g = {
        &#x27;&lt;A&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;C&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;B&gt;&#x27;]],
        &#x27;&lt;B&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;C&gt;&#x27;]],
        &#x27;&lt;C&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;D&gt;&#x27;]],
        &#x27;&lt;D&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;H&gt;&#x27;]],
        &#x27;&lt;E&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;F&gt;&#x27;]],
        &#x27;&lt;F&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;G&gt;&#x27;]],
        &#x27;&lt;G&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;E&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;H&gt;&#x27;]],
        &#x27;&lt;H&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;I&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;L&gt;&#x27;]],
        &#x27;&lt;I&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;I&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;J&gt;&#x27;]],
        &#x27;&lt;J&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;I&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;K&gt;&#x27;]],
        &#x27;&lt;K&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;I&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;L&gt;&#x27;]],
        &#x27;&lt;L&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;L&gt;&#x27;], [&#x27;b&#x27;, &#x27;&lt;L&gt;&#x27;], []],
        }
s = &#x27;&lt;A&gt;&#x27;
m = DRGMinimize(g, s)
g1, s1 = m.minimized_grammar()
gatleast.display_grammar(g1, s1)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
 
The runnable code for this post is available
[here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-02-minimizing-canonical-regular-grammar-dfa.py).

[^hopcroft1971:] John Hopcroft "An n log n algorithm for minimizing states in a finite automaton" 1971
[^brzozowski1963] "Canonical regular expressions and minimal state graphs for definite events" 1963


<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2023-11-02-minimizing-canonical-regular-grammar-dfa.py).


