---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: Template Haskell
review: done
---

Here are some notes on using Template Haskell. Note that the Template
Haskell API is still in flux and this may no longer be relevent if the
API changes.

Read the original research paper for
[preparation](http://research.microsoft.com/en-us/um/people/simonpj/papers/meta-haskell/meta-haskell.pdf).

I like to use a shortcut to easily load Template Haskell modules. In the
*~/.ghci* file, ensure that the following line exist.

~~~
:def . readFile
~~~

This will let you load often used ghci commands from a command file. Next,
create a file *th.cmd* with the following content

~~~
:m +Language.Haskell.TH
:m +Language.Haskell.TH.Syntax
:m +Language.Haskell.TH.Lib
~~~

The *th.cmd* can be loaded into your *ghci* session as below:

~~~
ghci> :. th.cmd
~~~

The notes are in literate Haskell format. You will need the following
initial imports at the beginning.

~~~
{-# LANGUAGE TemplateHaskell, LANGUAGE QuasiQuotes #-}
> module Main where
> import Language.Haskell.TH
> import Language.Haskell.TH.Syntax
> import Language.Haskell.TH.Lib

> -- import Defs -- to be enabled
> -- import Str  -- later
~~~

#### Syntax

A template haskell expression can be executed by marking it with `$(...)` that
is, if you have an function `myfn`, then `$myfn` would cause it to be called
at compile time with no arguments. and $(myfn a) would cause it to be called
with argument a, with the result added to AST before being compiled.

The template haskell expression is the AST of haskell expression to
be spliced in. For example, the following expression

~~~
$(return $ LitE $ IntegerL 1 :: Q Exp)
~~~

should return `1`.

The `$(...)` syntax expects a `Q` monad. Hence we wrapped the `Q Exp` in a
`return` to make it palatable to the monad.

Sicne it is tedious to construct the haskell AST by hand, Template haskell
provides the following shortcuts.

*Patterns* are constructed with, `[p| ... |]` with type `Q Pat`. For example:

~~~
runQ [p| x |]
~~~

Global declarations use `[d| ... |]`, and has type `Q [Dec]`. For example:

~~~
runQ [d| x = 100 |]
~~~

Types are constructed with `[t| ... |]`, with `Q Type`. For example:

~~~
runQ [t| Int |]
~~~

To extract the AST of haskell expressions, we use `[| ... |]`, with type `Q Exp`

~~~
runQ [| 100 |]
~~~

#### The cancellation requirement

Remember our original expression? we hand coded the values directly for
`$(...)`. That expression is equivalent to:

~~~
$([|1|])
~~~

That is, `$([?|..|])` and `[?|$(..)|]` are strictly cancellable as per the
meta-haskell paper.

*(The paper uses no parenthesis for cancellation. That is `$[|1|]` is a valid expression as far
as the meta-haskell paper is concerned. However ghc7 requires the parenthesis for it to work.)*

For *ghc7*, the following cancellation works.

~~~
runQ [| $( return $ LitE $ IntegerL 1 ) |]
~~~

#### Bugs?

The patterns `[p| ... |]` do not play nice with splicing. To illustrate, follow
this deconstruction.

~~~
runQ [| let x = 100 in x |]
runQ [| let x = $(return (LitE (IntegerL 100))) in x |]
runQ [| let x = $(return (LitE (IntegerL 100))) in $(return (VarE (mkName "x"))) |]
runQ [| let $(return (VarP (mkName "x"))) = $(return (LitE (IntegerL 100))) in $(return (VarE (mkName "x"))) |]
~~~

Everything except the last one works. I stumbled on it for a long time before
asking in the freenode#haskell and according to someone there, patterns do not
work well with splicing.
Apparently there is a [ticket](http://hackage.haskell.org/trac/ghc/ticket/1476)
which is patched in GHC Head.

#### Aside

The reason for the existence of `Q monad` is to avoid variable capturing.
This is ensured by a construct `newName` which creates a new name to be used
within the template body. On the other hand, we have a capturing variable
construct `mkName` which is a pure function.

We can also replace mkName "x" with 'x
<!--'-->

#### How do we construct these things?

Say we want a way to extract the first value out of any tuple, the expression
we want to create is something like

~~~
$(fst n) n-tuple
~~~

That is, we should be able to evaluate it as follows:

~~~
$(fst 3) (1,2,3)
= 3
~~~

The expression we want to construct looks like:

~~~
let fn (a,b,c) = a in fn
~~~

That is, we should be able to use the expression we make in place
of the below expression in parenthesis.

~~~
ghci> (let fn (a,b,c) = a in fn) (1,2,3)
= 1
~~~

We start by examining how tuples are made:

~~~
runQ [| (1,2,3) |]
= TupE [LitE (IntegerL 1),LitE (IntegerL 2),LitE (IntegerL 3)]
~~~

This suggests that, a tuple is an array of literals wrapped with constructor
`LitE` again wrapped in `TupE`

How about the expression template we demonstrated previously deconstruct?

~~~
runQ [| let fn (a,_,_) = a in fn |]
= LetE [FunD fn_0 [Clause [TupP [VarP a_1,WildP,WildP]] (NormalB (VarE a_1)) []]] (VarE fn_0)
~~~

So we need to construct our `TupP` array.
*(We use a lambda here so as to avoid the staging restriction.)*

~~~
> x = $((\n -> let a = mkName "a" ;
> f = mkName "fn" in
> return (LetE [FunD f [Clause [TupP (VarP a : take (n-1) (repeat WildP))] (NormalB (VarE a)) []]] (VarE f)))
> 3) (10,20,30)
~~~

If we use a staging module, `Defs.lhs`

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

We can do similar things with types.

~~~
runQ [t| Int -> Int |]
~~~

#### Comparison with Scheme macros.

* Lazy evaluation removes some of the requirements for lisp-macro expressions,
  but is somewhat restricted where it can be used.
* Template Haskell has no dynamic metaprogramming (eval) possibility
* No possibility of syntax-case like DSL for TH. The errors are caught
  deep inside the template code. (While type system catches a portion of
  the errors at compile time, it does not do that for all.)
* TH support for patterns and types is still evolving.
* quasiquoting is just sugar for TH

#### Reification

~~~
reify ''Int
~~~

This gets you `Q Info`

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


