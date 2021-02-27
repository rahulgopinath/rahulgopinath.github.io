---
published: true
title: Error Correcting Earley Parser
layout: post
comments: true
tags: parsing, error correcting, context-free
categories: post
---

We talked about Earley parsers [previously](/post/2021/02/06/earley-parsing/).
One of the interesting things about Earley parsers is that it also forms the
basis of best known general context-free error correcting parser. A parser is
error correcting if it is able to parse corrupt inputs that only partially
conform to a given grammar. The particular algorithm we will be examining is
the minimum distance error correcting parser by Aho et al.[^aho1972minimum].

There are two parts to this algorithm. The first is the idea of a
_covering grammar_ that parses any corrupt input and the second is the
extraction of the best possible parse from the corresponding parse forest.


