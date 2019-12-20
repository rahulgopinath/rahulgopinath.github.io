---
published: true
title: When are comprehensions (list, set) harmful in Python?
layout: post
comments: true
tags: parsing
categories: post
---

When programming in Python, one is often encouraged to apply list or set comprehensions in preference to methods such as `map` and `filter` since they mostly accomplish similar things. For example, say we have a list of 10 numbers
```pycon
>>> lst = list(range(10))
```
To apply a procedure, say `square` on the list elements, one can either use a `list comprehension` or a `map`
```pycon
>>> def square(x): return x*x
>>> [square(i) for i in lst]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
# Using a generator expression
>>> list(square(i) for i in lst)
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
# note that map is a generator in 3.x
>>> list(map(square, lst))
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```
However, are these two `(square(i) for i in lst)` and `map(square, lst)` the same? One area that one should watch out for is when you want to use a lambda expression.
```pycon
>>> v = [lambda: i*i for i in lst]
>>> [j() for j in v]
[81, 81, 81, 81, 81, 81, 81, 81, 81, 81]
```
On the other hand, a generator expression behaves as one would intuitively expect.
```pycon
>>> v = (lambda: i*i for i in lst)
>>> [j() for j in v]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```
So does `map`
```pycon
>>> v = map(lambda i: lambda: i*i, lst)
>>> [j() for j in v]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```
The reason is that the comprehensions effectively use the same variable to store each different value during iteration. The trouble with doing that is that, when one uses `lambda` which has the iteration variable as a `free variable`, it closes over the iteration variable, and creates a closure. This closure gets saved in the result of the comprehension. The problem here is that, each lambda closs over the same variable (think of it as saving a reference to the same variable). Hence, when any of the `lambda` gets invoked later, the value of the iterator variable would be the value it was assigned last in the comprehension. Hence the above behavior.

Does it mean that one should use the generator expression instead? since it is closer to the pythonic spirit? Unfortunately, there are still traps for the unwary.
```pycon
>>> v = (lambda: i for i in lst)
>>> [j() for j in v]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
# We can not reuse the generator expression as it is oneshot.
>>> v = (lambda: i for i in lst)
>>> [j() for j in list(v)]
[9, 9, 9, 9, 9, 9, 9, 9, 9, 9]
```
The reason the first behaves as expected is because of the way generators work. The first generator is steped one at a time in the first when we request of execution of the lambda in `j()`. Hence, eventhough it is the same variable `i`, it works as expected for us because new values are assigned and used in a single step.

On the other hand, `map` still works correctly
```pycon
>>> v = map(lambda i: lambda: i*i, lst)
>>> [j() for j in v]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
>>> v = map(lambda i: lambda: i*i, lst)
>>> [j() for j in list(v)]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```
The whole problem is due to the implicit variable capture. Map forces us to bind the variable i, which makes it a new variable for each iteration. It is possible to do the same thing in comprehensions too.
```pycon
>>> v = ((lambda i: lambda: i*i)(k) for k in lst)
>>> [j() for j in v]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
>>> v = ((lambda i: lambda: i*i)(k) for k in lst)
>>> [j() for j in list(v)]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

Indeed, here, `map` conforms to the [zen of python](https://www.python.org/dev/peps/pep-0020/) compared to the behavior of comprehensions. Unfortunately, I lost quite a bit of time that I did not have, debugging this, and I think that the implicit closing over behavior that comprehensions exhibit is actitvely harmful.
