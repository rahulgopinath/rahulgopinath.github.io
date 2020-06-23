---
layout: post
categories : student
tagline: "."
tags : [student guillermoaguilar 2020]
e: Identifying Implied Assumptions in Test Suits
---

#### Masters Thesis

Thesis submission: Identifying Implied Assumptions in Test Suits

#### Abstract

Good test suits are hard to produce and maintain, and practitioners rely on the
usage of a variety of adequacy criteria to measure the quality of test suites.
Unfortunately, having an adequate test suit provides no guarantee that the suit
is complete, it could contain implied assumptions about characteristics of
inputs. Finding such implied assumptions could allow us to progressively improve
the test suites such that all implied assumptions are captured by the test
suite.

We present a novel technique for improving test suites. We first identify the
dynamic invariants in the test suite by examining relations between test inputs.
We then identify the real constraints in the input space explored using concolic
execution using the inputs from the test suite. The difference between these
constraints provides us with the constraints that were implied in the test
suite. Such constraints can then be included to the original test suite, or can
be lifted to system level to improve the quality of system tests.
