---
layout: post
categories : student
tagline: "."
tags : [student feiyangchen YEAR_HERE]
e: Evaluation of Delta Debugging on Valgrind
---

#### Postgraduate Capstone Project

Evaluation of Delta Debugging on Valgrind

**By Feiyang Chen**

Supervised by: Rahul Gopinath

#### Abstract

Software debugging is difficult when failures depend on large, complex inputs.
Delta debugging is an automated technique that isolates minimal failure‑inducing
inputs, but existing frameworks are often outdated or fragmented, and there is no
standardised benchmark. This project introduces a Python framework to implement
and evaluate delta‑debugging algorithms, together with a benchmark suite integrated
with Valgrind—a suite of program‑analysis tools for executables. By collecting
reproducible Valgrind bugs from public trackers and instrumenting the framework to
record reduction ratio, test‑execution count, and wall‑clock time, both effectiveness
and efficiency can be measured. The study focuses on identifying algorithms that
achieve the strongest reductions, determining those that minimise runtime and oracle
calls, and quantifying the advantage of structure‑aware techniques over traditional
methods. The benchmark runs in a virtual machine to ensure reproducibility. The
project code is managed with Git, packaged with uv, and accompanied by a test suite.
This report describes related literature and details the methodology, resources, aims,
scope, schedule, results, discussion, and limitations.
