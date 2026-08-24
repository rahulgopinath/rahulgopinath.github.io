---
layout: page
header: Projects
title : Information for Potential Students
header : Information for Potential Students
group: navigation
exclude: true
---

> **Notice (August 2026): I am not taking on new students in any category
> — undergraduate interns, Honours, Dalyell, Masters, MPhil, or Ph.D.**
>
> I am overextended with the students I already supervise,
> and this will remain so until further notice.
> The projects and application instructions below are kept for reference,
> and will apply again when I reopen applications.
> Until then, please do not send an application.

# Important

Before you mail me or talk to me,
please work through [fuzzingbook](https://fuzzingbook.org) and [debuggingbook](https://debuggingbook.org),
and say explicitly in your application that you have done so.
My current research builds on the foundational ideas in these two textbooks,
so a shared starting point saves us both time.
If you have open source contributions or previously published research,
include them in your application.

**Please use the subject line format given in each section below.**
I use a script to sort student email, so a correctly formatted subject gets you a faster reply.

# <a id='undergrad' href='#undergrad'>Undergrad Summer Internship Applicants</a>

<!-- Please check the
[arch-india](https://arch-india.org/australia-india-research-students-fellowship-program?mc_cid=b1c3b6fef9&mc_eid=17e9b2f0e6) scholarship.
Applications typically open in October, and closes in November. University of Sydney also has a competitive summer reserch program for very talented undergraduate students. -->

If you are at an Indian institution and looking for a summer internship,
please note that the Vacation Research Internship (VRI) program does not fund students
without Australian permanent residency or citizenship.
Unfortunately, this means I cannot fund your research at present.
I consider remote supervision only when there is a co-supervisor
(faculty or postdoc) at your own institution.

I do not currently have the bandwidth to work with *sophomore* (second year)
students from Indian institutions.
If you are a final year thesis student, however,
I would be happy to co-advise your thesis,
especially if you have an upcoming industrial internship
where you could evaluate the effectiveness of the research.

<!-- However, I am happy to work with you if you would
like to work in areas of common interest, and I will be happy to provide
a reference and documentation. If this is the case, please indicate this in
your email.  -->

<!-- (Update: The School of Computer Science at University of Sydney is
looking into funding competitive Indian students. I will update this when
I have more information. Please watch this space. Latest (2024-03-04): The School of
Computer Science has decided not to support VRI for Indian students this year.)
-->
<!-- While the [website](https://www.sydney.edu.au/engineering/study/scholarships/engineering-vacation-research-internship-program.html) says that it is specific to Australia, I am happy to consider you if you are from outside Australia too, and have excellent credentials. -->

<!-- Before you apply, make yourself familiar with at least the basics of *regular expressions*,
*context-free grammars*, *parsing*, and *grammar based fuzzing*. You will get
sufficient information if you read the *fuzzingbook* and my posts.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Internship%20Application:%20(Full%20Name%20here)). -->

# <a id='honours' href='#honours'>Honours Applicants</a>

See [projects](#projects) for a list of projects.
I give preference to candidates who have worked with me previously on VRI projects.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Honours%20Application:%20(Full%20Name%20here)).

# <a id='dalyell' href='#dalyell'>Dalyell Research Project Applicants</a>

If you are an undergraduate,
you may want to look at [SCDL3991: Science Dalyell Individual Research Project](https://www.sydney.edu.au/units/SCDL3991).
It is a semester-long project.
If any of the projects I propose interests you,
or the general area of research does, please get in touch.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Dalyell%20Project%20Application:%20(Full%20Name%20here)).

# <a id='masters' href='#masters'>Masters Applicants</a>

See [projects](#projects) for a list of projects.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Masters%20Application:%20(Full%20Name%20here)).

# <a id='phd' href='#phd'>Ph.D. Applicants</a>

I have several ongoing projects you may find interesting.
These include, but are not limited to,
grammar inference, program repair, mutation analysis, program coverage,
debugging, fuzzing, and test oracles.
Pick one area, read up on it — especially if I have published on it —
and send me a paragraph on what you learned and what you would want to explore further.

I prefer to work with Ph.D. applicants for a few months on an ongoing project
before offering a position.
That way we get to know each other,
and we can each judge the fit better.

Note that for students from Iran and China,
[visa issues](https://twitter.com/ccanonne_/status/1595922255007035392) persist,
and the wait can exceed a year.
Until that is resolved,
unless you strongly prefer me as your supervisor,
please apply to countries that will not make you wait.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=PhD%20Application:%20(Full%20Name%20here)).

# <a id='projects' href='#projects'>Projects</a>

Here are several projects you can start with me.
Find one you like, think about it, do a bit of background research, and drop me a note.

**Eligibility.**
Unless a project says otherwise, I expect the same of every applicant:
you should be a fast learner,
with excellent programming skills (basic Python and Java),
strong problem-solving ability,
and the ability to work independently.
Where a project needs a different or additional skill set,
it says so under *Skills*.

**Outcome.**
Unless noted otherwise,
a project that goes well can be extended into a paper
at an A/A\* software engineering conference.

## <a id='ddforparsers' href='#ddforparsers'> Delta Debugging for Parsers</a>

In cybersecurity, your fuzzers can often come up with a massive input that causes a crash.
To debug the crash, one often needs a much smaller input that reproduces it.
HDD is an algorithm used to reduce the input size if the input conforms to a grammar.
However, it does not work well if the grammar is incomplete,
as it is in many handwritten parsers, and the input cannot be parsed.

In this project, we will explore input-repair based techniques
to repair and then parse the input,
and compare them with original delta debugging (which does not require a grammar)
and with coverage-based strategies for identifying hierarchies in the partially parsed input.

## <a id='errorcorrection' href='#errorcorrection'> Error Correction with Grammars </a>

*Skills:* the general requirements, plus comfort reading research papers.

Data aggregation and cleaning is one of the most important steps in data science.
The data may come from multiple sources and hence may not match the required format exactly.
This is especially an issue if the required format is a rich one
such as JSON, XML, or S-Expressions.
In such cases, we may have to rely on available error correction algorithms at best,
or manual labor at worst.
While numerous error correction algorithms exist,
error correction for context-free grammars still lags behind,
with the best known algorithm dating to Aho et al. in 1972, which extends Earley parsing.

In this project, we will explore how to implement faster error correction
for context-free grammars by extending Aho's algorithm,
and compare it with the original.
Two variations, using GLL and GLR parsing instead, can also be explored.

## <a id='optimizinggrammarfuzzers' href='#optimizinggrammarfuzzers'> Optimizing Grammar Fuzzers</a>

*Skills:* good Python, Java, and C; knowledge of assembly is excellent to have.
You will work with me directly on this project.

Grammar-based fuzzers are one of the most important tools in cybersecurity.
The effectiveness of fuzzing is often determined by the speed at which inputs can be generated,
so highly performant grammar fuzzers are crucial.
When building one, there are multiple trade-offs available.
These include fixing the depth of recursion —
at which point the fuzzer becomes an automaton
that can be implemented in code without subroutines —
or supercompiling the grammar (eliminating redundant procedure calls),
or superoptimizing the produced code (assembly level optimizations using solvers),
or finding better optimization techniques altogether.

This project will explore how to make grammar fuzzers much more performant,
and compare the result with the automata-based approach.

##  <a id='inferringcfg' href='#inferringcfg'>Inferring context-free grammars for blackbox programs</a>

Fuzzing blackbox programs that use an unknown but rich input structure
(for example, one conforming to a context-free grammar)
has traditionally been very difficult.
The problem is that any input that does not conform to the expected structure
gets rejected almost immediately, and never penetrates the actual program logic.
Hence there have been numerous recent attempts to infer the grammar from such programs
and to use the inferred grammars for fuzzing.
This has proven difficult, due to a theorem by Gold
which says that inferring context-free grammars from blackbox programs
is as hard as cracking RSA.

In this project, we will explore how to get around that requirement
by relaxing the opacity constraint a little.
We will assume the blackbox program will tell us
when an input is completely incorrect,
versus when it is a valid prefix that can be fixed by adding a suffix.
This lets us guess at the internal state of the program,
and hence infer the input grammar.

## <a id='reproduciblenotebooks' href='#reproduciblenotebooks'>Reproducible HTML Notebooks</a>

*Skills:* excellent JavaScript and basic Python.

*Outcome:* rather than a conference paper,
a successful project here may provide the foundation for a workshop
on reproducible software engineering, and be adopted by researchers worldwide.

Reproducibility is the core of science,
and software engineering unfortunately does not have a great reputation for it.
This project attempts to change that.
The idea is to start with WASM powered Jupyter notebooks
and bundle them into a completely self-contained HTML file,
which can hold implementations of algorithms
and be passed around and modified by other researchers and students.
The modified HTML files should be savable
using the [TiddlyWiki](https://tiddlywiki.com/) technique.

## <a id='mutationanalysisforfuzzers' href='#mutationanalysisforfuzzers'>Mutation Analysis for Fuzzers</a>

Fuzzers are test generators that specialize in producing millions of inputs at a time.
The next frontier of fuzzing is to incorporate better oracles — that is, verifiers of behavior.
For that to happen, we need evaluators that can verify behavior.
Mutation analysis is the gold standard here.
It works by generating thousands of possibly buggy variants of the given program
and checking how many of them are detected.
To use mutation analysis for fuzzing,
its computational cost needs to be brought under control.
One way is to evaluate multiple bugs in each execution.
To do that, we need to ensure the inserted bugs do not interact with each other.
This project will explore the best way to identify independent bugs so that they can be combined.

## <a id='sidechannelsforfuzzing' href='#sidechannelsforfuzzing'>Using side channels for feedback driven fuzzing</a>

*Skills:* expert C and UNIX knowledge.

Fuzzing is a premier technique in cybersecurity,
used by software engineers to ensure our systems are reliable
and by pen testers to identify possible avenues of attack.
Naive blackbox fuzzing is usually ineffective in practice,
and feedback from the program is necessary for fuzzing to work well.
Current tools such as AFL rely on extensive program instrumentation for that feedback,
which unfortunately limits their use:
many systems cannot be instrumented at all,
and in others instrumentation changes the behavior of the system.

One way to avoid instrumentation is to look at the memory contents at the end of execution,
the system calls that were made, and other side channels.
This project will explore such side channels —
especially memory and system calls —
to see whether we can do better than AFL at detecting faults in programs.

## <a id='testreductionslippage' href='#testreductionslippage'>Solving Test Reduction Slippage</a>

Fuzzers routinely produce massive and incomprehensible inputs that can crash a program.
Such inputs cannot be debugged
unless a much smaller input that reproduces the crash can be obtained.
Delta debugging is an algorithm used to reduce a test case to something comprehensible.
One of its problems is that while reducing the input,
it may produce new inputs that induce an unrelated crash.
This is called test reduction slippage,
and it can waste a programmer's time on an unrelated problem.
This project will explore how to solve test reduction slippage using execution grammars,
and compare that with the effectiveness of using simple coverage.

## <a id='betterdd' href='#betterdd'>Improving Delta Debugging</a>

Delta debugging is one of the best known algorithms for quick reduction of test cases,
and it operates in $O(log(n))$ in the best case.
The problem is that its worst case is $O(n^2)$.
Can we improve that bound?
What about Hierarchical Delta Debugging?
Finally, can we improve delta debugging in general,
even when program semantics must be respected (as in C, Java, and so on)?
Can we rely on the original delta debugging assumption of independence of deltas,
or are stricter assumptions required?

## <a id='grammarcoverage' href='#grammarcoverage'>Better Grammar Coverage</a>

Grammar coverage has a [strong](https://ieeexplore.ieee.org/document/8952419) [correlation](https://www.fuzzingbook.org/html/GrammarCoverageFuzzer.html) with whitebox program coverage.
[Havrikov et al.](https://ieeexplore.ieee.org/document/8952419) discuss how to obtain a stronger grammar coverage metric
using k-paths, which look at nesting contexts.
But is this the [best metric](https://dl.acm.org/doi/10.1145/3426425.3426946) for grammar coverage?
What about non-nesting (peer) nonterminals in the same rule?
This project will investigate which grammar coverage metric performs best
for evaluating the quality of generated input strings for fuzzing.

## <a id='probabilisticgrammars' href='#probabilisticgrammars'>Probabilistic Grammars</a>

[Soremekun et al.](https://publications.cispa.saarland/3167/7/inputs-from-hell.pdf) showed how to extract the characteristics of a set of inputs
as a probabilistic grammar.
In this project, we will investigate how to extend the probabilistic grammar further
by incorporating depth and position.

## <a id='binaryformats' href='#binaryformats'>Binary Formats</a>

*Outcome:* a paper at an A/A\* cybersecurity conference rather than a software engineering one.

In this project, we will investigate how to extract binary format specifications,
and how best to fuzz binary formats.

# <a href='#funding' id='funding'>Funding</a>

## India Specific

* [SPARC](https://sparc.iitkgp.ac.in/funding_budget.php)
* [Arch-India](https://arch-india.org/australia-india-research-students-fellowship-program?mc_cid=b1c3b6fef9&mc_eid=17e9b2f0e6)
* [Maitri](https://scholarshiparena.in/australian-maitri-scholarship-for-indian-students/)
* [Australia Grants](https://www.dfat.gov.au/people-to-people/foundations-councils-institutes/australia-india-council/grants)

<!-- TODO: this section was empty on the live page. Add Australian funding links.
## Australia Specific
-->
