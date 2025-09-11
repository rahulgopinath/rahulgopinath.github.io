---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Assessing Reliability of Statistical Maximum Coverage Estimators in Fuzzing 
title: Assessing Reliability of Statistical Maximum Coverage Estimators in Fuzzing 
authors: Danushka Liyanage, Nelum Attanayake, Zijian Luo, Rahul Gopinath
venue: ICSME
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

**Registered Report**

Background: Fuzzers are often guided by coverage, making the estimation of maximum achievable coverage a key concern in fuzzing. However, achieving 100% coverage is infeasible for most real-world software systems, regardless of effort. While static reachability analysis can provide an upper bound, it is often highly inaccurate. Recently, statistical estimation methods based on species richness estimators from biostatistics have been proposed as a potential solution. Yet, the lack of reliable benchmarks with labeled ground truth has limited rigorous evaluation of their accuracy. 

Objective: This work examines the reliability of reachability estimators from two axes: addressing the lack of labeled ground truth and evaluating their reliability on real-world programs.

Methods: (1) To address the challenge of labeled ground truth, we propose an evaluation framework that synthetically generates large programs with complex control flows, ensuring well-defined reachability and providing ground truth for evaluation. (2) To address the criticism from use of synthetic benchmarks, we adapt a reliability check for reachability estimators on real-world benchmarks without labeled ground truth -- by varying the size of sampling units, which, in theory, should not affect the estimate.

Results: These two studies together will help answer the question of whether current reachability estimators are reliable, and defines a protocol to evaluate future improvements in reachability estimation.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://arxiv.org/abs/2507.17093 "paper")

