---
layout: post
categories : student
tagline: "."
tags : [student sulavmalla 2025]
e: "Learning Highly Recursive Input Grammars: A Replication Study"
---

#### BE Honours Thesis

"Learning Highly Recursive Input Grammars": A Replication Study

**By Sulav Malla**

Supervised by: Rahul Gopinath, Yash Srivastava

#### Abstract


Knowing the source code of a program greatly aids program comprehension, testing techniques
such as fuzzing, optimisation, and debugging. However, due to various restrictions and other
external factors, accessing source code is often not possible. To address this limitation, recent
research has focused on inferring input grammars and execution behaviour directly from valid
program inputs. The ARVADA algorithm, developed by Lemieux C. and Kulkarni N. at UCB
in 2021, is a black-box approach designed to infer the grammar of a program using only valid
inputs and a black-box oracle.

Motivated by the lack of formal guarantees and concerns about the selectiveness of the
original study, this thesis attempts to re-implement the ARVADA algorithm in a clean-room
environment using the C programming language. Although a complete implementation was
not achieved, this paper presents a partial implementation of ARVADA algorithm in C with
improvements of the function MergeAllValid, and highlights the challenges faced and insights
gained during the re-implementation. These include the inherent complexity of ARVADA, the
difficulty of implementing such an algorithm in C, and the limited clarity and weakeness in the
explanation provided in the original paper.
