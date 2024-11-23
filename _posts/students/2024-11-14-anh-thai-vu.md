---
layout: post
categories : student
tagline: "."
tags : [student anhthaivu alistairvu 2023]
e: Directed Fuzzing for Binary Formats
---

#### Honours Thesis

Making Mutation Analysis Less Redundant

**By Anh Thai Vu (Alistair)**

Supervised by:   Rahul Gopinath, Francois Gauthier

#### Abstract

Introduction. Mutation analysis is the premier technique to evaluate the quality of test suites in finding bugs. However, traditional mutation analysis is computationally costly, which limits its use.  The reason is that it requires the execution of the same code segments multiple times, often with the same data. Removing this redundancy can result in significant speedup.

Aims. This project aims to remove the redundancy in mutation evaluation, making it more useful to the software practitioner.

Methods. We developed a prototype that uses specialised shadow memory variables to minimise the amount of redundant execution throughout the mutation analysis process. We implemented the main logic as a C++ library. We then compared the runtime of our prototype against an implementation of traditional mutation analysis, using a suite of ten maze solution verifier programs of varying sizes and mutant counts.

Results. After running the ten maze verifier programs four time each, we found that our prototype was between 1.5 times and up to 52.7 times faster than traditional mutation analysis. This meant that our prototype was able to reduce the amount of redundancy in terms of amount of execution compared to traditional mutation analysis.

Conclusions. The C++ prototype of our mutation analysis method was up to 52.7 times faster than a comparable implementation of traditional mutation analysis.  Moreover, our prototype provides the basis for future iterations, including additional mutant operations and further optimisations.
