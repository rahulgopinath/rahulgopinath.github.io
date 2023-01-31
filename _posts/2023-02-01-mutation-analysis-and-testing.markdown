---
published: true
title: Mutation Analysis and Mutation Testing
layout: post
comments: true
tags: mutation-analysis, mutation-testing
categories: post
---

Program mutation has historically had to different use cases. The first is as
the premier test-adequacy measure. The idea is that the ratio of number of
mutants killed vs those that can be killed (typically the generated mutants,
ignoring equivalent mutants) is an indication of the test suite quality, and
the remaining killable (but surviving) mutants are a measure of *residual risk*.
This lets mutation analysis score be used as an acceptance criteria by
end-users and managers.

The second is when the mutants themselves are used as a stand-in for possible
faults that can occur in the source. This is typically used by researchers
looking for a relatively bias free way to evaluate their tools possible faults.

A third use case is when the surviving mutants are used as a test objective
by developers.

The difference between the first and the rest is that for the first, the
*reality* or the *naturalness* of mutants is a non-issue, while for the second
and the third, the naturalness of the fault induced is a priority.

A subtle difference between the second and third in the relative
priority between variety and exhaustiveness. Researchers price variety while
developers require exhaustiveness.

This has been a sort of folklore in the community for sometime, but has been
clarified in a new paper by Kaufman et al. [^kaufman2022prioritizing]. They
call the first *Mutation Analysis*, and the second and third *Mutation
Testing*. 

[^kaufman2022prioritizing]: Kaufman, Samuel J and Featherman, Ryan and Alvin, Justin and Kurtz, Bob and Ammann, Paul and Just, Rene "Prioritizing Mutants to Guide Mutation Testing" ICSE 2022 <https://dl.acm.org/doi/pdf/10.1145/3510003.3510187>
