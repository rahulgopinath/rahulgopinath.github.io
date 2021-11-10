---
published: true
title: Semantic Testcase Reducer
layout: post
comments: true
tags: deltadebug, testcase reducer, cfg, generator
categories: post
---
 
Previously, we had [discussed](/post/2019/12/03/ddmin/) how delta-debugging worked, and I had explained at that time that when it comes
to preserving semantics, the only options are either custom passes such as [CReduce](http://embed.cs.utah.edu/creduce/)
or commandeering the generator as done by [Hypothesis](https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis-python/src/hypothesis/internal/conjecture/shrinker.py).
Of the two, the Hypothesis approach is actually more generalizable to arbitrary generators. Hence we will look at how it is done. For ease
of naming, I will call this approach the _generator reduction_ approach. Note that we use the simple `delta debug` on the choice sequences.
This is different from `Hypothesis` in that `Hypothesis` uses a number of custom passes rather than `delta debug`. For further information
on Hypothesis, please see the paper by MacIver et al.[^mciver2020reduction] at ECOOP.

For the _generator reduction_ to work, we need a generator in the first place. So, we start with a rather simple generator that we discussed [previously](/post/2019/05/28/simplefuzzer-01/).
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

<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
"https://rahul.gopinath.org/py/simplefuzer-0.0.1-py2.py3-none-any.whl"
</textarea>
</form>

<!--
############
import simplefuzzer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We have a grammar describes a simple assignment language.

<!--
############
import random
import string
import sys

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import random
import string
import sys
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using this grammar.

<!--
############
import textwrap
assignment_grammar = {
        '<start>' : [[ '<assignments>' ]],
        '<assignments>': [['<assign>'],
                          ['<assign>', ';\n', '<assignments>']],
        '<assign>': [['<var>', ' = ', '<expr>']],
        '<expr>': [
            ['<expr>', ' + ', '<expr>'],
            ['<expr>', ' - ', '<expr>'],
            ['(', '<expr>', ')'],
            ['<var>'],
            ['<digit>']],
        '<digit>': [['0'], ['1']],
        '<var>': [[i] for i in string.ascii_lowercase]
}
# doing exec because we want to correctly init random seeds.
lf_mystr = """\
import random
random.seed(seed)
c = simplefuzzer.LimitFuzzer(assignment_grammar)
print(c.fuzz('<start>'))
"""
lf_mystr = textwrap.dedent(lf_mystr)
exec(lf_mystr,
        {'simplefuzzer': simplefuzzer, 'assignment_grammar': assignment_grammar},
        {'seed': 5})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import textwrap
assignment_grammar = {
        &#x27;&lt;start&gt;&#x27; : [[ &#x27;&lt;assignments&gt;&#x27; ]],
        &#x27;&lt;assignments&gt;&#x27;: [[&#x27;&lt;assign&gt;&#x27;],
                          [&#x27;&lt;assign&gt;&#x27;, &#x27;;\n&#x27;, &#x27;&lt;assignments&gt;&#x27;]],
        &#x27;&lt;assign&gt;&#x27;: [[&#x27;&lt;var&gt;&#x27;, &#x27; = &#x27;, &#x27;&lt;expr&gt;&#x27;]],
        &#x27;&lt;expr&gt;&#x27;: [
            [&#x27;&lt;expr&gt;&#x27;, &#x27; + &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;&lt;expr&gt;&#x27;, &#x27; - &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
            [&#x27;&lt;var&gt;&#x27;],
            [&#x27;&lt;digit&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;1&#x27;]],
        &#x27;&lt;var&gt;&#x27;: [[i] for i in string.ascii_lowercase]
}
# doing exec because we want to correctly init random seeds.
lf_mystr = &quot;&quot;&quot;\
import random
random.seed(seed)
c = simplefuzzer.LimitFuzzer(assignment_grammar)
print(c.fuzz(&#x27;&lt;start&gt;&#x27;))
&quot;&quot;&quot;
lf_mystr = textwrap.dedent(lf_mystr)
exec(lf_mystr,
        {&#x27;simplefuzzer&#x27;: simplefuzzer, &#x27;assignment_grammar&#x27;: assignment_grammar},
        {&#x27;seed&#x27;: 5})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The context free grammar `assignment_grammar` generates assignment expressions. However, it tends to
use variables before they are defined. We want to avoid that. However, using only defined variables is a context sensitive feature, which we incorporate
by a small modification to the fuzzer.

<!--
############
class ComplexFuzzer(simplefuzzer.LimitFuzzer):
    def __init__(self, grammar):
        def cfg(g):
            return {k: [self.cfg_rule(r) for r in g[k]] for k in g}
        super().__init__(cfg(grammar))
        self.cfg_grammar = self.grammar
        self.grammar = grammar
        self.vars = []
        self._vars = []

    def select(self, lst):
        return random.choice(lst)

    def tree_to_str(self, val):
        return simplefuzzer.tree_to_string(val)

    def cfg_rule(self, rule):
        return [t[0] if isinstance(t, tuple) else t for t in rule]

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule) for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return (key, self.gen_rule(self.select(rules), depth+1, max_depth))

    def gen_rule(self, rule, depth, max_depth):
        ret = []
        for token_ in rule:
            if isinstance(token_, tuple):
                token = token_[0]
                fns = token_[1]
            else:
                token = token_
                fns = {}

            pre = fns.get('pre', lambda s, t, x: x())
            post = fns.get('post', lambda s, x: x)
            val = pre(self, token, lambda: self.gen_key(token, depth, max_depth))
            v = post(self, val)
            ret.append(v)
        return ret

    def fuzz(self, key='<start>', max_depth=10):
        return self.tree_to_str(self.gen_key(key=key, depth=0, max_depth=max_depth))

def defining_var(o, val):
    v = o.tree_to_str(val)
    o._vars.append(v)
    return val

def defined_var(o, token, val):
    assert token == '<var>'
    #v = val()
    if not o.vars:
        return ('00', [])
    else:
        return (o.select(o.vars), [])

def sync(o, val):
    o.vars.extend(o._vars)
    o._vars.clear()
    return val

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ComplexFuzzer(simplefuzzer.LimitFuzzer):
    def __init__(self, grammar):
        def cfg(g):
            return {k: [self.cfg_rule(r) for r in g[k]] for k in g}
        super().__init__(cfg(grammar))
        self.cfg_grammar = self.grammar
        self.grammar = grammar
        self.vars = []
        self._vars = []

    def select(self, lst):
        return random.choice(lst)

    def tree_to_str(self, val):
        return simplefuzzer.tree_to_string(val)

    def cfg_rule(self, rule):
        return [t[0] if isinstance(t, tuple) else t for t in rule]

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth &gt; max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule) for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return (key, self.gen_rule(self.select(rules), depth+1, max_depth))

    def gen_rule(self, rule, depth, max_depth):
        ret = []
        for token_ in rule:
            if isinstance(token_, tuple):
                token = token_[0]
                fns = token_[1]
            else:
                token = token_
                fns = {}

            pre = fns.get(&#x27;pre&#x27;, lambda s, t, x: x())
            post = fns.get(&#x27;post&#x27;, lambda s, x: x)
            val = pre(self, token, lambda: self.gen_key(token, depth, max_depth))
            v = post(self, val)
            ret.append(v)
        return ret

    def fuzz(self, key=&#x27;&lt;start&gt;&#x27;, max_depth=10):
        return self.tree_to_str(self.gen_key(key=key, depth=0, max_depth=max_depth))

def defining_var(o, val):
    v = o.tree_to_str(val)
    o._vars.append(v)
    return val

def defined_var(o, token, val):
    assert token == &#x27;&lt;var&gt;&#x27;
    #v = val()
    if not o.vars:
        return (&#x27;00&#x27;, [])
    else:
        return (o.select(o.vars), [])

def sync(o, val):
    o.vars.extend(o._vars)
    o._vars.clear()
    return val
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We now allow only defined variables to be used for later expansion. The helper procedures `defining_var` is invoked
when we produce the left hand side of the variable assignment, and the `defined_var` is invoked when the variable is
referred to from the right hand side. Hence `defined_var` ensures only defined vars are used. The `sync` function
ensures that the definition is complete only when the assignment is finished.

Note that the modifications assume the knowledge of the `<var>`  key in the grammar defined in the driver.

The driver now includes a context sensitive grammar in the form of `pre` and `post` functions.

<!--
############
assignment_grammar1 = {
        '<start>' : [[ '<assignments>' ]],
        '<assignments>': [['<assign>', (';\n', {'post':sync})],
                          ['<assign>', (';\n', {'post':sync}), '<assignments>']],
        '<assign>': [[('<var>', {'post':defining_var}), ' = ', '<expr>']],
        '<expr>': [
            ['<expr>', ' + ', '<expr>'],
            ['<expr>', ' - ', '<expr>'],
            ['(', '<expr>', ')'],
            [('<var>', {'pre':defined_var})],
            ['<digit>']],
        '<digit>': [['0'], ['1']],
        '<var>': [[i] for i in string.ascii_lowercase]
}
lf1_mystr = """\
import random
random.seed(seed)
c = ComplexFuzzer(assignment_grammar1)
print(c.fuzz('<start>'))
print(c.vars)
"""
lf1_mystr = textwrap.dedent(lf1_mystr)
print()
exec(lf1_mystr,
        {'ComplexFuzzer':ComplexFuzzer, 'assignment_grammar1':assignment_grammar1},
        {'seed': 6})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
assignment_grammar1 = {
        &#x27;&lt;start&gt;&#x27; : [[ &#x27;&lt;assignments&gt;&#x27; ]],
        &#x27;&lt;assignments&gt;&#x27;: [[&#x27;&lt;assign&gt;&#x27;, (&#x27;;\n&#x27;, {&#x27;post&#x27;:sync})],
                          [&#x27;&lt;assign&gt;&#x27;, (&#x27;;\n&#x27;, {&#x27;post&#x27;:sync}), &#x27;&lt;assignments&gt;&#x27;]],
        &#x27;&lt;assign&gt;&#x27;: [[(&#x27;&lt;var&gt;&#x27;, {&#x27;post&#x27;:defining_var}), &#x27; = &#x27;, &#x27;&lt;expr&gt;&#x27;]],
        &#x27;&lt;expr&gt;&#x27;: [
            [&#x27;&lt;expr&gt;&#x27;, &#x27; + &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;&lt;expr&gt;&#x27;, &#x27; - &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
            [(&#x27;&lt;var&gt;&#x27;, {&#x27;pre&#x27;:defined_var})],
            [&#x27;&lt;digit&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;1&#x27;]],
        &#x27;&lt;var&gt;&#x27;: [[i] for i in string.ascii_lowercase]
}
lf1_mystr = &quot;&quot;&quot;\
import random
random.seed(seed)
c = ComplexFuzzer(assignment_grammar1)
print(c.fuzz(&#x27;&lt;start&gt;&#x27;))
print(c.vars)
&quot;&quot;&quot;
lf1_mystr = textwrap.dedent(lf1_mystr)
print()
exec(lf1_mystr,
        {&#x27;ComplexFuzzer&#x27;:ComplexFuzzer, &#x27;assignment_grammar1&#x27;:assignment_grammar1},
        {&#x27;seed&#x27;: 6})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, the variables used are only those that were defined earlier. So, how do we minimize such a generated string?

For the answer, we need to modify our fuzzer a bit more. We need to make it take a stream of integers which are interpreted as the choices at each step.

<!--
############
class ChoiceFuzzer(ComplexFuzzer):
    def __init__(self, grammar, choices):
        super().__init__(grammar)
        self.grammar = grammar
        self.vars = []
        self._vars = []
        self.choices = choices

    def select(self, lst):
        return self.choices.choice(lst)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ChoiceFuzzer(ComplexFuzzer):
    def __init__(self, grammar, choices):
        super().__init__(grammar)
        self.grammar = grammar
        self.vars = []
        self._vars = []
        self.choices = choices

    def select(self, lst):
        return self.choices.choice(lst)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The choice sequence both keeps track of all choices made, and also allows one to reuse previous choices.

<!--
############
class ChoiceSeq:
    def __init__(self, ints=None):
        self.index = -1
        if ints is None:
            self.ints = []
            self.choose_new = True
        else:
            self.ints = ints
            self.choose_new = False

    def i(self):
        if self.choose_new:
            self.index += 1
            self.ints.append(random.randrange(10))
            return self.ints[self.index]
        else:
            self.index += 1
            return self.ints[self.index]

    def choice(self, lst):
        return lst[self.i() % len(lst)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ChoiceSeq:
    def __init__(self, ints=None):
        self.index = -1
        if ints is None:
            self.ints = []
            self.choose_new = True
        else:
            self.ints = ints
            self.choose_new = False

    def i(self):
        if self.choose_new:
            self.index += 1
            self.ints.append(random.randrange(10))
            return self.ints[self.index]
        else:
            self.index += 1
            return self.ints[self.index]

    def choice(self, lst):
        return lst[self.i() % len(lst)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver is as follows

<!--
############
print()
lf2_mystr = """\
import random
random.seed(seed)
choices = ChoiceSeq()
c = ChoiceFuzzer(assignment_grammar1, choices)
print(c.fuzz('<start>'))
print(c.vars)
print(c.choices.ints)
"""
lf2_mystr = textwrap.dedent(lf2_mystr)
exec(lf2_mystr, {'ChoiceSeq':ChoiceSeq, 'ChoiceFuzzer': ChoiceFuzzer,
    'assignment_grammar1' : assignment_grammar1}, {'seed' : 6})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
lf2_mystr = &quot;&quot;&quot;\
import random
random.seed(seed)
choices = ChoiceSeq()
c = ChoiceFuzzer(assignment_grammar1, choices)
print(c.fuzz(&#x27;&lt;start&gt;&#x27;))
print(c.vars)
print(c.choices.ints)
&quot;&quot;&quot;
lf2_mystr = textwrap.dedent(lf2_mystr)
exec(lf2_mystr, {&#x27;ChoiceSeq&#x27;:ChoiceSeq, &#x27;ChoiceFuzzer&#x27;: ChoiceFuzzer,
    &#x27;assignment_grammar1&#x27; : assignment_grammar1}, {&#x27;seed&#x27; : 6})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The choice sequence is printed out at the end. The same sequence can be used later, to produce the same string. We use this
in the next step. Now, all that we need is to hook up the predicate for ddmin, and its definitions.
First, the traditional `ddmin` that works on independent deltas that we defined in the previous [post](/post/2019/12/03/ddmin/).

<!--
############
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        stitched =  instr[:i] + instr[i+part_len:]
        if causal(stitched): return i, stitched
    return -1, instr

def ddmin(cur_str, causal_fn):
    start, part_len = 0, len(cur_str) // 2
    while part_len >= 1:
        start, cur_str = remove_check_each_fragment(cur_str, start, part_len, causal_fn)
        if start != -1:
            if not cur_str: return ''
        else:
            start, part_len = 0, part_len // 2
    return cur_str

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        stitched =  instr[:i] + instr[i+part_len:]
        if causal(stitched): return i, stitched
    return -1, instr

def ddmin(cur_str, causal_fn):
    start, part_len = 0, len(cur_str) // 2
    while part_len &gt;= 1:
        start, cur_str = remove_check_each_fragment(cur_str, start, part_len, causal_fn)
        if start != -1:
            if not cur_str: return &#x27;&#x27;
        else:
            start, part_len = 0, part_len // 2
    return cur_str
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The ddmin now operates on choice sequences. So we need to convert them back to string

<!--
############
def ints_to_string(grammar, ints):
    choices = ChoiceSeq(ints)
    cf = ChoiceFuzzer(grammar, choices)
    try:
        return cf.fuzz('<start>')
    except IndexError:
        return None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def ints_to_string(grammar, ints):
    choices = ChoiceSeq(ints)
    cf = ChoiceFuzzer(grammar, choices)
    try:
        return cf.fuzz(&#x27;&lt;start&gt;&#x27;)
    except IndexError:
        return None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need our predicate. Note that we specialcase `None` in case the `ints_to_string` cannot successfully produce a value.

<!--
############
def pred(v):
    if v is None: return False

    if '((' in v and '))' in v:
        return True
    return False

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def pred(v):
    if v is None: return False

    if &#x27;((&#x27; in v and &#x27;))&#x27; in v:
        return True
    return False
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver tries to minimize the string if predicate returns true.

<!--
############
print()
lf3_mystr = """\
choices = ChoiceSeq()
causal_fn = lambda ints: pred(ints_to_string(assignment_grammar1, ints))
import random
random.seed(seed)
c = ChoiceFuzzer(assignment_grammar1, choices)
val = c.fuzz('<start>')
if pred(val):
    newv = ddmin(c.choices.ints, causal_fn)
    choices = ChoiceSeq(newv)
    cf = ChoiceFuzzer(assignment_grammar1, choices)
    print('original:')
    print(val, len(c.choices.ints))

    while True:
        newv = ddmin(cf.choices.ints, causal_fn)
        if len(newv) >= len(cf.choices.ints):
            break
        cf = ChoiceFuzzer(assignment_grammar1, ChoiceSeq(newv))

    cf = ChoiceFuzzer(assignment_grammar1, ChoiceSeq(newv))
    print('minimal:')
    print(cf.fuzz('<start>'), len(newv))
    print(cf.choices.ints)
else: print("run again")
"""
lf3_mystr = textwrap.dedent(lf3_mystr)
exec(lf3_mystr, {
    'ChoiceFuzzer': ChoiceFuzzer,
    'assignment_grammar1': assignment_grammar1,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq': ChoiceSeq,
    'ints_to_string': ints_to_string,
    }, {
    'seed': 1,
        })


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
lf3_mystr = &quot;&quot;&quot;\
choices = ChoiceSeq()
causal_fn = lambda ints: pred(ints_to_string(assignment_grammar1, ints))
import random
random.seed(seed)
c = ChoiceFuzzer(assignment_grammar1, choices)
val = c.fuzz(&#x27;&lt;start&gt;&#x27;)
if pred(val):
    newv = ddmin(c.choices.ints, causal_fn)
    choices = ChoiceSeq(newv)
    cf = ChoiceFuzzer(assignment_grammar1, choices)
    print(&#x27;original:&#x27;)
    print(val, len(c.choices.ints))

    while True:
        newv = ddmin(cf.choices.ints, causal_fn)
        if len(newv) &gt;= len(cf.choices.ints):
            break
        cf = ChoiceFuzzer(assignment_grammar1, ChoiceSeq(newv))

    cf = ChoiceFuzzer(assignment_grammar1, ChoiceSeq(newv))
    print(&#x27;minimal:&#x27;)
    print(cf.fuzz(&#x27;&lt;start&gt;&#x27;), len(newv))
    print(cf.choices.ints)
else: print(&quot;run again&quot;)
&quot;&quot;&quot;
lf3_mystr = textwrap.dedent(lf3_mystr)
exec(lf3_mystr, {
    &#x27;ChoiceFuzzer&#x27;: ChoiceFuzzer,
    &#x27;assignment_grammar1&#x27;: assignment_grammar1,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq&#x27;: ChoiceSeq,
    &#x27;ints_to_string&#x27;: ints_to_string,
    }, {
    &#x27;seed&#x27;: 1,
        })
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, the original string that is a `61` choice long sequence has become reduced to an `8` choice long sequence, with a corresponding
decrease in the string length. At this point, note that it is fairly magick how the approach performs. In particular, as soon as an edit is made,
the remaining choices are not interpreted as in the original string. What if we help the reducer by specifying an `NOP` that allows one to delete
chunks with a chance for the remaining string to be interpreted similarly?

The idea is to delete a sequence of values and replace it by a single `-1` value which will cause the choice fuzzer to interpret it as fill in
with default value. The `ddmin` is modified as follows:

<!--
############
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        if i > 0:
            stitched =  instr[:i-1] + [-1] + instr[i+part_len:]
        else:
            stitched =  instr[:i] + [-1] + instr[i+part_len+1:]
        if causal(stitched): return i, stitched
    return -1, instr

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def remove_check_each_fragment(instr, start, part_len, causal):
    for i in range(start, len(instr), part_len):
        if i &gt; 0:
            stitched =  instr[:i-1] + [-1] + instr[i+part_len:]
        else:
            stitched =  instr[:i] + [-1] + instr[i+part_len+1:]
        if causal(stitched): return i, stitched
    return -1, instr
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we need to get our fuzzer to understand the `-1` value.
We add defaults to each nonterminal, and modify the `select` function to take a default value.

<!--
############
class ChoiceFuzzer2(ComplexFuzzer):
    def __init__(self, grammar, choices):
        super().__init__(grammar)
        self.choices = choices

        self.default = {
                '<start>': 'a=0;\n',
                '<assignments>': 'a=0;\n',
                '<assign>': 'a=0',
                '<assign>': 'a=0',
                '<expr>': '0',
                '<digit>': '0',
                '<var>': '0'
                }

    def select(self, lst, default):
        return self.choices.choice(lst, default)

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule)
                    for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        default = self.default[key]
        return (key, self.gen_rule(self.select(rules, default), depth+1, max_depth))

def defined_var2(o, token, val):
    assert token == '<var>'
    if not o.vars:
        return ('00', [])
    else:
        return (o.select(o.vars, '000'), [])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ChoiceFuzzer2(ComplexFuzzer):
    def __init__(self, grammar, choices):
        super().__init__(grammar)
        self.choices = choices

        self.default = {
                &#x27;&lt;start&gt;&#x27;: &#x27;a=0;\n&#x27;,
                &#x27;&lt;assignments&gt;&#x27;: &#x27;a=0;\n&#x27;,
                &#x27;&lt;assign&gt;&#x27;: &#x27;a=0&#x27;,
                &#x27;&lt;assign&gt;&#x27;: &#x27;a=0&#x27;,
                &#x27;&lt;expr&gt;&#x27;: &#x27;0&#x27;,
                &#x27;&lt;digit&gt;&#x27;: &#x27;0&#x27;,
                &#x27;&lt;var&gt;&#x27;: &#x27;0&#x27;
                }

    def select(self, lst, default):
        return self.choices.choice(lst, default)

    def gen_key(self, key, depth, max_depth):
        if key not in self.grammar: return (key, [])
        if depth &gt; max_depth:
            clst_ = [(self.cost[key][str(self.cfg_rule(rule))], rule)
                    for rule in self.grammar[key]]
            clst = sorted(clst_, key=lambda x: x[0])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        default = self.default[key]
        return (key, self.gen_rule(self.select(rules, default), depth+1, max_depth))

def defined_var2(o, token, val):
    assert token == &#x27;&lt;var&gt;&#x27;
    if not o.vars:
        return (&#x27;00&#x27;, [])
    else:
        return (o.select(o.vars, &#x27;000&#x27;), [])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Rebinding our grammar

<!--
############
assignment_grammar2 = {
        '<start>' : [[ '<assignments>' ]],
        '<assignments>': [['<assign>', (';\n', {'post':sync})],
                          ['<assign>', (';\n', {'post':sync}), '<assignments>']],
        '<assign>': [[('<var>', {'post':defining_var}), ' = ', '<expr>']],
        '<expr>': [
            ['<expr>', ' + ', '<expr>'],
            ['<expr>', ' - ', '<expr>'],
            ['(', '<expr>', ')'],
            [('<var>', {'pre':defined_var2})],
            ['<digit>']],
        '<digit>': [['0'], ['1']],
        '<var>': [[i] for i in string.ascii_lowercase]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
assignment_grammar2 = {
        &#x27;&lt;start&gt;&#x27; : [[ &#x27;&lt;assignments&gt;&#x27; ]],
        &#x27;&lt;assignments&gt;&#x27;: [[&#x27;&lt;assign&gt;&#x27;, (&#x27;;\n&#x27;, {&#x27;post&#x27;:sync})],
                          [&#x27;&lt;assign&gt;&#x27;, (&#x27;;\n&#x27;, {&#x27;post&#x27;:sync}), &#x27;&lt;assignments&gt;&#x27;]],
        &#x27;&lt;assign&gt;&#x27;: [[(&#x27;&lt;var&gt;&#x27;, {&#x27;post&#x27;:defining_var}), &#x27; = &#x27;, &#x27;&lt;expr&gt;&#x27;]],
        &#x27;&lt;expr&gt;&#x27;: [
            [&#x27;&lt;expr&gt;&#x27;, &#x27; + &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;&lt;expr&gt;&#x27;, &#x27; - &#x27;, &#x27;&lt;expr&gt;&#x27;],
            [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
            [(&#x27;&lt;var&gt;&#x27;, {&#x27;pre&#x27;:defined_var2})],
            [&#x27;&lt;digit&gt;&#x27;]],
        &#x27;&lt;digit&gt;&#x27;: [[&#x27;0&#x27;], [&#x27;1&#x27;]],
        &#x27;&lt;var&gt;&#x27;: [[i] for i in string.ascii_lowercase]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The choice sequence now returns the `default` when it sees the `-1` value.

<!--
############
class ChoiceSeq2:
    def __init__(self, ints=None):
        self.index = -1
        if ints is None:
            self.ints = []
            self.choose_new = True
        else:
            self.ints = ints
            self.choose_new = False

    def i(self):
        if self.choose_new:
            self.index += 1
            self.ints.append(random.randrange(10))
            return self.ints[self.index]
        else:
            self.index += 1
            return self.ints[self.index]

    def choice(self, lst, default):
        v = self.i()
        if v == -1:
            return default
        else:
            return lst[v % len(lst)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ChoiceSeq2:
    def __init__(self, ints=None):
        self.index = -1
        if ints is None:
            self.ints = []
            self.choose_new = True
        else:
            self.ints = ints
            self.choose_new = False

    def i(self):
        if self.choose_new:
            self.index += 1
            self.ints.append(random.randrange(10))
            return self.ints[self.index]
        else:
            self.index += 1
            return self.ints[self.index]

    def choice(self, lst, default):
        v = self.i()
        if v == -1:
            return default
        else:
            return lst[v % len(lst)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
def ints_to_string2(grammar, ints):
    choices = ChoiceSeq2(ints)
    cf = ChoiceFuzzer2(grammar, choices)
    try:
        return cf.fuzz('<start>')
    except IndexError:
        return None

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def ints_to_string2(grammar, ints):
    choices = ChoiceSeq2(ints)
    cf = ChoiceFuzzer2(grammar, choices)
    try:
        return cf.fuzz(&#x27;&lt;start&gt;&#x27;)
    except IndexError:
        return None
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
These are all the modifications that we require.

<!--
############
print()
lf4_mystr = """\
import random
random.seed(seed)
choices = ChoiceSeq2()

c = ChoiceFuzzer2(assignment_grammar2, choices)
val = c.fuzz('<start>')

causal_fn = lambda ints: pred(ints_to_string2(assignment_grammar2, ints))
if pred(val):
    newv = ddmin(c.choices.ints, causal_fn)
    choices = ChoiceSeq2(newv)
    cf = ChoiceFuzzer2(assignment_grammar2, choices)
    print("original:")
    print(val, len(c.choices.ints))

    while True:
        newv = ddmin(cf.choices.ints, causal_fn)
        if len(newv) >= len(cf.choices.ints):
            break
        cf = ChoiceFuzzer2(assignment_grammar2, ChoiceSeq2(newv))

    cf = ChoiceFuzzer2(assignment_grammar2, ChoiceSeq2(newv))
    print("minimal:")
    print(cf.fuzz("<start>"), len(newv))
    print(cf.choices.ints)
else: print("run again")
"""
lf4_mystr = textwrap.dedent(lf4_mystr)
exec(lf4_mystr, {
    'ChoiceFuzzer2': ChoiceFuzzer2,
    'assignment_grammar2': assignment_grammar2,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq2': ChoiceSeq2,
    'ints_to_string2': ints_to_string2,
    }, {
    'seed': 1,
})

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
lf4_mystr = &quot;&quot;&quot;\
import random
random.seed(seed)
choices = ChoiceSeq2()

c = ChoiceFuzzer2(assignment_grammar2, choices)
val = c.fuzz(&#x27;&lt;start&gt;&#x27;)

causal_fn = lambda ints: pred(ints_to_string2(assignment_grammar2, ints))
if pred(val):
    newv = ddmin(c.choices.ints, causal_fn)
    choices = ChoiceSeq2(newv)
    cf = ChoiceFuzzer2(assignment_grammar2, choices)
    print(&quot;original:&quot;)
    print(val, len(c.choices.ints))

    while True:
        newv = ddmin(cf.choices.ints, causal_fn)
        if len(newv) &gt;= len(cf.choices.ints):
            break
        cf = ChoiceFuzzer2(assignment_grammar2, ChoiceSeq2(newv))

    cf = ChoiceFuzzer2(assignment_grammar2, ChoiceSeq2(newv))
    print(&quot;minimal:&quot;)
    print(cf.fuzz(&quot;&lt;start&gt;&quot;), len(newv))
    print(cf.choices.ints)
else: print(&quot;run again&quot;)
&quot;&quot;&quot;
lf4_mystr = textwrap.dedent(lf4_mystr)
exec(lf4_mystr, {
    &#x27;ChoiceFuzzer2&#x27;: ChoiceFuzzer2,
    &#x27;assignment_grammar2&#x27;: assignment_grammar2,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq2&#x27;: ChoiceSeq2,
    &#x27;ints_to_string2&#x27;: ints_to_string2,
    }, {
    &#x27;seed&#x27;: 1,
})
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
How does this modification fare against the original without modification?
With seed 5

<!--
############
print()
print('seed:5', 'lf_3')
exec(lf3_mystr, {
    'ChoiceFuzzer': ChoiceFuzzer,
    'assignment_grammar1': assignment_grammar1,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq': ChoiceSeq,
    'ints_to_string': ints_to_string,
    }, {
    'seed': 5,
        })
print('seed:5', 'lf_4')
exec(lf4_mystr, {
    'ChoiceFuzzer2': ChoiceFuzzer2,
    'assignment_grammar2': assignment_grammar2,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq2': ChoiceSeq2,
    'ints_to_string2': ints_to_string2,
    }, {
    'seed': 5,
    })

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
print(&#x27;seed:5&#x27;, &#x27;lf_3&#x27;)
exec(lf3_mystr, {
    &#x27;ChoiceFuzzer&#x27;: ChoiceFuzzer,
    &#x27;assignment_grammar1&#x27;: assignment_grammar1,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq&#x27;: ChoiceSeq,
    &#x27;ints_to_string&#x27;: ints_to_string,
    }, {
    &#x27;seed&#x27;: 5,
        })
print(&#x27;seed:5&#x27;, &#x27;lf_4&#x27;)
exec(lf4_mystr, {
    &#x27;ChoiceFuzzer2&#x27;: ChoiceFuzzer2,
    &#x27;assignment_grammar2&#x27;: assignment_grammar2,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq2&#x27;: ChoiceSeq2,
    &#x27;ints_to_string2&#x27;: ints_to_string2,
    }, {
    &#x27;seed&#x27;: 5,
    })
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another:
With seed 9

<!--
############
print()
print('seed:9', 'lf_3')
exec(lf3_mystr, {
    'ChoiceFuzzer': ChoiceFuzzer,
    'assignment_grammar1': assignment_grammar1,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq': ChoiceSeq,
    'ints_to_string': ints_to_string,
    }, {
    'seed': 9,
        })
print('seed:9', 'lf_4')
exec(lf4_mystr, {
    'ChoiceFuzzer2': ChoiceFuzzer2,
    'assignment_grammar2': assignment_grammar2,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq2': ChoiceSeq2,
    'ints_to_string2': ints_to_string2,
    }, {
    'seed': 9,
    })

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
print(&#x27;seed:9&#x27;, &#x27;lf_3&#x27;)
exec(lf3_mystr, {
    &#x27;ChoiceFuzzer&#x27;: ChoiceFuzzer,
    &#x27;assignment_grammar1&#x27;: assignment_grammar1,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq&#x27;: ChoiceSeq,
    &#x27;ints_to_string&#x27;: ints_to_string,
    }, {
    &#x27;seed&#x27;: 9,
        })
print(&#x27;seed:9&#x27;, &#x27;lf_4&#x27;)
exec(lf4_mystr, {
    &#x27;ChoiceFuzzer2&#x27;: ChoiceFuzzer2,
    &#x27;assignment_grammar2&#x27;: assignment_grammar2,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq2&#x27;: ChoiceSeq2,
    &#x27;ints_to_string2&#x27;: ints_to_string2,
    }, {
    &#x27;seed&#x27;: 9,
    })
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another:
With seed 16

<!--
############
print()
print('seed:16', 'lf_3')
exec(lf3_mystr, {
    'ChoiceFuzzer': ChoiceFuzzer,
    'assignment_grammar1': assignment_grammar1,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq': ChoiceSeq,
    'ints_to_string': ints_to_string,
    }, {
    'seed': 16,
        })
print('seed:16', 'lf_4')
exec(lf4_mystr, {
    'ChoiceFuzzer2': ChoiceFuzzer2,
    'assignment_grammar2': assignment_grammar2,
    'ddmin': ddmin,
    'pred': pred,
    'ChoiceSeq2': ChoiceSeq2,
    'ints_to_string2': ints_to_string2,
    }, {
    'seed': 16,
    })

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print()
print(&#x27;seed:16&#x27;, &#x27;lf_3&#x27;)
exec(lf3_mystr, {
    &#x27;ChoiceFuzzer&#x27;: ChoiceFuzzer,
    &#x27;assignment_grammar1&#x27;: assignment_grammar1,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq&#x27;: ChoiceSeq,
    &#x27;ints_to_string&#x27;: ints_to_string,
    }, {
    &#x27;seed&#x27;: 16,
        })
print(&#x27;seed:16&#x27;, &#x27;lf_4&#x27;)
exec(lf4_mystr, {
    &#x27;ChoiceFuzzer2&#x27;: ChoiceFuzzer2,
    &#x27;assignment_grammar2&#x27;: assignment_grammar2,
    &#x27;ddmin&#x27;: ddmin,
    &#x27;pred&#x27;: pred,
    &#x27;ChoiceSeq2&#x27;: ChoiceSeq2,
    &#x27;ints_to_string2&#x27;: ints_to_string2,
    }, {
    &#x27;seed&#x27;: 16,
    })
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
There does not seem to be a lot of advantage in using an `NOP`.

Next: How does this compare against the custom passes of Hypothesis? and how does it compare against direct `delta debug` and variants of `HDD` including `Perses`.

The code for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2020-07-26-semantic-testcase-reducer.py).

[^mciver2020reduction]: *Test-Case Reduction via Test-Case Generation:Insights From the Hypothesis Reducer* by _David R. MacIver_ and _Alastair F. Donaldson_ at [ECOOP 2020](https://drmaciver.github.io/papers/reduction-via-generation-preview.pdf)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
