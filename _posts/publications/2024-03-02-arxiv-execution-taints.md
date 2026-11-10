---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Mutation Analysis with Execution Taints
title: Mutation Analysis with Execution Taints
authors: Rahul Gopinath, Philipp Görz
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Mutation analysis is one of the most effective,
but costly means of assessing the ability of software test suites to prevent bugs.
Traditional mutation analysis involves producing and evaluating syntactic variants of the original
to check whether the test suite under evaluation is capable of distinguishing
between the variant and the original in terms of behavior.

Evaluating each mutant separately means a large amount of redundant computation,
both between the original program and mutants, and also between different mutants.
Previous work explored numerous means of removing redundancy.
However, some amount of redundancy has remained especially in the post-mutation phase.

In this paper, we propose execution taints---a novel technique
that repurposes dynamic data-flow taints for mutation analysis.
Our technique is the only technique that can remove the redundancy in post-mutation phase,
achieving better efficiency in mutation analysis.
We further leverage memoization to eliminate redundant execution between program variants.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2403.01146)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2024/gopinath2024mutation.bib "reference")
