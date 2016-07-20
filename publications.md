---
layout: page
title : Publications
header : Publications
group: navigation
weight: 2
menu: Publications
---
<style type="text/css">
/*
My name.
*/
ul>li>p>em,ul>li>em {
  font-weight: 500;
  font-style: normal;
}
</style>


##### 2016

* [_Evaluating Non-Adequate Test-Case Reduction_](#alipour2016evaluating)<br/>
  Alipour, Shi, *Gopinath*, Marinov, Groce, Jensen - ASE, 2016

* [_Can Testedness be Effectively Measured?_](#ahmed2016can)<br/>
  Ahmed, *Gopinath*, Brindescu, Groce, Jensen - FSE, 2016

* [_Generating Focused Random Tests Using Directed Swarm Testing_](#alipour2016focused)<br/>
  Alipour, Groce, *Gopinath*, Christi - ISSTA, 2016

* [_Measuring Effectiveness of Mutant Sets_](#gopinath2016measuring)<br/>
  *Gopinath*, Alipour, Ahmed, Jensen, Groce - ICSTW Mutation, 2016

* [_Topsy-Turvy: A Smarter and Faster Parallelization of Mutation Analysis_](#gopinath2016topsy)<br/>
  *Gopinath*, Jensen, Groce - ICSE (Extended Abstract - Distinguished Award), 2016

* [_Does The Choice of Mutation Tool Matter?_](#gopinath2016does)<br/>
  *Gopinath*, Ahmed, Alipour, Jensen, Groce - SQJournal, 2016

* [_On The Limits Of Mutation Reduction Strategies_](#gopinath2016on)<br/>
  *Gopinath*, Alipour, Ahmed, Jensen, Groce - ICSE, 2016

##### 2015

* [_How hard does mutation analysis have to be anyway?_](#gopinath2015how)<br/>
  *Gopinath*, Alipour, Ahmed, Jensen, Groce - ISSRE, 2015

* [_An Empirical Study of Design Degradation: How Software Projects Get Worse Over Time_](#ahmed2015an)<br/>
  Ahmed, Mannan, *Gopinath*, Jensen - ESEM, 2015

##### 2014

* [_Mutations: How close are they to real faults?_](#gopinath2014mutations)<br/>
  *Gopinath*, Jensen, Groce - ISSRE, 2014

* [_Coverage and Its Discontents_](#groce2014coverage)<br/>
  Groce, Alipour, *Gopinath* - Essays 2014

* [_MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_](#le2014mucheck)<br/>
  Le, Alipour, *Gopinath*, Groce -  ISSTA Tools, 2014

* [_Code coverage for suite evaluation by developers_](#gopinath2014code)<br/>
  *Gopinath*, Jensen, Groce - ICSE, 2014

##### 2012

* [_Explanations for Regular Expressions_](#erwig2012explanations)<br/>
  Erwig, *Gopinath* - FASE, 2012

---

#### <a name='alipour2016evaluating'></a>[Alipour, Shi, Gopinath, Marinov, Groce: _Evaluating Non-Adequate Test-Case Reduction_ ASE, 2016]()

Given two test cases, one larger and one smaller, the smaller test case is preferred for many purposes. A smaller test case usually runs faster, is easier to understand, and is more convenient for debugging. However, smaller test cases also tend to cover less code and detect fewer faults than larger test cases. Whereas traditional research focused on reducing test suites while preserving code coverage, one line of recent work has introduced the idea of reducing individual test cases, rather than test suites, while still preserving code coverage. Another line of recent work has proposed non-adequately reducing test suites by not even preserving all the code coverage. This paper empirically evaluates a new combination of these ideas: non-adequate reduction of test cases, which allows for a wide range of trade-offs between test case size and fault detection.

Our study introduces and evaluates C%-coverage reduction (where a test case is reduced to retain at least C% of its original coverage) and N-mutant reduction (where a test case is reduced to kill at least N of the mutants it originally killed). We evaluate the reduction trade-offs with varying values of C and N for four real-world C projects: Mozilla’s SpiderMonkey JavaScript engine, the YAFFS2 flash file system, Grep, and Gzip. The results show that it is possible to greatly reduce the size of many test cases while still preserving much of their fault-detection capability.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/fse2016/alipour2016evaluating.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/fse2016/alipour2016evaluating.bib)

#### <a name='ahmed2016can'></a>[Ahmed, Gopinath, Brindescu, Groce, Jensen: _Can Testedness be Effectively Measured_ FSE, 2016]()

Among the major questions that a practicing tester faces are deciding where to
focus additional testing effort, and deciding when to stop testing. Test the
least-tested code, and stop when all code is well-tested, is a reasonable
answer. Many measures of "testedness" have been proposed; unfortunately, we do
not know whether these are truly effective.

In this paper we propose a novel evaluation of two of the most important and
widely-used measures of test suite quality. The first measure is statement
coverage, the simplest and best-known code coverage measure. The second measure
is mutation score, a supposedly more powerful, though expensive, measure.

We evaluate these measures using the actual criteria of interest: if a program
element is (by these measures) well tested at a given point in time, it should
require fewer future bug-fixes than a "poorly tested" element. If not, then it
seems likely that we are not effectively measuring testedness. Using a large
number of open source Java programs from Github and Apache, we show that both
statement coverage and mutation score have only a weak negative correlation with
bug-fixes. Despite the lack of strong correlation, there are statistically and
practically significant differences between program elements for various binary
criteria. Program elements (other than classes) covered by any test case see
about half as many bug-fixes as those not covered, and a similar line can be
drawn for mutation score thresholds. Our results have important implications for
both software engineering practice and research evaluation.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/fse2016/ahmed2016can.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/fse2016/ahmed2016can.bib)


#### <a name='alipour2016focused'></a>[Alipour, Groce, Gopinath, Christi: _Generating Focused Random Tests Using Directed Swarm Testing_ ISSTA, 2016]()

Random testing can be a powerful and scalable method for finding faults
in software. However, sophisticated random testers usually test a whole
program, not individual components. Writing random testers for individual
components of complex programs may require unreasonable effort. In this paper
we present a novel method, directed swarm testing, that uses statistics and
a variation of random testing to produce random tests that focus on only
part of a program, increasing the frequency with which tests cover the
targeted code. We demonstrate the effectiveness of this technique using
real-world programs and test systems (the YAFFS2 file system, GCC, and
Mozilla SpiderMonkey JavaScript engine), and discuss various strategies for
directed swarm testing. The best strategies can improve coverage frequency for
targeted code by a factor ranging from 1.1-4.5x on average, and from nearly
3x to nearly 9x in the best case. For YAFFS2, directed swarm testing never
decreased coverage, and for GCC and SpiderMonkey coverage increased for over
99% and 73% of targets, respectively, using the best strategies. Directed
swarm testing improves detection rates for real SpiderMonkey faults, when
the code in the introducing commit is targeted. This lightweight technique
is applicable to existing industrial-strength random testers.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/issta2016/alipour2016focused.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/issta2016/alipour2016focused.bib)


#### <a name='gopinath2016measuring'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _Measuring Effectiveness of Mutant Sets_ ICSTW, 2016]()

Redundant mutants, where multiple mutants end 
up producing same the semantic variant of the program is a major 
problem in mutation analysis, and a measure of effectiveness is 
an essential tool for evaluating mutation tools, new operators, 
and reduction techniques. Previous research suggests using size 
of disjoint mutant set as an effectiveness measure. 

We start from a simple premise: That test suites need to be 
judged on both the number of unique variations in specifications 
they detect (as variation measure), and also on how good they 
are in detecting harder to find bugs (as a measure of subtlety). 
Hence, any set of mutants should to be judged on how best they 
allow these measurements. 

We show that the disjoint mutant set has two major inadequacies 
— the single variant assumption and the large test suite 
assumption when used as a measure of effectiveness in variation, 
which stems from its reliance on minimal test suites, and we show 
that when used to emulate hard to find bugs (as a measure of 
subtlety), it discards useful mutants. 

We propose two alternative measures, one oriented toward 
the measure of effectiveness in variation and not vulnerable to 
either single variant assumption, or to large test suite assumption 
and the other towards effectiveness in subtlety, and provide a 
benchmark of these measures using diverse tools.

*Updates*: The terminology used in this paper is not completely correct.
The *minimal mutants* are different from *disjoint mutants*. The
*disjoint mutants* are actually *surface mutants*.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/icst2016/gopinath2016measuring.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/icst2016/gopinath2016measuring.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](http://eecs.osuosl.org/rahul/icst2016/)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/measuring-effectiveness-of-mutant-sets)

#### <a name='gopinath2016topsy'></a>[Gopinath, Jensen, Groce: _Topsy-Turvy: A Smarter and Faster Parallelization of Mutation Analysis_ ICSE (Extended Abstract), 2016]()

Mutation analysis is an effective, if computationally expensive, technique
that allows practitioners to accurately evaluate the quality of their test
suites.  To reduce the time and cost of mutation analysis, researchers have
looked at parallelizing mutation runs --- running multiple mutated versions of
the program in parallel, and running through the tests in sequence on each mutated program
until a bug is found. While an improvement over sequential execution
of mutants and tests, this technique carries a significant
overhead cost due to its redundant execution of unchanged code paths. In this
paper we propose a novel technique (and its implementation) which
parallelizes the test runs rather than the mutants, forking mutants from a
single program execution at the point of invocation, which reduces 
redundancy. We show that our
technique can lead to significant efficiency improvements and cost
reductions.

*Updates*: Part of our concept is similar to the split-stream execution of
mutants mentioned by Offutt et. al.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/icse2016/gopinath2016topsy.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/icse2016/gopinath2016topsy.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](http://eecs.osuosl.org/rahul/icse2016/)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/topsy-turvy-a-smarter-and-faster-parallelization-of-mutation-analysis)

#### <a name='gopinath2016does'></a>[Gopinath, Ahmed, Alipour, Jensen, Groce: _Does the Choice of Mutation Tool Matter?_ Software Quality Journal, 2016]()

Mutation analysis is the primary means of evaluating the quality of
test suites, though it suffers from inadequate standardization. Mutation
analysis tools vary based on language, when mutants are generated (phase
of compilation), and target audience. Mutation tools rarely implement the
complete set of operators proposed in the literature, and most implement at
least a few domain-specific mutation operators. Thus different tools may not
always agree on the mutant kills of a test suite, and few criteria exist
to guide a practitioner in choosing a tool, or a researcher in comparing
previous results. We investigate an ensemble of measures such as traditional
difficulty of detection, strength of minimal sets, diversity of mutants,
as well as the information carried by the mutants produced , to evaluate
the efficacy of mutant sets. By these measures, mutation tools rarely agree,
often with large differences, and the variation due to project, even after
accounting for difference due to test suites, is significant. However,
the mean difference between tools is very small indicating that no single
tool consistently skews mutation scores high or low for all projects. These
results suggest that research using a single tool, a small number of projects,
or small increments in mutation score may not yield reliable results. There
is a clear need for greater standardization of mutation analysis; we propose
one approach for such a standardization.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/sqj2016/gopinath2016does.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/sqj2016/gopinath2016does.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](http://eecs.osuosl.org/rahul/sqj2016/)

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

<!--script async class="speakerdeck-embed" data-id="6c0a81985e9c4f1cbd153b5a7ae60603" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/icse2016/gopinath2016on.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/icse2016/gopinath2016on.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](https://dx.doi.org/10.17605/OSF.IO/H5DCY)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/on-the-limits-of-mutation-reduction-strategies)

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

<!--script async class="speakerdeck-embed" data-id="3a16618236ad4f91b253a9f70b3cbe9b" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/issre2015/gopinath2015howhard.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/issre2015/gopinath2015howhard.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](https://dx.doi.org/10.17605/OSF.IO/MYDH2)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/how-hard-does-mutation-analysis-have-to-be-anyway)

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

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/esem2015/ahmed2015empirical.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/esem2015/ahmed2015empirical.bib)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/ahmedi/an-empirical-study-of-design-degradation-how-software-projects-get-worse-over-time) 

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

<!--script async class="speakerdeck-embed" data-id="5da07deb69d7421995908f629c055ace" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/issre2014/gopinath2014mutations.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/issre2014/gopinath2014mutations.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](https://dx.doi.org/10.17605/OSF.IO/ENZQK)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/mutations-how-close-are-they-to-real-faults)

#### <a name='groce2014coverage'></a>[Groce, Alipour, Gopinath: _Coverage and Its Discontents_ Essays 2014]()

Everyone wants to know one thing about a test suite: will it detect enough bugs? Unfortunately, in most settings that matter, answering this question directly is impractical or impossible. Software engineers and researchers therefore tend to rely on various measures of code coverage (where mutation testing is considered as a form of syntactic coverage). A long line of academic research efforts have attempted to determine whether relying on coverage as a substitute for fault detection is a reasonable solution to the problems of test suite evaluation. This essay argues that the profusion of coverage-related literature is in part a sign of an underlying uncertainty as to what exactly it is that measuring coverage should achieve, and how we would know if it can, in fact, achieve it. We propose some solutions, but the primary focus is to clarify the state of current confusions regarding this key problem for effective software testing. 

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/splash2014/groce2014coverage.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/splash2014/groce2014coverage.bib)

#### <a name='le2014mucheck'></a>[Le, Alipour, Gopinath, Groce: _MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ISSTA Tools 2014]()

This paper presents MuCheck, a mutation testing tool for Haskell programs. This is the first tool to be published (to our knowledge) that is explicitly oriented towards mutation testing for functional programs. MuCheck is a counterpart to the widely used QuickCheck random testing tool in fuctional programs, and can be used to evaluate the efficacy of QuickCheck property definitions. The tool implements mutation operators that are specifically designed for functional programs, and makes use of the type system of Haskell to achieve a more relevant set of mutants than otherwise possible. Mutation coverage is particularly valuable for functional programs due to highly compact code, referential transparency, and clean semantics, which make augmenting a test suite or specification based on surviving mutants a practical method for improved testing.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/issta2014/le2014mucheck.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/issta2014/le2014mucheck.bib)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/alipourm/mucheck-an-extensible-tool-for-mutation-testing-of-haskell-programs)

#### <a name='gopinath2014code'></a>[Gopinath, Jensen, Groce: _Code coverage for suite evaluation by developers_ ICSE 2014]()

One of the key challenges of developers testing code is determining a test suite's quality -- its ability to find faults. The most common approach is to use code coverage as a measure for test suite quality, and diminishing returns in coverage or high absolute coverage as a stopping rule. In testing research, suite quality is often evaluated by a suite's ability to kill mutants (artificially seeded potential faults). Determining which criteria best predict mutation kills is critical to practical estimation of test suite quality. Previous work has only used small sets of programs, and usually compares multiple suites for a single program. Practitioners, however, seldom compare suites --- they evaluate one suite. Using suites (both manual and automatically generated) from a large set of real-world open-source projects shows that evaluation results differ from those for suite-comparison: statement (not block, branch, or path) coverage predicts mutation kills best.

<!--script async class="speakerdeck-embed" data-id="640fad3e1a254985a10da2792866b675" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/icse2014/gopinath2014code.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/icse2014/gopinath2014code.bib)
[<i class="fa fa-database fa-lg" aria-hidden="true"></i>](https://dx.doi.org/10.17605/OSF.IO/K7JHU)
[<i class="fa fa-desktop" aria-hidden="true"></i>](https://speakerdeck.com/rahulgopinath/test-suite-evaluation-for-fun-and-profit)

#### <a name='erwig2012explanations'></a>[Erwig, Gopinath: _Explanations for Regular Expressions_ FASE 2012]()

Regular expressions are widely used, but they are inherently hard to understand and (re)use, which is primarily due to the lack of abstraction mechanisms that causes regular expressions to grow large very quickly. The problems with understandability and usability are further compounded by the viscosity, redundancy, and terseness of the notation. As a consequence, many different regular expressions for the same problem are floating around, many of them erroneous, making it quite difficult to find and use the right regular expression for a particular problem. Due to the ubiquitous use of regular expressions, the lack of understandability and usability becomes a serious software engineering problem. In this paper we present a range of independent, complementary representations that can serve as explanations of regular expressions. We provide methods to compute those representations, and we describe how these methods and the constructed explanations can be employed in a variety of usage scenarios. In addition to aiding understanding, some of the representations can also help identify faults in regular expressions. Our evaluation shows that our methods are widely applicable and can thus have a significant impact in improving the practice of software engineering.

[<i class="fa fa-book fa-lg" aria-hidden="true"></i>](/resources/fase2012/erwig2012explanations.pdf)
[<i class="fa fa-bookmark-o fa-lg" aria-hidden="true"></i>](/resources/fase2012/erwig2012explanations.bib)


<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-74302125-1', 'auto');
  ga('send', 'pageview');

</script>
