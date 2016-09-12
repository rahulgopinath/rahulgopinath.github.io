---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: A thin slice of Haskell
title: A thin slice of Haskell
---


These are notes on functional programming language Haskell some what tidied up to be presentable. I had made these as I was studying the language. (done using [Hugs](http://www.haskell.org/hugs/). )

Haskell is one of the better known functional languages in use. It is purely functional and follows the lambda calculus closely. While it is not homoiconic, it is one of those languages that will change your perspective on programming. 

```
Hugs> :version
-- Hugs Version September 2006
```


##### Some conventions

The interactive prompt of Hugs is assumed to be '|', the output from Hugs is shown with a leading '=', :e switches to edit mode (as it does in Hugs) and :t shows the type of the expressions.

The markers '<[ and ]>' denote the source code.

##### Arithmetic and Lists

```
> 2 + 1
=3
> length [1,2,3]
=3
> head [1,2,3]
=1
```

##### Lists creation.

The arithmetic progression lists are recognized based on the number of elements you provide and the difference between the first and second element. 

```
> take 3 [1..10]
=[1,2,3]
> take 3 [1,4..20]
=[1,4,7]
> take 3 [10, 9.. 1]
=[10,9,8]
> take 3 ['a'..'z']
=['a','b','c']
```

The lists are lazy (values are computed only when needed), which makes it possible to have infinite sequences.

```
> take 3 [2..]
=[2,3,4]
> take 3 [1,3..]
=[1,3,5]
```

Tuples can be used like structures in other languages (mostly).

```
> (2,3)
=(2,3)
> ('a',3,"My name")
=('a',3,"My name")
```

##### Editing

use :e to switch between editing modes and :l to load any file (when you exit the editor after :e, the current module is reloaded automatically). The :e will work only if you have the 'EDITOR' variable set.

```
> :e My.hs
```

My.hs

```
module My where
len [] = 1
len (x:xs) = 1 + (len xs)

-- the obligatory quicksort.

quicksort [] = []
quicksort (s:xs) = quicksort [x|x <- xs,x < s] ++ [s] ++ quicksort [x|x <- xs,x >= s]

```

```
> :l My.hs
```

notes:

* Module definition written as -- module <Name> where <definitions>
* The nil list can be written as [] and normal lists can be split as (x:xs)
* You can specify multiple definitions with different input patterns. The above should be read as, 
* len is defined as <...> when the input is \[\] (an empty list)
* len is defined as <...> when the input is a list (the empty list is already matched in the previous def, so we get only the non empty ones in the second.)

 

##### A simple definition.

```
quad a b c = (negb + discr) / (2 \* a)
        where
            negb = -(b)
            discr = sqrt ((b \* b) - 4 \* a \* c)

```

```
> quad 1 30 2
=-0.0688
```

 

Notes:

* using where to define local definitions.
* parens -- () -- are used for grouping and tuples, not for function argument delimits. Also function arguments are delimited by whitespace.

##### Guards.

```
fx x y  | y > z = 1
          | y == z = 0
          | y < z = -1
        where z = x \* x
```

```
>  fx 1 2
=1
> fx 4 1
=-1
```

Notes:

* The '|' are called pattern guards they can be used to provide different implementations for functions based on the value of expressions. They are like the input patterns but are defined with in the function itself and may involve computation.

some examples.

```
max x y
    | x > y = x
    | otherwise = y

fact n | n == 0 = 1
         | otherwise = n \* fact (n-1)
```

Using case instead of guards or input patterns.

```
len lst = case lst of
        [] -> 0
        (x:xs) -> 1 + (len xs)
```

Case with computable expressions.

```
abs x = case x of
        x | x >= 0 -> x
          | x < 0 -> -x
```

Destructuring a list using bind pattern

```
(x:y:z:rest) = [1..]
```

```
> x
=1
> y
=2
```


##### List comprehensions

 

 Generators

```
> [1..3]
=[1,2,3]

> [(x,y) | x <- [1..3], y <- [3,2..1]]
=[(1,3),(1,2),(1,1),(2,3),(2,2),(2,1),(3,3),(3,2),(3,1)]

> [(x,y) | x <- [1..3], y<- "ab"]
=[(1,'a'),(1,'b'),(2,'a'),(2,'b'),(3,'a'),(3,'b')]

> [x\*x | x <- [1..3]]
=[1,4,9]
```


Filters 

   Filters are created by following a generator with a filtering function

```
> [ x | x <- [1..4], even x]
=[2,4]

> [ (x,y) | x <- [1..4], even x, y <- "ab" ]
=[(2,'a'),(2,'b'),(4,'a'),(4,'b')]
```

 

map and filter using list comprehensions.

```
map f  xs = [ f x | x <- xs ]
filter p xs = [ x | x <- xs, p x ]
```


##### Using Let


```
sum ys =
  let sumlocal [] total = total
      sumlocal (x:xs) total = sumlocal xs (total+x)
  in sumlocal ys 0
```


notes:

- let allows creation of  inner functions.
- the syntax is let <...> in <expression> 



```
roots a b c =
    let det = sqrt (b\*b - 4\*a\*c)
        a2 = 2\*a
    in ((-b + det) / a2,
         (-b - det) / a2)
```

```
> roots 1 30 2
(-0.0668,-29.9331)
```


Unwrapping tuples


```
unzip ((a, b):rest) =
  let (as, bs) = unzip rest
  in (a:as, b:bs)
```



Tuples again


```
distance (x1,y1) (x2,y2) = sqrt (dx\^2 + dy\^2)
    where
        dx = x2 - x1
        dy = y2 - y1
```


```
> distance (1,2) (3,4)
=2.828
```

```
:t distance
=distance :: Floating a => (a,a) -> (a,a) -> a
```

notes:

- The tuples are an aggregate datatype composed by enclosing the values in parens-- ()

- we pass two tuples (1,2) and (3,4) to distance function. 

- As you can see in :t distance, the type of tuple is (a,a)

##### Monads

Monads are a way to encode sequential (or state) information in the programs (There are many other ways of looking at the monads, but this seems to be the simplest.) 

IO monad.


```
main = do
    putStr "hello"
```


```
> main
=hello
```


```
main = do
    putStr "Name? "
    x <- getLine
    putStr . concat $ ["Hello[", x, "]"]
```


notes:

- The do notation with the funny <- that looks like assignment is actually just syntax sugar for a higher operation called bind. I will not be treating that part here.
- be careful of the indentation. the first statement after do determines the indentation for the other statements.



```
readNum = do
    x <- getLine
```


```
:l Me.hs
=ERROR "Me.hs":9 - Last generator in do {...} must be an expression
```


```
readNum = do
    x <- getLine
    return (x)
```


notes:

- Common error: [ERROR "Me.hs":9 - Last generator in do {...} must be an expression solution: add a return () at the end.]
- The error is because we need to return the type of IO rather than x. (more detailed explanation below.)

- The do notation with the funny <- that looks like assignment is actually just syntax sugar for a higher operation called bind. I will not be treating that part here.
- If you have nothing to return just a return () will do.

The function readNum that you have just defined can not be used like 
a function that 'returns' a number

ie:

```
> :t readNum
=readNum :: IO [Char]
```

The type of function is still IO [Char]
to convert it to an integer, we need to tell hugs its signature.

```
readNum :: IO Integer
readNum = do
    x <- getLine
    return (read x)
```

```
> :t readNum
=readNum :: IO Integer
```

trying to use it as a function that 'returns' a number fails because the function is no longer pure.


```
mySqr = readNum \* 2

readNum :: IO Integer
readNum = do
    x <- getLine
    return (read x)
```


```
:l My.hs
=ERROR "Me.hs":1 - Unresolved top-level overloading
*** Binding             : mySqr
*** Outstanding context : Num (IO Integer)
```

For us to make use of an impure function we have to go back to using a monad where ever we need to the result of this function.

ie:


```
mySqr = do
    x <- readNum
    print (x \* 2)

readNum :: IO Integer
readNum = do
    putStr "Num? "
    x <- getLine
    return (read x)
```


```
> mySqr
>Num? 12
=24
```

Let us check the type of the function.

```
:t mySqr
=mySqr :: IO ()
```


##### Explaining return.

When using monads, the last line should have the same type as the function itself. The return is a statement that is guaranteed to have the same type.

that is, from a 'c' approach, the below

```
getName :: IO String
getName = do
    name <- getLine
    return name
```

should be read as


```
#define Return(x) return to_IO_String(x)

(IO_String) getName() {
    name = getLine()
    Return name
}
```


ie, what is returned is not 'String' but 'IO String'. This is the reason why we are not able to directly use the output of this function in another function that expects a string, but rather use <- to extract the value out of this.

##### Trouble shooting


When in doubt, insert braces and ';' to be sure that your indentation is correct.
braces can be used after the keywords 'where, let, do, of'


```
len l = case l of {
    [] -> 0;
    (x:xs) -> 1 + (len xs);
}
```


and be sure to delete them after your scope is clear to you.

The return does not work as in the other languages either. The only place that a return should be used is as the last statement of a sequence of do actions. 

ie:

```
checkRet = do
            putStr "Checking return"
            return ()
            putStr " here.."
```


```
> checkRet
=Checking return here..
```

As you can see, return() does not return from the action being executed by do. It is just a short cut to provide a value of the correct return type for a do.


##### Updatable variables (well not actually)


```
import Data.IORef

myRef = do varA <- newIORef 0
           a0 <- readIORef varA
           writeIORef varA 1
           a1 <- readIORef varA
           print (a0, a1)
```

```
> myRef
=(0,1)
```

the newIORef creates and initializes the variable (reference). readIORef  fetches the value, and writeIORef updates it.


##### DataTypes

Haskell is strongly typed and has static type system. Generally Haskell infers the type of your expressions (There will be exactly one type for any given expression.). If that fails (like in some of the examples above) You may have to provide explicit type information.

Haskell provides Integer, Int, Float, Double, Bool, and Char as the most basic building blocks. We can create more complex datatypes on the fly using tuples.

tuples can be named using the 'type' syntax.


```
type Vert = (Float, Float)
type Line = [Vert]

dist :: Line -> Float
dist [(x1,y1), (x2,y2)] = sqrt ((xd \* xd) + (yd \* yd))
    where
        xd = x2-x1
        yd = y2-y1
```



You can also build custom datatypes using the 'data' syntax.


```
data Rainbow = Violet | Indigo | Blue | Gree | Yellow | Orange | Red
-- define our show function too.
instance Show Rainbow where
    show Red = ':red'
    show Blue = ':blue'
```

```
> Red
=:red
```

The show function allows you to define the string representation of any custom datatype that you use. I will explain the 'instance' syntax later. but this is how you can define the show function.


##### Using Fields in data

when using the field name syntax, the selector functions are already defined.

```
data Point = Pt {pointx :: Float, pointy :: Float}
-- it helps to define a show always.
instance Show Point where
     show p = show [(pointx p), (pointy p)]

absPoint                :: Point -> Float
absPoint p              =  sqrt (pointx p \* pointx p +
                                 pointy p \* pointy p)

--using pattern matching with field names.
absPoint1 (Pt {pointx = x, pointy = y}) = sqrt (x\*x + y\*y)

-- updating a value using field names.
updatePt p = p {pointx=3}
```


```
> absPoint (Pt {pointx=1, pointy=2})
=2.236068
> absPoint (Pt 1 2)
=2.236068
:t pointx
=pointx :: Point -> Float
> updatePt (Pt 1 2)
=[3.0,2.0]
```

beware that the field names have the same scope as that of the type, so the same field name can not be used in another type in the same scope.
ie the following produces an error.


```
data Point3 = Pt3 {pointx :: Float, pointy :: Float, pointz :: Float}
```

```
:l 
=Error - Multiple declarations for selector "pointx"
```


##### polymorphic data


```
data MyPoint p = Mpt p p

xmpt :: MyPoint a -> a
xmpt (Mpt x y) = x
ympt :: MyPoint a -> a
ympt (Mpt x y) = x

-- we get an error 'Can not justify constraints' if we avoid ' => Show '
instance Show a => Show (MyPoint a) where
    show (Mpt a b) = show [a, b]

]>
> Mpt 1 2
=[1,2]
:t Mpt 1 2
=Mpt 1 1 :: Num a => MyPoint a
> Mpt "a" "b"
=["a","b"]
> :t Mpt "a" "b"
Mpt "a" "b" :: MyPoint [Char]
```



##### Using typeclasses (where the Show came from.)



```
class Myc a where
    (-+-) :: a -> a -> a
    (+-+) :: a -> a -> a
    (***) :: a -> a -> a
    x *** y = x

instance Myc (String,String) where
    x -+- y = y
    x +-+ y = x

instance Myc (Char,Char) where
    x -+- y = x
    x +-+ y = y

instance Myc Int where
    x -+- y = x
    x +-+ y = y

-- using a function that uses Myc
myfunc :: (Myc a) => a -> a
myfunc a = a +-+ a

myf :: (Myc a) => a -> a
myf a = a \*\*\* a
```


```
> :t myfunc
=myfunc :: Myc a => a -> a
> myfunc ("a","aa")
=("a","aa")
> myfunc (1,1)
    ERROR - Unresolved overloading
    *** Type       : (Num a, Num b, Myc (b,a)) => (b,a)
    *** Expression : myfunc (1,1)
> myf ('1','2')
=('1','2')
```


 

As you can see, the operator *** is defined for all types that are instances of class Myc. for the other functions, they have to be implemented by the individual type to be considered an instance of class Myc.

A common error is  

 

```
> myfunc 1
ERROR - Unresolved overloading
*** Type       : (Num a, Myc a) => a
*** Expression : myfunc 1
```


This happens because there are multiple types that are applicable here. This can be resolved by specifying the type of input explicitly.

```
> myfunc (1::Int)
=1
```
