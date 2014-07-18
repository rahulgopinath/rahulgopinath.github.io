---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: GHCI tricks
---

Here is a nifty trick you can use with ghci. (Assuming that you are using some variant of Unix)

put the below in your ~/.ghci file

~~~
:def x (\_ -> return ":e Main.hs \n :load Main.hs")
:def u (\_ -> return ":e UnitTest.hs \n :load UnitTest.hs")
~~~

These rules will ensure that if you are in a directory that contains Main.hs typing : x will open up Main.hs in the editor of your choice.
e.g

~~~
ghci Prelude> : x
~~~

I also use another trick, where I have a separate .ghci per project directory where another letter is redefined. Say you are in a directory "syntax" which contains Syntax.hs add a new .ghci to the syntax directory that contains

~~~
:def v (\_ -> return ":e Syntax.hs \n :load Syntax.hs")
~~~

This gives you a quick project specific shortcut to files from ghci prompt.
