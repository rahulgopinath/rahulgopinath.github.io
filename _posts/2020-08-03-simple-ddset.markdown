---
published: true
title: Simple DDSet
layout: post
comments: true
tags: deltadebug, ddset, testcase reducer, cfg, generator
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.8/';</script>
<script src="/resources/pyodide/full/3.8/pyodide.js"></script>
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
We previously [discussed](/post/2020/07/15/ddset/) how
DDSET [^gopinath2020abstracting] is implemented. However, DDSET is a fairly
complex algorithm, and tries to handle diverse cases that may arise in the
real world such as difference between syntactic and semantic validity,
impact of tokens, variables etc.  This complexity is however, not innate. One
can produce a much more simple version of DDSET if one is only interested in
abstracting inputs, and one has a predicate that does not have a semantic
validation phase. The algorithm is as follows:
(We use a number of library functions from that post). Unlike previous posts,
this post uses a top down approach since we have already
defined a number of functions [previously](/post/2020/07/15/ddset/).
First we load the prerequisite earley parser.

<!--
############
import sys, imp

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
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys, imp

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
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The imported modules

<!--
############
earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
hdd = import_file('hdd', '2019-12-04-hdd.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
earleyparser = import_file(&#x27;earleyparser&#x27;, &#x27;2021-02-06-earley-parsing.py&#x27;)
hdd = import_file(&#x27;hdd&#x27;, &#x27;2019-12-04-hdd.py&#x27;)
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We first define our input, and make sure that our predicate works

<!--
############
my_input = '1+((2*3/4))'
assert hdd.expr_double_paren(my_input) == hdd.PRes.success

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
my_input = &#x27;1+((2*3/4))&#x27;
assert hdd.expr_double_paren(my_input) == hdd.PRes.success
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, let us make sure that it parses correctly.

<!--
############
expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
parsed_expr = list(expr_parser.parse_on(my_input, '<start>'))[0]
print(parsed_expr)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
expr_parser = earleyparser.EarleyParser(hdd.EXPR_GRAMMAR)
parsed_expr = list(expr_parser.parse_on(my_input, &#x27;&lt;start&gt;&#x27;))[0]
print(parsed_expr)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Next, we use the *perses* reducer to produce a reduced derivation tree.

<!--
############
reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
reduced_expr_tree = hdd.perses_reduction(parsed_expr, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now we are ready to call our generalizer, which takes the expression tree, the grammar, and the predicate, and returns the generalized pattern.
```python
pattern = ddset_simple(reduced_expr, EXPR_GRAMMAR, expr_double_paren)
print(pattern)
```
The `ddset_simple()` is implemented as follows:

<!--
############
def ddset_simple(reduced_tree, grammar, predicate):
  vals = generalize(reduced_tree, [], [], grammar, predicate)
  ta = get_abstract_tree(reduced_expr_tree, vals)
  return tree_to_str_a(ta)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def ddset_simple(reduced_tree, grammar, predicate):
  vals = generalize(reduced_tree, [], [], grammar, predicate)
  ta = get_abstract_tree(reduced_expr_tree, vals)
  return tree_to_str_a(ta)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `generalize()` procedure tries to generalize a given tree recursively. For that, it starts at the root node, and replaces the node with
a randomly generated tree rooted at the same node. It tries that a configurable number of times, and if the tree can be replaced each time
without failure, then we mark the path as abstract. If not, we descent into its children and try the same. While generating a new tree, any
previous nodes marked as abstract is also replaced by randomly generated values.

<!--
############
def generalize(tree, path, known_paths, grammar, predicate):
    node = hdd.get_child(tree, path)
    if not fuzzer.is_nonterminal(node[0]): return known_paths
    if can_abstract(tree, path, known_paths, grammar, predicate):
        known_paths.append(path)
        return known_paths
    for i,child in enumerate(node[1]):
        ps = generalize(tree, path + [i], known_paths, grammar, predicate)
    return known_paths

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def generalize(tree, path, known_paths, grammar, predicate):
    node = hdd.get_child(tree, path)
    if not fuzzer.is_nonterminal(node[0]): return known_paths
    if can_abstract(tree, path, known_paths, grammar, predicate):
        known_paths.append(path)
        return known_paths
    for i,child in enumerate(node[1]):
        ps = generalize(tree, path + [i], known_paths, grammar, predicate)
    return known_paths
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `can_abstract()` procedure above does the checking to see if the tree can be abstracted. It is implemented as follows.

<!--
############
MAX_TRIES_FOR_ABSTRACTION = 100

def can_abstract(tree, path, known_paths, grammar, predicate):
    i = 0
    while (i < MAX_TRIES_FOR_ABSTRACTION):
        t = replace_all_paths_with_generated_values(tree, known_paths + [path], grammar)
        s = fuzzer.iter_tree_to_str(t)
        if predicate(s) == hdd.PRes.failed:
            return False
        elif predicate(s) == hdd.PRes.invalid:
            continue
        i += 1
    return True

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
MAX_TRIES_FOR_ABSTRACTION = 100

def can_abstract(tree, path, known_paths, grammar, predicate):
    i = 0
    while (i &lt; MAX_TRIES_FOR_ABSTRACTION):
        t = replace_all_paths_with_generated_values(tree, known_paths + [path], grammar)
        s = fuzzer.iter_tree_to_str(t)
        if predicate(s) == hdd.PRes.failed:
            return False
        elif predicate(s) == hdd.PRes.invalid:
            continue
        i += 1
    return True
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `can_abstract()` procedure tries to generate a valid value `MAX_TRIES_FOR_ABSTRACTION` times. For this, it relies on
`replace_all_paths_with_generated_values()` which is implemented as follows.

<!--
############
def replace_all_paths_with_generated_values(tree, paths, grammar):
    my_tree = tree
    for p in paths:
        my_tree = replace_path_with_generated_value(my_tree, p, grammar)
    return my_tree

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def replace_all_paths_with_generated_values(tree, paths, grammar):
    my_tree = tree
    for p in paths:
        my_tree = replace_path_with_generated_value(my_tree, p, grammar)
    return my_tree
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here, the major work is done by `replace_path_with_generated_value()` which replaces a single given path with a generated node
of the same kind.

<!--
############
import copy
def replace_path(tree, path, new_node=None):
    if new_node is None: new_node = []
    if not path: return copy.deepcopy(new_node)
    cur, *path = path
    name, children, *rest = tree
    new_children = []
    for i,c in enumerate(children):
        if i == cur:
            nc = replace_path(c, path, new_node)
        else:
            nc = c
        if nc:
            new_children.append(nc)
    return (name, new_children, *rest)

def replace_path_with_generated_value(tree, path, grammar):
    node = hdd.get_child(tree, path)
    s, gnode = generate_random_value(grammar, node[0])
    t = replace_path(tree, path, gnode)
    return t

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import copy
def replace_path(tree, path, new_node=None):
    if new_node is None: new_node = []
    if not path: return copy.deepcopy(new_node)
    cur, *path = path
    name, children, *rest = tree
    new_children = []
    for i,c in enumerate(children):
        if i == cur:
            nc = replace_path(c, path, new_node)
        else:
            nc = c
        if nc:
            new_children.append(nc)
    return (name, new_children, *rest)

def replace_path_with_generated_value(tree, path, grammar):
    node = hdd.get_child(tree, path)
    s, gnode = generate_random_value(grammar, node[0])
    t = replace_path(tree, path, gnode)
    return t
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Given a key, generate a random value for that key using the grammar. 

<!--
############
def generate_random_value(grammar, key):
    my_fuzzer = fuzzer.LimitFuzzer(grammar)
    s = my_fuzzer.iter_fuzz(key)
    return (s, my_fuzzer._s)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def generate_random_value(grammar, key):
    my_fuzzer = fuzzer.LimitFuzzer(grammar)
    s = my_fuzzer.iter_fuzz(key)
    return (s, my_fuzzer._s)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Finally, the converter from an abstract tree to a string expression

<!--
############
def tree_to_str_a(tree):
    name, children, *general_ = tree
    if not fuzzer.is_nonterminal(name): return name
    if is_node_abstract(tree):
        return name
    return ''.join([tree_to_str_a(c) for c in children])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def tree_to_str_a(tree):
    name, children, *general_ = tree
    if not fuzzer.is_nonterminal(name): return name
    if is_node_abstract(tree):
        return name
    return &#x27;&#x27;.join([tree_to_str_a(c) for c in children])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also need a few library functions for marking some nodes concrete and some abstract.

<!--
############
def mark_concrete_r(tree):
    name, children, *abstract_a = tree
    abstract = {'abstract': False} if not abstract_a else abstract_a[0]
    return (name, [mark_concrete_r(c) for c in children], abstract)

def mark_path_abstract(tree, path):
    name, children = hdd.get_child(tree, path)
    new_tree = replace_path(tree, path, (name, children, {'abstract': True}))
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def mark_concrete_r(tree):
    name, children, *abstract_a = tree
    abstract = {&#x27;abstract&#x27;: False} if not abstract_a else abstract_a[0]
    return (name, [mark_concrete_r(c) for c in children], abstract)

def mark_path_abstract(tree, path):
    name, children = hdd.get_child(tree, path)
    new_tree = replace_path(tree, path, (name, children, {&#x27;abstract&#x27;: True}))
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
        return abstract_a[0][&#x27;abstract&#x27;]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
With this, we are ready to extract our pattern.

<!--
############
pattern = ddset_simple(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
print(pattern)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
pattern = ddset_simple(reduced_expr_tree, hdd.EXPR_GRAMMAR, hdd.expr_double_paren)
print(pattern)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This prints:
```bash
$ python ddset_simple.py
((<expr>))
```

So, given that this algorithm is much simpler than the original, why should we use the
original algorithm? The problem is that when the input is a file in a programming language,
one also needs to take into account the semantics. That is, the generated input needs to be
valid both syntactically (by construction) as well as semantically. It is hard enough trying
to fill one hole in the parse tree (abstract node) with a semantically valid subtree. Now,
imagine that you have identified one abstraction and are evaluating a second node. You need to
generate random nodes both for previously identified abstract node, as well as the node you are
currently evaluating. Say you have identified three abstract nodes, for any node that will be
evaluated next, you need to fill in three abstract nodes with randomly generated semantically
valid values. This is exponential, and infeasible to continue as more nodes are added. Hence,
in original DDSet, we try to independantly evaluate each single node, and once we have collected
most of these nodes, we go for a second pass to verify.

How much difference does it make? For [Rhino bug 385](https://github.com/mozilla/rhino/issues/385)
abstracting the minimal string `var {baz: baz => {}} = baz => {};` took 15643 executions for
`ddsetsimple` when compared to 10340 executions for the ddset from the paper (discounting covarying
fragments).

The full code is available [here](https://github.com/vrthra/ddset/blob/master/simple/SimpleDDSet.py)

[^gopinath2020abstracting]: Rahul Gopinath, Alexander Kampmann, Nikolas Havrikov, Ezekiel Soremekun, Andreas Zeller, "Abstracting Failure Inducing Inputs" ISSTA 2020 URL:<https://rahul.gopinath.org/publications/#gopinath2020abstracting>

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
