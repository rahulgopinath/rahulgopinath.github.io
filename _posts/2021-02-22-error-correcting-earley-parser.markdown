---
published: true
title: Error Correcting Earley Parser
layout: post
comments: true
tags: parsing, error correcting, context-free
categories: post
---
**DRAFT**
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

We talked about Earley parsers [previously](/post/2021/02/06/earley-parsing/).
One of the interesting things about Earley parsers is that it also forms the
basis of best known general context-free error correcting parser. A parser is
error correcting if it is able to parse corrupt inputs that only partially
conform to a given grammar. The particular algorithm we will be examining is the
minimum distance error correcting parser by Aho et al.[^aho1972minimum].

## Covering Grammar

The idea from Aho et al. is to first transform the given grammar into a
*covering grammar*. A grammar $$G_2$$ covers another grammar $$G_1$$ if
(in essence) all productions in $$G_1$$ are in $$G_2$$, and a string that
is parsed by $$G_1$$ is guaranteed to be parsed by $$G_2$$, and all the
parses from $$G_1$$ are guaranteed to exist in the set of parses from $$G_2$$.

So, we first construct a covering grammar that can handle any corruption of
input, with the additional property that there will be a parse of the corrupt
string which contains **the minimum number of modifications needed** such that
if they are applied on the string, it will make it parsed by the original
grammar.

### First, the prerequisites

<!--
############
import random
import itertools as I
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
import itertools as I
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


### Our Grammar

<!--
############
grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],
        ['<term>']],
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
############
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
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We can also print it.



<!--
############
def print_g(g):
    for k in g:
        print(k)
        for rule in g[k]:
            print('|  ', ' '.join([str(k) for k in rule]))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def print_g(g):
    for k in g:
        print(k)
        for rule in g[k]:
            print(&#x27;|  &#x27;, &#x27; &#x27;.join([str(k) for k in rule]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



Checking whether a term is nonterminal

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

<!--
############
print(is_nt('a'))
print(is_nt('<a>'))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(is_nt(&#x27;a&#x27;))
print(is_nt(&#x27;&lt;a&gt;&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


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



Now, the covering grammar itself. The covering grammar constructed by Aho et al.
is fairly straight forward. It handles three possible mutations of the input

* The replacement of a terminal symbol by another terminal symbol
* The insertion of an extra terminal symbol
* Deletion of a terminal symbol

Any number and combinations of these mutations can accumulate in an input.
That is, in effect, *any string* can be considered a mutation of a parsable
string, and hence we can expect the covering grammar to parse it.

Now, to make sure that any string is parsable, we first define a nonterminal
that is capable of parsing any string. Now, for ease of parsing, let us define
a new terminal symbol that stands in for any terminal symbol. This stands for $$I$$
in Aho's paper.

<!--
############
Any_one = '{$.}' # this is a terminal
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_one = &#x27;{$.}&#x27; # this is a terminal
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We should be able to parse any number of such symbols. So, we define a new
nonterminal for that. This stands for $$H$$ in Aho's paper.

<!--
############
Any_plus = '<$.+>' # this is a nonterminal
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
Any_plus = &#x27;&lt;$.+&gt;&#x27; # this is a nonterminal
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

In a similar fashion, we also need a terminal symbol that will match any except
a given terminal symbol. Since this is specific to a terminal symbol, let us make
it a method.

<!--
############
def Any_not(t): return '{!%s}' % t # this is a terminal.
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def Any_not(t): return &#x27;{!%s}&#x27; % t # this is a terminal.
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Now, how do we check for match between a terminal symbol and a given input symbol?

<!--
############
def is_not(t):
    if len(t) > 1:
        if  t[1] == '!':
            return t[2]
    return None

def is_not_match(terminal, in_sym):
    l = is_not(terminal)
    if l is not None:
        return l != in_sym
    else:
        return False

def terminal_match(terminal, in_sym):
    if terminal == in_sym: return True
    # terminal can be any: <$.+> or not: <!x>
    if terminal == Any_one: return True
    if is_not_match(terminal, in_sym): return True
    return False
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def is_not(t):
    if len(t) &gt; 1:
        if  t[1] == &#x27;!&#x27;:
            return t[2]
    return None

def is_not_match(terminal, in_sym):
    l = is_not(terminal)
    if l is not None:
        return l != in_sym
    else:
        return False

def terminal_match(terminal, in_sym):
    if terminal == in_sym: return True
    # terminal can be any: &lt;$.+&gt; or not: &lt;!x&gt;
    if terminal == Any_one: return True
    if is_not_match(terminal, in_sym): return True
    return False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


Checking it



<!--
############
print(terminal_match('a', 'a'))
print(terminal_match('{$.}', 'a'))
print(terminal_match('{!a}', 'a'))
print(terminal_match('{!b}', 'a'))
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(terminal_match(&#x27;a&#x27;, &#x27;a&#x27;))
print(terminal_match(&#x27;{$.}&#x27;, &#x27;a&#x27;))
print(terminal_match(&#x27;{!a}&#x27;, &#x27;a&#x27;))
print(terminal_match(&#x27;{!b}&#x27;, &#x27;a&#x27;))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Now, we need to transform our grammar. Essentially, the idea is
that for each terminal symbol in the grammar, we add a
nonterminal symbol that handles the following possibilities

* The terminal is matched exactly as provided with a symbol in input
* The symbol that matches terminal is replaced by something else in the input, which means another symbol instead of the expected one
* Some junk symbols are present before the symbol that matches the given terminal
* The expected symbol was deleted from input string

That is, given `a` is a terminal symbol, we add the following

* `E_a -> a`
* `E_a -> b  | b != a`
* `E_a -> H a`
* `E_a -> {empty}`

<!--
############
def to_term(t): return '<$ %s>' % t

def fix_terminal(g, t):
    nt_t = to_term(t)
    if nt_t not in g:
        g[nt_t] = [ # Any_plus already has at least 1 weight.
                add_penalty([t], 0),
                add_penalty([Any_plus, t], 0),
                add_penalty([], 1),
                add_penalty([Any_not(t)], 1)
        ]


def change_t(t):
    if is_nt(t):
        return t
    else:
        return to_term(t)

def fix_weighted_terminals(g):
    keys = [k for k in g]
    for k in keys:
        for alt,w in g[k]:
            for t in alt:
                if t not in g:
                    fix_terminal(g, t)

    g_ = {}
    for k in g:
        if k[1] == '$':
            g_[k] = g[k]
        else:
            g_[k] = [(tuple([change_t(a) for a in alt]),w) for (alt,w) in g[k]]
    return g_
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_term(t): return &#x27;&lt;$ %s&gt;&#x27; % t

def fix_terminal(g, t):
    nt_t = to_term(t)
    if nt_t not in g:
        g[nt_t] = [ # Any_plus already has at least 1 weight.
                add_penalty([t], 0),
                add_penalty([Any_plus, t], 0),
                add_penalty([], 1),
                add_penalty([Any_not(t)], 1)
        ]


def change_t(t):
    if is_nt(t):
        return t
    else:
        return to_term(t)

def fix_weighted_terminals(g):
    keys = [k for k in g]
    for k in keys:
        for alt,w in g[k]:
            for t in alt:
                if t not in g:
                    fix_terminal(g, t)

    g_ = {}
    for k in g:
        if k[1] == &#x27;$&#x27;:
            g_[k] = g[k]
        else:
            g_[k] = [(tuple([change_t(a) for a in alt]),w) for (alt,w) in g[k]]
    return g_
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>




<!--
############

def new_start(old_start):
    old_start_ = old_start[1:-1]
    return '<$%s>' % old_start_

def add_any(g):
    g[Any_plus] = [
            add_penalty([Any_plus, Any_one], 1),
            add_penalty([Any_one], 1)]
    return g

def add_start(g, old_start):
    alts = [alt for alt,w in g[old_start]]
    for alt in alts:
        g[old_start].append(add_penalty(list(alt) + ['<$ .+>'], 0))
    return g

def add_penalty(rule, weight):
    assert isinstance(rule, list)
    return [tuple(rule), weight]

def add_weights_to_grammar(g):
    return {k:[add_penalty(rule, 0) for rule in g[k]] for k in g}
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>

def new_start(old_start):
    old_start_ = old_start[1:-1]
    return &#x27;&lt;$%s&gt;&#x27; % old_start_

def add_any(g):
    g[Any_plus] = [
            add_penalty([Any_plus, Any_one], 1),
            add_penalty([Any_one], 1)]
    return g

def add_start(g, old_start):
    alts = [alt for alt,w in g[old_start]]
    for alt in alts:
        g[old_start].append(add_penalty(list(alt) + [&#x27;&lt;$ .+&gt;&#x27;], 0))
    return g

def add_penalty(rule, weight):
    assert isinstance(rule, list)
    return [tuple(rule), weight]

def add_weights_to_grammar(g):
    return {k:[add_penalty(rule, 0) for rule in g[k]] for k in g}

</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
g_e = add_weights_to_grammar(grammar)
print_g(g_e)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g_e = add_weights_to_grammar(grammar)
print_g(g_e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
g_e = fix_weighted_terminals(g_e)
print_g(g_e)
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g_e = fix_weighted_terminals(g_e)
print_g(g_e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>








<!--
############
class Column:
    def __init__(self, index, letter):
        self.index, self.letter = index, letter
        self.states, self._unique = [], {}

    def __str__(self):
        return "%s chart[%d]\n%s" % (self.letter, self.index, "\n".join(
            str(state) for state in self.states if state.finished()))

    def add(self, state):
        if state in self._unique:
            if self._unique[state].weight > state.weight:
                # delete from self.states in fill_chart
                state.e_col = self
                self.states.append(state)
                self._unique[state] = state
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]

    def remove_extra_states(self):
        my_states = []
        for state in self._unique:
            cur_states = [s for s in self.states if s == state]
            if len(cur_states) > 1:
                cur_states = sorted(cur_states, key=lambda s: s.weight)
            my_states.append(cur_states[0])
        self.states = my_states
        return


class State:
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr_, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        self.expr, self.weight = expr

    def finished(self):
        return self.dot >= len(self.expr)

    def at_dot(self):
        return self.expr[self.dot] if self.dot < len(self.expr) else None

    def __str__(self):
        def idx(var):
            return var.index if var else -1

        return self.name + ':= ' + ' '.join([
            str(p)
            for p in [*self.expr[:self.dot], '|', *self.expr[self.dot:]]
            ]) + "(%d,%d):%d" % (idx(self.s_col), idx(self.e_col), self.weight)

    def copy(self):
        return State(self.name, (self.expr, self.weight), self.dot, self.s_col, self.e_col)

    def _t(self):
        return (self.name, self.expr, self.dot, self.s_col.index)

    def __hash__(self):
        return hash(self._t())

    def __eq__(self, other):
        return self._t() == other._t()

    def advance(self):
        return State(self.name, (self.expr, self.weight), self.dot + 1, self.s_col)

class Parser:
    def parse_on(self, text, start_symbol):
        raise NotImplemented()

class EarleyParser(Parser):
    def __init__(self, grammar, log=False, **kwargs):
        g_e = add_weights_to_grammar(grammar)
        # need to update terminals
        g_e = fix_weighted_terminals(g_e)
        self.epsilon = nullable(grammar)
        self._grammar = g_e
        self.log = log

        self._grammar = add_any(self._grammar)

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


class EarleyParser(EarleyParser):
    def chart_parse(self, tokens, start, alt):
        chart = [Column(i, tok) for i, tok in enumerate([None, *tokens])]
        chart[0].add(State(start, alt, 0, chart[0]))
        return self.fill_chart(chart)


class EarleyParser(EarleyParser):
    def predict(self, col, sym, state):
        for alt in self._grammar[sym]:
            col.add(State(sym, alt, 0, col))
        if sym in self.epsilon:
            col.add(state.advance())

class EarleyParser(EarleyParser):
    def scan(self, col, state, letter):
        if terminal_match(letter, col.letter):
            s = state.advance()
            s.expr = col.letter
            col.add(s)

class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        for st in parent_states:
            s = st.advance()
            s.weight += state.weight
            col.add(s)

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

class EarleyParser(EarleyParser):
    def parse_prefix(self, text, start_symbol, alt):
        self.table = self.chart_parse(text, start_symbol, alt)
        for col in reversed(self.table):
            states = [st for st in col.states
                if st.name == start_symbol and st.expr == alt[0] and st.s_col.index == 0
            ]
            if states:
                return col.index, states
        return -1, []

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
                        't')] if til > 0 and chart[til].letter == var else [])
        else:
            starts = [(s, s.s_col.index, 'n') for s in chart[til].states
                      if s.finished() and s.name == var]

        return [p for s, start, k in starts for p in paths(s, start, k, expr)]


class EarleyParser(EarleyParser):
    def forest(self, s, kind, chart):
        return self.parse_forest(chart, s) if kind == 'n' else (s, [])

    def parse_forest(self, chart, state):
        pathexprs = self.parse_paths(state.expr, chart, state.s_col.index,
                                     state.e_col.index) if state.expr else []
        return state.name, [[(v, k, chart) for v, k in reversed(pathexpr)]
                            for pathexpr in pathexprs]

class EarleyParser(EarleyParser):
    def parse_on(self, text, start_symbol):
        self._grammar = add_start(self._grammar, start_symbol)
        print_g(self._grammar)

        for alt in self._grammar[start_symbol]:
            cursor, states = self.parse_prefix(text, start_symbol, alt)
            start = next((s for s in states if s.finished()), None)

            if cursor < len(text) or not start:
                #raise SyntaxError("at " + repr(text[cursor:]))
                continue
            forest = self.parse_forest(self.table, start)
            print('weight = ', str(start))
            yield forest
            #for tree in self.extract_trees(forest):
            #    yield tree

class EarleyParser(EarleyParser):
    def extract_a_tree(self, forest_node):
        name, paths = forest_node
        if not paths:
            return (name, [])
        return (name, [self.extract_a_tree(self.forest(*p)) for p in paths[0]])


    def extract_trees(self, forest):
        yield self.extract_a_tree(forest)

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


class SimpleExtractor:
    def __init__(self, parser, text, start_symbol):
        parser._grammar = add_start(parser._grammar, start_symbol)
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol, parser._grammar[start_symbol][0])
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
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == 'n']
        return sum([s.weight for s in states])

    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree

############
-->


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
            if self._unique[state].weight &gt; state.weight:
                # delete from self.states in fill_chart
                state.e_col = self
                self.states.append(state)
                self._unique[state] = state
            return self._unique[state]
        self._unique[state] = state
        self.states.append(state)
        state.e_col = self
        return self._unique[state]

    def remove_extra_states(self):
        my_states = []
        for state in self._unique:
            cur_states = [s for s in self.states if s == state]
            if len(cur_states) &gt; 1:
                cur_states = sorted(cur_states, key=lambda s: s.weight)
            my_states.append(cur_states[0])
        self.states = my_states
        return


class State:
    def __init__(self, name, expr, dot, s_col, e_col=None):
        self.name, self.expr_, self.dot = name, expr, dot
        self.s_col, self.e_col = s_col, e_col
        self.expr, self.weight = expr

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
            ]) + &quot;(%d,%d):%d&quot; % (idx(self.s_col), idx(self.e_col), self.weight)

    def copy(self):
        return State(self.name, (self.expr, self.weight), self.dot, self.s_col, self.e_col)

    def _t(self):
        return (self.name, self.expr, self.dot, self.s_col.index)

    def __hash__(self):
        return hash(self._t())

    def __eq__(self, other):
        return self._t() == other._t()

    def advance(self):
        return State(self.name, (self.expr, self.weight), self.dot + 1, self.s_col)

class Parser:
    def parse_on(self, text, start_symbol):
        raise NotImplemented()

class EarleyParser(Parser):
    def __init__(self, grammar, log=False, **kwargs):
        g_e = add_weights_to_grammar(grammar)
        # need to update terminals
        g_e = fix_weighted_terminals(g_e)
        self.epsilon = nullable(grammar)
        self._grammar = g_e
        self.log = log

        self._grammar = add_any(self._grammar)

def is_nt(k):
    if len(k) == 1: return False
    return (k[0], k[-1]) == (&#x27;&lt;&#x27;, &#x27;&gt;&#x27;)

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


class EarleyParser(EarleyParser):
    def chart_parse(self, tokens, start, alt):
        chart = [Column(i, tok) for i, tok in enumerate([None, *tokens])]
        chart[0].add(State(start, alt, 0, chart[0]))
        return self.fill_chart(chart)


class EarleyParser(EarleyParser):
    def predict(self, col, sym, state):
        for alt in self._grammar[sym]:
            col.add(State(sym, alt, 0, col))
        if sym in self.epsilon:
            col.add(state.advance())

class EarleyParser(EarleyParser):
    def scan(self, col, state, letter):
        if terminal_match(letter, col.letter):
            s = state.advance()
            s.expr = col.letter
            col.add(s)

class EarleyParser(EarleyParser):
    def complete(self, col, state):
        parent_states = [st for st in state.s_col.states
                 if st.at_dot() == state.name]
        for st in parent_states:
            s = st.advance()
            s.weight += state.weight
            col.add(s)

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

class EarleyParser(EarleyParser):
    def parse_prefix(self, text, start_symbol, alt):
        self.table = self.chart_parse(text, start_symbol, alt)
        for col in reversed(self.table):
            states = [st for st in col.states
                if st.name == start_symbol and st.expr == alt[0] and st.s_col.index == 0
            ]
            if states:
                return col.index, states
        return -1, []

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


class EarleyParser(EarleyParser):
    def forest(self, s, kind, chart):
        return self.parse_forest(chart, s) if kind == &#x27;n&#x27; else (s, [])

    def parse_forest(self, chart, state):
        pathexprs = self.parse_paths(state.expr, chart, state.s_col.index,
                                     state.e_col.index) if state.expr else []
        return state.name, [[(v, k, chart) for v, k in reversed(pathexpr)]
                            for pathexpr in pathexprs]

class EarleyParser(EarleyParser):
    def parse_on(self, text, start_symbol):
        self._grammar = add_start(self._grammar, start_symbol)
        print_g(self._grammar)

        for alt in self._grammar[start_symbol]:
            cursor, states = self.parse_prefix(text, start_symbol, alt)
            start = next((s for s in states if s.finished()), None)

            if cursor &lt; len(text) or not start:
                #raise SyntaxError(&quot;at &quot; + repr(text[cursor:]))
                continue
            forest = self.parse_forest(self.table, start)
            print(&#x27;weight = &#x27;, str(start))
            yield forest
            #for tree in self.extract_trees(forest):
            #    yield tree

class EarleyParser(EarleyParser):
    def extract_a_tree(self, forest_node):
        name, paths = forest_node
        if not paths:
            return (name, [])
        return (name, [self.extract_a_tree(self.forest(*p)) for p in paths[0]])


    def extract_trees(self, forest):
        yield self.extract_a_tree(forest)

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


class SimpleExtractor:
    def __init__(self, parser, text, start_symbol):
        parser._grammar = add_start(parser._grammar, start_symbol)
        self.parser = parser
        cursor, states = parser.parse_prefix(text, start_symbol, parser._grammar[start_symbol][0])
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
        res = sorted([(self.cost_of_path(a),a) for a in arr], key=lambda a: a[0])
        return res[0][1], None, None

    def cost_of_path(self, p):
        states = [s for s,kind,chart in p if kind == &#x27;n&#x27;]
        return sum([s.weight for s in states])

    def extract_a_tree(self):
        pos_tree, parse_tree = self.extract_a_node(self.my_forest)
        return parse_tree
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>



<!--
############
class O:
    def __init__(self, **keys): self.__dict__.update(keys)
    def __repr__(self): return str(self.__dict__)

Options = O(F='|', L='+', V='|', H='-', NL='\n')

def format_newlines(prefix, formatted_node):
    replacement = ''.join([Options.NL, '\n', prefix])
    return formatted_node.replace('\n', replacement)

def format_tree(node, format_node, get_children, prefix=''):
    children = list(get_children(node))
    next_prefix = ''.join([prefix, Options.V, '   '])
    for child in children[:-1]:
        fml = format_newlines(next_prefix, format_node(child))
        yield ''.join([prefix, Options.F, Options.H, Options.H, ' ', fml])
        tree = format_tree(child, format_node, get_children, next_prefix)
        for result in tree:
            yield result
    if children:
        last_prefix = ''.join([prefix, '    '])
        fml = format_newlines(last_prefix, format_node(children[-1]))
        yield ''.join([prefix, Options.L, Options.H, Options.H, ' ', fml])
        tree = format_tree(children[-1], format_node, get_children, last_prefix)
        for result in tree:
            yield result

def format_parsetree(node,
          format_node=lambda x: repr(x[0]),
          get_children=lambda x: x[1]):
    lines = I.chain([format_node(node)], format_tree(node, format_node, get_children), [''],)
    return '\n'.join(lines)


# Modifications:
# Each rule gets a weight
# The start gets changed to:
# <$start>  := [0] <start>
#            | [0] <start> <$.+>
# <$.+>     := [1] <$.+> <$.>
#            | [1] <$.>
# Each terminal gets converted to a nonterminal

#ep = EarleyParser(grammar, log=False)
#cursor, columns = ep.parse_prefix('0', START, add_penalty(grammar[START][0], 0))
#print(cursor)
#for c in columns:
#    print(c)


myg = EarleyParser(grammar)
inp = 'xz+yz'
print(repr(inp))
x = SimpleExtractor(myg, inp, START)
t = x.extract_a_tree()
print(format_parsetree(t))
#forests = myg.parse_on(inp, START)
#for forest in forests:
#    print('parse:', inp)
#    for v in myg.extract_trees(forest):
#        print(format_parsetree(v))
#        print('||||||||||||||||||\n')
############
-->


<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
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

def format_parsetree(node,
          format_node=lambda x: repr(x[0]),
          get_children=lambda x: x[1]):
    lines = I.chain([format_node(node)], format_tree(node, format_node, get_children), [&#x27;&#x27;],)
    return &#x27;\n&#x27;.join(lines)


# Modifications:
# Each rule gets a weight
# The start gets changed to:
# &lt;$start&gt;  := [0] &lt;start&gt;
#            | [0] &lt;start&gt; &lt;$.+&gt;
# &lt;$.+&gt;     := [1] &lt;$.+&gt; &lt;$.&gt;
#            | [1] &lt;$.&gt;
# Each terminal gets converted to a nonterminal

#ep = EarleyParser(grammar, log=False)
#cursor, columns = ep.parse_prefix(&#x27;0&#x27;, START, add_penalty(grammar[START][0], 0))
#print(cursor)
#for c in columns:
#    print(c)


myg = EarleyParser(grammar)
inp = &#x27;xz+yz&#x27;
print(repr(inp))
x = SimpleExtractor(myg, inp, START)
t = x.extract_a_tree()
print(format_parsetree(t))
#forests = myg.parse_on(inp, START)
#for forest in forests:
#    print(&#x27;parse:&#x27;, inp)
#    for v in myg.extract_trees(forest):
#        print(format_parsetree(v))
#        print(&#x27;||||||||||||||||||\n&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!-- XXXXXXXXXX -->

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

[^aho1972minimum]: Alfred V. Aho and Thomas G. Peterson, A Minimum Distance Error-Correcting Parser for Context-Free Languages, SIAM Journal on Computing, 1972 <https://doi.org/10.1137/0201022>


