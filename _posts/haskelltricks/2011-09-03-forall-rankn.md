---
layout: post
categories : [post]
tagline: "."
tags : [haskelltricks blog haskell language]
e: Using forall - RankN Types
review: done
---

Notes on using *forall* construct in Haskell.

Say you have a couple of lists, the first one being a list of integers and the second a list of booleans

~~~
> li = [1,2,3,4]
> lb = [True,False,True,True]
> mypair = (li,lb)
~~~

Since they are lists, we would like to create a function that takes such a pair and apply a supplied function on lists to them.

~~~
> myfn (a,b) fn = (fn a, fn b)
~~~

If you try invoking this function with any list functions, you will get an error

~~~
ghci> myfn mypair reverse
Couldn't match expected type `Integer' with actual type `Bool'
Expected type: ([Integer], [Integer])
Actual type: ([Integer], [Bool])
~~~

The type of the function gives us a clue

~~~
ghci> :t myfn
myfn :: (t, t) -> (t -> t1) -> (t1, t1)
~~~

That is, the pair passed in is expected to contain elements of same type, and produces another pair with elements of same type.  This is because Haskell expects the function myfn to have a strict signature for both input and output.

The way around it is to use RankNTypes and forall.

~~~
> {-# LANGUAGE RankNTypes #-}
> li = [1,2,3,4]
> lb = [True,False,True,True]
> mypair = (li,lb)
> myfn :: ([t],[t']) -> (forall a. [a] -> [a]) -> ([t],[t'])
> myfn (a,b) fn = (fn a, fn b)
~~~

Now our function should work as expected.

~~~
ghci> myfn mypair reverse
([4,3,2,1],[True,True,False,True])
~~~

They are useful for much more than this. It is especially useful in data type declarations, but you need *ExistentialQuantification* for that. The idea is to have a heterogeneous list of elements along with functions that transforms them into a homogeneous element type.

~~~
> {-#  LANGUAGE ExistentialQuantification #-}
> data MyX = forall a. X a String (a -> Int)

> instance Show MyX where
> show (X a name fn) = name ++ (show (fn a))
~~~

You can use it this way

~~~
ghci> [X 10 "Int" $ id, X True "Bool" $ \x -> if x then 1 else 0 ]
[Int10,Bool1]
~~~

So this essentially gets us heterogeneous lists.

