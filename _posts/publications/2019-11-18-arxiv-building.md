---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Building Fast Fuzzers
title: Building Fast Fuzzers
authors: Rahul Gopinath, Andreas Zeller
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Fuzzing is one of the key techniques for evaluating the robustness of programs 
against attacks. Fuzzing has to be effective in producing inputs that cover 
functionality and find vulnerabilities. But it also has to be efficient in 
producing such inputs quickly. Random fuzzers are very efficient, as they can 
quickly generate random inputs; but they are not very effective, as the large 
majority of inputs generated is syntactically invalid. Grammar-based fuzzers 
make use of a grammar (or another model for the input language) to produce 
syntactically correct inputs, and thus can quickly cover input space and 
associated functionality. Existing grammar-based fuzzers are surprisingly 
inefficient, though: Even the fastest grammar fuzzer Dharma still produces 
inputs about a thousand times slower than the fastest random fuzzer. So far, 
one can have an effective or an efficient fuzzer, but not both.  In this paper, 
we describe how to build fast grammar fuzzers from the ground up, treating the 
problem of fuzzing from a programming language implementation perspective. 
Starting with a Python textbook approach, we adopt and adapt optimization 
techniques from functional programming and virtual machine implementation 
techniques together with other novel domain-specific optimizations in a 
step-by-step fashion. In our F1 prototype fuzzer, these improve production 
speed by a factor of 100--300 over the fastest grammar fuzzer Dharma. As F1 is 
even 5--8 times faster than a lexical random fuzzer, we can find bugs faster 
and test with much larger valid inputs than previously possible.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/1911.07707 "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2019/gopinath2019building.bib "reference")

