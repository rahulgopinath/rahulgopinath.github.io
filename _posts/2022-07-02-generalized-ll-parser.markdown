---
published: true
title: Generalized LL (GLL) Parser
layout: post
comments: true
tags: controlflow
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
We [previously discussed](/post/2021/02/06/earley-parsing/) the
implementation of an Earley parser with Joop Leo's optimizations. Earley
parser is one of the general context-free parsing algorithms available.
Another popular general context-free parsing algorightm is
*Generalized LL* parsing, which was invented by
Elizabeth Scott and Adrian Johnstone. In this post, I provide a complete
implementation and a tutorial on how to implement a GLL parser in Python.

**Note:** This post is not complete. Given the interest in GLL parsers, I am
simply providing the source until I have more bandwidth to complete the
tutorial.
#### Prerequisites
As before, we start with the prerequisite imports.

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
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import simplefuzzer as fuzzer

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as fuzzer
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Our grammar

<!--
############
G = {
  '<S>': [
       ['<A>', '<S>', 'd'],
       ['<B>', '<S>'],
       ['g', 'p', '<C>'],
       []],
  '<A>': [['a'], ['c']],
  '<B>': [['a'], ['b']],
  '<C>': ['c']
}
start = '<S>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
G = {
  &#x27;&lt;S&gt;&#x27;: [
       [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;S&gt;&#x27;, &#x27;d&#x27;],
       [&#x27;&lt;B&gt;&#x27;, &#x27;&lt;S&gt;&#x27;],
       [&#x27;g&#x27;, &#x27;p&#x27;, &#x27;&lt;C&gt;&#x27;],
       []],
  &#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;c&#x27;]],
  &#x27;&lt;B&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;b&#x27;]],
  &#x27;&lt;C&gt;&#x27;: [&#x27;c&#x27;]
}
start = &#x27;&lt;S&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## GLL with Separate Stacks

### The GLL Stack

<!--
############
class GLLStack:
    def __init__(self, s):
        self.R = []
        self.I = s

    def add_thread(self, L, u, j):
        self.R.append((L, u, j))

    def pop_stack(self, s, i):
        s, (L, i_) = s
        self.add_thread(L, s, i)
        return s

    def register_return(self, L, s, i):
        return (tuple(s), (L, i))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GLLStack:
    def __init__(self, s):
        self.R = []
        self.I = s

    def add_thread(self, L, u, j):
        self.R.append((L, u, j))

    def pop_stack(self, s, i):
        s, (L, i_) = s
        self.add_thread(L, s, i)
        return s

    def register_return(self, L, s, i):
        return (tuple(s), (L, i))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The Stack GLL Compiler
#### Compiling a Terminal Symbol

<!--
############
def compile_terminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = '%s[%d]_%d' % (key, n_alt, r_pos+1)
    return '''\
        elif L == '%s[%d]_%d':
            if parser.I[i] == '%s':
                i = i+1
                L = '%s'
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, token, Lnxt)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_terminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = &#x27;_&#x27;
    else:
        Lnxt = &#x27;%s[%d]_%d&#x27; % (key, n_alt, r_pos+1)
    return &#x27;&#x27;&#x27;\
        elif L == &#x27;%s[%d]_%d&#x27;:
            if parser.I[i] == &#x27;%s&#x27;:
                i = i+1
                L = &#x27;%s&#x27;
            else:
                L = &#x27;L0&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, token, Lnxt)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Nonterminal Symbol

<!--
############
def compile_nonterminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '_'
    else:
        Lnxt = '%s[%d]_%d' % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  '%s[%d]_%d':
            sval = parser.register_return('%s', sval, i)
            L = '%s'
            continue
''' % (key, n_alt, r_pos, Lnxt, token)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_nonterminal(key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = &#x27;_&#x27;
    else:
        Lnxt = &#x27;%s[%d]_%d&#x27; % (key, n_alt, r_pos+1)
    return &#x27;&#x27;&#x27;\
        elif L ==  &#x27;%s[%d]_%d&#x27;:
            sval = parser.register_return(&#x27;%s&#x27;, sval, i)
            L = &#x27;%s&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, r_pos, Lnxt, token)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Rule

<!--
############
def compile_rule(key, n_alt, rule):
    res = []
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            r = compile_nonterminal(key, n_alt, i, len(rule), t)
        else:
            r = compile_terminal(key, n_alt, i, len(rule), t)
        res.append(r)

    res.append('''\
        elif L == '%s[%d]_%d':
            L = 'L_'
            continue
''' % (key, n_alt, len(rule)))
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_rule(key, n_alt, rule):
    res = []
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            r = compile_nonterminal(key, n_alt, i, len(rule), t)
        else:
            r = compile_terminal(key, n_alt, i, len(rule), t)
        res.append(r)

    res.append(&#x27;&#x27;&#x27;\
        elif L == &#x27;%s[%d]_%d&#x27;:
            L = &#x27;L_&#x27;
            continue
&#x27;&#x27;&#x27; % (key, n_alt, len(rule)))
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Definition

<!--
############
def compile_def(key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            parser.add_thread( '%s[%d]_0', sval, i)''' % (key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt,rule in enumerate(definition):
        r = compile_rule(key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_def(key, definition):
    res = []
    res.append(&#x27;&#x27;&#x27;\
        elif L == &#x27;%s&#x27;:
&#x27;&#x27;&#x27; % key)
    for n_alt,rule in enumerate(definition):
        res.append(&#x27;&#x27;&#x27;\
            parser.add_thread( &#x27;%s[%d]_0&#x27;, sval, i)&#x27;&#x27;&#x27; % (key, n_alt))
    res.append(&#x27;&#x27;&#x27;
            L = &#x27;L0&#x27;
            continue&#x27;&#x27;&#x27;)
    for n_alt,rule in enumerate(definition):
        r = compile_rule(key, n_alt, rule)
        res.append(r)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Compiling a Grammar

<!--
############
def compile_grammar(g, start):
    res = ['''\
def parse_string(parser):
    L, sval, i = '%s', parser.register_return('L0', [], 0), 0
    while True:
        if L == 'L0':
            if parser.R:
                (L, sval, i), *parser.R = parser.R
                if ('L0', (), len(parser.I)-1) == (L, sval, i): return 'success'
                else: continue
            else: return 'error'
        elif L == 'L_':
            sval = parser.pop_stack(sval, i)
            L = 'L0'
            continue
    ''' % start]
    for k in g:
        r = compile_def(k, g[k])
        res.append(r)
    res.append('''\
        else:
            assert False
''')
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_grammar(g, start):
    res = [&#x27;&#x27;&#x27;\
def parse_string(parser):
    L, sval, i = &#x27;%s&#x27;, parser.register_return(&#x27;L0&#x27;, [], 0), 0
    while True:
        if L == &#x27;L0&#x27;:
            if parser.R:
                (L, sval, i), *parser.R = parser.R
                if (&#x27;L0&#x27;, (), len(parser.I)-1) == (L, sval, i): return &#x27;success&#x27;
                else: continue
            else: return &#x27;error&#x27;
        elif L == &#x27;L_&#x27;:
            sval = parser.pop_stack(sval, i)
            L = &#x27;L0&#x27;
            continue
    &#x27;&#x27;&#x27; % start]
    for k in g:
        r = compile_def(k, g[k])
        res.append(r)
    res.append(&#x27;&#x27;&#x27;\
        else:
            assert False
&#x27;&#x27;&#x27;)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Example

<!--
############
res = compile_grammar(G, '<S>')
print(res)
exec(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
res = compile_grammar(G, &#x27;&lt;S&gt;&#x27;)
print(res)
exec(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Usage

<!--
############
import simplefuzzer
G = {
'<S>': [
    ['<A>', '<S>', 'd'],
    ['<B>', '<S>'],
    ['g', 'p', '<C>'],
    []],
'<A>': [['a'], ['c']],
'<B>': [['a'], ['b']],
'<C>': ['c']
}
import sys
gf = simplefuzzer.LimitFuzzer(G)
for i in range(10):
    s = gf.iter_fuzz(key='<S>', max_depth=100)
    print(s)
    g = GLLStack(s+'$')
    assert parse_string(g) == 'success'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer
G = {
&#x27;&lt;S&gt;&#x27;: [
    [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;S&gt;&#x27;, &#x27;d&#x27;],
    [&#x27;&lt;B&gt;&#x27;, &#x27;&lt;S&gt;&#x27;],
    [&#x27;g&#x27;, &#x27;p&#x27;, &#x27;&lt;C&gt;&#x27;],
    []],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;c&#x27;]],
&#x27;&lt;B&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;b&#x27;]],
&#x27;&lt;C&gt;&#x27;: [&#x27;c&#x27;]
}
import sys
gf = simplefuzzer.LimitFuzzer(G)
for i in range(10):
    s = gf.iter_fuzz(key=&#x27;&lt;S&gt;&#x27;, max_depth=100)
    print(s)
    g = GLLStack(s+&#x27;$&#x27;)
    assert parse_string(g) == &#x27;success&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## GLL with a Graph Structured Stack (GSS)

### The GLL GSS

<!--
############
class Node:
    def __init__(self, L, j, children):
        self.L, self.i, self.children = L, j, children
    def __repr__(self): return str((self.L, self.i, self.children))

class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, L, i, children):
        my_label = (L, i)
        if my_label not in self.gss:
            self.gss[my_label] = Node(L, i, children)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_to_P(self, u, j):
        label = (u.L, u.i)
        self.P[label].append(j)

    def __repr__(self): return str(self.gss)

class GLLStructuredStack:
    def register_return(self, L, u, j):
        v = self.gss.get(L, j, [u])
        if u not in v.children:
            v.children.append(u)
            label = (L, j)
            for k in self.gss.P[label]:
                self.add_thread(L, u, k)
        return v

    def add_thread(self, L, u, j):
        if (L, u) not in self.U[j]:
            self.U[j].append((L, u))
            assert (L,u,j) not in self.R
            self.R.append((L, u, j))

    def pop_stack(self, u, j):
        if u != self.u0:
            self.gss.add_to_P(u, j)
            for v in u.children:
                self.add_thread(u.L, v, j)
        return u


    def __init__(self, input_str):
        self.R = []
        self.gss = GSS()
        self.I = input_str
        self.m = len(self.I) # |I| + 1
        self.u1 = self.gss.get('L0', 0, [])
        self.u0 = self.gss.get('$', self.m, [])
        self.u1.children.append(self.u0)

        self.U = []
        for j in range(self.m): # 0<=j<=m
            self.U.append([]) # U_j = empty

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Node:
    def __init__(self, L, j, children):
        self.L, self.i, self.children = L, j, children
    def __repr__(self): return str((self.L, self.i, self.children))

class GSS:
    def __init__(self): self.gss, self.P = {}, {}

    def get(self, L, i, children):
        my_label = (L, i)
        if my_label not in self.gss:
            self.gss[my_label] = Node(L, i, children)
            assert my_label not in self.P
            self.P[my_label] = []
        return self.gss[my_label]

    def add_to_P(self, u, j):
        label = (u.L, u.i)
        self.P[label].append(j)

    def __repr__(self): return str(self.gss)

class GLLStructuredStack:
    def register_return(self, L, u, j):
        v = self.gss.get(L, j, [u])
        if u not in v.children:
            v.children.append(u)
            label = (L, j)
            for k in self.gss.P[label]:
                self.add_thread(L, u, k)
        return v

    def add_thread(self, L, u, j):
        if (L, u) not in self.U[j]:
            self.U[j].append((L, u))
            assert (L,u,j) not in self.R
            self.R.append((L, u, j))

    def pop_stack(self, u, j):
        if u != self.u0:
            self.gss.add_to_P(u, j)
            for v in u.children:
                self.add_thread(u.L, v, j)
        return u


    def __init__(self, input_str):
        self.R = []
        self.gss = GSS()
        self.I = input_str
        self.m = len(self.I) # |I| + 1
        self.u1 = self.gss.get(&#x27;L0&#x27;, 0, [])
        self.u0 = self.gss.get(&#x27;$&#x27;, self.m, [])
        self.u1.children.append(self.u0)

        self.U = []
        for j in range(self.m): # 0&lt;=j&lt;=m
            self.U.append([]) # U_j = empty
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### The GSS GLL Compiler
The only difference in the main body when using the GSS is how we check
for termination.

<!--
############
def compile_grammar(g, start):
    res = ['''\
def parse_string(parser):
    L, sval, i = '%s', parser.u1, 0
    while True:
        if L == 'L0':
            if parser.R:
                (L, sval, i), *parser.R = parser.R
                continue
            else:
                if ('L0', parser.u0) in parser.U[parser.m-1]: return 'success'
                else: return 'error'
        elif L == 'L_':
            sval = parser.pop_stack(sval, i)
            L = 'L0'
            continue
    ''' % start]
    for k in g:
        r = compile_def(k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    return '\n'.join(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def compile_grammar(g, start):
    res = [&#x27;&#x27;&#x27;\
def parse_string(parser):
    L, sval, i = &#x27;%s&#x27;, parser.u1, 0
    while True:
        if L == &#x27;L0&#x27;:
            if parser.R:
                (L, sval, i), *parser.R = parser.R
                continue
            else:
                if (&#x27;L0&#x27;, parser.u0) in parser.U[parser.m-1]: return &#x27;success&#x27;
                else: return &#x27;error&#x27;
        elif L == &#x27;L_&#x27;:
            sval = parser.pop_stack(sval, i)
            L = &#x27;L0&#x27;
            continue
    &#x27;&#x27;&#x27; % start]
    for k in g:
        r = compile_def(k, g[k])
        res.append(r)
    res.append(&#x27;&#x27;&#x27;
        else:
            assert False&#x27;&#x27;&#x27;)
    return &#x27;\n&#x27;.join(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
#### Example

<!--
############
res = compile_grammar(G, '<S>')
print(res)
exec(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
res = compile_grammar(G, &#x27;&lt;S&gt;&#x27;)
print(res)
exec(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Usage

<!--
############
import simplefuzzer
G = {
'<S>': [
    ['<A>', '<S>', 'd'],
    ['<B>', '<S>'],
    ['g', 'p', '<C>'],
    []],
'<A>': [['a'], ['c']],
'<B>': [['a'], ['b']],
'<C>': ['c']
}
import sys
gf = simplefuzzer.LimitFuzzer(G)
for i in range(10):
    s = gf.iter_fuzz(key='<S>', max_depth=100)
    print(s)
    g = GLLStructuredStack(s+'$')
    assert parse_string(g) == 'success'


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer
G = {
&#x27;&lt;S&gt;&#x27;: [
    [&#x27;&lt;A&gt;&#x27;, &#x27;&lt;S&gt;&#x27;, &#x27;d&#x27;],
    [&#x27;&lt;B&gt;&#x27;, &#x27;&lt;S&gt;&#x27;],
    [&#x27;g&#x27;, &#x27;p&#x27;, &#x27;&lt;C&gt;&#x27;],
    []],
&#x27;&lt;A&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;c&#x27;]],
&#x27;&lt;B&gt;&#x27;: [[&#x27;a&#x27;], [&#x27;b&#x27;]],
&#x27;&lt;C&gt;&#x27;: [&#x27;c&#x27;]
}
import sys
gf = simplefuzzer.LimitFuzzer(G)
for i in range(10):
    s = gf.iter_fuzz(key=&#x27;&lt;S&gt;&#x27;, max_depth=100)
    print(s)
    g = GLLStructuredStack(s+&#x27;$&#x27;)
    assert parse_string(g) == &#x27;success&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-07-02-generalized-ll-parser.py).


