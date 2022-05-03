---
layout: post
categories : publications
tagline: "."
tags : publication
e: First, Fuzz The Mutants
title: First, Fuzz The Mutants
authors:  Alex Groce, Goutamkumar Kalburgi, Claire Le Goues, Kush Jain, Rahul Gopinath
venue: Fuzzing Workshop (NDSS)
kind: workshop
thesort: peerreviewed
peerreviewed: yes
---
Most fuzzing efforts, very understandably, focus on
fuzzing the program in which bugs are to be found. However,
in this paper we propose that fuzzing programs "near" the
System Under Test (SUT) can in fact improve the effectivness
of fuzzing, even if it means less time is spent fuzzing the actual
target system. In particular, we claim that fault detection and
code coverage can be improved by splitting fuzzing resources
between the SUT and mutants of the SUT. Spending half of
a fuzzing budget fuzzing mutants, and then using the seeds
generated to fuzz the SUT can allow a fuzzer to explore more
behaviors than spending the entire fuzzing budget on the SUT.
The approach works because fuzzing most mutants is “almost”
fuzzing the SUT, but may change behavior in ways that allow
a fuzzer to reach deeper program behaviors. Our preliminary
results show that fuzzing mutants is trivial to implement, and
provides clear, statistically significant, benefits in terms of fault
detection for a non-trivial benchmark program; these benefits are
robust to a variety of detailed choices as to how to make use of
mutants in fuzzing. The proposed approach has two additional
important advantages: first, it is fuzzer-agnostic, applicable to
any corpus-based fuzzer without requiring modification of the
fuzzer; second, the fuzzing of mutants, in addition to aiding
fuzzing the SUT, also gives developers insight into the mutation
score of a fuzzing harness, which may help guide improvements
to a project’s fuzzing approach.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ndss2022/groce2022first.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ndss2022/groce2022first.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>]()

