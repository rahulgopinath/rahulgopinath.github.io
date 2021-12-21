---
layout: post
categories : student
tagline: "."
tags : [student banjiolorundare 2021]
e: Inferring Input Grammars from Binary Programs using String Inclusion
---

#### Masters Thesis

Inferring Input Grammars from Binary Programs using String Inclusion

#### Abstract

Knowing the input language of a program is important for fuzzing. While there are tools that learn an input language from a program with or without samples, whitebox techniques are the best of the breed. However the current whitebox techniques rely on dynamic taints, and obtaining dynamic taints involves instrumentation. Unfortunately, such instrumentation may be infeasible in many cases. Hence, tracking information flow using dynamic taint information can be challenging. This can be especially hard in stripped binaries where no debug information is present.

In this work, we present a technique that can extract the input grammar from a given program. Using standard debuggers such as GDB, our technique takes a binary program and a small set of sample inputs and identifies the structural decomposition of the input using the generalized string inclusion technique. The result of this iterative process is context-free grammar that forms the complete input specification of the program. In our evaluation, our prototype automatically produces readable and structurally accurate grammar from various evaluation subjects. The resulting grammars produced can be used as input in test generators for comprehensive automated testing.
