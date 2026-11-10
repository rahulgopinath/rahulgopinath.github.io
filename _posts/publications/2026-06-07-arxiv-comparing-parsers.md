---
layout: post
categories : publications
tagline: "."
tags : publication
e:  An Empirical Comparison of General Context-Free Parsers
title: An Empirical Comparison of General Context-Free Parsers
authors: Huan Vo, Danushka Liyanage, Hong Jin Kang, Sasha Rubin, Rahul Gopinath
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Parsing underpins a vast range of software engineering tasks,
from compilers and static analyzers to language servers and fuzz testing tools.
Yet most parsers deployed in practice are deterministic (LL or LR),
forcing developers not only to contort their grammars to fit the parser,
but to simplify the very languages they design
sacrificing expressiveness for the sake of parseability.
General context-free parsers eliminate this constraint.
Yet, despite decades of algorithmic development,
no rigorous head-to-head comparison exists across the major families of parsing algorithms.

We present the first unified, controlled benchmark of six generalized parsing algorithms:
CYK, Valiant, Earley, GLL, RNGLR, and BRNGLR,
plus deterministic LL(1) and LR(1) baselines,
all implemented in Rust with shared data structures and parse-tree extraction,
and evaluated across 22 grammars ranging from simple expressions to full C++ and Java.
Our results show that the cost of generality is lower than widely assumed.
On deterministic grammars, the GLR family incurs only a 3x median slowdown over LR(1),
with a narrow and predictable variance.
GLR is the clear performance winner among generalized parsers
and a practical default choice for software engineering tools.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2606.08465)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2026/vo2026empirical.bib "reference")
