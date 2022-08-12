---
layout: post
categories : publications
tagline: "."
tags : publication
e: "CLIFuzzer: Mining Grammars for Command-Line Invocations"
title: "CLIFuzzer: Mining Grammars for Command-Line Invocations"
authors:  Abhilash Gupta, Rahul Gopinath, Andreas Zeller
venue: ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

The behavior of command-line utilities can be very much influenced by passing command-line options and arguments - configuration settings that enable, disable, or otherwise influence parts of the code to be executed. Hence, systematic testing of command-line utilities requires testing them with diverse configurations of supported command-line options.

We introduce CLIfuzzer, a tool that takes an executable program and, using dynamic analysis to track input processing, automatically extract a full set of its options, arguments, and argument types. This set forms a grammar that represents the valid sequences of valid options and arguments. Producing invocations from this grammar, we can fuzz the program with an endless list of random configurations, covering the related code. This leads to increased coverage and new bugs.

<!--
[<em class="fa fa-book fa-lg" aria-hidden="true"></em>]()
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>]()
[<em class="fa fa-desktop" aria-hidden="true"></em>]()

-->
