---
published: true
title: Can Mutation Analysis be used for Evaluating Static Analysis Tools?
layout: post
comments: true
tags: mutation analysis, static analysis
categories: post
---

Can mutation analysis be used to evaluate the effectiveness (in finding bugs) of static analysis tools?
Mutation analysis is the premier technique in evaluating test suites and test generators which are used
for finding bugs, and it is effective in evaluating the quality of such tools by injecting artificial
faults (mutations) into the program. So, will this technique work against static analysis tools?

The issue is that, the mutations induced by mutation analysis is all static. So, technically, one can
have a static analysis tool that looks for mutations induced by the mutation analysis. Such a tool
will be 100% effective for the induced mutations but fail utterly with real world faults. So, what can
we do?

One extreme suggestion would be to _require a test case_  (both input as well as the expected output) that
can detect the mutant to count a mutant as detected. However, providing this would be very hard for most
pattern based static analysis tools. Hence, we need a better idea.

One (related) issue is that mutation analysis does not have the concept of false positives either. That is,
if some equivalent mutants are falsely claimed to be detectable, how do we penalize the tool?


At this point at least, it seems to be an open problem for mutation analysis.
