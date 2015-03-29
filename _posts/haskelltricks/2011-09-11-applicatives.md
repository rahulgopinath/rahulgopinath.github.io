---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: Applicatives
---

Notes on using applicatives.

Applicative Functors are a solution that is half way between a functor and a full-blown monad. It has more structure than a functor but less than that of a monad. It is especially useful if you have a some function that needs to be applied to a series of values in a monad. e.g

Say you have

~~~
> f x y z = x * y * z
> (a,b,c) = (Just 1,Just 2,Just 3)
~~~

Applying f to a b c is simple using applicative

~~~
> f' = f <$> a <*> b <*> c
ghci> f'
Just 6
~~~

Notice the *<$>* combinator between the function and the first monadic value.

Another example

~~~
> f x y = [x,y]
> (a,b) = ([1,10,100], [2,20,200])
> y = f <$> a <*> b
~~~

~~~
ghci> y
[[1,2],[1,20],[1,200],[10,2],[10,20],[10,200],[100,2],[100,20],[100,200]]
~~~

