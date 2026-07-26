---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd adrianherrera 2024]
e:  State Space Search in Fuzzing
---

#### Ph.D. Thesis

State Space Search in Fuzzing

#### Abstract

Coverage-guided fuzzers are an indispensable tool in the software-testing toolbox. They
uncover bugs in a target program by subjecting it to a large number of automatically-
generated inputs. The fuzzer generates these inputs to search the corners of the
target’s (potentially vast) state space, where bugs are more likely to lurk. While
fuzzers have successfully uncovered bugs in a range of targets, they struggle to
discover “deep bugs” (i.e., bugs triggered under a complex set of control and data
dependencies). Moreover, security professionals deploying fuzzers lack observability
into fuzzers’ state space search (and thus an understanding of why these deep bugs
are missed).

This dissertation presents a set of techniques for reasoning about and improving a
fuzzer’s state space search, ultimately enhancing a fuzzer’s bug-finding ability.
First, we consider the task of bootstrapping this search process. Fuzzers typically
require an initial set of seeds (exemplar inputs accepted by the target) to kickstart their
state space search. We empirically evaluate various methods for selecting these seeds,
designing an optimal technique for reducing large seed sets in the process.
Second, we develop a new state space abstraction. Fuzzers traditionally abstract a
target’s state space based on control-flow features. We present an abstraction based on
data-flow features and demonstrate how our data-flow-based abstraction uncovers
bugs that traditional fuzzers fail to find.

Finally, we investigate how best to measure a fuzzer’s state space search after a
fuzzing campaign. We use static analysis to quantify a target’s state space, allowing
us to measure how much of this state space a fuzzer has explored. We empirically
evaluate several modern static analysis frameworks and propose new approaches for
assessing a fuzzer’s state space search.

[Link](https://adrian-herrera.com/assets/publications/phd.pdf)
