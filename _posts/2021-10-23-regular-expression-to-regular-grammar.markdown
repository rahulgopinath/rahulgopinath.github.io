---
published: true
title: Regular Expression to Regular Grammar
layout: post
comments: true
tags: python
categories: post
---
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
In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/), we
discussed how to produce a grammar out of regular expressions. This is
useful to make the regular expression a generator of matching inputs. However,
one detail is unsatisfying. The grammar produced is a context-free grammar.
Regular expressions actually correspond to regular grammars (which
are strictly less powerful than context-free grammars).
For reference, a context-free grammar is a grammar where the rules are of
the form $$ A -> \alpha $$ where $$A$$ is a single nonterminal symbol and
$$ \alpha $$ is any sequence of terminal or nonterminal symbols
(including $$\epsilon$$ (empty)).
A regular grammar on the other hand, is a grammar where the rules can take one
of the following forms:
* $$ A \rightarrow a $$
* $$ A \rightarrow a B $$
* $$ A \rightarrow \epsilon $$
where $$ A $$  and $$ B $$ are nonterminal symbols, $$ a $$ is a terminal
symbol, and $$ \epsilon $$ is the empty string.
So, why is producing a context-free grammar instead of regular grammar
unsatisfying? Because such regular grammars have more interesting properties
such as being closed under intersection and complement. By using a
context-free grammar, we miss out on such properties.
Hence, it would be really good if we could
translate the regular expression directly into a regular grammar. This is what
we will do in this post.
We start with importing the prerequisites

<!--
############
import sys, imp, pprint, string

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
        with open(module_loc, encoding='utf8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys, imp, pprint, string

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
        with open(module_loc, encoding=&#x27;utf8&#x27;) as f:
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
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
rxfuzzer = import_file(&#x27;rxfuzzer&#x27;, &#x27;2021-10-22-fuzzing-with-regular-expressions.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We want to produce regular grammars directly from regular expressions.
The translations of the basic operations are given by:
| RE                    | RG                                                  |
|-----------------------|-----------------------------------------------------|
| `e`                   | $$ S \rightarrow e $$                               |
| `e|f`                 | $$ S \rightarrow e | f $$                           |
| `ef`                  | $$ S \rightarrow e A$$, $$ A \rightarrow f $$       |
| `e+`                  | $$ S \rightarrow e S | e        $$                  |
| `e*`                  | $$ S \rightarrow e S | \epsilon $$                  |
## Union of Regular Grammars

Given two regular grammars such that their nonterminals do not overlap,
we need to produce a union grammar.
The idea is that you only need to modify the start symbol such that
the definition of the new start symbol is a combination of starts from both
grammars.

<!--
############
def key_intersection(g1, g2):
    return [k for k in g1 if k in g2]

def regular_union(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_s = '<%s>' % (s1[1:-1] + s2[1:-1])
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def key_intersection(g1, g2):
    return [k for k in g1 if k in g2]

def regular_union(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_s = &#x27;&lt;%s&gt;&#x27; % (s1[1:-1] + s2[1:-1])
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1 = 'a1(b1(c1)|b1)'
g1 = {
        '<start1>' : [['<A1>']],
        '<A1>' : [['a1', '<B1>']],
        '<B1>' : [['b1','<C1>'], ['b1']],
        '<C1>' : [['c1']]
        }
my_re2 = 'a2(b2)|a2'
g2 = {
        '<start2>' : [['<A2>']],
        '<A2>' : [['a2', '<B2>'], ['a2']],
        '<B2>' : [['b2']]
        }
g, s = regular_union(g1, '<start1>', g2, '<start2>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1, v) or re.match(my_re2, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1 = &#x27;a1(b1(c1)|b1)&#x27;
g1 = {
        &#x27;&lt;start1&gt;&#x27; : [[&#x27;&lt;A1&gt;&#x27;]],
        &#x27;&lt;A1&gt;&#x27; : [[&#x27;a1&#x27;, &#x27;&lt;B1&gt;&#x27;]],
        &#x27;&lt;B1&gt;&#x27; : [[&#x27;b1&#x27;,&#x27;&lt;C1&gt;&#x27;], [&#x27;b1&#x27;]],
        &#x27;&lt;C1&gt;&#x27; : [[&#x27;c1&#x27;]]
        }
my_re2 = &#x27;a2(b2)|a2&#x27;
g2 = {
        &#x27;&lt;start2&gt;&#x27; : [[&#x27;&lt;A2&gt;&#x27;]],
        &#x27;&lt;A2&gt;&#x27; : [[&#x27;a2&#x27;, &#x27;&lt;B2&gt;&#x27;], [&#x27;a2&#x27;]],
        &#x27;&lt;B2&gt;&#x27; : [[&#x27;b2&#x27;]]
        }
g, s = regular_union(g1, &#x27;&lt;start1&gt;&#x27;, g2, &#x27;&lt;start2&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1, v) or re.match(my_re2, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Concatenation of Regular Grammars

Next, given two regular grammars g1 g2, such that
their nonterminals do not overlap, producing a concatenation grammar is as
follows: We collect all terminating rules from g1 which looks like
$$ A \\rightarrow a $$ where
$$ a $$ is a terminal symbol. We then transform them to $$ A -> a S2 $$
where $$ S2 $$ is the start symbol of g2. If epsilon was present in one of the
rules of gA, then we simply produce $$ A \rightarrow S2 $$.

<!--
############
def regular_catenation(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                #new_rules.extend(g2[s2])
                new_rules.append([s2])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r + [s2])
            else:
                new_rules.append(r)
    return {**g2, **new_g}, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regular_catenation(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                #new_rules.extend(g2[s2])
                new_rules.append([s2])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r + [s2])
            else:
                new_rules.append(r)
    return {**g2, **new_g}, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re3 = '1(2(3|5))'
g3 = {
        '<start3>' : [['1', '<A3>']],
        '<A3>' : [['2', '<B3>']],
        '<B3>' : [['3'], ['5']]
        }
my_re4 = 'a(b(c|d)|b)'
g4 = {
        '<start4>' : [['a', '<A4>']],
        '<A4>' : [['b', '<B4>'], ['b']],
        '<B4>' : [['c'], ['d']]
        }
g, s = regular_catenation(g3, '<start3>', g4, '<start4>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re3 + my_re4, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re3 = &#x27;1(2(3|5))&#x27;
g3 = {
        &#x27;&lt;start3&gt;&#x27; : [[&#x27;1&#x27;, &#x27;&lt;A3&gt;&#x27;]],
        &#x27;&lt;A3&gt;&#x27; : [[&#x27;2&#x27;, &#x27;&lt;B3&gt;&#x27;]],
        &#x27;&lt;B3&gt;&#x27; : [[&#x27;3&#x27;], [&#x27;5&#x27;]]
        }
my_re4 = &#x27;a(b(c|d)|b)&#x27;
g4 = {
        &#x27;&lt;start4&gt;&#x27; : [[&#x27;a&#x27;, &#x27;&lt;A4&gt;&#x27;]],
        &#x27;&lt;A4&gt;&#x27; : [[&#x27;b&#x27;, &#x27;&lt;B4&gt;&#x27;], [&#x27;b&#x27;]],
        &#x27;&lt;B4&gt;&#x27; : [[&#x27;c&#x27;], [&#x27;d&#x27;]]
        }
g, s = regular_catenation(g3, &#x27;&lt;start3&gt;&#x27;, g4, &#x27;&lt;start4&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re3 + my_re4, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Kleene Plus of Regular Grammars
For every terminating rule in g, add $$ A \rightarrow a S $$ where S is the
start symbol.

<!--
############
def regular_kleeneplus(g1, s1):
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                new_rules.append([])
                #new_rules.extend(g1[s2])
                new_rules.append([s1])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r)
                new_rules.append(r + [s1])
            else:
                new_rules.append(r)
    return new_g, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regular_kleeneplus(g1, s1):
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                new_rules.append([])
                #new_rules.extend(g1[s2])
                new_rules.append([s1])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r)
                new_rules.append(r + [s1])
            else:
                new_rules.append(r)
    return new_g, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1plus = '(%s)+' % my_re1
g, s = regular_kleeneplus(g1, '<start1>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1plus, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1plus = &#x27;(%s)+&#x27; % my_re1
g, s = regular_kleeneplus(g1, &#x27;&lt;start1&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert re.match(my_re1plus, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Kleene Star of Regular Grammars
For Kleene Star, add $$ \epsilon $$ to the language.

<!--
############
def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    g[s].append([])
    return g, s

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    g[s].append([])
    return g, s
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re1star = '(%s)+' % my_re1
g, s = regular_kleenestar(g1, '<start1>')
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert (re.match(my_re1star, v) or v == ''), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re1star = &#x27;(%s)+&#x27; % my_re1
g, s = regular_kleenestar(g1, &#x27;&lt;start1&gt;&#x27;)
print(s)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    assert (re.match(my_re1star, v) or v == &#x27;&#x27;), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we have all operations  necessary to convert a regular
expression to a regular grammar directly. We first define the class

<!--
############
class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
 <cex>   ::= <exp>
           | <exp> <cex> 
```
| RE                    | RG                                                  |
|-----------------------|-----------------------------------------------------|
| `ef`                  | $$ S \rightarrow e A$$, $$ A \rightarrow f $$       |

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_exp(child)
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            g, s = regular_catenation(g1, s1, g2, key2)
            return g, s
        else:
            return g1, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_exp(child)
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            g, s = regular_catenation(g1, s1, g2, key2)
            return g, s
        else:
            return g1, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
  <regex> ::= <cex>
            | <cex> `|` <regex>
```
| RE                    | RG                                                  |
|-----------------------|-----------------------------------------------------|
| `e|f`                 | $$ S \rightarrow e | f $$                           |

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_cex(child)
        if not children: return g1, s1
        if len(children) == 2:
            g2, s2 = self.convert_regex(children[1])
            g, s = regular_union(g1, s1, g2, s2)
            return g, s
        else:
            assert len(children) == 1
            g1[s1].append([])
            return g1, s1

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_cex(child)
        if not children: return g1, s1
        if len(children) == 2:
            g2, s2 = self.convert_regex(children[1])
            g, s = regular_union(g1, s1, g2, s2)
            return g, s
        else:
            assert len(children) == 1
            g1[s1].append([])
            return g1, s1
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
```
   <regexplus> ::= <unitexp> `+`
```
| RE                    | RG                                                  |
|-----------------------|-----------------------------------------------------|
| `e+`                  | $$ S \rightarrow e S | e        $$                  |
| `e*`                  | $$ S \rightarrow e S | \epsilon $$                  |

<!--
############
class RegexToRGrammar(RegexToRGrammar):
    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleeneplus(g, s)

    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleenestar(g, s)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class RegexToRGrammar(RegexToRGrammar):
    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleeneplus(g, s)

    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleenestar(g, s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
my_re = 'x(a|b|c)+'
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_re = &#x27;x(a|b|c)+&#x27;
print(my_re)
g, s = RegexToRGrammar().to_grammar(my_re)
gatleast.display_grammar(g, s)
# check it has worked
import re
rgf = fuzzer.LimitFuzzer(g)
for i in range(10):
    v = rgf.fuzz(s)
    print(repr(v))
    assert re.match(my_re, v), v
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py)

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
