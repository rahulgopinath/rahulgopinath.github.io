---
published: false
title: Parsing with table parsers
layout: post
comments: true
tags: parsing
categories: post
---
```python
import sys
def rules(g): return [(k,e) for k,a in g.items() for e in a]

def terminals(g):
    return set(token for k,expr in rules(g) for token in expr if token not in g)

def fixpoint(f):
    def helper(*args):
        while True:
            sargs = repr(args)
            args_ = f(*args)
            if repr(args_) == sargs: return args
            args = args_
    return helper

@fixpoint
def compute_ff(grammar, first, follow, epsilon):
    for A, expression in rules(grammar):
        nullable = True
        for token in expression:
            first[A] |= first[token]

            # update until the first token that is not nullable
            if token not in epsilon: nullable = False; break

        if nullable:
            epsilon |= {A}
            first[A] |= {''}

        # https://www.cs.uaf.edu/~cs331/notes/FirstFollow.pdf
        # essentially, we start from the end of the expression. Then:
        # (3) if there is a production A -> aB, then every thing in
        # FOLLOW(A) is in FOLLOW(B)
        follow_B = follow[A]
        for t in reversed(expression):
            if not t: continue
            # update the follow for the current token. If this is the
            # first iteration, then here is the assignment
            if t in grammar: follow[t] |= follow_B #only bother with nt

            # computing the last follow symbols for each token t. This
            # will be used in the next iteration. If current token is
            # nullable, then previous follows can be a legal follow for
            # next. Else, only the first of current token is legal follow
            # essentially

            # (2) if there is a production A -> aBb then everything in FIRST(B)
            # except for epsilon is added to FOLLOW(B)
            follow_B = follow_B | (first[t] - {''}) if t in epsilon else first[t]

    return (grammar, first, follow, epsilon)

def process(grammar):
    # first initialize the first for non terminals.
    first = {i: set() for i in grammar}
    follow = {i: set() for i in grammar}

    # If X is a terminal, then First(X) is just X
    first.update((i,{i}) for i in terminals(grammar))
    epsilon = {''}
    return compute_ff(grammar, first, follow, epsilon)

def rnullable(rule, epsilon):
    return all(token in epsilon for token in rule)

def rfirst(rule, first, epsilon):
    tokens = set()
    for token in rule:
        tokens |= first[token]
        if token not in epsilon: break # not nullable
    return tokens

def predict(rulepair, first, follow, epsilon):
    A, rule = rulepair
    rf = rfirst(rule, first, epsilon)
    if rnullable(rule, epsilon): rf |= follow[A] - {''}
    return rf

def parse_table(grammar, my_rules):
    _, first, follow, epsilon = process(grammar)

    ptable = [(rule,predict(rule, first, follow, epsilon)) for rule in my_rules]

    parse_tbl = {k:{} for k in grammar}

    for (k,expr),pvals in ptable:
        parse_tbl[k].update({v:(k,expr) for v in pvals})
    return parse_tbl

def parse_helper(grammar, tbl, stack, inplst):
    inp,*inplst = inplst
    while stack:
        val,*stack = stack
        if val not in grammar: # terminal
            if val == '': continue
            if val != inp: raise Exception("%s != %s" % (val, inp))
            inp,*inplst = inplst if inplst else ['']
        else:
            k,rhs = tbl[val][inp]
            assert k == val
            stack = rhs + stack

def parse(grammar, inp):
    my_rules =  rules(grammar)
    parse_tbl = parse_table(grammar, my_rules)
    k,_ = my_rules[0]
    stack = [k]
    return parse_helper(grammar, parse_tbl, stack, list(inp))


grammar = {
        'S': [['E']],
        'E': [['T','X']],
        'X': [
            ['+', 'T', 'X'],
            ['']],
        'T': [['F', 'Y']],
        'Y': [
            ['*', 'F', 'Y'],
            ['']],
        'F': [['(', 'E', ')'], ['x']]
        }
parse(grammar, sys.argv[1] if len(sys.argv) > 1 else '(x+x)')
```
