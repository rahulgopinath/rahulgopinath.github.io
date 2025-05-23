---
layout: page
header: Projects
title : Information for Potential Students
header : Information for Potential Students
group: navigation
exclude: true
---
# Important

For all students, please work through, and make yourself familiar with [fuzzingbook](https://fuzzingbook.org) and [debuggingbook](https://debuggingbook.org) **before** you mail me or talk to me. Please explicitly note in your application that you have gone through both. My current research is based on the foundational ideas discussed in these introductory text books, and it helps to have a common understanding. If you have opensource contributions or previously published research, please include it in the application. **Please use to the specified subject format for applications. I use a script to identify and hence respond faster to student emails**.


# <a id='undergrad' href='#undergrad'>Undergrad Summer Internship Applicants</a>

<!-- Please check the
[arch-india](https://arch-india.org/australia-india-research-students-fellowship-program?mc_cid=b1c3b6fef9&mc_eid=17e9b2f0e6) scholarship.
Applications typically open in October, and closes in November. University of Sydney also has a competitive summer reserch program for very talented undergraduate students. -->

If you are in one of the Indian Institutions, looking for summer internship,
please note that VRI does not include funding for students without either a PR
or citizenship of Australia. Unfortunately, this means that I am unable to fund
your research at this point. Remote supervision is only considered if there is
a co-supervisor (faculty/postdoc) at the Indian institution.
I do not at present have the bandwidth to work with *sophomore* students
(second year) from Indian institutions. However, if you are a final year thesis
student, I would be happy to co-advise you on your thesis, especially if you
have an upcoming industrial internship, where you can potentially evaluate the
effectiveness of some of your research.

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

Please see [projects](#projects) for a list of projects. Please note that
I give preference to candidates who have worked with me previously on VRI
projects.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Honours%20Application:%20(Full%20Name%20here)).

# <a id='honours' href='#honours'>Daytell Research Project Applicants</a>

If you are an undergrad, you may look at [SCDL3991: Science Dalyell Individual Research Project](https://www.sydney.edu.au/units/SCDL3991) from Sydney University. It is a semester long
project, and if you like any of the projects I propose, or the general area of
research, please contact me.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Daytell%20Project%20Application:%20(Full%20Name%20here)).

# <a id='masters' href='#masters'>Masters Applicants</a>

Please see [projects](#projects) for a list of projects.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=Masters%20Application:%20(Full%20Name%20here)).

# <a id='phd' href='#phd'>Ph.D. Applicants</a>

I have several ongoing projects that you may find interesting. These include,
but not limited to grammar inference, program repair, mutation analysis,
program coverage, debugging, fuzzing, oracles and test oracles. Pick one area,
read up on it (especially if I have publication on it), and send me a paragraph
on what you learned, and what you may want to explore further.

In general, I prefer to work with the Ph.D. applicants for a few months on an
ongoing project before offering a position. This way, we will get to know each
other, and can evaluate each others suitability better

Note that for students form Iran and China, [visa issues](https://twitter.com/ccanonne_/status/1595922255007035392) persist, and can be more than an year for the visa. So, until
this gets resolved, unless you strongly prefer me to be your supervisor, please
apply to other countries that does not make you wait.

Please use [this format to apply](mailto:rahul.gopinath@sydney.edu.au?subject=PhD%20Application:%20(Full%20Name%20here)).

# <a id='projects' href='#projects'>Projects</a>
Here are several possible projects you can start with me. Find one of your
choice, think about it, do a bit of background research, and drop me a note.

## <a id='ddforparsers' href='#ddforparsers'> Delta Debugging for Parsers</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary),
problem-solving, as well as the ability to work independently, are required.

### Description

In cybersecurity, your fuzzers can often come up with a massive input that causes a crash. To debug the crash, one often needs a much smaller input that reproduces the crash.  HDD is an algorithm used to reduce the input size if the input conforms to a grammar.  However, it does not work well if the grammar is incomplete, such as in many handwritten parsers and the input can’t be parsed.

In this project, we will explore input-repair based techniques to repair and then parse the input and compare it with using original delta debugging (which does not require a grammar) and coverage-based strategies to identify hierarchies in the partially parsed input.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in software engineering.

## <a id='errorcorrection' href='#errorcorrection'> Error Correction with Grammars </a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), understanding research papers, problem-solving, as well as the ability to work independently are required.

### Description

Data aggregation and cleaning is one of the most important steps in data science. The data may come from multiple sources and, hence, may not match the required format exactly. This is especially an issue if the required format is a rich format like JSON, XML, S- Expr etc. In such cases, we may have to rely on available error correction algorithms (at best) or manual labour (at worst). While numerous error correction algorithms exist, error correction for context-free grammars is still lagging with the best-known algorithm from 1972 from Aho et al. which extends Earley parsing.

In this project, we will explore how to implement faster error correction for context-free grammars by extending the Aho's algorithm and compare it with the original.

Two possible variations using GLL and GLR grammars instead can also be
explored.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in software engineering.

## <a id='optimizinggrammarfuzzers' href='#optimizinggrammarfuzzers'> Optimizing Grammar Fuzzers</a>

### Eligibility

You will work with the supervisor directly for this project. You should be a fast learner. Excellent skills in programming (Good Python, Java, and C Skills. Knowledge of assembly is excellent to have.), problem-solving, as well as the ability to work independently are required.

### Description

Grammar based Fuzzers are one of the most important tools in cybersecurity. The
effectiveness of fuzzing is often determined by the speed at which inputs can be generated, and highly performant grammar fuzzers are crucial. When making a grammar fuzzer, there are multiple trade-offs that can be made to make it performant. These include fixing the depth of recursion, at which point it becomes automata that can be easily implemented in code without subroutines, or supercompiling the grammar
(i.e., eliminating redundant procedure calls), or superoptimizing the produced code (i.e., assembly level optimizations using solvers), or come up with other better optimization techniques.

This project will explore how to make grammar fuzzers much more performant and
compare it with the automata-based approach.

##  <a id='inferringcfg' href='#inferringcfg'>Inferring context-free grammars for blackbox programs</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Fuzzing blackbox programs that use an unknown but rich input structure (e.g. conforms to a context-free grammar) has been traditionally very difficult. The problem is that any input that does not conform to the expected input structure will get rejected almost immediately and will not penetrate the actual program logic. Hence, there have been numerous recent attempts to infer the grammar from such blackbox programs, and to use such inferred grammars for fuzzing. This has been, however, rather difficult due to a theorem by Gold which says that inferring context-free grammars from blackbox programs is as difficult as cracking RSA.

In this project, we will explore how to get around this requirement by relaxing the opacity constraint a little bit. We will assume that the blackbox program will tell us when the input is completely incorrect, verses whether the input is a valid prefix that can be fixed by adding some suffix. This can allow us to guess at the internal state of the program, and hence, infer the input grammar.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in software engineering.

## <a id='reproduciblenotebooks' href='#reproduciblenotebooks'>Reproducible HTML Notebooks</a>

### Eligibility
You should be a fast learner. Excellent skills in programming (Excellent JavaScript knowledge, and basic Python skills are necessary), problem-solving, as well as the ability to work independently are required.

### Description

Reproducibility is the core of science, and software engineering unfortunately doesn’t have a great reputation when it comes to reproducibility. This project attempts to change that.  The idea is to start with the WASM powered Jupyter notebooks, bundle them into a completely self-contained HTML file which can contain implementations of algorithms, and can be passed around and modified by other researchers and students. The modified HTML files should be savable using the TiddlyWiki (https://tiddlywiki.com/) technique.

This project, if completed successfully, may provide a starting foundation for a workshop on reproducible software engineering, and lead to being adopted by researchers worldwide.

## <a id='mutationanalysisforfuzzers' href='#mutationanalysisforfuzzers'>Mutation Analysis for Fuzzers</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Fuzzers are test generators that specialize in producing millions of inputs at a time. The next frontier of fuzzing is to incorporate better oracles, that is, verifiers of behavior.  However, for this to happen, we need evaluators that can verify behavior. Mutation analysis is the gold standard for evaluating behavior. It accomplishes this by generating thousands of possibly buggy variants of the given program and checking how many of these are detected. To use mutation analysis for fuzzing, its computational expenditure needs to be brought under control. One way to do that is to evaluate multiple bugs at the same time in each execution. However, to achieve that, we need to ensure that the inserted bugs do not interact with each other. This project will explore the best way to identify independent bugs so that they can be combined.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in software engineering.

## <a id='sidechannelsforfuzzing' href='#sidechannelsforfuzzing'>Using side channels for feedback driven fuzzing</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (expert C & UNIX knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Fuzzing is a premier technique in Cybersecurity and is used by software engineers to ensure that our systems are reliable, and by pen testers to identify possible avenues of attack. Naive fuzzing (blackbox) is usually ineffective in practice, and feedback from the program is necessary for effective fuzzing. Current fuzzing tools such as AFL rely on extensive program instrumentation for feedback, which unfortunately limits their use. Many systems can't be instrumented at all, and in some other systems, instrumentation can change the behaviour of the system.

One way we can avoid instrumentation is by looking at the memory contents at the end of execution, the system calls that were made, and other side channels. This project will explore such side channels, especially memory and system calls to find if we can do better than AFL in detecting faults in programs.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in software engineering.

## <a id='testreductionslippage' href='#testreductionslippage'>Solving Test Reduction Slippage</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Fuzzers routinely produce massive and incomprehensible inputs that can crash a program. Such inputs can't be debugged unless a much smaller input that reproduces the crash can be obtained. Delta debugging is an algorithm used to reduce the input of a test case to make it comprehensible.  One of the problems with delta debugging is that while reducing the input, new inputs may be produced that induces an unrelated crash. This is called test reduction slippage. The problem is that slippage can result in programmers time being wasted on an unrelated problem. This project will explore how to solve the test reduction slippage using execution grammars and compare it to the effectiveness of using simple coverage.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in Software engineering.

## <a id='betterdd' href='#betterdd'>Improving Delta Debugging</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Delta debugging is one of the best known algorithms for quick reduction of test cases, and it operates with $O(log(n))$ best case. The problem with Delta-Debugging is that it has a worst case $O(n^2)$. Can we improve this bound? What about Hierarchical Delta Debugging? Finally, can we improve delta debugging in common even when program semantics is required (such as C,Java etc.)? Can we rely on the original Delta Debugging assumptions? (Independence of deltas), or are stricter assumptions required?

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in Software engineering.

## <a id='grammarcoverage' href='#grammarcoverage'>Better Grammar Coverage</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

Grammar coverage has a [strong](https://ieeexplore.ieee.org/document/8952419) [correlation](https://www.fuzzingbook.org/html/GrammarCoverageFuzzer.html) with whitebox program coverage. [Havrikov et al.](https://ieeexplore.ieee.org/document/8952419) discusses how one can obtain a stronger grammar coverage metric using k-paths which looks at nesting contexts. However, this the [best metric](https://dl.acm.org/doi/10.1145/3426425.3426946) for grammar coverage? What about non-nesting (peer) nonterminals in the same rule? This project will investigate what grammar coverage metric is the best performing metric for evaluating quality of generated input strings for fuzzing.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in Software engineering.

## <a id='probabilisticgrammars' href='#probabilisticgrammars'>Probabilistic Grammars</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description

[Soremekun et al.](https://publications.cispa.saarland/3167/7/inputs-from-hell.pdf) showed how to extract the characteristics of a set of inputs as a probabilistic grammar. In this project, we will investigate how to extend the probabilistic grammar further by incorporating depth, and position.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in Software engineering.

## <a id='binaryformats' href='#binaryformats'>Binary Formats</a>

### Eligibility

You should be a fast learner. Excellent skills in programming (Basic Python & Java knowledge is necessary), problem-solving, as well as the ability to work independently are required.

### Description
In this project, we will investigate how to extract binary format specifications, and how to best fuzz binary formats.

This project, if completed successfully, may be extended for a paper in one of the A/A* conferences in Cybersecurity.

# <a href='#funding' id='funding'>Funding</a>

## India Specific

* [SPARC](https://sparc.iitkgp.ac.in/funding_budget.php)
* [Arch-India](https://arch-india.org/australia-india-research-students-fellowship-program?mc_cid=b1c3b6fef9&mc_eid=17e9b2f0e6)
* [Maitri](https://scholarshiparena.in/australian-maitri-scholarship-for-indian-students/)
* [Australia Grants](https://www.dfat.gov.au/people-to-people/foundations-councils-institutes/australia-india-council/grants)

## Australia Specific

