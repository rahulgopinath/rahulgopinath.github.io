---
layout: page
title : Publications
header : Publications
group: navigation
weight: 2
menu: Publications
---
* [_On The Limits Of Mutation Reduction Strategies_](#gopinath2016on)<br/>
  Gopinath, Alipour, Ahmed, Jensen, Groce - ICSE, 2016

* [_How hard does mutation analysis have to be anyway?_](#gopinath2015how)<br/>
  Gopinath, Alipour, Ahmed, Jensen, Groce - ISSRE, 2015

* [_An Empirical Study of Design Degradation: How Software Projects Get Worse Over Time_](#ahmed2015an)<br/>
  Ahmed, Mannan, Gopinath, Jensen - ESEM, 2015

* [_Mutations: How close are they to real faults?_](#gopinath2014mutations)<br/>
  Gopinath, Jensen, Groce - ISSRE, 2014

* [_Coverage and Its Discontents_](#groce2014coverage)<br/>
  Groce, Alipour, Gopinath - Essays 2014

* [_MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_](#le2014mucheck)<br/>
  Le, Alipour, Gopinath, Groce -  ISSTA Tools, 2014

* [_Code coverage for suite evaluation by developers_](#gopinath2014code)<br/>
  Gopinath, Jensen, Groce - ICSE, 2014

* [_Explanations for Regular Expressions_](#erwig2012explanations)<br/>
  Erwig, Gopinath - FASE, 2012

---

#### <a name='gopinath2016on'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _On The Limits Of Mutation Reduction Strategies_ ICSE, 2016]()

Although mutation analysis is considered the best way to
evaluate the effectiveness of a test suite, hefty computational
cost often limits its use. To address this problem, various
mutation reduction strategies have been proposed, all seeking
to gain efficiency by reducing the number of mutants
while maintaining the representativeness of an exhaustive
mutation analysis. While research has focused on the
efficiency of reduction, the effectiveness of these strategies in
selecting representative mutants, and the limits in doing so
has not been investigated.

We investigate the practical limits to the effectiveness of
mutation reduction strategies, and provide a simple theoretical
framework for thinking about the absolute limits.
Our results show that the limit in effectiveness over random
sampling for real-world open source programs is 13.078%
(mean). Interestingly, there is no limit to the improvement
that can be made by addition of new mutation operators.

Given that this is the maximum that can be achieved with
perfect advance knowledge of mutation kills, what can be
practically achieved may be much worse. We conclude that
more effort should be focused on enhancing mutations than
removing operators in the name of selective mutation for
questionable benefit.

[Publication](/resources/icse2016/gopinath2016on.pdf) [Bib](/resources/icse2016/gopinath2016on.bib) [Data](http://eecs.osuosl.org/rahul/icse2016/)

#### <a name='gopinath2015how'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _How hard does mutation analysis have to be, anyway?_ ISSRE, 2015]()

Mutation analysis is considered the best method for
measuring the adequacy of test suites. However, the number of
test runs required for a full mutation analysis grows faster than
project size, which is not feasible for real-world software projects,
which often have more than a million lines of code. It is for
projects of this size, however, that developers most need a method
for evaluating the efficacy of a test suite. Various strategies have
been proposed to deal with the explosion of mutants. However,
these strategies at best reduce the number of mutants required to
a fraction of overall mutants, which still grows with program size.
Running, e.g., 5% of all mutants of a 2MLOC program usually
requires analyzing over 100,000 mutants. Similarly, while various
approaches have been proposed to tackle equivalent mutants,
none completely eliminate the problem, and the fraction of
equivalent mutants remaining is hard to estimate, often requiring
manual analysis of equivalence.

In this paper, we provide both theoretical analysis and
empirical evidence that a small constant sample of mutants yields
statistically similar results to running a full mutation analysis,
regardless of the size of the program or similarity between
mutants. We show that a similar approach, using a constant
sample of inputs can estimate the degree of stubbornness in
mutants remaining to a high degree of statistical confidence,
and provide a mutation analysis framework for Python that
incorporates the analysis of stubbornness of mutants.

[Publication](/resources/issre2015/gopinath2015howhard.pdf) [Bib](/resources/issre2015/gopinath2015howhard.bib) [Data](http://eecs.osuosl.org/rahul/issre15/)
[Presentation](/resources/issre2015/gopinath2015howhard.pptx) 

#### <a name='ahmed2015an'></a>[Ahmed, Mannan, Gopinath, Jensen: _An Empirical Study of Design Degradation: How Software Projects Get Worse Over Time_ ESEM 2015]()

Software decay is a key concern for large, long lived software
projects. Systems degrade over time as design and implementation compromises
and exceptions pile up. However, there has been little research quantifying
this decay, or understanding how software projects deal with this issue. While
the best approach to improve the quality of a project is to spend time
on reducing both software defects (bugs) and addressing design issues
(refactoring), we find that design issues are frequently ignored in favor of
fixing defects. We find that design issues have a higher chance of being fixed
in the early stages of a project, and that efforts to correct these stall as
projects mature and code bases grow leading to a build-up of design problems.
From studying a large set of open source projects, our research suggests that
while core contributors tend to fix design issues more often than non-core
contributors, there is no difference once the relative quantity of commits
is accounted for.

[Publication](/resources/esem2015/ahmed2015empirical.pdf) [Bib](/resources/esem2015/ahmed2015empirical.bib)

#### <a name='gopinath2014mutations'></a>[Gopinath, Jensen, Groce: _Mutations: How close are they to real faults?_ ISSRE 2014]()

Mutation analysis is often used to compare the effectiveness of different test suites or testing techniques. One of 
the main assumptions underlying this technique is the Competent Programmer Hypothesis, which proposes that programs are very 
close to a correct version, or that the difference between current and correct code for each fault is very small. 
Researchers have assumed on the basis of the Competent Programmer Hypothesis that the faults produced by mutation 
analysis are similar to real faults. While there exists some evidence that supports this assumption, these studies are based 
on analysis of a limited and potentially non-representative set of programs and are hence not conclusive. In this paper, we 
separately investigate the characteristics of bugfixes and other changes in a very large set of randomly selected projects using 
four different programming languages.  Our analysis suggests that a typical fault involves about three 
to four tokens, and is seldom equivalent to any traditional mutation operator. We also find the most frequently occurring 
syntactical patterns, and identify the factors that affect the real bug-fix change distribution. Our analysis suggests that different 
languages have different distributions, which in turn suggests that operators optimal in one language may not be optimal 
for others. Moreover, our results suggest that mutation analysis stands in need of better empirical support of the connection 
between mutant detection and detection of actual program faults in a larger body of real programs. 

[Publication](/resources/issre2014/gopinath2014mutations.pdf) [Bib](/resources/issre2014/gopinath2014mutations.bib) [Data](http://eecs.osuosl.org/rahul/issre2014/)
[Presentation](/resources/issre2014/gopinath2014mutations.pptx) 

#### <a name='groce2014coverage'></a>[Groce, Alipour, Gopinath: _Coverage and Its Discontents_ Essays 2014]()

Everyone wants to know one thing about a test suite: will it detect enough bugs? Unfortunately, in most settings that matter, answering this question directly is impractical or impossible. Software engineers and researchers therefore tend to rely on various measures of code coverage (where mutation testing is considered as a form of syntactic coverage). A long line of academic research efforts have attempted to determine whether relying on coverage as a substitute for fault detection is a reasonable solution to the problems of test suite evaluation. This essay argues that the profusion of coverage-related literature is in part a sign of an underlying uncertainty as to what exactly it is that measuring coverage should achieve, and how we would know if it can, in fact, achieve it. We propose some solutions, but the primary focus is to clarify the state of current confusions regarding this key problem for effective software testing. 

[Publication](/resources/splash2014/groce2014coverage.pdf) [Bib](/resources/splash2014/groce2014coverage.bib)

#### <a name='le2014mucheck'></a>[Le, Alipour, Gopinath, Groce: _MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ISSTA Tools 2014]()

This paper presents MuCheck, a mutation testing tool for Haskell programs. This is the first tool to be published (to our knowledge) that is explicitly oriented towards mutation testing for functional programs. MuCheck is a counterpart to the widely used QuickCheck random testing tool in fuctional programs, and can be used to evaluate the efficacy of QuickCheck property definitions. The tool implements mutation operators that are specifically designed for functional programs, and makes use of the type system of Haskell to achieve a more relevant set of mutants than otherwise possible. Mutation coverage is particularly valuable for functional programs due to highly compact code, referential transparency, and clean semantics, which make augmenting a test suite or specification based on surviving mutants a practical method for improved testing.

[Publication](/resources/issta2014/le2014mucheck.pdf) [Bib](/resources/issta2014/le2014mucheck.bib)

#### <a name='gopinath2014code'></a>[Gopinath, Jensen, Groce: _Code coverage for suite evaluation by developers_ ICSE 2014]()

One of the key challenges of developers testing code is determining a test suite's quality -- its ability to find faults. The most common approach is to use code coverage as a measure for test suite quality, and diminishing returns in coverage or high absolute coverage as a stopping rule. In testing research, suite quality is often evaluated by a suite's ability to kill mutants (artificially seeded potential faults). Determining which criteria best predict mutation kills is critical to practical estimation of test suite quality. Previous work has only used small sets of programs, and usually compares multiple suites for a single program. Practitioners, however, seldom compare suites --- they evaluate one suite. Using suites (both manual and automatically generated) from a large set of real-world open-source projects shows that evaluation results differ from those for suite-comparison: statement (not block, branch, or path) coverage predicts mutation kills best.

[Publication](/resources/icse2014/gopinath2014code.pdf) [Bib](/resources/icse2014/gopinath2014code.bib) [Data](http://eecs.osuosl.org/rahul/icse2014/)
[Presentation](/resources/icse2014/gopinath2014code.pptx) 

#### <a name='erwig2012explanations'></a>[Erwig, Gopinath: _Explanations for Regular Expressions_ FASE 2012]()

Regular expressions are widely used, but they are inherently hard to understand and (re)use, which is primarily due to the lack of abstraction mechanisms that causes regular expressions to grow large very quickly. The problems with understandability and usability are further compounded by the viscosity, redundancy, and terseness of the notation. As a consequence, many different regular expressions for the same problem are floating around, many of them erroneous, making it quite difficult to find and use the right regular expression for a particular problem. Due to the ubiquitous use of regular expressions, the lack of understandability and usability becomes a serious software engineering problem. In this paper we present a range of independent, complementary representations that can serve as explanations of regular expressions. We provide methods to compute those representations, and we describe how these methods and the constructed explanations can be employed in a variety of usage scenarios. In addition to aiding understanding, some of the representations can also help identify faults in regular expressions. Our evaluation shows that our methods are widely applicable and can thus have a significant impact in improving the practice of software engineering.

[Publication](/resources/fase2012/erwig2012explanations.pdf) [Bib](/resources/fase2012/erwig2012explanations.bib)
