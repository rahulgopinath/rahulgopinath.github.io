---
layout: post
categories : publications
tagline: "."
tags : publication
e: Parser Directed Fuzzing
title: Parser Directed Fuzzing
authors:  Bjoern Mathis, Rahul Gopinath, Michael Mera, Alexander Kampmann, Matthias Hoeschele, Andreas Zeller
venue: ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

To be effective, software test generation needs to well cover the space of
possible inputs. Traditional fuzzing generates large numbers of random inputs,
which however are unlikely to contain keywords and other specific inputs of
non-trivial input languages. Constraint-based test generation solves conditions
of paths leading to uncovered code, but fails on programs with complex input
conditions because of path explosion.

In this paper, we present a test generation technique specifically directed at
input parsers. We systematically produce inputs for the parser and track
comparisons made; after every rejection, we satisfy the comparisons leading to
rejection. This approach effectively covers the input space: Evaluated on five
subjects, from CSV files to JavaScript, our pFuzzer prototype covers more tokens
than both random-based and constraint-based approaches, while requiring no
symbolic analysis and far fewer tests than random fuzzers.

This is an expansion of our [TR](https://arxiv.org/abs/1810.08289).


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3925727.svg)](https://doi.org/10.5281/zenodo.3925727)


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/pldi2019/mathis2019parser.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/pldi2019/mathis2019parser.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://www.slideshare.net/secret/iCJtAe8yn1EQ0g "presentation")

