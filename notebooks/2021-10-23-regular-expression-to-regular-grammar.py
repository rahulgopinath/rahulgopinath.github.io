# ---
# published: true
# title: Regular Expression to Regular Grammar
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the [previous post](/post/2021/10/22/fuzzing-with-regular-expressions/), we
# discussed how to produce a grammar out of regular expressions. This is
# useful to make the regular expression a generator of matching inputs. However,
# one detail is unsatisfying. The grammar produced is a context-free grammar.
# Regular expressions actually correspond to regular grammars (which
# are strictly less powerful than context-free grammars).
#
# For reference, a context-free grammar is a grammar where the rules are of
# the form $$ A \rightarrow \alpha $$ where $$A$$ is a single nonterminal symbol
# and $$ \alpha $$ is any sequence of terminal or nonterminal symbols
# including $$\epsilon$$ (empty).
#
# A regular grammar on the other hand, is a grammar where the rules can take one
# of the following forms:
# * $$ A \rightarrow a $$
# * $$ A \rightarrow a B $$
# * $$ A \rightarrow \epsilon $$
# 
# where $$ A $$  and $$ B $$ are nonterminal symbols, $$ a $$ is a terminal
# symbol, and $$ \epsilon $$ is the empty string.
#
# So, why is producing a context-free grammar instead of regular grammar
# unsatisfying? Because such regular grammars have more interesting properties
# such as being closed under intersection and complement. By using a
# context-free grammar, we miss out on such properties.
# Hence, it would be really good if we could
# translate the regular expression directly into a regular grammar. This is what
# we will do in this post.
#
# We start with importing the prerequisites

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

# We want to produce regular grammars directly from regular expressions.
# 
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

def key_union(k, s): return '<%s+%s>' % (k[1:-1], s[1:-1])

def regular_union(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_s = key_union(s1, s2)
    assert new_s not in g1
    assert new_s not in g2
    return {**g1, **g2, **{new_s: (list(g1[s1]) + list(g2[s2]))}}, new_s

# Using it

if __name__ == '__main__':
    my_re1 = 'a1(b1(c1)|b1)'
    g1 = {
            '<start1>' : [['<A1>']],
            '<A1>' : [['a1', '<B1>']],
            '<B1>' : [['b1','<C1>'], ['b1']],
            '<C1>' : [['c1']]
            }
    my_re2 = 'a2(b2)|a2'
    g2 = {
            '<start2>' : [['<A2>']],
            '<A2>' : [['a2', '<B2>'], ['a2']],
            '<B2>' : [['b2']]
            }
    g, s = regular_union(g1, '<start1>', g2, '<start2>')
    print(s)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re1, v) or re.match(my_re2, v), v

# ## Concatenation of Regular Grammars
# 
# Next, given two regular grammars $$G1$$ and $$G2$$ such that
# their nonterminals do not overlap, producing a concatenation grammar is as
# follows: We collect all terminating rules from $$G1$$ which looks like
# $$ A \rightarrow a $$ where
# $$ a $$ is a terminal symbol. We then transform them to $$ A \rightarrow a S2 $$
# where $$ S2 $$ is the start symbol of $$G2$$. If $$ \epsilon $$ was present in
# one of the rules of $$G1$$, then we simply produce $$ A \rightarrow S2 $$.
#  
# We can take a shortcut if we are willing to reuse the start key. For example,
# the below computes the regular catenation of grammars, by reusing the start key.
# ```
# def regular_catenation(g1, s1, g2, s2, verify=True):
#     if verify: assert not key_intersection(g1, g2)
#     new_g = {}
#     for k in g1:
#         new_rules = []
#         new_g[k] = new_rules
#         for r in g1[k]:
#             if len(r) == 0: # epsilon
#                 new_rules.append([s2])
#             elif len(r) == 1 and not fuzzer.is_nonterminal(r[0]):
#                 new_rules.append(r + [s2])
#             else:
#                 new_rules.append(r)
#     return {**g2, **new_g}, s1
# ```
# But a better way is to not to reuse the key, but to build a new key in a
# principled fashion. We start with catenation of nonterminals.

def nonterminal_catenation(k, s): return '<%s.%s>' % (k[1:-1], s[1:-1])

# Next, we define what happens when we catenate a nontrminal to a rule.
# It returns any new keys created, along with the new rule

def rule_catenation(rule, s2):
    if len(rule) == 0: # epsilon
        return [], [s2]
    elif len(rule) == 1:
        if not fuzzer.is_nonterminal(rule[0]):
            return [], rule + [s2]
        else: # degenerate
            return [rule[0]], [nonterminal_catenation(rule[0], s2)]
    else:
        return [rule[1]], [rule[0], nonterminal_catenation(rule[1], s2)]

# Finally, we define our regular catenation of two grammars.

def regular_catenation(g1, s1, g2, s2, verify=True):
    if verify: assert not key_intersection(g1, g2)
    new_g = {}
    keys = [s1]
    seen_keys = set()

    while keys:
        k, *keys = keys
        if k in seen_keys: continue
        seen_keys.add(k)

        new_rules = []
        for r in g1[k]:
            uks, new_rule = rule_catenation(r, s2)
            new_rules.append(new_rule)
            keys.extend(uks)

        k_ = nonterminal_catenation(k, s2)
        new_g[k_] = new_rules
    ks = nonterminal_catenation(s1, s2)
    return {**g2, **new_g}, ks

# Using it

if __name__ == '__main__':
    my_re3 = '1(2(3|5))'
    g3 = {
            '<start3>' : [['1', '<A3>']],
            '<A3>' : [['2', '<B3>']],
            '<B3>' : [['3'], ['5']]
            }
    my_re4 = 'a(b(c|d)|b)'
    g4 = {
            '<start4>' : [['a', '<A4>']],
            '<A4>' : [['b', '<B4>'], ['b']],
            '<B4>' : [['c'], ['d']]
            }
    g, s = regular_catenation(g3, '<start3>', g4, '<start4>')
    print(s)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re3 + my_re4, v), v

# ## Kleene Plus of Regular Grammars
#
# Given a nonterminal symbol and the grammar in which it is defined, the
# Kleene plus is simply a regular concatenation of the nontrerminal with
# itself (recursive), with a regular union of its nonterminal's rules. The small
# difference here from regular concatenation is that, when we concatenate the
# nonterminal with itself, we do not need to check for disjointness of
# nonterminals, because the definitions of other nonterminals are exactly the
# same. Further, $$G2$$ is never used in the algorithm except in the final
# grammar.

def regular_kleeneplus(g1, s1):
    s1plus = '<%s.>' % s1[1:-1]
    gn, sn = regular_catenation(g1, s1, g1, s1plus, verify=False)
    gn[s1plus] = gn[sn]
    gn[s1plus].extend(g1[s1])
    return gn, s1plus

# Using it

if __name__ == '__main__':
    my_re1plus = '(%s)+' % my_re1
    g, s = regular_kleeneplus(g1, '<start1>')
    print(s)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re1plus, v), v

# ## Kleene Star of Regular Grammars
# For Kleene Star, add $$ \epsilon $$ to the language of Kleene Plus.

def regular_kleenestar(g1, s1):
    g, s = regular_kleeneplus(g1, s1)
    if [] not in g[s]: g[s].append([])
    return g, s

# Using it

if __name__ == '__main__':
    my_re1star = '(%s)+' % my_re1
    g, s = regular_kleenestar(g1, '<start1>')
    print(s)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert (re.match(my_re1star, v) or v == ''), v 

# At this point, we have all operations  necessary to convert a regular
# expression to a regular grammar directly. We first define the class

class RegexToRGrammar(rxfuzzer.RegexToGrammar):
    pass

# ```
#  <cex>   ::= <exp>
#            | <exp> <cex> 
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
    my_re = 'x(a|b|c)+'
    print(my_re)
    g, s = RegexToRGrammar().to_grammar(my_re)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        print(repr(v))
        assert re.match(my_re, v), v 

# At this point, the grammar may still contain degenerate rules
# of the form $$ A \rightarrow B $$. We need to clean that up so
# that rules follow one of $$ A \rightarrow a B $$ or $$ A \rightarrow a $$ 
# or $$ A \rightarrow \epsilon $$.

class RegexToRGrammar(RegexToRGrammar):
    def is_degenerate_rule(self, rule):
        return len(rule) == 1 and fuzzer.is_nonterminal(rule[0])

    def cleanup_regular_grammar(self, g, s):
        # assumes no cycle
        cont = True
        while cont:
            cont = False
            new_g = {}
            for k in g:
                new_rules = []
                new_g[k] = new_rules
                for r in g[k]:
                    if self.is_degenerate_rule(r):
                        new_r = g[r[0]]
                        if self.is_degenerate_rule(new_r): cont = True
                        new_rules.extend(new_r)
                    else:
                        new_rules.append(r)
            return new_g, s

    def to_grammar(self, my_re):
        parsed = self.parse(my_re)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        grammar, start = self.convert_regex(children[0])
        return self.cleanup_regular_grammar(grammar, start)

# Using it

if __name__ == '__main__':
    my_re = '(a|b|c)+(de|f)*'
    print(my_re)
    g, s = RegexToRGrammar().to_grammar(my_re)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        print(repr(v))
        assert re.match(my_re, v), v 

# The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-23-regular-expression-to-regular-grammar.py)
