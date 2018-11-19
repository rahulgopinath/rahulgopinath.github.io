---
published: true
title: Rehabilitating Mutant Immortals
layout: post
comments: true
tags: mutation
---

# Rehabilitating Mutant Immortals.

One often hears the claim that mutation analysis is unreliable because of the presence of immortal (equivalent) mutants. The problem is that the true mutation score is the ratio between the number of mutants killed and the actual number of mortal mutants. Since there is no general algorithm to determine all immortal mutants from a set of mutants, it is impossible to determine the actual number of mortal mutants from an arbitrary set of mutants. Hence, the mutation score is unreliable as a measure of test suite quality, which is the primary purpose of mutation testing.

Further, live mutants are often used by practitioners to determine how to enhance their test cases so that it covers more specification by killing them. Immortal mutants, by definition can not help here because they can not be killed. Hence, human effort spent on analyzing these mutants is often considered a waste.

## Useful immortal patterns

Our thesis is that one needs to consider the issue from a more holistic perspective. Mutation analysis should not be considered as a way to improve tests alone, rather, it should be regarded as an opportunity to improve both the test cases, and the code that it tests. We present several patterns where code that produced equivalent mutants were improved by refactoring or rewriting that eliminated equivalent mutants, which resulted in better code. Our experience suggests that these patterns are common enough that human analysis of live mutants -- whether they are immortal or not -- can be worth the investment for a practitioner. We study several patterns below

### Deletion of unreachable code

Unreachable code represents one of the simplest instances of equivalent mutants that are relatively easy to identify. These can often be identified statically and eliminated. We are talking about code that can't be identified statically. The problem with unreachable code is that such code often represents a cognitive load for a new programmer. The programmer has to understand how the code behaves, because any set of statements represent a vulnerability surface if an attacker is able to make them execute. Hence, removing unreachable code can often simplify the codebase, and make it easier to understand and maintain.

### Deletion of code that does nothing

Another pattern that one often find is code that performs some computation, where the results are discarded at the end. While it may be that the computation may have been useful in the past (or may be useful in the future), performing it incurs a penalty in the computational resources required. Further, such code still represents code that a programmer needs to understand, and hence contributes to the cognitive load. Hence, removing such code can make the code better performant and easier to maintain.

### What about optimization branches

A common pattern that is seen in performance oriented programs is optimization of certain often occuring conditions. For example, optimization of multiplication of two by shifts. This optimization can take place only if the multiplier is 2. Hence, a program that checks and optimizes for multiplication by 2 will have an immortal mutant in the program that disables that optimization. Here, while by usual definitions, both are equivalent programs, we argue that the performance difference should have been noticeable, and verified by a test case. Otherwise, one is relying on knowledge of conditions that is not codified anywhere, and may be subject to change (e.g y2k). Hence, we argue that optimization immortals are not true immortals, and inspecting them can be worth the effort spent.

### Functional idoms

One often finds that one of the ways to eliminate immortal mutants is to rewrite an imperative style function in a functional idiom. This often reduces the quantity of the code involved, reducing both mortal and immortal mutants. The more concise code from the functional idioms require using functions that are harder to replace exactly (because each function does more), and hence result in less immortals. Here again, the equivalent mutants are an opportunity to improve the code

#### Why smaller number of mutants are better

Number of mutants represent the complexity of a piece of code. A reduction in the number of mutants represent a reduction in the complexity because there is less opportunity to go wrong (vague -- needs to rethink).

### Code duplication

A common reason for a large number of immortal mutants is duplicated code in the code base. If the original code contained immortal mutants, duplication of it will multiply the number of immortals. Since duplicated code is often indicative of poor code, immortals can often serve as a powerful signal for code quality.


### Estimating the number of equivalent mutants

There seems to be few research papers regarding equivalent mutants. The only ones I have been able to find is from Ayad et al. [3] that tries to relate program redundancy to the number of equivalent mutants, and another from me [4] that applies simple statistical estimation using random sampling. A third approach (that I have not seen used so far) can be to make use of the [lincoln index](https://www.johndcook.com/blog/2010/07/13/lincoln-index/) from the capture-recapture ecological statistics literature.

#### Lincoln Index

The basic idea is that if you have two mutation testers that are independent of each other tasked to find killable mutants from a set of mutants M, and they provide $$ K_1 $$ (from the first), and $$ K_2 $$ (from the second) as the estimate of total killable mutants (equvalent mutants $$ E = M - K_{actual} $$ ), then the actual $$ K $$ can be estimated as below

$$ |K| = \frac{ |K_1| \times |K_2| }{ |K_1 \cap K_2| } $$

That is, say $$p_1$$ is the effectiveness of first tester and $$p_2$$ is the effectiveness of second tester ( $$ Effectiveness  = \frac{K_{Found}}{K_{Actual}} $$ ), then 

$$ \frac{ (K_{A} p_1 \times K_{A} p_2) }{K_{A} p_1 p_2} = K_{A} $$

If both testers are independent, and each mutant has similar probability of being detected. That is,

$$  |K_1 \cap K_2| = K_{A} p_1 p_2 $$

A slightly better technique for the estimation is given by [Seber](http://ag.unr.edu/sedinger/Courses/ERS488-688/lectures/openjolly-seber.pdf)

$$ |K| = \frac{ |K_1 + 1| \times |K_2 + 1| }{ |K_1 \cap K_2| + 1 } - 1 $$

The interesting thing here is that the mutation testers need not be human. Given a simple sample space explorer as in [xmutant.py](https://github.com/vrthra/xmutant.py) [4], one can turn it loose on the complete set of mutants, and let it kill $$ K_1 $$, and let your own test suite that you are evaluating kill $$ K_2 $$ mutants, then the above formula can be applied to get an estimate of K.

The main assumption we made here is that all mutants are equally hard to catch. However, that can be overcome by using more complex estimators. The nice thing about mutation analysis is that one can quite accurately estimate the probability distribution for difficulty of killing by looking at the kill matrix from both methods. Further, one can refine the population estimate further by using better or more varied fuzzers. See Accettura et al.[5] for details on capture-recapture models.

### References

* [1] Jorge López, Natalia Kushik, Nina Yevtushenko [Source Code Optimization using Equivalent Mutants
](https://arxiv.org/abs/1803.09571) published at Information and Software Technology Volume 103, November 2018, Pages 138-141
* [2] Paolo Arcaini, Angelo Gargantini, Elvinia Riccobene, Paolo Vavassori [A novel use of equivalent mutants for static anomaly detection in software artifacts](https://www.sciencedirect.com/science/article/abs/pii/S0950584916300180) Published at Information & Software Technology 2017
* [3] Imen Marsit, Nazih Mohamed Omri, Ali Mili [Estimating the Survival Rates of Mutants](https://web.njit.edu/~mili/mad.pdf) 2017 in ICSOFT.
* [4] Gopinath, Alipour, Ahmed, Jensen, Groce [How hard does mutation analysis have to be, anyway?](http://rahul.gopinath.org/publications/#gopinath2015how) ISSRE, 2015
* [5] Nicola Accettura, Giovanni Neglia, Luigi Alfredo Grieco [The Capture-Recapture Approach for Population
Estimation in Computer Networks](https://telematics.poliba.it/publications/2015/COMNET-accettura.pdf) in Computer Networks 2015
* [6] Marsit Imen, Mohamed Nazih Omri, Ji Meng Loh, Ali Mili [Impact of Mutation Operators on the Ratio of Equivalent Mutants](https://www.researchgate.net/publication/325895168_Impact_of_Mutation_Operators_on_the_Ratio_of_Equivalent_Mutants) SOMET 2018

Please comment [here](https://gist.github.com/vrthra/aa7527ee5c6085bb9124d06a7f24c662)
