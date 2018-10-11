---
published: false
title: Parsing with table parsers
layout: post
comments: true
tags: parsing
---
```python
def rules(g): return [(k,e) for k,a in g.items() for e in a]

def terminals(g):
    return set(s for _,a in g.items() for e in a for s in e if s not in g)

def fixpoint(f):
    def helper(farg, *args):
        x = [farg] + list(args)
        while True:
            hx = repr(x)
            newx = f(*x)
            hn = repr(newx)
            if hn == hx: return x
            x = newx
        assert False
    return helper

@fixpoint
def process(grammar, first, follow, epsilon):
    for nonterm, expression in rules(grammar):
        nullable = True
        for symbol in expression:
            first[nonterm] |= first[symbol]

            # update until the first symbol that is not nullable
            if symbol not in epsilon:
                nullable = False
                break
        if nullable:
            epsilon.add(nonterm)

        nt_follow = follow[nonterm]
        for symbol in reversed(expression):
            if symbol in follow: follow[symbol] |= nt_follow
            # if the symbol was nullable, then we simply append
            # to the previous symbols follow. If not, the actual
            # follow is the current follow
            nt_follow = nt_follow | first[symbol] if symbol in epsilon else first[symbol]

    return (grammar, first, follow, epsilon)

grammar = {
        'start': [['E','$']],
        'E': [['E','+','T'], ['T']],
        'T': [['T','*','F'], ['F']],
        'F': [['(','E',')'], ['x']],
        }

# first initialize the first for non terminals.
first = {i: set() for i in grammar.keys()}
follow = {i: set() for i in grammar.keys()}

# If X is a terminal, then First(X) is just X
ft = {i:{i} for i in terminals(grammar)}
first.update(ft)
epsilon = set()
p = fixpoint(process)
g, first, follow, e = p(grammar, first, follow, epsilon)
print('first')
for k in first:
    print(k, first[k])
print()

print('follow')
for k in follow:
    print(k, follow[k])

print(e)
```
