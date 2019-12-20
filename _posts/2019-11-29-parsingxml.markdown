---
published: true
title: Parsing XML with a context free grammar
layout: post
comments: true
tags: parsing
categories: post
---

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

```python
import string
grammar = {
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
```

We use our [PEG parser from the previous post](/2018/09/06/peg-parsing/) to
parse XML. First we define a convenience method that translate a derivation
tree to its corresponding textual representation.

```python
import sys
import functools
import pegparser
import xmlgrammar

def tree_to_string(tree, g):
    symbol, children, *_ = tree
    if children:
        return ''.join(tree_to_string(c, g) for c in children)
    else:
        return '' if (symbol in g) else symbol
```

One thing we want to take care of is to translate
our derivations trees to actual XML DOM. So, we define a translator for the tree
as below.

```python
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
```

Now, all that is left to validate the tags.

```python
def validate_key(key, tree, validate_fn):
    symbol, children = tree
    if symbol == key: validate_fn(children)

    for child in children:
        validate_key(key, child, validate_fn)

def validate_tags(nodes, g):
    (first, _), (last, _) = (tree_to_string(nodes[0], g), tree_to_string(nodes[-1], g))
    assert first[1:-2] == last[2:-2]
```
Finally, we define our parser. 

```python
def parse_xml(to_parse):
    till, tree = pegparser.peg_parse(xmlgrammar.grammar).unify_key('{.}', to_parse)
    assert (len(to_parse) - till) == 0
    assert tree_to_string(tree, xml_grammar) == to_parse
    new_tree = translate(tree, xml_grammar, translations)
    validate_key('{ntag}', new_tree, lambda nodes: validate_tags(nodes, xml_grammar))
    print(new_tree)

if __name__ == '__main__':
  parse_xml(sys.argv[1])
```

We can use this parser as follows:

```python
$ python3 parse_xml.py '<t><c/>my text</t>'
<t> </t>
('{.}', [('{xml}', [('{ntag}', [('<t>', []), ('{xmlfragment}', [('{xml}', [('<c/>', [])]), ('{xmlfragment}', [('my text', []), ('{xmlfragment}', [('', [])])])]), ('</t>', [])])])])

$ python3   parse_xml.py '<t><c></t>' 
AssertionError
```

