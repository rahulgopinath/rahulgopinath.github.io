# ---
# published: true
# title: Intersection Between a Context Free Grammar and a Regular Grammar
# layout: post
# comments: true
# tags: python
# categories: post
# ---

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
gexpr = import_file('gexpr', '2021-09-11-fault-expressions.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
rxfuzzer = import_file('rxfuzzer', '2021-10-22-fuzzing-with-regular-expressions.py')
rxcanonical = import_file('rxcanonical', '2021-10-24-canonical-regular-grammar.py')

#     $$ A \rightarrow BC $$
#     $$ A \rightarrow a $$
#     $$ A \rightarrow B $$
#     $$ S \rightarrow \epsilon $$

from collections import defaultdict

def new_k(k, y, x):
    return '<%s %s-%s>' % (k[1:-1], str(y), str(x))

def binary_form(g, s):
    new_g = defaultdict(list)
    productions_to_process = [(k, i, 0, r) for k in g for i,r in enumerate(g[k])]
    while productions_to_process:
        (k, y, x, r), *productions_to_process =  productions_to_process
        if x > 0:
            k_ = new_k(k, y, x)
        else:
            k_ = k
        if len(r) == 0:
            new_g[k_].append(r)
        elif len(r) == 1:
            new_g[k_].append(r)
        elif len(r) == 2:
            new_g[k_].append(r)
        else:
            new_g[k_].append(r[:1] + [new_k(k, y, x+1)])
            remaining = r[1:]
            prod = (k, y, x+1, remaining)
            productions_to_process.append(prod)
    return new_g, s 

EXPR_GRAMMAR = {
    '<start>': [['<expr>']],
    '<expr>': [ ['<term>', '+', '<expr>'], ['<term>', '-', '<expr>'], ['<term>']],
    '<term>': [ ['<fact>', '*', '<term>'], ['<fact>', '/', '<term>'], ['<fact>']],
    '<fact>': [ ['<digits>'], ['(','<expr>',')']],
    '<digits>': [ ['<digit>','<digits>'], ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(1)],
}
EXPR_GRAMMAR = {
    '<start>': [['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(2)],
}
EXPR_START = '<start>'

JSON_GRAMMAR = {
        '<start>': [['<json>']],
        '<json>': [['<element>']],
        '<element>': [['<ws>', '<value>', '<ws>']],
        '<value>': [
           ['<object>'],
           ['<array>'],
           ['<string>'],
           ['<number>'],
           list('true'),
           list('false'),
           list('null')],
        '<object>': [
            ['{', '<ws>', '}'],
            ['{', '<members>', '}']],
        '<members>': [
            ['<member>'],
            ['<member>', ',', '<members>']
        ],
        '<member>': [
            ['<ws>', '<string>', '<ws>', ':', '<element>']],
        '<array>': [
            ['[', '<ws>', ']'],
            ['[', '<elements>', ']']],
        '<elements>': [
            ['<element>'],
            ['<element>', ',', '<elements>']
        ],
        '<string>': [
            ['"', '<characterz>', '"']],
        '<characterz>': [
                [],
                ['<character>', '<characterz>']],
        '<character>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['g'], ['h'], ['i'], ['j'],
            ['k'], ['l'], ['m'], ['n'], ['o'], ['p'], ['q'], ['r'], ['s'], ['t'],
            ['u'], ['v'], ['w'], ['x'], ['y'], ['z'], ['A'], ['B'], ['C'], ['D'],
            ['E'], ['F'], ['G'], ['H'], ['I'], ['J'], ['K'], ['L'], ['M'], ['N'],
            ['O'], ['P'], ['Q'], ['R'], ['S'], ['T'], ['U'], ['V'], ['W'], ['X'],
            ['Y'], ['Z'], ['!'], ['#'], ['$'], ['%'], ['&'], ["'"], ['('], [')'],
            ['*'], ['+'], [','], ['-'], ['.'], ['/'], [':'], [';'], ['<'], ['='],
            ['>'], ['?'], ['@'], ['['], [']'], ['^'], ['_'], ['`'], ['{'], ['|'],
            ['}'], ['~'], [' '], ['\\"'], ['\\\\'], ['\\/'], ['<escaped>']],
        '<number>': [
            ['<int>', '<frac>', '<exp>']],
        '<int>': [
           ['<digit>'],
           ['<onenine>', '<digits>'],
           ['-', '<digits>'],
           ['-', '<onenine>', '<digits>']],
        '<digit>': [
            ['0'],
            ['<onenine>']],
        '<onenine>': [
            ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<frac>': [
            [],
            ['.', '<digits>']],
        '<exp>': [
                [],
                ['E', '<sign>', '<digits>'],
                ['e', '<sign>', '<digits>']],
        '<sign>': [[], ['+'], ['-']],
        '<ws>': [['<sp1>', '<ws>'], []],
        '<sp1>': [[' ']], ##[['\n'], ['\r'], ['\t'], ['\x08'], ['\x0c']],
        '<digits>': [
                ['<digit>'],
                ['<digit>', '<digits>']],
        '<escaped>': [
                ['\\u', '<hex>', '<hex>', '<hex>', '<hex>']],
        '<hex>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['A'], ['B'], ['C'], ['D'], ['E'],   ['F']]
}
JSON_START = '<start>'

# Check it works

if __name__ == '__main__':
     g, s = binary_form(JSON_GRAMMAR, JSON_START)
     gatleast.display_grammar(g, s)

def split_into_three(ks, kf, reaching):
    lst = []
    for k in ([ks] + reaching[ks]):
        if kf in reaching[k]:
            lst.append((ks, k, kf))
    return lst

def reachable_dict(g):
    gn = gatleast.reachable_dict(g)
    return {k:list(gn[k]) for k in gn}

def filter_grammar(g, s):
    new_g = {}
    for k in g:
        new_rs = []
        for r in g[k]:
            new_r = [t[1] for t in r]
            new_rs.append(new_r)
        new_g[k[1]] = new_rs
    return new_g, s[1]

def make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f):
    new_g1 = defaultdict(list)
    cf_reachable = reachable_dict(cf_g)
    r_reachable = reachable_dict(r_g)
    for cf_k in cf_g:
        for cf_r in cf_g[cf_k]:
            if len(cf_r) == 0:
                for r_k1 in r_g:
                    # what are reachable from r_k1 with exactly epsilon?
                    # itself!
                    r = [(r_k1, '', r_k1)]
                    new_g1[(r_k1, cf_k, r_k1)].append(r)
                    # or the final from the start.
                    if r_k1 == r_s:
                        if r_f in r_g[r_k1]:
                            r = [(r_k1, '', r_f)]
                            new_g1[(r_k1, cf_k, r_k1)].append(r)
            elif len(cf_r) == 1:
                cf_token =  cf_r[0]
                #assert fuzzer.is_terminal(cf_token) <- we also allow nonterminals
                if fuzzer.is_terminal(cf_token):
                    for r_k1 in r_g:
                        # things reachable from r_k1 with exactly cf_token -- there is just one in canonical RG.
                        for rule in r_g[r_k1]:
                            if not rule: continue
                            if rule[0] != cf_token: continue
                            r_k2 = rule[1]
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
                else:
                    for r_k1 in r_g:
                        for r_k2 in ([r_k1] + r_reachable[r_k1]):
                            # postpone checking cf_token
                            r = [(r_k1, cf_token, r_k2)]
                            new_g1[(r_k1, cf_k, r_k2)].append(r)
            elif len(cf_r) == 2:
                for r_k1 in r_g:
                    for r_k2 in ([r_k1] + r_reachable[r_k1]): # things reachable from r_k1
                        for a,b,c in split_into_three(r_k1, r_k2, r_reachable):
                            r = [(a, cf_r[0], b), (b, cf_r[1], c)]
                            new_g1[(a, cf_k, c)].append(r)
            else:
                assert False
    return new_g1, (r_s, cf_s, r_f)

def filter_terminal_transitions(g, r_g):
    new_g1 = defaultdict(list)
    for key in g:
        for rule in g[key]:
            if len(rule) == 1:
                a, t, b = rule[0]
                if len(t) == 0:
                    assert a == b
                else:
                    if fuzzer.is_terminal(t):
                        found_right_transition = any([1 for r_rule in r_g[a] if r_rule and r_rule[0] == t and r_rule[1] == b])
                        if found_right_transition:
                            new_g1[key].append(rule)
                    else:
                        new_g1[key].append(rule)
            else:
                new_g1[key].append(rule)
    return new_g1

def filter_rules_with_undefined_keys(g):
    cont = False
    new_g1 = defaultdict(list)
    for k in g:
        for r in g[k]:
            if len(r) == 0:
                new_g1[k].append(r)
            elif len(r) == 1:
                if fuzzer.is_nonterminal(r[0][1]):
                    if r[0] not in g:
                        cont = True
                        pass
                    else:
                        new_g1[k].append(r)
                else:
                    new_g1[k].append(r)
            elif len(r) == 2:
                assert fuzzer.is_nonterminal(r[0][1])
                assert fuzzer.is_nonterminal(r[1][1])
                if r[0] not in g or r[1] not in g:
                    cont = True
                    pass
                else:
                    new_g1[k].append(r)
            else: assert False
    return new_g1, cont

def intersect_cfg_and_rg(cf_g, cf_s, r_g, r_s, r_f=rxcanonical.NT_EMPTY):
    # first wrap every token in start and end states.
    new_g, new_s = make_triplet_rules(cf_g, cf_s, r_g, r_s, r_f)
    gatleast.display_grammar(*filter_grammar(new_g, new_s))

    # remove any (a, x, b) sequence where x is terminal, and a does not have a transition a x b
    new_g = filter_terminal_transitions(new_g, r_g)
    gatleast.display_grammar(*filter_grammar(new_g, new_s))

    cont = True
    while cont:
        new_g1, cont = filter_rules_with_undefined_keys(new_g)
        # Now, remove any rule that refers to nonexistant keys.
        new_g = {k:new_g1[k] for k in new_g1 if new_g1[k]} # remove empty keys
        gatleast.display_grammar(*filter_grammar(new_g, new_s))

    print()
    gatleast.display_grammar(*filter_grammar(new_g, new_s))
    print()
    # convert keys to template
    new_g1 = defaultdict(list)
    for k in new_g:
        for r in new_g[k]:
            new_g1[convert_key(k)].append([convert_key(t) for t in r])
    new_g = new_g1
    return new_g, convert_key(new_s)

def convert_key(k):
    p,k,q = k
    if fuzzer.is_nonterminal(k):
    #return '<%s,%s,%s>' % (p[1:-1], k[1:-1], q[1:-1])
        return '<%s %s %s>' % (p[1:-1], k[1:-1], q[1:-1])
    else:
        return '[%s %s %s]' % (p[1:-1], k[1:-1], q[1:-1])
    #return k

expr_re = '1+'

if __name__ == '__main__':
    rg, rs = rxcanonical.regexp_to_regular_grammar(expr_re)
    rxcanonical.display_canonical_grammar(rg, rs)
    string = '111'
    re_start = '<^>'
    rg[re_start] = [[rs]]
    rp = earleyparser.EarleyParser(rg, parse_exceptions=False)
    res = rp.recognize_on(string, re_start)
    assert res
    bg, bs = binary_form(EXPR_GRAMMAR, EXPR_START)
    ing, ins = intersect_cfg_and_rg(bg, bs, rg, rs)
    gatleast.display_grammar(ing, ins)

# The runnable code for this post is available
# [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-26-regular-grammar-expressions.py)
