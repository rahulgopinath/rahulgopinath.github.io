---
layout: post
categories: publications
tagline: "."
tags : publication
e:  Evaluating Impact of Coverage Feedback on Estimators for Maximum Reachability in Fuzzing (Registered Report)
title: Evaluating Impact of Coverage Feedback on Estimators for Maximum Reachability in Fuzzing (Registered Report)
authors: Nelum Attanayake, Danushka Liyanage, Clement Canonne, Suranga Seneviratne, Rahul Gopinath
venue: NDSS
kind: workshop
thesort: peerreviewed
peerreviewed: yes
---

Background: Fuzzing campaigns require accurate estimation of maximum reachable coverage to ensure that resources are not wasted. However, adaptive bias due to the use of coverage feedback in modern fuzzers prevents accurate statistical estimation of maximum reachable coverage. Recent work hypothesizes that adaptive bias is minimized when singleton species, observed exactly once, equal doubletons, observed exactly twice. Rigorous evaluation of this hypothesis has been hindered by the lack of ground truth.

Objective: This work evaluates whether maximum reachable coverage estimates are reliable when adaptive bias is minimized, using two complementary approaches (1) to mitigate the lack of ground truth and (2) to establish ground truth. Methods: First, we compare maximum reachable coverage estimates between coverage-guided and purely random fuzzers on real-world benchmarks. Since random fuzzers lack coverage feedback, they exhibit no adaptive bias. If the singleton-doubleton equilibrium criterion reliably indicates minimal adaptive bias, the coverage-guided fuzzer should reach maximum reachable coverage estimates comparable to the random fuzzer at this equilibrium point. Second, we validate estimates using synthetic programs with known maximum reachable coverage, where complex control flows mimic real-world complexity while providing objective ground truth.

Results: These complementary studies will determine whether maximum reachable coverage estimates are reliable when the singleton-doubleton equilibrium criterion is satisfied, validating or refuting its use as a stopping criterion for fuzzing campaigns.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/fuzzing2024/attanayake2026evaluating.pdf "paper")
<!-- [<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/an-empirical-evaluation-of-frequency-based-statistical-models-for-estimating-killable-mutants "presentation") -->

