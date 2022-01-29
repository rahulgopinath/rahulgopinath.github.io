---
layout: post
categories : publications
tagline: "."
tags : publication
e: MuCheck -- an extensible tool for mutation testing of haskell programs 
title: MuCheck -- an extensible tool for mutation testing of haskell programs
authors: Duc Le, Mohammad Amin Alipour, Rahul Gopinath, Alex Groce
venue: ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

This paper presents MuCheck, a mutation testing tool for Haskell programs. This is the first tool to be published (to our knowledge) that is explicitly oriented towards mutation testing for functional programs. MuCheck is a counterpart to the widely used QuickCheck random testing tool in fuctional programs, and can be used to evaluate the efficacy of QuickCheck property definitions. The tool implements mutation operators that are specifically designed for functional programs, and makes use of the type system of Haskell to achieve a more relevant set of mutants than otherwise possible. Mutation coverage is particularly valuable for functional programs due to highly compact code, referential transparency, and clean semantics, which make augmenting a test suite or specification based on surviving mutants a practical method for improved testing.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2014/le2014mucheck.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2014/le2014mucheck.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/alipourm/mucheck-an-extensible-tool-for-mutation-testing-of-haskell-programs "presentation")

