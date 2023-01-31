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
type checking as a static analysis technique, we already have some evidence [^gopinath2017how] that it works well. Further, researchers already use mutation analysis [^araujo2016correlating] and fault injection [^ghaleb2020how] for evaluating the effectiveness of static analysis tools.
However, does it make sense to use mutation analysis
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
ineffective for real world faults. Indeed, false positives are one of the major
issues in static analysis. So, what can we do?

One extreme suggestion would be to _require a test case_  (both input as well as
the expected output) that can detect the mutant to count a mutant as detected.
However, providing this would be very much beyond most static
analysis tools (if we can do this, then the problem of false positives is resolved).
Hence, we need a better idea.

One way to do this is to try and lie. That is, ask the static analysis
framework whether the program itself is faulty. If it claims the program to
be faulty, then we either disbelieve the claim or fix the pattern. Say the
static analyzer claims the program not to be faulty, then we can produce
known equivalent mutants: For example, we could swap the order of non
dependent lines, or swap the operators in functions that does not ascribe
meaning to the argument order etc. If the static analyzer claims fault in
such equivalent mutants, then we know that static analyzer is lying. That is,
it has high false positive rate. This is the approach taken by
Parveen et al.[^parveen2020a]. They call such
mutants *benign*.

The unfortunate problem is that static analysis tools can again try to
detect such benigh mutants.

A third idea is to consider what static analysis tools accomplish. They reduce
the *degrees of freedom* of the program in that they limit in what ways a
program can change. So, perhaps this can be leveraged? The idea then is to
simply count the number of lexical mutation points in the program where *some*
specific value could be substituted. The difference between this and constant
mutation pattern is that we avoid concrete values that can be easily spotted
statically. That is, given two boolean variables `a` and `b`, we change 
`if a:` to `if b:` rather than to `if True:`. Count the *locations* where such
changes are possible. This can provide a truer picture about the capability of
a static analysis tool. In a similar way, we can also evaluate stronger type
systems (better type systems can make larger classes of bugs unrepresentable,
so we expect the degrees of freedom to reduce), as well as effectiveness of
language design by comparing the best implementations of similar algorithms
across different languages (an equivalent program with smaller number of mutation
points is better).

[^gopinath2017how]: Rahul Gopinath, Eric Walkingshaw "How Good are Your Types? Using Mutation Analysis to Evaluate the Effectiveness of Type Annotations" ICSTW Mutation, 2017 URL:<https://rahul.gopinath.org/resources/icst2017/gopinath2017how.pdf>

[^araujo2016correlating]: Cláudio A. Araujo,  Marcio E. Delamaro, Jose C. Maldonado and Auri M. R. Vincenzi "Correlating automatic static analysis and mutation testing: towards incremental strategies" Journal of Software Engineering Research and Development 2016 DOI:10.1186/s40411-016-0031-8 URL:<https://core.ac.uk/download/pdf/81636717.pdf>

[^ghaleb2020how]: Asem  Ghaleb, Karthik Pattabiraman "How effective are smart contract analysis tools? evaluating smart contract static analysis tools using bug injection ISSTA 2016 URL:<https://dl.acm.org/doi/abs/10.1145/3395363.3397385>

[^parveen2020a]: Sajeda Parveen; Manar H. Alalfi "A Mutation Framework for Evaluating Security Analysis Tools in IoT Applications" SANER 2020 URL:<https://ieeexplore.ieee.org/document/9054853>
