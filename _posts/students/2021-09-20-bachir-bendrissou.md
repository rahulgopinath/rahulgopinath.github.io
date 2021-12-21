---
layout: post
categories : student
tagline: "."
tags : [student bachirbendrissou 2021]
e: Empirical Evaluation of GLADE
---

#### Masters Thesis

Empirical Evaluation of GLADE

#### Abstract

Having a program input specification is crucial in various fields such as vulnerability analysis, reverse engineering, and software testing. However, in many cases, a formal input specification may be unavailable, incomplete, or obsolete. When the program source is available, one may be able to mine the input specification from the source code itself. However, when the source code is unavailable, a black-box approach becomes necessary.

Unfortunately, black-box approaches to learning context-free grammars are bounded in theory and were shown to be as hard as reversing RSA. Hence, general context-free grammar recovery is thought to be computationally hard. Glade is a recent black-box grammar synthesizer, which claims it can recover an accurate context-free input grammar of any given subject using only a small set of seed inputs, and a general oracle able to distinguish between valid and invalid inputs. It also claims to be fast for all programs tested. While an implementation of GLADE is available, the input grammar produced is in an undocumented format that is hard to reverse engineer. Furthermore, GLADE also uses custom parsers and fuzzers which are hard to verify.

This thesis attempts to first replicate GLADE independently by first implementing the GLADE algorithm in Python, then use this implementation to verify the reported GLADE experiment results, and further evaluate GLADE using new context-free grammars. This will provide us with precise information and insights about the limits and suitability of GLADE in diverse circumstances.
