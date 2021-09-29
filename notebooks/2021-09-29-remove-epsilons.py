# ---
# published: true
# title: Remove empty (epsilon) rules from a grammar.
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the previous post about [uniform random sampling from grammars](https://rahul.gopinath.org/post/2021/07/27/random-sampling-from-context-free-grammar/)
# I mentioned that the algorithm expects an *epsilon-free*` grammar. That is,
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

import sys, imp
import itertools as I

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
        with open(module_loc, encoding='utf-8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# We import the following modules
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')

# Note that we still need an empty expansion inside the definition. i.e `[[]]`.
# Leaving `<empty>` without an expansion, i.e. `[]` means that `<empty>` can't
# be expanded, and hence we will have an invalid grammar.

# ## Remove empty keys

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
# rules. First, we need to identify such rules that are empty.
#
# ## Finding empty (epsilon) rules

class GrammarShrinker(GrammarShrinker):
    def find_epsilon_rules(self):
        e_rules = []
        for key in self.grammar:
            if key == self.start: continue
            rules = self.grammar[key]
            for i, r in enumerate(rules):
                if not r:
                    e_rules.append((key, i))
        return e_rules

# We can use it thus:

if __name__ == '__main__':
    gs = GrammarShrinker(newG, newS)
    erules = gs.find_epsilon_rules()
    print('Empty rules:')
    for key,rule in erules:
        print('',key,rule)

# Now that we can find epsilon rules, we need generate all combinations of
# the corresponding keys, so that we can generate corresponding rules.

class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            a = list(I.combinations(positions, n))
            combinations.extend(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            new_rules.append(new_rule)
        return new_rules

# We can use it thus:

if __name__ == '__main__':
    gs = GrammarShrinker(newG, newS)
    zrule = newG['<spaceZ>'][0]
    print('Rule to produce combinations:', zrule)
    erules = gs.find_epsilon_rules()
    comb = gs.rule_combinations(zrule, [k for k,rule in erules])
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
    zrule = jsonG['<member>'][0]
    erules = gs.find_epsilon_rules()
    print('Rule to produce combinations:', zrule)
    comb = gs.rule_combinations(zrule, [k for k,rule in erules])
    for c in comb:
        print('', c)

# Here comes the last part, which stitches all these together.

class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        while True:
            self.remove_empty_rule_keys()
            e_rules = self.find_epsilon_rules()
            if not e_rules: break
            for e_key, index in e_rules:
                del self.grammar[e_key][index]
                assert self.grammar[e_key]

            for key in self.grammar:
                rules_hash = {}
                for rule in self.grammar[key]:
                    # find e_key positions.
                    combs = self.rule_combinations(rule, [k for k,i in e_rules])
                    for nrule in combs:
                        rules_hash[str(nrule)] = nrule
                self.grammar[key] = [rules_hash[k] for k in rules_hash]


# Using the complete epsilon remover.

if __name__ == '__main__':
    gs = GrammarShrinker(jsonG, jsonS)
    gs.remove_epsilon_rules()
    gatleast.display_grammar(gs.grammar, gs.start)

# As before, the runnable source of this notebook is [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-29-remove-epsilons.py).
