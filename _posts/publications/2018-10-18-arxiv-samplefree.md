---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Sample-Free Learning of Input Grammars for Comprehensive Software Fuzzing
title: Sample-Free Learning of Input Grammars for Comprehensive Software Fuzzing
authors: Rahul Gopinath, Björn Mathis, Mathias Höschele, Alexander Kampmann, Andreas Zeller
venue: arXiv
kind: arxiv
thesort: techreport
peerreviewed: no
---

Generating valid test inputs for a program is much easier if one knows the 
input language. We present first successes for a technique that, given a 
program P without any input samples or models, learns an input grammar that 
represents the syntactically valid inputs for P -- a grammar which can then be 
used for highly effective test generation for P . To this end, we introduce a 
test generator targeted at input parsers that systematically explores parsing 
alternatives based on dynamic tracking of constraints; the resulting inputs go 
into a grammar learner producing a grammar that can then be used for fuzzing. 
In our evaluation on subjects such as JSON, URL, or Mathexpr, our PYGMALION 
prototype took only a few minutes to infer grammars and generate thousands of 
valid high-quality inputs. 


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2109.11277 "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2021/dutra2021formatfuzzer.bib "reference")

