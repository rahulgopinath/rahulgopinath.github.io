---
layout: post
categories : publications
tagline: "."
tags : publication
e: Evaluating non-adequate test-case reduction 
title: Evaluating non-adequate test-case reduction
authors: Mohammad Amin Alipour, August Shi, Rahul Gopinath, Darko Marinov, Alex Groce
venue: IEEE/ACM International Conference on Automated Software Engineering (ASE)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Given two test cases, one larger and one smaller, the smaller test case is preferred for many purposes. A smaller test case usually runs faster, is easier to understand, and is more convenient for debugging. However, smaller test cases also tend to cover less code and detect fewer faults than larger test cases. Whereas traditional research focused on reducing test suites while preserving code coverage, one line of recent work has introduced the idea of reducing individual test cases, rather than test suites, while still preserving code coverage. Another line of recent work has proposed non-adequately reducing test suites by not even preserving all the code coverage. This paper empirically evaluates a new combination of these ideas: non-adequate reduction of test cases, which allows for a wide range of trade-offs between test case size and fault detection.

Our study introduces and evaluates C%-coverage reduction (where a test case is reduced to retain at least C% of its original coverage) and N-mutant reduction (where a test case is reduced to kill at least N of the mutants it originally killed). We evaluate the reduction trade-offs with varying values of C and N for four real-world C projects: Mozilla’s SpiderMonkey JavaScript engine, the YAFFS2 flash file system, Grep, and Gzip. The results show that it is possible to greatly reduce the size of many test cases while still preserving much of their fault-detection capability.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ase2016/alipour2016evaluating.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ase2016/alipour2016evaluating.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/evaluating-non-adequate-test-case-reduction "presentation")
