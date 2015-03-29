---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: GHCI tricks
reviewe: done
---

If you are using a variant of Unix with Haskell and GHC, here is a nifty trick
you can use with the ghci repl to make editing your source files relatively
painless.

First, notice that *ghci* allows us to define macros in the repl.

~~~
ghci > :?
  ...
   :def <cmd> <expr>           define command :<cmd> (later defined command has
                               precedence, ::<cmd> is always a builtin command)
  ...
~~~

This lets us define our own shortcut commands that can be invoked similar to
the *ghci* builtins using *Haskell*.

These should go in the *~/.ghci* file, and ensures that if you 
are in a directory that contains Main.hs typing *:x* will open *Main.hs* in the
editor of your choice.

~~~
:def x (\_ -> return ":e Main.hs \n :load Main.hs")
:def u (\_ -> return ":e UnitTest.hs \n :load UnitTest.hs")
~~~

To use it, the incantation is 

~~~
ghci > :x
~~~

Another trick is to have separate *.ghci* per project directory, and
commandeer another letter for editing specific files. Say you are in a
directory "mysyntax" which contains Syntax.hs. Add a new *.ghci* to the
*mysyntax* directory with:

~~~
:def v (\_ -> return ":e Syntax.hs \n :load Syntax.hs")
~~~

This gets you a quick project specific shortcut to files from ghci prompt.

