---
published: true
title: Incorporating Indentation Parsing in Standard Parsers -- PEG
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
indentation sensitive parsing to combinatory parsers. There were two things
that made that solution somewhat unsatisfactory. The first is that we had to
use a lexer first, and generate lexical tokens before we could actually
parse. This is unsatisfactory because it forces us to deal with two different
kinds of grammars -- the lexical grammar of tokens and the parsing grammar.
Given that we have reasonable complete grammar parsers such as
[PEG parser](/post/2018/09/06/peg-parsing/) and the [Earley
parser](/post/2021/02/06/earley-parsing/), it would be nicer if we can reuse
these parsers somehow. The second problem is that
combinatory parsers can be difficult to debug.

So, can we incorporate the indentation sensitive parsing to more standard
parsers? Turns out, it is fairly simple to retrofit Python like parsing to
standard grammar parsers. In this post we will see how to do that for
[PEG parsers](/post/2018/09/06/peg-parsing/). (The
[PEG parser post](/post/2018/09/06/peg-parsing/) post contains the background
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
z = 300;
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
## Delimited Parser
We first define our grammar.

<!--
############
import string
e_grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', ';', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letters>', '=','<expr>']],
    '<letter>': [[c] for c in string.ascii_letters],
    '<digit>': [[c] for c in string.digits],
    '<letters>': [
        ['<letter>', '<letters>'],
        ['<letter>']],
    '<digits>': [
        ['<digit>', '<digits>'],
        ['<digit>']],
    '<ifstmt>': [['if', '<expr>', '<block>']],
    '<expr>': [
        ['(', '<expr>', '==', '<expr>', ')'],
        ['(', '<expr>', '!=', '<expr>', ')'],
        ['<digits>'],
        ['<letters>']
        ],
    '<block>': [['{','<stmts>', '}']]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
e_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;stmts&gt;&#x27;]],
    &#x27;&lt;stmts&gt;&#x27;: [
        [&#x27;&lt;stmt&gt;&#x27;, &#x27;;&#x27;, &#x27;&lt;stmts&gt;&#x27;],
        [&#x27;&lt;stmt&gt;&#x27;]],
    &#x27;&lt;stmt&gt;&#x27;: [[&#x27;&lt;assignstmt&gt;&#x27;], [&#x27;&lt;ifstmt&gt;&#x27;]],
    &#x27;&lt;assignstmt&gt;&#x27;: [[&#x27;&lt;letters&gt;&#x27;, &#x27;=&#x27;,&#x27;&lt;expr&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[c] for c in string.ascii_letters],
    &#x27;&lt;digit&gt;&#x27;: [[c] for c in string.digits],
    &#x27;&lt;letters&gt;&#x27;: [
        [&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;letters&gt;&#x27;],
        [&#x27;&lt;letter&gt;&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;ifstmt&gt;&#x27;: [[&#x27;if&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;&lt;block&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;==&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;!=&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;letters&gt;&#x27;]
        ],
    &#x27;&lt;block&gt;&#x27;: [[&#x27;{&#x27;,&#x27;&lt;stmts&gt;&#x27;, &#x27;}&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
### Text
We want a stream of text that we can manipulate where needed. This stream
will allow us to control our parsing.

<!--
############
class Text:
    def __init__(self, text, at=0):
        self.text, self.at = text, at

    def _match(self, t):
        return self.text[self.at:self.at+len(t)] == t

    def advance(self, t):
        if self._match(t):
            return Text(self.text, self.at + len(t))
        else:
            return None

    def __repr__(self):
        return repr(self.text[:self.at]+ '|' +self.text[self.at:])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Text:
    def __init__(self, text, at=0):
        self.text, self.at = text, at

    def _match(self, t):
        return self.text[self.at:self.at+len(t)] == t

    def advance(self, t):
        if self._match(t):
            return Text(self.text, self.at + len(t))
        else:
            return None

    def __repr__(self):
        return repr(self.text[:self.at]+ &#x27;|&#x27; +self.text[self.at:])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we modify our PEG parser so that we can use the text stream instead of
the array.

### PEG

<!--
############
class peg_parser:
    def __init__(self, grammar):
        self.grammar = grammar

    def parse(self, key, text):
        return self.unify_key(key, Text(text))

    def unify_key(self, key, text):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return v, (key, [])
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text):
        results = []
        for part in parts:
            text, res = self.unify_key(part, text)
            if res is None: return text, None
            results.append(res)
        return text, results

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class peg_parser:
    def __init__(self, grammar):
        self.grammar = grammar

    def parse(self, key, text):
        return self.unify_key(key, Text(text))

    def unify_key(self, key, text):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return v, (key, [])
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text):
        results = []
        for part in parts:
            text, res = self.unify_key(part, text)
            if res is None: return text, None
            results.append(res)
        return text, results
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
my_text = 'if(a==1){x=10}'
v, res = peg_parser(e_grammar).parse('<start>', my_text)
print(len(my_text), '<>', v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text = &#x27;if(a==1){x=10}&#x27;
v, res = peg_parser(e_grammar).parse(&#x27;&lt;start&gt;&#x27;, my_text)
print(len(my_text), &#x27;&lt;&gt;&#x27;, v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
It is often useful to understand the parser actions. Hence, we also define
a parse visualizer as follows.

<!--
############
class peg_parser_visual(peg_parser):
    def __init__(self, grammar, loginit=False, logfalse=False):
        self.grammar = grammar
        self.loginit = loginit
        self.logfalse = logfalse

    def log(self, depth, *args):
        print(' '*depth, *args)

    def unify_key(self, key, text, _stackdepth=0):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return (v, (key, []))
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, _stackdepth+1)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text, _stackdepth):
        results = []
        text_ = text
        for part in parts:
            if self.loginit:
                self.log(_stackdepth,' ', part, '=>', repr(text))
            text_, res = self.unify_key(part, text_, _stackdepth)
            if res is not None:
                self.log(_stackdepth, part, '#', '=>', repr(text_))
            elif self.logfalse:
                self.log(_stackdepth, part, '_', '=>', repr(text_))
            if res is None: return text, None
            results.append(res)
        return text_, results

    def parse(self, key, text):
        return self.unify_key(key, Text(text), 0)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class peg_parser_visual(peg_parser):
    def __init__(self, grammar, loginit=False, logfalse=False):
        self.grammar = grammar
        self.loginit = loginit
        self.logfalse = logfalse

    def log(self, depth, *args):
        print(&#x27; &#x27;*depth, *args)

    def unify_key(self, key, text, _stackdepth=0):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return (v, (key, []))
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, _stackdepth+1)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text, _stackdepth):
        results = []
        text_ = text
        for part in parts:
            if self.loginit:
                self.log(_stackdepth,&#x27; &#x27;, part, &#x27;=&gt;&#x27;, repr(text))
            text_, res = self.unify_key(part, text_, _stackdepth)
            if res is not None:
                self.log(_stackdepth, part, &#x27;#&#x27;, &#x27;=&gt;&#x27;, repr(text_))
            elif self.logfalse:
                self.log(_stackdepth, part, &#x27;_&#x27;, &#x27;=&gt;&#x27;, repr(text_))
            if res is None: return text, None
            results.append(res)
        return text_, results

    def parse(self, key, text):
        return self.unify_key(key, Text(text), 0)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
my_text = '(12==a)'
v, res = peg_parser_visual(e_grammar).parse('<expr>', my_text)
print(len(my_text), '<>', v.at)
F.display_tree(res)

my_text = '12'
v, res = peg_parser_visual(e_grammar,
        loginit=True,logfalse=True).parse('<digits>', my_text)
print(len(my_text), '<>', v.at)
F.display_tree(res)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text = &#x27;(12==a)&#x27;
v, res = peg_parser_visual(e_grammar).parse(&#x27;&lt;expr&gt;&#x27;, my_text)
print(len(my_text), &#x27;&lt;&gt;&#x27;, v.at)
F.display_tree(res)

my_text = &#x27;12&#x27;
v, res = peg_parser_visual(e_grammar,
        loginit=True,logfalse=True).parse(&#x27;&lt;digits&gt;&#x27;, my_text)
print(len(my_text), &#x27;&lt;&gt;&#x27;, v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Indentation Based Parser
For indentation based parsing, we modify our string stream slightly. The idea
is that when the parser is expecting a new line that corresponds to a new
block (indentation) or a delimiter, then it will specifically ask for `<$nl>`
token from the text stream. The text stream will first try to satisfy the
new line request. If the request can be satisfied, it will also try to
identify the new indentation level. If the new indentation level is
more than the current indentation level, it will insert a new `<$indent>`
token into the text stream. If on the other hand, the new indentation level
is less than the current level, it will generate as many `<$dedent>` tokens
as required that will match the new indentation level. 
### IText

<!--
############
class IText(Text):
    def __init__(self, text, at=0, buf=None, indent=None):
        self.text, self.at = text, at
        self.buffer = [] if buf is None else buf
        self._indent = [0] if indent is None else indent

    def advance(self, t):
        if t == '<$nl>': return self._advance_nl()
        else: return self._advance(t)

    def _advance(self, t):
        if self.buffer:
            if self.buffer[0] != t: return None
            return IText(self.text, self.at, self.buffer[1:], self._indent)
        elif self.text[self.at:self.at+len(t)] != t:
            return None
        return IText(self.text, self.at + len(t), self.buffer, self._indent)

    def _read_indent(self, at):
        indent = 0
        while self.text[at+indent:at+indent+1] == ' ':
            indent += 1
        return indent, at+indent

    def _advance_nl(self):
        if self.buffer: return None
        if self.text[self.at] != '\n': return None
        my_indent, my_buf = self._indent, self.buffer
        i, at = self._read_indent(self.at+1)
        if i > my_indent[-1]:
            my_indent, my_buf = my_indent + [i], ['<$indent>'] + my_buf
        else:
            while i < my_indent[-1]:
                my_indent, my_buf = my_indent[:-1], ['<$dedent>'] + my_buf
        return IText(self.text, at, my_buf, my_indent)

    def __repr__(self):
        return (repr(self.text[:self.at])+ '|' + ''.join(self.buffer) + '|'  +
                repr(self.text[self.at:]))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class IText(Text):
    def __init__(self, text, at=0, buf=None, indent=None):
        self.text, self.at = text, at
        self.buffer = [] if buf is None else buf
        self._indent = [0] if indent is None else indent

    def advance(self, t):
        if t == &#x27;&lt;$nl&gt;&#x27;: return self._advance_nl()
        else: return self._advance(t)

    def _advance(self, t):
        if self.buffer:
            if self.buffer[0] != t: return None
            return IText(self.text, self.at, self.buffer[1:], self._indent)
        elif self.text[self.at:self.at+len(t)] != t:
            return None
        return IText(self.text, self.at + len(t), self.buffer, self._indent)

    def _read_indent(self, at):
        indent = 0
        while self.text[at+indent:at+indent+1] == &#x27; &#x27;:
            indent += 1
        return indent, at+indent

    def _advance_nl(self):
        if self.buffer: return None
        if self.text[self.at] != &#x27;\n&#x27;: return None
        my_indent, my_buf = self._indent, self.buffer
        i, at = self._read_indent(self.at+1)
        if i &gt; my_indent[-1]:
            my_indent, my_buf = my_indent + [i], [&#x27;&lt;$indent&gt;&#x27;] + my_buf
        else:
            while i &lt; my_indent[-1]:
                my_indent, my_buf = my_indent[:-1], [&#x27;&lt;$dedent&gt;&#x27;] + my_buf
        return IText(self.text, at, my_buf, my_indent)

    def __repr__(self):
        return (repr(self.text[:self.at])+ &#x27;|&#x27; + &#x27;&#x27;.join(self.buffer) + &#x27;|&#x27;  +
                repr(self.text[self.at:]))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We will first define a small grammar to test it out.

<!--
############
g1 = {
    '<start>': [['<ifstmt>']],
    '<stmt>': [['<assignstmt>']],
    '<assignstmt>': [['<letter>', '<$nl>']],
    '<letter>': [['a']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<block>': [['<$indent>','<stmt>', '<$dedent>']]
}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g1 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;ifstmt&gt;&#x27;]],
    &#x27;&lt;stmt&gt;&#x27;: [[&#x27;&lt;assignstmt&gt;&#x27;]],
    &#x27;&lt;assignstmt&gt;&#x27;: [[&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[&#x27;a&#x27;]],
    &#x27;&lt;ifstmt&gt;&#x27;: [[&#x27;if &#x27;, &#x27;&lt;letter&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;$nl&gt;&#x27;, &#x27;&lt;block&gt;&#x27;]],
    &#x27;&lt;block&gt;&#x27;: [[&#x27;&lt;$indent&gt;&#x27;,&#x27;&lt;stmt&gt;&#x27;, &#x27;&lt;$dedent&gt;&#x27;]]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is our text that corresponds to the g1 grammar.

<!--
############
my_text = """\
if a:
    a
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text = &quot;&quot;&quot;\
if a:
    a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now use the same parser with the text stream.

<!--
############
v, res = peg_parser(g1).unify_key('<start>', IText(my_text))
assert(len(my_text) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g1).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text))
assert(len(my_text) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here is a slightly more complex grammar and corresponding text

<!--
############
g2 = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<ifstmt>'], ['<assignstmt>']],
    '<assignstmt>': [['<letter>', '<$nl>']],
    '<letter>': [['a']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}
my_text = """\
a
a
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
g2 = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;stmts&gt;&#x27;]],
    &#x27;&lt;stmts&gt;&#x27;: [
        [&#x27;&lt;stmt&gt;&#x27;, &#x27;&lt;stmts&gt;&#x27;],
        [&#x27;&lt;stmt&gt;&#x27;]],
    &#x27;&lt;stmt&gt;&#x27;: [[&#x27;&lt;ifstmt&gt;&#x27;], [&#x27;&lt;assignstmt&gt;&#x27;]],
    &#x27;&lt;assignstmt&gt;&#x27;: [[&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[&#x27;a&#x27;]],
    &#x27;&lt;ifstmt&gt;&#x27;: [[&#x27;if &#x27;, &#x27;&lt;letter&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;$nl&gt;&#x27;, &#x27;&lt;block&gt;&#x27;]],
    &#x27;&lt;block&gt;&#x27;: [[&#x27;&lt;$indent&gt;&#x27;,&#x27;&lt;stmts&gt;&#x27;, &#x27;&lt;$dedent&gt;&#x27;]]
}
my_text = &quot;&quot;&quot;\
a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Checking if the text is parsable.

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text))
assert(len(my_text) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text))
assert(len(my_text) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another test

<!--
############
my_text1 = """\
if a:
    a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text1 = &quot;&quot;&quot;\
if a:
    a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text1))
assert(len(my_text1) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text1))
assert(len(my_text1) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text2 = """\
if a:
    a
    a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text2 = &quot;&quot;&quot;\
if a:
    a
    a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text2))
assert(len(my_text2) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text2))
assert(len(my_text2) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text3 = """\
if a:
    a
    a
a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text3 = &quot;&quot;&quot;\
if a:
    a
    a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text3))
assert(len(my_text3) == v.at)
F.display_tree(res)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text3))
assert(len(my_text3) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text4 = """\
a
a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text4 = &quot;&quot;&quot;\
a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text4))
assert(len(my_text4) == v.at)
F.display_tree(res)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text4))
assert(len(my_text4) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text5 = """\
if a:
    if a:
        a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text5 = &quot;&quot;&quot;\
if a:
    if a:
        a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text5))
assert(len(my_text5) == v.at)
F.display_tree(res)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text5))
assert(len(my_text5) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text6 = """\
if a:
    if a:
        a
a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text6 = &quot;&quot;&quot;\
if a:
    if a:
        a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text6))
assert(len(my_text6) == v.at)
F.display_tree(res)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text6))
assert(len(my_text6) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text7 = """\
if a:
    if a:
        a
        a
a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text7 = &quot;&quot;&quot;\
if a:
    if a:
        a
        a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text7))
assert(len(my_text7) == v.at)
F.display_tree(res)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text7))
assert(len(my_text7) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Another

<!--
############
my_text8 = """\
if a:
    if a:
        a
        a
    if a:
        a
a
"""
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_text8 = &quot;&quot;&quot;\
if a:
    if a:
        a
        a
    if a:
        a
a
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(g2).unify_key('<start>', IText(my_text8))
assert(len(my_text8) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(g2).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text8))
assert(len(my_text8) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us make a much larger grammar

<!--
############
e_grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letters>', '=','<expr>', '<$nl>']],
    '<letter>': [[c] for c in string.ascii_letters],
    '<digit>': [[c] for c in string.digits],
    '<letters>': [
        ['<letter>', '<letters>'],
        ['<letter>']],
    '<digits>': [
        ['<digit>', '<digits>'],
        ['<digit>']],
    '<ifstmt>': [['if', '<expr>', ':', '<$nl>', '<block>']],
    '<expr>': [
        ['(', '<expr>', '==', '<expr>', ')'],
        ['(', '<expr>', '!=', '<expr>', ')'],
        ['<digits>'],
        ['<letters>']
        ],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}
my_text9 = '''\
if(a==1):
    x=10
'''
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
e_grammar = {
    &#x27;&lt;start&gt;&#x27;: [[&#x27;&lt;stmts&gt;&#x27;]],
    &#x27;&lt;stmts&gt;&#x27;: [
        [&#x27;&lt;stmt&gt;&#x27;, &#x27;&lt;stmts&gt;&#x27;],
        [&#x27;&lt;stmt&gt;&#x27;]],
    &#x27;&lt;stmt&gt;&#x27;: [[&#x27;&lt;assignstmt&gt;&#x27;], [&#x27;&lt;ifstmt&gt;&#x27;]],
    &#x27;&lt;assignstmt&gt;&#x27;: [[&#x27;&lt;letters&gt;&#x27;, &#x27;=&#x27;,&#x27;&lt;expr&gt;&#x27;, &#x27;&lt;$nl&gt;&#x27;]],
    &#x27;&lt;letter&gt;&#x27;: [[c] for c in string.ascii_letters],
    &#x27;&lt;digit&gt;&#x27;: [[c] for c in string.digits],
    &#x27;&lt;letters&gt;&#x27;: [
        [&#x27;&lt;letter&gt;&#x27;, &#x27;&lt;letters&gt;&#x27;],
        [&#x27;&lt;letter&gt;&#x27;]],
    &#x27;&lt;digits&gt;&#x27;: [
        [&#x27;&lt;digit&gt;&#x27;, &#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;digit&gt;&#x27;]],
    &#x27;&lt;ifstmt&gt;&#x27;: [[&#x27;if&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;:&#x27;, &#x27;&lt;$nl&gt;&#x27;, &#x27;&lt;block&gt;&#x27;]],
    &#x27;&lt;expr&gt;&#x27;: [
        [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;==&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;(&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;!=&#x27;, &#x27;&lt;expr&gt;&#x27;, &#x27;)&#x27;],
        [&#x27;&lt;digits&gt;&#x27;],
        [&#x27;&lt;letters&gt;&#x27;]
        ],
    &#x27;&lt;block&gt;&#x27;: [[&#x27;&lt;$indent&gt;&#x27;,&#x27;&lt;stmts&gt;&#x27;, &#x27;&lt;$dedent&gt;&#x27;]]
}
my_text9 = &#x27;&#x27;&#x27;\
if(a==1):
    x=10
&#x27;&#x27;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
v, res = peg_parser(e_grammar).unify_key('<start>', IText(my_text9))
assert(len(my_text9) == v.at)
F.display_tree(res)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
v, res = peg_parser(e_grammar).unify_key(&#x27;&lt;start&gt;&#x27;, IText(my_text9))
assert(len(my_text9) == v.at)
F.display_tree(res)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As can be seen, we require no changes to the standard PEG parser for
incorporating indentation sensitive (layout sensitive) parsing. The situation
is same for other parsers such as Earley parsing.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-06-05-peg-parsing-indentation.py).


