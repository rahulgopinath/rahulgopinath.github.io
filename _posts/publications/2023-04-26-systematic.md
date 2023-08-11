---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Systematic Assessment of Fuzzers using Mutation Analysis
title: Systematic Assessment of Fuzzers using Mutation Analysis
authors: Philipp Goerz, Bjoern Mathis, Keno Hassler, Emre Gueler, Thorsten Holz, Andreas Zeller, and Rahul Gopinath
venue: Usenix Security
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Fuzzing is an important method to discover vulnerabilities
in programs. Despite considerable progress in this area in
the past years, measuring and comparing the effectiveness of
fuzzers is still an open research question. In software testing,
the gold standard for evaluating test quality is mutation analysis,
which evaluates a test’s ability to detect synthetic bugs:
if a set of tests fails to detect such mutations, it is expected to
also fail to detect real bugs. Mutation analysis subsumes various
coverage measures and provides a large and diverse set
of faults that can be arbitrarily hard to trigger and detect, thus
preventing the problems of saturation and overfitting.
Unfortunately, the cost of traditional mutation analysis is exorbitant
for fuzzing, as mutations need independent evaluation.

In this paper, we apply modern mutation analysis techniques that pool multiple mutations and allow us—for the
first time—to evaluate and compare fuzzers with mutation
analysis. We introduce an evaluation bench for fuzzers and
apply it to a number of popular fuzzers and subjects. In a
comprehensive evaluation, we show how we can use it to assess
fuzzer performance and measure the impact of improved
techniques. The CPU time required remains manageable:
4.09 CPU years are needed to analyze a fuzzer on seven
subjects and a total of 141,278 mutations. We find that today’s
fuzzers can detect only a small percentage of mutations, which
should be seen as a challenge for future research—notably in
improving (1) detecting failures beyond generic crashes and
(2) triggering mutations (and thus faults).

**Artifacts** _available_ ![ACM artifact available](/resources/usenixbadges-available_20px.png) _functional_ ![Usenix artifact functional](/resources/usenixbadges-functional_20px.png) _reusable_ ![Usenix artifact reusable](/resources/usenixbadges-reproduced_20px.png)


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/usenixsecurity2023/goerz2023systematic.pdf "paper")
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://github.com/CISPA-SysSec/mua_fuzzer_bench/ "replication")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/systematic-assessment-of-fuzzers-using-mutation-analysis "presentation")

