---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Input Algebras
title: Input Algebras
authors: Rahul Gopinath, Hamed Nemati, Andreas Zeller
venue: ACM/IEEE International Conference on Software Engineering (ICSE) 
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Grammar-based test generators are highly efficient in producing syntactically
valid test inputs, and give their user precise control over which test inputs
should be generated. Adapting a grammar or a test generator towards a particular
testing goal can be tedious, though. We introduce the concept of a grammar
transformer, specializing a grammar towards inclusion or exclusion of specific
patterns: "The phone number must not start with 011 or +1". To the best of our
knowledge, ours is the first approach to allow for arbitrary Boolean
combinations of patterns, giving testers unprecedented flexibility in creating
targeted software tests. The resulting specialized grammars can be used with any
grammar-based fuzzer for targeted test generation, but also as validators to
check whether the given specialization is met or not, opening up additional
usage scenarios. In our evaluation on real-world bugs, we show that specialized
grammars are accurate both in producing and validating targeted inputs.

##### Updates:

In the paper, for negation of a rule such as below

```
<A X> ::= <B E> <C F> <D>
```
we provide the following result

```
<A neg(X)> ::= <B neg(E)> <C F> <D>
             | <B E> <C neg(F)> <D>
```

However, this expansion is wrong. The reason is that our guarantee is simply
that `X` exists in one of `<B E>` or `<C F>` or `<D>`. The above result assumes
that all the specializations in tokens are necessary to reproduce the fault.
However, this is incorrect. In particular, the fault may be present either in
`<B E>` or `<C F>` or even in `<D>`.

Hence, for negating a rule that corresponds to a specialized *nonterminal* after
the operations in the paper, one also has to perform a conjunction of all the
*nonterminal* in the resulting rule with the negation of specialization of the
nonterminal. That is, if one is trying to negate a rule

```
<A X> ::= <B E> <C F> <D>
```

The operations mentioned in the paper will result in

```
<A neg(X)> ::= <B neg(E)> <C F> <D>
             | <B E> <C neg(F)> <D>
```

From this update, the following would result after conjunction with the
corresponding specialization of `<A X>` which is `X`

```
<A neg(X)> ::= <B neg(E) & neg(X)> <C F & neg(X)> <D T & neg(X)>
             | <B E & neg(X) > <C neg(F) & neg(X)> <D T & neg(X)>
```

Which simplifies to

```
<A neg(X)> ::= <B neg(E) & neg(X)> <C F & neg(X)> <D neg(X)>
             | <B E & neg(X) > <C neg(F) & neg(X)> <D neg(X)>
```

This treatment is different for negating keys of the pattern grammar because
their matching is dependent on the exact position. For these, the conjunction
is with the corresponding fault of the pattern grammar (i.e., paper version is
sufficient).

**Artifacts** _available_ ![ACM artifact available](/resources/acm_artifact_available_20px.png) (implies _functional_ ![ACM artifact functional](/resources/acm_artifact_functional_20px.png) and _reusable_ ![ACM artifact reusable](/resources/acm_artifact_reusable_20px.png) at ICSE)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4456296.svg)](https://doi.org/10.5281/zenodo.4456296)

