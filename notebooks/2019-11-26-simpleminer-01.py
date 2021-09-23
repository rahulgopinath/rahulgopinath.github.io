# ---
# published: true
# title: A simple grammar miner
# layout: post
# comments: true
# tags: fuzzing
# categories: post
# ---

# Note: This post is based on the string inclusion grammar miner in
# [the fuzzingbook](https://www.fuzzingbook.org/html/GrammarMiner.html),
# but reduced to bare essentials.
# 
# The concept of _grammar mining_ from programs is as follows: Given a program that
# uses recursive descent parsing on its input, the call graph along with the
# arguments passed corresponds to the parse tree of the input string.
# 
# Once we have the parse tree from a sufficient number of input strings (or an
# input string with sufficiently diverse features), one can extract the grammar
# directly.
# 
# In this post, I will explain how to recover the input grammar from `urlparse`
# from the Python standard library.
# 
# First, we have to import our function, and dependencies:

from urllib.parse import urlparse
import sys

# Next, we define our input values.

INPUTS = [
    'http://user:pass@www.freebsd.com:80/release/7.8',
    'https://www.microsoft.com/windows/2000',
    'http://www.fuzzing.info:8080/app?search=newterm#ref2',
]

# The basic procedure of our grammar mining algorithm is to hook into a debugger,
# and inspect the environment variables as the execution traverses the call graph.
# Then, identify the variables that represent fragments of the input that was
# passed in.
# 
# Hence, we need to hook into the Python debugger. This is accomplished using the
# [trace](https://docs.python.org/3/library/sys.html#sys.settrace) functionality.

# ### Tracing

# First, we define `traceit()` the function that actually gets called on each
# trace event. For now, we are only interested in arguments to a function, and
# hence, ignore all events other than function `call`. This allows us to ignore
# reassignments.

def traceit(frame, event, arg):
    if (event != 'call'): return traceit
    strings = {k:v for k,v in frame.f_locals.items() if isinstance(v, str) and len(v) >= 2}
    for var, value in strings.items():
        if value not in the_input: continue
        if var in the_values: continue
        the_values[var] = value
    return traceit


# Next, we define the `trace_function()` which hooks into the trace functionality,
# and registers a given function to be called on each trace event.


the_input = None
the_values = None
def trace_function(function, inputstr):
    global the_input, the_values
    the_input = inputstr
    the_values = {}

    old_trace = sys.gettrace()
    sys.settrace(traceit)
    function(the_input)
    sys.settrace(old_trace)
    return the_values

# We can now inspect the fragments produced

if __name__ == '__main__':
    tvars = [trace_function(urlparse, i) for i in INPUTS]
    print(repr(tvars[0]))

# ### Parse Tree

# We will next use these fragments to construct a derivation tree of the given
# input string. The idea is to start with the input string that corresponds to the
# `<START>` symbol. Then take one fragment at a time, and replace the matching
# substring by a reference to the fragment, and add the fragment variable name as
# a non terminal symbol in the grammar.
# 
# The `to_tree()` iterates through the fragments, and refines the defined tree.

def to_tree(tree, fragments):
    for fvar, fval in fragments.items():
        tree = refine_tree(tree, fvar, fval)
    return tree

# Next, we define the `refine_tree()` which takes one single fragment (a key value
# pair), and recursively searches and update the tree.


def refine_tree(tree, fvar, fval):
    node_name, children = tree
    new_children = []
    for child in children:
        if isinstance(child, str):
            pos = child.find(fval)
            if pos == -1:
                new_children.append(child)
            else:
                frags = child[0:pos], ("<%s>" % fvar, [fval]), child[pos + len(fval):]
                for f in frags:
                    if not f: continue
                    new_children.append(f)
        else:
            nchild = refine_tree(child, fvar, fval)
            new_children.append(nchild)

    return (node_name, new_children)

# We use the `to_tree()` in the following fashion.

if __name__ == '__main__':
    trees = [to_tree(('<START>', [inpt]), tvars[i]) for i,inpt in enumerate(INPUTS)]
    print(repr(trees[0]))

# ### Grammar Extraction

# Once we have this tree, extracting the grammar is as simple as recursively
# traversing the tree, and collecting the alternative expansions of the rules.
# This is accomplished by the `to_grammar()` function.


def refine_grammar(g, tree):
    node, children = tree

    rule = [c[0] if isinstance(c, tuple) else c for c in children]

    if node not in g: g[node] = set()
    g[node].add(tuple(rule))

    for c in children:
        if not isinstance(c, tuple): continue
        refine_grammar(g, c)

# It is used as follows:

if __name__ == '__main__':
    url_grammar = {}
    for tree in trees:
       refine_grammar(url_grammar, tree)
    print(repr(url_grammar))

# This represents the input grammar of the function `urlparse()`.
#
# All together:

def to_grammar(inputs, fn):
    tvars = [trace_function(fn, i) for i in inputs]
    trees = [to_tree(('<START>', [inpt]), tvars[i])
             for i,inpt in enumerate(inputs)]
    my_grammar = {}
    for tree in trees:
        refine_grammar(my_grammar, tree)
    return {k:[r for r in my_grammar[k]] for k in my_grammar}

# The function can be used as follows:

if __name__ == '__main__':
    grammar = to_grammar(INPUTS, urlparse)
    print(grammar)

# ### Fuzzing
#
# Let us see if our [simple fuzzer](/2019/05/28/simplefuzzer-01/) is able
# to work with this grammar.

if __name__ == '__main__':
    if 'pyodide' in sys.modules:
        import micropip
        await micropip.install('/py/moduleloader-0.1.0-py3-none-any.whl')
    import moduleloader
    moduleloader.Importer(['notebooks/2019-05-28-simplefuzzer-01.py'])
    import simplefuzzer01

# Using it to fuzz:

if __name__ == '__main__':
    res = simplefuzzer01.tree_to_string(simplefuzzer01.unify_key_inv_t(grammar, '<START>'))
    print(res)

