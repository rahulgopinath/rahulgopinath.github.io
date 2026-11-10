---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Input Repair via Synthesis and Lightweight Error Feedback
title: Input Repair via Synthesis and Lightweight Error Feedback
authors: Lukas Kirschner, Ezekiel Soremekun, Rahul Gopinath, Andreas Zeller
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Often times, input data may ostensibly conform to a given input format,
but cannot be parsed by a conforming program,
for instance, due to human error or data corruption.
In such cases, a data engineer is tasked with input repair,
i.e., she has to manually repair the corrupt data such that it follows a given format,
and hence can be processed by the conforming program.
Such manual repair can be time-consuming and error-prone.
In particular, input repair is challenging without an input specification (e.g., input grammar) or program analysis.

In this work, we show that incorporating lightweight failure feedback (e.g., input incompleteness) to parsers
is sufficient to repair any corrupt input data with maximal closeness to the semantics of the input data.
We propose an approach (called FSYNTH) that leverages lightweight error-feedback and input synthesis to repair invalid inputs.
FSYNTH is grammar-agnostic, and it does not require program analysis.
Given a conforming program, and any invalid input,
FSYNTH provides a set of repairs prioritized by the distance of the repair from the original input.
We evaluate FSYNTH on 806 (real-world) invalid inputs using four well-known input formats,
namely INI, TinyC, SExp, and cJSON.
In our evaluation, we found that FSYNTH recovers 91% of valid input data.
FSYNTH is also highly effective and efficient in input repair:
It repairs 77% of invalid inputs within four minutes.
It is up to 35% more effective than DDMax, the previously best-known approach.
Overall, our approach addresses several limitations of DDMax,
both in terms of what it can repair, as well as in terms of the set of repairs offered.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2208.08235)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2022/kirschner2022input.bib "reference")
