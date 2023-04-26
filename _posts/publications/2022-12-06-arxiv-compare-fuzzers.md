---
layout: post
categories : publications
tagline: "."
tags : publication
e:  How to Compare Fuzzers
title: How to Compare Fuzzers
authors: Philipp Görz, Björn Mathis, Keno Hassler, Emre Güler, Thorsten Holz, Andreas Zeller, Rahul Gopinath
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Fuzzing is a key method to discover vulnerabilities in programs. Despite considerable progress in this area in the past years, measuring and comparing the effectiveness of fuzzers is still an open research question. In software testing, the gold standard for evaluating test quality is mutation analysis, assessing the ability of a test to detect synthetic bugs; if a set of tests fails to detect such mutations, it will also fail to detect real bugs. Mutation analysis subsumes various coverage measures and provides a large and diverse set of faults that can be arbitrarily hard to trigger and detect, thus preventing the problems of saturation and overfitting. Unfortunately, the cost of traditional mutation analysis is exorbitant for fuzzing, as mutations need independent evaluation.

In this paper, we apply modern mutation analysis techniques that pool multiple mutations; allowing us, for the first time, to evaluate and compare fuzzers with mutation analysis. We introduce an evaluation bench for fuzzers and apply it to a number of popular fuzzers and subjects. In a comprehensive evaluation, we show how it allows us to assess fuzzer performance and measure the impact of improved techniques. While we find that today's fuzzers can detect only a small percentage of mutations, this should be seen as a challenge for future research -- notably in improving (1) detecting failures beyond generic crashes (2) triggering mutations (and thus faults). 

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2212.03075)
