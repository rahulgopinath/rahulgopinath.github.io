---
layout: post
categories : publications
tagline: "."
tags : publication
e: Evaluating Fault Localization for Resource Adaptation via Test-based Software Modification
title: Evaluating Fault Localization for Resource Adaptation via Test-based Software Modification
authors: Arpit Christi, Alex Groce, Rahul Gopinath
venue: IEEE International Conference on Software Quality, Reliability and Security (QRS)
kind: conference
thesort: peerreviewed
peerreviewed: yes
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


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/qrs2019/christi2019evaluating.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/qrs2019/christi2019evaluating.bib "reference")


