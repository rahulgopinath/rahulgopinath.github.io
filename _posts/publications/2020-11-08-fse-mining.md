---
layout: post
categories : publications
tagline: "."
tags : publication
e: Mining input grammars from dynamic control flow 
title: Mining input grammars from dynamic control flow
authors: Rahul Gopinath, Bjoern Mathis, Andreas Zeller
venue: ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

One of the key properties of a program is its input specification. Having a
formal input specification can be critical in fields such as vulnerability
analysis, reverse engineering, software testing, clone detection, or
refactoring. Unfortunately, accurate input specifications for typical programs
are often unavailable or out of date.

In this paper, we present a general algorithm that takes a program and a small
set of sample inputs and automatically infers a readable context-free grammar
capturing the input language of the program. We infer the syntactic input
structure only by observing access of input characters at different locations of
the input parser. This works on all stack based recursive descent input parsers,
including parser combinators, and works entirely without program specific
heuristics. Our Mimid prototype produced accurate and readable grammars for a
variety of evaluation subjects, including complex languages such as JSON,
TinyC, and JavaScript.

**Artifacts** _available_ ![ACM artifact available](/resources/acm_artifact_available_20px.png) _functional_ ![ACM artifact functional](/resources/acm_artifact_functional_20px.png) _reusable_ ![ACM artifact reusable](/resources/acm_artifact_reusable_20px.png)


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3876969.svg)](https://doi.org/10.5281/zenodo.3876969)


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/fse2020/gopinath2020mining.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/fse2020/gopinath2020mining.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/mining-input-grammars-from-dynamic-control-flow "presentation")

