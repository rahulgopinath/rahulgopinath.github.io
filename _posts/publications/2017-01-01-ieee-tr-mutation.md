---
layout: post
categories : publications
tagline: "."
tags : publication
e: Mutation Reduction Strategies Considered Harmful
title: Mutation Reduction Strategies Considered Harmful
authors: Rahul Gopinath, Iftekhar Ahmed, Mohammad Amin Alipour, Carlos Jensen, Alex Groce
venue: IEEE Transactions on Reliability
kind: journal
thesort: peerreviewed
peerreviewed: no
---

Mutation analysis is a well-known yet unfortunately costly method for measuring
test suite quality. Researchers have proposed numerous mutation reduction
strategies in order to reduce the high cost of mutation analysis, while
preserving the representativeness of the original set of mutants.

As mutation reduction is an area of active research, it is important to
understand the limits of
possible improvements. We theoretically and empirically investigate the
limits of improvement in effectiveness from using mutation reduction
strategies compared to random sampling.
Using real-world open source programs as subjects, we find an absolute limit in
improvement of effectiveness over random sampling - 13.078%.

Given our findings with respect to absolute limits, one may ask: how
effective are the extant mutation reduction strategies?  We evaluate
the effectiveness of multiple mutation reduction strategies in
comparison to random sampling.  We find that none of the mutation
reduction strategies evaluated -- many forms of operator
selection, and stratified sampling (on operators or program elements)
-- produced an effectiveness advantage larger than 5% in
comparison with random sampling.

Given the poor performance of mutation selection strategies --- they may have a
negligible advantage at best, and often perform worse than random sampling --
we caution practicing testers against applying mutation reduction
strategies without adequate justification.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ieeetr2017/gopinath2017mutation.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ieeetr2017/gopinath2017mutation.bib "reference")

