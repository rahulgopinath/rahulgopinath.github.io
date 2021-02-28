---
published: true
title: Error Correcting Earley Parser
layout: post
comments: true
tags: parsing, error correcting, context-free
categories: post
---

We talked about Earley parsers [previously](/post/2021/02/06/earley-parsing/).
One of the interesting things about Earley parsers is that it also forms the
basis of best known general context-free error correcting parser. A parser is
error correcting if it is able to parse corrupt inputs that only partially
conform to a given grammar. The particular algorithm we will be examining is
the minimum distance error correcting parser by Aho et al.[^aho1972minimum].

There are two parts to this algorithm. The first is the idea of a
covering grammar that parses any corrupt input and the second is the
extraction of the best possible parse from the corresponding parse forest.

Aho et al. uses Earley parser for their error correcting parser. So, we will
follow in their foot steps.
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

<!--
############
import sys
if "pyodide" in sys.modules:
    import pyodide
    github_repo = 'https://raw.githubusercontent.com/'
    my_repo = 'rahulgopinath/rahulgopinath.github.io'
    earley_module_str = pyodide.open_url(github_repo + my_repo +
            '/master/notebooks/2021-02-06-earley-parsing.py')
    pyodide.eval_code(earley_module_str.getvalue(), globals())
else:
    # caution: this is a horrible temporary hack to load a local file with
    # hyphens, and make it available in the current namespace.
    # Dont use it in production.
    __vars__ = vars(__import__('2021-02-06-earley-parsing'))
    globals().update({k:__vars__[k] for k in __vars__ if k not in ['__name__']})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys
if &quot;pyodide&quot; in sys.modules:
    import pyodide
    github_repo = &#x27;https://raw.githubusercontent.com/&#x27;
    my_repo = &#x27;rahulgopinath/rahulgopinath.github.io&#x27;
    earley_module_str = pyodide.open_url(github_repo + my_repo +
            &#x27;/master/notebooks/2021-02-06-earley-parsing.py&#x27;)
    pyodide.eval_code(earley_module_str.getvalue(), globals())
else:
    # caution: this is a horrible temporary hack to load a local file with
    # hyphens, and make it available in the current namespace.
    # Dont use it in production.
    __vars__ = vars(__import__(&#x27;2021-02-06-earley-parsing&#x27;))
    globals().update({k:__vars__[k] for k in __vars__ if k not in [&#x27;__name__&#x27;]})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Covering Grammar

The idea from Aho et al. is to first transform the given grammar into a
*covering grammar*. A grammar $$G_2$$ covers another grammar $$G_1$$ if
all productions in $$G_1$$ have a one to one correspondence to some production
in $$G_2$$, and a string that is parsed by $$G_1$$ is guaranteed to be parsed
by $$G_2$$, and all the parses from $$G_1$$ are guaranteed to exist in the set
of parses from $$G_2$$ (with the given homomorphism of productions).

So, we first construct a covering grammar that can handle any corruption of
input, with the additional property that there will be a parse of the corrupt
string which contains **the minimum number of modifications needed** such that
if they are applied on the string, it will make it parsed by the original
grammar.

### First, we load the prerequisites


<!--
############
import string
import random
import itertools as I

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
import random
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The following is our grammar and its start symbol.

<!--
############
grammar = {
    '<start>': [['<expr>']],
    '<expr>': [ ['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
    '<term>': [ ['<fact>', '*', '<term>'], ['<fact>', '/', '<term>'], ['<fact>']],
    '<fact>': [ ['<digits>'], ['(','<expr>',')']],
    '<digits>': [ ['<digit>','<digits>'], ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}
START = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [ [&#x27;&lt;term&gt;&#x27;, &#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;, &#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&lt;term&gt;&#x27;]],
    &#x27;&lt;term&gt;&#x27;: [ [&#x27;&lt;fact&gt;&#x27;, &#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;, &#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&lt;fact&gt;&#x27;]],
    &#x27;&lt;fact&gt;&#x27;: [ [&#x27;&lt;digits&gt;&#x27;], [&#x27;(&#x27;,&#x27;&lt;expr&gt;&#x27;,&#x27;)&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [ [&#x27;&lt;digit&gt;&#x27;,&#x27;&lt;digits&gt;&#x27;], [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;digit&gt;&#x27;: [[&quot;%s&quot; % str(i)] for i in range(10)],
}
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The grammar can be printed as follows.

<!--
############
def print_g(g):
    for k in g:
        print(k)
        for rule in g[k]:
            print('|  ', ' '.join([repr(k) for k in rule]))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def print_g(g):
    for k in g:
        print(k)
        for rule in g[k]:
            print(&#x27;|  &#x27;, &#x27; &#x27;.join([repr(k) for k in rule]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For example,

<!--
############
print_g(grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print_g(grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, constructing a covering grammar proceeds as follows.
First we define how to distinguish nonterminal and terminal symbols

<!--
############
def is_nt(k):
    if len(k) == 1: return False
    return (k[0], k[-1]) == ('<', '>')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_nt(k):
    if len(k) == 1: return False
    return (k[0], k[-1]) == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we take each terminal symbol in the given grammar. For example, the
below contains all terminal symbols from our `grammar`

<!--
############
Symbols = [t for k in grammar for alt in grammar[k] for t in alt if not is_nt(t)]
print(len(Symbols))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Symbols = [t for k in grammar for alt in grammar[k] for t in alt if not is_nt(t)]
print(len(Symbols))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we consider the following corruptions of the valid input:

* The input symbol being considered may have been deleted
* The input symbol being considered may have some junk value in front
* The input symbol may have been mistakenly written as something else.

A moment's reflection should convince you that a covering grammar only needs
to handle these three cases (In fact, only the first two cases are sufficient
but we add the third because it is also a _simple_ mutation).

The main idea is that we replace the given terminal symbol with an equivalent
nonterminal that lets you make these mistakes. So, we first define that
nonterminal that corresponds to each terminal symbol.

<!--
############
def This_sym(t):
    return '<$ [%s]>' % t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def This_sym(t):
    return &#x27;&lt;$ [%s]&gt;&#x27; % t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
print(This_sym('a'))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(This_sym(&#x27;a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also define a convenience function that when given a rule, translates the
terminal symbols in that rule to the above nonterminal symbol.

<!--
############
def translate_terminal(t):
    if is_nt(t): return t
    return This_sym(t)

def translate_terminals(g):
    return {k:[[translate_terminal(t) for t in alt] for alt in g[k]] for k in g}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def translate_terminal(t):
    if is_nt(t): return t
    return This_sym(t)

def translate_terminals(g):
    return {k:[[translate_terminal(t) for t in alt] for alt in g[k]] for k in g}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
print_g(translate_terminals(grammar))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print_g(translate_terminals(grammar))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
How are these nonterminals defined? Each nonterminal has the following
expansion rules

```
<$ {a}> -> a
         | <$.+> a
         | <$>
         | <$!{a}>
```

That is, each nonterminal that corresponds to a terminal symbol has the
following expansions: (1) it matches the original terminal symbol
(2) there is some junk before the terminal symbol. So, match and discard
that junk before matching the terminal symbol
-- `<$.+>` matches any number of any symbols. These are the corresponding
nonterminals names

<!--
############
Any_one = '<$.>'
Any_plus = '<$.+>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_one = &#x27;&lt;$.&gt;&#x27;
Any_plus = &#x27;&lt;$.+&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
(3) the terminal symbol was deleted. So, skip this terminal symbol by matching
empty (`<$>`)

<!--
############
Empty = '<$>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Empty = &#x27;&lt;$&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
(4) the input symbol was a mistake. That is, it matches any input symbol other
than the expected input symbol `a` -- `<$!{a}>`. We have to define as many
nonterminals as there are terminal symbols again. So, we define a function.

<!--
############
Any_not_str = '<$![%s]>'
def Any_not(t): return Any_not_str % t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_not_str = &#x27;&lt;$![%s]&gt;&#x27;
def Any_not(t): return Any_not_str % t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What happens if there is junk after parsing? We take care of that by wrapping
the start symbol as follows

```
<$corrupt_start> -> <start>
                  | <start> <$.+>
<$new_start> -> <$corrupt_start>
```

<!--
############
def corrupt_start(old_start):
    return '<@# %s>' % old_start[1:-1]

def new_start(old_start):
    return '<@ %s>' % old_start[1:-1]

def add_start(g, old_start):
    g_ = {}
    g_[corrupt_start(old_start)] = [[old_start], [old_start, Any_plus]]
    new_s = new_start(old_start)
    g_[new_s] = [[corrupt_start(old_start)]]
    return g_, new_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def corrupt_start(old_start):
    return &#x27;&lt;@# %s&gt;&#x27; % old_start[1:-1]

def new_start(old_start):
    return &#x27;&lt;@ %s&gt;&#x27; % old_start[1:-1]

def add_start(g, old_start):
    g_ = {}
    g_[corrupt_start(old_start)] = [[old_start], [old_start, Any_plus]]
    new_s = new_start(old_start)
    g_[new_s] = [[corrupt_start(old_start)]]
    return g_, new_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally we are ready to augment the original given grammar so that what we
have is a covering grammar. We first extract the symbols used, then produce
the nonterminal `Any_one` that correspond to any symbol match. Next,
we use `Any_not` to produce an any symbol except match. We then have a
`Empty` to match the absence of the nonterminal.

<!--
############
def augment_grammar(g, start, Symbols=None):
    if Symbols is None:
        Symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[k] for k in Symbols]}


    Match_any_sym_except = {}
    for kk in Symbols:
        Match_any_sym_except[Any_not(kk)] = [[k] for k in Symbols if k != kk]
    Match_empty = {Empty: []}

    Match_a_sym = {}
    for kk in Symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(g, start)
    return {**start_g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def augment_grammar(g, start, Symbols=None):
    if Symbols is None:
        Symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[k] for k in Symbols]}


    Match_any_sym_except = {}
    for kk in Symbols:
        Match_any_sym_except[Any_not(kk)] = [[k] for k in Symbols if k != kk]
    Match_empty = {Empty: []}

    Match_a_sym = {}
    for kk in Symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(g, start)
    return {**start_g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is the augmented grammar

<!--
############
covering_grammar, covering_start = augment_grammar(grammar, START)
print_g(covering_grammar)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar, covering_start = augment_grammar(grammar, START)
print_g(covering_grammar)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we are ready to check the covering properties of our grammar.

<!--
############
ie = SimpleExtractor(EarleyParser(covering_grammar), '1+1', covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ie = SimpleExtractor(EarleyParser(covering_grammar), &#x27;1+1&#x27;, covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What about an error?

<!--
############
ie2 = SimpleExtractor(EarleyParser(covering_grammar), '1+1+', covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie2.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ie2 = SimpleExtractor(EarleyParser(covering_grammar), &#x27;1+1+&#x27;, covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie2.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, we can parse corrupt inputs. The next step is how to extract
the minimally corrupt parse.

## The minimally corrupt parse.

First, we need to modify the Earley parser so that it can keep track of the
penalties. We essentially assign a penalty if any of the following us used.

* Any use of <$.> : Any_one --- note, Any_plus gets +1 automatically
* Any use of <$>  : Empty
* Any use of <$ !{.}>  : Any_not

<!--
############
class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        my_penalty = state.penalty
        if state.name ==  Empty:
            my_penalty = 1
        elif state.name == Any_one:
            my_penalty = 1
        elif state.name.startswith(Any_not_str[:4]):
            my_penalty = 1
        for st in parent_states:
            s = st.advance()
            s.penalty += my_penalty
            col.add(s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        my_penalty = state.penalty
        if state.name ==  Empty:
            my_penalty = 1
        elif state.name == Any_one:
            my_penalty = 1
        elif state.name.startswith(Any_not_str[:4]):
            my_penalty = 1
        for st in parent_states:
            s = st.advance()
            s.penalty += my_penalty
            col.add(s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This means that we need a new state definition with penalty.

<!--
############
class State(State):
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        self.penalty = 0

    def copy(self):
        s = State(self.name, self.expr, self.dot, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

    def advance(self):
        s = State(self.name, self.expr, self.dot + 1, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class State(State):
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        self.penalty = 0

    def copy(self):
        s = State(self.name, self.expr, self.dot, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s

    def advance(self):
        s = State(self.name, self.expr, self.dot + 1, self.s_col, self.e_col)
        s.penalty = self.penalty
        return s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Since States are created by Columns, we need new column too that knows about
state penalties. We also need to keep track of the minimum penalty that a state
incurred. In particular, any time we find a less corrupt parse, we update the
penalty.

<!--
############
class Column(Column):
    def add(self, state):
        if state in self._unique:
            if self._unique[state].penalty > state.penalty:
                # delete from self.states in fill_chart
                state.e_col = self
                self.states.append(state)
                self._unique[state] = state
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Column(Column):
    def add(self, state):
        if state in self._unique:
            if self._unique[state].penalty &gt; state.penalty:
                # delete from self.states in fill_chart
                state.e_col = self
                self.states.append(state)
                self._unique[state] = state
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As we find and add our states with lesser penalties, we need to remove the
higher penalty states from our list.

<!--
############
class Column(Column):
    def remove_extra_states(self):
        my_states = []
        for state in self._unique:
            cur_states = [s for s in self.states if s == state]
            if len(cur_states) > 1:
                cur_states = sorted(cur_states, key=lambda s: s.penalty)
            my_states.append(cur_states[0])
        self.states = my_states
        return

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Column(Column):
    def remove_extra_states(self):
        my_states = []
        for state in self._unique:
            cur_states = [s for s in self.states if s == state]
            if len(cur_states) &gt; 1:
                cur_states = sorted(cur_states, key=lambda s: s.penalty)
            my_states.append(cur_states[0])
        self.states = my_states
        return
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We need to call this method at the end of processing of the column.

<!--
############
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
                        if i + 1 >= len(chart):
                            continue
                        self.scan(chart[i + 1], state, sym)
            col.remove_extra_states()
            if self.log: print(col, '\n')
        return chart

############
-->
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
            col.remove_extra_states()
            if self.log: print(col, &#x27;\n&#x27;)
        return chart
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now, we need to hook up our new column and state to Earley parser.

<!--
############
class EarleyParser(EarleyParser):
    def create_column(self, i, tok): return Column(i, tok)

    def create_state(self, sym, alt, num, col): return State(sym, alt, num, col)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def create_column(self, i, tok): return Column(i, tok)

    def create_state(self, sym, alt, num, col): return State(sym, alt, num, col)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we hook up our simple extractor to choose the lowest cost path.

<!--
############
class SimpleExtractor(SimpleExtractor):
    def choose_path(self, arr):
        l = len(arr)
        i = random.randrange(l)
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == 'n']
        return sum([s.penalty for s in states])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class SimpleExtractor(SimpleExtractor):
    def choose_path(self, arr):
        l = len(arr)
        i = random.randrange(l)
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == &#x27;n&#x27;]
        return sum([s.penalty for s in states])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
ie3 = SimpleExtractor(EarleyParser(covering_grammar), '1+1+', covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie3.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ie3 = SimpleExtractor(EarleyParser(covering_grammar), &#x27;1+1+&#x27;, covering_start, covering_grammar[covering_start][0])
for i in range(3):
    tree = ie3.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Caution, this command will take time. 30 seconds in Mac Book Pro.

<!--
############
if False:
    covering_grammar, covering_start = augment_grammar(grammar, START, Symbols=[i for i in string.printable if i not in '\n\r\t\x0b\x0c'])
    ie4 = SimpleExtractor(EarleyParser(covering_grammar), 'x+y', covering_start, covering_grammar[covering_start][0])
    for i in range(3):
        tree = ie4.extract_a_tree()
        print(tree_to_str(tree))
        print(format_parsetree(tree))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
if False:
    covering_grammar, covering_start = augment_grammar(grammar, START, Symbols=[i for i in string.printable if i not in &#x27;\n\r\t\x0b\x0c&#x27;])
    ie4 = SimpleExtractor(EarleyParser(covering_grammar), &#x27;x+y&#x27;, covering_start, covering_grammar[covering_start][0])
    for i in range(3):
        tree = ie4.extract_a_tree()
        print(tree_to_str(tree))
        print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Why is this so slow? One reason is that, for conceptual clarity, and
generality, we opted to expand two terms from the original paper.
For example, we chose set Any_one: `<$.>` as well as
Any_not_str: `<$![.]>` as nonterminal symbols. This means that
to match `<$.>`, (say we have $$T$$ terminal symbols,) we have to carry
an extra $$T$$ symbols per each symbol -- essentially giving us $$T^2$$
extra matches to perform. For matching `<$![.]>`, the situation is worse,
we have to carry $$T^2$$ symbols per each terminal, giving $$T^3$$
matches per original terminal symbol.

Fortunately, there is an optimization possible here. We can set the
Any_one: `.` and Any_not(a): `!a` to be terminal symbols, and fix the
terminal match so that we match any character on `.` and except the given
character (e.g. `a`) on `!a`. What we lose there is generality. THat is, the
augmented context-free grammar will no longer be usable by other parsers
(unless they are augmented got match regular expressions).
We modify our Earley parser to expect these. First our strings.

<!--
############
Any_term = '$.'

Any_not_term = '!%s'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_term = &#x27;$.&#x27;

Any_not_term = &#x27;!%s&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now our parser.

<!--
############
class EarleyParser(EarleyParser):
    def match_terminal(self, rex, input_term):
        if len(rex) > 1:
            if rex == Any_term: return True
            if rex[0] == Any_not_term[0]: return rex[1] != input_term # Any not
            return False
        else: return rex == input_term # normal

    def scan(self, col, state, letter):
        if self.match_terminal(letter, col.letter):
            col.add(state.advance())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def match_terminal(self, rex, input_term):
        if len(rex) &gt; 1:
            if rex == Any_term: return True
            if rex[0] == Any_not_term[0]: return rex[1] != input_term # Any not
            return False
        else: return rex == input_term # normal

    def scan(self, col, state, letter):
        if self.match_terminal(letter, col.letter):
            col.add(state.advance())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Our grammars are augmented this way.

<!--
############
def augment_grammar_ex(g, start, Symbols=None):
    if Symbols is None:
        Symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[Any_term]]}


    Match_any_sym_except = {}
    for kk in Symbols:
        Match_any_sym_except[Any_not(kk)] = [[Any_not_term % kk]]
    Match_empty = {Empty: []}

    Match_a_sym = {}
    for kk in Symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(g, start)
    return {**start_g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def augment_grammar_ex(g, start, Symbols=None):
    if Symbols is None:
        Symbols = [t for k in g for alt in g[k] for t in alt if not is_nt(t)]
    Match_any_sym = {Any_one: [[Any_term]]}


    Match_any_sym_except = {}
    for kk in Symbols:
        Match_any_sym_except[Any_not(kk)] = [[Any_not_term % kk]]
    Match_empty = {Empty: []}

    Match_a_sym = {}
    for kk in Symbols:
        Match_a_sym[This_sym(kk)] = [
                [kk],
                [Any_plus, kk],
                [Empty],
                [Any_not(kk)]
                ]
    start_g, start_s = add_start(g, start)
    return {**start_g,
            **translate_terminals(g),
            **Match_any_sym,
            **Match_a_sym,
            **Match_any_sym_except,
            **Match_empty}, start_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it.

<!--
############
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START)
print_g(covering_grammar_ex)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START)
print_g(covering_grammar_ex)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Testing

<!--
############
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START, Symbols=[i for i in string.printable if i not in '\n\r\t\x0b\x0c'])
ie5 = SimpleExtractor(EarleyParser(covering_grammar_ex), 'x+y', covering_start_ex, covering_grammar_ex[covering_start_ex][0])
for i in range(3):
    tree = ie5.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
covering_grammar_ex, covering_start_ex = augment_grammar_ex(grammar, START, Symbols=[i for i in string.printable if i not in &#x27;\n\r\t\x0b\x0c&#x27;])
ie5 = SimpleExtractor(EarleyParser(covering_grammar_ex), &#x27;x+y&#x27;, covering_start_ex, covering_grammar_ex[covering_start_ex][0])
for i in range(3):
    tree = ie5.extract_a_tree()
    print(tree_to_str(tree))
    print(format_parsetree(tree))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
[^aho1972minimum]: Alfred V. Aho and Thomas G. Peterson, A Minimum Distance Error-Correcting Parser for Context-Free Languages, SIAM Journal on Computing, 1972 <https://doi.org/10.1137/0201022>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
