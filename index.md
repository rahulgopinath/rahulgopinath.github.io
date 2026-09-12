---
layout: default
menu: Rahul Gopinath
weight: 1
---

<!--b>IMPORTANT: I am recruiting students for my group at Sydney University.
If you are either an *excellent programmer*, or a strong student in *Automata and
Theory of Computation*, [please drop me a note](/contact/). </b-->



I am a lecturer at the [University of Sydney](https://www.sydney.edu.au/),
where I work on **software reliability**, including its security-critical cases.
I received my Ph.D. in 2017 from the [School of EECS at Oregon State University](http://eecs.oregonstate.edu/),
and did my postdoc at
[CISPA Helmholtz Center for Information Security](http://cispa.saarland), Germany.
<!-- PhD Supervisors: [Prof. Dr. Carlos Jensen](http://dblp.uni-trier.de/pers/hd/j/Jensen:Carlos)
and [Prof. Dr. Alex Groce](http://dblp.uni-trier.de/pers/hd/g/Groce:Alex)<br/>
-->

My research asks a single question:
*how much confidence can we justify that a software system will not fail in operation?*

Failures arrive by two routes.
Most arrive by chance, through inputs nobody anticipated.
Some arrive by design, through an adversary searching for precisely the input
that breaks you.
The engineering problem is the same either way —
find the inputs that provoke failure,
measure whether the search was thorough,
and estimate what it missed —
which is why the same techniques serve reliability engineering and security.
Fuzzing is the clearest case:
it is automated test generation,
and it is also how most modern vulnerabilities are found.
I treat security as the adversarial corner of reliability rather than as a
separate discipline,
and the work below is organized accordingly.

The question is most urgent where failure is expensive.
In high-consequence software — industrial control, instrumentation, medical
devices, critical infrastructure — what matters is not whether testing found
bugs, but whether the evidence gathered justifies the confidence being claimed.
That is a quantitative question, and it is largely unsolved.

Dependability engineering names four means of getting there:
preventing faults, removing them, tolerating those that remain,
and forecasting what is left.
My work covers the last three, in five parts that build on one another:

* **What remains?** After a test campaign ends, how many faults are still there?
* **Can we trust the measurement?** Is our estimate of test quality itself sound?
* **How do we provoke the failures?** Reaching a fault requires inputs the system will accept, whether we are testing or attacking.
* **How do we diagnose one?** A failure report is only useful if someone can act on it.
* **What if the damage is already done?** Corrupted data has to be recovered, not discarded.

<h3>Estimating what remains</h3>

The oldest question in software reliability is when to stop.
Classical software reliability growth models answer it by fitting a curve to the
arrival of failures over time and extrapolating to the faults not yet seen.
My group approaches the same question from a different direction,
borrowing from ecology:
*species richness estimation*,
which infers how many species exist in a population
from how often each one has been observed.
Coverage elements and killable faults behave, statistically, much like species.

The thread starts with a result on residual defects.
We were the first, and to date the only ones, to find evidence
that mutation score and coverage are inversely related to the
*residual defect density* of a program
[(FSE 2016)](/publications/2016/11/13/fse-can/):
the number of live mutants remaining is related to the number of real bugs
remaining.

We then asked whether richness estimators could count the *killable* mutants in
a program directly.
Across twelve frequency-based models and ten mature projects, they could not —
the estimators lacked the predictive power to be useful
[(ESEM 2024)](/publications/2024/06/20/empirical-evaluation/).
A negative result, but a load-bearing one:
it told us the difficulty lies in the sampling process, not the estimator.

Applied to coverage, the problem is harder still,
because there is no ground truth to check an estimate against.
We proposed an evaluation framework that synthesizes large programs with complex
control flow and *known* reachability,
paired with a reliability check that works on real programs without ground truth,
by varying the size of the sampling unit
[(ICSME 2025)](/publications/2025/09/11/assessing/).
A further complication is that modern test generators use coverage feedback,
which biases the sample adaptively.
We are testing the hypothesis that this bias is minimized when singletons
(coverage seen exactly once) equal doubletons (seen exactly twice),
which would give a principled stopping criterion for a campaign
[(NDSS Workshop 2026)](/publications/2026/03/01/evaluating-impact/).
Most recently we asked whether parametric estimators would beat non-parametric
ones by assuming a distribution for coverage discovery.
Fitting Poisson, Exponential, Gamma, Gamma–Poisson, Negative Binomial, and
Zipf–Mandelbrot models across seven benchmarks,
we found that a better distributional fit does *not* yield better estimates
[(ISSRE 2026)](/publications/2026/08/13/better/).

This bears directly on assurance.
A safety case or an assurance argument must justify a claimed level of confidence
with evidence, and the usual evidence is a test campaign that has ended.
If we cannot say what that campaign missed, we cannot say what the claim is worth.
There is a long-running argument in the software safety literature that software
reliability cannot be quantified to the levels critical systems demand,
and our results so far support the skeptical side of it:
the estimators available today are not dependable enough to carry a confidence
claim on their own.
I would rather establish that clearly than overstate what the methods can do.
Closing that gap — knowing when a campaign has genuinely saturated, and with what
error bars — is the aim of this thread.

<h3>Trusting the measurement</h3>

Any claim about residual risk rests on a measurement of test quality,
so the measurement has to be sound.
Mutation analysis — seeding artificial faults and counting how many the tests
detect — is the best instrument we have, and my Ph.D. was devoted to making it
usable on real systems.

In dependability terms this is software fault injection,
and fault injection does two jobs at once.
It serves fault removal, by exposing tests that fail to detect what they should.
It also serves fault forecasting:
the estimation work above runs on mutation analysis,
and the link between mutation score and residual defects is what makes that
forecast possible at all.
I treat the two separately here because an instrument has to be trusted before
the estimates built on it mean anything.

I first asked whether seeded faults resemble real ones.
Examining over 5,371 projects in four languages,
we found the faults used by mutation analysis are simplistic compared to
real-world bugs in terms of the size of the code change
[(ISSRE 2014)](/publications/2014/11/03/issre-mutations/).
To reduce its cost I developed an algorithm exploiting execution redundancy
between similar mutants
[(ICSE 2016)](/publications/2016/05/14/icse-topsy/),
and showed how combinatorial evaluation can identify equivalent mutants
[(ISSRE 2015)](/publications/2015/11/05/issre-how/).

I then tested the prevailing belief that mutants should be *selected* rather than
sampled.
Comparing the theoretical best selection methods against random sampling,
I found that **even under oracular knowledge of test kills**,
selection can be at best less than 20% better than random sampling,
and is often much worse
[(ICSE 2016)](/publications/2016/05/14/icse-on/).
There is no such ceiling on the gains from *adding* operators,
which says effort belongs in finding new operators rather than discarding
existing ones.
**This settled a long standing debate on mutation reduction strategies in favor
of random sampling.**
Finally, we proved the _coupling effect_ theoretically and quantified it
empirically
[(ICST 2017)](/publications/2017/03/13/icstw-the-theory/),
clarifying how the simple faults mutants represent relate to the higher order
faults common in real programs.

Coverage is the other common instrument, and it is widely misread.
Our work found that **statement coverage**, not *branch* or *path* coverage,
is the better predictor of mutation score across more than 200 real-world
projects
[(ICSE 2014)](/publications/2014/05/31/icse-code/),
contradicting the prevailing wisdom of the time.
We later settled how test suite *size* should be accounted for in empirical
evaluations
[(ASE 2020)](/publications/2020/09/21/ase-revisiting/).

These instruments now do work they were not built for.
Automated test generators are judged almost entirely by coverage reached and
crashes found, both of which saturate and invite overfitting.
Mutation score is the better yardstick, but evaluating each mutant independently
made it unaffordable.
We set out the obstacles
[(arXiv 2022)](/publications/2022/01/27/arxiv-mutation/),
then showed that pooling multiple mutations into a single execution brings the
cost down far enough to compare generators by mutation score for the first time
[(Usenix Security 2023)](/publications/2023/04/26/systematic/).
Mutants also serve as intermediate *targets*: splitting a generation budget
between a program and its mutants explores more behavior than spending all of it
on the program
[(NDSS Workshop 2022)](/publications/2022/04/24/ndss-first-fuzz-the-mutants/).

<h3>Provoking the failures: fuzzing</h3>

None of the above is measurable without inputs that actually reach the code.
Fuzzing — generating large volumes of unexpected and possibly invalid input,
and watching for anomalous behavior — is the cheapest way to get them,
and it is simultaneously the dominant technique in vulnerability discovery.
A system that rejects every invalid input and behaves correctly on valid ones is
robust under fuzzing, and fuzzing it before release finds the failures before
users and attackers do.

This work produced [the fuzzing book](https://www.fuzzingbook.org/),
an open textbook now used by students and practitioners worldwide.
[![Fuzzingbook Image](/resources/fuzzingbook_image.webp)](https://www.fuzzingbook.org/)
It takes a reader from simple random generators through fuzzers that analyze the
system under test to infer its expected inputs and use feedback from earlier runs
to steer later ones.

The hard part is reaching deep code.
Most systems accept only highly structured input,
and a generator that cannot produce valid structure never gets past the parser.
Real systems compound this: an HTTP request wrapping a JSON object encoding an
RPC call encoding a custom structure defeats coverage-guided fuzzing entirely,
because the paths explored are identical for simple and complex inputs.

Our first approach generated valid inputs against an unmodified parser.
Symbolic execution fails here through *path explosion*,
so we [built](https://arxiv.org/abs/1810.08289) a lightweight alternative,
[Pygmalion](https://github.com/vrthra/pygmalion),
which iteratively corrects a generated prefix until it is accepted.
It works for single pass parsers
[(PLDI 2019)](/publications/2019/06/22/pldi-parser/),
for parsers with a lexical stage
[(ISSTA 2020)](/publications/2020/07/18/issta-learning/),
and even for
[systems that cannot be instrumented](https://arxiv.org/abs/2012.13516),
such as embedded and remote systems — a common constraint in security testing,
where the target is frequently a binary nobody can recompile.

Correcting one input at a time is still expensive.
So we [built](https://github.com/vrthra/mimid) _Mimid_,
which recovers the input structure a parser expects as a *context-free grammar*
by dynamic analysis of program runs
[(FSE 2020)](/publications/2020/11/08/fse-mining/),
covering the full range from ad hoc handwritten parsers to parser combinators.
With a grammar in hand the bottleneck moves to generation speed,
so we [adapted](/publications/2019/11/18/arxiv-building/) ideas from language
implementation and virtual machine optimization to build the
[F1 fuzzer](https://github.com/vrthra/f1), which produces millions of inputs
per second.

![Fuzzing pipeline](/resources/totalfuzz.webp)

Since then we have pushed inference in several directions.
Reimplementing the GLADE algorithm, we found its reported effectiveness overly
optimistic and in some cases measured against the wrong language
[(PLDI 2022)](/publications/2022/04/04/pldi-synthesizing/) —
replication matters here, because grammar inference results are easy to overstate.
_CLIFuzzer_ mines the valid command-line invocations of a utility into a grammar
[(FSE 2022)](/publications/2022/08/12/fse-clifuzzer/),
and _FormatFuzzer_ compiles a binary template into a parser, mutator, and
generator for structured binary formats such as MP4 and ZIP,
finding previously unknown memory errors in ffmpeg and timidity
[(TOSEM 2024)](/publications/2024/02/10/effective/).

The techniques hold up outside the lab.
With an industrial partner we reverse-engineered the protocol accepted by a
virtualized packet processing engine,
with no access to source code or internal documentation,
inferring its grammar at an F1 score of 0.94 and driving a full blackbox test
campaign from it
[(ISSRE 2025)](/publications/2025/07/01/from/).
Blackbox conditions of this kind are the norm in industrial and security
settings, where instrumentation is barred by legal, operational, or safety
constraints.

<h3>Diagnosing failures</h3>

A detected failure is only useful if someone can act on it,
and generated inputs are typically enormous and unreadable.
Test case reduction shrinks them, but a minimal input still does not say *what*
went wrong, and casual inspection often suggests the wrong hypothesis.
We [built](/publications/2020/07/18/issta-abstracting/) _DDSET_,
which identifies the parts of an input responsible for the failure and abstracts
away the rest.
The resulting _evocative patterns_ — for example `((<expr>))` when nested
parentheses are the cause — are precise and readable.
This work received the __ACM SIGSOFT Distinguished Paper__ award
[(ISSTA 2020)](/publications/2020/07/18/issta-abstracting/).

An evocative pattern is a specialization of the input grammar.
At [ICSE 2021](/publications/2021/05/22/icse-input-algebras/) we showed how to
turn a base grammar and a pattern into a specialized grammar guaranteed to
produce the evocative fragment in every input,
and how to combine patterns under conjunction, disjunction, and negation to form
evocative *expressions*.

![Evocative Expressions](/resources/ewok.webp)

The expression above specializes a JSON grammar so that every input has at least
one empty key and no null key values,
while still parsing *any* input meeting that specification.
Patterns can be written by hand or mined from existing bugs with DDSET,
and the expressions serve both as precise generators and as semantic pattern
matchers in the spirit of Semgrep.

Reduction itself needed work.
Delta debugging guarantees 1-minimality but pays quadratically for it,
restarting at every partition level.
Re-examining _ddmin_, we showed restarts are needed only at the single-element
level to preserve 1-minimality,
and that the quadratic worst case comes from causal chains rather than restarts.
_drdd_ is a drop-in replacement keeping the guarantee while dropping the
redundant restarts, with a tunable restart budget trading minimality against
linear worst-case behavior
[(ISSRE 2026)](/publications/2026/07/11/drdd/).

<h3>Tolerating corrupt data</h3>

Not every fault can be removed before deployment,
and not every damaged input is the program's fault.
Data arrives corrupted through entry error, truncated transmission,
storage decay, inconsistent formatting,
and specifications that changed underneath it.
The usual response is to drop the affected records,
which is a data loss decision dressed up as a correctness decision.

Where the data can be regenerated, that is merely wasteful.
Where it cannot — a one-off experiment, a monitoring record,
an instrument stream that will never be replayed —
discarding is not an acceptable answer,
and repair stops being a convenience and becomes a reliability requirement.

The obstacle is that established repair methods need a format specification,
and frequently there is none to be had.
Long-lived archives are the sharp case:
formats drift across decades, tooling is retired,
and the specification is often the first thing lost.
_εRepair_ works without one,
using parser feedback alone to locate and correct inconsistencies.
It produces repairs 2.6 times higher in quality than _ddmax_,
measured by the edits needed to restore the data,
while losing 2.8 times less of it, at 1.4 times the runtime
[(ISSRE 2025)](/publications/2025/07/01/automatic/).
Our follow-up generalizes this to maximal format-free repair,
lifting the restrictions earlier methods imposed on repair operations,
repair locations, and the parser properties they required
[(ASE 2026)](/publications/2026/06/20/ase-maximal/).

Repair of this kind is the fault tolerance half of reliability.
It does not make the corruption less likely.
It makes the consequence of corruption recoverable,
which is the property that matters when the data is irreplaceable.

<!--
<h3>Implementation</h3>
The ideas from my research have resulted in two practical implementations -- [MuCheck](https://hackage.haskell.org/package/MuCheck) for Haskell, and [Xmutant](https://pypi.python.org/pypi/xmutant) for Python. I am also a contributor for [PIT](http://pitest.org/) mutation analysis system for Java, and [Rubocop](https://github.com/bbatsov/rubocop), a static analyzer for Ruby.
-->

<h3>Practice</h3>
My interest in the reliability of programs is informed by a wealth of practical knowledge from the Industry. Before joining the Ph.D. program, I worked in the software industry as a developer for ten years, where I was part of the web and proxy server development teams at [Quark Media House](http://www.quark.com/), and [Sun Microsystems](http://www.sun.com/). My primary area of interest was the web caches,  particularly the distributed caching systems and protocols. I participated in the [OpenSolaris](https://www.openindiana.org/) effort, where I was the maintainer of multiple open source packages. I have also contributed to the Apache HTTPD project, in core and mod_proxy modules. During my Ph.D., I worked at [Puppet Labs](https://puppet.com/) where I contributed extensively towards the functionalities in the Solaris Operating system, and at [Galois](https://galois.com/) where I contributed to the visualization of effectiveness of one of the vulnerability mitigation approaches.

That experience continues to shape the work.
The industrial protocol study above was run against a production system under
real operational constraints,
and the reduction and repair tools are built to be dropped into existing
pipelines rather than to require them to be rebuilt.

<hr>
<b>IMPORTANT: If you are my student, and facing _any_ sort of difficulties, please
do [contact me](/contact). I will be happy to talk to you, and help you in any way. </b>

