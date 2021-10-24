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
# Regular expressions actually corresond to regular grammars (which
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
# So, why is producing a context-free grammar instead of regular grammar
# unsatisfying? Because such regular grammars have more interesting properties
# such as being closed under intersection and negation. By using a context-free
# grammar, we miss out on such properties.
# Hence, it would be really good if we could
# translate the regular expression directly into a regular grammar. This is what
# we will do in this post.
#
# We start with importing the prerequiesites

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

# We want to produce regular grammars directly from regular expressions. A
# regular expression, as we have seen in the previous posts, has two basic
# operations to combine two sub expressions. Given two regular expressions
# `A` and `B`, it can be combined using `|` to produce `A | B` which matches
# either `A` or `B`. That is, a union of matches of `A` and `B`.
# Secondly, given `A` and `B`, we can concat them to produce
# `A B` which matches `A` first, and then `B`.
# Finally, regular expressions also allow repetitions. That is, given a regular
# expression `A`, `A+` denotes one or more matches of `A`. Similarly `A*`
# denotes zero or more matches of `A`.
#
# If we can produce regular grammars for these operations, we can have produce
# regular grammar.  So, we first tackle union of two regular grammars
#
# ## Union of Regular Grammars
# 
# Given two regular grammars such that their nonterminals do not overlap,
# we need to produce a union grammar.
# The idea is that you only need to modify the start symbol such that
# the definition of the new start symbol is a combination of starts from both
# grammars.

def key_intersection(g1, g2):
    return [k for k in g1 if k in g2]

def regular_union(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_s = '<%s>' % (s1[1:-1] + s2[1:-1])
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s

# Using it

if __name__ == '__main__':
    g1 = {
            '<start1>' : [['<A1>']],
            '<A1>' : [['a', '<B1>']],
            '<B1>' : [['b','<C1>'], ['d']],
            '<C1>' : [['c']]
            }
    g2 = {
            '<start2>' : [['<A2>']],
            '<A2>' : [['a', '<B2>'], ['b']],
            '<B2>' : [['c'], ['d']]
            }
    g, s = regular_union(g1, '<start1>', g2, '<start2>')
    print(s)
    gatleast.display_grammar(g, s)

# ## Concatenation of Regular Grammars
# 
# Next, given two regular grammars g1 g2, such that
# their nonterminals do not overlap, producing a concatenation grammar is as
# follows: We collect all terminating rules from g1 which looks like
# $$ A -> a $$ where
# $$ a $$ is a terminal symbol. We then trasnform them to $$ A -> a S2 $$
# where $$ S2 $$ is the start symbol of g2. If epsilon was present in one of the
# rules of gA, then we simply produce $$ A -> S2 $$.

def regular_catenation(g1, s1, g2, s2):
    assert not key_intersection(g1, g2)
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                #new_rules.extend(g2[s2])
                new_rules.append([s2])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r + [s2])
            else:
                new_rules.append(r)
    return {**g2, **new_g}, s1

# Using it

if __name__ == '__main__':
    g3 = {
            '<start3>' : [['1', '<A3>']],
            '<A3>' : [['2', '<B3>']],
            '<B3>' : [['3'], ['5']]
            }
    g4 = {
            '<start4>' : [['a', '<A4>']],
            '<A4>' : [['b', '<B4>'], ['b']],
            '<B4>' : [['c'], ['d']]
            }
    g, s = regular_catenation(g3, '<start3>', g4, '<start4>')
    print(s)
    gatleast.display_grammar(g, s)

# ## Kleene Plus of Regular Grammars
#
# For every terminating rule in g, add $$ A -> a S $$ where S is the
# start symbol.

def regular_kleeneplus(g1, s1):
    new_g = {}
    for k in g1:
        new_rules = []
        new_g[k] = new_rules
        for r in g1[k]:
            if len(r) == 0: # epsilon
                new_rules.append([])
                #new_rules.extend(g1[s2])
                new_rules.append([s1])
            elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
                new_rules.append(r)
                new_rules.append(r + [s1])
            else:
                new_rules.append(r)
    return new_g, s1

# Using it

if __name__ == '__main__':
    g, s = regular_kleeneplus(g1, '<start1>')
    print(s)
    gatleast.display_grammar(g, s)

# ## Kleene Star of Regular Grammars
# For Kleene Star, add epsilon to the language.

def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    g[s].append([])
    return g, s

# Using it

if __name__ == '__main__':
    g, s = regular_kleeneplus(g1, '<start1>')
    print(s)
    gatleast.display_grammar(g, s)

# At this point, we have all operations  necessary to convert a regular
# expression to a regular grammar directly. We first define the class

class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass

# ```
#  <cex>   ::= <exp>
#            | <exp> <cex> 
# ```
# The translation is:
# ```
# <X> := a
# <Y> := b
# <Z> := <X> . <Y>
# ```
class RegexToRGrammar(RegexToRGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_exp(child)
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            g, s = regular_catenation(g1, s1, g2, key2)
            return g, s
        else:
            return g1, s1

# ```
#   <regex> ::= <cex>
#             | <cex> `|` <regex>
# ```
#
# ```
# <X> := a
# <Y> := b
# <Z> := <X>
#      | <Y>
# ```

class RegexToRGrammar(RegexToRGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g1, s1 = self.convert_cex(child)
        if not children: return g1, s1
        if len(children) == 2:
            g2, s2 = self.convert_regex(children[1])
            g, s = regular_union(g1, s1, g2, s2)
            return g, s
        else:
            assert len(children) == 1
            g1[s1].append([])
            return g1, s1

# ```
#    <regexplus> ::= <unitexp> `+`
# ```
#
# ```
# <X> ::= a <X>
#       | a
# ```
class RegexToRGrammar(RegexToRGrammar):
    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleeneplus(g, s)

    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        g, s = self.convert_unitexp(children[0])
        return regular_kleenestar(g, s)


# Using it

if __name__ == '__main__':
    my_input = '(abc)'
    print(my_input)
    g, s = RegexToRGrammar().to_grammar(my_input)
    gatleast.display_grammar(g, s)

# The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py)
