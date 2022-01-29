---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Inferring Input Grammars from Dynamic Control Flow
title: Inferring Input Grammars from Dynamic Control Flow
authors: Rahul Gopinath, Björn Mathis, Andreas Zeller
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

A program is characterized by its input model, and a formal input model can be 
of use in diverse areas including vulnerability analysis, reverse engineering, 
fuzzing and software testing, clone detection and refactoring. Unfortunately, 
input models for typical programs are often unavailable or out of date. While 
there exist algorithms that can mine the syntactical structure of program 
inputs, they either produce unwieldy and incomprehensible grammars, or require 
heuristics that target specific parsing patterns. In this paper, we present a 
general algorithm that takes a program and a small set of sample inputs and 
automatically infers a readable context-free grammar capturing the input 
language of the program. We infer the syntactic input structure only by 
observing access of input characters at different locations of the input 
parser. This works on all program stack based recursive descent input parsers, 
including PEG and parser combinators, and can do entirely without program 
specific heuristics. Our Mimid prototype produced accurate and readable 
grammars for a variety of evaluation subjects, including expr, URLparse, and 
microJSON.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/1912.05937 "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2019/gopinath2019inferring.bib "reference")

