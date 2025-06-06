---
layout: publications
title : Talks
header : Talks
group: navigation
weight: 3
menu: Talks
---

##### 2025
* [_Fuzzing Without Specifications: Learning Structure from Behaviour_](#gopinath2025fuzzing)<br/>
  *Gopinath* - Fuzzing Summer School'25, NUS, Singapore, May 29, 2025

##### 2024
* [_How to Compare Fuzzers_](#gopinath2024how)<br/>
  *Gopinath* - SAPLING'24, ANU, Canberra, Australia, December 1, 2023

* [_Look Ma, No Hands! Testing Software Without Specifications_](#gopinath2024look)<br/>
  *Gopinath* - [Australian National University](https://comp.anu.edu.au/events/2024/06/14/look-ma-no-hands-testing-software-without-specifications/), Canberra, Australia, June 10, 2024


* [_How to Talk to Strange Programs and Find Bugs_](#gopinath2024how)<br/>
  *Gopinath* - ASESS'24, NSW, Sydney, Australia, February 1, 2024

##### 2023
* [_Dancing to Unknown Music: Learning Black-Box Program Input Grammars with Prefix Queries_](#gopinath2023dancing)<br/>
  *Gopinath* - SAPLING'23, Google, Sydney, Australia, December 1, 2023

##### 2022
* [_Mutation Analysis: Answering the Fuzzing Challenge_](#gopinath2022answering)<br/>
  *Gopinath* - University of Melbourne, Melbourne, Australia, October 13, 2022

* [_Building Blocks for Fuzzing_](#gopinath2022building)<br/>
  *Gopinath* - Indian Institute of Technology, Gandhinagar, India, July 19, 2022

* [_Learning And Refining Input Grammars For Effective Fuzzing_](#gopinath2022learning)<br/>
  *Gopinath* - International Workshop on Search-Based Software Testing (SBST), May 9, 2022

##### 2021
* [_Input Languages for Effective and Focused Fuzzing_](#dutra2021input)<br/>
  *Dutra and Gopinath* - FuzzCon Europe, (virtual), October 21, 2021

* [_GAP Interview_](#rigger2021gap)<br/>
  *Rigger and Gopinath* - Getting Academic Positions (GAP) Interviewing Series: Rahul Gopinath (University of Sydney), (virtual), July 21, 2021

* [_Fuzzing -- from Alchemy to a  Science_](#gopinath2021fuzzing)<br/>
  *Gopinath* - The University of Passau, Germany, (virtual), June 30, 2021

<!--
* [_Automated Software Testing and Repair_](http://intersection.dsi.cnrs.fr/intersection/resultats-cc-fr.do?campagne=92&section=6&grade=223&phase=ADMAPOUR&conc=06/02)<br/>
  *Gopinath* - CNRS, France, (virtual), (Declined), 2021

* [_The Science of Fuzzing_](#gopinath2021melbourne)<br/>
  *Gopinath* - The University of Melbourne, Australia, (Declined), (TBD), 2021
-->

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - Delft University of Technology, Netherlands, (virtual), Mar 16, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - The University of Wisconsin-Madison, USA, (virtual), Mar 15, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - Simon Fraser University, Canada, (virtual), Mar 10, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - Auburn University, USA, (virtual), Mar 4, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - University of Sydney, Australia, (virtual), Feb 19, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - CISPA, Germany, (virtual), Feb 9, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - IMDEA, Spain, (virtual), Jan 29, 2021

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - Portland State University, USA, (virtual), Jan 6, 2021

##### 2020

* [_The Science of Fuzzing_](#gopinath2021sf)<br/>
  *Gopinath* - KU Leuven, Belgium, (virtual), Dec 1, 2020

* [_Sample Free Learning of Input Grammars_](#gopinath2020sutd)<br/>
  *Gopinath* - Singapore University of Technology and Design, (virtual), Nov 17, 2020

* [_The Fuzzing Synergy_](#gopinath2020eurecom)<br/>
  *Gopinath* - EURECOM, France, (virtual), Nov 6, 2020

##### 2019
* [_Learning Grammars without Samples_](https://speakerdeck.com/rahulgopinath/learning-grammars-without-samples)<br/>
  *Gopinath* - Università degli Studi di Napoli Federico II, Italy, (virtual), 2019


##### 2018

* [_Look Ma No Hands: Learning Input Grammar without Inputs_](https://speakerdeck.com/rahulgopinath/look-ma-no-hands-learning-input-grammar-without-inputs)<br/>
  *Gopinath* - Workshop: Systematic Analysis of Security Protocol Implementations, Lorentz center, Leiden University, Netherlands, 2018

##### 2017

* [_Pygram: Learning input grammars for Python programs_](#gopinath2017pygram)<br/>
  *Gopinath* - TU Darmstadt, Germany, 2017

* [_Who tests our tests: An overview of mutation analysis, its caveats, and pitfalls_](http://cse.ucsd.edu/about/who-tests-our-tests-overview-mutation-analysis-its-caveats-and-pitfalls)<br/>
  *Gopinath* - UC San Diego, US, 2017

* [_Who tests our tests: An overview of mutation analysis, its caveats, and pitfalls_](#gopinath2017who)<br/>
  *Gopinath* - McGill University, Canada, 2017

##### 2016

* [_Code Coverage is a Strong Predictor of Test suite Effectiveness in the Real World_](#gopinath2016code)<br/>
  *Gopinath* - GTAC, 2016

#### <a id='gopinath2025fuzzing'></a> [Gopinath: _Fuzzing Without Specifications: Learning Structure from Behaviour_, NUS, 2025]()

When fuzzing uncovers a bug, it’s rarely caused by a single input—it’s usually a pattern of inputs that consistently triggers the same underlying issue. Validating a fix, therefore, means testing against that broader pattern, not just the one input that happened to expose the bug.
In this lecture, I’ll show how to capture these input patterns as specialized grammars that reflect specific program behaviours—especially faulty ones. You’ll learn techniques for extracting such patterns, merging them into specialized grammars, and using them for focused fuzzing. These grammars integrate seamlessly with smart fuzzers, offering precise control over input generation and enabling consistent, reproducible testing.
But where do we obtain the input specification? This is a common challenge: effective fuzzing depends on leveraging the input structure, yet accurate specifications are not always available.
I’ll demonstrate how to automatically derive input grammars from the program itself. When source code is available, we can apply static and dynamic analysis to trace input-handling logic directly. Without source code, we can infer grammars by observing how the program reacts to inputs—refining our understanding through continuous feedback.

Together, these techniques enable powerful, specification-free fuzzing and lay the groundwork for the behaviour-driven strategies we’ll explore throughout the session.
 
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/fuzzing-without-specifications-learning-structure-from-behaviour-part-i)

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/fuzzing-without-specifications-learning-structure-from-behaviour-part-ii)

---
#### <a id='gopinath2024how'></a> [Gopinath: _How to Compare Fuzzers_ SAPLING, ANU, 2024]()

Fuzzing is a leading technique for assessing the effectiveness of software test suites and test generators in finding bugs. However, with numerous fuzzers available, it can be unclear which one to use. Fuzzing campaigns are typically limited by available computing resources, and any compute wasted on an underperforming fuzzer can impact the final outcome. Moreover, a fuzzer’s effectiveness often depends on the domain and specific program being tested. As a result, one of the key challenges in fuzzing is determining how to evaluate their effectiveness.

In this talk, I will explore various methods for evaluating test generators like fuzzers, their respective pros and cons, and strategies for addressing these challenges.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/how-to-compare-fuzzers)


---
#### <a id='gopinath2024look'></a> [Gopinath: _Look Ma, No Hands! Testing Software Without Specifications_ ANU, 2024]()

How do we test software when detailed specifications are unavailable? Effective testing requires both input and behavioural specifications. However, often in the industry, one cannot rely on the availability or reliability of either. In this talk, I will demonstrate how to extract detailed specifications from given programs when the provided specifications are unreliable. I will explain how to leverage detailed error feedback to construct input and behavioural models of the program. These models can be used to verify program behaviour, identifying, and eliminating software bugs before they are deployed in production.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/look-ma-no-hands-testing-software-without-specifications)

#### <a id='gopinath2024how'></a> [Gopinath: _How to Talk to Strange Programs and Find Bugs_ ASESSG 2024]()

For effective testing of programs with complex structured inputs, the input
specification or the input grammar is practically mandatory.  Given an input
grammar, we can use it to produce inputs that reach program internals and induce
interesting behaviours. We can also use such grammars for quickly generating
inputs, for characterizing program behaviours, for repair of inputs, as well as
for quick input validation. However, many programs that require complex
structured inputs come with a precise input grammar. Even when such a grammar is
available, the grammar could be incomplete, obsolete, or incorrect. Hence, one
of the long-standing questions in software engineering is the inference of such
grammars. That is, given a parser, how do we /invert/ such parsers, and get the
input specification back? This talk will focus on how to extract such grammars
from parsers themselves, and what can we do with such grammars.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/how-to-talk-to-strange-programs-and-find-bugs)


#### <a id='gopinath2023dancing'></a> [Gopinath: _Dancing to Unknown Music: Learning Black-Box Program Input Grammars with Prefix Queries_ SAPLING 2023]()

For effective testing of programs with complex structured inputs, we need the
input grammar. Yet, neither the input grammar nor the source code is guaranteed
for many programs. If we have a program for which neither code nor input
specifications are available, how can we generate test inputs? In this talk,
I show how this is possible if the program provides failure feedback, which is
information on whether the input is valid and, if not, the part of the input
that was successfully processed before failure. Such feedback is available out
of the box for most parsers. Given this feedback, I show how to leverage it for
inferring the input grammar of the program under test.
This grammar can then be used for effective testing of the program under test.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/dancing-to-an-unknown-music-grammar-inferrence-with-prefix-queries)

#### <a id='gopinath2022answering'></a> [Gopinath: _Mutation Analysis: Answering the Fuzzing Challenge_ University of Melbourne 2022]()

Our society now relies on software to such an extent that cyberattacks and
related information infrastructure problems are classified as having the same
scale of catastrophic disruption as that of natural disasters by the World
Economic Forum. This also means that there is a huge cost to bugs in the
critical software systems. We need effective testing to make sure that our
systems are robust and trustworthy. But to do that, we need to measure the
quality of our test suites and test generators. In this talk I will discuss
the limitations of structural coverage, and introduce mutation analysis as
an alternative.

With the increase in software complexity, we need to rely on automatic test
generators such as fuzzers more and more. However, evaluating fuzzers has its
own challenges. In this talk, I will discuss the challenges and opportunities
in applying mutation analysis to fuzzing.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/mutation-analysis-answering-the-fuzzing-challenge "presentation")

#### <a id='gopinath2022building'></a> [Gopinath: _Building Blocks for Fuzzing_ IIT Gandhinagar 2022]()

Fuzzing is a key technique for evaluating the robustness of programs
against malicious inputs. Effective fuzzing requires the availability
of the program input grammar, which is typically unavailable, limiting
the reach and effectiveness of fuzzers.

In this talk, I show how to extract precise input grammar for programs.
Such grammars can not only be used for effective exploration of the
program input space, but also to decompose any available sample inputs,
and recombine such parts to produce novel inputs and behaviors.

One of the questions in fuzzing is how to generate inputs that exercise
a specific behavior in a program without losing the fuzzing effectiveness.
In this talk, I show how to extract and abstract patterns that represent
unique program behaviors, and use such patterns for focused fuzzing.

Any number of such abstract patterns can then be combined using the
full set of logical connectives --- to produce specialized grammars
that can be used by any grammar fuzzer for precise control of produced
inputs and hence the expected behavior.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/building-blocks-for-fuzzing)

#### <a id='gopinath2022learning'></a> [Gopinath: _Learning And Refining Input Grammars For Effective Fuzzing_ SBST 2022]()

Fuzzing is one of the key techniques for evaluating robustness of programs against malicious inputs. To fuzz the program logic effectively, one needs the input specification of the program under fuzzing. However, such input specifications are rarely available, and even when present, can be obsolete, incomplete or incorrect leading to fuzzing blind spots. In this tutorial, I will show how to mine the input specification from a given program from the ground up, first generating sample inputs, then using such inputs to mine the program input grammar, and finally using the mined grammar to fuzz the program and find any bugs.

What should you do next once you find a bug? An input pattern rather than a particular input is likely to result in the bug, and to have any confidence in a bug fix, we should test the fix using the input pattern rather than a single input. In this talk, I will show how to abstract such input patterns corresponding to program behaviors such as bugs into a focused grammar, how to combine multiple input patterns together, and use such patterns to fuzz. The specialized grammars we generate can be used by any grammar fuzzer for precise control of produced inputs and hence the expected behavior. 

More info [here](https://sbst22.github.io/keynotes/)

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/learning-and-refining-input-grammars-for-effective-fuzzing)
<iframe width="838" height="471" src="https://www.youtube.com/embed/_GFrw1fBUFI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


#### <a id='dutra2021input'></a>[Dutra & Gopinath: _Input Languages for Effective and Focused Fuzzing_ FuzzCon Europe 2021]()

In this talk, we present several ways in which fuzzers can be enhanced with an
input language specification, in order to enable focused fuzzing and reach
deeper parts of the code. First, we focus on input languages which are expressed
as context-free grammars, as well as refinements of such grammars. Here, we show
how those grammars can be mined from the program execution, as well as
abstracted to capture particular behaviors, such as a failure-inducing pattern.
We also show how the original input grammar can be refined to produce the
pattern of interest, or even a boolean combination of such patterns, enabling a
full algebra of inputs. Next, we focus on the fuzzing of binary file formats,
such as MP4 or ZIP. We show how such formats can be effectively represented using
binary templates, which are a format specification used by the 010 Editor.
Our new tool FormatFuzzer can turn those binary templates into highly efficient
parsers, mutators and generators for the specified format. This can be
integrated into existing fuzzers such as AFL++ to boost their efficacy and
detect new memory errors.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/input-languages-for-effective-and-focused-fuzzing)
<iframe width="560" height="315" src="https://www.youtube.com/embed/kaastMal2iw?start=967" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


### <a id='rigger2021gap'></a> [Rigger: _GAP Interview_ (virtual), 2021]()<br/>

<iframe width="560" height="315" src="https://www.youtube.com/embed/HyIdD3V4mnA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

#### <a id='gopinath2021fuzzing'></a>[Gopinath: _Fuzzing -- from Alchemy to a Science_ Guest Lecture, 2020-2021]()

Fuzzing is one of the key techniques in the arsenal of a practitioner of
cyber-security, and is used for evaluating the robustness of programs against
malicious inputs. To fuzz effectively, the input specification of
the program under evaluation is practically a requirement.
However, such specifications are typically unavailable, obsolete, incomplete,
or inaccurate, limiting the reach of fuzzers. This has led to a proliferation
of hacky recipes by different fuzzers to get past the input parsing
stage, with each recipe working on some but not all programs. That is,
fuzzing most resembles alchemy than science at this point.

In this talk, I show how to transform fuzzing to a science. I present
an end-to-end framework for recovering precise input specifications of
programs. Such mined specifications can immediately be used for
effective exploration of the program input space as well as the space
of the program behavior, leading to the identification of
failure-inducing inputs. Next, given any failure-inducing input, I
show how to generalize such inputs into abstract patterns, precisely
identifying the failure causing parts of the input. Any number of such
abstract patterns can then be combined using the full set of logical
connectives --- to produce specialized grammars that can be used by
any grammar fuzzer for precise control of produced inputs and hence
the expected behavior.

[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/fuzzing-from-alchemy-to-a-science)

#### <a id='gopinath2021sf'></a>[Gopinath: _The Science of Fuzzing_ Job Talk, 2020-2021]()

Fuzzing is a key method for evaluating the robustness of a program
against malicious inputs. It involves generating and feeding arbitrary
data to a program, and monitoring the program for catastrophic
failures. Any failure in the program in processing the data indicates
a possible vulnerability in the program. Efficient and effective
fuzzing requires the availability of the input specification for the
program under test. However, such specifications are typically
unavailable, obsolete, incomplete, or inaccurate, limiting the reach
of fuzzers. This has led to a proliferation of hacky recipes by
different fuzzers to get past the input parsing stage, with each
recipe working on some but not all programs. That is, fuzzing most
resembles alchemy than science at this point.

In this talk, I show how to transform fuzzing into a science. I
present an end-to-end framework for recovering precise input
specifications of programs.
Such mined specifications can immediately be used for effective
exploration of the program input space as well as the space of the
program behavior, leading to the identification of failure-inducing
inputs. Next, given any failure-inducing input, I show how to
generalize such inputs into abstract patterns, precisely identifying
the failure-causing parts of the input. Any number of such abstract
patterns can then be combined using the full set of logical
connectives --- to produce specialized grammars that can be used by
any grammar fuzzer for precise control of produced inputs and hence
the expected behavior.

<iframe width="560" height="315" src="https://www.youtube.com/embed/Al4C-goD6kg" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

#### <a id='gopinath2020sutd'></a>[Gopinath: _Sample Free Learning of Input Grammars_ Singapore University of Technology and Design, 2020]()

Efficient and Effective fuzzing requires the availability of the input specification for the program under test. However, such specifications are typically unavailable or inaccurate, limiting the reach of fuzzers. In this talk, I present an end-to-end framework for recovering the input specification for given programs without samples, using such mined specifications for isolating and generalizing failure-inducing inputs, as well as for the precise control of fuzzers.

#### <a id='gopinath2017pygram'></a>[Gopinath: _Pygram: Learning input grammars for Python programs_ TU Darmstadt, Germany (software group retreat), 2017]()

AUTOGRAM is a method to infer human-readable input grammars from observing
program behavior on test runs. The resulting grammars can be used for fuzzing,
secondary or parallel validation of new inputs, and identifying the essence of
a program in a language agnostic manner. I will present my current work in
AUTOGRAM, and discuss my research in taking AUTOGRAM forward.


#### <a id='gopinath2017who'></a>[Gopinath: _Who tests our tests: An overview of mutation analysis, its caveats, and pitfalls_ McGill University, Canada, 2017]()

A key concern in software engineering is determining the reliability of our 
software artifacts. Software engineers traditionally rely on extensive testing
to ensure that programs are fault free. However, tests are usually also written
by human beings, and hence vulnerable to the similar problems as software 
applications. An inadequate test suite, or one that contains errors, can 
provide a false sense of security to the programmer or the consumer. Hence a 
major question in software testing is how to evaluate the quality of test 
suites.

Following the maxim "you can't find a bug in what you don’t cover", code 
coverage is often used as a measure of test suite quality.
However, code coverage can not evaluate the quality of our oracles, and given 
that our oracles are often insufficient or wrong, code coverage, on its own is 
insufficient, and mutation testing, a stronger fault-based technique is often 
recommended. In this talk, I will present the basics of mutation testing, and 
look at why it is effective. Next, I will examine the limitations to mutation 
analysis, and how these can be mitigated. I will also examine how insights from
mutation testing may be used in fields such as evaluating type annotations, 
program repair, and program adaptation.


#### <a id='gopinath2016code'></a>[Gopinath: _Code Coverage is a Strong Predictor of Test suite Effectiveness in the Real World_ GTAC, 2016]()

This talk is about the effectiveness of coverage as a technique for evaluating quality of test suite. We show the utility of coverage by considering its correlation with mutation score, and also show that coverage is a significant defence against bugs. Further, we also critique effectiveness of mutation score as a criteria for test suite quality.

<iframe width="560" height="315" src="https://www.youtube.com/embed/NKEptA3KP08" frameborder="0" allowfullscreen></iframe>

<!-- script async class="speakerdeck-embed" data-id="fc3fde8ea9d948f496ea79378c45161f" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script -->


