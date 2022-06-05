---
published: true
title: Incorporating Indentation Parsing in PEG
layout: post
comments: true
tags: peg, parsing, cfg, indentation
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
We previously [saw](/post/2022/06/04/parsing-indentation/) how to incorporate
indentation sensitive parsing to combinatory parsers. One of the problems
with combinatory parsers is that they can be difficult to debug. So, can we
incorporate the indentation sensitive parsing to more standard parsers? Turns
out, it is fairly simple to retrofit Python like parsing to
[PEG parsers](/post/2018/09/06/peg-parsing/). (The
[PEG parser](/post/2018/09/06/peg-parsing/) post contains the background
information on PEG parsers.)
That is, given
```
if True:
   if False:
      x = 100
      y = 200
z = 300
```
We want to parse it similar to
```
if True: {
   if False: {
      x = 100;
      y = 200;
   }
}
```
in a `C` like language.
As before, we start by importing our prerequisite packages.

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
import simplefuzzer as F

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import simplefuzzer as F
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Example.

Here is the text we want to parse.

<!--
############
my_text = '''\
if a=b:
    if c=d:
        a=b
    c=d
c=b
'''


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text = &#x27;&#x27;&#x27;\
if a=b:
    if c=d:
        a=b
    c=d
c=b
&#x27;&#x27;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Grammar
We first define our grammar. Within our grammar, we use `<$indent>` and
`<$dedent>` to wrap lines with similar indentation. We also use `<$nl>` as
delimiters when lines have similar indentation.

<!--
############
grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<$nl>', '<stmts>'],
        ['<stmt>', '<$nl>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letter>', '=','<letter>']],
    '<letter>': [['a'],['b'], ['c'], ['d']],
    '<ifstmt>': [['if ', '<expr>', ':', '<block>']],
    '<expr>': [['<letter>', '=', '<letter>']],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;stmts&gt;&#x27;]],
    &#x27;&lt;stmts&gt;&#x27;: [
        [&#x27;&lt;stmt&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;, &#x27;&lt;stmts&gt;&#x27;],
        [&#x27;&lt;stmt&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;],
        [&#x27;&lt;stmt&gt;&#x27;]],
    &#x27;&lt;stmt&gt;&#x27;: [[&#x27;&lt;assignstmt&gt;&#x27;], [&#x27;&lt;ifstmt&gt;&#x27;]],
    &#x27;&lt;assignstmt&gt;&#x27;: [[&#x27;&lt;letter&gt;&#x27;, &#x27;=&#x27;,&#x27;&lt;letter&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[&#x27;a&#x27;],[&#x27;b&#x27;], [&#x27;c&#x27;], [&#x27;d&#x27;]],
    &#x27;&lt;ifstmt&gt;&#x27;: [[&#x27;if &#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;block&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [[&#x27;&lt;letter&gt;&#x27;, &#x27;=&#x27;, &#x27;&lt;letter&gt;&#x27;]],
    &#x27;&lt;block&gt;&#x27;: [[&#x27;&lt;$indent&gt;&#x27;,&#x27;&lt;stmts&gt;&#x27;, &#x27;&lt;$dedent&gt;&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## ipeg_parse
Our class is initialized with the grammar. We also initialize a stack of
indentations.

<!--
############
class ipeg_parse:
    def __init__(self, grammar):
        self.grammar, self.indent = grammar, [0]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse:
    def __init__(self, grammar):
        self.grammar, self.indent = grammar, [0]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## read_indent
When given a line, we find the number of spaces occurring before a non-space
character is found.

<!--
############
def read_indent(text, at):
    indent = 0
    while text[at:at+1] == ' ':
        indent += 1
        at += 1
    return indent, at

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def read_indent(text, at):
    indent = 0
    while text[at:at+1] == &#x27; &#x27;:
        indent += 1
        at += 1
    return indent, at
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using it

<!--
############
print(read_indent('  abc', 0))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
print(read_indent(&#x27;  abc&#x27;, 0))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## unify_indent
Next, we define how to parse a nonterminal symbol. This is the area
where we hook indentation parsing. When unifying `<$indent>`,
we expect the text to contain a new line,
and we also expect an increase in indentation.

<!--
############
class ipeg_parse(ipeg_parse):
    def unify_indent(self, text, at):
        if text[at:at+1] != '\n': return (at, None)
        indent, at_ = read_indent(text, at+1)
        if indent <= self.indent[-1]: return (at, None)
        self.indent.append(indent)
        return (at_, ('<$indent>', []))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse(ipeg_parse):
    def unify_indent(self, text, at):
        if text[at:at+1] != &#x27;\n&#x27;: return (at, None)
        indent, at_ = read_indent(text, at+1)
        if indent &lt;= self.indent[-1]: return (at, None)
        self.indent.append(indent)
        return (at_, (&#x27;&lt;$indent&gt;&#x27;, []))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## unify_dedent
To unify a `<$dedent>` key, we simply have to pop off the current
indentation.

<!--
############
class ipeg_parse(ipeg_parse):
    def unify_dedent(self, text, at):
        self.indent.pop()
        return (at, ('<$dedent>', []))
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse(ipeg_parse):
    def unify_dedent(self, text, at):
        self.indent.pop()
        return (at, (&#x27;&lt;$dedent&gt;&#x27;, []))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## unify_nl
If the current key is `<$nl>`, then we
expect the current text to contain a new line. Furthermore, there may also be
a reduction in indentation.

<!--
############
class ipeg_parse(ipeg_parse):
    def unify_nl(self, text, at):
        if text[at:at+1] != '\n': return (at, None)
        indent, at_ = read_indent(text, at+1)
        assert indent <= self.indent[-1]
        return (at_, ('<$nl>', []))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse(ipeg_parse):
    def unify_nl(self, text, at):
        if text[at:at+1] != &#x27;\n&#x27;: return (at, None)
        indent, at_ = read_indent(text, at+1)
        assert indent &lt;= self.indent[-1]
        return (at_, (&#x27;&lt;$nl&gt;&#x27;, []))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## unify_key
With this, we are ready to define the main PEG parser.
The rest of the implementation is very similar to
[PEG parser](/post/2018/09/06/peg-parsing/) that we discussed before.

<!--
############
class ipeg_parse(ipeg_parse):
    def unify_key(self, key, text, at=0):
        if key == '<$nl>': return self.unify_nl(text, at)
        elif key == '<$indent>': return self.unify_indent(text, at)
        elif key == '<$dedent>': return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse(ipeg_parse):
    def unify_key(self, key, text, at=0):
        if key == &#x27;&lt;$nl&gt;&#x27;: return self.unify_nl(text, at)
        elif key == &#x27;&lt;$indent&gt;&#x27;: return self.unify_indent(text, at)
        elif key == &#x27;&lt;$dedent&gt;&#x27;: return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## unify_rule
We add some logging to unify_rule to see how the matching takes place.
Otherwise it is exactly same as the original PEG parser.

<!--
############
class ipeg_parse(ipeg_parse):
    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse(ipeg_parse):
    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
display

<!--
############
def get_children(node):
    if node[0] in ['<$indent>', '<$dedent>', '<$nl>']: return []
    return F.get_children(node)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_children(node):
    if node[0] in [&#x27;&lt;$indent&gt;&#x27;, &#x27;&lt;$dedent&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;]: return []
    return F.get_children(node)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now test it out

<!--
############
v, res = ipeg_parse(grammar).unify_key('<start>', my_text)
print(len(my_text), '<>', v)
F.display_tree(res, get_children=get_children)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = ipeg_parse(grammar).unify_key(&#x27;&lt;start&gt;&#x27;, my_text)
print(len(my_text), &#x27;&lt;&gt;&#x27;, v)
F.display_tree(res, get_children=get_children)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Visualization
Visualization can be of use when trying to debug grammars. So, here we add a
bit more log output.

<!--
############
class ipeg_parse_log(ipeg_parse):
    def __init__(self, grammar, log):
        self.grammar, self.indent, self._log = grammar, [0], log

    def unify_rule(self, parts, text, tfrom, _indent):
        results = []
        for part in parts:
            if self._log:
                print(' '*_indent, part, '=>', repr(text[tfrom:]))
            tfrom_, res = self.unify_key(part, text, tfrom, _indent+1)
            if self._log:
                print(' '*_indent, part, '=>', repr(text[tfrom:tfrom_]), "|",
                        repr(text[tfrom:]), res is not None)
            tfrom = tfrom_
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

    def unify_key(self, key, text, at=0, _indent=0):
        if key == '<$nl>': return self.unify_nl(text, at)
        elif key == '<$indent>': return self.unify_indent(text, at)
        elif key == '<$dedent>': return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at, _indent)
            if res is not None: return l, (key, res)
        return (0, None)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class ipeg_parse_log(ipeg_parse):
    def __init__(self, grammar, log):
        self.grammar, self.indent, self._log = grammar, [0], log

    def unify_rule(self, parts, text, tfrom, _indent):
        results = []
        for part in parts:
            if self._log:
                print(&#x27; &#x27;*_indent, part, &#x27;=&gt;&#x27;, repr(text[tfrom:]))
            tfrom_, res = self.unify_key(part, text, tfrom, _indent+1)
            if self._log:
                print(&#x27; &#x27;*_indent, part, &#x27;=&gt;&#x27;, repr(text[tfrom:tfrom_]), &quot;|&quot;,
                        repr(text[tfrom:]), res is not None)
            tfrom = tfrom_
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

    def unify_key(self, key, text, at=0, _indent=0):
        if key == &#x27;&lt;$nl&gt;&#x27;: return self.unify_nl(text, at)
        elif key == &#x27;&lt;$indent&gt;&#x27;: return self.unify_indent(text, at)
        elif key == &#x27;&lt;$dedent&gt;&#x27;: return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at, _indent)
            if res is not None: return l, (key, res)
        return (0, None)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
test with visualization

<!--
############
my_text = """
if a=b:
    a=b
c=d
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text = &quot;&quot;&quot;
if a=b:
    a=b
c=d
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = ipeg_parse_log(grammar, log=True).unify_key('<start>', my_text)
print(len(my_text), '<>', v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = ipeg_parse_log(grammar, log=True).unify_key(&#x27;&lt;start&gt;&#x27;, my_text)
print(len(my_text), &#x27;&lt;&gt;&#x27;, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-06-05-peg-parsing-indentation.py).


