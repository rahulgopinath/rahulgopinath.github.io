---
layout: post
categories : student
tagline: "."
tags : [student mariussmytzek 2020]
e: Mutation-Based Impact Analysis
---

#### Masters Thesis

Mutation-Based Impact Analysis or Where Do My Results Come From?

#### Abstract

Evaluating today’s complex software applications is unaccomplishable without
effort. The verification of its functional correctness is achievable by testing
the software to the extent that the confidence in it is significant enough to
establish its overall rightness. The validation regarding stated claims or
derived conclusions remains even more troublesome.

In this thesis, I propose a technique to determine the impact of single program
components on the eventual result. I consider two program elements as the
principal implementation features: functions and constants. The approach
utilizes dynamic mutations activatable at runtime to disable particular
components. Combined with the derived outcome, the deviation to the concrete
result indicates the impact of the disabled element. The awareness of the
essential parts of a program provides a more superior understanding of the
origins of the outcomes. Hence, the approach could guide a developer to
enhance or expand the program to improve the quality of the results. Moreover,
the extracted information provides aids for validating scientific applications
based on the derived claims or conclusions by researchers, which would reinforce
the quality and correctness of their work.

I evaluated the approach on a diverse collection of interacting program
components from a set of real-world applications, and the results show that it
works in practice. Besides this evaluation, I applied the technique in a
realistic environment to the famous AFL fuzz tester. With the results,
I generated a modified version of it by deleting unimportant components.
This version shows an average increase in the triggered crashes for several subjects.
