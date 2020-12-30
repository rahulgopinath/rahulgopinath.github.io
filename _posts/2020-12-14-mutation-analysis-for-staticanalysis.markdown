---
published: true
title: Can Mutation Analysis be used for Evaluating Static Analysis Tools?
layout: post
comments: true
tags: mutation analysis, static analysis
categories: post
---

Can mutation analysis be used to evaluate the effectiveness (in finding bugs) of
static analysis tools?  Mutation analysis is the premier technique in evaluating
test suites and test generators which are used for finding bugs, and it is
effective in evaluating the quality of such tools by injecting artificial
faults (mutations) into the program.
So, will this technique work against static analysis tools? If one considers
type checking as a static analysis technique, we already have [some evidence](https://rahul.gopinath.org/publications/#gopinath2017how)
that it works well. However, does it make sense to use mutation analysis
for evaluating static analysis tools _in general_?

The impediment here is that mutations induced by mutation analysis is all
static.  So, technically, one can have a static analysis tool that looks for
mutations induced by the mutation analysis. Most of these mutants have
distinctive patterns (e.g. `if cond` is replaced by `if false`). Hence, this
is certainly doable.
This is compounded by the fact that mutation analysis does not have the concept
of false positives. That is, if some equivalent mutants are falsely claimed to
be killable, there is no penalty suffered by the tool.
Hence, a deceitful tool could simply claim every single evaluated mutant to
be detectable.
Such a tool will be 100% effective for the induced mutations but will be utterly
ineffective for real world faults. So, what can we do?

One extreme suggestion would be to _require a test case_  (both input as well as
the expected output) that can detect the mutant to count a mutant as detected.
However, providing this would be very hard for most pattern based static
analysis tools. Hence, we need a better idea.

One way to do this is to try and lie. That is, ask the static analysis
framework whether the program itself is faulty. If it claims the program to
be faulty, then we either disbelieve the claim or fix the pattern. Say the
static analyzer claims the program not to be faulty, then we can produce
known equivalent mutants: For example, we could swap the order of non
dependent lines, or swap the operators in functions that does not ascribe
meaning to the argument order etc. If the static analyzer claims fault in
such equivalent mutants, then we know that static analyzer is lying. That is,
it has high false positive rate.

So, in effect, if one is evaluating static analysis tools using mutation
analysis, one should start with a green state (no flagged faults in
the program under analysis or only known flagged faults). Next, introduce
equivalent mutants and check how many such mutants are claimed to be
faults. This provides the believability ratio of the static analysis tool.

