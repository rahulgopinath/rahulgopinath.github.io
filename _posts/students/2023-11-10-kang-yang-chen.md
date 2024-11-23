---
layout: post
categories : student
tagline: "."
tags : [student kangyangchen 2023]
e: Binary Format Fuzzer
---

#### Honours Thesis

Binary Format Fuzzer

**By Kang Yang Chen**

Supervised by:   Rahul Gopinath

#### Abstract

Fuzzing binary format programs effectively can be hard, as there are no popular, format-aware binary fuzzers currently available. Popular, format-aware context-free grammar fuzzers, such as Gramminator, do exist. However, they are ill-suited for fuzzing binary formats, as binary formats often contain data-dependent fields that cannot be represented by context-free grammar, such as a length field or a checksum field. Format-agnostic fuzzers, such as AFL, can also face trouble fuzzing these formats, as any mutation to a field that is checksummed will immediately invalidate the data, causing the parser to terminate and preventing us from reaching deep code paths easily. While one can manually implement a fuzzer for each binary format to overcome these issues, it is very time-consuming and tedious.  We attempted to solve these issues by building a compiler (fuzzer generator) for Kaitai Struct, a domain-specific language that utilises YAML to define binary formats. This allows one to generate a format-specific binary fuzzer easily with the extensive binary formats provided by the Kaitai Project, without having to manually implement a format-specific fuzzer from scratch.

