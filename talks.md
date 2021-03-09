---
layout: publications
title : Talks
header : Talks
group: navigation
weight: 3
menu: Talks
---
##### 2021

* [_Automated Software Testing and Repair_](http://intersection.dsi.cnrs.fr/intersection/resultats-cc-fr.do?campagne=92&section=6&grade=223&phase=ADMAPOUR&conc=06/02)<br/>
  *Gopinath* - CNRS, France, (virtual), (TBD), 2021

* [_The Science of Fuzzing_](#gopinath2021melbourne)<br/>
  *Gopinath* - The University of Melbourne, Australia, (virtual), (TBD), 2021

* [_The Science of Fuzzing_](#gopinath2021tudelft)<br/>
  *Gopinath* - Delft University of Technology, Netherlands, (virtual), Mar 16, 2021

* [_The Science of Fuzzing_](#gopinath2021uwmadison)<br/>
  *Gopinath* - The University of Wisconsin-Madison, USA, (virtual), Mar 15, 2021

* [_The Science of Fuzzing_](#gopinath2021simonfraser)<br/>
  *Gopinath* - Simon Fraser University, Canada, (virtual), Mar 10, 2021

* [_The Science of Fuzzing_](#gopinath2021cispa)<br/>
  *Gopinath* - Auburn University, USA, (virtual), Mar 4, 2021

* [_The Science of Fuzzing_](#gopinath2021sydney)<br/>
  *Gopinath* - University of Sydney, Australia, (virtual), Feb 19, 2021

* [_The Science of Fuzzing_](#gopinath2021cispa)<br/>
  *Gopinath* - CISPA, Germany, (virtual), Feb 9, 2021

* [_The Science of Fuzzing_](#gopinath2021imdea)<br/>
  *Gopinath* - IMDEA, Spain, (virtual), Jan 29, 2021

* [_The Science of Fuzzing_](#gopinath2021psu)<br/>
  *Gopinath* - Portland State University, USA, (virtual), Jan 6, 2021

##### 2020

* [_The Science of Fuzzing_](#gopinath2020kuleuven)<br/>
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
  *Gopinath* - Lorentz center, Leiden University, Netherlands, 2018

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

---

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


