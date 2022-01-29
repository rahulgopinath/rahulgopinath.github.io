---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Generating focused random tests using directed swarm testing.
title: Generating focused random tests using directed swarm testing.
authors: Mohammad Amin Alipour, Alex Groce, Rahul Gopinath, Arpit Christi
venue: ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Random testing can be a powerful and scalable method for finding faults
in software. However, sophisticated random testers usually test a whole
program, not individual components. Writing random testers for individual
components of complex programs may require unreasonable effort. In this paper
we present a novel method, directed swarm testing, that uses statistics and
a variation of random testing to produce random tests that focus on only
part of a program, increasing the frequency with which tests cover the
targeted code. We demonstrate the effectiveness of this technique using
real-world programs and test systems (the YAFFS2 file system, GCC, and
Mozilla SpiderMonkey JavaScript engine), and discuss various strategies for
directed swarm testing. The best strategies can improve coverage frequency for
targeted code by a factor ranging from 1.1-4.5x on average, and from nearly
3x to nearly 9x in the best case. For YAFFS2, directed swarm testing never
decreased coverage, and for GCC and SpiderMonkey coverage increased for over
99% and 73% of targets, respectively, using the best strategies. Directed
swarm testing improves detection rates for real SpiderMonkey faults, when
the code in the introducing commit is targeted. This lightweight technique
is applicable to existing industrial-strength random testers.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2016/alipour2016focused.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2016/alipour2016focused.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/arpitchristi/issta-2016-generating-focused-random-tests-using-directed-swarm-testing "presentation")

