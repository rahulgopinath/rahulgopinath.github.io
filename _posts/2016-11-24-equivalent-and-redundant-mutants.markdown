---
published: false
title: Equivalent, Redundant, Trivial and Stubborn Mutants
layout: post
comments: true
tags: [mutation]
categories: post
---

A recent discussion I had with other researchers suggests that the
terms *equivalent*, *redundant*, *stubborn* and *trivial* mutants
are sometimes misunderstood. I hope that this post clarifies the distinctions.
For these definitions, the notion of *semantic equivalence* is important, and we define it first.

### Semantic Equivalence

A program is semantically equivalent to another if it can not be distinguished from another in terms of its semantic properties (input-output mapping, runtime requirements etc.).

Indeed, a *general* solution to program equivalence is impossible due to the well known Rice's theorem.

Rice's theorem ([Rice 1953](/references#rice1953classes)): All non-trivial semantic properties of programs are undecidable. (A property is trivial if it is true or false for all programs. A property is semantic -- as opposed to syntactic -- if it is about a programs behavior).

### Mutant of a program

A mutant of a program is a variant of a program that is syntactically *valid*, but *different* from the original. That is, if a variant does not compile, it is *not* a mutant ([Demillo 1979](/references#demillo1979program)). The idea of mutation analysis is to produce variants that can plausibly be present in the code-base, so that we can evaluate the effectiveness of test cases by running the program against the test suite. So variants that does not compile, and hence can not be *run* does not serve the purpose of mutation analysis. I emphasize it because this seems to be an area where there seems to be quite a bit of confusion, especially because of trivial mutation systems that mutate programs using simple regular expression searches.

## Equivalent Mutant

A mutant is classified as an equivalent mutant if the mutant is semantically equivalent to the original program ([Budd 1982](/references#budd1982two)). Note that it says nothing about the test cases. The number of equivalent mutants are dependent only on the particular mutation operators used, and the program which was mutated. This again seems to be a confusion in some of the recent publications ([Visser 2016](/references#visser2016what)).

## Redundant Mutant

A mutant is classified as redundant when it is *easier to detect* than another mutant. That is, given a mutant m1 that contains fault f1, and a mutant m2, that contains faults f1 and f2, the mutant m2 is redundant with respect to mutant m1. Entire sets of mutants may be redundant with respect to another set (for example, theoretical minimal sets make the full set redundant), and mutants equivalent to each other are trivially redundant. Due to Rice's theorem, one does not have have a general way to distinguish whether a given mutant is redundant with respect to another or not. So we usually satisfy ourselves with dynamic redundancy where we only look at the test we have (under the assumption that the test suite is reasonably adequate).

## Trivial and Stubborn Mutant

Trivialness and stubbornness of mutant is a matter of degree. A mutant is x% trivial if it is detected by at least x% of the input test data. Similarly a mutant is x% stubborn if it is detected by at most x% of the input test data.
Note that this says nothing about the structure of the program.


## Trivial and Stubborn Mutant After Excluding Reachability

Recent publications ([Visser 2016](/references#visser2016what)) include reachability into the definition. That is, a mutant is x% trivial after excluding reachability if at least x% of the input test data that reaches the mutant is able to detect it. Similarly, a mutant is x% stubborn after excluding reachability if at most x% of the input test data that reaches the mutant is able to detect it.

