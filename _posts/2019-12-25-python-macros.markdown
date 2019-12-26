---
published: true
title: Automatically Preprocessing Python Files with Codecs
layout: post
comments: true
tags: vm
categories: post
---

Python is one of the nicer languages out there. It's syntax is clean, 
and its philosophy (`import this`) is refreshing. Unfortunately, perhaps due to compatibility
reasons, Python has accumulated many syntactical warts[1]. The question is what can one do about it?

One of the options available is to write a preprocessor stage before the interpreter sees the source.
[Macropy](https://github.com/lihaoyi/macropy) is a project that seeks to bring syntactic macros
to Python. That is, you can use *Macropy* to modify the source code at compile time. Unfortunately,
using *Macropy* is a little cumbersome. Macropy uses
[import hooks](https://macropy3.readthedocs.io/en/latest/overview.html) for rewriting the AST on the
fly, which means that when you invoke the intrpreter directly on the source code, Macropy does not
get a chance to rewrite the source code.

One may use decorators to modify the AST of functions. However, the issue there is that, your source
has to pass through the Python parser first. Sometimes, you want a feature that is syntactically
different (e.g. implementing a `switch` statement) or a `with` *expression* or a multiline *lambda*.

So, is there a better way?

Turns out, there is!. Python [allows](https://www.python.org/dev/peps/pep-0263/) one to specify the *encoding* of a file as follows:

```python
#!/usr/bin/env python
# coding: UTF-8
```
The interesting part here is that, the decoder `UTF-8` is simply a Python library flie typically found in the encodings directory, which
can be found as follows:

```python
>>> import encodings, os
>>> print(os.path.dirname(encodings.__file__))
```

There are a number of coding files there, of which `ascii.py` is particularly simple. Let us see if we can modify the
`ascii` encoding to support `define` as an alternative to `def`.

The first step is to copy the `ascii.py` file to `xascii.py`, and try out with an example.
```python
>>> base = os.path.dirname(encodings.__file__) + '/' 
>>> with open(base + 'ascii.py') as f: src = f.read()
>>> with open(base + 'xascii.py', 'w+') as f: print(src.replace("'ascii'", "'xascii'"), file=f)
```

Next, see if we succeeded:

```python
#!/usr/bin/env python
# coding: xascii

def hello():
    print('hello')
hello()
```

Let us test it:

```shell
$ python3 hello.py
hello
```

What if we go a bit more complex? We want to let functions be defined using `define ` along with `def `.
Here are the changes:

```diff
--- 3.7/lib/python3.7/encodings/ascii.py	2019-10-14 16:08:55.000000000 -0700
+++ 3.7/lib/python3.7/encodings/xascii.py	2019-12-25 08:31:04.000000000 -0800
@@ -23,7 +23,8 @@

 class IncrementalDecoder(codecs.IncrementalDecoder):
     def decode(self, input, final=False):
-        return codecs.ascii_decode(input, self.errors)[0]
+        res = codecs.ascii_decode(input, self.errors)[0]
+        return res.replace('define ', 'def ')

 class StreamWriter(Codec,codecs.StreamWriter):
     pass
@@ -40,7 +41,7 @@

 def getregentry():
     return codecs.CodecInfo(
-        name='ascii',
+        name='xascii',
         encode=Codec.encode,
         decode=Codec.decode,
         incrementalencoder=IncrementalEncoder,
```

Here is how one would use it:

```python
#!/usr/bin/env python
# coding: xascii

define hello():
    print('hello')
hello()
```

```shell
$ python3 hello.py
hello
```

## A DSL for context free grammars.

Here is what I want to do now. Given the below definition (which will not be parsed by the standard Python), I want to make Python read it
and print the expression grammar data structure.

```python
#!/usr/bin/env python
# coding: cfg

# This is expr_grammar.py

grammar expression_grammar:
    start   = expr
    expr    = (term + '+' + expr
            |  term + '-' + expr)
    term    = (factor + '*' + term
            |  factor + '/' + term
            |  factor)
    factor  = ('+' + factor
            |  '-' + factor
            |  '(' + expr + ')'
            |  integer + '.' + integer
            |  integer)
    integer = (digit + integer
            |  digit)
    digit   = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'

if __name__ == '__main__':
    print(expression_grammar)
```

We will do the editing in two steps. First, we will replace `grammar` by `def` which will make the Python parser parse it,
and then, we will interpret the AST ourselves to return a data structure instead.

### Imports

```python
#!/usr/bin/env python
import codecs
import re
import ast
```

### Registering our codec

As we saw before, the main action happens in `Codec.decode`. We first make the source parsable, parse it, and then interpret the
AST.

```python
class Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        return (input.encode('utf8'), len(input))

    def decode(self, input, errors='strict'):
        input_string = codecs.decode(input, 'utf8')
        parsable = make_it_parsable(input_string)
        g = define_ex_grammars(parsable)
        return (g, len(input))

class IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return Codec().encode(input)

class IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return Codec().decode(input)[0]

class StreamReader(Codec, codecs.StreamReader): pass
class StreamWriter(Codec, codecs.StreamWriter): pass

def getregentry():
    return codecs.CodecInfo(
        name='cfg',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
```

### Making it parsable

To make it parsable, we simply have to repalce `grammar ` with `def `

```python
def make_it_parsable(source):
    return '\n'.join([gdef(s) for s in source.split('\n')])

def gdef(line):
    if line.startswith('grammar '):
        words = line.split(' ')
        if not words[1].endswith(':'):
            return line
        name = words[1][0:-1]
        return 'def %s():' % name
    return line
```

### The grammar parser


```python
def define_name(o):
    return o.id if isinstance(o, ast.Name) else o.s

def get_alternatives(op, to_expr=lambda o: o.s):
    if isinstance(op, ast.BinOp) and isinstance(op.op, ast.BitOr):
        return get_alternatives(op.left, to_expr) + [to_expr(op.right)]
    return [to_expr(op)]

def funct_parser(tree, to_expr=lambda o: o.s):
    return {assign.targets[0].id: get_alternatives(assign.value, to_expr) for assign in tree.body}

def define_expr(op):
    if isinstance(op, ast.BinOp) and isinstance(op.op, ast.Add):
        return (*define_expr(op.left), define_name(op.right))
    return (define_name(op),)

 def define_grammar(source, to_expr=lambda o: o.s):
    src_lines = source.split('\n')
    module = ast.parse('\n'.join(src_lines))
    last_line = 0
    lines = []
    # of course this is a hack. We are simply looking for function
    # definitions, and leaving everything else as they are.
    for e in module.body:
        if last_line is not None:
            my_lines = '\n'.join(src_lines[last_line:e.lineno-1])
            lines.append(my_lines)

        if isinstance(e, ast.FunctionDef):
            fname = e.name
            grammar = funct_parser(e, to_expr)
            sline = "%s = %s" % (fname, grammar)
            lines.append(sline)
            last_line = None
        else:
            v = e.lineno
            last_line = e.lineno - 1

    my_lines = '\n'.join(src_lines[last_line:])
    lines.append(my_lines)
    return '\n'.join(lines)

def define_ex_grammars(fn):
    return define_grammar(fn, define_expr)
 ```
 
 Using it:

```shell
$ python expr_grammar.py
{'start': [('expr',)], 'expr': [('term', '+', 'expr'), ('term', '-', 'expr')],
 'term': [('factor', '*', 'term'), ('factor', '/', 'term'), ('factor',)],
 'factor': [('+', 'factor'), ('-', 'factor'), ('(', 'expr', ')'), ('integer', '.', 'integer'), ('integer',)],
 'integer': [('digit', 'integer'), ('digit',)], 
 'digit': [('0',), ('1',), ('2',), ('3',), ('4',), ('5',), ('6',), ('7',), ('8',), ('9',)]
}
```

Can we use it with imports too

```python
import expr_grammar
print(expr_grammar.expression_grammar)
```


### Limitations

The biggest limitation is that, one needs to move the encoding definition to the `system` encodings directory,
which means  that it may require root privileges if you are using the system Python. If you are unable to do it,
you will need a runner that will import your code (as in the last example). We need a bit more machinery to make
that work. See [this project](https://pypi.org/project/emoji-encoding/) for a simple example of how to do it.

**Fair warning**: I had fun writing this post, however, I do not recommend using this technique in production. That way lies madness. Remember, *[With great power comes great responsibility](https://en.wikipedia.org/wiki/With_great_power_comes_great_responsibility)*.

[1] See [this project](https://github.com/satwikkansal/wtfpython/blob/master/README.md) for examples of Python warts. I particularly dislike the [mutable default arguments](https://github.com/satwikkansal/wtfpython/blob/master/README.md#-beware-of-default-mutable-arguments).
