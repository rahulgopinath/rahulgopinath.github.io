---
layout: default
menu: Rahul Gopinath
weight: 1
---
Rahul Gopinath is a PhD candidate in the School of Electrical Engineering and Computer Science (EECS) at Oregon State University (OSU). He received his B-Tech  from Kerala University, India, and  MCS from Illinois Institute of Technology in 2010.

Supervisors: [Dr. Carlos Jensen](http://eecs.oregonstate.edu/people/jensen-carlos) and [Dr. Alex Groce](http://eecs.oregonstate.edu/people/groce-alex)<br/>
Research Team: [HCI](http://research.engr.oregonstate.edu/hci/) and [Testing](http://web.engr.oregonstate.edu/~alex/testing/) at [Oregon State University](http://oregonstate.edu/)<br/>
Areas of Interest: Software analysis and verification, programming languages, and distributed and parallel systems.<br/>

<h3>Research</h3>
My primary area of research is mutation analysis of programs, and especially how to make mutation analysis a workable technique for real-world developers and testers.

Mutation analysis is a method of evaluating the quality of software test suites by introducing simple faults into a program. A test suite's ability to detect these mutants, or artificial faults, is a reasonable proxy for the effectiveness of the test suite. While mutation analysis is the best technique for test suite evaluation we have, it is also rather computationally and time intensive, requiring millions of test suite runs for even a moderately large software project.  This also means that mutation analysis is effectively impossible to use by developers and practicing testers working on real-world problems, and who need to evaluate whether their current test suites are adequate. Unfortunately, most of the research done in mutation analysis has been done on a small number of subject programs, small in size, and that have test suites with high coverage and adequacy -- something that is a rarity in real-world development (at least at early development stages).

<h4>Overview of publications</h4>
<img src="/resources/mindmap.jpg" width="550px">

My [initial research](/publications/#gopinath2014code) towards addressing the shortcomings of mutation analysis found that <em>statement coverage</em>, rather than branch or path coverage is a better measure of mutation score, and hence quality of a test suite. This was substantiated by extensive examination of over 200 real world projects of various sizes. The [second part](/publications/#gopinath2014mutations) of my research was to evaluate whether the faults produced by mutation analysis were representative of real faults. Our examination of over 5,371 projects in four different programming languages found that the faults used by mutation analysis are rather simplistic in practice compared to real world bugs (in terms of the size of code change).

As an initial step towards reducing the computational requirements of mutation analysis, I compared the effectiveness of current techniques for reducing mutants to be evaluated such as operator selection and stratum based sampling, and found that they offer surprisingly little advantage (less than 10% for stratum sampling and negative for operator selection) compared to simple random sampling in multiple evaluation criteria. This prompted me to find how many mutants are actually required for a reasonable approximation of the full mutation score. My [research](/publications/#gopinath2015how) suggests that theoretically, a sample of 10,000 mutants is sufficient for a single decimal approximation of the full mutation score, while practically a random sample of just 1000 mutants is sufficient irrespective of the code-base size.

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


<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-74302125-1', 'auto');
  ga('send', 'pageview');

</script>
