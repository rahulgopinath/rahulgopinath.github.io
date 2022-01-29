---
layout: post
categories : publications
tagline: "."
tags : publication
e: Topsy-Turvy -- a smarter and faster parallelization of mutation analysis 
title: Topsy-Turvy -- a smarter and faster parallelization of mutation analysis
authors: Rahul Gopinath, Carlos Jensen, Alex Groce
venue: ACM/IEEE International Conference on Software Engineering (ICSE)
kind: extended abstract
thesort: peerreviewed
peerreviewed: yes
---

Mutation analysis is an effective, if computationally expensive, technique
that allows practitioners to accurately evaluate the quality of their test
suites.  To reduce the time and cost of mutation analysis, researchers have
looked at parallelizing mutation runs --- running multiple mutated versions of
the program in parallel, and running through the tests in sequence on each mutated program
until a bug is found. While an improvement over sequential execution
of mutants and tests, this technique carries a significant
overhead cost due to its redundant execution of unchanged code paths. In this
paper we propose a novel technique (and its implementation) which
parallelizes the test runs rather than the mutants, forking mutants from a
single program execution at the point of invocation, which reduces 
redundancy. We show that our
technique can lead to significant efficiency improvements and cost
reductions.

##### Updates:

* Part of our concept is similar to the split-stream execution of
mutants suggested (not implemented) by King & Offutt ([King 1991](/references#king1991a)).

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icse2016/gopinath2016topsy.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icse2016/gopinath2016topsy.bib "reference")
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](http://eecs.osuosl.org/rahul/icse2016/ "data")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/topsy-turvy-a-smarter-and-faster-parallelization-of-mutation-analysis "presentation")
