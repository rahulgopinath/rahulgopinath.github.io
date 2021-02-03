---
layout: post
categories : student
tagline: "."
tags : [student leonbettscheider 2020]
e: grammar refinement
---

#### Masters Thesis

Concolic Grammar Refinement for Stateful Fuzzing

#### Abstract

Fuzz testing, or fuzzing, is a widely deployed automated software testing technique which has been used to discover many security-critical software bugs. Fuzzing probes the program under test for faulty behavior by repeatedly running it on automatically generated inputs. This method is efficient because test cases can be produced very quickly using generative or mutational approaches. However, one of the problems with fuzzing is that, to be effective, fuzzers need to generate plausible inputs that reach non-trivial parts of the program. Programs that process highly-structured inputs, such as interpreters, typically process their input in two stages. They start by parsing the input and, given that it is syntactically correct, continue to evaluate it. Grammar-based fuzzing is the prime technique to test such programs, as a large fraction of the generated inputs is syntactically correct, allowing them to reach and test the evaluation stage.

In stateful programs, such as database engines or web servers, it is even more difficult for fuzzers to reach the evaluation stage. The generated inputs need to be semantically correct with respect to the current transient program state, in addition to being syntactically correct. Even grammar-based fuzzers are unable to reliably produce semantically correct inputs. For example, the validation of inputs may depend on the state of the program in question (such as session IDs), which are hard to produce using random chance. Thus, grammar fuzzers struggle to generate inputs that satisfy state checks and exercise code paths located beyond these checks, which greatly reduces their ability to discover software bugs.

To overcome this limitation, we propose a novel grammar refinement strategy for stateful programs. We start with a context-free grammar, and leverage concolic execution of generated inputs to mine state-based constraints that need to be satisfied. These constraints are then lifted to the grammar, which results in a grammar that automatically fine tunes itself towards inputs that can reach deeper and deeper code paths in the current execution.

We implement our grammar refinement technique on top of a concolic execution engine for the C programming language. We demonstrate a proof
of concept on SQLite that shows the ability of our approach to mine existing table and column names from the database. In addition, we combine our approach with a state-of-the-art grammar fuzzer and compare it with grammar fuzzing alone in an experiment on SQLite. Our evaluation suggests that grammar refinement enhances fuzzing if the targeted state information contains a sufficiently high level of entropy.
