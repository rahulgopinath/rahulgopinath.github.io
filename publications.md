---
layout: publications
title : Publications
header : Publications
group: navigation
weight: 2
menu: Publications
---

## Peer Reviewed Publications

##### 2020

* [_Revisiting the Relationship between Fault Detection, Test Adequacy Criteria, and Test Set Size_](#chen2020revisiting)<br/>
  Chen, *Gopinath*, Tadakamalla, Ernst, Holmes, Fraser, Ammann, Just, ASE, 2020

* [_Mining Input Grammars from Dynamic Control Flow_](#gopinath2020mining)<br/>
  *Gopinath*, Mathis, Zeller, FSE, 2020

* [_Abstracting Failure Inducing Inputs_](#gopinath2020abstracting)<br/>
  *Gopinath*, Kampmann, Havrikov, Soremekun, Zeller, ISSTA, 2020

* [_Learning Input Tokens for Effective Fuzzing_](#mathis2020learning)<br/>
  Mathis, *Gopinath*, Zeller, ISSTA, 2020

* [_Using Relative Lines of Code to Guide Automated Test Generation for Python_](#ahmed2020using)<br/>
  Ahmed, Holmes, Brindescu, *Gopinath*, Zhang, Groce, TOSEM, 2020


##### 2019

* [_Parser-Directed Fuzzing_](#mathis2019parser)<br/>
  Mathis, *Gopinath*, Mera, Kampmann, Höschele, Zeller, PLDI, 2019

* [_Evaluating Fault Localization for Resource Adaptation via Test-based
Software Modification_](#christi2019evaluating)<br/>
  Christi, Groce, *Gopinath*, QRS, 2019

##### 2018

* [_If You Can't Kill a Supermutant, You Have a Problem_](#gopinath2018if)<br/>
  *Gopinath*, Mathis, Zeller, ICSTW Mutation, 2018

##### 2017

* [_Resource Adaptation via Test-Based Software Minimization_](#christi2017resource)<br/>
  Christi, Groce, *Gopinath*, SASO, 2017

* [_Mutation Reduction Strategies Considered Harmful_](#gopinath2017mutation)<br/>
  *Gopinath*, Ahmed, Alipour, Jensen, Groce, IEEE Transactions on Reliability, 2017

* [_How Good are Your Types? Using Mutation Analysis to Evaluate the Effectiveness of Type Annotations_](#gopinath2017how)<br/>
  *Gopinath*, Walkingshaw, ICSTW Mutation (Best Presentation Award), 2017

* [_The Theory of Composite Faults_](#gopinath2017the)<br/>
  *Gopinath*, Jensen, Groce - ICST, 2017

##### 2016

* [_Evaluating Non-Adequate Test-Case Reduction_](#alipour2016evaluating)<br/>
  Alipour, Shi, *Gopinath*, Marinov, Groce - ASE, 2016

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

* [_Mutation Testing of Functional Programming Languages_](#le2014mutation)<br/>
  Le, Alipour, *Gopinath*, Groce -  ICSTW Mutation, 2014

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



## Technical Reports

* [_Inferring Input Grammars from Dynamic Control Flow_](#gopinath2019inferring)<br/>
   *Gopinath*, *Mathis*, *Zeller*, 2019

* [_Building Fast Fuzzers_](#gopinath2019building)<br/>
  *Gopinath*, Zeller, 2019


* [_Sample-Free Learning of Input Grammars for Comprehensive Software Fuzzing_](#gopinath2018sample)<br/>
  *Gopinath*, Mathis, Hoschele, Kampmann, Zeller, 2018


## Thesis

* [_On the Limits of Mutation Analysis_](#gopinath2017on)<br/>
  *Gopinath*, PhD Thesis, 2017

## Books

* [Generating Software Tests -- Breaking Software for Fun and Profit](https://www.fuzzingbook.org) <br/>
  Zeller, *Gopinath*, Böhme, Fraser, Holler, 2019

#### <a id='gopinath2020mining'></a>[Gopinath, Mathis, Zeller: _Mining Input Grammars from Dynamic Control Flow_ FSE, 2020]()

One of the key properties of a program is its input specification. Having a
formal input specification can be critical in fields such as vulnerability
analysis, reverse engineering, software testing, clone detection, or
refactoring. Unfortunately, accurate input specifications for typical programs
are often unavailable or out of date.

In this paper, we present a general algorithm that takes a program and a small
set of sample inputs and automatically infers a readable context-free grammar
capturing the input language of the program. We infer the syntactic input
structure only by observing access of input characters at different locations of
the input parser. This works on all stack based recursive descent input parsers,
including parser combinators, and works entirely without program specific
heuristics. Our Mimid prototype produced accurate and readable grammars for a
variety of evaluation subjects, including complex languages such as JSON,
TinyC, and JavaScript.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/fse2020/gopinath2020mining.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/fse2020/gopinath2020mining.bib)

#### <a id='chen2020revisiting'></a>[Chen, Gopinath, Tadakamalla, Ernst, Holmes, Fraser, Ammann, Just: _Revisiting the Relationship between Fault Detection, Test Adequacy Criteria, and Test Set Size_ ASE, 2020]()

The research community has long recognized a complex interrelationship between test set size, test adequacy criteria, and test effectiveness in terms of fault detection. However, there is substantial confusion about the role and importance of controlling for test set size when assessing and comparing test adequacy criteria. This paper makes the following contributions: (1) A review of contradictory analyses of the relationship between fault detection, test suite size, and test adequacy criteria. Specifically, this paper addresses the supposed contradiction of prior work and explains why test suite size is neither a confounding variable, as previously suggested,nor an independent variable that should be experimentally manipulated. (2) An explication and discussion of the experimental design and sampling strategies of prior work, together with a discussion of conceptual and statistical problems, and specific guidelines for future work. (3) A methodology for comparing test-adequacy criteria on an equal basis, which accounts for test suite size by treating it as a covariate. (4) An empirical evaluation that compares the effectiveness of coverage-based and mutation-based testing to one another and random testing. Additionally, this paper proposes probabilistic coupling, a methodology for approximating the representativeness of a set of test goals for a given set of real faults

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ase2020/chen2020revisiting.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ase2020/chen2020revisiting.bib)


#### <a id='gopinath2020abstracting'></a>[Gopinath, Kampmann, Havrikov, Soremekun, Zeller: _Abstracting Failure Inducing Inputs_ ISSTA, 2020]()
A program fails.  Under which circumstances does the failure occur?  Starting
with a single failure-inducing input ("The input ((4)) fails") and an input
grammar, the DDSET algorithm uses systematic tests to automatically generalize
the input to an abstract failure inducing input that contains both (concrete)
terminal symbols and (abstract) nonterminal symbols from the grammar---for
instance, "((&lt;expr&gt;))", which represents any expression &lt;expr&gt; in double
parentheses.  Such an abstract failure inducing input can be used
1. as a debugging diagnostic, characterizing the circumstances under which a
failure occurs ("The error occurs whenever an expression is enclosed in
double parentheses"); 2. as a producer of additional failure-inducing tests to
help design and validate fixes and repair candidates ("The inputs ((1)), ((3 * 4)),
and many more also fail").
In its evaluation on real-world bugs in JavaScript, Clojure, Lua, and Coreutils,
DDSET's abstract failure inducing inputs provided to-the-point diagnostics, and
precise producers.

**Note:**
As of now, we check each abstraction independently of others, and then merge them which necessitates isolation later. An alternative route is to simply accumulate abstractions as your find them, and when generating, regenerate each abstract node that you have accumulated. With this, we can be sure that each node that we mark as abstract is truly abstract. A problem here is that of semantic validity. That is, if say the first abstraction has only 0.5 chance of producing a valid input, and the next abstraction candidate has again only 0.5 chance of producing a valid input, combining them together will reduce the probability of valid input in any generation to 0.25, and as abstractions accumulate, the probability of generating semantically valid inputs drop. Hence, we instead identify them independently and later merge them, with the trade off being a later isolation step.

Another difference is that during isolation we leave every possibly causative part intact. That is, if A or B is necessary for fault reproduction, we leave both A and B as concrete. A user may instead change it to leave either A or B as concrete.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3895797.svg)](https://doi.org/10.5281/zenodo.3895797)

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2020/gopinath2020abstracting.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2020/gopinath2020abstracting.bib)

#### <a id='mathis2020learning'></a>[Mathis, Gopinath, Zeller: _Learning Input Tokens for Effective Fuzzing_ ISSTA, 2020]()

Modern fuzzing tools like AFL operate at a lexical level: They explore the input
space of tested programs one byte after another.  For inputs with complex
syntactical properties, this is very inefficient, as keywords and other tokens
have to be composed one character at a time. Fuzzers thus allow to specify
dictionaries listing possible tokens the input can be composed from; such
dictionaries speed up fuzzers dramatically. Also, fuzzers make use of dynamic
tainting to track input tokens and infer values that are expected in the input
validation phase. Unfortunately, such tokens are usually implicitly converted to
program specific values which causes a loss of the taints attached to the input
data in the lexical phase. In this paper we present a technique to extend
dynamic tainting to not only track explicit data flows but also taint implicitly
converted data without suffering from taint explosion. This extension makes it
possible to augment existing techniques and automatically infer a set of
tokens and seed inputs for the input language of a program given nothing but the
source code.  Specifically targeting the lexical analysis of an input processor,
our LFuzzer test generator systematically explores branches of the lexical
analysis, producing a set of tokens that fully cover all decisions seen.
The resulting set of tokens can be directly used as a dictionary for fuzzing.
Along with the token extraction seed inputs are generated which give further
fuzzing processes a head start. In our experiments, the LFuzzer-AFL combination
achieves up to 17% more coverage on complex input formats like JSON, Lisp,
TinyC, and JS compared to AFL.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2020/mathis2020learning.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2020/mathis2020learning.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://www.slideshare.net/BjrnMathis/lfuzzer-learning-input-tokens-for-effective-fuzzing-237085021)

#### <a id='holmes2020using'></a>[Holmes, Brindescu, Gopinath, Zhang, Groce: _Using Relative Lines of Code to Guide Automated Test Generation for Python_ TOSEM, 2020]()

Raw lines of code (LOC) is a metric that does not, at first glance, seem extremely
useful for automated test generation. It is both highly language-dependent and not
extremely meaningful, semantically, within a language: one coder can produce the
same effect with many fewer lines than another. However, relative LOC, between
components of the same project, turns out to be a highly useful metric for automated
testing. In this paper, we make use of a heuristic based on LOC counts for tested
functions to dramatically improve the effectiveness of automated test generation.
This approach is particularly valuable in languages where collecting code coverage
data to guide testing has a very high overhead.  We apply the heuristic to property-based
Python testing using the TSTL (Template Scripting Testing Language) tool.
In our experiments, the simple LOC heuristic can improve branch and statement coverage
by large margins (often more than 20%, up to 40% or more), and improve fault detection
by an even larger margin (usually more than 75%, and up to 400% or more).
The LOC heuristic is also easy to combine with other approaches, and is comparable to,
and possibly more effective than, two well-established approaches for guiding random testing.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/tosem2020/holmes2020using.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/tosem2020/holmes2020using.bib)

#### <a id='mathis2019parser'></a>[Mathis, Gopinath, Mera, Kampmann, Höschele, Zeller: _Parser Directed Fuzzing_ PLDI, 2019]()

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


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/pldi2019/mathis2019parser.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/pldi2019/mathis2019parser.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://www.slideshare.net/secret/iCJtAe8yn1EQ0g)

#### <a id='christi2019evaluating'></a>[Christi, Groce, Gopinath: _Evaluating Fault Localization for Resource Adaptation via Test-based Software Modification_  QRS, 2019]()

Building software systems that adapt to changing resource environments
is challenging: developers cannot anticipate all future situations
that a software system may face, and even if they could, the effort
required to handle such situations would often be too onerous for
practical purposes. We propose a novel approach to allow a system to
generate resource usage adaptations: use delta-debugging to generate
versions of software systems that are reduced in size because they no
longer have to satisfy all tests in the software's test suite. Many
such variations will, while retaining core system functionality, use
fewer resources. We describe an tool for computing such adaptations,
based on our notion that labeled subsets of a test suite can be used
to conveniently describe possible relaxations of system
specifications. Using the NetBeans IDE, we demonstrate that even
without additional infrastructure or heuristics, our approach is
capable of quickly and cleanly removing a program's undo
functionality, significantly reducing its memory use, with no more
effort than simply labeling three test cases as undo-related.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/qrs2019/christi2019evaluating.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/qrs2019/christi2019evaluating.bib)


#### <a id='gopinath2019inferring'></a>[Gopinath, Mathis, Zeller: _Inferring Input Grammars from Dynamic Control Flow_ 2019]()

A program is characterized by its input model, and a formal input model can be of use in diverse areas including vulnerability analysis, reverse engineering, fuzzing and software testing, clone detection and refactoring. Unfortunately, input models for typical programs are often unavailable or out of date. While there exist algorithms that can mine the syntactical structure of program inputs, they either produce unwieldy and incomprehensible grammars, or require heuristics that target specific parsing patterns.
In this paper, we present a general algorithm that takes a program and a small set of sample inputs and automatically infers a readable context-free grammar capturing the input language of the program. We infer the syntactic input structure only by observing access of input characters at different locations of the input parser. This works on all program stack based recursive descent input parsers, including PEG and parser combinators, and can do entirely without program specific heuristics. Our Mimid prototype produced accurate and readable grammars for a variety of evaluation subjects, including expr, URLparse, and microJSON. 

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/1912.05937)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2019/gopinath2019inferring.bib)


#### <a id='gopinath2019building'></a>[Gopinath, Zeller: _Building Fast Fuzzers_ 2019]()

Fuzzing is one of the key techniques for evaluating the robustness of programs against attacks. Fuzzing has to be effective in producing inputs that cover functionality and find vulnerabilities. But it also has to be efficient in producing such inputs quickly. Random fuzzers are very efficient, as they can quickly generate random inputs; but they are not very effective, as the large majority of inputs generated is syntactically invalid. Grammar-based fuzzers make use of a grammar (or another model for the input language) to produce syntactically correct inputs, and thus can quickly cover input space and associated functionality. Existing grammar-based fuzzers are surprisingly inefficient, though: Even the fastest grammar fuzzer Dharma still produces inputs about a thousand times slower than the fastest random fuzzer. So far, one can have an effective or an efficient fuzzer, but not both.

In this paper, we describe how to build fast grammar fuzzers from the ground up, treating the problem of fuzzing from a programming language implementation perspective. Starting with a Python textbook approach, we adopt and adapt optimization techniques from functional programming and virtual machine implementation techniques together with other novel domain-specific optimizations in a step-by-step fashion. In our F1 prototype fuzzer, these improve production speed by a factor of 100--300 over the fastest grammar fuzzer Dharma. As F1 is even 5--8 times faster than a lexical random fuzzer, we can find bugs faster and test with much larger valid inputs than previously possible. 

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/1911.07707)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2019/gopinath2019building.bib)


#### <a id='gopinath2018sample'></a>[Gopinath, Mathis, Hoschele, Kampmann, Zeller: _Sample-Free Learning of Input Grammars for Comprehensive Software Fuzzing_ 2018]()

Quality of software test suites can be effectively and accurately measured using mutation analysis. Traditional mutation involves seeding first and sometimes higher order faults into the program, and evaluating each for detection. However, traditional mutants are often heavily redundant, and it is often desirable to produce the complete matrix of test cases vs mutants detected by each. Unfortunately, even the traditional mutation analysis has a heavy computational footprint due to the requirement of independent evaluation of each mutant by the complete test suite, and consequently the cost of evaluation of complete kill matrix is exorbitant.

We present a novel approach of combinatorial evaluation of multiple mutants at the same time that can generate the complete mutant kill matrix with lower computational requirements.

Our approach also has the potential to reduce the cost of execution of traditional mutation analysis especially for test suites with weak oracles such as machine-generated test suites, while at the same time liable to only a linear increase in the time taken for mutation analysis in the worst case.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/1810.08289)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/arxiv2018/gopinath2018learning.bib)


#### <a id='gopinath2018if'></a>[Gopinath, Mathis, Zeller: _If You Can't Kill a Supermutant, You Have a Problem_ ICSTW Mutation, 2018]()

Quality of software test suites can be effectively and accurately measured using mutation analysis. Traditional mutation involves seeding first and sometimes higher order faults into the program, and evaluating each for detection. However, traditional mutants are often heavily redundant, and it is often desirable to produce the complete matrix of test cases vs mutants detected by each. Unfortunately, even the traditional mutation analysis has a heavy computational footprint due to the requirement of independent evaluation of each mutant by the complete test suite, and consequently the cost of evaluation of complete kill matrix is exorbitant.

We present a novel approach of combinatorial evaluation of multiple mutants at the same time that can generate the complete mutant kill matrix with lower computational requirements.

Our approach also has the potential to reduce the cost of execution of traditional mutation analysis especially for test suites with weak oracles such as machine-generated test suites, while at the same time liable to only a linear increase in the time taken for mutation analysis in the worst case.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icstw2018/gopinath2018if.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icstw2018/gopinath2018if.bib)
[<em class="fa fa-desktop"
aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/if-you-cant-kill-a-supermutant-you-have-a-problem)

#### <a id='christi2017resource'></a>[Christi, Groce, Gopinath: _Resource Adaptation via Test-Based Software Minimization_  SASO, 2017]()

Building software systems that adapt to changing resource environments
is challenging: developers cannot anticipate all future situations
that a software system may face, and even if they could, the effort
required to handle such situations would often be too onerous for
practical purposes. We propose a novel approach to allow a system to
generate resource usage adaptations: use delta-debugging to generate
versions of software systems that are reduced in size because they no
longer have to satisfy all tests in the software's test suite. Many
such variations will, while retaining core system functionality, use
fewer resources. We describe an tool for computing such adaptations,
based on our notion that labeled subsets of a test suite can be used
to conveniently describe possible relaxations of system
specifications. Using the NetBeans IDE, we demonstrate that even
without additional infrastructure or heuristics, our approach is
capable of quickly and cleanly removing a program's undo
functionality, significantly reducing its memory use, with no more
effort than simply labeling three test cases as undo-related.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/saso2017/christi2017resource.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/saso2017/christi2017resource.bib)


#### <a id='gopinath2017on'></a>[Gopinath: _On the Limits of Mutation Analysis_ Ph.D. Thesis , 2017]()

Mutation analysis is the gold standard for evaluating test-suite adequacy. It
involves exhaustive seeding of all small faults in a program and evaluating the
effectiveness of test suites in detecting these faults. Mutation analysis
subsumes numerous structural coverage criteria, approximates fault detection
capability of test suites, and the faults produced by mutation have been shown
to be similar to the real faults. This dissertation looks at the effectiveness
of mutation analysis in terms of its ability to evaluate the quality of test
suites, and how well the mutants generated emulate real faults. The
effectiveness of mutation analysis hinges on its two fundamental hypotheses:
The competent programmer hypothesis, and the coupling effect. The competent
programmer hypothesis provides the model for the kinds of faults that mutation
operators emulate, and the coupling effect provides guarantees on the ratio of
faults prevented by a test suite that detects all simple faults to the complete
set of possible faults. These foundational hypotheses determine the limits of
mutation analysis in terms of the faults that can be prevented by a mutation
adequate test suite. Hence, it is important to understand what factors affect
these assumptions, what kinds of faults escape mutation analysis, and what
impact interference between faults (coupling and masking) have. A secondary
concern is the computational footprint of mutation analysis. Mutation analysis
requires the evaluation of numerous mutants, each of which potentially requires
complete test runs to evaluate. Numerous heuristic methods exist to reduce the
number of mutants that need to be evaluated. However, we do not know the effect
of these heuristics on the quality of mutants thus selected. Similarly, whether
the possible improvement in representation using these heuristics are subject
to any limits have also not been studied in detail. Our research investigates
these fundamental questions in mutation analysis both empirically and
theoretically. We show that while a majority of faults are indeed small, and
hence within a finite neighborhood of the correct version, their size is larger
than typical mutation operators. We show that strong interactions between
simple faults can produce complex faults that are semantically unrelated to the
component faults, and hence escape first order mutation analysis. We further
validate the coupling effect for a large number of real-world faults, provide
theoretical support for fault coupling, and evaluate its theoretical and
empirical limits. Finally, we investigate the limits of heuristic mutation
reduction strategies in comparison with random sampling in representativeness
and find that they provide at most limited improvement. These investigations
underscore the importance of research into new mutation operators and show that
the potential benefit far outweighs the perceived drawbacks in terms of
computational cost.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/phd2017/gopinath2017on.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/phd2017/gopinath2017on.bib)


#### <a id='gopinath2017mutation'></a>[Gopinath, Ahmed, Alipour, Jensen, Groce: _Mutation Reduction Strategies Considered Harmful_  IEEE Transactions on Reliability, 2017]()

Mutation analysis is a well-known yet unfortunately costly method for measuring
test
suite quality. Researchers have proposed numerous mutation reduction
strategies in order to reduce the high cost of mutation analysis, while
preserving the representativeness of the original set of mutants.

As mutation reduction is an area of active research, it is important to
understand the limits of
possible improvements. We theoretically and empirically investigate the
limits of improvement in effectiveness from using mutation reduction
strategies compared to random sampling.
Using real-world open source programs as subjects, we find an absolute limit in
improvement of effectiveness over random sampling - 13.078%.

Given our findings with respect to absolute limits, one may ask: how
effective are the extant mutation reduction strategies?  We evaluate
the effectiveness of multiple mutation reduction strategies in
comparison to random sampling.  We find that none of the mutation
reduction strategies evaluated -- many forms of operator
selection, and stratified sampling (on operators or program elements)
-- produced an effectiveness advantage larger than 5% in
comparison with random sampling.

Given the poor performance of mutation selection strategies --- they may have a
negligible advantage at best, and often perform worse than random sampling --
we caution practicing testers against applying mutation reduction
strategies without adequate justification.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ieeetr2017/gopinath2017mutation.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ieeetr2017/gopinath2017mutation.bib)


#### <a id='gopinath2017how'></a>[Gopinath, Walkingshaw: _How Good are Your Types? Using Mutation Analysis to Evaluate the Effectiveness of Type Annotations_ ICSTW Mutation, 2017]()

Software engineers primarily use two orthogonal means to reduce susceptibility to faults: software
testing and static type checking. While many strategies exist to evaluate the effectiveness of a
test suite in catching bugs, there are few that evaluate the effectiveness of type annotations in a
program. This problem is most relevant in the context of gradual or optional typing, where
programmers are free to choose which parts of a program to annotate and in what detail. Mutation
analysis is one strategy that has proven useful for measuring test suite effectiveness by emulating
potential software faults. We propose that mutation analysis can be used to evaluate the
effectiveness of type annotations too. We analyze mutants produced by the MutPy mutation framework
against both a test suite and against type-annotated programs. We show that, while mutation analysis
can be useful for evaluating the effectiveness of type annotations, we require stronger mutation
operators that target type information in programs to be an effective mutation analysis tool.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icst2017/gopinath2017how.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icstw2017/gopinath2017how.bib)
[<em class="fa fa-desktop"
aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/how-good-are-your-types)

#### <a id='gopinath2017the'></a>[Gopinath, Jensen, Groce: _The Theory of Composite Faults_ ICST, 2017]()
Fault masking happens when the effect of one fault serves to mask that of another fault for particular test inputs. The coupling effect is relied upon by testing practitioners to ensure that fault masking is rare. It states that complex faults are coupled to simple faults in such a way that a test data set that detects all simple faults in a program will detect a high percentage of the complex faults..

While this effect has been empirically evaluated, our theoretical understanding of the coupling effect is as yet incomplete. Wah proposed a theory of the coupling effect on finite bijective (or near bijective) functions with the same domain and co-domain, and assuming uniform distribution for candidate functions. This model however, was criticized as being too simple to model real systems, as it did not account for differing domain and co-domain in real programs, or for syntactic neighborhood.
We propose a new theory of fault coupling for general functions (with certain constraints). We show that there are two kinds of fault interactions, of which only the weak interaction can be modeled by the theory of the coupling effect. The strong interaction can produce faults that are semantically different from the original faults. These faults should hence be considered as independent atomic faults. Our analysis show that the theory holds even when the effect of syntactical neighborhood of the program is considered. We analyze numerous real-world programs with real faults to validate our hypothesis.

##### Updates:

* Updates to Impact of Syntax.


Let us call the original input $h$, $g(i_0) = j_0$, and the changed value $g_a(i_0) = j_a$.
Similarly, let $f(i_0) = k_0$, $f_a(i_0) = k_a$, $f_b(i_0)=k_b$, and $f_{ab}(i_0) = k_{ab}$. Given two
inputs $i_0$, and $i_1$ for a function $f$, we call $i_0$, and $i_1$ semantically close if
their execution paths in f follow equivalent profiles, e.g taking the same
branches and conditionals. We call $i_0$ and $i_1$ semantically far in terms of f if
their execution profiles are different.

Consider the possibility of masking the output of $g_a$ by $h_b$ ($h_{b'}$ in Figure 3)).
We already know that $h(j_a) = k_a$ was detected. That is, we know that $j_a$ was
sufficiently different from $j_0$, that it propagated through $h$ to be caught
by a test case. Say $j_a$ was semantically far from $j_0$, and the difference (i.e
the skipped part) contained the fault $\hat{b}$. In that case, the fault $\hat{b}$
would not have been executed, and since $k_{ab} = k_a$, it will always be detected.

On the other hand, say $j_a$ was semantically close to $j_0$ in terms of $g$ and the
fault $\hat{b}$ was executed. There are again three possibilities. The first is
that $\hat{b}$ had no impact, in which case the analysis is the same as before.
The second is that $\hat{b}$ caused a change in the output. It is possible that
the execution of $\hat{b}$ could be problematic enough to always cause an error,
in which case we have $k_{ab} = k_b$ (error), and detection. Thus masking requires
$k_{ab}$ to be equal to $k_0$.

Even if we assume that the function $h_b$ is close syntactically to $h$, and that
this implies semantic closeness of functions $h$ and $h_b$, we expect the value $k_{ab}$
to be near $k_a$, and not $k_0$.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icst2017/gopinath2017the.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icst2017/gopinath2017the.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/the-theory-of-composite-faults)

#### <a id='alipour2016evaluating'></a>[Alipour, Shi, Gopinath, Marinov, Groce: _Evaluating Non-Adequate Test-Case Reduction_ ASE, 2016]()

Given two test cases, one larger and one smaller, the smaller test case is preferred for many purposes. A smaller test case usually runs faster, is easier to understand, and is more convenient for debugging. However, smaller test cases also tend to cover less code and detect fewer faults than larger test cases. Whereas traditional research focused on reducing test suites while preserving code coverage, one line of recent work has introduced the idea of reducing individual test cases, rather than test suites, while still preserving code coverage. Another line of recent work has proposed non-adequately reducing test suites by not even preserving all the code coverage. This paper empirically evaluates a new combination of these ideas: non-adequate reduction of test cases, which allows for a wide range of trade-offs between test case size and fault detection.

Our study introduces and evaluates C%-coverage reduction (where a test case is reduced to retain at least C% of its original coverage) and N-mutant reduction (where a test case is reduced to kill at least N of the mutants it originally killed). We evaluate the reduction trade-offs with varying values of C and N for four real-world C projects: Mozilla’s SpiderMonkey JavaScript engine, the YAFFS2 flash file system, Grep, and Gzip. The results show that it is possible to greatly reduce the size of many test cases while still preserving much of their fault-detection capability.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ase2016/alipour2016evaluating.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ase2016/alipour2016evaluating.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/evaluating-non-adequate-test-case-reduction)

#### <a id='ahmed2016can'></a>[Ahmed, Gopinath, Brindescu, Groce, Jensen: _Can Testedness be Effectively Measured_ FSE, 2016]()

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

##### Updates:

In this paper we found that coverage and mutation score of a program element has
only a weak negative correlation with future bug fixes *per line* in that
element. In retrospect, comparing the future bug fixes *per line* was a mistake.
We should have compared the coverage and mutation score of the element with the
*total* future bugfixes of that element.

Crucially, our research is the first to provide evidence that the mutation
score is related to the _residual defect density_ of the program. That is, the
number of live mutants remaining is related to the actual bugs remaining in the
program.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/fse2016/ahmed2016can.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/fse2016/ahmed2016can.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/ahmedi/can-testedness-be-effectively-measured)


#### <a id='alipour2016focused'></a>[Alipour, Groce, Gopinath, Christi: _Generating Focused Random Tests Using Directed Swarm Testing_ ISSTA, 2016]()

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

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2016/alipour2016focused.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2016/alipour2016focused.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/arpitchristi/issta-2016-generating-focused-random-tests-using-directed-swarm-testing)


#### <a id='gopinath2016measuring'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _Measuring Effectiveness of Mutant Sets_ ICSTW, 2016]()

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

##### Updates:

(Thanks to [Darko Marinov](http://mir.cs.illinois.edu/marinov/), [Farah Hariri](http://mir.cs.illinois.edu/farah/), [August Shi](http://mir.cs.illinois.edu/awshi2/), Muhammad Mahmood, and Warnakulasuriya Fernando)

* The *minimal mutants* from Ammann et al. ([Ammann 2014](/references#ammann2014establishing)), and the *disjoint mutants* from Kintis et al. ([Kintis 2010](/references#kintis2010evaluating)) is same as the *surface mutants* in this paper. Hence, the *surface mutants* are not an alternative. However, the two measures provided: The *volume ratio*, and the *surface correction* are the right interpretations for disjoint/minimal/surface mutants.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icst2016/gopinath2016measuring.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icst2016/gopinath2016measuring.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](http://eecs.osuosl.org/rahul/icst2016/)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/measuring-effectiveness-of-mutant-sets)

#### <a id='gopinath2016topsy'></a>[Gopinath, Jensen, Groce: _Topsy-Turvy: A Smarter and Faster Parallelization of Mutation Analysis_ ICSE (Extended Abstract), 2016]()

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

##### Updates:

* Part of our concept is similar to the split-stream execution of
mutants suggested (not implemented) by King & Offutt ([King 1991](/references#king1991a)).

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icse2016/gopinath2016topsy.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icse2016/gopinath2016topsy.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](http://eecs.osuosl.org/rahul/icse2016/)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/topsy-turvy-a-smarter-and-faster-parallelization-of-mutation-analysis)

#### <a id='gopinath2016does'></a>[Gopinath, Ahmed, Alipour, Jensen, Groce: _Does the Choice of Mutation Tool Matter?_ Software Quality Journal, 2016]()

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

##### Updates:

(Thanks to [Darko Marinov](http://mir.cs.illinois.edu/marinov/), [Farah Hariri](http://mir.cs.illinois.edu/farah/), [August Shi](http://mir.cs.illinois.edu/awshi2/), Muhammad Mahmood, and Warnakulasuriya Fernando)

* The *surface mutants* in this paper is actually the *minimal mutants* from Ammann et al. ([Ammann 2014](/references#ammann2014establishing)), and the *disjoint mutants* from Kintis et al. ([Kintis 2010](/references#kintis2010evaluating)). The *minimal mutants* in this paper
starts by minimizing the test suite, and hence different from *minimal mutants* from Ammann et al.
* The definition of *mutation subsumption* in the paper is flipped. That is, a
mutant dynamically subsumes another if all test cases that kills the *former* is guaranteed
to kill the *later*, and the mutant is killed by the test suite.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/sqj2016/gopinath2016does.pdf) <!--(http://rdcu.be/ut76)-->
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/sqj2016/gopinath2016does.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](http://eecs.osuosl.org/rahul/sqj2016/)

#### <a id='gopinath2016on'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _On The Limits Of Mutation Reduction Strategies_ ICSE, 2016]()

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
removing operators in the id of selective mutation for
questionable benefit.

<!--script async class="speakerdeck-embed" data-id="6c0a81985e9c4f1cbd153b5a7ae60603" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icse2016/gopinath2016on.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icse2016/gopinath2016on.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://dx.doi.org/10.17605/OSF.IO/H5DCY)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/on-the-limits-of-mutation-reduction-strategies)

#### <a id='gopinath2015how'></a>[Gopinath, Alipour, Ahmed, Jensen, Groce: _How hard does mutation analysis have to be, anyway?_ ISSRE, 2015]()

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

##### Updates:

* One can simplify, and reach our conclusions in this paper by noting
that, theory of random sampling only requires randomness in the sample
selection, and not in the population. That is, even if the population
contains strongly correlated variables, so long as the sampling procedure
is random, one can expect the sample to obey statistical laws.
<!-- need to check _Extension of the law of large numbers to quantities, depending on each other_ by (Markov 1906) --> 
* Further, we recommend that one should sample at least 9,604 mutants
for 99% precision 95% of the time, as suggested by theory.

<!--script async class="speakerdeck-embed" data-id="3a16618236ad4f91b253a9f70b3cbe9b" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issre2015/gopinath2015howhard.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issre2015/gopinath2015howhard.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://dx.doi.org/10.17605/OSF.IO/MYDH2)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/how-hard-does-mutation-analysis-have-to-be-anyway)

#### <a id='ahmed2015an'></a>[Ahmed, Mannan, Gopinath, Jensen: _An Empirical Study of Design Degradation: How Software Projects Get Worse Over Time_ ESEM 2015]()

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

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/esem2015/ahmed2015empirical.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/esem2015/ahmed2015empirical.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/ahmedi/an-empirical-study-of-design-degradation-how-software-projects-get-worse-over-time) 


#### <a id='le2014mutation'></a>[Le, Alipour, Gopinath, Groce: _Mutation Testing of Functional Programming Languages_ ICSTW Mutation 2014]()

Mutation testing has been widely studied in imperative programming languages. The rising popularity of functional
languages and the adoption of functional idioms in traditional languages (e.g. lambda expressions) requires a new set of studies
for evaluating the effectiveness of mutation testing in a functional context. In this paper, we report our ongoing effort in applying
mutation testing in functional programming languages. We describe new mutation operators for functional constructs and
explain why functional languages might facilitate understanding of mutation testing results. We also introduce MuCheck, our
mutation testing tool for Haskell programs.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icstw2014/le2014mutation.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icstw2014/le2014mutation.bib)


#### <a id='gopinath2014mutations'></a>[Gopinath, Jensen, Groce: _Mutations: How close are they to real faults?_ ISSRE 2014]()

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

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issre2014/gopinath2014mutations.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issre2014/gopinath2014mutations.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://dx.doi.org/10.17605/OSF.IO/ENZQK)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/mutations-how-close-are-they-to-real-faults)

#### <a id='groce2014coverage'></a>[Groce, Alipour, Gopinath: _Coverage and Its Discontents_ Essays 2014]()

Everyone wants to know one thing about a test suite: will it detect enough bugs? Unfortunately, in most settings that matter, answering this question directly is impractical or impossible. Software engineers and researchers therefore tend to rely on various measures of code coverage (where mutation testing is considered as a form of syntactic coverage). A long line of academic research efforts have attempted to determine whether relying on coverage as a substitute for fault detection is a reasonable solution to the problems of test suite evaluation. This essay argues that the profusion of coverage-related literature is in part a sign of an underlying uncertainty as to what exactly it is that measuring coverage should achieve, and how we would know if it can, in fact, achieve it. We propose some solutions, but the primary focus is to clarify the state of current confusions regarding this key problem for effective software testing. 

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/splash2014/groce2014coverage.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/splash2014/groce2014coverage.bib)

#### <a id='le2014mucheck'></a>[Le, Alipour, Gopinath, Groce: _MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ISSTA Tools 2014]()

This paper presents MuCheck, a mutation testing tool for Haskell programs. This is the first tool to be published (to our knowledge) that is explicitly oriented towards mutation testing for functional programs. MuCheck is a counterpart to the widely used QuickCheck random testing tool in fuctional programs, and can be used to evaluate the efficacy of QuickCheck property definitions. The tool implements mutation operators that are specifically designed for functional programs, and makes use of the type system of Haskell to achieve a more relevant set of mutants than otherwise possible. Mutation coverage is particularly valuable for functional programs due to highly compact code, referential transparency, and clean semantics, which make augmenting a test suite or specification based on surviving mutants a practical method for improved testing.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issta2014/le2014mucheck.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issta2014/le2014mucheck.bib)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/alipourm/mucheck-an-extensible-tool-for-mutation-testing-of-haskell-programs)

#### <a id='gopinath2014code'></a>[Gopinath, Jensen, Groce: _Code coverage for suite evaluation by developers_ ICSE 2014]()

One of the key challenges of developers testing code is determining a test suite's quality -- its ability to find faults. The most common approach is to use code coverage as a measure for test suite quality, and diminishing returns in coverage or high absolute coverage as a stopping rule. In testing research, suite quality is often evaluated by a suite's ability to kill mutants (artificially seeded potential faults). Determining which criteria best predict mutation kills is critical to practical estimation of test suite quality. Previous work has only used small sets of programs, and usually compares multiple suites for a single program. Practitioners, however, seldom compare suites --- they evaluate one suite. Using suites (both manual and automatically generated) from a large set of real-world open-source projects shows that evaluation results differ from those for suite-comparison: statement (not block, branch, or path) coverage predicts mutation kills best.

<!--script async class="speakerdeck-embed" data-id="640fad3e1a254985a10da2792866b675" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

##### Updates:

Laura  Inozemtseva and Reid Holmes published the paper [Coverage is not strongly correlated with test suite effectiveness](https://dl.acm.org/doi/10.1145/2568225.2568271) at the same ICSE 2014 conference. Their title seems to be counter to the findings in this paper. Why is it so?
Here are my observations:

1. Inozemtseva et al.'s central thesis is that _normalized mutation score_ is not highly correlated with coverage.
2. The normalized mutation score is computed by Inozemtseva et al. as #mutants killed / #mutants covered.
3. However, note that #covered mutants is _directly_ determined by statement coverage. That is, it depends only on the average number of mutants per line along with statement coverage.

Normalization is done _according to Inozemtseva et al._ to _remove the effect of coverage_ (Sec 3.6 2ed para).
So, removing the effect of coverage, if that attempt was successful, should result in a number that is _not_ correlated with coverage (by construction).

So, this means that:

1. A finding that there is no correlation between the normalized mutation score and coverage would be a tautology. This is the expected result.
2. The finding that there is a moderate correlation between the two just means that the effect of coverage was not completely removed by division. That is, there was some non-linear component involved.


[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icse2014/gopinath2014code.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icse2014/gopinath2014code.bib)
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://dx.doi.org/10.17605/OSF.IO/K7JHU)
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/test-suite-evaluation-for-fun-and-profit)

#### <a id='erwig2012explanations'></a>[Erwig, Gopinath: _Explanations for Regular Expressions_ FASE 2012]()

Regular expressions are widely used, but they are inherently hard to understand and (re)use, which is primarily due to the lack of abstraction mechanisms that causes regular expressions to grow large very quickly. The problems with understandability and usability are further compounded by the viscosity, redundancy, and terseness of the notation. As a consequence, many different regular expressions for the same problem are floating around, many of them erroneous, making it quite difficult to find and use the right regular expression for a particular problem. Due to the ubiquitous use of regular expressions, the lack of understandability and usability becomes a serious software engineering problem. In this paper we present a range of independent, complementary representations that can serve as explanations of regular expressions. We provide methods to compute those representations, and we describe how these methods and the constructed explanations can be employed in a variety of usage scenarios. In addition to aiding understanding, some of the representations can also help identify faults in regular expressions. Our evaluation shows that our methods are widely applicable and can thus have a significant impact in improving the practice of software engineering.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/fase2012/erwig2012explanations.pdf)
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/fase2012/erwig2012explanations.bib)


## Technical Reports

My technical reports at Oregon State can be found [here](http://ir.library.oregonstate.edu/xmlui/handle/1957/7302/discover?query=Rahul+Gopinath&filtertype=author&filter_relational_operator=equals&filter=Gopinath%2C+Rahul).

