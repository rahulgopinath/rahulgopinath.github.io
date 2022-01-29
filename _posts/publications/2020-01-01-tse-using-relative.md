---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Using Relative Lines of Code to Guide Automated Test Generation for Python
title: Using Relative Lines of Code to Guide Automated Test Generation for Python
authors: Josie Holmes, Iftekhar Ahmed, Caius Brindescu, Rahul Gopinath, He Zhang, Alex Groce
venue: ACM Transactions on Software Engineering and Methodology (TOSEM)
kind: journal
thesort: peerreviewed
peerreviewed: yes
---


Raw lines of code (LOC) is a metric that does not, at first glance, seem extremely
useful for automated test generation. It is both highly language-dependent and not
extremely meaningful, semantically, within a language: one coder can produce the
same effect with many fewer lines than another. However, relative LOC, between
components of the same project, turns out to be a highly useful metric for automated
testing. In this paper, we make use of a heuristic based on LOC counts for tested
functions to dramatically improve the effectiveness of automated test generation.
This approach is particularly valuable in languages where collecting code coverage
data to guide testing has a very high overhead.  We apply the heuristic to property-based
Python testing using the TSTL (Template Scripting Testing Language) tool.
In our experiments, the simple LOC heuristic can improve branch and statement coverage
by large margins (often more than 20%, up to 40% or more), and improve fault detection
by an even larger margin (usually more than 75%, and up to 400% or more).
The LOC heuristic is also easy to combine with other approaches, and is comparable to,
and possibly more effective than, two well-established approaches for guiding random testing.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/tosem2020/holmes2020using.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/tosem2020/holmes2020using.bib "reference")

