---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Inducing Subtle Mutations with Program Repair
title: Inducing Subtle Mutations with Program Repair
authors: Florian Schwander, Rahul Gopinath, Andreas Zeller
venue: IEEE International Conference on Software Testing, Verification and Validation Workshop (ICSTW) Mutation
kind: workshop
thesort: peerreviewed
peerreviewed: yes
---

Mutation analysis is the gold standard for assessing the effectiveness of a
test suite to prevent bugs. It involves generating variants (mutants) of the
program under test, and checking whether the test suite detects the mutant.
A tester relies on the live mutants to decide what test cases to write for
improving the test suite effectiveness. However, while a majority of such
syntactic changes result in detectable semantic differences from the original,
it is, however, possible that such a change fails to induce a semantic change.
Such equivalent mutants can lead to wastage of manual effort.

We describe a novel technique that produces high-quality mutants while avoiding
the generation of equivalent mutants for input processors. Our idea is to
generate plausible, near correct inputs for the program, collect those rejected,
and generate variants that accept these rejected strings. Our technique allows
us to provide an enhanced set of mutants along with newly generated test cases
that kill them.

We evaluate our method on eight python programs and show that our technique
can generate new mutants that are both interesting for the developer and
guaranteed to be mortal.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icstw2021/schwander2021inducing.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icstw2021/schwander2021inducing.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/inducing-subtle-mutations-with-program-repair "presentation")
