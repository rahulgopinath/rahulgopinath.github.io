---
published: false
title: Foundations of Mutation Analysis
layout: post
---
This is an expansion on the implications of our [recent publication](http://rahul.gopinath.org/publications/#gopinath2014mutations) on the Competent Programmer Hypothesis.

A few definitions: A *fault* is a lexical problem within a program, which can lead to compilation error if the compiler catches it, or can lead to incorrect program if the compiler fails to catch it. An *error* is an incorrect state during the execution of a program which happens due to the execution passing through a *fault* (for our purposes -- there can be other causes of errors). When the *error* manifests in a detectable deviation in behavior of the program, we call the deviation a *failure*.

Mutation analysis relies on two fundamental assumptions --- *The Competent Programmer Hypothesis* and *The Coupling Effect*. The *Competent Programmer Hypothesis* states that programmers make simple mistakes, such that the new fixed program is not completely different, but within the neighborhood of the original. The *Coupling Effect* states that if a test case is able to identify faults in isolation, it will overwhelmingly be able to identify it even in the presence of other faults.


-- Problems with features
-- Lexical units.