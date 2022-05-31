---
published: true
title: Parsing XML with a context free grammar
layout: post
comments: true
tags: parsing
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
Note: The grammar is based on the XML grammar in [the fuzzingbook](https://www.fuzzingbook.org/html/GreyboxGrammarFuzzer.html#Parsing-and-Recombining-HTML).

XML (and its relatives like HTML) is present pretty much everywhere at this
point. One of the problems with XML is that, while the idea of XML is really
simple, the implementation is fairly heavyweight, with Apache Xerces Java
clocking at 127 KLOC of Java files.

Do we really need such a heavyweight machinery? especially if one is only
interested in a subset of the functionality of XML? Similar languages such
as JSON clock in at a few hundred lines of code.

XML is a context sensitive language, and hence, it is hard to write a parser
for it.  However, XML if you look at it, is a parenthesis language, and except
for the open and close tag matching, doesn't have long range context sensitive
features. So, can we parse and validate XML using a parser that accepts
simple context free parsers? 

Turns out, one can! The idea is to simply use a context-free grammar that
ignores the requirement that the closing tag must match the opening tag, and
then use a secondary traversal to validate the open/close tags.

We define our grammar as below:

<!--
############
import string
xml_grammar = {
    '{.}': [['{xml}']],
    '{xml}': [
        ['{emptytag}'],
        ['{ntag}']],
    '{emptytag}': [
        ['<', '{tag}', '/>'],
    ],
    '{ntag}': [
        ['{opentag}', '{xmlfragment}', '{closetag}']],
    '{opentag}': [['<', '{tag}', '>']],
    '{closetag}': [['</', '{tag}', '>']],
    '{xmlfragment}': [
        ['{xml}', '{xmlfragment}'],
        ['{text}', '{xmlfragment}'],
        ['']],
    '{tag}': [
        ['{alphanum}', '{alphanums}']],
    '{alphanums}': [
        ['{alphanum}', '{alphanums}'],
        ['']],
    '{alphanum}': [['{digit}'], ['{letter}']],
    '{digit}': [[i] for i in string.digits],
    '{letter}': [[i] for i in string.ascii_letters],
    '{space}': [[i] for i in string.whitespace],
    '{text}': [['{salphanum}', '{text}'], ['{salphanum}']],
    '{salphanum}':  [['{digit}'], ['{letter}'], ['{space}']],
}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import string
xml_grammar = {
    &#x27;{.}&#x27;: [[&#x27;{xml}&#x27;]],
    &#x27;{xml}&#x27;: [
        [&#x27;{emptytag}&#x27;],
        [&#x27;{ntag}&#x27;]],
    &#x27;{emptytag}&#x27;: [
        [&#x27;&lt;&#x27;, &#x27;{tag}&#x27;, &#x27;/&gt;&#x27;],
    ],
    &#x27;{ntag}&#x27;: [
        [&#x27;{opentag}&#x27;, &#x27;{xmlfragment}&#x27;, &#x27;{closetag}&#x27;]],
    &#x27;{opentag}&#x27;: [[&#x27;&lt;&#x27;, &#x27;{tag}&#x27;, &#x27;&gt;&#x27;]],
    &#x27;{closetag}&#x27;: [[&#x27;&lt;/&#x27;, &#x27;{tag}&#x27;, &#x27;&gt;&#x27;]],
    &#x27;{xmlfragment}&#x27;: [
        [&#x27;{xml}&#x27;, &#x27;{xmlfragment}&#x27;],
        [&#x27;{text}&#x27;, &#x27;{xmlfragment}&#x27;],
        [&#x27;&#x27;]],
    &#x27;{tag}&#x27;: [
        [&#x27;{alphanum}&#x27;, &#x27;{alphanums}&#x27;]],
    &#x27;{alphanums}&#x27;: [
        [&#x27;{alphanum}&#x27;, &#x27;{alphanums}&#x27;],
        [&#x27;&#x27;]],
    &#x27;{alphanum}&#x27;: [[&#x27;{digit}&#x27;], [&#x27;{letter}&#x27;]],
    &#x27;{digit}&#x27;: [[i] for i in string.digits],
    &#x27;{letter}&#x27;: [[i] for i in string.ascii_letters],
    &#x27;{space}&#x27;: [[i] for i in string.whitespace],
    &#x27;{text}&#x27;: [[&#x27;{salphanum}&#x27;, &#x27;{text}&#x27;], [&#x27;{salphanum}&#x27;]],
    &#x27;{salphanum}&#x27;:  [[&#x27;{digit}&#x27;], [&#x27;{letter}&#x27;], [&#x27;{space}&#x27;]],
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

We use our [PEG parser from the previous post](/2018/09/06/peg-parsing/) to
parse XML. First we define a convenience method that translate a derivation
tree to its corresponding textual representation.

<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
<li><a href="https://rahul.gopinath.org/py/pegparser-0.0.1-py2.py3-none-any.whl">pegparser-0.0.1-py2.py3-none-any.whl</a> from "<a href="/post/2018/09/06/peg-parsing/">Recursive descent parsing with Parsing Expression (PEG) and Context Free (CFG) Grammars</a>".</li>
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
https://rahul.gopinath.org/py/pegparser-0.0.1-py2.py3-none-any.whl
</textarea>
</form>
</div>
</details>

<!--
############
import pegparser
import sys
import functools

def tree_to_string(tree, g):
    symbol, children, *_ = tree
    if children:
        return ''.join(tree_to_string(c, g) for c in children)
    else:
        return '' if (symbol in g) else symbol
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import pegparser
import sys
import functools

def tree_to_string(tree, g):
    symbol, children, *_ = tree
    if children:
        return &#x27;&#x27;.join(tree_to_string(c, g) for c in children)
    else:
        return &#x27;&#x27; if (symbol in g) else symbol
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
One thing we want to take care of is to translate
our derivations trees to actual XML DOM. So, we define a translator for the tree
as below.


<!--
############
def translate(tree, g, translations):
    symbol, children = tree
    if symbol in translations:
        return translations[symbol](tree, g, translations)
    return symbol, [translate(c, g, translations) for c in children]

def to_s(tree, g, translations):
    return (tree_to_string(tree, g), [])

translations = {
    '{opentag}': to_s,
    '{closetag}': to_s,
    '{emptytag}': to_s,
    '{text}': to_s
}
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def translate(tree, g, translations):
    symbol, children = tree
    if symbol in translations:
        return translations[symbol](tree, g, translations)
    return symbol, [translate(c, g, translations) for c in children]

def to_s(tree, g, translations):
    return (tree_to_string(tree, g), [])

translations = {
    &#x27;{opentag}&#x27;: to_s,
    &#x27;{closetag}&#x27;: to_s,
    &#x27;{emptytag}&#x27;: to_s,
    &#x27;{text}&#x27;: to_s
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

Now, all that is left to validate the tags.


<!--
############
def validate_key(key, tree, validate_fn):
    symbol, children = tree
    if symbol == key: validate_fn(children)

    for child in children:
        validate_key(key, child, validate_fn)

def validate_tags(nodes, g):
    first = tree_to_string(nodes[0], g)
    last = tree_to_string(nodes[-1], g)
    assert first[1:-2] == last[2:-2], 'incorrect tags'
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def validate_key(key, tree, validate_fn):
    symbol, children = tree
    if symbol == key: validate_fn(children)

    for child in children:
        validate_key(key, child, validate_fn)

def validate_tags(nodes, g):
    first = tree_to_string(nodes[0], g)
    last = tree_to_string(nodes[-1], g)
    assert first[1:-2] == last[2:-2], &#x27;incorrect tags&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, we define our parser. 


<!--
############
def parse_xml(to_parse):
    till, tree = pegparser.peg_parse(xml_grammar).unify_key('{.}', to_parse)
    assert (len(to_parse) - till) == 0
    assert tree_to_string(tree, xml_grammar) == to_parse
    new_tree = translate(tree, xml_grammar, translations)
    validate_key('{ntag}', new_tree, lambda nodes: validate_tags(nodes, xml_grammar))
    print(new_tree)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def parse_xml(to_parse):
    till, tree = pegparser.peg_parse(xml_grammar).unify_key(&#x27;{.}&#x27;, to_parse)
    assert (len(to_parse) - till) == 0
    assert tree_to_string(tree, xml_grammar) == to_parse
    new_tree = translate(tree, xml_grammar, translations)
    validate_key(&#x27;{ntag}&#x27;, new_tree, lambda nodes: validate_tags(nodes, xml_grammar))
    print(new_tree)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using

<!--
############
parse_xml('<t><c/>my text</t>')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
parse_xml(&#x27;&lt;t&gt;&lt;c/&gt;my text&lt;/t&gt;&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
try:
    parse_xml('<t><c></t>')
except Exception as e:
    print(e)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
try:
    parse_xml(&#x27;&lt;t&gt;&lt;c&gt;&lt;/t&gt;&#x27;)
except Exception as e:
    print(e)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2019-11-29-parsingxml.py).


