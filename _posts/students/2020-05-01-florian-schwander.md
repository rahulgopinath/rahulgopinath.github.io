---
layout: post
categories : student
tagline: "."
tags : [student florianschwander 2020]
e: Higher Order Mutation Analysis Using Rejected Input Strings
---

#### Masters Thesis

Higher Order Mutation Analysis Using Rejected Input Strings

#### Abstract


Mutation analysis is a method of assessing the quality of a test suite. It involves generating variants of the program that is being tested, and checking whether the test suite under evaluation detects the variation. While a majority of such syntactic changes result in detectable semantic differences from the original, it is, however, possible that such a change fails to induce a semantic change. Such mutants are considered equivalent to the original program. Since these mutants cannot be detected by any test suite, achieving a 100% detection rate (kill rate) may be impossible for a given program and its mutants. This threatens the utility of the mutation score. Further, the undetected mutants may need to be manually checked for equivalence in case the programmer wants to improve their test suite based on them.
We describe a novel technique that avoids creating equivalent mutants for input processors. Our idea is to generate plausible, near correct inputs for the program, collect those rejected, and generate variants that accept these rejected strings. Our technique allows us to provide an enhanced set of mutants along with newly generated test cases that kill them.

We evaluate our method on eight python programs and show that our technique can generate new mutants that are both interesting for the developer and guaranteed to be mortal.
