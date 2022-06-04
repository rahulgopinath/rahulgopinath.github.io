---
published: true
title: Parsing Indentation Sensitive Languages
layout: post
comments: true
tags: combinators, parsing, cfg, indentation
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
We have previously seen how to parse strings using both [context-free
grammars](/post/2021/02/06/earley-parsing/), as well as usin [combinatory
parsers](https://rahul.gopinath.org/post/2020/03/02/combinatory-parsing/).
However, languages such as Python and Haskell cannot be directly parsed by
these parsers. This is because they use indentation levels to indicate
nested statement groups.
For example, given:
```
if True:
   x = 100
   y = 200
```
Python groups the `x = 100` and `y = 200` together, and is parsed equivalent
to
```
if True: {
   x = 100;
   y = 200;
}
```
in a `C` like language. This use of indentation is hard to capture in
context-free grammars.
Interestingly, it turns out that there is an easy solution. We can simply
keep track of the indentation and de-indentation for identifying groups.
The idea here is to first use a lexical analyzer to translate the source code
into tokens, and then post-process these tokens to insert *Indent* and
*Dedent* tokens. Hence, we start by defining our lexical analyzer. Turns out,
our combinatory parser is really good as a lexical analyzer.
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
<li><a href="https://rahul.gopinath.org/py/combinatoryparser-0.0.1-py2.py3-none-any.whl">combinatoryparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2020/03/02/combinatory-parsing/">Simple Combinatory Parsing For Context Free Languages</a>".</li>
<li><a href="https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl">simplefuzzer-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2019/05/28/simplefuzzer-01/">The simplest grammar fuzzer in the world</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/combinatoryparser-0.0.1-py2.py3-none-any.whl
https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import combinatoryparser as C

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import combinatoryparser as C
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Tokens
We start by defining a minimal set of tokens necessary to lex a simple
language.

<!--
############
def to_val(name):
    return lambda v: [(name, ''.join([i for i in v]))]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_val(name):
    return lambda v: [(name, &#x27;&#x27;.join([i for i in v]))]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Numeric literals represent numbers.

<!--
############
numeric_literal = C.P(lambda:
        C.Apply(to_val('NumericLiteral'), lambda: C.Re('^[0-9][0-9_.]*')))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
numeric_literal = C.P(lambda:
        C.Apply(to_val(&#x27;NumericLiteral&#x27;), lambda: C.Re(&#x27;^[0-9][0-9_.]*&#x27;)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
for to_parse, parsed in numeric_literal(list('123')):
    if to_parse: continue
    print(parsed)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for to_parse, parsed in numeric_literal(list(&#x27;123&#x27;)):
    if to_parse: continue
    print(parsed)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Quoted literals represent strings.

<!--
############
quoted_literal = C.P(lambda:
        C.Apply(to_val('QuotedLiteral'), lambda: C.Re('^"[^"]*"')))
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
quoted_literal = C.P(lambda:
        C.Apply(to_val(&#x27;QuotedLiteral&#x27;), lambda: C.Re(&#x27;^&quot;[^&quot;]*&quot;&#x27;)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
for to_parse, parsed in quoted_literal(list('"abc def"')):
    if to_parse: continue
    print(parsed)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for to_parse, parsed in quoted_literal(list(&#x27;&quot;abc def&quot;&#x27;)):
    if to_parse: continue
    print(parsed)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Punctuation represent operators and other punctuation

<!--
############
punctuation = C.P(lambda:
        C.Apply(to_val('Punctuation'), lambda:
            C.Re('^[!#$%&()*+,-./:;<=>?@\[\]^`{|}~\\\\]+')))
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
punctuation = C.P(lambda:
        C.Apply(to_val(&#x27;Punctuation&#x27;), lambda:
            C.Re(&#x27;^[!#$%&amp;()*+,-./:;&lt;=&gt;?@\[\]^`{|}~\\\\]+&#x27;)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
for to_parse, parsed in punctuation(list('<=')):
    if to_parse: continue
    print(parsed)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for to_parse, parsed in punctuation(list(&#x27;&lt;=&#x27;)):
    if to_parse: continue
    print(parsed)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Name represents function and variable names, and other names in the program.

<!--
############
name = C.P(lambda: C.Apply(to_val('Name'), lambda: C.Re('^[a-zA-Z_]+')))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
name = C.P(lambda: C.Apply(to_val(&#x27;Name&#x27;), lambda: C.Re(&#x27;^[a-zA-Z_]+&#x27;)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need to represent new lines and whitespace.

<!--
############
nl = C.P(lambda: C.Apply(to_val('NL'), lambda: C.Lit('\n')))

ws = C.P(lambda: C.Apply(to_val('WS'), lambda: C.Re('^[ ]+')))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
nl = C.P(lambda: C.Apply(to_val(&#x27;NL&#x27;), lambda: C.Lit(&#x27;\n&#x27;)))

ws = C.P(lambda: C.Apply(to_val(&#x27;WS&#x27;), lambda: C.Re(&#x27;^[ ]+&#x27;)))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
With these, we can define our tokenizer as follows. A lexical token can
anything that we previously defined.

<!--
############
lex = numeric_literal | quoted_literal | punctuation | name | nl | ws

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
lex = numeric_literal | quoted_literal | punctuation | name | nl | ws
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
And the source string can contain any number of such tokens.

<!--
############
lexs =  C.P(lambda: lex | (lex >> lexs))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
lexs =  C.P(lambda: lex | (lex &gt;&gt; lexs))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Tokenize
We can now define our tokenizer as follows.

<!--
############
def tokenize(mystring):
    for (rem,lexed) in lexs(list(mystring)):
        if rem: continue
        return lexed
    raise Exception('Unable to tokenize')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def tokenize(mystring):
    for (rem,lexed) in lexs(list(mystring)):
        if rem: continue
        return lexed
    raise Exception(&#x27;Unable to tokenize&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
lex_tokens = tokenize('ab + cd < " xyz "')
print(lex_tokens)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
lex_tokens = tokenize(&#x27;ab + cd &lt; &quot; xyz &quot;&#x27;)
print(lex_tokens)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Indents
Next, we want to insert indentation and de-indentation. We do that by keeping
a stack of seen indentation levels. If the new indentation level is greater
than the current indentation level, we push the new indentation level into
the stack. If the indentation level is smaller, the we pop the stack until we
reach the correct indentation level.

<!--
############
def generate_indents(tokens):
    indents = [0]
    stream = []
    while tokens:
        token, *tokens  = tokens
        # did a nested block begin
        if token[0] == 'NL':
            if not tokens:
                stream.append(token)
                dedent(0, indents, stream)
                break
            elif tokens[0][0] == 'WS':
                indent = len(tokens[0][1])
                if indent > indents[-1]:
                    indents.append(indent)
                    stream.append(('Indent', indent))
                elif indent == indents[-1]:
                    stream.append(token)
                else:
                    stream.append(token)
                    dedent(indent, indents, stream)
                tokens = tokens[1:]
            else:
                stream.append(token)
                dedent(0, indents, stream)
        else:
            stream.append(token)
    assert len(indents) == 1
    return stream

def dedent(indent, indents, stream):
    while indent < indents[-1]:
        indents.pop()
        stream.append(('Dedent', indents[-1]))
    assert indent == indents[-1]
    return

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def generate_indents(tokens):
    indents = [0]
    stream = []
    while tokens:
        token, *tokens  = tokens
        # did a nested block begin
        if token[0] == &#x27;NL&#x27;:
            if not tokens:
                stream.append(token)
                dedent(0, indents, stream)
                break
            elif tokens[0][0] == &#x27;WS&#x27;:
                indent = len(tokens[0][1])
                if indent &gt; indents[-1]:
                    indents.append(indent)
                    stream.append((&#x27;Indent&#x27;, indent))
                elif indent == indents[-1]:
                    stream.append(token)
                else:
                    stream.append(token)
                    dedent(indent, indents, stream)
                tokens = tokens[1:]
            else:
                stream.append(token)
                dedent(0, indents, stream)
        else:
            stream.append(token)
    assert len(indents) == 1
    return stream

def dedent(indent, indents, stream):
    while indent &lt; indents[-1]:
        indents.pop()
        stream.append((&#x27;Dedent&#x27;, indents[-1]))
    assert indent == indents[-1]
    return
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
we can now extract the indentation based blocks as follows

<!--
############
example = """\
if foo:
    if bar:
        x = 42
        y = 100
else:
    print foo
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
example = &quot;&quot;&quot;\
if foo:
    if bar:
        x = 42
        y = 100
else:
    print foo
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
tokens = tokenize(example)
res = generate_indents(tokens)
current_indent = 0
for k in res:
    if k[0] in 'Indent':
        current_indent = k[1]
        print()
        print(' ' * current_indent + '{')
        print(current_indent * ' ', end = '')
    elif k[0] in 'Dedent':
        print()
        print(current_indent * ' ' + '}')
        current_indent = k[1]
    elif k[0] in 'NL':
        print()
        print(current_indent * ' ', end = '')
    else:
        print(k[1], end = '')
print()

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
tokens = tokenize(example)
res = generate_indents(tokens)
current_indent = 0
for k in res:
    if k[0] in &#x27;Indent&#x27;:
        current_indent = k[1]
        print()
        print(&#x27; &#x27; * current_indent + &#x27;{&#x27;)
        print(current_indent * &#x27; &#x27;, end = &#x27;&#x27;)
    elif k[0] in &#x27;Dedent&#x27;:
        print()
        print(current_indent * &#x27; &#x27; + &#x27;}&#x27;)
        current_indent = k[1]
    elif k[0] in &#x27;NL&#x27;:
        print()
        print(current_indent * &#x27; &#x27;, end = &#x27;&#x27;)
    else:
        print(k[1], end = &#x27;&#x27;)
print()
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
At this point, we can apply a standard context-free parser for parsing the
produced tokens. We use a simple Combinatory parser for that.
## Combinatory parser

<!--
############
def NoParse():
    def parse(instr): return [(instr, [('Empty',)])]
    return parse

def Keyword(k):
    def parse(instr):
        if instr and instr[0] == ('Name', k):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Literal(k):
    def parse(instr):
        if instr and instr[0][0] == k:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def NL():
    def parse(instr):
        if instr and instr[0][0] == 'NL':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def WS():
    def parse(instr):
        if instr and instr[0][0] == 'WS':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Name():
    def parse(instr):
        if instr and instr[0][0] == 'Name':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Punct(c):
    def parse(instr):
        if instr and instr[0] == ('Punctuation', c):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Indent():
    def parse(instr):
        if instr and instr[0][0] == 'Indent':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Dedent():
    def parse(instr):
        if instr and instr[0][0] == 'Dedent':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def NoParse():
    def parse(instr): return [(instr, [(&#x27;Empty&#x27;,)])]
    return parse

def Keyword(k):
    def parse(instr):
        if instr and instr[0] == (&#x27;Name&#x27;, k):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Literal(k):
    def parse(instr):
        if instr and instr[0][0] == k:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def NL():
    def parse(instr):
        if instr and instr[0][0] == &#x27;NL&#x27;:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def WS():
    def parse(instr):
        if instr and instr[0][0] == &#x27;WS&#x27;:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Name():
    def parse(instr):
        if instr and instr[0][0] == &#x27;Name&#x27;:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Punct(c):
    def parse(instr):
        if instr and instr[0] == (&#x27;Punctuation&#x27;, c):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Indent():
    def parse(instr):
        if instr and instr[0][0] == &#x27;Indent&#x27;:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Dedent():
    def parse(instr):
        if instr and instr[0][0] == &#x27;Dedent&#x27;:
            return [(instr[1:], [instr[0]])]
        return []
    return parse
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
example = """\
if False:
    if True:
        x = "ab cd"
        y = 100
z = 1
"""

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
example = &quot;&quot;&quot;\
if False:
    if True:
        x = &quot;ab cd&quot;
        y = 100
z = 1
&quot;&quot;&quot;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<!--
############
def to_valA(name):
    return lambda v: [(name, v)]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def to_valA(name):
    return lambda v: [(name, v)]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
For display

<!--
############
def get_children(node):
    if node[0] in ['Name', 'WS', 'Empty', 'Punctuation', 'Indent', 'Dedent',
            'QuotedLiteral', 'NumericLiteral', 'NL']:
        return []
    return node[1]

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_children(node):
    if node[0] in [&#x27;Name&#x27;, &#x27;WS&#x27;, &#x27;Empty&#x27;, &#x27;Punctuation&#x27;, &#x27;Indent&#x27;, &#x27;Dedent&#x27;,
            &#x27;QuotedLiteral&#x27;, &#x27;NumericLiteral&#x27;, &#x27;NL&#x27;]:
        return []
    return node[1]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Tokenizing

<!--
############
tokens = tokenize(example)
print(tokens)
res = generate_indents(tokens)
for k in res:
    print(k)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
tokens = tokenize(example)
print(tokens)
res = generate_indents(tokens)
for k in res:
    print(k)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Parsing

<!--
############
ifkey = C.P(lambda: Keyword('if'))
empty = C.P(lambda: NoParse())
name = C.P(lambda: Name())
expr = C.P(lambda:
        C.Apply(
            to_valA('Expr'),
            lambda: name | nlit | qlit)
        )
ws = C.P(lambda: WS())
nl = C.P(lambda: NL())
spaces = C.P(lambda: (ws >> spaces) | empty)
colon = C.P(lambda: Punct(':'))
equals = C.P(lambda: Punct('='))
nlit = C.P(lambda: Literal('NumericLiteral'))
qlit = C.P(lambda: Literal('QuotedLiteral'))
indent = C.P(lambda: Indent())
dedent = C.P(lambda: Dedent())

assignstmt = C.P(lambda:
        C.Apply(
            to_valA('Assignment'),
            lambda: name >> spaces >> equals >> spaces >> (nlit | qlit) >> nl)
        )
ifstmt =  C.P(lambda:
        C.Apply(
            to_valA('If'),
            lambda: ifkey >> spaces >> expr >> spaces >> colon >> block)
        )

block = C.P(lambda: (indent >> stmts >> dedent) | stmts)

stmt = C.P(lambda:
        C.Apply(
            to_valA('Statement'),
            lambda: ifstmt | assignstmt)
        )

stmts = C.P(lambda:
        C.Apply(
            to_valA('Stmts'),
            lambda: stmt| (stmt >> stmts))
        )

for to_parse, parsed in stmts(res):
    if not to_parse:
        C.display_trees(parsed, get_children=get_children)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
ifkey = C.P(lambda: Keyword(&#x27;if&#x27;))
empty = C.P(lambda: NoParse())
name = C.P(lambda: Name())
expr = C.P(lambda:
        C.Apply(
            to_valA(&#x27;Expr&#x27;),
            lambda: name | nlit | qlit)
        )
ws = C.P(lambda: WS())
nl = C.P(lambda: NL())
spaces = C.P(lambda: (ws &gt;&gt; spaces) | empty)
colon = C.P(lambda: Punct(&#x27;:&#x27;))
equals = C.P(lambda: Punct(&#x27;=&#x27;))
nlit = C.P(lambda: Literal(&#x27;NumericLiteral&#x27;))
qlit = C.P(lambda: Literal(&#x27;QuotedLiteral&#x27;))
indent = C.P(lambda: Indent())
dedent = C.P(lambda: Dedent())

assignstmt = C.P(lambda:
        C.Apply(
            to_valA(&#x27;Assignment&#x27;),
            lambda: name &gt;&gt; spaces &gt;&gt; equals &gt;&gt; spaces &gt;&gt; (nlit | qlit) &gt;&gt; nl)
        )
ifstmt =  C.P(lambda:
        C.Apply(
            to_valA(&#x27;If&#x27;),
            lambda: ifkey &gt;&gt; spaces &gt;&gt; expr &gt;&gt; spaces &gt;&gt; colon &gt;&gt; block)
        )

block = C.P(lambda: (indent &gt;&gt; stmts &gt;&gt; dedent) | stmts)

stmt = C.P(lambda:
        C.Apply(
            to_valA(&#x27;Statement&#x27;),
            lambda: ifstmt | assignstmt)
        )

stmts = C.P(lambda:
        C.Apply(
            to_valA(&#x27;Stmts&#x27;),
            lambda: stmt| (stmt &gt;&gt; stmts))
        )

for to_parse, parsed in stmts(res):
    if not to_parse:
        C.display_trees(parsed, get_children=get_children)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2022-06-04-parsing-indentation.py).


