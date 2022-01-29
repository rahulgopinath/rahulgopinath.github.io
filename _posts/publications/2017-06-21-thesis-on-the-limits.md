---
layout: post
categories : publications
tagline: "."
tags : publication
e: On the Limits of Mutation Analysis
title: On the Limits of Mutation Analysis
authors: Rahul Gopinath
venue: Ph.D. Thesis
kind: thesis
thesort: thesis
peerreviewed: no
---

Mutation analysis is the gold standard for evaluating test-suite adequacy. It 
involves exhaustive seeding of all small faults in a program and evaluating the 
effectiveness of test suites in detecting these faults. Mutation analysis 
subsumes numerous structural coverage criteria, approximates fault detection 
capability of test suites, and the faults produced by mutation have been shown 
to be similar to the real faults. This dissertation looks at the effectiveness 
of mutation analysis in terms of its ability to evaluate the quality of test 
suites, and how well the mutants generated emulate real faults. The 
effectiveness of mutation analysis hinges on its two fundamental hypotheses: 
The competent programmer hypothesis, and the coupling effect. The competent 
programmer hypothesis provides the model for the kinds of faults that mutation 
operators emulate, and the coupling effect provides guarantees on the ratio of 
faults prevented by a test suite that detects all simple faults to the complete 
set of possible faults. These foundational hypotheses determine the limits of 
mutation analysis in terms of the faults that can be prevented by a mutation 
adequate test suite. Hence, it is important to understand what factors affect 
these assumptions, what kinds of faults escape mutation analysis, and what 
impact interference between faults (coupling and masking) have. A secondary 
concern is the computational footprint of mutation analysis. Mutation analysis 
requires the evaluation of numerous mutants, each of which potentially requires 
complete test runs to evaluate. Numerous heuristic methods exist to reduce the 
number of mutants that need to be evaluated. However, we do not know the effect 
of these heuristics on the quality of mutants thus selected. Similarly, whether 
the possible improvement in representation using these heuristics are subject 
to any limits have also not been studied in detail. Our research investigates 
these fundamental questions in mutation analysis both empirically and 
theoretically. We show that while a majority of faults are indeed small, and 
hence within a finite neighborhood of the correct version, their size is larger 
than typical mutation operators. We show that strong interactions between 
simple faults can produce complex faults that are semantically unrelated to the 
component faults, and hence escape first order mutation analysis. We further 
validate the coupling effect for a large number of real-world faults, provide 
theoretical support for fault coupling, and evaluate its theoretical and 
empirical limits. Finally, we investigate the limits of heuristic mutation 
reduction strategies in comparison with random sampling in representativeness 
and find that they provide at most limited improvement. These investigations 
underscore the importance of research into new mutation operators and show that 
the potential benefit far outweighs the perceived drawbacks in terms of 
computational cost.

The thesis can be found at [https://ir.library.oregonstate.edu/concern/graduate_thesis_or_dissertations/9306t349j](https://ir.library.oregonstate.edu/concern/graduate_thesis_or_dissertations/9306t349j).
