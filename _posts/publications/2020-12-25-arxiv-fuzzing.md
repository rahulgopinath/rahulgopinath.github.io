---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Fuzzing with Fast Failure Feedback
title: Fuzzing with Fast Failure Feedback
authors: Rahul Gopinath, Bachir Bendrissou, Björn Mathis, Andreas Zeller
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Fuzzing -- testing programs with random inputs -- has become the prime 
technique to detect bugs and vulnerabilities in programs. To generate inputs 
that cover new functionality, fuzzers require execution feedback from the 
program -- for instance, the coverage obtained by previous inputs, or the 
conditions that need to be resolved to cover new branches. If such execution 
feedback is not available, though, fuzzing can only rely on chance, which is 
ineffective. In this paper, we introduce a novel fuzzing technique that relies 
on failure feedback only -- that is, information on whether an input is valid 
or not, and if not, where the error occurred. Our bFuzzer tool enumerates byte 
after byte of the input space and tests the program until it finds valid 
prefixes, and continues exploration from these prefixes. Since no 
instrumentation or execution feedback is required, bFuzzer is language agnostic 
and the required tests execute very quickly. We evaluate our technique on five 
subjects, and show that bFuzzer is effective and efficient even in comparison 
to its white-box counterpart.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2012.13516 "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2020/gopinath2020fuzzing.bib "reference")

