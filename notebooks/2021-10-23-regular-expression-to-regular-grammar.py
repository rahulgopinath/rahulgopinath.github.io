# ---
# published: true
# title: Fuzzing With Regular Expressions
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/), we
# discussed how to produce a grammar out of regular expressions. This is
# useful to make the regular expression a generator of matching inputs. However,
# one detail is unsatisfying. The grammar produced is a context-free grammar.
# However, regular expressions corresond to regular grammars (which
# are strictly less powerful than context-free grammars).
#
# For reference, a context-free grammar is a grammar where the rules are of
# the format $$ A -> \alpha $$ where $$A$$ is a single nonterminal symbol and
# $$ \alpha $$ is any sequence of terminal or nonterminal symbols
# (including empty).
#
# A regular grammar on the other hand, is a grammar where the rules can take one
# of the following forms: $$ A -> a $$ or $$ A -> a B $$ or $$ A -> \epsilon $$
# where $$ A $$  and $$ B $$ are nonterminal symbols, and $$ a $$ is a terminal
# symbol and $$ \epsilon $$ is the empty string.
#
# Such regular grammars have more interesting properties such as being closed
# under intersection and negation. Hence, it would be really good if we could
# translate the regular expression directly into a regular grammar.

import sys, imp, pprint, string

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
        with open(module_loc, encoding='utf8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# We import the following modules

earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')

# We want to produce regular grammars directly from regular expressions. To do
# that, we need two techniques.
#
# ## Union of Regular Grammars
# 
# The first, given two regular grammars, such that
# their nonterminals do not overlap, we need to produce a union grammar.
# The idea is that you only need to modify the start symbol such that
# the definition of the new start symbol is a combination of starts from both
# grammars.

def assert_disjoint(g1, g2):
    for k in g1: assert k not in g2

def regular_union(g1, s1, g2, s2):
    assert_disjoint(g1, g2)
    new_s = s1[1:-1] + s2[1:-1]
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}

# ## Concatenation of Regular Grammars
# Next, given two regular grammars g1 g2, such that
# their nonterminals do not overlap, producing a concatenation grammar is as
# follows: We collect all terminating rules from g1 which looks like
# $$ A -> a $$ where
# $$ a $$ is a terminal symbol. We then trasnform them to $$ A -> a S2 $$
# where $$ S2 $$ is the start symbol of g2. If epsilon was present in one of the
# rules of gA, then we simply produce $$ A -> S2 $$.

def regular_catenation(g1, s1, g2, s2):
    assert_disjoint(g1, g2)
    # find all terminal rules in g1
    terminal_rules = []
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                terminal_rules.append(r)
                new_rules.extend(g2[s2])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                terminal_rules.append(r)
                new_rules.append(r + [s2])
            else:
                new_rules.append(r)
    return new_g, s1

# 

class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    def convert_unitexp(self, node, grammar):
        _key, children = node
        key = children[0][0]
        if key == '<alpha>':
            return self.convert_alpha(children[0], grammar)
        elif key == '<bracket>':
            return self.convert_bracket(children[0], grammar)
        elif key == '<dot>':
            return self.convert_dot(children[0], grammar)
        elif key == '<parenexp>':
            return self.convert_regexparen(children[0], grammar)
        else:
            assert False
        return key
# Using it

if __name__ == '__main__':
    my_input = '(abc)'
    print(my_input)
    s, g = RegexToRGrammar().to_grammar(my_input)
    gatleast.display_grammar(g, s)

# The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-22-fuzzing-with-regular-expressions.py)
