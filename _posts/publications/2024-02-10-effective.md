---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Effective Fuzzing of Binary File Formats
title: Effective Fuzzing of Binary File Formats
authors: Rafael Dutra, Rahul Gopinath, and Andreas Zeller
venue: ACM TOSEM
kind: journal
thesort: peerreviewed
peerreviewed: yes
---

Effective fuzzing of programs that process structured binary inputs, such as multimedia files, is a challenging task, since those programs expect a very specific input format. Existing fuzzers, however, are mostly format-agnostic, which makes them versatile, but also ineffective when a specific format is required.

We present FormatFuzzer, a generator for format-specific fuzzers. FormatFuzzer takes as input a binary template (a format specification used by the 010 Editor) and compiles it into C++ code that acts as parser, mutator, and highly efficient generator of inputs conforming to the rules of the language.

The resulting format-specific fuzzer can be used as a standalone producer or mutator in black-box settings, where no guidance from the program is available. In addition, by providing mutable decision seeds, it can be easily integrated with arbitrary format-agnostic fuzzers such as AFL to make them format-aware. In our evaluation on complex formats such as MP4 or ZIP, FormatFuzzer showed to be a highly effective producer of valid inputs that also detected previously unknown memory errors in ffmpeg and timidity.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/tosem2024/dutra2024.pdf)
[<em class="fa fa-bookmark fa-lg" aria-hidden="true"></em>](
https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/tosem2024/dutra2024.bib)

