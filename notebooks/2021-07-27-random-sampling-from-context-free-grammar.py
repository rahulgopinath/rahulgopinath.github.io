# ---
# published: true
# title: Random Sampling of Strings from Context-Free Grammar
# layout: post
# comments: true
# tags: pipes, python
# categories: post
# ---
# 
# Status: DRAFT
# 
# In one of the [previous posts](/post/2019/05/28/simplefuzzer-01/) I talked about
# how to generate input strings from any given context-free grammar. While that
# algorithm is quite useful for fuzzing, one of the problems with that algorithm
# is that the strings produced from that grammar is skewed toward shallow strings.
# 
# For example, consider this grammar:

G = {
    "<start>" : [["<digits>"]],
    "<digits>" : [["<digit>", "<digits>"],
        ["<digit>"]],
    "<digit>" : [[str(i)] for i in range(10)]
}

# To generate inputs, let us load the limit fuzzer from the previous post.

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

# ## The Fuzzer

fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')

# The generated strings (which generate random integers) are as follows

gf = fuzzer.LimitFuzzer(G)
for i in range(10):
    print(gf.fuzz('<start>'))

# As you can see, there are more single digits in the output than
# longer integers. Almost half of the generated strings are single character.
# If we modify our grammar as below

G = {
    "<start>" : [["<digits>"]],
    "<digits>" : [["<digit>", "<digits>"],
                  ["<digit>"],
                  ["<threedigits>"],
                  ],
    "<digit>" : [[str(i)] for i in range(10)],
    "<threedigits>" : [[str(i) + str(j) + str(k)] for i in range(2) for j in range(2) for k in range(2)]
}

# and run it again

gf = fuzzer.LimitFuzzer(G)
for i in range(10):
    print(gf.fuzz('<start>'))

# you will notice a lot more three digit wide binary numbers are produced. In
# fact, now, more than one third of the generated strings are likely to be three
# digits. This is because of the way the grammar is written. That is, there are
# three possible expansions of the `<digits>` nonterminal, and our fuzzer
# chooses one of the expansions with equal probability. This leads to the skew
# in the inputs we see above.
#
# This is interesting, but why is it a problem for practitioners? Consider these
# two grammars.
E1 = {
 '<start>': [['<E>']],
 '<E>': [['<F>', '*', '<E>'],
         ['<F>', '/', '<E>'],
         ['<F>']],
 '<F>': [['<T>', '+', '<F>'],
         ['<T>', '-', '<F>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<D>']],
 '<D>': [['0'], ['1']]
}
E2 = {
 '<start>': [['<E>']],
 '<E>': [['<T>', '+', '<E>'],
            ['<T>', '-', '<E>'],
            ['<T>']],
 '<T>': [['<F>', '*', '<T>'],
            ['<F>', '/', '<T>'],
            ['<F>']],
 '<F>': [['(', '<E>', ')'],
         ['<D>']],
 '<D>': [['0'], ['1']]
} 

# Now, let us look at the generated strings. The first:
print("E1")
e1f = fuzzer.LimitFuzzer(E1)
for i in range(10):
    print(e1f.fuzz('<start>', max_depth=1))

# And the second:

print("E2")
e2f = fuzzer.LimitFuzzer(E2)
for i in range(10):
    print(e2f.fuzz('<start>', max_depth=1))

# Notice that both grammars describe exactly the same language, but the
# first one has a higher proportion of multiplications and divisions while the
# second one has a higher proportion of additions and subtractions. This means
# that the effectiveness of our fuzzers is determined to a large extent by the
# way the context-free grammar is written. 
#
# Another case is when one wants to compare the agreement between two grammars.
# As you can see from the above cases, the same language can be described by
# different grammars, and it is undecidable.
