---
layout: post
categories : publications
tagline: "."
tags : publication
e: Resource Adaptation via Test-Based Software Minimization 
title: Resource Adaptation via Test-Based Software Minimization
authors: Arpit Christi, Alex Groce, Rahul Gopinath
venue: IEEE International Conference on Self-Adaptive and Self-Organizing Systems (SASO)
kind: conference
thesort: peerreviewed
peerreviewed: no
---

Building software systems that adapt to changing resource environments
is challenging: developers cannot anticipate all future situations
that a software system may face, and even if they could, the effort
required to handle such situations would often be too onerous for
practical purposes. We propose a novel approach to allow a system to
generate resource usage adaptations: use delta-debugging to generate
versions of software systems that are reduced in size because they no
longer have to satisfy all tests in the software's test suite. Many
such variations will, while retaining core system functionality, use
fewer resources. We describe an tool for computing such adaptations,
based on our notion that labeled subsets of a test suite can be used
to conveniently describe possible relaxations of system
specifications. Using the NetBeans IDE, we demonstrate that even
without additional infrastructure or heuristics, our approach is
capable of quickly and cleanly removing a program's undo
functionality, significantly reducing its memory use, with no more
effort than simply labeling three test cases as undo-related.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/saso2017/christi2017resource.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/saso2017/christi2017resource.bib "reference")

