---
layout: page
title : Silly little idioms that should never be used
header : Silly little idioms that should never be used
group: navigation
exclude: true
---

## Python

### Declawing PEP 3113 -- No argument destructuring in python3

```
ls.sort(key=lambda (value, frequency): -frequency) # Python2

ls.sort(key=lambda x: next(-frequency for value, frequency in [x])) # Python3

```

This is better than the first level unwrapping

```
ls.sort(key=lambda x: (lambda value, frequency: frequency)(*x))
```

