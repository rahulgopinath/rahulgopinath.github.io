# ---
# published: true
# title: CYK Parser
# layout: post
# comments: true
# tags: parsing, gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of CYK Parser in Python[^grune2008parsing]
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#  
# A CYK parser is a general context-free parser. 
# It uses dynamic # programming to fill in a chart. Unlike Earley, GLL and GLR
# parsers, it requires the grammar to be in the Chomsky normal form, which
# allows at most two symbols on the right hand side of any production.
# In particular, all the rules have to conform to
# 
# $$ A -> BC $$
# 
# $$ A -> a $$
# 
# $$ S -> \epsilon $$
# 
# Where A,B, and C are nonterminal symbols, a is a terminal symbol, S is the
# start symbol, and $$\epsilon$$ is the empty string.
#  
# We [previously discussed](/post/2021/02/06/earley-parsing/) 
# Earley parser which is a general context-free parser. CYK
# parser is another general context-free parser that is capable of parsing
# strings that conform to **any** given context-free grammar.
#  
# Similar to Earley, GLR, GLL, and other general context-free parsers, the worst
# case for CYK parsing is $$ O(n^3) $$ . However, unlike those parsers, the best
# case is also $$ O(n^3) $$ for all grammars. A peculiarity of CYK parser is that
# unlike Earley, GLL, and GLR, it is not a left-to-right parser. In this respect,
# the best known other parser that is not left-to-right is Ungar's parser.
# Furthermore, it is a bottom-up parser that builds substrings of fixed length
# from the bottom up.
#  
# ## Synopsis
#
# ```python
# import cykparser as P
# my_grammar = {'<start>': [['1', '<A>'],
#                           ['2']
#                          ],
#               '<A>'    : [['a']]}
# my_parser = P.CYKParser(my_grammar)
# assert my_parser.recognize_on(text='1a', start_symbol='<start>'):
# for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
#     P.display_tree(tree)
# ```

# ## Definitions
# For this post, we use the following terms:
#  
# * The _alphabet_ is the set all of symbols in the input language. For example,
#   in this post, we use all ASCII characters as alphabet.
# 
# * A _terminal_ is a single alphabet symbol. Note that this is slightly different
#   from usual definitions (done here for ease of parsing). (Usually a terminal is
#   a contiguous sequence of symbols from the alphabet. However, both kinds of
#   grammars have a one to one correspondence, and can be converted easily.)
# 
#   For example, `x` is a terminal symbol.
# 
# * A _nonterminal_ is a symbol outside the alphabet whose expansion is _defined_
#   in the grammar using _rules_ for expansion.
# 
#   For example, `<term>` is a nonterminal in the below grammar.
# 
# * A _rule_ is a finite sequence of _terms_ (two types of terms: terminals and
#   nonterminals) that describe an expansion of a given terminal. A rule is
#   also called an _alternative_ expansion.
# 
#   For example, `[<term>+<expr>]` is one of the expansion rules of the nonterminal `<expr>`.
# 
# * A _production_ is a combination of a nonterminal and one of its productions.
# 
#   For example `<expr>: [<term>+<expr>]` is a production.
# 
# * A _definition_ is a set of _rules_ that describe the expansion of a given nonterminal.
# 
#   For example, `[[<digit>,<digits>],[<digit>]]` is the definition of the nonterminal `<digits>`
# 
# * A _context-free grammar_ is  composed of a set of nonterminals and 
#   corresponding definitions that define the structure of the nonterminal.
# 
#   The grammar given below is an example context-free grammar.
#  
# * A terminal _derives_ a string if the string contains only the symbols in the
#   terminal. A nonterminal derives a string if the corresponding definition
#   derives the string. A definition derives the  string if one of the rules in
#   the definition derives the string. A rule derives a string if the sequence
#   of terms that make up the rule can derive the string, deriving one substring
#   after another contiguously (also called parsing).
# 
# * A *derivation tree* is an ordered tree that describes how an input string is
#   derived by the given start symbol. Also called a *parse tree*.
# * A derivation tree can be collapsed into its string equivalent. Such a string
#   can be parsed again by the nonterminal at the root node of the derivation
#   tree such that at least one of the resulting derivation trees would be the
#   same as the one we started with.
# 
# * The *yield* of a tree is the string resulting from collapsing that tree.
# 
# * An *epsilon* rule matches an empty string.

# 
# #### Prerequisites
#  
# As before, we start with the prerequisite imports.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl

# We need the fuzzer to generate inputs to parse and also to provide some
# utilities
import simplefuzzer as fuzzer
# We use the `display_tree()` method in earley parser for displaying trees.
import earleyparser as ep

# We use the random choice to extract derivation trees from the parse forest.
import random

# As before, we use the [fuzzingbook](https://www.fuzzingbook.org) grammar style.
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# 

# Let us start with the following grammar.

g1 = {
    '<S>': [
          ['<A>', '<B>'],
          ['<B>', '<C>'],
          ['<A>', '<C>'],
          ['c']],
   '<A>': [
        ['<B>', '<C>'],
        ['a']],
   '<B>': [
        ['<A>', '<C>'],
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

# We initialize our parser with the grammar, and identify the terminal and
# nonterminal productions separately. termiinal productions are those that
# are of the form `<A> ::= a` where a is a terminal symbol. Nonterminal
# productions are of the form `<A> ::= <B><C>` where `<B>` and `<C>` are
# nonterminal symbols.

class CYKRecognizer(ep.Parser):
    def __init__(self, grammar):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.cell_width = 5 

        # let us get an inverse cache
        self.terminal_rules = {}
        self.nonterminal_rules = {}
        for k, rule in self.productions:
            if fuzzer.is_terminal(rule[0]):
                if k not in self.terminal_rules:
                    self.terminal_rules[rule[0]] = []
                self.terminal_rules[rule[0]].append(k)
            else:
                if k not in self.nonterminal_rules:
                    self.nonterminal_rules[(rule[0],rule[1])] = []
                self.nonterminal_rules[(rule[0],rule[1])].append(k)

# Next, we define the recognizer. The idea here is that CYK algorithm formulates
# the recognition problem as a dynamic problem where the parse of a string of
# length `n` using a nonterminal `<A>` which is defined as `<A> ::= <B> <C>` is
# defined as a parse of the substring `0..x` with the nonterminal `<B>` and the
# parse of the substring `x..n` with nonterminal `<C>` where `0 < x < n`. That
# is, `<A>` parses the string if there exists such a parse with `<B>` and `<C>`
# for some `x`.
#
# We first initialize the matrix that holds the results. The `cell[i][j]`
# represents the nonterminals that can parse the substring `text[i..j]`

class CYKRecognizer(CYKRecognizer):
    def init_table(self, text, length):
        return [[{} for i in range(length+1)] for j in range(length+1)]

# Let us define a printing routine.
class  CYKRecognizer(CYKRecognizer):
    def print_table(self, table):
        for i, row in enumerate(table):
            # f"{value:{width}.{precision}}"
            s = f'{i:<2}'
            for j,cell in enumerate(row):
                ckeys = list(cell.keys())
                if len(ckeys) == 0:
                    r = ''
                    s += f'|{r:>{self.cell_width}}'
                elif len(ckeys) == 1:
                    r = ckeys[0]
                    s += f'|{r:>{self.cell_width}}'
                else:
                    l = 2 + (j+1) * (self.cell_width + 1)
                    r = ckeys[0]
                    s += f'|{r:>{self.cell_width}}'
                    for ck in ckeys[1:]:
                        s += '\n' + f'{ck:>{l}}'
            print(s + '|')

# Using it
if __name__ == '__main__':
    p = CYKRecognizer(g1)
    t = p.init_table('abcd', 4)
    p.print_table(t)
    print()

# Next, we define the base case, which is when a single input token matches one
# of the terminal symbols. In that case, we look at each character in the input,
# and for each `i` in the input we identify `cell[i][i+1]` and add the
# nonterminal symbol that derives the corresponding token.

class CYKRecognizer(CYKRecognizer):
    def parse_1(self, text, length, table):
        for s in range(0,length):
            table[s][s+1] = {key:True for key in self.terminal_rules[text[s]]}
        return table

# Using it
if __name__ == '__main__':
    p = CYKRecognizer(g1)
    txt = 'aabc'
    tbl = p.init_table(txt, len(txt))
    p.parse_1(txt, len(txt), tbl)
    p.print_table(tbl)


# Next, we define the multi-token parse. The idea is to build the table
# incrementally. We have already indicated in the table which nonterminals parse
# a single token. Next, we find all nonterminals that parse two tokens, then
# using that, we find all nonterminals that can parse three tokens etc.

class CYKRecognizer(CYKRecognizer):
    def parse_n(self, text, n, length, table):
        # check substrings starting at s, with length n
        for s in range(0, length-n+1):
            # partition the substring at p (n = 1 less than the length of substring)
            for p in range(1, n):
                pairs = [(b,c) for b in table[s][p] for c in table[s+p][s+n]]
                matching_pairs = [(b,c) for (b,c) in pairs
                            if (b,c) in self.nonterminal_rules]
                keys = {k:True for pair in matching_pairs
                               for k in self.nonterminal_rules[pair]}
                table[s][s+n].update(keys)
        return table

# Using it for example, on substrings of length 2
if __name__ == '__main__':
    print('length: 2')
    p = CYKRecognizer(g1)
    txt = 'aabc'
    tbl = p.init_table(txt, len(txt))
    p.parse_1(txt, len(txt), tbl)
    p.parse_n(txt, 2, len(txt), tbl)
    p.print_table(tbl)

# For length 3
if __name__ == '__main__':
    print('length: 3')
    p.parse_n(txt, 3, len(txt), tbl)
    p.print_table(tbl)

# For length 4
if __name__ == '__main__':
    print('length: 4')
    p.parse_n(txt, 4, len(txt), tbl)
    p.print_table(tbl)


# We combine everything together. At the end, we check if the start_symbol can
# parse the given tokens by checking (0, n) in the table.
class CYKRecognizer(CYKRecognizer):
    def recognize_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        self.parse_1(text, length, table)
        for n in range(2,length+1): # n is the length of the sub-string
            self.parse_n(text, n, length, table)
        return start_symbol in table[0][-1]

# Using it
if __name__ == '__main__':
    mystring = 'aabc'
    p = CYKRecognizer(g1)
    v = p.recognize_on(mystring, '<S>')
    print(v)

    mystring = 'cb'
    p = CYKRecognizer(g1)
    v = p.recognize_on(mystring, '<S>')
    print(v)

# At this point, we have a recognizer for a grammar in CNF form. However, this
# is a bit unsatisfying because the CNF form is not very userfriendly. In
# particluar it lacks two conveniences we are used to in context-free gramamrs
# 
# 1. Having more than two tokens in a rule
# 2. The ability to add epsilon rules.
# 
# The first one is not very difficult to solve. Given an expansion rule for a
# nonterminal
# ```
# <nt> ::= <a> <b> <c> <d>
# ```
# we can always rewrite this as
# ```
# <nt> ::= <a> <nt_1_1>
# <nt_1_1> ::= <b> <nt_1_2>
# <nt_1_2> ::= <c> <d>
# ```
# and so on. We can also recover the structure back from any parse tree by
# combining the corresponding tokens. The second restriction is more difficult
# Having to factor out epsilon can change the grammar completely. Turns out, it
# is not very difficult to incorporate epsilons into this parser.
# 
# First, we extract all nullable nonterminals of our grammar. (See Earley parser)

def is_nt(k):
    return (k[0], k[-1]) == ('<', '>')

def rem_terminals(g):
    g_cur = {}
    for k in g:
        alts = []
        for alt in g[k]:
            ts = [t for t in alt if not is_nt(t)]
            if not ts:
                alts.append(alt)
        if alts:
            g_cur[k] = alts
    return g_cur

def nullable(g):
    nullable_keys = {k for k in g if [] in g[k]}

    unprocessed  = list(nullable_keys)

    g_cur = rem_terminals(g)
    while unprocessed:
        nxt, *unprocessed = unprocessed
        g_nxt = {}
        for k in g_cur:
            g_alts = []
            for alt in g_cur[k]:
                alt_ = [t for t in alt if t != nxt]
                if not alt_:
                    nullable_keys.add(k)
                    unprocessed.append(k)
                    break
                else:
                    g_alts.append(alt_)
            if g_alts:
                g_nxt[k] = g_alts
        g_cur = g_nxt

    return nullable_keys

# Let us test this out


nullable_grammar = {
    '<start>': [['<A>', '<D>']],
    '<D>': [['<A>', '<B>']],
    '<A>': [['a'], [], ['<C>']],
    '<B>': [['b']],
    '<C>': [['<A>'], ['<B>']]
}

# Testing

if __name__ == '__main__':
    v = nullable(nullable_grammar)
    print(v)

# Once we have the nullable grammar, for each nonterminal in our grammar,
# we want to identify whether parsinga string with one nonterminal
# guarantees parse of a parent nonterminal. This is because if <A> parses
# a string s1, and there exists a rule `<A> := <B> <C>` and <B> is nullable,
# then parsing with <C> guarantees that <A> also can parse it.
# So, this is what we will do.

def extend_chain(guarantee_1):
    # initialize it with the first level parent
    chains = {k:set(guarantee_1[k]) for k in guarantee_1}
    while True:
        modified = False
        for k in chains:
            # for each token, get the guarantees, and add it to current
            for t in list(chains[k]):
                for v in chains[t]:
                    if v not in chains[k]:
                        chains[k].add(v)
                        modified = True
        if not modified: break
    return chains

def identify_gauranteed_parses(grammar):
    guarantee_1 = {k:[] for k in grammar}
    nullable_keys = nullable(grammar)
    for k in grammar:
        for r in grammar[k]:
            if len(r) == 0: continue
            if len(r) == 1: continue
            # <A>:k := <B> <C>
            b, c = r
            if b in nullable_keys:
                # parsing with c guarantees parsing with A
                guarantee_1[c].append(k)
            if c in nullable_keys:
                # parsing with b guarantees parsing with A
                guarantee_1[b].append(k)
    return extend_chain(guarantee_1)

# A grammar. Note that we use `<>` to represent empty (epsilon) nonterminal
nullable_grammar = {
    '<start>': [
        ['<A>', '<B>']],
    '<A>': [
        ['<_a>', '<>'],
        [],
        ['<C>', '<>']],
    '<B>': [
        ['<_b>', '<>']],
    '<C>': [
        ['<A>', '<>'],
        ['<B>', '<>']],

    '<>': [[]],
    '<_a>': [['a']],
    '<_b>': [['b']]
}


# Testing
if __name__ == '__main__':
    v = identify_gauranteed_parses(nullable_grammar)
    print(v)

# So at this point, all we have to do is, after each cell is computed fully, we
# just have to extend the cell with the guaranteed parse.

class CYKRecognizer(CYKRecognizer):
    def __init__(self, grammar):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.cell_width = 5 

        # let us get an inverse cache
        self.terminal_rules = {}
        self.nonterminal_rules = {}
        for k, rule in self.productions:
            if not rule: continue # empty
            if fuzzer.is_terminal(rule[0]):
                if k not in self.terminal_rules:
                    self.terminal_rules[rule[0]] = []
                self.terminal_rules[rule[0]].append(k)
            else:
                if k not in self.nonterminal_rules:
                    self.nonterminal_rules[(rule[0],rule[1])] = []
                self.nonterminal_rules[(rule[0],rule[1])].append(k)

        self.chains = identify_gauranteed_parses(grammar)

    def parse_1(self, text, length, table):
        for s in range(0,length):
            table[s][s+1] = {key:True for key in self.terminal_rules[text[s]]}
            for k in list(table[s][s+1]):
                table[s][s+1].update({v:True for v in self.chains[k]})
        return table

    def parse_n(self, text, n, length, table):
        # check substrings starting at s, with length n
        for s in range(0, length-n+1):
            # partition the substring at p (n = 1 less than the length of substring)
            for p in range(1, n):
                matching_pairs = [
                        (b,c) for b in table[s][p] for c in table[s+p][s+n]
                            if (b,c) in self.nonterminal_rules]
                keys = {k:True for pair in matching_pairs
                               for k in self.nonterminal_rules[pair]}
                table[s][s+n].update(keys)

        for s in range(0, length-n+1):
            for k in list(table[s][s+n]):
                # for each key, add the chain.
                table[s][s+n].update({v:True for v in self.chains[k]})
        return table

# Testing
if __name__ == '__main__':
    mystring = 'b' # g.fuzz('<start>')
    print(v)
    p = CYKRecognizer(nullable_grammar)
    v = p.recognize_on(mystring, '<start>')
    print(v)
    assert v

    g = fuzzer.LimitFuzzer(nullable_grammar)
    for i in range(100):
        mystring = g.fuzz('<start>')
        p = CYKRecognizer(nullable_grammar)
        v = p.recognize_on(mystring, '<start>')
        assert v

# Handling epsilons now allows us to get to the next step in supporting any
# context free grammar. We require two more steps to support.
# 1. Replacing terminal symbols with nonterminal symbols representing tokens
# 2. Ensuring that there are exactly two nonterminal symbols in any nonterminal
# rule. We will handle the first one now.

def replace_terminal_symbols(grammar):
    new_g = {}
    for k in grammar:
        new_g[k] = []
        for r in grammar[k]:
            new_r = []
            new_g[k].append(new_r)
            for t in r:
                if fuzzer.is_terminal(t):
                    nt = '<_' + t + '>'
                    new_g[nt] = [[t]]
                    new_r.append(nt)
                else:
                    new_r.append(t)
    return new_g

# Test

if __name__ == '__main__':
    my_grammar = {
            '<start>' : [['<p*>']],
            '<p*>' : [['<p>', '<p*>'], []],
            '<p>' : [['(', '<p>', ')'], ['1']]
    }
    g_new_g =  replace_terminal_symbols(my_grammar)
    print(g_new_g)

# Next, we want to replace any rule that contains more than two tokens with
# it decomposition.
# [] = []
# [t1] = [t1]
# [t1, t2] = [t1, t2]
# [t1, t2, t3] = [t1, _t2], _t2 = [t2, t3]

def decompose_rule(rule, prefix):
    l = len(rule)
    if l in [0, 1, 2]: return rule, {}
    t, *r = rule
    kp = prefix + '_'
    nr, d = decompose_rule(r, kp)
    k = '<' + kp + '>'
    d[k] = [nr]
    return [t, k], d


# test
if __name__ == '__main__':
    my_r = ['<a>', '<b>', '<c>', '<d>', '<e>']
    nr, d = decompose_rule(my_r, '')
    print(nr)
    for k in d:
        print(k, d[k])

# decompose grammar

def decompose_grammar(grammar):
    new_g = {}
    for k in grammar:
        new_g[k] = []
        for i,r in enumerate(grammar[k]):
            nr, d = decompose_rule(r, k[1:-1] + '_' + str(i))
            new_g[k].append(nr)
            new_g.update(d)
    return new_g

# all that remains now is to ensure that each rule is exactly two
# token nonterminal, or a single token terminal.
def is_newterminal(k):
    return k[1] == '_'

def balance_grammar(grammar):
    new_g = {}
    for k in grammar:
        if is_newterminal(k):
            assert len(grammar[k]) == 1
            new_g[k] = grammar[k]
            continue
        new_g[k] = []
        for r in grammar[k]:
            l = len(r)
            if l == 0:
                new_g[k].append([])
            elif l == 1:
                new_g[k].append([r[0], '<>'])
            elif l == 2:
                new_g[k].append(r)
            else:
                assert False
    return new_g

# connecting everything together

def cfg_to_cnf(g):
    g1 = replace_terminal_symbols(g)
    g2 = decompose_grammar(g1)
    g3 = balance_grammar(g2)
    g3['<>'] = [[]]
    return g3

# A grammar

expr_grammar = {
'<start>': [['<expr>']],
'<expr>': [
    ['<expr>', '+', '<expr>'],
    ['<expr>', '-', '<expr>'],
    ['<expr>', '*', '<expr>'],
    ['<expr>', '/', '<expr>'],
    ['(', '<expr>', ')'],
    ['<integer>']],
'<integer>': [
    ['<digits>']],
'<digits>': [
    ['<digit>','<digits>'],
    ['<digit>']],
'<digit>': [["%s" % str(i)] for i in range(10)],
}

# Test
if __name__ == '__main__':
    g = cfg_to_cnf(expr_grammar)
    for k in g:
        print(k)
        for r in g[k]:
            print('\t', r)

# Testing
if __name__ == '__main__':
    mystring = '1+1'
    cnf_expr = cfg_to_cnf(expr_grammar)
    p = CYKRecognizer(cnf_expr)
    v = p.recognize_on(mystring, '<start>')
    print(v)
    assert v

    g = fuzzer.LimitFuzzer(cnf_expr)
    for i in range(100):
        mystring = g.fuzz('<start>')
        p = CYKRecognizer(cnf_expr)
        v = p.recognize_on(mystring, '<start>')
        assert v


# ## CYKParser
# Now, all we need to do is to add trees. Unlike GLL, GLR, and Earley, due to
# restricting epsilons to the start symbol, there are no infinite parse trees.

class CYKParser(CYKRecognizer):
    def __init__(self, grammar):
        self.grammar = grammar
        self.productions = [(k,r) for k in grammar for r in grammar[k]]
        self.terminal_productions = [(k,r[0])
            for (k,r) in self.productions if fuzzer.is_terminal(r[0])]
        self.nonterminal_productions = [(k,r)
            for (k,r) in self.productions if not fuzzer.is_terminal(r[0])]

# The parse_1 for terminal symbols

class CYKParser(CYKParser):
    def parse_1(self, text, length, table):
        for s in range(0,length):
            for (key, terminal) in self.terminal_productions:
                if text[s] == terminal:
                    if key not in table[s][s+1]:
                        table[s][s+1][key] = []
                    table[s][s+1][key].append((key, [(text[s], [])]))
        return table

# The substring parse

class CYKParser(CYKParser):
    def parse_n(self, text, n, length, table):
        for s in range(0, length-n+1):
            for p in range(1, n):
                for (k, [R_b, R_c]) in self.nonterminal_productions:
                    if R_b in table[s][p]:
                        if R_c in table[s+p][s+n]:
                            if k not in table[s][s+n]:
                                table[s][s+n][k] = []
                            table[s][s+n][k].append(
                                (k,[table[s][p][R_b], table[s+p][s+n][R_c]]))

# Parsing

class CYKParser(CYKParser):
    def trees(self, forestnode):
        if forestnode:
            if isinstance(forestnode, list):
                key, children = random.choice(forestnode)
            else:
                key,children = forestnode
            ret = []
            for c in children:
                t = self.trees(c)
                ret.append(t)
            return (key, ret)

        return None

    def parse_on(self, text, start_symbol):
        length = len(text)
        table = self.init_table(text, length)
        self.parse_1(text, length, table)
        for n in range(2,length+1):
            self.parse_n(text, n, length, table)
        return [self.trees(table[0][-1][start_symbol])]


# Using it (uses random choice, click run multiple times to get other trees).
if __name__ == '__main__':
    mystring = 'aabc'
    p = CYKParser(g1)
    v = p.parse_on(mystring, '<S>')
    for t in v:
        print(ep.display_tree(t))

# assign display_tree

def display_tree(t):
    return ep.display_tree(t)

# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008

