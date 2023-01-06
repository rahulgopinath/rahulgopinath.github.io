# ---
# published: true
# title: Generalized LL (GLL) Parser
# layout: post
# comments: true
# tags: parsing, gll
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of GLL Parser in Python
# including SPPF parse tree extraction [^scott2013gll].
# The Python interpreter is embedded so that you can work through the
# implementation steps.
#  
# A GLL parser is a generalization of LL parsers. The first generalized LL
# parser was reported by Grune and Jacob [^grune2008parsing] (11.2) from a
# masters thesis report in 1993 (another possibly earlier paper looking at
# generalized LL parsing is from Lang in 1974 [^lang1974deterministic] and
# another from Bouckaert et al. [^bouckaert1975efficient]).
# However, a better known generalization
# of LL parsing was described by Scott and Johnstone [^scott2010gll]. This
# post follows the later parsing technique.
# In this post, I provide a complete
# implementation and a tutorial on how to implement a GLL parser in Python.
#  
# We [previously discussed](/post/2021/02/06/earley-parsing/) 
# Earley parser which is a general context-free parser. GLL
# parser is another general context-free parser that is capable of parsing
# strings that conform to **any** given context-free grammar.
# The algorithm is a generalization of the traditional recursive descent parsing
# style. In traditional recursive descent parsing, the programmer uses the
# call stack for keeping track of the parse context. This approach, however,
# fails when there is left recursion. The problem is that recursive
# descent parsers cannot advance the parsed index as it is not immediately
# clear how many recursions are required to parse a given string. Bounding
# of recursion as we [discussed before](/post/2020/03/17/recursive-descent-contextfree-parsing-with-left-recursion/)
# is a reasonable solution. However, it is very inefficient.
#   
# GLL parsing offers a solution. The basic idea behind GLL parsing is to
# maintain the call stack programmatically, which allows us to iteratively
# deepen the parse for any nonterminal at any given point. This combined with
# sharing of the stack (GSS) and generation of parse forest (SPPF) makes the
# GLL parsing very efficient. Furthermore, unlike Earley, CYK, and GLR parsers,
# GLL parser operates by producing a custom parser for a given grammar. This
# means that one can actually debug the recursive descent parsing program
# directly. Hence, using GLL can be much more friendly to the practitioner.
#  
# Similar to Earley, GLR, CYK, and other general context-free parsers, the worst
# case for parsing is $$ O(n^3) $$ . However, for LL(1) grammars, the parse time
# is $$ O(n) $$ .
#  
# ## Synopsis
#
# ```python
# import gllparser as P
# my_grammar = {'<start>': [['1', '<A>'],
#                           ['2']
#                          ],
#               '<A>'    : [['a']]}
# my_parser = P.compile_grammar(my_grammar)
# for tree in my_parser.parse_on(text='1a', start_symbol='<start>'):
#     print(P.format_parsetree(tree))
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
# Here is an example grammar for arithmetic expressions, starting at `<start>`.
# A terminal symbol has exactly one character
# (Note that we disallow empty string (`''`) as a terminal symbol).
# Secondly, as per traditional implementations,
# there can only be one expansion rule for the `<start>` symbol. We work around
# this restriction by simply constructing as many charts as there are expansion
# rules, and returning all parse trees.
# 


# ## Traditional Recursive Descent
# Consider how you will parse a string that conforms to the following grammar

g1 = {
    '<S>': [
          ['<A>', '<B>'],
          ['<C>']],
   '<A>': [
        ['a']],
   '<B>': [
        ['b']],
   '<C>': [
        ['c']],
}
g1_start = '<S>'

# In traditional recursive descent, we write a parser in the following fashion

class G1TraditionalRD(ep.Parser):
    def recognize_on(self, text):
        res =  self.S(text, 0)
        if res == len(text): return True
        return False

    # S ::= S_0 | S_1
    def S(self, text, cur_idx):
        if (i:= self.S_0(text, cur_idx)) is not None: return i
        if (i := self.S_1(text, cur_idx)) is not None: return i 
        return None

    # S_0 ::= <A> <B>
    def S_0(self, text, cur_idx):
        if (i := self.A(text, cur_idx)) is None: return None
        if (i := self.B(text, i)) is None: return None
        return i

    # S_1 ::= <C>
    def S_1(self, text, cur_idx):
        if (i := self.C(text, cur_idx)) is None: return None
        return i

    def A(self, text, cur_idx):
        if (i := self.A_0(text, cur_idx)) is not None: return i 
        return None

    # A_0 ::= a
    def A_0(self, text, cur_idx):
        i = cur_idx+1
        if text[cur_idx:i] != 'a': return None
        return i

    def B(self, text, cur_idx):
        if (i := self.B_0(text, cur_idx)) is not None: return i 
        return None

    # B_0 ::= b
    def B_0(self, text, cur_idx):
        i = cur_idx+1
        if text[cur_idx:i] != 'b': return None
        return i

    def C(self, text, cur_idx):
        if (i := self.C_0(text, cur_idx)) is not None: return i 
        return None

    # C_0 ::= c
    def C_0(self, text, cur_idx):
        i = cur_idx+1
        if text[cur_idx:i] != 'c': return None
        return i

# Using it

if __name__ == '__main__':
    p = G1TraditionalRD()
    assert p.recognize_on('ab')
    assert p.recognize_on('c')
    assert not p.recognize_on('abc')
    assert not p.recognize_on('ac')
    assert not p.recognize_on('')

# What if there is recursion? Here is another grammar with recursion
g2 = {
    '<S>': [
          ['<A>']],
   '<A>': [
        ['a', '<A>'],
        []]
}
g2_start = '<S>'

# In traditional recursive descent, we write a parser in the following fashion

class G2TraditionalRD(ep.Parser):
    def recognize_on(self, text):
        res =  self.S(text, 0)
        if res == len(text): return True
        return False

    # S ::= S_0
    def S(self, text, cur_idx):
        if (i:= self.S_0(text, cur_idx)) is not None: return i
        return None

    # S_0 ::= <A>
    def S_0(self, text, cur_idx):
        if (i := self.A(text, cur_idx)) is None: return None
        return i

    def A(self, text, cur_idx):
        if (i := self.A_0(text, cur_idx)) is not None: return i 
        if (i := self.A_1(text, cur_idx)) is not None: return i 
        return None

    # A_0 ::= a <A>
    def A_0(self, text, cur_idx):
        i = cur_idx+1
        if text[cur_idx:i] != 'a': return None
        if (i := self.A(text, i)) is None: return None
        return i

    # A_1 ::= 
    def A_1(self, text, cur_idx):
        return cur_idx

# Using it

if __name__ == '__main__':
    p = G2TraditionalRD()
    assert p.recognize_on('a')
    assert not p.recognize_on('b')
    assert p.recognize_on('aa')
    assert not p.recognize_on('ab')
    assert p.recognize_on('')

# The problem happens when there is a left recursion. For example, the following
# grammar contains a left recursion even though it recognizes the same language
# as before.

g3 = {
    '<S>': [
          ['<A>']],
   '<A>': [
        ['<A>', 'a'],
        []]
}
g3_start = '<S>'

# ## Naive Threaded Recognizer
# The problem with left recursion is that in traditional recursive descent
# style, we are forced to follow a depth first exploration, completing the
# parse of one entire rule before attempting then next rule. We can work around
# this by managing the call stack ourselves. The idea is to convert each
# procedure into a case label, save the previous label in the stack
# (managed by us) before a sub procedure. When the exploration
# is finished, we pop the previous label off the stack, and continue where we
# left off.

class NaiveThreadedRecognizer(ep.Parser):
    def recognize_on(self, text, start_symbol, max_count=1000):
        parser = self.parser
        parser.initialize(text)
        parser.set_grammar(
        {
         '<S>': [['<A>']],
         '<A>': [['<A>', 'a'],
                 []]
        })
        L, stack_top, cur_idx = start_symbol, parser.stack_bottom, 0
        self.count = 0
        while self.count < max_count:
            self.count += 1
            if L == 'L0':
                if parser.threads:
                    (L, stack_top, cur_idx) = parser.next_thread()
                    if (L[0], stack_top, cur_idx) == (start_symbol, parser.stack_bottom, (parser.m-1)):
                        return parser
                    continue
                else:
                    return []
            elif L == 'L_':
                stack_top = parser.fn_return(stack_top, cur_idx) # pop
                L = 'L0' # goto L_0
                continue
        
            elif L == '<S>':
                # <S>::=['<A>']
                parser.add_thread( ('<S>',0,0), stack_top, cur_idx)
                L = 'L0'
                continue

            elif L ==  ('<S>',0,0): # <S>::= | <A>
                stack_top = parser.register_return(('<S>',0,1), stack_top, cur_idx)
                L = '<A>'
                continue

            elif L ==  ('<S>',0,1): # <S>::= <A> |
                L = 'L_'
                continue

            elif L == '<A>':
                # <A>::=['<A>', 'a']
                parser.add_thread( ('<A>',0,0), stack_top, cur_idx)
                # <A>::=[]
                parser.add_thread( ('<A>',1,0), stack_top, cur_idx)
                L = 'L0'
                continue

            elif L == ('<A>',0,0): # <A>::= | <A> a
                stack_top = parser.register_return(('<A>',0,1), stack_top, cur_idx)
                L = "<A>"
                continue

            elif L == ('<A>',0,1): # <A>::= <A> | a
                if parser.I[cur_idx] == 'a':
                    cur_idx = cur_idx+1
                    L = ('<A>',0,2)
                else:
                    L = 'L0'
                continue

            elif L == ('<A>',0,2): # <A>::= <A> a |
                L = 'L_'
                continue

            elif L == ('<A>',1,0): # <A>::= |
                L = 'L_'
                continue

            else:
                assert False

# We also need a way to hold the call stack. The call stack is actually stored
# as a linked list with the current stack_top on the top. With multiple
# alternatives being explored together, we actually have a tree structured stack[^tomita1984lr], but
# the leaf nodes only know about their parent (not the reverse).
# For convenience, we use a wrapper for the call-stack, where we define a few
# book keeping functions. First the initialization of the call stack.

class CallStack:
    def initialize(self, s):
        self.threads = []
        self.I = s + '$'
        self.m = len(self.I)
        self.stack_bottom = {'label':('L0', 0), 'previous': []}

    def set_grammar(self, g):
        self.grammar = g

# Adding a thread simply means appending the label, current stack top, and
# current parse index to the threads. We can also retrieve threads.

class CallStack(CallStack):
    def add_thread(self, L, stack_top, cur_idx):
        self.threads.append((L, stack_top, cur_idx))

    def next_thread(self):
        t, *self.threads = self.threads
        return t

# Next, we define how returns are handed. That is, before exploring a new
# sub procedure, we have to save the return label in the stack, which
# is handled by `register_return()`. The current stack top is added as a child
# of the return label.
class CallStack(CallStack):
    def register_return(self, L, stack_top, cur_idx):
        v = {'label': (L, cur_idx), 'previous': [stack_top]}
        return v

# When we have finished exploring a given procedure, we return back to the
# original position in the stack by poping off the prvious label.

class CallStack(CallStack):
    def fn_return(self, stack_top, cur_idx):
        if stack_top != self.stack_bottom:
            (L, _k) = stack_top['label']
            for c_st in stack_top['previous']: # only one previous
                self.add_thread(L, c_st, cur_idx)
        return stack_top

# Using it.

if __name__ == '__main__':
    p = NaiveThreadedRecognizer()
    p.parser = CallStack()
    assert p.recognize_on('', '<S>')
    print(p.count)
    assert p.recognize_on('a', '<S>')
    print(p.count)
    assert p.recognize_on('aa', '<S>')
    print(p.count)
    assert p.recognize_on('aaa', '<S>')
    print(p.count)

# This unfortunately has a problem. The issue is that, when a string does not
# parse, the recursion along with the epsilon rule means that there is always a
# thread that keeps spawning new threads.
if __name__ == '__main__':
    assert not p.recognize_on('ab', '<S>', max_count=1000)
    print(p.count)


# ## The GSS Graph
# The way to solve it is to use something called a *graph-structured stack*.
# A naive conversion of recursive descent parsing to generalized recursive
# descent parsing can be done by maintaining independent stacks for each thread.
# However, this approach is has problems as we saw previously, when it comes to
# left recursion. The GSS converts the tree structured stack to a graph.
# 
# ### The GSS Node
# A GSS node is simply a node that can contain any number of children. Each
# child is actually an edge in the graph.
# 
# (Each GSS Node is of the form $$L_i^j$$ where $$j$$ is the index of the
# character consumed. However, we do not need to know the internals of the label
# here).

class GSSNode:
    def __init__(self, label): self.label, self.children = label, []
    def __eq__(self, other): return self.label == other.label
    def __repr__(self): return str((self.label, self.children))

# ### The GSS container
# Next, we define the graph container. We keep two structures. `self.graph`
# which is the shared stack, and `self.P` which is the set of labels that went
# through a `fn_return`, i.e. `pop` operation.

class GSS:
    def __init__(self): self.graph, self.P = {}, {}

    def get(self, my_label):
        if my_label not in self.graph:
            self.graph[my_label], self.P[my_label] = GSSNode(my_label), []
        return self.graph[my_label]

    def add_parsed_index(self, label, j):
        self.P[label].append(j)

    def parsed_indexes(self, label):
        return self.P[label]

    def __repr__(self): return str(self.graph)

# A wrapper for book keeping functions.

class GLLStructuredStack:
    def initialize(self, input_str):
        self.I = input_str + '$'
        self.m = len(self.I)
        self.gss = GSS()
        self.stack_bottom = self.gss.get(('L0', 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)]

    def set_grammar(self, g):
        self.grammar = g

# ### GLL+GSS add_thread (add)
# Our add_thread increases a bit in complexity. We now check if a thread already
# exists before starting a new thread.
class GLLStructuredStack(GLLStructuredStack):
    def add_thread(self, L, stack_top, cur_idx):
        if (L, stack_top) not in self.U[cur_idx]:  # added
            self.U[cur_idx].append((L, stack_top)) # added
            self.threads.append((L, stack_top, cur_idx))

# next_thread is same as before
class GLLStructuredStack(GLLStructuredStack):
    def next_thread(self):
        t, *self.threads = self.threads
        return t


# ### GLL+GSS register_return (create)
# A major change in this method. We now look for pre-existing
# edges before appending edges (child nodes).
class GLLStructuredStack(GLLStructuredStack):
    def register_return(self, L, stack_top, cur_idx):
        v = self.gss.get((L, cur_idx))   # added
        v_to_u = [c for c in v.children  # added
                            if c.label == stack_top.label]
        if not v_to_u:                   # added
            v.children.append(stack_top) # added

            for h_idx in self.gss.parsed_indexes(v.label): # added
                self.add_thread(v.L, stack_top, h_idx)     # added
        return v

# ### GLL+GSS fn_return (pop)
# A small change in fn_return. We now save all parsed indexes at
# every label when the parse is complete.
class GLLStructuredStack(GLLStructuredStack):
    def fn_return(self, stack_top, cur_idx):
        if stack_top != self.stack_bottom:
            (L, _k) = stack_top.label
            self.gss.add_parsed_index(stack_top.label, cur_idx) # added
            for c_st in stack_top.children: # changed
                self.add_thread(L, c_st, cur_idx)
        return stack_top

# With GSS, we finally have a true GLL recognizer.
# Here is the same recognizer unmodified, except for checking the parse
# ending. Here, we check whether the start symbol is completely parsed
# only when the threads are complete.
class GLLG1Recognizer(ep.Parser):
    def recognize_on(self, text, start_symbol):
        parser = self.parser
        parser.initialize(text)
        parser.set_grammar(
        {
         '<S>': [['<A>']],
         '<A>': [['<A>', 'a'],
                 []]
        })
        L, stack_top, cur_idx = start_symbol, parser.stack_bottom, 0
        while True:
            if L == 'L0':
                if parser.threads:
                    (L, stack_top, cur_idx) = parser.next_thread()
                    continue
                else: # changed
                    for n_alt, rule in enumerate(self.parser.grammar[start_symbol]):
                        if ((start_symbol, n_alt, len(rule)), parser.stack_bottom) in parser.U[parser.m-1]:
                            parser.root = (start_symbol, 0, parser.m)
                            return parser
                    return []
            elif L == 'L_':
                stack_top = parser.fn_return(stack_top, cur_idx) # pop
                L = 'L0' # goto L_0
                continue
        
            elif L == '<S>':
                # <S>::=['<A>']
                parser.add_thread( ('<S>',0,0), stack_top, cur_idx)
                L = 'L0'
                continue

            elif L ==  ('<S>',0,0): # <S>::= | <A>
                stack_top = parser.register_return(('<S>',0,1), stack_top, cur_idx)
                L = '<A>'
                continue

            elif L ==  ('<S>',0,1): # <S>::= <A> |
                L = 'L_'
                continue

            elif L == '<A>':
                # <A>::=['<A>', 'a']
                parser.add_thread( ('<A>',0,0), stack_top, cur_idx)
                # <A>::=[]
                parser.add_thread( ('<A>',1,0), stack_top, cur_idx)
                L = 'L0'
                continue

            elif L == ('<A>',0,0): # <A>::= | <A> a
                stack_top = parser.register_return(('<A>',0,1), stack_top, cur_idx)
                L = "<A>"
                continue

            elif L == ('<A>',0,1): # <A>::= <A> | a
                if parser.I[cur_idx] == 'a':
                    cur_idx = cur_idx+1
                    L = ('<A>',0,2)
                else:
                    L = 'L0'
                continue

            elif L == ('<A>',0,2): # <A>::= <A> a |
                L = 'L_'
                continue

            elif L == ('<A>',1,0): # <A>::= |
                L = 'L_'
                continue

            else:
                assert False

# Using it.

if __name__ == '__main__':
    p = GLLG1Recognizer()
    p.parser = GLLStructuredStack()
    assert p.recognize_on('', '<S>')
    assert p.recognize_on('a', '<S>')
    assert p.recognize_on('aa', '<S>')
    assert p.recognize_on('aaa', '<S>')
    assert not p.recognize_on('ab', '<S>')
    assert not p.recognize_on('aaab', '<S>')
    assert not p.recognize_on('baaa', '<S>')

# ## GLL Parser
# A recognizer is of limited utility. We need the parse tree if we are to
# use it in practice. Hence, We will now see how to convert this recognizer to a
# parser.
# 
# ## Utilities.
# We start with a few utilities.
# 
# ### Symbols in the grammar
# Here, we extract all terminal and nonterminal symbols in the grammar.

def symbols(grammar):
    terminals, nonterminals = [], []
    for k in grammar:
        for r in grammar[k]:
            for t in r:
                if fuzzer.is_nonterminal(t):
                    nonterminals.append(t)
                else:
                    terminals.append(t)
    return (sorted(list(set(terminals))), sorted(list(set(nonterminals))))


# Using it
if __name__ == '__main__':
    print(symbols(g1))

# ### First, Follow, Nullable sets
# To optimize GLL parsing, we need the [First, Follow, and Nullable](https://en.wikipedia.org/wiki/Canonical_LR_parser#FIRST_and_FOLLOW_sets) sets.
# (*Note* we do not use this at present)
# 
# Here is a nullable grammar.

nullable_grammar = {
    '<start>': [['<A>', '<B>']],
    '<A>': [['a'], [], ['<C>']],
    '<B>': [['b']],
    '<C>': [['<A>'], ['<B>']]
}

# The definition is as follows.

def union(a, b):
    n = len(a)
    a |= b
    return len(a) != n

def get_first_and_follow(grammar):
    terminals, nonterminals = symbols(grammar)
    first = {i: set() for i in nonterminals}
    first.update((i, {i}) for i in terminals)
    follow = {i: set() for i in nonterminals}
    nullable = set()
    while True:
        added = 0
        productions = [(k,rule) for k in nonterminals for rule in grammar[k]]
        for k, rule in productions:
            can_be_empty = True
            for t in rule:
                added += union(first[k], first[t])
                if t not in nullable:
                    can_be_empty = False
                    break
            if can_be_empty:
                added += union(nullable, {k})

            follow_ = follow[k]
            for t in reversed(rule):
                if t in follow:
                    added += union(follow[t], follow_)
                if t in nullable:
                    follow_ = follow_.union(first[t])
                else:
                    follow_ = first[t]
        if not added:
            return first, follow, nullable

# Using

if __name__ == '__main__':
    first, follow, nullable = get_first_and_follow(nullable_grammar)
    print("first:", first)
    print("follow:", follow)
    print("nullable", nullable)


# ### First of a rule fragment.
# (*Note* we do not use this at present)
# We need to compute the expected `first` character of a rule suffix.

def get_rule_suffix_first(rule, dot, first, follow, nullable):
    alpha, beta = rule[:dot], rule[dot:]
    fst = []
    for t in beta:
        if fuzzer.is_terminal(t):
            fst.append(t)
            break
        else:
            fst.extend(first[t])
            if t not in nullable: break
            else: continue
    return sorted(list(set(fst)))

# To verify, we define an expression grammar.

grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<term>', '+', '<expr>'],
        ['<term>', '-', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<fact>', '*', '<term>'],
        ['<fact>', '/', '<term>'],
        ['<fact>']],
    '<fact>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [["%s" % str(i)] for i in range(10)],
}

grammar_start = '<start>'

if __name__ == '__main__':
    rule_first = get_rule_suffix_first(grammar['<term>'][1], 1, first, follow, nullable)
    print(rule_first)

# ## SPPF Graph
# We use a data-structure called *Shared Packed Parse Forest* to represent
# the parse forest. We cannot simply use a parse tree because there may be
# multiple possible derivations of the same input string (possibly even an
# infinite number of them). The basic idea here is that multiple derivations
# (even an infinite number of derivations) can be represented as links in the
# graph.
# 
# The SPPF graph contains four kinds of nodes. The *dummy* node represents an
# empty node, and is the simplest. The *symbol* node represents the parse of a
# nonterminal symbol within a given extent (i, j).
# Since there can be multiple derivations for a nonterminal
# symbol, each derivation is represented by a *packed* node, which is the third
# kind of node. Another kind of node is the *intermediate* node. An intermediate
# node represents a partially parsed rule, containing a prefix rule and a suffix
# rule. As in the case of symbol nodes, there can be many derivations for a rule
# fragment. Hence, an intermediate node can also contain multiple packed nodes.
# A packed node in turn can contain symbol, intermediate, or dummy nodes.
# 
# ### SPPF Node

class SPPFNode:
    def __init__(self): self.children, self.label = [], '<None>'

    def __eq__(self, o): return self.label == o.label

    def add_child(self, child): self.children.append(child)

    def to_s(self, g): return self.label[0]

    def __repr__(self): return 'SPPF:%s' % str(self.label)

    def to_tree(self, hmap, tab): raise NotImplemented

    def to_tree_(self, hmap, tab):
        key = self.label[0] # ignored
        ret = []
        for n in self.children:
            v = n.to_tree_(hmap, tab+1)
            ret.extend(v)
        return ret


# ### SPPF Dummy Node
# The dummy SPPF node is used to indicate the empty node at the end of rules.

class SPPF_dummy_node(SPPFNode):
    def __init__(self, s, i, j): self.label, self.children = (s, i, j), []

# ### SPPF Symbol Node
# j and i are the extents.
# Each symbol can contain multiple packed nodes each
# representing a different derivation. See getNodeP
#
# **Note.** In the presence of ambiguous parsing, we choose a derivation
# at random. So, run the `to_tree()` multiple times to get all parse
# trees. If you want a better solution, see the
# [forest generation in earley parser](/post/2021/02/06/earley-parsing/)
# which can be adapted here too.

class SPPF_symbol_node(SPPFNode):
    def __init__(self, x, i, j): self.label, self.children = (x, i, j), []

    def to_tree(self, hmap, tab): return self.to_tree_(hmap, tab)[0]
    def to_tree_(self, hmap, tab):
        key = self.label[0]
        if self.children:
            n = random.choice(self.children)
            return [[key, n.to_tree_(hmap, tab+1)]]
        return [[key, []]]

# ### SPPF Intermediate Node
# Has only two children max (or 1 child).
class SPPF_intermediate_node(SPPFNode):
    def __init__(self, t, j, i): self.label, self.children = (t, j, i), []

# ### SPPF Packed Node

class SPPF_packed_node(SPPFNode):
    def __init__(self, t, k): self.label, self.children = (t,k), []

# ## The GLL parser
# We can now build our GLL parser. All procedures change to include SPPF nodes.
#
# We first define our initialization
class GLLStructuredStackP:
    def initialize(self, input_str):
        self.I = input_str + '$'
        self.m = len(input_str)
        self.gss = GSS()
        self.stack_bottom = self.gss.get(('L0', 0))
        self.threads = []
        self.U = [[] for j in range(self.m+1)] # descriptors for each index
        self.SPPF_nodes = {}

    def to_tree(self):
        return self.SPPF_nodes[self.root].to_tree(self.SPPF_nodes, tab=0)

    def set_grammar(self, g):
        self.grammar = g
        self.first, self.follow, self.nullable = get_first_and_follow(g)

# ### GLL+GSS+SPPF add_thread (add)
class GLLStructuredStackP(GLLStructuredStackP):
    def add_thread(self, L, stack_top, cur_idx, sppf_w):
        if (L, stack_top, sppf_w) not in self.U[cur_idx]:
            self.U[cur_idx].append((L, stack_top, sppf_w))
            self.threads.append((L, stack_top, cur_idx, sppf_w))

# ### GLL+GSS+SPPF fn_return (pop)
class GLLStructuredStackP(GLLStructuredStackP):
    def fn_return(self, stack_top, cur_idx, sppf_z):
        if stack_top != self.stack_bottom:
            (L, _k) = stack_top.label
            self.gss.add_parsed_index(stack_top.label, sppf_z)
            for c_st,sppf_w in stack_top.children:
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                self.add_thread(L, c_st, cur_idx, sppf_y)
        return stack_top

# ### GLL+GSS+SPPF register_return (create)
class GLLStructuredStackP(GLLStructuredStackP):
    def register_return(self, L, stack_top, cur_idx, sppf_w):
        v = self.gss.get((L, cur_idx))
        v_to_u_labeled_w = [c for c,lbl in v.children
                            if c.label == stack_top.label and lbl == sppf_w]
        if not v_to_u_labeled_w:
            v.children.append((stack_top, sppf_w))

            for sppf_z in self.gss.parsed_indexes(v.label):
                sppf_y = self.getNodeP(L, sppf_w, sppf_z)
                h_idx = sppf_z.label[-1]
                self.add_thread(v.L, stack_top, h_idx, sppf_y)
        return v

# ### GLL+GSS+SPPF utilities.

class GLLStructuredStackP(GLLStructuredStackP):
    def next_thread(self):
        t, *self.threads = self.threads
        return t

    def sppf_find_or_create(self, label, j, i):
        n = (label, j, i)
        if  n not in self.SPPF_nodes: 
            node = None
            if label is None:            node = SPPF_dummy_node(*n)
            elif isinstance(label, str): node = SPPF_symbol_node(*n)
            else:                        node = SPPF_intermediate_node(*n)
            self.SPPF_nodes[n] = node
        return self.SPPF_nodes[n]

# We also need the to produce SPPF nodes correctly.
# 
# `getNode(x, i)` creates and returns an SPPF node labeled `(x, i, i+1)` or
# `(epsilon, i, i)` if x is epsilon
# 
# `getNodeP(X::= alpha.beta, w, z)` takes a grammar slot `X ::= alpha . beta`
# and two SPPF nodes w, and z (z may be dummy node $).
# the nodes w and z are not packed nodes, and will have labels of form
# `(s, j, k)` and `(r, k, i)`


class GLLStructuredStackP(GLLStructuredStackP):
    def not_dummy(self, sppf_w):
        if sppf_w.label[0] == '$':
            assert isinstance(sppf_w, SPPF_dummy_node)
            return False
        assert not isinstance(sppf_w, SPPF_dummy_node)
        return True

    def getNodeT(self, x, i):
        j = i if x is None else i+1
        return self.sppf_find_or_create(x, i, j)

    def getNodeP(self, X_rule_pos, sppf_w, sppf_z):
        X, nalt, dot = X_rule_pos
        rule = self.grammar[X][nalt]
        alpha, beta = rule[:dot], rule[dot:]

        if self.is_non_nullable_alpha(alpha) and beta: return sppf_z

        t = X if beta == [] else X_rule_pos

        _q, k, i = sppf_z.label
        if self.not_dummy(sppf_w):
            _s,j,_k = sppf_w.label # assert k == _k
            children = [sppf_w,sppf_z]
        else:
            j = k
            children = [sppf_z]

        y = self.sppf_find_or_create(t, j, i)
        if not [c for c in y.children if c.label == (X_rule_pos, k)]:
            pn = SPPF_packed_node(X_rule_pos, k)
            for c_ in children: pn.add_child(c_)
            y.add_child(pn)
        return y

    def is_non_nullable_alpha(self, alpha):
        if not alpha: return False
        if len(alpha) != 1: return False
        if fuzzer.is_terminal(alpha[0]): return True
        if alpha[0] in self.nullable: return False
        return True

# We can now use all these to generate trees.

class SPPFG1Recognizer(ep.Parser):
    def recognize_on(self, text, start_symbol):
        parser = self.parser
        parser.initialize(text)
        parser.set_grammar(
        {
         '<S>': [['<A>']],
         '<A>': [['<A>', 'a'],
                 []]
        })
        # L contains start nt.
        end_rule = SPPF_dummy_node('$', 0, 0)
        L, stack_top, cur_idx, cur_sppf_node = start_symbol, parser.stack_bottom, 0, end_rule
        while True:
            if L == 'L0':
                if parser.threads: # if R != \empty
                    (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                    # goto L
                    continue
                else:
                    # if there is an SPPF node (start_symbol, 0, m) then report success
                    if (start_symbol, 0, parser.m) in parser.SPPF_nodes:
                          parser.root = (start_symbol, 0, parser.m)
                          return parser
                    else: return []
            elif L == 'L_':
                stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
                L = 'L0' # goto L_0
                continue
        
            elif L == '<S>':

                # <S>::=['<A>']
                parser.add_thread( ('<S>',0,0), stack_top, cur_idx, end_rule)

                L = 'L0'
                continue
            elif L ==  ('<S>',0,0): # <S>::= | <A>
                stack_top = parser.register_return(('<S>',0,1), stack_top, cur_idx, cur_sppf_node)
                L = "<A>"
                continue

            elif L == ('<S>',0,1): # <S>::= <A> |
                L = 'L_'
                continue

            elif L == '<A>':

                # <A>::=['<A>', 'a']
                parser.add_thread( ('<A>',0,0), stack_top, cur_idx, end_rule)
                # <A>::=[]
                parser.add_thread( ('<A>',1,0), stack_top, cur_idx, end_rule)

                L = 'L0'
                continue
            elif L ==  ('<A>',0,0): # <A>::= | <A> a
                stack_top = parser.register_return(('<A>',0,1), stack_top, cur_idx, cur_sppf_node)
                L = "<A>"
                continue

            elif L == ("<A>",0,1): # <A>::= <A> | a
                if parser.I[cur_idx] == 'a':
                    right_sppf_child = parser.getNodeT(parser.I[cur_idx], cur_idx)
                    cur_idx = cur_idx+1
                    L = ("<A>",0,2)
                    cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
                else:
                    L = 'L0'
                continue

            elif L == ('<A>',0,2): # <A>::= <A> a |
                L = 'L_'
                continue

            elif L == ("<A>", 1, 0): # <A>::= |
                # epsilon: If epsilon is present, we skip the end of rule with same
                # L and go directly to L_
                right_sppf_child = parser.getNodeT(None, cur_idx)
                cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
                L = 'L_'
                continue


            else:
                assert False

# We need trees

class SPPFG1Recognizer(SPPFG1Recognizer):
    def parse_on(self, text, start_symbol):
        p = self.recognize_on(text, start_symbol)
        return [p.to_tree()]

# Using it

if __name__ == '__main__':
    p = SPPFG1Recognizer()
    p.parser = GLLStructuredStackP()
    for tree in p.parse_on('aa', start_symbol='<S>'):
        print(ep.display_tree(tree))

# ## Building the parser with GLL
# At this point, we are ready to build our parser compiler.
# ### Compiling an empty rule
# We start with compiling an epsilon rule.

def compile_epsilon(g, key, n_alt):
    return '''\
        elif L == ("%s", %d, 0): # %s
            # epsilon: If epsilon is present, we skip the end of rule with same
            # L and go directly to L_
            right_sppf_child = parser.getNodeT(None, cur_idx)
            cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            L = 'L_'
            continue
''' % (key, n_alt, ep.show_dot(key, g[key][n_alt], 0))

# Using it.
if __name__ == '__main__':
    v = compile_epsilon(grammar, '<expr>', 1)
    print(v)

# ### Compiling a Terminal Symbol
def compile_terminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = '("%s",%d,%d)' % (key, n_alt, r_pos+1)
    return '''\
        elif L == ("%s",%d,%d): # %s
            if parser.I[cur_idx] == '%s':
                right_sppf_child = parser.getNodeT(parser.I[cur_idx], cur_idx)
                cur_idx = cur_idx+1
                L = %s
                cur_sppf_node = parser.getNodeP(L, cur_sppf_node, right_sppf_child)
            else:
                L = 'L0'
            continue
''' % (key, n_alt, r_pos, ep.show_dot(key, g[key][n_alt], r_pos), token, Lnxt)

# ### Compiling a Nonterminal Symbol
def compile_nonterminal(g, key, n_alt, r_pos, r_len, token):
    if r_len == r_pos:
        Lnxt = '"L_"'
    else:
        Lnxt = "('%s',%d,%d)" % (key, n_alt, r_pos+1)
    return '''\
        elif L ==  ('%s',%d,%d): # %s
            stack_top = parser.register_return(%s, stack_top, cur_idx, cur_sppf_node)
            L = "%s"
            continue
''' % (key, n_alt, r_pos, ep.show_dot(key, g[key][n_alt], r_pos), Lnxt, token)

# Using it.
if __name__ == '__main__':
    rule = grammar['<expr>'][1]
    for i, t in enumerate(rule):
        if fuzzer.is_nonterminal(t):
            v = compile_nonterminal(grammar, '<expr>', 1, i, len(rule), t)
        else:
            v = compile_terminal(grammar, '<expr>', 1, i, len(rule), t)
        print(v)

# ### Compiling a Rule
# `n_alt` is the position of `rule`.
def compile_rule(g, key, n_alt, rule):
    res = []
    if not rule:
        r = compile_epsilon(g, key, n_alt)
        res.append(r)
    else:
        for i, t in enumerate(rule):
            if fuzzer.is_nonterminal(t):
                r = compile_nonterminal(g, key, n_alt, i, len(rule), t)
            else:
                r = compile_terminal(g, key, n_alt, i, len(rule), t)
            res.append(r)
        # if epsilon present, we do not want this branch.
        res.append('''\
        elif L == ('%s',%d,%d): # %s
            L = 'L_'
            continue
''' % (key, n_alt, len(rule), ep.show_dot(key, g[key][n_alt], len(rule))))
    return '\n'.join(res)

# Using it.
if __name__ == '__main__':
    v = compile_rule(grammar, '<expr>', 1, grammar['<expr>'][1])
    print(v)


# ### Compiling a Definition
# Note that if performance is important, you may want to check if the current
# input symbol at `parser.I[cur_idx]` is part of the following, where X is a
# nonterminal and p is a rule fragment. Note that if you care about the
# performance, you will want to pre-compute first[p] for each rule fragment
# `rule[j:]` in the grammar, and first and follow sets for each symbol in the
# grammar. This should be checked before `parser.add_thread`.

def test_select(a, X, p, rule_first, follow):
    if a in rule_first[p]: return True
    if '' not in rule_first[p]: return False
    return a in follow[X]

# Given that removing this check does not affect the correctness of the
# algorithm, I have chosen not to add it.

def compile_def(g, key, definition):
    res = []
    res.append('''\
        elif L == '%s':
''' % key)
    for n_alt,rule in enumerate(definition):
        res.append('''\
            # %s
            parser.add_thread( ('%s',%d,0), stack_top, cur_idx, end_rule)''' % (key + '::=' + str(rule), key, n_alt))
    res.append('''
            L = 'L0'
            continue''')
    for n_alt, rule in enumerate(definition):
        r = compile_rule(g, key, n_alt, rule)
        res.append(r)
    return '\n'.join(res)

# Using it.
if __name__ == '__main__':
    v = compile_def(grammar, '<expr>', grammar['<expr>'])
    print(v)

# A template.
class GLLParser(ep.Parser):
    def recognize_on(self, text, start_symbol):
        raise NotImplemented()

# ### Compiling a Grammar

def compile_grammar(g, evaluate=True):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    res = ['''\
def recognize_on(self, text, start_symbol):
    parser = self.parser
    parser.initialize(text)
    parser.set_grammar(
%s
    )
    # L contains start nt.
    end_rule = SPPF_dummy_node('$', 0, 0)
    L, stack_top, cur_idx, cur_sppf_node = start_symbol, parser.stack_bottom, 0, end_rule
    while True:
        if L == 'L0':
            if parser.threads: # if R != \empty
                (L, stack_top, cur_idx, cur_sppf_node) = parser.next_thread()
                # goto L
                continue
            else:
                # if there is an SPPF node (start_symbol, 0, m) then report success
                if (start_symbol, 0, parser.m) in parser.SPPF_nodes:
                      parser.root = (start_symbol, 0, parser.m)
                      return parser
                else: return []
        elif L == 'L_':
            stack_top = parser.fn_return(stack_top, cur_idx, cur_sppf_node) # pop
            L = 'L0' # goto L_0
            continue
    ''' % pp.pformat(g)]
    for k in g: 
        r = compile_def(g, k, g[k])
        res.append(r)
    res.append('''
        else:
            assert False''')
    res.append('''
def parse_on(self, text, start_symbol):
    p = self.recognize_on(text, start_symbol)
    return [p.to_tree()]
    ''')

    parse_src = '\n'.join(res)
    s = GLLParser()
    s.src = parse_src
    if not evaluate: return parse_src
    l, g = locals().copy(), globals().copy()
    exec(parse_src, g, l)
    s.parser = GLLStructuredStackP()
    s.recognize_on = l['recognize_on'].__get__(s)
    s.parse_on = l['parse_on'].__get__(s)
    return s

# Using it
if __name__ == '__main__':
    v = compile_grammar(grammar, False)
    print(v)

# ## Running it
# ### 1
if __name__ == '__main__':
    G1 = {
        '<S>': [['c']]
    }
    mystring = 'c'
    p = compile_grammar(G1)
    v = p.parse_on(mystring, '<S>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 2
if __name__ == '__main__':
    G2 = {
        '<S>': [['c', 'c']]
    }
    mystring = 'cc'
    p = compile_grammar(G2)
    v = p.parse_on(mystring, '<S>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 3
if __name__ == '__main__':
    G3 = {
        '<S>': [['c', 'c', 'c']]
    }
    mystring = 'ccc'
    p = compile_grammar(G3)
    v = p.parse_on(mystring, '<S>')[0]
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 4
if __name__ == '__main__':
    G4 = {
        '<S>': [['c'],
                ['a']]
    }
    mystring = 'a'
    p = compile_grammar(G4)
    v = p.parse_on(mystring, '<S>')[0]
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 5

if __name__ == '__main__':
    G5 = {
        '<S>': [['<A>']],
        '<A>': [['a']]
    }
    mystring = 'a'
    p = compile_grammar(G5)
    v = p.parse_on(mystring, '<S>')[0]
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ## Expression

# ### 1
if __name__ == '__main__':
    mystring = '(1+1)*(23/45)-1'
    p = compile_grammar(grammar)
    v = p.parse_on(mystring, grammar_start)[0]
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ### 2
# Since we use a random choice to get different parse trees in ambiguity, click
# the run button again and again to get different parses.
if __name__ == '__main__':
    a_grammar = {
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
    mystring = '1+2+3+4'
    p = compile_grammar(a_grammar)
    v = p.parse_on(mystring, grammar_start)[0]
    r = fuzzer.tree_to_string(v)
    assert r == mystring
    ep.display_tree(v)

# ## A few more examples
if __name__ == '__main__':
    RR_GRAMMAR2 = {
        '<start>': [
        ['b', 'a', 'c'],
        ['b', 'a', 'a'],
        ['b', '<A>', 'c']
        ],
        '<A>': [['a']],
    }
    mystring = 'bac'
    p = compile_grammar(RR_GRAMMAR2)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    RR_GRAMMAR3 = {
        '<start>': [['c', '<A>']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring = 'cababababab'
     
    p = compile_grammar(RR_GRAMMAR3)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(7)
     
    RR_GRAMMAR4 = {
        '<start>': [['<A>', 'c']],
        '<A>': [['a', 'b', '<A>'], []],
    }
    mystring = 'ababababc'
     
    p = compile_grammar(RR_GRAMMAR4)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(8)
     
    RR_GRAMMAR5 = {
    '<start>': [['<A>']],
    '<A>': [['a', 'b', '<B>'], []],
    '<B>': [['<A>']],
    }
    mystring = 'abababab'
     
    p = compile_grammar(RR_GRAMMAR5)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(9)
     
    RR_GRAMMAR6 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<B>'], []],
    '<B>': [['b', '<A>']],
    }
    mystring = 'abababab'
     
    p = compile_grammar(RR_GRAMMAR6)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(10)

    RR_GRAMMAR7 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']],
    }
    mystring = 'aaaaaaaa'

    p = compile_grammar(RR_GRAMMAR7)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(11)

    RR_GRAMMAR8 = {
    '<start>': [['<A>']],
    '<A>': [['a', '<A>'], ['a']]
    }
    mystring = 'aa'

    p = compile_grammar(RR_GRAMMAR8)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print(12)

    X_G1 = {
        '<start>': [['a']],
    }
    mystring = 'a'
    p = compile_grammar(X_G1)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G1')

    X_G2 = {
        '<start>': [['a', 'b']],
    }
    mystring = 'ab'
    p = compile_grammar(X_G2)
    v = p.parse_on(mystring, '<start>')[0]
    print('X_G2')

    X_G3 = {
        '<start>': [['a', '<b>']],
        '<b>': [['b']]
    }
    mystring = 'ab'
    p = compile_grammar(X_G3)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G3')

    X_G4 = {
        '<start>': [
        ['a', '<a>'],
        ['a', '<b>'],
        ['a', '<c>']
        ],
        '<a>': [['b']],
        '<b>': [['b']],
        '<c>': [['b']]
    }
    mystring = 'ab'
    p = compile_grammar(X_G4)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring


    print('X_G4')

    X_G5 = {
        '<start>': [['<expr>']],
        '<expr>': [
            ['<expr>', '+', '<expr>'],
            ['1']]
    }
    X_G5_start = '<start>'

    mystring = '1+1'
    p = compile_grammar(X_G5)
    v = p.parse_on(mystring, '<start>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring


    print('X_G5')

    X_G6 = {
        '<S>': [
        ['b', 'a', 'c'],
        ['b', 'a', 'a'],
        ['b', '<A>', 'c'],
        ],
        '<A>': [
            ['a']]
    }
    X_G6_start = '<S>'

    mystring = 'bac'
    p = compile_grammar(X_G6)
    v = p.parse_on(mystring, '<S>')[0]
    print(v)
    r = fuzzer.tree_to_string(v)
    assert r == mystring

    print('X_G6')

# We assign format parse tree so that we can refer to it from this module

def format_parsetree(t):
    return ep.format_parsetree(t)

# [^lang1974deterministic]: Bernard Lang. "Deterministic techniques for efficient non-deterministic parsers." International Colloquium on Automata, Languages, and Programming. Springer, Berlin, Heidelberg, 1974.
#
# [^bouckaert1975efficient] M. Bouckaert, Alain Pirotte, M. Snelling. "Efficient parsing algorithms for general context-free parsers." Information Sciences 8.1 (1975): 1-26.
# 
# [^scott2013gll]: Elizabeth Scott, Adrian Johnstone. "GLL parse-tree generation." Science of Computer Programming 78.10 (2013): 1828-1844.
# 
# [^scott2010gll]: Elizabeth Scott, Adrian Johnstone. "GLL parsing." Electronic Notes in Theoretical Computer Science 253.7 (2010): 177-189.
# 
# [^grune2008parsing]: Dick Grune and Ceriel J.H. Jacobs "Parsing Techniques A Practical Guide" 2008
# 
# [^tomita1984lr]: Masaru Tomita. LR parsers for natural languages. In 22nd conference on Association for Computational Linguistics, pages 354–357, Stanford, California, 1984. Association for Computational Linguistics.
