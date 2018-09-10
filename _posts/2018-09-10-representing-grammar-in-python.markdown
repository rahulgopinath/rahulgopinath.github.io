---
published: false
title: Representing a Grammar in Python
layout: post
comments: true
tags: parsing
---

In the [previous](2018/09/05/top-down-parsing/) [posts](/2018/09/06/peg-parsing/), I described how can write a parser. For doing that, I made use of a grammar written as a python data structure, with the assumption that it can be loaded as a JSON file if necessary. The grammar looks like this:

```python
term_grammar = {
    'expr': [
        ['term', '+', 'expr'],
        ['term', '-', 'expr'],

        ['term']],
    'term': [
        ['fact', '*', 'term'],
        ['fact', '/', 'term'],
        ['fact']],
    'fact': [
        ['digits'],
        ['(','expr',')']],
    'digits': [
        ['digit','digits'],
        ['digit']],
    'digit': [[str(i)] for i in range(10)],
}
```
However, this is somewhat unsatisfying. There are too many distracting syntactic elements in the code, making it difficult to see where each elements are. What we want is a better representation. Indeed, one better representation is to lose one level of nesting, and instead, parse the string for terminals and non-terminals. The following representation uses a single string for a single production, and a list for all alternative productions for a key.
```python
term_grammar = {
    'expr': ['{term} + {expr}', '{term} - {expr}', 'term'],
    'term': ['{fact} * {fact}', '{fact} / {fact}', '{fact}'],
    'fact': ['{digits}','({expr})'],
    'digits': ['{digit}{digits}','{digit}'],
    'digit': [str(i) for i in range(10)],
}
```
Since we are using the string interpolation in Python, one can recover the non-terminal symbols given any of the productions as follows using the `parse` method.
```python
def nonterminals(production):
    return set(i[1] for i in string.Formatter().parse(production) if i[1])
```
But is there a better way? Ideally, one would like to define the grammar like one defines the class, so that it feels part of the language.

One mechanism we can (ab)use is the type annotations. Specifically in `Python 3.7` one can use the postponed evaluation of annotations to accomplish a DSL as below, with grammar keys as attributes of the grammar class:
```python
from __future__ import annotations

class expr(grammar):
    start: '{expr}'
    expr: '{term} + {term}' | '{term} - {term}'
    term: '{factor} * {term}' | 'factor / {term}'
    factor: '( {expr} )' | '{integer}'
    integer: '{digit} {integer}' | '{digit}'
    digit: '0' | '1' | '2'
```
The annotations lets us access the types of each class as a string, that can be evaluated separately. The `grammar` class is defined as follows:
```python
import string
import ast

class grammar:
    def alternatives(self, k):
        def strings(v):
            return [v.right.s] + strings(v.left) if isinstance(v, ast.BinOp) else [v.s]
        return strings(ast.parse(self.production(k), mode='eval').body)

    def nonterminals(self, expansion):
        return set(i[1] for i in string.Formatter().parse(expansion) if i[1])

    def production(self, k):
        return self.__annotations__[k]

    def keys(self):
        return self.__annotations__.keys()
```
Given all this, to print the grammar in a readable form is simply:
```python
e = expr()
for i in e.keys():
    print(i, "::= ")
    for alt in  e.alternatives(i):
        print("\t| %s\t\t # %s" % (alt.strip(), e.nonterminals(alt)))
```
Which results in
```ebnf
start ::= 
	| {expr}		 # {'expr'}
expr ::= 
	| {term} - {term}		 # {'term'}
	| {term} + {term}		 # {'term'}
term ::= 
	| factor / {term}		 # {'term'}
	| {factor} * {term}		 # {'term', 'factor'}
factor ::= 
	| {integer}		 # {'integer'}
	| ( {expr} )		 # {'expr'}
integer ::= 
	| {digit}		 # {'digit'}
	| {digit} {integer}		 # {'digit', 'integer'}
digit ::= 
	| 2		 # set()
	| 1		 # set()
	| 0		 # set()
```
