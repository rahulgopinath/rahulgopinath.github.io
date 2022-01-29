---
layout: post
categories : publications
tagline: "."
tags : publication
e: Measuring Effectiveness of Mutant Sets 
title: Measuring Effectiveness of Mutant Sets
authors: Rahul Gopinath, Amin Alipour, Iftekhar Ahmed, Carlos Jensen, Alex Groce
venue: IEEE International Conference on Software Testing, Verification and Validation Workshop (ICSTW) Mutation
kind: workshop
thesort: peerreviewed
peerreviewed: yes
---

Redundant mutants, where multiple mutants end 
up producing same the semantic variant of the program is a major 
problem in mutation analysis, and a measure of effectiveness is 
an essential tool for evaluating mutation tools, new operators, 
and reduction techniques. Previous research suggests using size 
of disjoint mutant set as an effectiveness measure. 

We start from a simple premise: That test suites need to be 
judged on both the number of unique variations in specifications 
they detect (as variation measure), and also on how good they 
are in detecting harder to find bugs (as a measure of subtlety). 
Hence, any set of mutants should to be judged on how best they 
allow these measurements. 

We show that the disjoint mutant set has two major inadequacies 
— the single variant assumption and the large test suite 
assumption when used as a measure of effectiveness in variation, 
which stems from its reliance on minimal test suites, and we show 
that when used to emulate hard to find bugs (as a measure of 
subtlety), it discards useful mutants. 

We propose two alternative measures, one oriented toward 
the measure of effectiveness in variation and not vulnerable to 
either single variant assumption, or to large test suite assumption 
and the other towards effectiveness in subtlety, and provide a 
benchmark of these measures using diverse tools.

##### Updates:

(Thanks to [Darko Marinov](http://mir.cs.illinois.edu/marinov/), [Farah Hariri](http://mir.cs.illinois.edu/farah/), [August Shi](http://mir.cs.illinois.edu/awshi2/), Muhammad Mahmood, and Warnakulasuriya Fernando)

* The *minimal mutants* from Ammann et al. ([Ammann 2014](/references#ammann2014establishing)), and the *disjoint mutants* from Kintis et al. ([Kintis 2010](/references#kintis2010evaluating)) is same as the *surface mutants* in this paper. Hence, the *surface mutants* are not an alternative. However, the two measures provided: The *volume ratio*, and the *surface correction* are the right interpretations for disjoint/minimal/surface mutants.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icst2016/gopinath2016measuring.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icst2016/gopinath2016measuring.bib "reference")
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](http://eecs.osuosl.org/rahul/icst2016/ "data")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/measuring-effectiveness-of-mutant-sets "presentation")

