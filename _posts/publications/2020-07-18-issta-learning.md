---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Learning Input Tokens for Effective Fuzzing
title: Learning Input Tokens for Effective Fuzzing
authors: Bjoern Mathis, Rahul Gopinath, Andreas Zeller
venue: ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Modern fuzzing tools like AFL operate at a lexical level: They explore the input
space of tested programs one byte after another.  For inputs with complex
syntactical properties, this is very inefficient, as keywords and other tokens
have to be composed one character at a time. Fuzzers thus allow to specify
dictionaries listing possible tokens the input can be composed from; such
dictionaries speed up fuzzers dramatically. Also, fuzzers make use of dynamic
tainting to track input tokens and infer values that are expected in the input
validation phase. Unfortunately, such tokens are usually implicitly converted to
program specific values which causes a loss of the taints attached to the input
data in the lexical phase. In this paper we present a technique to extend
dynamic tainting to not only track explicit data flows but also taint implicitly
converted data without suffering from taint explosion. This extension makes it
possible to augment existing techniques and automatically infer a set of
tokens and seed inputs for the input language of a program given nothing but the
source code.  Specifically targeting the lexical analysis of an input processor,
our LFuzzer test generator systematically explores branches of the lexical
analysis, producing a set of tokens that fully cover all decisions seen.
The resulting set of tokens can be directly used as a dictionary for fuzzing.
Along with the token extraction seed inputs are generated which give further
fuzzing processes a head start. In our experiments, the LFuzzer-AFL combination
achieves up to 17% more coverage on complex input formats like JSON, Lisp,
TinyC, and JS compared to AFL.

**Artifacts** _available_ ![ACM artifact available](/resources/acm_artifact_available_20px.png) _functional_ ![ACM artifact functional](/resources/acm_artifact_functional_20px.png)

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2020/mathis2020learning.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2020/mathis2020learning.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://www.slideshare.net/BjrnMathis/lfuzzer-learning-input-tokens-for-effective-fuzzing-237085021 "presentation")

