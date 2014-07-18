---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: Template Haskell
---

[Preparation](http://research.microsoft.com/en-us/um/people/simonpj/papers/meta-haskell/meta-haskell.pdf)

You need the following code in the `.ghci` of your directory

~~~
:m +Language.Haskell.TH
:m +Language.Haskell.TH.Syntax
:m +Language.Haskell.TH.Lib
~~~

Your source file

~~~
{-# LANGUAGE TemplateHaskell, LANGUAGE QuasiQuotes #-}
> module Main where
> import Language.Haskell.TH
> import Language.Haskell.TH.Syntax
> import Language.Haskell.TH.Lib

> import Defs
> import Str
~~~

#### Syntax

A template haskell expression can be executed by marking it with $(...)
that is, if you have an function myfn, then $myfn would cause it to be called at compile time with no arguments. and $(myfn a) would cause it to be called with argument a, and the result is added to the AST before being compiled.

The template haskell expression is nothing but AST of haskell expression to be spliced in. For example, try
this.

~~~
$(return $ LitE $ IntegerL 1 :: Q Exp)
~~~

This should return 1
The `$(...)` syntax expects a `Q` monad. This is the reason for return.

It is somewhat hard to construct the haskell AST by hand, so Template haskell provides four shortcuts.

For patterns, you can use `[p| ... |]` to construct values. It has type `Q Pat`

~~~
runQ [p| x |]
~~~

For global declarations, use `[d| ... |]`, it has type `Q [Dec]`

~~~
runQ [d| x = 100 |]
~~~

For types use `[t| ... |]`, with `Q Type`

~~~
runQ [t| Int |]
~~~

And to extract the AST of haskell expressions, we can use `[| ... |]` It has a type `Q Exp`

~~~
runQ [| 100 |]
~~~

#### Cancellation

Now, remember our original expression, where we hand coded the values directly into the `$(...)`.
This becomes easier for us now,

~~~
$([|1|])
~~~

Infact it is a requirement of the above quoted paper that `$([?|..|])` and `[?|$(..)|]` be strictly cancellable.

(The paper uses no parenthesis for cancellation too, that is `$[|1|]` is a valid expression as far
as the meta-haskell paper is concerned. However ghc7 requires the parenthesis for it to work.)

So the following cancellation also works.


~~~
runQ [| $( return $ LitE $ IntegerL 1 ) |]
~~~

The patterns `[p| ... |]` do not play nice with splicing. To illustrate, follow this deconstruction.

~~~
runQ [| let x = 100 in x |]
runQ [| let x = $(return (LitE (IntegerL 100))) in x |]
runQ [| let x = $(return (LitE (IntegerL 100))) in $(return (VarE (mkName "x"))) |]
runQ [| let $(return (VarP (mkName "x"))) = $(return (LitE (IntegerL 100))) in $(return (VarE (mkName "x"))) |]
~~~

Every thing except the last one works. I stumbled on it for a long time before asking in the freenode#haskell
and according to some one there, patterns do not work well with splicing
Apparently there is a ticket on that http://hackage.haskell.org/trac/ghc/ticket/1476 which is patched in GHC Head

A small aside. The reason for the existence of Q monad is to make sure that capturing of variables do not happen.
This is ensured by a construct newName which creates a new name to be used within the template body. On the other hand
we have a capturing variable construct mkName which is a pure function. Also, we can replace mkName "x" with 'x

Things get interesting. Say we want a way to extract the first value out of any tuple, the expression
we want to create is something like

~~~
$(fst n) n-tuple
~~~

i.e

~~~
$(fst 3) (1,2,3)
~~~

The expression we want to construct looks like

~~~
let fn (a,b,c) = a in fn
~~~

We start by running the below expression to determine how the tuples are made.

~~~
runQ [| (1,2,3) |]
= TupE [LitE (IntegerL 1),LitE (IntegerL 2),LitE (IntegerL 3)]
~~~

So a tuple is nothing but an array of literals wrapped with constructor LitE again wrapped in TupE

How about the function we have?

~~~
runQ [| let fn (a,_,_) = a in fn |]
= LetE [FunD fn_0 [Clause [TupP [VarP a_1,WildP,WildP]] (NormalB (VarE a_1)) []]] (VarE fn_0)
~~~

So we need to construct our VarP arrays.
We use a lambda here so that we don't have to use a staging module.

~~~
> x = $((\n -> let a = mkName "a" ;
> f = mkName "fn" in
> return (LetE [FunD f [Clause [TupP (VarP a : take (n-1) (repeat WildP))] (NormalB (VarE a)) []]] (VarE f)))
> 3) (10,20,30)
~~~

Here is the same thing defined in our staging module Defs.lhs


~~~
module Defs where
import Language.Haskell.TH
import Language.Haskell.TH.Syntax
import Language.Haskell.TH.Lib
nfst n = let a = mkName "a" ; f = mkName "fn" in
return (LetE [FunD f [Clause [TupP (VarP a : take (n-1) (repeat WildP))] (NormalB (VarE a)) []]] (VarE f))
~~~

~~~
$(nfst 3) (10,20,30)
~~~

Can you guess what would happen if we execute

~~~
$(nfst 1) (10,20,30)
~~~

Same stuff is possible with types too.

~~~
runQ [t| Int -> Int |]
~~~

#### Comparison with scheme macros.


~~~
> x' = 10
> y' = 20

> z' = $(add x'' y'')
~~~

~~~
add x y = [| x + y |]
~~~

GHC stage restriction: `x'' is used in a top-level splice or annotation

But this works for scheme

~~~
(define-macro (add x y) `(+ ,x ,y))
~~~

... another file.

~~~
(add 3 4)
~~~

The stage restriction applies not only to the definitions but also to
arguments.

A larger macro from scheme world.

~~~
(define-macro (expand-power n x)
(if (eq? n 0) `1
`(* ,x ,(expand-power (- n 1) x))))

(define-macro (mk-power n) `(lambda (x) ,(expand-power n 'x)))
~~~

~~~
> expandPower :: Num a => a -> Q Exp -> Q Exp
> expandPower n x = case n == 0 of
> True -> [| 1 |]
> False -> [| $(x) * $(expandPower (n - 1) x) |]

> mkPower n = [| \x -> $(expandPower n [|x|]) |]

$(mkPower 4) 2
~~~

Some evaluation

* Lazy evaluation removes some requirement for macros
* Thaskell has no dynamic metaprogramming (eval) possibility
* No syntax-case like DSL for TH. The errors are caught deep inside the template code. (While type system catches a portion of the errors at compile time, it does not do that for all.)
* Thaskell support for patterns and types is still evolving.
* quasiquoting is just sugar for TH


#### Reification

~~~
reify ''Int
~~~

This gets you Q Info

~~~
$(stringE . show =<< reify ''Int)
~~~

~~~
> myvar = 5 :: Int
~~~

~~~
$(stringE . show =<< reify 'myvar)
$(stringE . show =<< reify 'even)
$(stringE . show =<< reify ''String)
~~~


#### Now for quasiquotes.

The first example is on a simple multiline string reader.

~~~
module Str where
import Language.Haskell.TH
import Language.Haskell.TH.Quote
qq = QuasiQuoter { quoteExp = (litE . StringL) }
~~~

Now, we can use qq to add multiline statements.

~~~
> multi = [qq|
> A
> B
> C
> |]
~~~

same as $(quoteExp qq " a b c d ")


