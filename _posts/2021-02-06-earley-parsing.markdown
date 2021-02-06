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
This an implementation of Earley parsing that handles the epsilon case.

For a much more complete implementation including Leo's fixes[^leo1991a], and
full recovery of parsing forests, see our parsing implementation in the [fuzzingbook](https://www.fuzzingbook.org/html/Parser.html) (See the solved exercises).

As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
Here is an example grammar for arithmetic expressions, starting at `<start>`.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
 &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;expr&gt;&#x27;]],
 &#x27;&lt;expr&gt;&#x27;: [[&#x27;&lt;term&gt;&#x27;, &#x27;&lt;expr_&gt;&#x27;]],
 &#x27;&lt;expr_&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;-&#x27;, &#x27;&lt;expr&gt;&#x27;], [&#x27;&#x27;]],
 &#x27;&lt;term&gt;&#x27;: [[&#x27;&lt;factor&gt;&#x27;, &#x27;&lt;term_&gt;&#x27;]],
 &#x27;&lt;term_&gt;&#x27;: [[&#x27;*&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;/&#x27;, &#x27;&lt;term&gt;&#x27;], [&#x27;&#x27;]],
 &#x27;&lt;factor&gt;&#x27;: [[&#x27;+&#x27;, &#x27;&lt;factor&gt;&#x27;],
  [&#x27;-&#x27;, &#x27;&lt;factor&gt;&#x27;],
  [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
  [&#x27;&lt;int&gt;&#x27;]],
 &#x27;&lt;int&gt;&#x27;: [[&#x27;&lt;integer&gt;&#x27;, &#x27;&lt;integer_&gt;&#x27;]],
 &#x27;&lt;integer_&gt;&#x27;: [[&#x27;&#x27;], [&#x27;.&#x27;, &#x27;&lt;integer&gt;&#x27;]],
 &#x27;&lt;integer&gt;&#x27;: [[&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;I&gt;&#x27;]],
 &#x27;&lt;I&gt;&#x27;: [[&#x27;&lt;integer&gt;&#x27;], [&#x27;&#x27;]],
 &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;],
  [&#x27;1&#x27;],
  [&#x27;2&#x27;],
  [&#x27;3&#x27;],
  [&#x27;4&#x27;],
  [&#x27;5&#x27;],
  [&#x27;6&#x27;],
  [&#x27;7&#x27;],
  [&#x27;8&#x27;],
  [&#x27;9&#x27;]]}
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


The chart parser depends on a chart (a table) for parsing. The rows are the
characters in the input string. Each column represents a set of *states*, and
corresponds to the legal rules to follow from that point on.

## State

Each state contains the following:

* name: The non-terminal that this rule represents.
* expr: The rule that is being followed
* dot:  The point till which parsing has happened in the rule.
* start_column: The starting point for this rule.
* children: Child states if any.

We use a global `counter` so that it is easier to keep track of the different
states.
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
counter = 0
class State:
    def __init__(self, name, expr, dot, start_column):
        global counter
        self.name, self.expr, self.dot, self.start_column, self.children = name, expr, dot, start_column, []
        self.c = counter
        counter += 1
    def finished(self): return self.dot &gt;= len(self.expr)
    def shift(self, bp=None):
        s = State(self.name, self.expr, self.dot+1, self.start_column)
        s.children = self.children[:]
        return s
    def symbol(self): return self.expr[self.dot]

    def _t(self): return (self.name, self.expr, self.dot, self.start_column)
    def __hash__(self): return hash((self.name, self.expr))
    def __eq__(self, other): return  self._t() == other._t()
    def __str__(self): return (&quot;(S%d)   &quot; % self.c) + self.name +&#x27;:= &#x27;+ &#x27; &#x27;.join([str(p) for p in [*self.expr[:self.dot],&#x27;|&#x27;, *self.expr[self.dot:]]])
    def __repr__(self): return str(self)
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Column

The column contains a set of states. Each column corresponds
to a character (or a token if tokens are used). We also define
`show_col()` to make it easier to debug.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Column:
    def __init__(self, i, token):
        self.token, self.states, self._unique = token, [], {}
        self.i = i
    def add(self, state, bp=None):
        if state in self._unique:
            if bp: state.children.append(bp)
            return
        self._unique[state] = state
        if bp: state.children.append(bp)
        self.states.append(state)
    def __repr__(self):
        return &quot;%s chart[%d] %s&quot; % (self.token, self.i, str(self.states))

def show_col(col, i):
    print(&quot;chart[%d]&quot;%i)
    for state in col.states:
        print(state, &quot;\t&quot;, [s.c for s in state.children])
    print()
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

## Parsing

There are three main methods: `complete()`, `predict()`, and `scan()`

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def parse(words, grammar, start):
    alt = tuple(*grammar[start])
    chart = [Column(i,tok) for i,tok in enumerate([None, *words])]
    chart[0].add(State(start, alt, 0, chart[0]))

    for i, col in enumerate(chart):
        for state in col.states:
            if state.finished():
                complete(col, state, grammar)
            else:
                sym = state.symbol()
                if sym in grammar:
                    predict(col, sym, grammar)
                else:
                    if i + 1 &gt;= len(chart): continue
                    scan(chart[i+1], state, sym)
    return chart
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

### Complete

The `complete()` method is called if a particular state has finished the rule
during execution. It first extracts the start column of the finished state, then
for all states in the start column that is not finished, find the states that
were parsing this current state (that is, we can go back to continue to parse
those rules now). Next, shift them by one position, and add them to the current
column.

<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def complete(col, state, grammar):
    for st in state.start_column.states:
        if st.finished(): continue
        sym = st.symbol()
        if state.name != sym: continue
        assert sym in grammar
        col.add(st.shift(), state)
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
def predict(col, sym, grammar):
    for alt in grammar[sym]:
        if is_empty(alt):
            col.add(State(sym, tuple([]), 0, col))
        else:
            col.add(State(sym, tuple(alt), 0, col))

def is_empty(a): return a == [&#x27;&#x27;]
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
def scan(col, state, token):
    if token == col.token:
        col.add(state.shift())
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
def process_expr(expr, children, grammar):
    lst = []
    nt_counter = 0
    for i in expr:
        if i not in grammar:
            lst.append((i,[]))
        else:
            lst.append(node_translator(children[nt_counter], grammar))
            nt_counter += 1
    return lst

def node_translator(state, grammar):
    return (state.name, process_expr(state.expr, state.children, grammar))
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
table = parse(list(text), grammar, START)
state, *states = [st for st in table[-1].states if st.name == START and st.finished()]
assert not states
trees = [node_translator(state, grammar)]
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
for tree in trees:
    print(format_parsetree(tree, format_node=lambda x: repr(x[0]), get_children=lambda x: x[1]))

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

