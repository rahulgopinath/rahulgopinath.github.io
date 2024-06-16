---
layout: post
categories : student
tagline: "."
tags : [student evefernando 2022]
e: Example Free Learning of Regular Languages with Prefix Queries
---

#### Honours Thesis

Example-Free Learning of Regular Languages with Prefix Queries

Supervised by: Sasha Rubin, Rahul Gopinath

#### Abstract

Language learning refers to the problem of inferring a mathematical model which accurately represents a formal language. Many language learning algorithms learn by asking certain types of queries about the language being modelled. Language learning is of practical interest in the field of cybersecurity, where it is used to model the language accepted by a program’s input parser (also known as its input processor). In this setting, a learner can only query a string of its choice by executing the parser on it, which limits the language learning algorithms that can be used. Most practical parsers can indicate not only whether the string is valid or not, but also where the parsing failed. This extra information can be leveraged into producing a type of query we call the prefix query. Notably, no existing language learning algorithms make use of prefix queries, though some ask membership queries i.e., they ask whether or not a given string is valid. When these approaches are used to learn the language of a parser, the prefix information provided by the parser remains unused.

In this work, we present PL*, the first known language learning algorithm to make use of the prefix query, and a novel modification of the classical L* algorithm proposed by Angluin (1987). We show both theoretically and empirically that PL* is able to learn more efficiently than L* due to its ability to exploit the additional information given by prefix queries over membership queries. Furthermore, we show how PL* can be used to learn the language of a parser, by adapting it to a more practical setting in which prefix queries are the only source of information available to it; that is, it does not have access to any labelled examples or any other types of queries. We demonstrate empirically that, even in this more constrained setting, PL* is still capable of accurately learning a range of languages of practical interest.
