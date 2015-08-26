---
layout: default
menu: Rahul Gopinath
---
<link rel="icon" type="image/x-icon" href="/favicon.ico">
Rahul Gopinath is a PhD candidate in the School of Electrical Engineering and Computer Science (EECS) at Oregon State University (OSU). He received his B-Tech  from Kerala University, India, and  MCS from Illinois Institute of Technology in 2010.

Supervisor: [Dr. Carlos Jensen](http://eecs.oregonstate.edu/people/jensen-carlos)<br/>
Research Team: [HCI](http://research.engr.oregonstate.edu/hci/) at [Oregon State University](http://oregonstate.edu/)<br/>
Areas of Interest: Mutation Analysis of software test suites, programming languages, and distributed and parallel systems.<br/>

<h3>Research</h3>
My primary area of research is mutation analysis of programs, and especially how to make mutation analysis a workable technique for real-world developers and testers.

Mutation analysis is a method of evaluating the quality of software test suites by introducing simple faults into a program. A test suites ability to detect these mutants, or artificial faults, is a reasonable proxy for the effectiveness of the test suite. While mutation analysis is the best technique for test suite evaluation we have, it is also rather computationally and time intensive, requiring millions of test suite runs for even a moderately large software project.  This also means that mutation analysis is effectively impossible to use by developers and practicing testers working on real-world problems, and who need to evaluate whether their current test suites are adequate. Unfortunately, most of the research done in mutation analysis has been done on a small number of subject programs, small in size, and that have test suites with high coverage and adequacy -- something that is a rarity in real-world development (at least at early development stages).

My initial research towards addressing the shortcomings of mutation analysis found that <i>statement coverage</i>, rather than branch or path coverage is a better measure of mutation score, and hence quality of a test suite. This was substantiated by extensive examination of over 200 real world projects of various sizes. A second part of my research was to evaluate whether the faults produced by mutation analysis were representative of real faults. Our examination of over 5,371 projects in four different programming languages found that the faults used by mutation analysis are rather simplistic in practice compared to real world bugs (in terms of the size of code change).

As an initial step towards reducing the computational requirements of mutation analysis, I analyzed the statistical properties of the mutants produced both theoretically and empirically, while considering the similarity of many mutants to each other, which defeats simple statistical sampling.
My research suggests that theoretically, a sample of 10,000 mutants is sufficient for a single decimal approximation of the full mutation score, while practically a random sample of just 1000 mutants is sufficient irrespective of the code-base size.

<h3>Implementation</h3>
The ideas from my research have resulted in two practical implementations -- MuCheck for Haskell, and Xmutant for Python. I am also a contributor for Pit mutation analysis system for Java, and Rubocop, a static analyzer for Ruby.

<h3>Practice</h3>
My interest in quality of programs is informed by a wealth of practical knowledge from the Industry. Before joining the PhD program, I worked in the software industry as a developer for ten years, where I was part of web and proxy server development teams at Quark Media House, and Sun Microsystems. My primary area of interest was the web caches,  particularly the distributed caching systems and protocols. I participated in the OpenSolaris effort, where I was the maintainer of multiple open source packages. I have also contributed to the Apache HTTPD project, in core and mod_proxy modules. During my PhD, I worked at Puppet  Labs where I contributed extensively towards the functionalities in the Solaris Operating system.


<h3> Publications </h3>

Gopinath, Alipour, Ahmed, Jensen, Groce<br/>
[_How hard does mutation analysis have to be anyway?_](publications#gopinath-alipour-ahmed-jensen-groce-how-hard-does-mutation-analysis-have-to-be-anyway-issre-2015)<br/>
ISSRE 2015

Ahmed, Gopinath, Mannan, Jensen<br/>
[_An Empirical Study of Design Degradation: How Software Projects Get Worse Over Time_ ](publications#ahmed-gopinath-mannan-jensen-an-empirical-study-of-design-degradation-how-software-projects-get-worse-over-time-esem-2015)<br/>
ESEM 2015

Gopinath, Jensen, Groce<br/>
[_Mutations: How close are they to real faults?_ ](publications#gopinath-jensen-groce-mutations-how-close-are-they-to-real-faults-issre-2014)<br/>
ISSRE 2014

Groce, Alipour, Gopinath<br/>
[_Coverage and Its Discontents_ ](publications#groce-alipour-gopinath-coverage-and-its-discontents-essays-2014)<br/>
SPLASH 2014

Le, Alipour, Gopinath, Groce<br/>
[_MuCheck: An Extensible Tool for Mutation Testing of Haskell Programs_ ](publications#le-alipour-gopinath-groce-mucheck-an-extensible-tool-for-mutation-testing-of-haskell-programs-issta-tools-2014)<br/>
ISSTA Tools 2014

Gopinath, Jensen, Groce<br/>
[ _Code coverage for suite evaluation by developers_ ](publications#gopinath-jensen-groce-code-coverage-for-suite-evaluation-by-developers-icse-2014-72-82-2014)<br/>
ICSE 2014

Erwig, Gopinath<br/>
[_Explanations for Regular Expressions_](publications#erwig-gopinath-explanations-for-regular-expressions-fase12-lncs-7212-394-408-2012)<br/>
FASE 2012

<h3> Current Projects </h3>

[MuCheck](https://hackage.haskell.org/package/MuCheck): A mutation analysis framework for Haskell

[XMutant](https://pypi.python.org/pypi/xmutant): A mutation analysis framework for Python

<h3> Past Projects </h3>

[Apache HTTPD](https://httpd.apache.org): Contributor for Apache HTTPD

[mod-scheme](https://github.com/vrthra/mod-scheme): A Scheme language plugin for Apache HTTPD

[openstack-mellanox-cookbook](https://github.com/osuosl-cookbooks/cookbook-openstack-mellanox): IBM Mellanox Chef Cookbook for OpenStack

Ruby [ircd](https://github.com/vrthra/ruby-ircd) [nntpd](https://github.com/vrthra/ruby-nntpd) [imapd](https://github.com/vrthra/ruby-imapd) : Simple server implementations in Ruby

My github id is [Vrthra](https://github.com/vrthra).
