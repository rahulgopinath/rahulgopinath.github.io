---
published: false
title: Fault, Error, Failure, and Equivalent Mutants
layout: post
---
According to IEEE, a _mistake_ is a problem in the logical conceptualization of the program in the programmers mind. A _fault_ is a lexical problem within a program, which can lead to compilation error if the compiler catches it, or can lead to incorrect program if the compiler fails to catch it. An _error_ is an incorrect state during the execution of a program which happens due to the execution passing through a fault (for our purposes -- there can be other causes of errors). When the error manifests in a detectable deviation in behavior of the program, we call the deviation a _failure_.

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