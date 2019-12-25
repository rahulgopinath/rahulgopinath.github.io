---
layout: default
menu: Rahul Gopinath
weight: 1
---
Rahul Gopinath is a postdoctoral researcher working on static and dynamic analysis of software at [CISPA Saarland University](http://cispa.saarland). He works with [Prof. Dr. Andreas Zeller](https://www.st.cs.uni-saarland.de/zeller/). He received his PhD in 2017 from the [School of EECS at Oregon State University](http://eecs.oregonstate.edu/).


<h2>Research at CISPA</h2>

At CISPA, I work in _Grammar Mining_, and _Grammar Based Fuzzing_.
I am one of the authors of [the fuzzing book](https://www.fuzzingbook.org/). Some of our recent results include the [F1 grammar fuzzer](https://rahul.gopinath.org/publications/#gopinath2019building) and the grammar inference engine [Mimid](https://rahul.gopinath.org/publications/#gopinath2019inferring).

Stay tuned for our recent results ...

<h2>Research until Ph.D.</h2>

PhD Supervisors: [Dr. Carlos Jensen](http://dblp.uni-trier.de/pers/hd/j/Jensen:Carlos) and [Dr. Alex Groce](http://dblp.uni-trier.de/pers/hd/g/Groce:Alex)<br/>
<h3>Research</h3>
My primary focus during my PhD was mutation analysis of programs, and especially how to make mutation analysis a workable technique for real-world developers and testers.

<!--h5>Overview of publications</h5>
[<img src="/resources/img-publications.svg" alt="Publications" title="Publications" width="550px" align='center'>](/publications) -->

Mutation analysis is a method of evaluating the quality of software test suites by introducing simple faults into a program. A test suite's ability to detect these mutants, or artificial faults, is a reasonable proxy for the effectiveness of the test suite. While mutation analysis is the best technique for test suite evaluation we have, it is also rather computationally and time intensive, requiring millions of test suite runs for even a moderately large software project.  This also means that mutation analysis is effectively impossible to use by developers and practicing testers working on real-world problems, and who need to evaluate whether their current test suites are adequate. Unfortunately, most of the research done in mutation analysis has been done on a small number of subject programs, small in size, and that have test suites with high coverage and adequacy -- something that is a rarity in real-world development (at least at early development stages).


My [initial research](/publications/#gopinath2014code) towards addressing the shortcomings of mutation analysis found that <em>statement coverage</em>, rather than branch or path coverage is a better measure of mutation score, and hence quality of a test suite. This was substantiated by extensive examination of over 200 real world projects of various sizes. The [second part](/publications/#gopinath2014mutations) of my research was to evaluate whether the faults produced by mutation analysis were representative of real faults. Our examination of over 5,371 projects in four different programming languages found that the faults used by mutation analysis are rather simplistic in practice compared to real world bugs (in terms of the size of code change).

As an initial step towards reducing the computational requirements of mutation analysis, I investigated techniques used for mutation analysis, and invented a [new algorithm](/publications/#gopinath2016topsy) for faster mutation analysis, taking advantage of redundancy in execution between similar mutants. Further, I was able to identify how [combinatorial evaluation](/publications/#gopinath2015how) could be used for evaluating equivalent mutants. Next,
I compared the effectiveness of current techniques for reducing mutants to be evaluated such as operator selection and stratum based sampling, and found that they offer surprisingly little advantage (less than 10% for stratum sampling and negative for operator selection) compared to simple random sampling in multiple evaluation criteria.

My [recent research](/publications/#gopinath2016on) comparing the effectiveness of the theoretical best mutation
selection methods with random sampling found that even under oracular
knowledge of test kills, mutation selection methods can at best be less than
20% better than random sampling, and are often much worse. Interestingly, there
is no such limit on how the amount of efficiency that can be achieved by
addition of new operators. This discovery suggests that effort should be spent
on finding newer and relevant mutation operators rather than removing the
operators in the name of effectiveness.

<h3>Implementation</h3>
The ideas from my research have resulted in two practical implementations -- [MuCheck](https://hackage.haskell.org/package/MuCheck) for Haskell, and [Xmutant](https://pypi.python.org/pypi/xmutant) for Python. I am also a contributor for [PIT](http://pitest.org/) mutation analysis system for Java, and [Rubocop](https://github.com/bbatsov/rubocop), a static analyzer for Ruby.

<h3>Practice</h3>
My interest in quality of programs is informed by a wealth of practical knowledge from the Industry. Before joining the PhD program, I worked in the software industry as a developer for ten years, where I was part of web and proxy server development teams at [Quark Media House](http://www.quark.com/), and [Sun Microsystems](http://www.sun.com/). My primary area of interest was the web caches,  particularly the distributed caching systems and protocols. I participated in the OpenSolaris effort, where I was the maintainer of multiple open source packages. I have also contributed to the Apache HTTPD project, in core and mod_proxy modules. During my PhD, I worked at [Puppet Labs](https://puppet.com/) where I contributed extensively towards the functionalities in the Solaris Operating system.


