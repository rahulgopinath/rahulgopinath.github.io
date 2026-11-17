---
layout: post
categories : publications
tagline: "."
tags : publication
e:  "AutoDiDact: Input Reduction over Inferred Structure"
title: "AutoDiDact: Input Reduction over Inferred Structure"
authors: Aarush Kumbhakern, Rahul Gopinath
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Delta debugging reduces a failing input by deleting chunks chosen by length,
which cuts through identifiers, keywords, and delimited groups.
The reduced input is often far from minimal,
and reaching it costs many oracle calls.
Grammar-based hierarchical reduction avoids this,
at the cost of needing a grammar for the format.

AutoDiDact recovers enough structure to reduce hierarchically without a grammar.
It infers a neutral word, such as a space,
whose insertion and removal leave the failure intact,
and uses it to split the input into tokens.
It then infers delimiter pairs that bound spans which can be reduced as units,
and applies hierarchical delta debugging to the resulting span tree.
Both inference steps ask only the question delta debugging already asks
of its oracle: does the failure still occur?

Across 125 inputs drawn from 18 format families,
AutoDiDact finds a neutral word for 75.
On those, its output is 83% smaller than byte-level delta debugging
while using 37% fewer oracle calls, by geometric mean,
and the advantage grows with input size.
It matches grammar-based hierarchical delta debugging in output size
without using a grammar, at roughly 3.85 times the oracle calls.
Because it needs only the oracle,
it can reduce malformed inputs as well.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2611.20969)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2026/kumbhakern2026autodidact.bib "reference")
