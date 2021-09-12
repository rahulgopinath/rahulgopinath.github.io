---
published: true
title: Some Sillyness with Python Iterators  as Pipes
layout: post
comments: true
tags: pipes, python
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.9/';</script>
<script src="/resources/pyodide/full/3.9/pyodide.js"></script>
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/pyodide/js/env/editor.js" type="text/javascript"></script>

**Important:** [Pyodide](https://pyodide.readthedocs.io/en/latest/) takes time to initialize.
Initialization completion is indicated by a red border around *Run all* button.
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
Here is a how we write a normal `for` loop in Python.

<!--
############
for i in [1,2,3,4,5,6,7,8,9]:
    print(i)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in [1,2,3,4,5,6,7,8,9]:
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What if you want to operate on the list, such as squaring each element, or
perhaps only selecting values greater than 5? Python list comprehensions are the
Pythonic solution, which is as below

<!--
############
for i in [i*i for i in [1,2,3,4,5,6,7,8,9] if i > 5]:
    print(i)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in [i*i for i in [1,2,3,4,5,6,7,8,9] if i &gt; 5]:
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
But I have always found more complex list comprehensions a bit difficult to
read. Is there a better solution? Here is an attempt to adapt a UNIX shell
pipelines like solution to Python. Something like

```
[i1,2,3,4,5,6,7,8,9] | where(_ > 5) | map(_ * _)
```

Here is a possible solution. What we need is a way to stitch operations on a
list together. So, we define a class `Chains` with the `__or__` *dunder method*
redefined. What it does is to connect the current object to the right object
in the pipeline, and set the current object as the source of values..

<!--
############
class Chains:
    def __or__(self, trans):
        return trans.source(self)

    def __iter__(self):
        return self

    def source(self, src):
        self._source = src
        return self

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Chains:
    def __or__(self, trans):
        return trans.source(self)

    def __iter__(self):
        return self

    def source(self, src):
        self._source = src
        return self
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Source

Next, we define the source. That is, an object that is at the start of the
pipeline.

<!--
############
class S_(Chains):
    def __init__(self, nxt): self._source = iter(nxt)

    def __next__(self): return next(self._source)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class S_(Chains):
    def __init__(self, nxt): self._source = iter(nxt)

    def __next__(self): return next(self._source)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it as follows:

<!--
############
for i in S_([i for i in range(10)]):
    print(i)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in S_([i for i in range(10)]):
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Map
Next, we define maps.

<!--
############
class M_(Chains):
    def __init__(self, nxt): self._transform = nxt

    def __next__(self):
        return self._transform(next(self._source))

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class M_(Chains):
    def __init__(self, nxt): self._transform = nxt

    def __next__(self):
        return self._transform(next(self._source))
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We use it as follows.

<!--
############
for i in S_([i for i in range(10)]) | M_(lambda s: s + 10):
    print(i)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in S_([i for i in range(10)]) | M_(lambda s: s + 10):
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Filter

Finally, we implement filters as follows.

<!--
############
class F_(Chains):
    def __init__(self, nxt): self._filter = nxt

    def __next__(self):
        r = next(self._source)
        v = self._filter(r)
        while not v:
            r = next(self._source)
            v = self._filter(r)
        return r

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class F_(Chains):
    def __init__(self, nxt): self._filter = nxt

    def __next__(self):
        r = next(self._source)
        v = self._filter(r)
        while not v:
            r = next(self._source)
            v = self._filter(r)
        return r
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
This is used as follows.

<!--
############
for i in S_([i for i in range(10)]) | F_(lambda s: s > 5):
    print(i)


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in S_([i for i in range(10)]) | F_(lambda s: s &gt; 5):
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
## Pipe DSL

This is great, but can we do better? In particular, can we avoid having
to specify the constructors? One way to do that is through introspection. 
We redefine `Chains` as below. (The other classes are simply redefined so
that they inherit from the right `Chain` class)

<!--
############
class Chains:
    def __or__(self, src):
        s = None
        if isinstance(src, set) and callable(list(src)[0]):
            s = F_(list(src)[0])
        elif isinstance(src, list) and callable(src[0]):
            s = M_(src[0])
        else:
            s = S_(src)
        s._source = self
        return s

    def __iter__(self):
        return self

class S_(Chains):
    def __init__(self, nxt): self._source = iter(nxt)

    def __next__(self): return next(self._source)


class M_(Chains):
    def __init__(self, nxt): self._transform = nxt

    def __next__(self):
        return self._transform(next(self._source))


class F_(Chains):
    def __init__(self, nxt): self._filter = nxt

    def __next__(self):
        r = next(self._source)
        v = self._filter(r)
        while not v:
            r = next(self._source)
            v = self._filter(r)
        return r

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class Chains:
    def __or__(self, src):
        s = None
        if isinstance(src, set) and callable(list(src)[0]):
            s = F_(list(src)[0])
        elif isinstance(src, list) and callable(src[0]):
            s = M_(src[0])
        else:
            s = S_(src)
        s._source = self
        return s

    def __iter__(self):
        return self

class S_(Chains):
    def __init__(self, nxt): self._source = iter(nxt)

    def __next__(self): return next(self._source)


class M_(Chains):
    def __init__(self, nxt): self._transform = nxt

    def __next__(self):
        return self._transform(next(self._source))


class F_(Chains):
    def __init__(self, nxt): self._filter = nxt

    def __next__(self):
        r = next(self._source)
        v = self._filter(r)
        while not v:
            r = next(self._source)
            v = self._filter(r)
        return r
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
What we are essentially saying here is that, a `lambda` within a list (`[lambda s: ...]`)
is treated as a map, while within a set (`{lambda s:, ..}`) is treated as a
filter.

It is used a follows

<!--
############
for i in S_(range(10)) | [lambda s: s + 10] | {lambda s: s > 15} | [lambda s: s*10]:
    print(i)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
for i in S_(range(10)) | [lambda s: s + 10] | {lambda s: s &gt; 15} | [lambda s: s*10]:
    print(i)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
One final note here is that, the final iterator object that the for loop
iterates on here is of kind `M_` from the last object.
This is a consequence of the precedence of the operator `|`. That is, when
we have `a | b | c`, this is parenthesized as `(a | b) | c`, which is then
taken as `c(b(a()))`. This is also the reason why we have to wrap the
initial value in `S_`, but not any others (Because we override `__or__`
only the right hand object in an `|` operation needs to be the type `Chain`).
(We are also essentially pulling the values from previous pipe stages.)

If we want, we can make the last stage the required `Chain` type so that
we can write `a | b | c | Chain()`. However, for that, we need to override
the only right associative operator in python -- `**`. That is, we have to
write `a ** b ** c ** Chain()`, and have to override `__rpow__()`. We will
then get the object corresponding to `a`, and we will then have to *push*
the values to the later pipe stages.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
