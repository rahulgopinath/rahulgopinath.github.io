---
layout: post
categories : publications
tagline: "."
tags : publication
e: "\"Synthesizing Input Grammars\": A Replication Study"
title: "\"Synthesizing Input Grammars\": A Replication Study"
authors:  Bachir Bendrissou, Rahul Gopinath, Andreas Zeller
venue: ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

When producing test inputs for a program, test generators (“fuzzers”) can greatly profit from grammars that formally describe the language of expected inputs. In recent years, researchers thus have studied means to recover input grammars from programs and their executions. The GLADE algorithm by Bastani et al., published at PLDI 2017, was the first black-box approach to claim context-free approximation of input specification for non-trivial languages such as XML, Lisp, URLs, and more.

Prompted by recent observations that the GLADE algorithm may show lower performance than reported in the original paper, we have reimplemented the GLADE algorithm from scratch. Our evaluation confirms that the effectiveness score (F1) reported in the GLADE paper is overly optimistic, and in some cases, based on the wrong language. Furthermore, GLADE fares poorly in several real-world languages evaluated, producing grammars that spend megabytes to enumerate inputs.

**Artifacts** _available_ ![ACM artifact available](/resources/acm_artifact_available_20px.png) and _evaluated_ ![ACM artifact evaluated reusable](/resources/acm_artifact_reusable_20px.png)


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6409786.svg)](https://doi.org/10.5281/zenodo.6409786)



[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/pldi2022/bendrissou2022synthesizing.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/pldi2022/bendrissou2022synthesizing.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/synthesizing-input-grammars-a-replication-study)

