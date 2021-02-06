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

The *Earley* parsing algorithm was invented by Jay Earley [^earley1970an] that
can be used to parse strings that conform to a context-free grammar. The
algorithm uses a chart for parsing -- that is, it is implemented as a dynamic
program relying on solving simpler sub-problems.

Earley parsers are very appealing for a practitioner because they can use any
context-free grammar for parsing a string, and from the parse forest generated,
one can recover all (even an infinite number) of parse trees that correspond to
the given grammar. Unfortunately, this style of parsing pays for generality by
being slightly expensive. It takes $$O(n^3)$$ time to parse in the worst case.
This an implementation of Earley parsing that handles the epsilon case as
given by Aycock et a.[^aycock2002practical].

For a much more complete implementation including Leo's optimizations[^leo1991a], and
full recovery of parsing forests using iterative solutions,
see our parsing implementation in the [fuzzingbook](https://www.fuzzingbook.org/html/Parser.html) (See the solved exercises).

As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
Here is an example grammar for arithmetic expressions, starting at `<start>`.

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


The chart parser depends on a chart (a table) for parsing. The rows are the
characters in the input string. Each column represents a set of *states*, and
corresponds to the legal rules to follow from that point on.

## Column

The column contains a set of states. Each column corresponds
to a character (or a token if tokens are used).
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

Each state contains the following:

* name: The non-terminal that this rule represents.
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


## Parser

We start with a bare minimum interface for a parser. It should allow one
to parse a given text using a given non-terminal (which should be present in
the grammar)

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Parser:
    def parse_on(self, text, start_symbol):
        cursor, forest = self.parse_prefix(text, start_symbol)
        if cursor &lt; len(text):
            raise SyntaxError(&quot;at &quot; + repr(text[cursor:]))
        return forest
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
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

#### Nullable

Earley parser handles *nullable* non-terminals separately. A nullable
non-terminal is a non-terminal that can derive an empty string. That is
at least one of the expansion rules must derive an empty string. An
expansion rule derives an empty string if *all* of the tokens can
derive the empty string. This means no terminal symbols (assuming we
do not have zero width terminal symbols), and all non-terminal symbols
can derive empty string.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def fixpoint(f):
    def helper(arg):
        while True:
            sarg = str(arg)
            arg_ = f(arg)
            if str(arg_) == sarg:
                return arg
            arg = arg_
    return helper
def rules(grammar):
    return [(key, choice)
            for key, choices in grammar.items()
            for choice in choices]
def terminals(grammar):
    return set(token
               for key, choice in rules(grammar)
               for token in choice if token not in grammar)

def nullable(grammar):
    productions = rules(grammar)

    @fixpoint
    def nullable_(nullables):
        for A, expr in productions:
            if nullable_expr(expr, nullables):
                nullables |= {A}
        return (nullables)

    return nullable_(set())

def nullable_expr(expr, nullables):
    return all(token in nullables for token in expr)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Chart construction

First, we seed the chart with columns representing the tokens or characters.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def chart_parse(self, tokens, start):
        alt = tuple(*self._grammar[start])
        chart = [Column(i, tok) for i, tok in enumerate([None, *tokens])]
        chart[0].add(State(start, alt, 0, chart[0]))
        return self.fill_chart(chart)
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
        return chart
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def parse_prefix(self, text, start_symbol):
        self.table = self.chart_parse(text, start_symbol)
        for col in reversed(self.table):
            states = [
                st for st in col.states if st.name == start_symbol
            ]
            if states:
                return col.index, states
        return -1, []
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


There are three main methods: `complete()`, `predict()`, and `scan()`

### Complete

The `complete()` method is called if a particular state has finished the rule
during execution. It first extracts the start column of the finished state, then
for all states in the start column that is not finished, find the states that
were parsing this current state (that is, we can go back to continue to parse
those rules now). Next, shift them by one position, and add them to the current
column.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [
            st for st in state.s_col.states if st.at_dot() == state.name
        ]
        for st in parent_states:
            col.add(st.advance())
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


### Predict

If the term after the dot is a non-terminal, `predict()` is called. It
adds the expansion of the non-terminal to the current column.

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


### Scan

The `scan()` method is called if the next symbol is a terminal symbol. If the
state matches the next term, moves the dot one position, and adds the new
state to the column.

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
#grammar = {
#        START: ['<S>'],
#        '<S>': ['<NP><VP>'],
#        '<PP>': ['<P><NP>'],
#        '<VP>': ['<V><NP>', '<VP><PP>'],
#        '<P>': ['with'],
#        '<V>': ['saw'],
#        '<NP>': ['<NP><PP>', '<N>'],
#        '<N>': ['astronomers', 'ears', 'stars', 'telescopes']
#        }


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

## Parse trees

We use the following procedures to translate the parse forest to individual
trees.


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class EarleyParser(EarleyParser):
    def parse_on(self, text, start_symbol):
        cursor, states = self.parse_prefix(text, start_symbol)
        start = next((s for s in states if s.finished()), None)

        if cursor &lt; len(text) or not start:
            raise SyntaxError(&quot;at &quot; + repr(text[cursor:]))

        forest = self.parse_forest(self.table, start)
        for tree in self.extract_trees(forest):
            yield tree
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

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
            for p in zip(*ptrees):
                yield (name, p) 
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


## Example
Now we are ready for parsing. 

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
text = &#x27;11+2&#x27;
ep = EarleyParser(grammar)
for tree in ep.parse_on(text, START):
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

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

[^earley1970an]: Earley, Jay. "An efficient context-free parsing algorithm." Communications of the ACM 13.2 (1970): 94-102.

[^leo1991a]: Leo, Joop MIM. "A general context-free parsing algorithm running in linear time on every LR (k) grammar without using lookahead." Theoretical computer science 82.1 (1991): 165-176.

[^aycock2002practical]: Aycock, John, and R. Nigel Horspool. "Practical earley parsing." The Computer Journal 45.6 (2002): 620-630.
