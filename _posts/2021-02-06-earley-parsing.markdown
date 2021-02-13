---
published: true
title: Earley Parser
layout: post
comments: true
tags: parsing, context-free
categories: post
---

<script type="text/javascript">window.languagePluginUrl='https://cdn.jsdelivr.net/pyodide/v0.16.1/full/';</script>
<script src="https://cdn.jsdelivr.net/pyodide/v0.16.1/full/pyodide.js"></script>
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

The *Earley* parsing algorithm was invented by Jay Earley [^earley1970an] in 1970. It
can be used to parse strings that conform to a context-free grammar. The
algorithm uses a chart for parsing -- that is, it is implemented as a dynamic
program relying on solving simpler sub-problems.

Earley parsers are very appealing for a practitioner because they can use any
context-free grammar for parsing a string, and from the parse forest generated,
one can recover all (even an infinite number) of parse trees that correspond to
the given grammar. Unfortunately, this style of parsing pays for generality by
being slightly expensive. It takes $$O(n^3)$$ time to parse in the worst case.
However, if the grammar is unambiguous, it can parse in $$O(n^2)$$ time, and
all [LR(k)](https://en.wikipedia.org/wiki/LR_parser) grammars in linear time[^leo1991a].

This an implementation of Earley parsing that handles the epsilon case as
given by Aycock et al.[^aycock2002practical].

For a much more complete implementation including Leo's optimizations[^leo1991a], and
full recovery of parsing forests using iterative solutions,
see our parsing implementation in the [fuzzingbook](https://www.fuzzingbook.org/html/Parser.html)
(See the solved exercises). A very detailed explanation of Earley parsing is
by [Loup Vaillant](https://loup-vaillant.fr/tutorials/earley-parsing/).

As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
Here is an example grammar for arithmetic expressions, starting at `<start>`.
A terminal symbol has exactly one character
(Note that we disallow empty string (`''`) as a terminal symbol).
Secondly, as per traditional implementations,
there can only be one expansion rule for the `<start>` symbol. We work around
this restriction by simply constructing as many charts as there are expansion
rules, and returning all parse trees.

For this post, we use the following terms:

* The _alphabet_ is the set all of symbols in the input language
* A _terminal_ is a single alphabet symbol. Note that this is slightly different
  from usual definitions (done here for ease of parsing). (Usually a terminal is
  a contiguous sequence of symbols from the alphabet. However, both kinds of
  grammars have a one to one correspondence, and can be converted easily.)
* A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
  in the grammar using _rules_ for expansion.
* A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
  nonterminals) that describe an expansion of a given terminal.
* A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.
* A _context-free grammar_ is  composed of a set of nonterminals and 
  corresponding definitions that define the structure of the nonterminal.
* A terminal _derives_ a string if the string contains only the symbols in the
  terminal. A nonterminal derives a string if the corresponding definition
  derives the string. A definition derives the  string if one of the rules in
  the definition derives the string. A rule derives a string if the sequence
  of terms that make up the rule can derive the string, deriving one substring 
  after another contiguously (also called parsing).
* A *derivation tree* is an ordered tree that describes how an input string is
  derived by the given start symbol. Also called a *parse tree*.
* A derivation tree can be collapsed into its string equivalent. Such a string
  can be parsed again by the nonterminal at the root node of the derivation
  tree such that at least one of the resulting derivation trees would be the
  same as the one we started with.

<!--


grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<expr>', '+', '<expr>'],
        ['<expr>', '-', '<expr>'],
        ['<expr>', '*', '<expr>'],
        ['<expr>', '/', '<expr>'],
        ['<expr>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}
START = '<start>'
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;],

        [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [
        [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;],
        [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
a_grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<expr>', '+', '<expr>'],
        ['<expr>', '-', '<expr>'],
        ['<expr>', '*', '<expr>'],
        ['<expr>', '/', '<expr>'],
        ['<integer>']],
    '<integer>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}
############
-->

Here is another grammar that targets the same language. Unlike the first
grammar, this grammar produces ambiguous parse results.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
a_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;&lt;expr&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;expr&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;expr&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;expr&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;expr&gt;&#x27;],
        [&#x27;&lt;integer&gt;&#x27;]],
    &#x27;&lt;integer&gt;&#x27;: [
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>




## Summary

An Earley parser executes the following steps for parsing:

Use `<start>` as the entry into parsing. At this point, we want to parse the
given string by the nonterminal `<start>`. The _definition_ of `<start>`
contains the possible expansion rule that can match the given string. Each
expansion rule can be thought of as a *parsing path*, with contiguous
substrings of the given input string matched by the particular terms in the
rule.

* When given a nonterminal to match the string, the essential idea is to
  get the rules in the definition, and add them to the current set of
  parsing paths to try with the given string. Within the parsing path, we have
  a parsed index which denotes the progress of parsing that particular path
  (i.e the point till which the string until now has been recognized by that
  path, and any parents of this path). When a rule is newly added, this parsed
  index is set to zero.

* We next look at our set of possible parsing paths, and check if any of these
  paths start with a nonterminal. If one is found, then for that parsing path to
  be completed with the given string, that nonterminal has to be recognized
  first. So, we add the expansion rules corresponding to that nonterminal to the
  list of possible parsing paths. We do this recursively.

* Now, examine the current letter in the input. Then select all parsing paths
  that have that particular letter at the parsed index. These expressions can
  now advance one step to the next index. We add such parsing paths to the
  set of parsing paths to try for the next character.

* While doing this, any parsing paths have finished parsing, fetch its
  corresponding nonterminal and advance all parsing paths that have that
  nonterminal at the parsing index.

* Continue recursively until the parsing path corresponding to `<start>` has
  finished.


The chart parser depends on a chart (a table) for parsing. The columns
correspond to the characters in the input string. Each column represents a set
of *states*, and corresponds to the legal rules to follow from that point on.

Say we start with the following grammar:

<!--

sample_grammar = {
    '<start>': [['<A>','<B>']],
    '<A>': [['a', '<B>', 'c'], ['a', '<A>']],
    '<B>': [['b', '<C>'], ['<D>']],
    '<C>': [['c']],
    '<D>': [['d']]
}
-->

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

sample_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;,&#x27;&lt;B&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;, &#x27;&lt;B&gt;&#x27;, &#x27;c&#x27;], [&#x27;a&#x27;, &#x27;&lt;A&gt;&#x27;]],
    &#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;, &#x27;&lt;C&gt;&#x27;], [&#x27;&lt;D&gt;&#x27;]],
    &#x27;&lt;C&gt;&#x27;: [[&#x27;c&#x27;]],
    &#x27;&lt;D&gt;&#x27;: [[&#x27;d&#x27;]]
}
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


Earley parser produces a table of possible parse paths at each letter index of
the table. Given an input `adcd`, we seed the column `0`  with:

```
   <start>: | <A> <B>
```

where the `|` represents the parsing index (also called the dot). This indicates
that we are at the starting, and the next step is to identify `<A>`. After this
rule is processed, the column would contain two more states

```
   <A>: | a <B> <c>
   <A>: | a <A>
```
which represents two parsing paths to complete `<A>`.

After processing of column `0` (which corresponds to input character `a`), we
would find the following in column `1` (which corresponds to the input character `b`)

```
   <A>: a | <B> c
   <A>: a | <A>
   <B>: | b <C>
   <B>: | <D>
   <A>: | a <B> c
   <A>: | a <A>
   <D>: | d
```

Similarly, the next column (column `2` corresponding to `d`) would contain the following.

```
   <D>: | d
   <B>: <D> |
   <A>: a <B> | c
```

Next, column `3` corresponding to `c` would contain:
```
   <A>: a <B> c |
   <start>: <A> | <B>
   <B>: | <b> <C>
   <B>: | <D>
   <D>: | d
```

Finally, column `4` (`d`) would contain this at the end of processing.
```
   <D>: d |
   <B>: <D> |
   <start>: <A> <B> |
```

This is how the table or the chart -- from where the parsing gets its name: chart parsing -- gets filled.

## Column

The column contains a set of states. Each column corresponds
to a character (or a token if tokens are used).
Note that the states in a column corresponds to the parsing expression that will
occur once that character has been read. That is, the first column will
correspond to the parsing expression when no characters have been read.

The column allows for adding states, and checks to prevent duplication of
states.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Column:
    def __init__(self, index, letter):
        self.index, self.letter = index, letter
        self.states, self._unique = [], {}

    def __str__(self):
        return &quot;%s chart[%d]\n%s&quot; % (self.letter, self.index, &quot;\n&quot;.join(
            str(state) for state in self.states if state.finished()))

    def add(self, state):
        if state in self._unique:
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## State

A state represents a parsing path (which corresponds to the nonterminal, and the
expansion rule that is being followed) with the current parsed index. 
Each state contains the following:

* name: The nonterminal that this rule represents.
* expr: The rule that is being followed
* dot:  The point till which parsing has happened in the rule.
* s_col: The starting point for this rule.
* e_col: The ending point for this rule.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class State:
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col

    def finished(self):
        return self.dot &gt;= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot &lt; len(self.expr) else None

    def __str__(self):
        def idx(var):
            return var.index if var else -1

        return self.name + &#x27;:= &#x27; + &#x27; &#x27;.join([
            str(p)
            for p in [*self.expr[:self.dot], &#x27;|&#x27;, *self.expr[self.dot:]]
        ]) + &quot;(%d,%d)&quot; % (idx(self.s_col), idx(self.e_col))

    def copy(self):
        return State(self.name, self.expr, self.dot, self.s_col, self.e_col)

    def _t(self):
        return (self.name, self.expr, self.dot, self.s_col.index)

    def __hash__(self):
        return hash(self._t())

    def __eq__(self, other):
        return self._t() == other._t()

    def advance(self):
        return State(self.name, self.expr, self.dot + 1, self.s_col)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

The convenience methods `finished()`, `advance()` and `at_dot()` should be
self explanatory. For example,

<!--
############
nt_name = '<B>'
nt_expr = tuple(sample_grammar[nt_name][1])
col_0 = Column(0, None)
a_state = State(nt_name, tuple(nt_expr), 0, col_0)
print(a_state.at_dot())
############
-->

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nt_name = &#x27;&lt;B&gt;&#x27;
nt_expr = tuple(sample_grammar[nt_name][1])
col_0 = Column(0, None)
a_state = State(nt_name, tuple(nt_expr), 0, col_0)
print(a_state)
print(a_state.at_dot())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

That is, the next symbol to be parsed is `<D>`, and if we advance it,

<!--
############
b_state = a_state.advance()
print(b_state)
print(b_state.finished())
############
-->

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
b_state = a_state.advance()
print(b_state)
print(b_state.finished())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


## Parser

We start with a bare minimum interface for a parser. It should allow one
to parse a given text using a given nonterminal (which should be present in
the grammar).

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Parser:
    def parse_on(self, text, start_symbol):
        raise NotImplemented()
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We now initialize the Earley parser, which is a parser.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(Parser):
    def __init__(self, grammar, **kwargs):
        self._grammar = grammar
        self.epsilon = nullable(grammar)
        self.log = False
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

#### Nullable

Earley parser handles *nullable* nonterminals separately. A nullable
nonterminal is a nonterminal that can derive an empty string. That is
at least one of the expansion rules must derive an empty string. An
expansion rule derives an empty string if *all* of the tokens can
derive the empty string. This means no terminal symbols (assuming we
do not have zero width terminal symbols), and all nonterminal symbols
can derive empty string.

In this implementation, we first initialize the list of first level
nullable nonterminals that contain an empty expansion. That is, they
directly derive the empty string.
Next, we remove any expansion rule that contains a token as these
expansion rules will not result in empty strings. Next, we start with
our current list of nullable nonterminals, take one at a time, and
remove them from the current expansion rules. If any expansion rule
becomes empty, the corresponding nonterminal is added to the nullable
nonterminal list. This continues until all nullable nonterminals
are processed.


<!--
############
def is_nt(k):
    return (k[0], k[-1]) == ('<', '>')

def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not is_nt(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_nt(k):
    return k[0], k[-1] == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)

def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not is_nt(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

An example

<!--
############
nullable_grammar = {
    '<start>': [['<A>', '<B>']],
    '<A>': [['a'], [], ['<C>']],
    '<B>': [['b']],
    '<C>': [['<A>'], ['<B>']]
}
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nullable_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;, &#x27;&lt;B&gt;&#x27;]],
    &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;], [], [&#x27;&lt;C&gt;&#x27;]],
    &#x27;&lt;B&gt;&#x27;: [[&#x27;b&#x27;]],
    &#x27;&lt;C&gt;&#x27;: [[&#x27;&lt;A&gt;&#x27;], [&#x27;&lt;B&gt;&#x27;]]
}
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Checking
<!--
############
print(nullable(nullable_grammar))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable(nullable_grammar))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

This is however expensive. The main problem is that we are looking up
expansion rules again and again. Can we make this linear?
Here is a simple solution. We simply keep a look up table for each
nonterminal that provides the expansion rules it appears in. Further,
for each expansion rule, we keep the count of non-nullable nonterminals.
This way, we can directly lookup the corresponding rules whenever we
need to process a nullable nonterminal.

<!--
############
def get_appearances(g, key):
    res = []
    for k in g:
        alts = []
        for alt in g[k]:
            cnt = [t for t in alt if t == key]
            if cnt:
                res.append((len(alt), k, alt))
    return res
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_appearances(g, key):
    res = []
    for k in g:
        alts = []
        for alt in g[k]:
            cnt = [t for t in alt if t == key]
            if cnt:
                res.append((len(alt), k, alt))
    return res
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
def nullable(g):
    g_cur = rem_terminals(g)

    hash_counts = {k:get_appearances(g_cur, k) for k in g_cur}

    nullable_keys = {k for k in g if [] in g[k]}
   
    unprocessed  = list(nullable_keys)

    while unprocessed:
        nxt, *unprocessed = unprocessed
        lst = hash_counts[nxt]
        new_lst = []
        for (cnt, k, rule) in lst:
            new_cnt = cnt - 1
            if new_cnt == 0:
                if k not in nullable_keys:
                    unprocessed.append(k)
                    nullable_keys.add(k)
            else:
                new_lst.append((new_cnt, k, rule))
    return nullable_keys
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def nullable(g):
    # remove expansions with terminals
    g_cur = rem_terminals(g)

    hash_counts = {k:get_appearances(g_cur, k) for k in g_cur}

    nullable_keys = {k for k in g if [] in g[k]}
   
    unprocessed  = list(nullable_keys)

    while unprocessed:
        nxt, *unprocessed = unprocessed
        lst = hash_counts[nxt]
        new_lst = []
        for (cnt, k, rule) in lst:
            new_cnt = cnt - 1
            if new_cnt == 0:
                if k not in nullable_keys:
                    unprocessed.append(k)
                    nullable_keys.add(k)
            else:
                new_lst.append((new_cnt, k, rule))
    return nullable_keys
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Checking
<!--
############
print(nullable(nullable_grammar))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(nullable(nullable_grammar))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



## Chart construction

Earley parser is a chart parser. That is, it relies on a table of solutions
to smaller problems. This table is called a chart (hence the name of such parsers -- chart parsers).

Here, we begin the chart construction by 
seeding the chart with columns representing the tokens or characters.
Consider our example grammar again. The starting point is,
```
   <start>: | <A> <B>
```
We add this state to the `chart[0]` to start the parse. Note that the term
after dot is `<A>`, which will need to be recursively inserted to the column.
We will see how to do that later.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def chart_parse(self, tokens, start, alt):
        chart = [Column(i, tok) for i, tok in enumerate([None, *tokens])]
        chart[0].add(State(start, alt, 0, chart[0]))
        return self.fill_chart(chart)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We seed our initial state in the example

<!--
############
nt_expr = tuple(sample_grammar[START][0])
col_0 = Column(0, None)
start_state = State(START, nt_expr, 0, col_0)
col_0.add(start_state)
print(start_state)
print(start_state.at_dot())
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nt_expr = tuple(sample_grammar[START][0])
col_0 = Column(0, None)
start_state = State(START, nt_expr, 0, col_0)
col_0.add(start_state)
print(start_state)
print(start_state.at_dot())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



Then, we complete the chart.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def fill_chart(self, chart):
        for i, col in enumerate(chart):
            for state in col.states:
                if state.finished():
                    self.complete(col, state)
                else:
                    sym = state.at_dot()
                    if sym in self._grammar:
                        self.predict(col, sym, state)
                    else:
                        if i + 1 &gt;= len(chart):
                            continue
                        self.scan(chart[i + 1], state, sym)
            if self.log: print(col, '\n')
        return chart
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


There are three main methods: `predict()`, `scan()`, and `complete()`

### Predict

If the term after the dot is a nonterminal, `predict()` is called. It
adds the expansion of the nonterminal to the current column.

If the term is nullable, then we simply advance the current state, and
add that to the current column. This fix to the original Earley parsing
was suggested by Aycock et al.[^aycock2002practical].


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def predict(self, col, sym, state):
        for alt in self._grammar[sym]:
            col.add(State(sym, tuple(alt), 0, col))
        if sym in self.epsilon:
            col.add(state.advance())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

If we look our example, we have seeded the first column with `| <A> <B>`. Now,
`fill_chart()` will find that the next term is `<A>` and call `predict()`
which will then add the expansions of `<A>`.

<!--
############
ep = EarleyParser(sample_grammar)
ep.chart = [col_0]
for s in ep.chart[0].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar)
ep.chart = [col_0]
for s in ep.chart[0].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


Next, we apply predict.

<!--
############
ep.predict(col_0, '<A>', s)
for s in ep.chart[0].states:
    print(s)
############
-->

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep.predict(col_0, &#x27;&lt;A&gt;&#x27;, s)
for s in ep.chart[0].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


### Scan

The `scan()` method is called if the next symbol is a terminal symbol. If the
state matches the next term, moves the dot one position, and adds the new
state to the column.

For example, consider this state.
```
   <B>: | b c
```
If we scan the next column's letter, and that letter is `b`, then it matches the
next symbol. So, we can advance the state by one symbol, and add it to the next
column.
```
   <B>: b | c
```

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def scan(self, col, state, letter):
        if letter == col.letter:
            col.add(state.advance())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Here is our continuing example.

<!--
############
ep = EarleyParser(sample_grammar)
col_1 = Column(1, 'a')
ep.chart = [col_0, col_1]

new_state = ep.chart[0].states[1]
print(new_state)

ep.scan(col_1, new_state, 'a')
for s in ep.chart[1].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar)
col_1 = Column(1, &#x27;a&#x27;)
ep.chart = [col_0, col_1]

new_state = ep.chart[0].states[1]
print(new_state)

ep.scan(col_1, new_state, &#x27;a&#x27;)
for s in ep.chart[1].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
#grammar = {
#        START:['<expr>'],
#        '<sym>': ['a', 'b', 'c', 'd'],
#        '<op>': ['+', '-'],
#        '<expr>': ['<sym>', '<expr><op><expr>']
#        }
#
#grammar = {
#        START:['<expr>'],
#        '<sym>': ['a', 'b', 'c', 'd'],
#        '<expr>': ['<sym>', '<expr>+<expr>', '<expr>-<expr>']
#        }
#
#grammar = {'<start>': ['<expr>'],
# '<expr>': ['<term>+<expr>', '<term>-<expr>', '<term>'],
# '<term>': ['<factor>*<term>', '<factor>/<term>', '<factor>'],
# '<factor>': ['+<factor>',
#  '-<factor>',
#  '(<expr>)',
#  '<integer>',
#  '<integer>.<integer>'],
# '<integer>': ['<digit><integer>', '<digit>'],
# '<digit>': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']}
-->

### Complete

The `complete()` method is called if a particular state has finished the rule
during execution. It first extracts the start column of the finished state, then
for all states in the start column that is not finished, find the states that
were parsing this current state (that is, we can go back to continue to parse
those rules now). Next, shift them by one position, and add them to the current
column.

For example, say the state we have is:
```
   <A>: a | <B> c
   <B>: b c |
```
The state `<B> b c |` is complete, and we need to advance any state that
has `<B>` at the dot to one index forward, which is `<A>: a <B> | c`

How do we determine the parent states? During predict, we added the predicted
child states to the same column as that of the inspected state. So, the states
will be found in the starting column of the current state, with the same symbol
at_dot as that of the name of the completed state.

We advance all such parents (producing new states) and add the new states to the
current column.


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        for st in parent_states:
            col.add(st.advance())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Here is our example. We start parsing `ad`. So, we have three columns.

<!--
############
ep = EarleyParser(sample_grammar)
col_1 = Column(1, 'a')
col_2 = Column(2, 'd')
ep.chart = [col_0, col_1, col_2]
ep.predict(col_0, '<A>', s)
for s in ep.chart[0].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar)
col_1 = Column(1, &#x27;a&#x27;)
col_2 = Column(2, &#x27;d&#x27;)
ep.chart = [col_0, col_1, col_2]
ep.predict(col_0, &#x27;&lt;A&gt;&#x27;, s)
for s in ep.chart[0].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Next, we populate column 1

<!--
############
for state in ep.chart[0].states:
    if state.at_dot() not in sample_grammar:
        ep.scan(col_1, state, 'a')
for s in ep.chart[1].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for state in ep.chart[0].states:
    if state.at_dot() not in sample_grammar:
        ep.scan(col_1, state, &#x27;a&#x27;)
for s in ep.chart[1].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Predict again to flush out

<!--
############
for state in ep.chart[1].states:
    if state.at_dot() in sample_grammar:
        ep.predict(col_1, state.at_dot(), state)
for s in ep.chart[1].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for state in ep.chart[1].states:
    if state.at_dot() in sample_grammar:
        ep.predict(col_1, state.at_dot(), state)
for s in ep.chart[1].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Scan again to populate column 2

<!--
############
for state in ep.chart[1].states:
    if state.at_dot() not in sample_grammar:
        ep.scan(col_2, state, state.at_dot())

for s in ep.chart[2].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for state in ep.chart[1].states:
    if state.at_dot() not in sample_grammar:
        ep.scan(col_2, state, state.at_dot())

for s in ep.chart[2].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Finally, we use complete.


<!--
############
for state in ep.chart[2].states:
    if state.finished():
        ep.complete(col_2, state)

for s in ep.chart[2].states:
    print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for state in ep.chart[2].states:
    if state.finished():
        ep.complete(col_2, state)

for s in ep.chart[2].states:
    print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Filling the chart

We can now recognize the given string as part of the language represented by the grammar.

<!--
############
ep = EarleyParser(sample_grammar, log=True)
columns = ep.chart_parse('adcd', START, tuple(sample_grammar[START][0]))
for c in columns: print(c)
############
-->

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar, log=True)
columns = ep.chart_parse(&#x27;adcd&#x27;, START, tuple(sample_grammar[START][0]))
for c in columns: print(c)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



The chart above only shows completed entries. The parenthesized expression
indicates the column just before the first character was recognized, and the
ending column.

Notice how the `<start>` nonterminal shows the dot at the end. That is, fully parsed.

<!--
############
last_col = columns[-1]
for s in last_col.states:
    if s.name == '<start>':
        print(s)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
last_col = columns[-1]
for s in last_col.states:
    if s.name == &#x27;&lt;start&gt;&#x27;:
        print(s)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


## Derivation trees

We use the following procedures to translate the parse forest to individual
trees.

### parse_prefix

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def parse_prefix(self, text, start_symbol, alt):
        self.table = self.chart_parse(text, start_symbol, alt)
        for col in reversed(self.table):
            states = [st for st in col.states
                if st.name == start_symbol and st.expr == alt and st.s_col.index == 0
            ]
            if states:
                return col.index, states
        return -1, []
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Here is an example of using it.

<!--
############
ep = EarleyParser(sample_grammar)
cursor, last_states = ep.parse_prefix('adcd', START, tuple(sample_grammar[START][0]))
print(cursor, [str(s) for s in last_states])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar)
cursor, last_states = ep.parse_prefix(&#x27;adcd&#x27;, START, tuple(sample_grammar[START][0]))
print(cursor, [str(s) for s in last_states])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

### parse_on

Our `parse_on()` method is slightly different from usual Earley implementations
in that we accept any nonterminal symbol, not just nonterminal symbols with a
single expansion rule. We accomplish this by computing a different chart for
each expansion.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def parse_on(self, text, start_symbol):
        for alt in self._grammar[start_symbol]:
            cursor, states = self.parse_prefix(text, start_symbol, tuple(alt))
            start = next((s for s in states if s.finished()), None)

            if cursor &lt; len(text) or not start:
                #raise SyntaxError(&quot;at &quot; + repr(text[cursor:]))
                continue

            forest = self.parse_forest(self.table, start)
            for tree in self.extract_trees(forest):
                yield tree
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

### parse_paths


The parse_paths() method tries to unify the given expression in `named_expr` with
the parsed string. For that, it extracts the last symbol in `named_expr` and
checks if it is a terminal symbol. If it is, then it checks the chart at `til` to
see if the letter corresponding to the position matches the terminal symbol.
If it does, extend our start index by the length of the symbol.

If the symbol was a nonterminal symbol, then we retrieve the parsed states
at the current end column index (`til`) that correspond to the nonterminal
symbol, and collect the start index. These are the end column indexes for
the remaining expression.

Given our list of start indexes, we obtain the parse paths from the remaining
expression. If we can obtain any, then we return the parse paths. If not, we
return an empty list.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def parse_paths(self, named_expr, chart, frm, til):
        def paths(state, start, k, e):
            if not e:
                return [[(state, k)]] if start == frm else []
            else:
                return [[(state, k)] + r
                        for r in self.parse_paths(e, chart, frm, start)]

        *expr, var = named_expr
        starts = None
        if var not in self._grammar:
            starts = ([(var, til - len(var),
                        &#x27;t&#x27;)] if til &gt; 0 and chart[til].letter == var else [])
        else:
            starts = [(s, s.s_col.index, &#x27;n&#x27;) for s in chart[til].states
                      if s.finished() and s.name == var]

        return [p for s, start, k in starts for p in paths(s, start, k, expr)]
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Example

<!--
############
print(sample_grammar[START])
ep = EarleyParser(sample_grammar)
completed_start = last_states[0]
paths = ep.parse_paths(completed_start.expr, columns, 0, 4)
for path in paths:
    print([list(str(s_) for s_ in s) for s in path])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(sample_grammar[START])
ep = EarleyParser(sample_grammar)
completed_start = last_states[0]
paths = ep.parse_paths(completed_start.expr, columns, 0, 4)
for path in paths:
    print([list(str(s_) for s_ in s) for s in path])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

That is, the parse path for `<start>` given the input `adcd` included
recognizing the expression `<A><B>`. This was recognized by the two states:
`<A>` from input(0) to input(2) which further involved recognizing the rule
`a<B>c`, and the next state `<B>` from input(3) which involved recognizing the
rule `<D>`.

### parse_forest

The `parse_forest()` method takes the state which represents the completed
parse, and determines the possible ways that its expressions corresponded to
the parsed expression. For example, say we are parsing `1+2+3`, and the
state has `[<expr>,+,<expr>]` in `expr`. It could have been parsed as either
`[{<expr>:1+2},+,{<expr>:3}]` or `[{<expr>:1},+,{<expr>:2+3}]`.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def forest(self, s, kind, chart):
        return self.parse_forest(chart, s) if kind == &#x27;n&#x27; else (s, [])

    def parse_forest(self, chart, state):
        pathexprs = self.parse_paths(state.expr, chart, state.s_col.index,
                                     state.e_col.index) if state.expr else []
        return state.name, [[(v, k, chart) for v, k in reversed(pathexpr)]
                            for pathexpr in pathexprs]
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Example

<!--
############
ep = EarleyParser(sample_grammar)
result = ep.parse_forest(columns, last_states[0])
print(result)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ep = EarleyParser(sample_grammar)
result = ep.parse_forest(columns, last_states[0])
print(result)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

### extract_trees

We show how to extract a single tree first, and then generalize it to
all trees.

<!--
############
class EarleyParser(EarleyParser):
    def extract_a_tree(self, forest_node):
        name, paths = forest_node
        if not paths:
            return (name, [])
        return (name, [self.extract_a_tree(self.forest(*p)) for p in paths[0]])

    def extract_trees(self, forest):
        yield self.extract_a_tree(forest)

############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def extract_a_tree(self, forest_node):
        name, paths = forest_node
        if not paths:
            return (name, [])
        return (name, [self.extract_a_tree(self.forest(*p)) for p in paths[0]])


    def extract_trees(self, forest):
        yield self.extract_a_tree(forest)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Example

<!--
############
mystring = '1+2+4'
parser = EarleyParser(a_grammar)
for tree in parser.parse_on(mystring, START):
    print(tree)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;1+2+4&#x27;
parser = EarleyParser(a_grammar)
for tree in parser.parse_on(mystring, START):
    print(tree)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



### Ambiguous Parsing

Ambiguous grammars can produce multiple derivation trees for some given string.
In the above example, the `a_grammar` can parse `1+2+4` in as either `[1+2]+4` or `1+[2+4]`.

That is, we need to extract all derivation trees.
We enhance our `extract_trees()` as below.

<!--
############
import itertools as I
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import itertools as I
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
class EarleyParser(EarleyParser):
    def extract_trees(self, forest_node):
        name, paths = forest_node
        if not paths:
            yield (name, [])
        results = []
        for path in paths:
            ptrees = [self.extract_trees(self.forest(*p)) for p in path]
            for p in I.product(*ptrees):
                yield (name, p)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def extract_trees(self, forest_node):
        name, paths = forest_node
        if not paths:
            yield (name, [])
        results = []
        for path in paths:
            ptrees = [self.extract_trees(self.forest(*p)) for p in path]
            for p in I.product(*ptrees):
                yield (name, p)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


## Example

Using the same example,

<!--
############
mystring = '1+2+4'
parser = EarleyParser(a_grammar)
for tree in parser.parse_on(mystring, START):
    print(tree)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;1+2+4&#x27;
parser = EarleyParser(a_grammar)
for tree in parser.parse_on(mystring, START):
    print(tree)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>




We need a way to display parse trees.


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import itertools

class O:
    def __init__(self, **keys): self.__dict__.update(keys)
    def __repr__(self): return str(self.__dict__)

Options = O(F=&#x27;|&#x27;, L=&#x27;+&#x27;, V=&#x27;|&#x27;, H=&#x27;-&#x27;, NL=&#x27;\n&#x27;)

def format_newlines(prefix, formatted_node):
    replacement = &#x27;&#x27;.join([Options.NL, &#x27;\n&#x27;, prefix])
    return formatted_node.replace(&#x27;\n&#x27;, replacement)

def format_tree(node, format_node, get_children, prefix=&#x27;&#x27;):
    children = list(get_children(node))
    next_prefix = &#x27;&#x27;.join([prefix, Options.V, &#x27;   &#x27;])
    for child in children[:-1]:
        fml = format_newlines(next_prefix, format_node(child))
        yield &#x27;&#x27;.join([prefix, Options.F, Options.H, Options.H, &#x27; &#x27;, fml])
        tree = format_tree(child, format_node, get_children, next_prefix)
        for result in tree:
            yield result
    if children:
        last_prefix = &#x27;&#x27;.join([prefix, &#x27;    &#x27;])
        fml = format_newlines(last_prefix, format_node(children[-1]))
        yield &#x27;&#x27;.join([prefix, Options.L, Options.H, Options.H, &#x27; &#x27;, fml])
        tree = format_tree(children[-1], format_node, get_children, last_prefix)
        for result in tree:
            yield result

def format_parsetree(node, format_node, get_children):
    lines = itertools.chain([format_node(node)], format_tree(node, format_node, get_children), [&#x27;&#x27;],)
    return &#x27;\n&#x27;.join(lines)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


Displaying the tree

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(format_parsetree(tree, format_node=lambda x: repr(x[0]),
        get_children=lambda x: x[1]))
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Remaining

There is a problem with our `extract_trees()` method. The issue is that it is
too eager. The parse forest can have an infinite number of trees, and at this
time we effectively try to extract all at the same time. So, in case of
such grammars our `extract_trees()` will fail. Here are two example grammars.


<!--
############
directly_self_referring = {
    '<start>': [['<query>']],
    '<query>': [['<expr>']],
    "<expr>": [["<expr>"], ['a']],
}

indirectly_self_referring = {
    '<start>': [['<query>']],
    '<query>': [['<expr>']],
    '<expr>': [['<aexpr>'], ['a']],
    '<aexpr>': [['<expr>']],
}
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
directly_self_referring = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;query&gt;&#x27;]],
    &#x27;&lt;query&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &quot;&lt;expr&gt;&quot;: [[&quot;&lt;expr&gt;&quot;], [&#x27;a&#x27;]],
}

indirectly_self_referring = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;query&gt;&#x27;]],
    &#x27;&lt;query&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [[&#x27;&lt;aexpr&gt;&#x27;], [&#x27;a&#x27;]],
    &#x27;&lt;aexpr&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
}
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

An example run.

<!--
############
mystring = 'a'
for grammar in [directly_self_referring, indirectly_self_referring]:
    forest = EarleyParser(grammar).parse_on(mystring, START)
    print('recognized', mystring)
    try:
        for tree in forest:
            print(tree)
    except RecursionError as e:
         print("Recursion error",e)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
mystring = &#x27;a&#x27;
for grammar in [directly_self_referring, indirectly_self_referring]:
    forest = EarleyParser(grammar).parse_on(mystring, START)
    print(&#x27;recognized&#x27;, mystring)
    try:
        for tree in forest:
            print(tree)
    except RecursionError as e:
         print(&quot;Recursion error&quot;,e)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


The problem is that, our implementation of `extract_trees()` is eager.
That is, it attempts to extract all inner parse trees before it can construct
the outer parse tree. When there is a self reference, this results in recursion.
Here is a simple extractor that avoids this problem. The idea here is that we
randomly and lazily choose a node to expand, which avoids the infinite
recursion.

<!--
############
import random
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
class SimpleExtractor:
    def __init__(self, parser, text, start_symbol, alt):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol, tuple(alt))
        start = next((s for s in states if s.finished()), None)
        if cursor < len(text) or not start:
            raise SyntaxError("at " + repr(cursor))
        self.my_forest = parser.parse_forest(parser.table, start)

    def extract_a_node(self, forest_node):
        name, paths = forest_node
        if not paths:
            return ((name, 0, 1), []), (name, [])
        cur_path, i, l = self.choose_path(paths)
        child_nodes = []
        pos_nodes = []
        for s, kind, chart in cur_path:
            f = self.parser.forest(s, kind, chart)
            postree, ntree = self.extract_a_node(f)
            child_nodes.append(ntree)
            pos_nodes.append(postree)
        
        return ((name, i, l), pos_nodes), (name, child_nodes)
    
    def choose_path(self, arr):
        l = len(arr)
        i = random.randrange(l)
        return arr[i], i, l
    
    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SimpleExtractor:
    def __init__(self, parser, text, start_symbol, alt):
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol, tuple(alt))
        start = next((s for s in states if s.finished()), None)
        if cursor &lt; len(text) or not start:
            raise SyntaxError(&quot;at &quot; + repr(cursor))
        self.my_forest = parser.parse_forest(parser.table, start)

    def extract_a_node(self, forest_node):
        name, paths = forest_node
        if not paths:
            return ((name, 0, 1), []), (name, [])
        cur_path, i, l = self.choose_path(paths)
        child_nodes = []
        pos_nodes = []
        for s, kind, chart in cur_path:
            f = self.parser.forest(s, kind, chart)
            postree, ntree = self.extract_a_node(f)
            child_nodes.append(ntree)
            pos_nodes.append(postree)
        
        return ((name, i, l), pos_nodes), (name, child_nodes)
    
    def choose_path(self, arr):
        l = len(arr)
        i = random.randrange(l)
        return arr[i], i, l
    
    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
de = SimpleExtractor(EarleyParser(directly_self_referring), mystring, START, directly_self_referring[START][0])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
de = SimpleExtractor(EarleyParser(directly_self_referring), mystring, START, directly_self_referring[START][0])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
for i in range(5):
    tree = de.extract_a_tree()
    print(tree)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in range(5):
    tree = de.extract_a_tree()
    print(tree)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


indirect reference

<!--
############
ie = SimpleExtractor(EarleyParser(indirectly_self_referring), mystring, START, indirectly_self_referring[START][0])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ie = SimpleExtractor(EarleyParser(indirectly_self_referring), mystring, START, indirectly_self_referring[START][0])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
for i in range(5):
    tree = ie.extract_a_tree()
    print(tree)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in range(5):
    tree = ie.extract_a_tree()
    print(tree)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Simple extractor gives no guarantee on the order. Can we fix that?



<!--
############
class ChoiceNode:
    def __init__(self, parent, total):
        self._p, self._chosen = parent, 0
        self._total, self.next = total, None

    def chosen(self):
        assert not self.finished()
        return self._chosen

    def __str__(self):
        return '%d(%s/%s %s)' % (self._i, str(self._chosen),
                                 str(self._total), str(self.next))
    def __repr__(self):
        return repr((self._i, self._chosen, self._total))

    def increment(self):
        # as soon as we increment, next becomes invalid
        self.next = None
        self._chosen += 1
        if self.finished():
            if self._p is None:
                return None
            return self._p.increment()
        return self
    
    def finished(self):
        return self._chosen >= self._total
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ChoiceNode:
    def __init__(self, parent, total):
        self._p, self._chosen = parent, 0
        self._total, self.next = total, None

    def chosen(self):
        assert not self.finished()
        return self._chosen

    def __str__(self):
        return &#x27;%d(%s/%s %s)&#x27; % (self._i, str(self._chosen),
                                 str(self._total), str(self.next))
    def __repr__(self):
        return repr((self._i, self._chosen, self._total))

    def increment(self):
        # as soon as we increment, next becomes invalid
        self.next = None
        self._chosen += 1
        if self.finished():
            if self._p is None:
                return None
            return self._p.increment()
        return self
    
    def finished(self):
        return self._chosen &gt;= self._total
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
class EnhancedExtractor(SimpleExtractor):
    def __init__(self, parser, text, start_symbol, alt):
        super().__init__(parser, text, start_symbol, alt)
        self.choices = choices = ChoiceNode(None, 1)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EnhancedExtractor(SimpleExtractor):
    def __init__(self, parser, text, start_symbol, alt):
        super().__init__(parser, text, start_symbol, alt)
        self.choices = choices = ChoiceNode(None, 1)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
class EnhancedExtractor(EnhancedExtractor):
    def choose_path(self, arr, choices):
        arr_len = len(arr)
        if choices.next is not None:
            if choices.next.finished():
                return None, None, None, choices.next
        else:
            choices.next = ChoiceNode(choices, arr_len)
        next_choice = choices.next.chosen()
        choices = choices.next
        return arr[next_choice], next_choice, arr_len, choices
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EnhancedExtractor(EnhancedExtractor):
    def choose_path(self, arr, choices):
        arr_len = len(arr)
        if choices.next is not None:
            if choices.next.finished():
                return None, None, None, choices.next
        else:
            choices.next = ChoiceNode(choices, arr_len)
        next_choice = choices.next.chosen()
        choices = choices.next
        return arr[next_choice], next_choice, arr_len, choices
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
class EnhancedExtractor(EnhancedExtractor):
    def extract_a_node(self, forest_node, seen, choices):
        name, paths = forest_node
        if not paths:
            return (name, []), choices

        cur_path, _i, _l, new_choices = self.choose_path(paths, choices)
        if cur_path is None:
            return None, new_choices
        child_nodes = []
        for s, kind, chart in cur_path:
            if kind == 't':
                child_nodes.append((s, []))
                continue
            nid = (s.name, s.s_col.index, s.e_col.index)
            if nid in seen:
                return None, new_choices
            f = self.parser.forest(s, kind, chart)
            ntree, newer_choices = self.extract_a_node(f, seen | {nid}, new_choices)
            if ntree is None:
                return None, newer_choices
            child_nodes.append(ntree)
            new_choices = newer_choices
        return (name, child_nodes), new_choices
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EnhancedExtractor(EnhancedExtractor):
    def extract_a_node(self, forest_node, seen, choices):
        name, paths = forest_node
        if not paths:
            return (name, []), choices

        cur_path, _i, _l, new_choices = self.choose_path(paths, choices)
        if cur_path is None:
            return None, new_choices
        child_nodes = []
        for s, kind, chart in cur_path:
            if kind == &#x27;t&#x27;:
                child_nodes.append((s, []))
                continue
            nid = (s.name, s.s_col.index, s.e_col.index)
            if nid in seen:
                return None, new_choices
            f = self.parser.forest(s, kind, chart)
            ntree, newer_choices = self.extract_a_node(f, seen | {nid}, new_choices)
            if ntree is None:
                return None, newer_choices
            child_nodes.append(ntree)
            new_choices = newer_choices
        return (name, child_nodes), new_choices
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
class EnhancedExtractor(EnhancedExtractor):
    def extract_a_tree(self):
        while not self.choices.finished():
            parse_tree, choices = self.extract_a_node(self.my_forest, set(), self.choices)
            choices.increment()
            if parse_tree is not None:
                return parse_tree
        return None
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EnhancedExtractor(EnhancedExtractor):
    def extract_a_tree(self):
        while not self.choices.finished():
            parse_tree, choices = self.extract_a_node(self.my_forest, set(), self.choices)
            choices.increment()
            if parse_tree is not None:
                return parse_tree
        return None
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
ee = EnhancedExtractor(EarleyParser(indirectly_self_referring), mystring, START, indirectly_self_referring[START][0])
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ee = EnhancedExtractor(EarleyParser(indirectly_self_referring), mystring, START, indirectly_self_referring[START][0])
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
i = 0
while True:
    i += 1
    t = ee.extract_a_tree()
    if t is None: break
    print(i, t)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
i = 0
while True:
    i += 1
    t = ee.extract_a_tree()
    if t is None: break
    print(i, t)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>


[^earley1970an]: Earley, Jay. "An efficient context-free parsing algorithm." Communications of the ACM 13.2 (1970): 94-102.

[^leo1991a]: Leo, Joop MIM. "A general context-free parsing algorithm running in linear time on every LR (k) grammar without using lookahead." Theoretical computer science 82.1 (1991): 165-176.

[^aycock2002practical]: Aycock, John, and R. Nigel Horspool. "Practical earley parsing." The Computer Journal 45.6 (2002): 620-630.
