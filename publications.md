---
layout: page
title : Publications
header : Publications
group: navigation
weight: 3
---
{% include JB/setup %}

* [Le, Alipour, Gopinath, Groce _MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ISSTA Tools 2014](#le--alipour--gopinath--groce-mucheck--an-extensible-tool-for-mutation-testing-of-haskell-programs-issta-tools-2014)

* [Gopinath, Jensen, Groce: _Code coverage for suite evaluation by developers_ ICSE 2014: 72-82, 2014](#gopinath-jensen-groce-code-coverage-for-suite-evaluation-by-developers-icse-2014-72-82-2014)

* [Erwig, Gopinath: _Explanations for Regular Expressions_ FASE12, LNCS 7212, 394-408, 2012](#erwig-gopinath-explanations-for-regular-expressions-fase12-lncs-7212-394-408-2012)

---

### [Le, Alipour, Gopinath, Groce _MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ISSTA Tools 2014]()

This paper presents MuCheck, a mutation testing tool for Haskell programs. This is the first tool to be published (to our knowledge) that is explicitly oriented towards mutation testing for functional programs. MuCheck is a counterpart to the widely used QuickCheck random testing tool in fuctional programs, and can be used to evaluate the efficacy of QuickCheck property definitions. The tool implements mutation operators that are specifically designed for functional programs, and makes use of the type system of Haskell to achieve a more relevant set of mutants than otherwise possible. Mutation coverage is particularly valuable for functional programs due to highly compact code, referential transparency, and clean semantics, which make augmenting a test suite or specification based on surviving mutants a practical method for improved testing.

### [Gopinath, Jensen, Groce: _Code coverage for suite evaluation by developers_ ICSE 2014: 72-82, 2014]()

One of the key challenges of developers testing code is determining a test suite's quality -- its ability to find faults. The most common approach is to use code coverage as a measure for test suite quality, and diminishing returns in coverage or high absolute coverage as a stopping rule. In testing research, suite quality is often evaluated by a suite's ability to kill mutants (artificially seeded potential faults). Determining which criteria best predict mutation kills is critical to practical estimation of test suite quality. Previous work has only used small sets of programs, and usually compares multiple suites for a single program. Practitioners, however, seldom compare suites --- they evaluate one suite. Using suites (both manual and automatically generated) from a large set of real-world open-source projects shows that evaluation results differ from those for suite-comparison: statement (not block, branch, or path) coverage predicts mutation kills best.

### [Erwig, Gopinath: _Explanations for Regular Expressions_ FASE12, LNCS 7212, 394-408, 2012]()

Regular expressions are widely used, but they are inherently hard to understand and (re)use, which is primarily due to the lack of abstraction mechanisms that causes regular expressions to grow large very quickly. The problems with understandability and usability are further compounded by the viscosity, redundancy, and terseness of the notation. As a consequence, many different regular expressions for the same problem are floating around, many of them erroneous, making it quite difficult to find and use the right regular expression for a particular problem. Due to the ubiquitous use of regular expressions, the lack of understandability and usability becomes a serious software engineering problem. In this paper we present a range of independent, complementary representations that can serve as explanations of regular expressions. We provide methods to compute those representations, and we describe how these methods and the constructed explanations can be employed in a variety of usage scenarios. In addition to aiding understanding, some of the representations can also help identify faults in regular expressions. Our evaluation shows that our methods are widely applicable and can thus have a significant impact in improving the practice of software engineering.

