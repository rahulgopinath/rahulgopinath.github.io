---
published: true
title: Various Definitions of Minimal Mutant Sets. 
layout: post
comments: true
tags: [mutation]
categories: post
---

The large redundancy of mutants in mutation analysis is a topic that has
received much attention from the researchers. To evaluate how redundant a
mutant set is, one requires some notion of a minimal set of mutants. 

A recent conversation convinced me that a number of misunderstandings exist on
the various minimal mutant set definitions. Here is an attempt to clarify some
of the common definitions.

There are five common mutant selection techniques that produce sets *minimal* in some respect:

* [Absolute minimal sets of mutants](#absoluteminimal)
* [Theoretical minimal sets of mutants](#theoreticalminimal) (commonly called *minimal mutants*)
* [Disjoint mutants](#disjointmutants)
* [Surface Mutants](#surfacemutants)
* [Distinguished or Unique Mutants](#distinguishedmutants)

To understand each, we have to start with a few definitions.

### Minimal Test Suite

In general, a test suite is considered minimal with respect to a particular
objective ([Harrold 1993](/references#harrold1993a)), if the test cases in the test suite are sufficient and necessary
for fulfilling that objective. That is, a test suite is minimal against
a set of mutants ([Ammann 2014](/references#ammann2014establishing)) if removal of any test from
the test suite results in a drop in the mutation score of the test suite
achieved against the set of mutants.

#### Algorithm
The computation of a minimal test suite is given by:

```
function MinTest(Mutants, Tests)
  T = Tests
  M = kill(T, Mutants)
  T_min = {}
  while M != {} do
    t = random(max_t|kill({t}, M)|))
    M = M \ kill({t}, M)
    T_min = T_min U {t}
  end
  return T_min
end
```

Note that according to the order in which tests are removed, one can end up with different minimal test suites.

See ([Gopinath 2016](http://rahul.gopinath.org/publications/#gopinath2016measuring)) for further details.

### <a id='distinguishedmutants'>Distinguished or Unique Mutants </a>

Any mutant is identified by the tests that kill it. Hence, a mutant is
distinguished from another if the specific tests that kill that mutant is
different from the other. For example, given three mutants m1 killed by {t1, t2}
m2 killed by {t2 t3}, and m3 killed by {t2, t3}, the mutants m2 and m3 are
indistinguishable from each other, while m1 is distinguishable from both m2
and m3. To compute a set of unique mutants, simply sort them by test kill pattern
and remove duplicates.

### Mutant Subsumption

A mutant subsumes another, if all possible test cases that kills the former are
guaranteed to kill the later. For example, given m1 killed by {t1, t2} and
m2 killed by {t2, t3}, and m3 killed by {t2}, the mutants m1 and m2 are
subsumed by m3. A mutant dynamically subsumes another with respect to a test suite T
if both the mutants are killed by T, and the test cases in T that kills the former
are guaranteed to kill the later.

### <a id='surfacemutants'>Surface Mutants </a>

If one removes all subsumed mutants with respect to the entire test suite T,
then one ends up with the [surface mutants](http://rahul.gopinath.org/publications/#gopinath2016measuring).

The algorithm for removing subsumed mutants is given by:

```
function RmSubsumed(Tests, Mutants)
  M = kill(T, Mutants)
  T <- Tests
  M_min = M
  while M != {} do
    m = random(M)
    M = M \ {m}
    N = M_min \ {m}
    while N != {} do
      n = random(N)
      N = N \ {n}
      if cover({m}, T) `subset of` cover({n}, T) then
        M_min = M_min \ n
        M = M \ n
      end
    end
  end
  return M_min
end
```

The details can be found in ([Gopinath 2016](http://rahul.gopinath.org/publications/#gopinath2016measuring)).

### <a id='absoluteminimal'>Absolute Minimal Mutants</a> 

If one applies removal of subsumed mutants with respect to a minimal test suite, T_min
then one ends up with the absolute minimal mutant set.

### <a id='theoreticalminimal'>Theoretical Minimal Mutants (aka Minimal Mutants) </a> 

According to the order in which different tests are removed, one can end up with different minimal test suites. The
idea of theoretical minimal mutants is that we can remove a mutant as redundant if removing that mutant does not
result in a change in the *set* of minimal test suites.

As I mentioned in my update ([Gopinath 2016](http://rahul.gopinath.org/publications/#gopinath2016measuring)), the surface
mutants are actually theoretical minimal mutants.

### <a id='disjointmutants'> Disjoint Mutants </a>

Disjoint mutants were proposed in ([Kintis 2010](/references#kintis2010evaluating)).
According to Kintis et al. *Two mutants are considered disjoint if the test sets
that kill them are as disjoint as possible*. The procedure give is, choose the
mutants that are hardest to kill, and also ensure minimal overlap in terms of
tests with any other mutant thus selected.

What exactly is the relation of disjoint mutants to other minimal sets? The
authors of the disjoint mutants [suggests](https://arxiv.org/pdf/1601.02351.pdf)
that it is equivalent to theoretical minimal mutant sets, and
[the algorithm given by them](https://arxiv.org/pdf/1601.02351.pdf) seems to
remove the subsumed mutants using a full test suite. Hence, all the three: *surface*, *disjoint* and *theoretical minimal* mutant sets are equivalent.

