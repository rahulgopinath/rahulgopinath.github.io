---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: Homoiconic languages
title: Homoiconic languages
---

    I have been interested in [homoiconicity](http://en.wikipedia.org/wiki/Homoiconicity) in languages for some time now. In simple terms, it means that the code is accessible in the same format as that of one of the fundamental data types in the language. Often this data type is the one that gives the language its character.

Homoiconicity is not precisely defined yet, and is subject of an ongoing [debate](http://c2.com/cgi/wiki?HomoiconicityClassification). However, as far as I am concerned, the degree of Homoiconicity in a language corresponds to the degree of corelation between the expressions in the language and the datastructure used to represent them. ie, If I am using a tree to represent my program, then the language is homoiconic if all the leaves in the tree are valid tokens for the language and the token should parse the same both in the datastructure and in the language.

The reason for such a definition is that, just having an 'eval(<string>)' function does not make a language homoiconic, since the string datatype does not have a high correlation with the program encoded in the string.

ie: in a string 'a = myfunction(a,b,c)', each token in language is a valid string (ignoring the quote), but the smallest strings possible (leaves of the datastructure) does not parse the same as the corresponding program.

-- myfunction is the lexical token as parsed by the language translator, while my, func, t,i,o,n are all valid strings.

for a Homoiconic language like scheme,

'(append (my) long (list)), represented by a tree, having leaves, append, my, long and list, each parse the same as that of the language represented with in.


 This property is interesting because it immediately implies some wonderful properties in the language, notably:

* Ability to Generate programs during runtime allowing for a higher level of abstraction.
* Ability to Meta program (Allowing for hooking into and modification of language structures) during runtime.
* And most important of all, the Syntax of language is generally very simple with very few special cases (if at all.)

 The last point is very special because it has a huge advantage and an equally huge disadvantage.

The disadvantage is that it is hard for humans to visually parse as the uniformity of the language often removes any visual cues that we are familiar with in most of the languages. (I think one of the reasons of Perl's success was its abundance of visual cues.) This leads to a very steep learning curve for the language in question.

 The advantage on the other hand is that the uniformity of syntax makes it easy for us (Humans) to think about the written code as another data that can be manipulated. It becomes easy to think about higher order code (i.e. code that writes or modifies code). (This is what gives us the first point.) This gives us the ability to mould the language to the needs of specific domains at hand.

Some of these languages also are the best examples of a particular way of thinking (what are called 'pure' languages) and very often they provide the 'aha' moment for the particular paradigm they represent.

Below are some of the homoiconic languages that I know of. (Some have examples of syntaxes but I will treat them more in detail in later entries.)

(Most of the code is intented to show just the syntax so they are very inefficient but compact.)

##### Scheme

    Scheme is a lisp variant (Almost all lisp variants are homoiconic) and has the most consistent semantics in the lisp family. It has list as the fundamental data structure and it is encoded by parenthesis - ( ).

It supports higher order programming, and is usually used in the functional programming paradigm. The scheme language is mostly based on lambda calculus. 

Here is a fragment of Scheme (A quicksort function)

```
(require (lib "list.ss"))
(define (qsort lst)
  (cond
    ((null? lst) lst)
    (else
     (let ((h (car lst)) (t (cdr lst)))
       (append
        (qsort (filter (lambda (x) (<= x h)) t))
	(list h)
        (qsort (filter (lambda (x) (> x h)) t))))
       )))
```

Usage

```
> (qsort '(3 8 5 4 8 2 4 1 9 4))
```

##### Joy

      Joy is a stack based (concatenative seems to be the word used nowadays.) language that is similar to postscript and forth. It is very minimalist and has a very consistent syntax compared to either of them and supports a points-free style of programming (A style in which variables are not used). It is based on combinatorial calculus rather than lambda calculus and supports anonymous functions, higher order programming and others.

The quote (bounded by [ and ]) is the most basic data structure in joy. It can act as both a store for values and also as definition of function.

{Shameless plug: [V](http://code.google.com/p/v-language/) is the variant of Joy on JVM that I developed. I changed the definition format of Joy in V so that it is more Homoiconic.}

QuickSort in [V](http://code.google.com/p/v-language/) (A variant of [Joy](http://www.latrobe.edu.au/philosophy/phimvt/joy.html)) 

```
[qsort
    [small?]
    []
    [uncons [>] split&]
    [[swap] dip cons concat]
    binrec].
```

Usage

```
> [3 1 8 5 7 9 2] qsort
```

It can also be written using the stack shuffler in 'V' as below (which might be more understandable.)

```
[qsort
    [joinparts [pivot [\*list1] [\*list2] : [\*list1 pivot \*list2]] view].
    [split_on_first_element uncons [>] split&].
    [small?]
        []
        [split_on_first_element
            [list1 list2 : [list1 qsort list2 qsort joinparts]] view i]
    ifte].
```

##### Tcl

Tcl is famous as the glue language for applications. It's cardinal data type is the string (actually the list). Every thing including the arguments to functions, the bodies of functions, and other data types can be converted back and forth from list to their representation. The biggest idea in Tcl is that you do not need to provide the parsing of any kind of data with in the language, and can instead delegate it to the individual commands that receive the strings as the arguments. Thus all control structures are implemented in Tcl the same way, and it allows for a very consistent syntax. The cardinal datatype the list is usually bounded by braces - { }.

 The quick sort in tcl

```
proc lmatch {l args} {
    set mylst {}
    foreach x $l {
        if {[expr $x $args]} {
            lappend mylst $x
        }
    }
    return $mylst
}

proc qsort lst {
    if {![llength $lst]} {
        return {}
    }
    set h [lindex $lst 0]
    set t [lrange $lst 1 end]
    return [concat [qsort [lmatch $t <= $h]] $h [qsort [lmatch $t > $h]]]
}
```


Usage

```
> puts [qsort {5 3 4 1 7 8 2 9 1}]
```

##### SmallTalk

SmallTalk (80) is possibly the purest object oriented language that you can find in the planet.  All things happen in SmallTalk by way of messages passed back and forth between objects. While the SmallTalk does not have a defined physical representation for the code for creating classes,  It does allow access to the classes as objects directly (Which is the fundamental datatype). This makes it eligible to be called a Homoiconic language.

```
qsort
	| t h |
	self isEmpty
		ifFalse: [
			t := self allButFirst.
			h := self first.
			\^ (t select: [:each | each < h]) qsort ,
				{h} ,
				(t select: [:each | each >= h]) qsort].
```

Usage

```
> #(3 2 5 1 3 7 9 8) qsort
```


Others (From wiki)- 

[Prolog](http://en.wikipedia.org/wiki/Prolog), [REBOL](http://en.wikipedia.org/wiki/REBOL), [SNOBOL](http://en.wikipedia.org/wiki/SNOBOL), [TRAC](http://en.wikipedia.org/wiki/TRAC_programming_language), [Io](http://en.wikipedia.org/wiki/Io_programming_language)

The purest one is ofcourse the lambda calculus (the only datatype is a function that takes one argument.) 

I think some variants of APL (like K or J) might fit into the Homoiconic category too, but I have not studied them yet. I will treat each of the homoiconic languages in detail in later enties.
