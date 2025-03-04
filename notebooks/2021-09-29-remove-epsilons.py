# ---
# published: true
# title: Remove Empty (Epsilon) Rules From a Context-Free Grammar.
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the previous post about [uniform random sampling from grammars](https://rahul.gopinath.org/post/2021/07/27/random-sampling-from-context-free-grammar/),
# I mentioned that the algorithm expects an *epsilon-free* grammar. That is,
# the grammar should contain no empty rules. Unfortunately, empty rules are
# quite useful for describing languages. For example, to specify that we need
# zero or more white space characters, the following definition of `<spaceZ>`
# is the ideal representation.

grammar = {
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        []
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ]
}

# So, what can we do? In fact, it is possible to transform the grammar such that
# it no longer contain epsilon rules. The idea is that any rule that references
# a nonterminal that can be empty can be represented by skipping in a duplicate
# rule. When there are multiple such empty-able nonterminals, you need to
# produce every combination of skipping them.
#
# But first, let us tackle an easier task. We want to remove those nonterminals
# that exclusively represent an empty string. E.g.

emptyG = {
    "<start>": [
        ["<spaceZ>"]
            ],
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        ['<empty>']
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ],
    '<empty>': [[]]
}
emptyS = '<start>'

# We also load a few prerequisites

#^
# sympy

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/cfgrandomsample-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import cfgrandomsample as grandom
import itertools as I

import sympy

# ## Remove empty keys
# First, we implement removing empty keys that have empty expansions.
# In the above `<empty>` is such a key.
#
# Note that we still need an empty expansion inside the definition. i.e `[[]]`.
# Leaving `<empty>` without an expansion, i.e. `[]` means that `<empty>` can't
# be expanded, and hence we will have an invalid grammar.
# That is, `<empty>: []` is not a valid definition.


class GrammarShrinker:
    def __init__(self, grammar, start):
        self.grammar, self.start = grammar, start

    def remove_empty_rule_keys(self):
        while True:
            keys_to_delete = []
            for key in self.grammar:
                if key == self.start: continue
                if self.grammar[key] == [[]]:
                    keys_to_delete.append(key)
            if not keys_to_delete: break
            self.grammar = {k:[[t for t in r if t not in keys_to_delete]
                for r in self.grammar[k]]
                    for k in self.grammar if k not in keys_to_delete}
        return self.grammar

# We can use it thus:

if __name__ == '__main__':
    gatleast.display_grammar(emptyG, emptyS)
    gs = GrammarShrinker(emptyG, emptyS)
    newG, newS = gs.remove_empty_rule_keys(), emptyS
    gatleast.display_grammar(newG, newS)

# Now we are ready to tackle the more complex part: That of removing epsilon
# rules. First, we need to identify such rules that can become empty, and
# hence the corresponding keys that can become empty.
#
# ## Finding empty (epsilon) rules
# The idea is as follows, We keep a set of nullable nonterminals. For each
# rule, we check if all the tokens in the rule are nullable (i.e in the nullable
# set). If all are (i.e `all(t in my_epsilons for t in r)`), then, this rule
# is nullable. If there are `any` nullable rules for a key, then the key is
# nullable. We process these keys until there are no more new keys.

def find_epsilons(g):
    q = [k for k in g if [] in g[k]]
    my_epsilons = set(q)
    while q:
        ekey, *q = q
        nq = [k for k in g if any(all(t in my_epsilons for t in r) for r in g[k])
                if k not in my_epsilons]
        my_epsilons.update(nq)
        q += nq
    return my_epsilons

class GrammarShrinker(GrammarShrinker):
    def find_empty_keys(self):
        return find_epsilons(self.grammar)

# We can use it thus:

if __name__ == '__main__':
    gs = GrammarShrinker(newG, newS)
    e_keys = gs.find_empty_keys()
    print('Emptyable keys:')
    for key in e_keys:
        print('',key)

# Now that we can find epsilon rules, we need generate all combinations of
# the corresponding keys, so that we can generate corresponding rules.
# The idea is that for any given rule with nullable nonterminals in it,
# you need to generate all combinations of possible rules where some of
# such nonterminals are missing. That is, if given
# `[<A> <E1> <B> <E2> <C> <E3>]`, you need to generate these rules.
#
# ```
# [<A> <E1> <B> <E2> <C> <E3>]
# [<A> <B> <E2> <C> <E3>]
# [<A> <B> <C> <E3>]
# [<A> <B> <C>]
# [<A> <E1> <B> <C> <E3>]
# [<A> <E1> <B> <C>]
# [<A> <E1> <B> <E2> <C>]
# ```

class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            for a in I.combinations(positions, n):
                combinations.append(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            if new_rule:
                new_rules.append(new_rule)
        return new_rules

# We can use it thus:

if __name__ == '__main__':
    gs = GrammarShrinker(newG, newS)
    zrule = ['<A>', '<E1>', '<B>', '<E2>', '<C>', '<E3>']
    print('Rule to produce combinations:', zrule)
    ekeys = ['<E1>', '<E2>', '<E3>']
    comb = gs.rule_combinations(zrule, ekeys)
    for c in comb:
        print('', c)

# Let us try a larger grammar. This is the JSON grammar.

jsonG = {
    "<start>": [["<json>"]],
    "<json>": [["<element>"]],
    "<element>": [["<ws>", "<value>", "<ws>"]],
    "<value>": [["<object>"], ["<array>"], ["<string>"], ["<number>"],
                ["true"], ["false"],
                ["null"]],
    "<object>": [["{", "<ws>", "}"], ["{", "<members>", "}"]],
    "<members>": [["<member>", "<symbol-2>"]],
    "<member>": [["<ws>", "<string>", "<ws>", ":", "<element>"]],
    "<array>": [["[", "<ws>", "]"], ["[", "<elements>", "]"]],
    "<elements>": [["<element>", "<symbol-1-1>"]],
    "<string>": [["\"", "<characters>", "\""]],
    "<characters>": [["<character-1>"]],
    "<character>": [["0"], ["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"],
                    ["8"], ["9"], ["a"], ["b"], ["c"], ["d"], ["e"], ["f"],
                    ["g"], ["h"], ["i"], ["j"], ["k"], ["l"], ["m"], ["n"],
                    ["o"], ["p"], ["q"], ["r"], ["s"], ["t"], ["u"], ["v"],
                    ["w"], ["x"], ["y"], ["z"], ["A"], ["B"], ["C"], ["D"],
                    ["E"], ["F"], ["G"], ["H"], ["I"], ["J"], ["K"], ["L"],
                    ["M"], ["N"], ["O"], ["P"], ["Q"], ["R"], ["S"], ["T"],
                    ["U"], ["V"], ["W"], ["X"], ["Y"], ["Z"], ["!"], ["#"],
                    ["$"], ["%"], ["&"], ["\""], ["("], [")"], ["*"], ["+"],
                    [","], ["-"], ["."], ["/"], [":"], [";"], ["<"], ["="],
                    [">"], ["?"], ["@"], ["["], ["]"], ["^"], ["_"], ["`"],
                    ["{"], ["|"], ["}"], ["~"], [" "], ["<esc>"]],
    "<esc>": [["\\","<escc>"]],
    "<escc>": [["\\"],["b"],["f"], ["n"], ["r"],["t"],["\""]],
    "<number>": [["<int>", "<frac>", "<exp>"]],
    "<int>": [["<digit>"], ["<onenine>", "<digits>"], ["-", "<digits>"],
              ["-", "<onenine>", "<digits>"]],
    "<digits>": [["<digit-1>"]],
    "<digit>": [["0"], ["<onenine>"]],
    "<onenine>": [["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"], ["8"],
                  ["9"]],
    "<frac>": [[], [".", "<digits>"]],
    "<exp>": [[], ["E", "<sign>", "<digits>"], ["e", "<sign>", "<digits>"]],
    "<sign>": [[], ["+"], ["-"]],
    "<ws>": [["<sp1>", "<ws>"], []],
    "<sp1>": [[" "],["\n"],["\t"],["\r"]],
    "<symbol>": [[",", "<members>"]],
    "<symbol-1>": [[",", "<elements>"]],
    "<symbol-2>": [[], ["<symbol>", "<symbol-2>"]],
    "<symbol-1-1>": [[], ["<symbol-1>", "<symbol-1-1>"]],
    "<character-1>": [[], ["<character>", "<character-1>"]],
    "<digit-1>": [["<digit>"], ["<digit>", "<digit-1>"]]
}
jsonS = '<start>'

# Extract combinations.

if __name__ == '__main__':
    gs = GrammarShrinker(jsonG, jsonS)
    ekeys = gs.find_empty_keys()
    print('Emptyable:', ekeys)
    zrule = jsonG['<member>'][0]
    print('Rule to produce combinations:', zrule)
    comb = gs.rule_combinations(zrule, ekeys)
    for c in comb:
        print('', c)

# Here comes the last part, which stitches all these together.

class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        self.remove_empty_rule_keys()
        e_keys = self.find_empty_keys()
        for e_key in e_keys:
            positions = [i for i,r in enumerate(self.grammar[e_key]) if not r]
            for index in positions:
                del self.grammar[e_key][index]
            assert self.grammar[e_key]

        for key in self.grammar:
            rules_hash = {}
            for rule in self.grammar[key]:
                # find e_key positions.
                combs = self.rule_combinations(rule, e_keys)
                for nrule in combs:
                    rules_hash[str(nrule)] = nrule
            self.grammar[key] = [rules_hash[k] for k in rules_hash]


# Using the complete epsilon remover.

if __name__ == '__main__':
    gs = GrammarShrinker(jsonG, jsonS)
    gs.remove_epsilon_rules()
    gatleast.display_grammar(gs.grammar, gs.start)

# We can now count the strings produced by the epsilon free grammar

if __name__ == '__main__':
    rscfg = grandom.RandomSampleCFG(gs.grammar)
    max_len = 5
    rscfg.produce_shared_forest(gs.start, max_len)
    for i in range(10):
        v, tree = rscfg.random_sample(gs.start, 5)
        string = fuzzer.tree_to_string(tree)
        print("mystring:", repr(string), "at:", v)

# As before, the runnable source of this notebook is [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-29-remove-epsilons.py).
