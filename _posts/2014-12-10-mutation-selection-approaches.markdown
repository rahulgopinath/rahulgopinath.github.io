---
published: true
title: Mutation Selection Approaches
layout: post
categories: [post]
tags: [mutation]
---
According to [Offutt et al.](http://dl.acm.org/citation.cfm?id=571305.571314), mutation selection approaches can be categorized into three orthogonal techniques: Do fewer, Do faster, and Do smarter.

![Selective Mutation](/resources/posts/do-x.png)

### Do Smarter

Improve the mutation analysis runtime by splitting tasks across multiple processes or machines, and running in parallel. The main innovations under this category involves scheduling how mutations are to be run.

### Do Faster

Improve the mutation analysis runtime of a single mutant, or that of the whole set without using parallelization. It includes compiler integration of mutation analysis, byte-code modification rather than source modification, techniques using mutant schemata etc.

### Do fewer

Reduce the number of mutations that are examined. It involves operator selection, clustering, sampling, pre-execution reduction using static analysis etc.

Ideally, one should be able to apply methods under each category independently since they are orthogonal. That is, parallelization of mutants should not affect the improvements possible using either a better algorithm for analysis of a single mutant, or advances in sampling mutants.
