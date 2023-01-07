---
layout: post
categories : publications
tagline: "."
tags : publication
e:  The Theory of Composite Faults
title: The Theory of Composite Faults
authors: Rahul Gopinath, Carlos Jensen, Alex Groce
venue:  IEEE International Conference on Software Testing, Verification and Validation (ICST)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Fault masking happens when the effect of one fault serves to mask that of another fault for particular test inputs. The coupling effect is relied upon by testing practitioners to ensure that fault masking is rare. It states that complex faults are coupled to simple faults in such a way that a test data set that detects all simple faults in a program will detect a high percentage of the complex faults..

While this effect has been empirically evaluated, our theoretical understanding of the coupling effect is as yet incomplete. Wah proposed a theory of the coupling effect on finite bijective (or near bijective) functions with the same domain and co-domain, and assuming uniform distribution for candidate functions. This model however, was criticized as being too simple to model real systems, as it did not account for differing domain and co-domain in real programs, or for syntactic neighborhood.
We propose a new theory of fault coupling for general functions (with certain constraints). We show that there are two kinds of fault interactions, of which only the weak interaction can be modeled by the theory of the coupling effect. The strong interaction can produce faults that are semantically different from the original faults. These faults should hence be considered as independent atomic faults. Our analysis show that the theory holds even when the effect of syntactical neighborhood of the program is considered. We analyze numerous real-world programs with real faults to validate our hypothesis.

##### Updates:

* Updates to Impact of Syntax.


Let us call the original input $$h$$, $$g(i_0) = j_0$$, and the changed value $$g_a(i_0) = j_a$$.
Similarly, let $$f(i_0) = k_0$$, $$f_a(i_0) = k_a$$, $$f_b(i_0)=k_b$$, and $$f_{ab}(i_0) = k_{ab}$$. Given two
inputs $$i_0$$, and $$i_1$$ for a function $$f$$, we call $$i_0$$, and $$i_1$$ semantically close if
their execution paths in f follow equivalent profiles, e.g taking the same
branches and conditionals. We call $$i_0$$ and $$i_1$$ semantically far in terms of f if
their execution profiles are different.

Consider the possibility of masking the output of $$g_a$$ by $$h_b$$ ($$h_{b'}$$ in Figure 3)).
We already know that $$h(j_a) = k_a$$ was detected. That is, we know that $$j_a$$ was
sufficiently different from $$j_0$$, that it propagated through $$h$$ to be caught
by a test case. Say $$j_a$$ was semantically far from $$j_0$$, and the difference (i.e,
the skipped part) contained the fault $$\hat{b}$$. In that case, the fault $$\hat{b}$$
would not have been executed, and since $$k_{ab} = k_a$$, it will always be detected.

On the other hand, say $$j_a$$ was semantically close to $$j_0$$ in terms of $$g$$ and the
fault $$\hat{b}$$ was executed. There are again three possibilities. The first is
that $$\hat{b}$$ had no impact, in which case the analysis is the same as before.
The second is that $$\hat{b}$$ caused a change in the output. It is possible that
the execution of $$\hat{b}$$ could be problematic enough to always cause an error,
in which case we have $$k_{ab} = k_b$$ (error), and detection. Thus masking requires
$$k_{ab}$$ to be equal to $$k_0$$.

Even if we assume that the function $$h_b$$ is close syntactically to $$h$$, and that
this implies semantic closeness of functions $$h$$ and $$h_b$$, we expect the value $$k_{ab}$$
to be near $$k_a$$, and not $$k_0$$.

* Coupling Effect

For coupling effect, we use the definition from [Richard A. DeMillo](https://dl.acm.org/doi/pdf/10.1145/74587.74634). 
"The coupling effect asserts that test data that is sensitive enough to kill
simple mutants also causes the vast majority of k-ary mutants to die." where
1-ary mutant is a mutant with a single fault.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/icst2017/gopinath2017the.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/icst2017/gopinath2017the.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/the-theory-of-composite-faults "presentation")
