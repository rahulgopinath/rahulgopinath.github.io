---
published: true
title: Using Mutants to Improve Test Suites.
layout: post
tags: [mutation]
categories: post
---

I had [previously written](/post/2015/10/01/should-we-use-mutation-score/) why
mutation analysis is not yet ready for prime time. Is there any way we can use
mutation analysis *now* to improve our test suites?

It seems there is indeed a way to do that so long as you are willing to follow
certain best practices.

### Use mutation analysis in the small

When writing unit tests, only create mutants in the specific unit you
are testing. That is, if you are testing a function *f()*, which in
turn calls *g()*, only create mutants in function *f()*, and verify
the following in those mutants.

### Ensure new mutants are killed for each new tests added

The first idea is that, while mutation score seems to be a measure with
specific range (0..100), the twin problems of *equivalent* and *redundant*
mutants ensure that we can not trust the mutation score. Rather, the only
thing we can trust is the absolute mutation detection numbers. The idea
is that when you add a new test, make sure that it kills at least some
*new* mutants.

### Ensure that your assertions actually kill new mutants compared to test cases without assertions

When adding a new test case, make sure that your assertions are
actually working, by verifying that they are able to kill more mutants
when compared to running a test case without assertion.

Because you are evaluating mutants in much smaller units, there is a better
chance you will be able to eliminate equivalent mutants as they occur.

## Use statement deletion operator exclusively to obtain mutation score

Use statement deletion mutation as the primary means to
*measure* quality of test suite. The interesting thing about statement
deletion is that if a statement (or an expression) can be deleted to
create a semantic clone, then we can argue that the clone
is *better* compared to the actual program because it is more
concise. (If the deleted statement (or expression) is an optimization,
and the semantic clone results in a worse program, it suggests that
the tests should have included a performance metric for distinguishing
the optimization).

Thus, if one is using deletion mutation exclusively, then 100% mutation
score does mean something, and is achievable for a perfect program. If
you are unable to obtain 100% with deletion mutation operators, it
suggests that either your program is not perfect, or your test suite is
not adequate.

The other important benefit of statement deletion mutation
is that there is a consistent and standard definition (unfortunately,
expression deletion operators are inconsistent in this regard). That is, you
can expect tools that implement statement or expression deletion
mutation to provide similar scores (although not across translation stages).
