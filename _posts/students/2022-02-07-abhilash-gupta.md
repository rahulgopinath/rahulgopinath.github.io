---
layout: post
categories : student
tagline: "."
tags : [student abhilashgupta 2022]
e: Grammar Fuzzing Command line utilities in Linux
---

#### Masters Thesis

Grammar Fuzzing Command line utilities in Linux

#### Abstract

The execution of command-line (CLI) utilities is determined by both the configuration options and arguments passed in its invocation.
Configuration options activate specific code segments in the utility while arguments are the utility's input.
It is imperative to utilise both arguments and configuration options to fuzz these utilities.
However, almost every fuzzing study on CLI utilities excluded configuration options from the fuzzing process.
We suspect that more failures exist in the code segments activated by the options, which compromises the utilities' reliability.

We describe a method to integrate configuration options and arguments to grammar fuzz CLI utilities.
We present a general technique that takes an utility and automatically constructs a readable context-free grammars (CFG) capturing the syntax of its invocation.
The generated grammars are then saved and used to fuzz the command-line utilities in search of failures in them.

This thesis employs this approach to fuzz test 44 CLI utilities in Linux. This approach discovered more failures in CLI utilities than the best reported literature. Furthermore, this approach is observed to generally achieve better code coverage than a state-of-the-art feedback driven fuzzer.
