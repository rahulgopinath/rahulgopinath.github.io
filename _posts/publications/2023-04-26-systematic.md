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
the gold standard for evaluating test quality is mutation anal-
ysis, which evaluates a test’s ability to detect synthetic bugs:
if a set of tests fails to detect such mutations, it is expected to
also fail to detect real bugs. Mutation analysis subsumes vari-
ous coverage measures and provides a large and diverse set
of faults that can be arbitrarily hard to trigger and detect, thus
preventing the problems of saturation and overfitting. Unfor-
tunately, the cost of traditional mutation analysis is exorbitant
for fuzzing, as mutations need independent evaluation.

In this paper, we apply modern mutation analysis tech-
niques that pool multiple mutations and allow us—for the
first time—to evaluate and compare fuzzers with mutation
analysis. We introduce an evaluation bench for fuzzers and
apply it to a number of popular fuzzers and subjects. In a
comprehensive evaluation, we show how we can use it to as-
sess fuzzer performance and measure the impact of improved
techniques. The CPU time required remains manageable:
4.09 CPU years are needed to analyze a fuzzer on seven sub-
jects and a total of 141,278 mutations. We find that today’s
fuzzers can detect only a small percentage of mutations, which
should be seen as a challenge for future research—notably in
improving (1) detecting failures beyond generic crashes and
(2) triggering mutations (and thus faults).

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/usenixsecurity2023/goerz2023systematic.pdf "paper")
