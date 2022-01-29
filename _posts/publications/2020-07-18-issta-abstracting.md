---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Abstracting Failure Inducing Inputs
title: Abstracting Failure Inducing Inputs
authors: Rahul Gopinath, Alexander Kampmann, Nikolas Havrikov, Ezekiel O. Soremekun, Andreas Zeller
venue: ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

A program fails.  Under which circumstances does the failure occur?  Starting
with a single failure-inducing input ("The input ((4)) fails") and an input
grammar, the DDSET algorithm uses systematic tests to automatically generalize
the input to an abstract failure inducing input that contains both (concrete)
terminal symbols and (abstract) nonterminal symbols from the grammar---for
instance, "((&lt;expr&gt;))", which represents any expression &lt;expr&gt; in double
parentheses.  Such an abstract failure inducing input can be used
1. as a debugging diagnostic, characterizing the circumstances under which a
failure occurs ("The error occurs whenever an expression is enclosed in
double parentheses"); 2. as a producer of additional failure-inducing tests to
help design and validate fixes and repair candidates ("The inputs ((1)), ((3 * 4)),
and many more also fail").
In its evaluation on real-world bugs in JavaScript, Clojure, Lua, and Coreutils,
DDSET's abstract failure inducing inputs provided to-the-point diagnostics, and
precise producers.

**Note:**
As of now, we check each abstraction independently of others, and then merge them which necessitates isolation later. An alternative route is to simply accumulate abstractions as your find them, and when generating, regenerate each abstract node that you have accumulated. With this, we can be sure that each node that we mark as abstract is truly abstract. A problem here is that of semantic validity. That is, if say the first abstraction has only 0.5 chance of producing a valid input, and the next abstraction candidate has again only 0.5 chance of producing a valid input, combining them together will reduce the probability of valid input in any generation to 0.25, and as abstractions accumulate, the probability of generating semantically valid inputs drop. Hence, we instead identify them independently and later merge them, with the trade off being a later isolation step.

Another difference is that during isolation we leave every possibly causative part intact. That is, if A or B is necessary for fault reproduction, we leave both A and B as concrete. A user may instead change it to leave either A or B as concrete.

**Artifacts** _available_ ![ACM artifact available](/resources/acm_artifact_available_20px.png) _functional_ ![ACM artifact functional](/resources/acm_artifact_functional_20px.png) _reusable_ ![ACM artifact reusable](/resources/acm_artifact_reusable_20px.png)

**ACM Distinguished Paper** ![distinguished paper](/resources/acm_distinguished_paper_20px.png)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3895797.svg)](https://doi.org/10.5281/zenodo.3895797)

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2020/gopinath2020abstracting.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2020/gopinath2020abstracting.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/abstracting-failure-inducing-inputs "presentation")

