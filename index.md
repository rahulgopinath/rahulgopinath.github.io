---
layout: default
menu: Rahul Gopinath
weight: 1
---

<!--b>IMPORTANT: I am recruiting students for my group at Sydney University.
If you are either an *excellent programmer*, or a strong student in *Automata and
Theory of Computation*, [please drop me a note](/contact/). </b-->



Rahul Gopinath is a lecturer at the [University of Sydney](https://www.sydney.edu.au/).
His focus is static and dynamic analysis of software.
He received his Ph.D. in 2017 from the [School of EECS at Oregon State University](http://eecs.oregonstate.edu/),
and did his postdoc at
[CISPA Helmholtz Center for Information Security](http://cispa.saarland), Germany.
 The following is a summary of his research.
<!-- PhD Supervisors: [Prof. Dr. Carlos Jensen](http://dblp.uni-trier.de/pers/hd/j/Jensen:Carlos)
and [Prof. Dr. Alex Groce](http://dblp.uni-trier.de/pers/hd/g/Groce:Alex)<br/>
-->
<h3>Cybersecurity</h3>

My work is focused on fuzzing software systems. Fuzzing is essentially about
evaluating how a software system responds to unexpected and possibly invalid
inputs. The question is, can you make the system under fuzzing behave in an
unexpected or unforeseen manner?
If a system correctly rejects all invalid inputs and behaves correctly under
valid inputs, we say that the system is robust under fuzzing. Fuzzing a system
requires relatively little manual input, and fuzzing a system before its release
can help uncover vulnerabilities before it is exposed to the wider world.

Our work produced [the fuzzing book](https://www.fuzzingbook.org/) which is an
accessible resource for students and practitioners new to fuzzing.
[![Fuzzingbook Image](/resources/fuzzingbook_image.webp)](https://www.fuzzingbook.org/)
It takes the student through writing simple fuzzers that generate random inputs
without any information or feedback from the program to writing complex fuzzers
that analyze the system under fuzzing for information about the expected inputs
and incorporate the feedback from previous runs to guide further fuzzing.

One of the challenges in fuzzing is how to reach deep code paths. In particular,
many systems accept multilayered inputs such as an HTTP request that wraps a
JSON object, which in turn encodes an RPC call, which may, in turn, encode a
custom data structure. For such inputs, traditional fuzzers rarely reach beyond
the first layer. The problem is that traditional fuzzers rely on coverage to
decide how to proceed. When a fuzzer is faced with a program with a complex
input structure, coverage is of little help beyond producing simple values as
the paths explored are the same for simple or complex inputs. This means that
one needs a better way of producing complex inputs than traditional coverage
guided fuzzing.

Our first research was toward generating complex *valid* inputs when faced with
a parser so that we can get to the next level. We found that traditional
approaches such as symbolic execution do not work well due to *path explosion*
when faced with parsers. 
We [invented](https://arxiv.org/abs/1810.08289) a fast and lightweight approach
called [Pygmalion](https://github.com/vrthra/pygmalion) that iteratively
corrects a generated input prefix which ultimately leads to valid inputs.
Our approach is applicable both for
single pass parsers [(PLDI 2019)](/publications/2019/06/22/pldi-parser/) as well
as for parsers with a lexical analysis
stage [(ISSTA 2020)](/publications/2020/07/18/issta-learning/). Our
technique is applicable even for [instrumentation-less systems](https://arxiv.org/abs/2012.13516)
such as embedded systems and remote systems.

While *Pygmalion* can get us valid inputs faster than traditional methods, it is
limited to overcoming the first layer parser. While *Pygmalion* is fast, it
still needs to run the program under fuzzing once per input character, which is
comparatively expensive if one wants to produce a large number of valid inputs.
Hence, we [invented](https://github.com/vrthra/mimid) a technique called _Mimid_
that can infer the input structure expected by a given parser as a
*context-free grammar* from the dynamic analysis of the program run [(FSE 2020)](/publications/2020/11/08/fse-mining/).
In particular, _Mimid_ covers the entire spectrum of parsers from ad hoc
handwritten parsers to modern parser combinators, and represents a significant
advancement in the field.

Given such a grammar, the problem reduces to how one can generate inputs fast
from a *context-free grammar*. The problem at this point was that the available
grammar-based fuzzers were too slow.
Hence, we [adapted](/publications/2019/11/18/arxiv-building/) ideas from
programming language implementation, and virtual machine optimization to build
our [F1 grammar fuzzer](https://github.com/vrthra/f1) which is effective and
efficient and can produce millions of inputs per second.

![Pygmalion Pipeline](/resources/totalfuzz.webp)

While fuzzers are effective in quickly identifying failure conditions using
surprising inputs, the inputs produced by these tools can often be huge, and
incomprehensible to the developer.
Hence, test case reduction (often variants of _delta debugging_) is often used
to reduce the test case to a minimal input, such strings still fail to inform the developer as to what went wrong.
Even worse, a casual inspection of many such test cases can often suggest an
incorrect hypothesis. We [invented](/publications/2020/07/18/issta-abstracting/)
a technique called _DDSET_ that identifies the parts of the input that caused
the failure, and abstracts away everything else.
The failure representations (we call these
_evocative patterns_) produced by _DDSET_ (e.g. `((<expr>))` when
the error is caused due nested parenthesis)
are precise and easy to understand.
Our work was presented at [ISSTA 2020](/publications/2020/07/18/issta-abstracting/),
and received the __ACM SIGSOFT Distinguished Paper__ award.

The evocative patterns thus produced represent a specialization of the base
grammar of the input. In our paper at [ICSE 2021](/publications/2021/05/22/icse-input-algebras/),
we show how, given the base grammar and the evocative pattern corresponding
to a failure, one can produce the corresponding specialized context-free
grammar which guarantees that the evocative fragment is present in all
inputs produced from the specialized grammar at least once. We also show
how to combine such evocative patterns using all logical connectives
--- conjunction, disjunction, and negation --- forming evocative expressions
that represent a specialized _context-free_ grammar.

![Evocative Expressions](/resources/ewok.webp)

The example above shows a simple evocative expression that specializes
a base JSON grammar. The corresponding evocative grammar guarantees
that the inputs produced will have at least one empty key (the first evocative
pattern in the _where_ clause), and no _null_ key values (the second evocative
pattern in the _where_ clause, negated). Second, it also guarantees that the
evocative grammar produced will be able to successfully parse _any_ input
that conforms to these specifications (or the grammar when used as a producer
can produce any such input).
While the evocative patterns can be written by hand,
they can also be mined from existing bugs by simply using the DDSET
algorithm.
These evocative expressions can not only be used as precise generators
but also as supercharged semantic pattern matchers similar to Semgrep.

<h3>Mining input specifications</h3>

Inferring the input language of a program is the thread that ties much of
my recent work together,
and we have pushed it in several directions since *Mimid*.

Taking stock of the field, we reimplemented the GLADE algorithm — the first
blackbox approach to claim context-free approximation of real input
languages — and found that its reported effectiveness was overly optimistic
[(PLDI 2022)](/publications/2022/04/04/pldi-synthesizing/).
Replication of this kind matters:
grammar inference results are easy to overstate and hard to compare.

Not every input language is textual, and not every one is context-free.
_CLIFuzzer_ mines the space of valid command-line invocations of a utility —
its options, arguments, and argument types —
and turns that into a grammar for fuzzing
[(FSE 2022)](/publications/2022/08/12/fse-clifuzzer/).
For structured binary formats such as MP4 and ZIP,
_FormatFuzzer_ compiles a binary template into a C++ parser, mutator,
and highly efficient generator,
which found previously unknown memory errors in ffmpeg and timidity
[(TOSEM 2024)](/publications/2024/02/10/effective/).

These techniques also hold up outside the lab.
Working with an industrial partner,
we reverse-engineered the protocol accepted by a virtualized packet processing
engine with no access to source code or internal documentation,
inferring its grammar at an F1 score of 0.94 and driving a blackbox test
campaign from it
[(ISSRE 2025)](/publications/2025/07/01/from/).

<h3>Reducing and repairing inputs</h3>

Delta debugging guarantees 1-minimality but pays for it with quadratic
worst-case behavior, caused by restarting the search at every partition level.
Re-examining _ddmin_, we showed that restarts are only needed at the
single-element level to preserve 1-minimality,
and that the quadratic worst case arises from causal chains rather than from
the restarts themselves.
The resulting algorithm, _drdd_, is a drop-in replacement for _ddmin_
that keeps the 1-minimality guarantee while skipping the redundant restarts,
and exposes a restart budget that trades minimality against linear worst-case
performance
[(ISSRE 2026)](/publications/2026/07/11/drdd/).

A closely related question is what to do with input that is broken rather than
merely large.
Data-repair techniques that rely on a format specification are of no use when
no specification exists.
_εRepair_ uses parser feedback alone to locate and correct inconsistencies,
producing repairs of substantially higher quality than _ddmax_ while losing far
less of the original data
[(ISSRE 2025)](/publications/2025/07/01/automatic/).
Our follow-up work generalizes this to maximal format-free repair,
lifting the restrictions on repair operations, repair locations, and the parser
properties earlier methods required
[(ASE 2026)](/publications/2026/06/20/ase-maximal/).

<h3>Knowing when a test campaign is done</h3>

A fuzzing campaign is guided by coverage, but the total reachable coverage of a
real program is unknown.
Without it, there is no principled way to say how much of the program remains
unexplored, or when to stop.
This has become one of the main threads in my group,
and it borrows its machinery from biostatistics:
species richness estimators, which infer how many species exist in a population
from how often each has been observed.

We first applied this family of estimators to mutation analysis,
asking whether they could estimate the number of *killable* mutants.
Across twelve frequency-based models and ten mature projects,
they could not: the estimators lacked the predictive power to be useful
[(ESEM 2024)](/publications/2024/06/20/empirical-evaluation/).

Applying them to coverage raises a harder problem —
there is no ground truth to check an estimate against.
We proposed an evaluation framework that synthesizes large programs with complex
control flow and known reachability,
together with a reliability check that works on real programs without ground
truth, by varying the size of the sampling unit
[(ICSME 2025)](/publications/2025/09/11/assessing/).
A further complication is that modern fuzzers use coverage feedback,
which introduces adaptive bias into the sample.
We are testing the hypothesis that this bias is minimized when singletons
(coverage observed exactly once) equal doubletons (observed exactly twice),
which would make that equilibrium a usable stopping criterion
[(NDSS Fuzzing Workshop 2026)](/publications/2026/03/01/evaluating-impact/).
Most recently, we asked whether parametric estimators would do better than the
non-parametric ones by assuming a distribution for coverage discovery.
Fitting Poisson, Exponential, Gamma, Gamma–Poisson, Negative Binomial, and
Zipf–Mandelbrot models across seven benchmarks,
we found that a better distributional fit does *not* translate into better
reachable coverage estimation
[(ISSRE 2026)](/publications/2026/08/13/better/).

<h3>Test suite and test case effectiveness</h3>

I have also worked on empirical evaluation of the effectiveness of different
coverage techniques. Our initial work [(ICSE 2014)](/publications/2014/05/31/icse-code/) towards addressing the
shortcomings of mutation analysis found that **statement coverage**, rather
than *branch* or *path* coverage is a better measure of mutation score,
and hence the quality of a test suite. This was substantiated by extensive
examination of over 200 real-world projects of various sizes, and this was
notably different from the prevailing wisdom which claimed that *branch* and
*path* coverage was obviously better.

We were also the first (and to date, the only ones) to find evidence
that  mutation score as well as coverage is inversely related to the
*residual defect density* of the program [(FSE 2016)](/publications/2016/11/13/fse-can/).
That is, the number of live mutants remaining is related to the actual bugs
remaining in the program.
Finally, our recent work [(ASE 2020)](/publications/2020/09/21/ase-revisiting/)
clarifies the relationship between test suite size and coverage. It settles
a long standing debate about how to interpret the effect of test suite size, and
shows how to correctly account for the suite size in empirical evaluations.

<!-- PhD Supervisors: [Prof. Dr. Carlos Jensen](http://dblp.uni-trier.de/pers/hd/j/Jensen:Carlos)
and [Prof. Dr. Alex Groce](http://dblp.uni-trier.de/pers/hd/g/Groce:Alex)<br/> 
<h3>Research</h3> -->

<h3>Mutation analysis</h3>
My primary focus during my PhD was mutation analysis of programs, and especially how to make mutation analysis a workable technique for real-world developers and testers.

<!--h5>Overview of publications</h5>
[<img src="/resources/img-publications.svg" alt="Publications" title="Publications" width="550px" align='center'>](/publications) -->

Mutation analysis is a method of evaluating the quality of software test suites
by introducing simple faults into a program. A test suite's ability to detect
these mutants, or artificial faults, is a reasonable proxy for the effectiveness
of the test suite. While mutation analysis is the best technique for test suite
evaluation we have, it is also rather computationally and time intensive,
requiring millions of test suite runs for even a moderately large software project.
This also means that mutation analysis is effectively impossible to use by
developers and practicing testers working on real-world problems, and who need
to evaluate whether their current test suites are adequate. Unfortunately, most
of the research done in mutation analysis has been done on a small number of
subject programs, small in size, and that have test suites with high coverage
and adequacy -- something that is a rarity in real-world development
(at least at early development stages).

My research [(ISSRE 2014)](/publications/2014/11/03/issre-mutations/)
evaluated whether the faults produced by mutation analysis were representative
of real faults. Our examination of over 5,371 projects in four different
programming languages found that the faults used by mutation analysis are rather
simplistic in practice compared to real-world bugs (in terms of the size of code
change).

As an initial step towards reducing the computational requirements of mutation
analysis, I investigated techniques used for mutation analysis, and invented a
[new algorithm](/publications/2016/05/14/icse-topsy/) (ICSE 2016 abstract) for
faster mutation analysis, taking advantage of redundancy in execution between
similar mutants. Further, I was able to identify how combinatorial evaluation
could be used for evaluating equivalent mutants [(ISSRE 2015)](/publications/2015/11/05/issre-how/).

Next, I compared the effectiveness of current techniques for reducing mutants to
be evaluated such as operator selection and stratum based sampling and found
that they offer surprisingly little advantage (less than 10% for stratum
sampling and negative for operator selection) compared to simple random sampling
in multiple evaluation criteria.
My research [(ICSE 2016)](/publications/2016/05/14/icse-on/) comparing the
effectiveness of the theoretical best mutation selection methods with random
sampling found that **even under oracular knowledge of test kills**, mutation
selection methods can at best be less than
20% better than random sampling, and are often much worse. Interestingly, there
is no such limit on how the amount of efficiency that can be achieved by the
addition of new operators. This discovery suggests that effort should be spent
on finding newer and relevant mutation operators rather than removing the
operators in the name of effectiveness. **This research also effectively settled
the long standing debate on the utility of mutation reduction strategies such
as operator selection in favor of random sampling**.

Finally, we were able to conclusively prove the _coupling effect_ theoretically,
as well as quantify its impact empirically [(ICST 2017)](/publications/2017/03/13/icstw-the-theory/).
The *coupling effect* is one of the corner stones of *mutation analysis*, and
our research provided the much needed clarification on
the relation between simple faults that mutants represent and higher order
faults that are common in real world programs.

Mutation analysis has since come back into my work from an unexpected direction.
Fuzzers are evaluated almost entirely by the coverage they reach and the crashes
they find, both of which saturate and are easy to overfit to.
Mutation score is the natural yardstick instead —
it subsumes coverage measures and supplies a large, diverse set of faults —
but the cost of evaluating each mutant independently made it unaffordable for
fuzzing.
We laid out the obstacles in the way
[(arXiv 2022)](/publications/2022/01/27/arxiv-mutation/),
then showed that modern techniques for pooling multiple mutations into a single
execution bring the cost down far enough to evaluate and compare fuzzers with
mutation analysis for the first time
[(Usenix Security 2023)](/publications/2023/04/26/systematic/).
Today's fuzzers detect only a small fraction of mutants,
which we read as a challenge for the field rather than a verdict on the method.
Mutants are also useful as fuzzing *targets*:
splitting a fuzzing budget between the program and its mutants explores more
behaviors than spending all of it on the program itself
[(NDSS Fuzzing Workshop 2022)](/publications/2022/04/24/ndss-first-fuzz-the-mutants/).

<!--
<h3>Implementation</h3>
The ideas from my research have resulted in two practical implementations -- [MuCheck](https://hackage.haskell.org/package/MuCheck) for Haskell, and [Xmutant](https://pypi.python.org/pypi/xmutant) for Python. I am also a contributor for [PIT](http://pitest.org/) mutation analysis system for Java, and [Rubocop](https://github.com/bbatsov/rubocop), a static analyzer for Ruby.
-->

<h3>Practice</h3>
My interest in the quality of programs is informed by a wealth of practical
knowledge from the Industry. Before joining the Ph.D. program, I worked in the
software industry as a developer for ten years, where I was part of the web and
proxy server development teams at [Quark Media House](http://www.quark.com/),
and [Sun Microsystems](http://www.sun.com/).
My primary area of interest was the web caches,  particularly the distributed
caching systems and protocols. I participated in the [OpenSolaris](https://www.openindiana.org/)
effort, where I was the maintainer of multiple open source packages. I have
also contributed to the Apache HTTPD project, in core and mod_proxy modules.
During my Ph.D., I worked at [Puppet Labs](https://puppet.com/) where I
contributed extensively towards the functionalities in the Solaris Operating
system, and at [Galois](https://galois.com/) where I contributed to the
visualization of effectiveness of one of the vulnerability mitigation approaches.

<hr>
<b>IMPORTANT: If you are my student, and facing _any_ sort of difficulties, please
do [contact me](/contact). I will be happy to talk to you, and help you in any way. </b>


