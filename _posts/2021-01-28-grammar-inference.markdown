---
published: true
title: Blackbox Inference of Context Free Grammars -- Verification
layout: post
comments: true
tags: grammar mining, context-free grammar
categories: post
---

The problem of infering the input specification of a program has recently seen some
interest[^bastani2017synthesizing][^wu2019reinam] from researchers. This is of huge interest in fuzzing as recovery
of the input specification can improve the efficiency, effectiveness, and generality
of a fuzzer by leaps and bounds.

The best way to go about it is to look for a general solution with proofs. However,
a fully general solution to the problem is impossible, and is as hard as reversing
the RSA encryption[^angluin1995when]. However, this has not stopped researchers from
attempting to look for heuristics which are applicable to context-free grammars that
are found in real-world software. The idea being that, the theoretical limitation
could be about pathological grammars. Even if one could recover the grammar of a
reasonable subset of context-free grammars, it is a win. Indeed, Clark et al.[^clark2008a]
takes this approach. Another reasonable approach is to look for approximations.

Now, how does one verify their approach? One approach that recent research has taken
is to try and recover the context free grammar from one of the blackbox programs, then
use the recovered grammar to generate inputs, and check how many of these inputs are
accepted by the program under grammar mining[^bastani2017synthesizing][^wu2019reinam].
Now, for completeness, one needs to turn around, and use the grammar as an acceptor
for the input produced by the program.
The problem here is that going the other way is tricky. That is, the program under
grammar mining is an acceptor. How do you turn it into a producer? The route that
is taken by Bastani et al. is to write a grammar by hand. Then, use this grammar to
generate inputs, which are parsed by the mined grammar [^1]
However, this is unsatisfying and error prone. Is there a better way?

Turns out, there is indeed a better way. Unlike in [whitebox grammar recovery](https://rahul.gopinath.org/resources/fse2020/gopinath2020mining.pdf)
for blackbox grammar inference, there is no particular reason to start with a program.
Instead, start with a context-free grammar of your choice, and use a standard
context-free parser such as GLL, GLR, CYK or Earley parser to turn it into an acceptor. Then, use
your blackbox grammar inference algorithm to recover the grammar. Now, you have the
original grammar, and the recovered grammar. You can now use a number of tools[^madhavan2015automating] to
check how close they are to each other. Indeed, the most basic idea is to make
one grammar the producer, and see how many of the produced is accepted by the second.
Then, turn it around, make the second the producer, and see how many of the produced
is accepted by the first. We note that doing both is extremely important to have
confidence in the results. What if we only do one side? That is, only verify that
the inputs produced by the first are accepted by the second? In that case, nothing
prevents us from infering an extremely permissive grammar for the second that never
rejects any input -- say `/.*/`. This grammar would have 100% accuracy in this testing even though
it is a very poor inferred grammar. Such problems can only be detected if we turn
around and use the infered grammar as producer. Now, imagine that the infered grammar
doesn't generalize at all, and produces only a small set of inputs. In that case, again
the original grammar will accept all generated inputs, resulting in 100% accuracy even though
the infered grammar was bad. Hence, both tests are equally important.

The TLDR; is that **if you are doing blackbox grammar inference, please start with a grammar rather than a program. Use a parser to turn the grammar into an acceptor, and infer the grammar of that acceptor. Then verify both grammars against each other** .

A nice result that I should mention here is that comparison of deterministic context-free
grammars is decidable![^senizergues2001l]. Géraud Sénizerguese was awarded the Gödel Prize in
2002 for this discovery. What this means is that if the grammars are deterministic, you
can even compare them directly.


[^1]: We note here that the grammar derived by [GLADE](https://github.com/obastani/glade) is not in the usual format, and hence, we could not verify that their parser is correct. Unfortunately, general context-free parsers are notoriously difficult to get right as shown by the history of the Earley parser.

[^bastani2017synthesizing]: Bastani, O., Sharma, R., Aiken, A., & Liang, P. (2017). Synthesizing program input grammars. ACM SIGPLAN Notices, 52(6), 95-110.
[^wu2019reinam]: Wu, Z., Johnson, E., Yang, W., Bastani, O., Song, D., Peng, J., & Xie, T. (2019, August). REINAM: reinforcement learning for input-grammar inference. In Proceedings of the 2019 27th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (pp. 488-498).
[^angluin1995when]: Angluin, D., & Kharitonov, M. (1995). When Won′ t Membership Queries Help?. Journal of Computer and System Sciences, 50(2), 336-355.
[^clark2008a]: Clark, A., Eyraud, R., & Habrard, A. (2008, September). A polynomial algorithm for the inference of context free languages. In International Colloquium on Grammatical Inference (pp. 29-42). Springer, Berlin, Heidelberg.

[^madhavan2015automating]: Madhavan, R., Mayer, M., Gulwani, S., & Kuncak, V. (2015, October). Automating grammar comparison. In Proceedings of the 2015 ACM SIGPLAN International Conference on Object-Oriented Programming, Systems, Languages, and Applications (pp. 183-200).
[^fischer2011comparison]: Fischer, B., Lämmel, R., & Zaytsev, V. (2011, July). Comparison of context-free grammars based on parsing generated test data. In International Conference on Software Language Engineering (pp. 324-343). Springer, Berlin, Heidelberg.
[^senizergues2001l]: Sénizergues, G. (2001). L (A)= L (B)? decidability results from complete formal systems. Theoretical Computer Science, 251(1-2), 1-166.

