---
layout: post
categories : student
tagline: "."
tags : [student harshinijayakumar 2023]
e: Directed Fuzzing for Binary Formats
---

#### Honours Thesis

Directed Fuzzing for Binary Formats

**By Harshini Jayakumar**

Supervised by:   Rahul Gopinath, Xi Wu

#### Abstract

Fuzzing is a vital testing technique that uncovers software vulnerabilities by subjecting systems to random inputs. It's particularly effective for exposing both known and unknown security flaws, crucial in today's complex software landscape. Fuzzing's importance has grown due to its applicability even with limited program knowledge.

Efficient fuzzers explore diverse inputs, but traditional approaches fall short with structured input programs. One method to tackle this is generating valid inputs through mutations, but it's limited by coverage. An alternative approach leverages error feedback from parsers to replace incorrect bytes, making it efficient for black-box systems.

We introduce Tfuzzer, a novel strategy for structured input programs specifically to test VMs. Virtual machines (VMs) have become the backbone of modern computing environments, serving a pivotal role in the operation of cloud services, software systems, and numerous applications. This thesis introduces a pioneering approach, Tfuzzer, which leverages a TLV (Type-Length-Value) framework to enhance the fuzzing of specific structures within VM bytecode files.

Fuzzing for VMs has emerged as a central focus of this research, driven by the increasing prevalence of VM technologies and the unique security challenges they pose. VMs encapsulate complex structures within their bytecode files, making them susceptible to vulnerabilities that may remain hidden. Tfuzzer addresses this challenge by capitalizing on the structured nature of VM bytecode and employing error feedback mechanisms to enhance security assessments.

The adoption of a TLV framework within the context of VMs introduces a systematic approach to bytecode fuzzing. Tfuzzer analyzes VM bytecode structures, type, length, and value information, and generates test inputs that explore these structures comprehensively. By injecting randomized data while adhering to TLV constraints, Tfuzzer systematically evaluates the robustness of VMs against unexpected inputs, uncovering vulnerabilities both known and previously undisclosed.



