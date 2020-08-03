---
published: true
title: Simple DDSet
layout: post
comments: true
tags: deltadebug, ddset, testcase reducer, cfg, generator
categories: post
---
We previously [discussed](/post/2020/07/15/ddset/) how DDSET is implemented. However, DDSET is a fairly complex algorithm, and
tries to handle diverse cases that may arise in the real world such as difference between syntactic and semantic validity, impact of tokens, variables etc.
This complexity is however, not innate. One can produce a much more simple version of DDSET if one is only interested in abstracting
inputs, and one has a predicate that does not have a semantic validation phase. The algorithm is as follows:

(We use a number of library functions from that post). Unlike previous posts, this post uses a top down approach since we have already
defined a number of functions [previously](/post/2020/07/15/ddset/).

We first define our predicate. It returns `PRes.success` when there is a nested parenthesis.
```python
import re
from enum import Enum

class PRes(str, Enum):
    success = 'SUCCESS'
    failed = 'FAILED'
    invalid = 'INVALID'
    timeout = 'TIMEOUT'

def expr_double_paren(inp):
    if re.match(r'.*[(][(].*[)][)].*', inp):
        return PRes.success
    return PRes.failed
```
We define and use the example input as follows.
```python
my_input = '1 + ((2 * 3 / 4))'
assert expr_double_paren(my_input) == PRes.success
```
We use the parser from [the fuzzingbook](https://fuzzingbook.org) and pass the result to the [perses reducer from here](/post/2019/12/03/ddmin/).

```python
expr_parser = Parser(EXPR_GRAMMAR, start_symbol='<start>', canonical=True)
parsed_expr_tree = list(expr_parser.parse(my_input))[0]
reduced_expr_tree = reduction(parsed_expr, EXPR_GRAMMAR, expr_double_paren)
```

Now we are ready to call our generalizer, which takes the expression tree, the grammar, and the predicate, and returns the generalized pattern.
```python
pattern = ddset_simple(reduced_expr, EXPR_GRAMMAR_expr_double_paren)
print(pattern)
```
The `ddset_simple()` is implemented as follows:
```python
def ddset_simple(reduced_tree, grammar, predicate):
  vals = generalize(reduced_tree, [], [], grammar, predicate)
  ta = get_abstract_tree(reduced_expr_tree, vals)
  return tree_to_str_a(ta)
```
The `generalize()` procedure tries to generalize a given tree recursively. For that, it starts at the root node, and replaces the node with
a randomly generated tree rooted at the same node. It tries that a configurable number of times, and if the tree can be replaced each time
without failure, then we mark the path as abstract. If not, we descent into its children and try the same. While generating a new tree, any
previous nodes marked as abstract is also replaced by randomly generated values.
```python
def generalize(tree, path, known_paths, grammar, predicate):
    node = get_child(tree, path)
    if not is_nt(node[0]): return known_paths
    if can_abstract(tree, path, known_paths, grammar, predicate):
        known_paths.append(path)
        return known_paths
    for i,child in enumerate(node[1]):
        ps = generalize(tree, path + [i], known_paths, grammar, predicate)
    return known_paths
```
The `can_abstract()` procedure above does the checking to see if the tree can be abstracted. It is implemented as follows.
```python
def can_abstract(tree, path, known_paths, grammar, predicate):
    i = 0
    while (i < MAX_TRIES_FOR_ABSTRACTION):
        t = replace_all_paths_with_generated_values(tree, known_paths + [path], grammar)
        s = tree_to_str(t)
        if predicate(s) == PRes.failed:
            return False
        elif predicate(s) == PRes.invalid:
            continue
        i += 1
    return True
```
The `can_abstract()` procedure tries to generate a valid value `MAX_TRIES_FOR_ABSTRACTION` times. For this, it relies on
`replace_all_paths_with_generated_values()` which is implemented as follows.
```python
def replace_all_paths_with_generated_values(tree, paths, grammar):
    my_tree = tree
    for p in paths:
        my_tree = replace_path_with_generated_value(my_tree, p, grammar)
    return my_tree
```
Here, the major work is done by `replace_path_with_generated_value()` which replaces a single given path with a generated node
of the same kind.
```python
def replace_path_with_generated_value(tree, path, grammar):
    node = get_child(tree, path)
    s, gnode = generate_random_value(grammar, node[0])
    t = replace_tree_node(tree, path, gnode)
    return t
```
Given a key, generate a random value for that key using the grammar. 
```python
def generate_random_value(grammar, key):
    fuzzer = LimitFuzzer(grammar)
    s = fuzzer.fuzz(key)
    return (s, fuzzer._s)
```
Finally, the converter from an abstract tree to a string expression
```python
def tree_to_str_a(tree):
    name, children, *general_ = tree
    if not is_nt(name): return name
    if is_node_abstract(tree):
        return name
    return ''.join([tree_to_str_a(c) for c in children])
```
We also need a few library functions for marking some nodes concrete and some abstract.
```python
def mark_concrete_r(tree):
    name, children, *abstract_a = tree
    abstract = {'abstract': False} if not abstract_a else abstract_a[0]
    return (name, [mark_concrete_r(c) for c in children], abstract)

def mark_path_abstract(tree, path):
    name, children = get_child(tree, path)
    new_tree = replace_tree_node(tree, path, (name, children, {'abstract': True}))
    return new_tree

def get_abstract_tree(tree, paths):
    for path in paths:
        tree = mark_path_abstract(tree, path)
    return mark_concrete_r(tree)

def is_node_abstract(node):
    name, children, *abstract_a = node
    if not abstract_a:
        return True
    else:
        return abstract_a[0]['abstract']
```
With this, we are ready to extract our pattern.
```python
pattern = ddset_simple(reduced_expr, EXPR_GRAMMAR_expr_double_paren)
print(pattern)
```
This prints:
```bash
$ python ddset_simple.py
((<expr>))
```
