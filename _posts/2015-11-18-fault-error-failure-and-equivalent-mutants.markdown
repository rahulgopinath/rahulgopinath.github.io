---
published: false
title: Fault, Error, Failure, and Equivalent Mutants
layout: post
---
According to [IEEE 1044-2009](https://standards.ieee.org/findstds/standard/1044-2009.html), A _defect_ is a deficiency in the software artifact (the _source code_ for us working in mutation analysis) that does not meet the requirements. A defect can be detected before execution of the code in question. If a defect escapes detection using any of the pre-execution techniques such as code-review, compilation, static analysis etc. it is called a _fault_. An _error_ is a human action that can result in the above. That is, if a programmer understands a requirement incorrectly when producing the program, or the programming results in an oversight resulting in a deficiency. A _fault_ is a manifestation of an error. A _failure_ may be produced when a _fault_ is encountered during execution of the code in question, and it is the deviation of the behavior of a system from its specification.

The problem with equivalent mutants is this. Given a while loop such as below

```python
def looper(j):
    i = 0
    while i < 10:
        i++
        j += i
    return j

print looper(10)

```
It is equivalent to 
```python
def looper(j):
    i = 0
    while i < 10:
        i++
        j += i
    return j

print looper(10)
```
And no practitioner would claim that the second one is a bug. However consider this.
```python
def roots(a,b,c):
    d = b**2-4*a*c
    if a == 0: return -a/b
    if d < 0: return []
    elif d == 0:
        x1 = -b / (2*a)
        return [x1]
    else:
        x1 = (-b + math.sqrt(d)) / (2*a)
        x2 = (-b - math.sqrt(d)) / (2*a)
        return [x1,x2]
roots(1,2,3)
```
And one of its mutant.
```python
def roots(a,b,c):
    d = b**2-4*a*c
    if d < 0: return []
    elif d == 0:
        x1 = -b / (2*a)
        return [x1]
    else:
        x1 = (-b + math.sqrt(d)) / (2*a)
        x2 = (-b - math.sqrt(d)) / (2*a)
        return [x1,x2]
roots(1,2,3)
```
Since we only invoke `root(1,2,3)` the `divide by zero` can never be caused. However, intuitively, there is
a mistake here, with programmer forgetting to check for the linear case. However, both this, and the previous mutant are under the equivalent mutant category.