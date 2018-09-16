---
published: false
title: Parsing Context Free Languages with Derivatives in Python
layout: post
comments: true
tags: parsing
---

```python
def is_empty(l): return l == []
def is_eps(l):   return l == ''
def is_char(l):  return isinstance(l, str) and len(l) == 1    # 'a'
def is_star(l):  return isinstance(l, tuple) and len(l) == 1  # (x,)
def is_alt(l):   return isinstance(l, tuple) and len(l) > 1   # (a,b,c)
def is_cat(l):   return isinstance(l, list)                   # [a,b,c]

def nullable(l):
    if is_empty(l): return False
    if is_eps(l):   return True
    if is_char(l):  return False
    if is_star(l):  return True
    if is_alt(l):   return any(nullable(i) for i in l)
    if is_cat(l):   return all(nullable(i) for i in l)

def derive(c, l):
    if is_empty(l): return []
    if is_eps(l):   return []
    if is_char(l):  return '' if c == l else []
    if is_alt(l):   return tuple(derive(c, i) for i in l)
    if is_cat(l):
        if nullable(l[0]):
            return (derive(c, l[1:]), [derive(c, l[0])] + l[1:])
        else:
            return [derive(c, l[0])] + l[1:]
    if is_star(l): return [derive(c, l[0]), l]
    return False

def matches(w, l):
    return nullable(l) if w == '' else matches(w[1:], derive(w[0], l))

#print(matches('aabzd', [('a',), ['b', ('x', 'y', 'z'), 'd', ('e',)]]))
#print(matches('aabnd', [('a',), ['b', ('x', 'y', 'z'), 'd', ('e',)]]))

digit = tuple(list("0123456789"))
floater = [('', ('+', '-')),
              (digit,),
              '.',
              digit,
              (digit,)]

for i in [("-2.0", True), ("1", False), ("", False), ("+12.12", True), ("1.0", True)]:
    print(i[0], matches(i[0], floater), i[1])
```

## Add recursive names (need `lambda`)

```python
def is_empty(l): return l == []
def is_eps(l):   return l == ''
def is_char(l):  return isinstance(l, str) and len(l) == 1    # 'a'
def is_star(l):  return isinstance(l, tuple) and len(l) == 1  # (x,)
def is_alt(l):   return isinstance(l, tuple) and len(l) > 1   # (a,b,c)
def is_cat(l):   return isinstance(l, list)                   # [a,b,c]

def nullable(lx):
    l = lx()
    if is_empty(l): return False
    if is_eps(l):   return True
    if is_char(l):  return False
    if is_star(l):  return True
    if is_alt(l):   return any(nullable(i) for i in l)
    if is_cat(l):   return all(nullable(i) for i in l)
    assert False

def derive(c, lx):
    l = lx()
    if is_empty(l): return lambda: []
    if is_eps(l):   return lambda: []
    if is_char(l):  return (lambda: '') if c == l else lambda: []
    if is_alt(l):   return lambda: tuple(derive(c, i) for i in l)
    if is_cat(l):
        if nullable(l[0]):
            return lambda: (derive(c, lambda: l[1:]), lambda: [derive(c, l[0])] + l[1:])
        else:
            return lambda: [derive(c, l[0])] + l[1:]
    if is_star(l): return lambda: [derive(c, l[0]), l]
    assert False

def matches(w, l):
    if w == '':
        return nullable(l)
    else:
        lx = derive(w[0], l)
        return matches(w[1:], lx)

print(matches('b', lambda: 'b'))
print(matches('x', lambda: 'b'))
print(matches('ab', lambda: [lambda: 'a', lambda: (lambda: 'b', lambda: 'x')]))

L = lambda: [lambda: 'a', lambda: (lambda: 'b', lambda: 'x'), lambda: 'c']
print(matches('axc', L))

S = lambda: (lambda: [lambda: 'b', S], lambda: '')
print(matches('b', S))

B = lambda: [lambda: 'a', S]
print(matches('ab', B))
```

## With least fixed point

```python
def is_empty(l): return l == []
def is_eps(l):   return l == ''
def is_char(l):  return isinstance(l, str) and len(l) == 1    # 'a'
def is_star(l):  return isinstance(l, tuple) and len(l) == 1  # (x,)
def is_alt(l):   return isinstance(l, tuple) and len(l) > 1   # (a,b,c)
def is_cat(l):   return isinstance(l, list)                   # [a,b,c]

def nullable(l, lfp):
    if is_empty(l): return False
    if is_eps(l):   return True
    if is_char(l):  return False
    if is_star(l):  return True
    if is_alt(l):   return any(lfp.get(i()) for i in l)
    if is_cat(l):   return all(lfp.get(i()) for i in l)
    assert False

def derive(x, lfp):
    c,l = x
    if is_empty(l): return []
    if is_eps(l):   return []
    if is_char(l):  return '' if c == l else []
    if is_alt(l):   return tuple(lfp.get((c, i())) for i in l)
    if is_cat(l):
        if LFP(nullable)(l[0]()):
            return (lfp.get((c, l[1:])), [lfp.get((c, l[0]()))] + l[1:])
        else:
            return [lfp.get((c, l[0]()))] + l[1:]
    if is_star(l): return [lfp.get((c, l[0]())), l]
    return False

class LFP:
    Bottom = False
    def __init__(self, fn):
        self.cache = {}
        self.visited = set()
        self.changed = True
        self.fn = fn

    def __call__(self, obj):
        v = None
        while self.changed:
            self.reset()
            v = self.get(obj)
        return v

    def reset(self):
        self.changed = False
        self.visited = set()

    def get(self, obj):
        if str(obj) in self.visited:
            return self.cache.get(obj, LFP.Bottom)
        else:
            self.visited.add(str(obj))
            val = self.fn(obj, self)
            if self.cache.get(str(obj), LFP.Bottom) != val:
                self.changed = True
                self.cache[str(obj)] = val
            return val

def matches(w, l):
    return LFP(nullable)(l) if w == '' else matches(w[1:], LFP(derive)((w[0], l)))

# B = ((B 'b') | eps)

B = (lambda: [lambda: B, lambda: 'b'], lambda: '')

# L = (L 'a' B) | eps

L = (lambda: [lambda: [ lambda: L, lambda: 'a' ], lambda: B], lambda: '')



L_ = [lambda: 'a']
L0 = [lambda: 'a', lambda: 'b']
L1 = (lambda: [lambda: 'a', lambda: 'b'], lambda: '')


print(LFP(nullable)(L))
print(matches('x', L_))
```
