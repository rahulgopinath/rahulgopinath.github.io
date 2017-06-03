---
layout: publications
title : Talks
header : Talks
group: navigation
weight: 3
menu: Talks
---

##### 2017

* [_Who tests our tests: An overview of mutation analysis, its caveats, and pitfalls_](http://cse.ucsd.edu/about/who-tests-our-tests-overview-mutation-analysis-its-caveats-and-pitfalls)<br/>
  *Gopinath* - UC San Diego , 2017

* [_Who tests our tests: An overview of mutation analysis, its caveats, and pitfalls_](#gopinath2017who)<br/>
  *Gopinath* - McGill University, 2017

##### 2016

* [_Code Coverage is a Strong Predictor of Test suite Effectiveness in the Real World_](#gopinath2016code)<br/>
  *Gopinath* - GTAC, 2016

---

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

<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-74302125-1', 'auto');
  ga('send', 'pageview');

</script>
