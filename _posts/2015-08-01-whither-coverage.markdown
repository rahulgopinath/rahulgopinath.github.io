---
published: true
title: Whither Coverage?
layout: post
tags: [coverage]
categories: post
---

As a researcher working in mutation analysis, I have been somewhat
concerned by the recent discussions in
[Hackernews](https://news.ycombinator.com/item?id=10644987) and
[Reddit](https://www.reddit.com/r/programming/comments/3uvcf2/coverage_is_not_strongly_correlated_with_test/).
These discussions are based on a publication from
Laura Inozemtseva et al. ([Inozemtseva 2014](/references#inozemtseva2014coverage))
which suggests that coverage provides little additional benefit over simply counting
the test size. Inozemtseva et al. further suggests that we all should
use mutation score instead.

The main result in the paper is that they found raw coverage to have a strong
relation with the mutation score. However, they found that if one looks only at
test suites of the same size; say 10 test cases each, 100 test cases
each etc. then there is little correlation between the effectiveness of
test suite (as measured by its mutation score), and the coverage.

### Coverage

The author tries very hard ([GTAC 2015](https://www.youtube.com/watch?v=sAfROROGujU)) to point out
that correlation does not imply causation, and to point out that once
the test suite size is controlled, that correlation vanishes. However,
this assumes that test suite size (in absolute numbers -- say 10 test cases, or
100 test cases) is some thing that people care about. Usually, when we
decides to test, we have a budget. But that budget is defined in terms
of test development time (and for larger applications, the test run time may
also count) but rarely if ever, one hears about limiting the tests to
run in terms of absolute numbers (i.e. run only 100 tests).

One usually decides to stop testing when one reaches some sort of
adequacy. Say 100% statement coverage. Unfortunately, test suite size
has no equivalent notion. So test suite size can not supplant coverage
as an adequacy measure. Notice that the paper talks about number of
test cases in specific programs, and not in terms of general programs,
(for example, N test cases equates X% coverage). Given this, I do not
see why one should consider the correlation between suite size and
coverage to be harmful, or why one should control for test suite size.

Author's point is that the correlation between coverage and effectiveness
is not a real causative correlation. That both are caused by the increase
in the number of tests. However, consider a test suite. Say we improve
the test cases without increasing the number; say by fixing some bugs.
Say the improved test cases resulted in a larger coverage.
We could expect the improved test cases to have better coverage because
it covers more lines, and so long as our oracles are sufficient, the
bugs (or mutants) in the newly covered lines can be detected without
a corresponding increase in the number of test cases in the test suite.
Similarly, a doubling of test cases by just duplicating them increases
the test suite size without an increase in either coverage or
effectiveness. Hence, I believe that authors insistence that the
correlation is not due to a causative relationship is incorrect.

### Mutation Score

The next problem is that mutation analysis is pushed forward as the *silver
bullet*. However, mutation analysis is again beset with a number of problems.
The biggest practical difficulty is due to the number of mutants.
Even when we restrict the mutants to just first order, the number of
mutants is still extremely large, and each mutant requires a complete
test suite run. Note that we assume that first order mutation is
sufficient by assuming coupling hypothesis works. However, a result
from Wah et al. ([Wah 2001](/references#wah2001theoretical)) suggests
that as the programs become larger, the coupling effect decreases. If
that is the case, one would need to look harder at using the higher
order mutants also, which would increase the number of mutants again.

The other issue is with semantic mutant clones. *Equivalent mutants*
are versions of the original with syntactic mutation, but no semantic
impact. For example, deletion of a print statement or an initialization
statement may not have an impact in the program behavior observable by
the test cases. So, given a set of mutants of which 50% is equivalent
(50% is not an extreme estimate. A previous study ([Papadakis 2015](/references#papadakis2015trivial))
found that up to 17% mutants were trivially equivalent -- that is, these
mutants result in no difference in object code once optimizations are applied),
not even the best test suite will have greater than 50% mutation score.

This means that *a low mutation score is not indicative of low quality
test suite*.

*Redundant mutants* on the other hand are mutants that are semantically
equivalent to each other. So if you catch one, you catch all in that
set. As you can imagine, redundant mutants can increase the mutation
score artificially without a corresponding increase in the actual
effectiveness.

This means that *a high mutation score is not indicative of high quality
test suite*.

Finally, can we assume that two test suites with 50% coverage is similar
in effectiveness? That again is problematic because it assumes that mutants
are similar in ease of detection. However, there is sufficient evidence
that some mutants are hard to kill ([Papadakis 2015](/references#papadakis2015trivial))
while others are extremely easy. So given a test suite that is
optimized for killing stubborn mutants, and another which
kills a few sets of redundant and trivial mutants, the measure will
favor the test suite that kills trivial and redundant mutants, while
the effectiveness of the test suite targeting stubborn mutants may be
larger.  Hence, mutation score does not even facilitate
an unbiased comparison between test suites.

![Hierarchical](/resources/posts/spherical-cow.png)

My point is not that mutation analysis is totally useless. Rather, I
wish to argue that mutation analysis is not yet ready for prime time,
and those who ignore the complexities of mutation analysis do so at their
own peril. Beware of spherical cows.

