---
layout: post
categories : publications
tagline: "."
tags : publication
e: Mutations -- How Close are they to Real Faults? 
title: Mutations -- How Close are they to Real Faults?
authors: Rahul Gopinath, Carlos Jensen, Alex Groce
venue: IEEE International Symposium on Software Reliability Engineering (ISSRE) 
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Mutation analysis is often used to compare the effectiveness of different test suites or testing techniques. One of 
the main assumptions underlying this technique is the Competent Programmer Hypothesis, which proposes that programs are very 
close to a correct version, or that the difference between current and correct code for each fault is very small. 
Researchers have assumed on the basis of the Competent Programmer Hypothesis that the faults produced by mutation 
analysis are similar to real faults. While there exists some evidence that supports this assumption, these studies are based 
on analysis of a limited and potentially non-representative set of programs and are hence not conclusive. In this paper, we 
separately investigate the characteristics of bugfixes and other changes in a very large set of randomly selected projects using 
four different programming languages.  Our analysis suggests that a typical fault involves about three 
to four tokens, and is seldom equivalent to any traditional mutation operator. We also find the most frequently occurring 
syntactical patterns, and identify the factors that affect the real bug-fix change distribution. Our analysis suggests that different 
languages have different distributions, which in turn suggests that operators optimal in one language may not be optimal 
for others. Moreover, our results suggest that mutation analysis stands in need of better empirical support of the connection 
between mutant detection and detection of actual program faults in a larger body of real programs. 

<!--script async class="speakerdeck-embed" data-id="5da07deb69d7421995908f629c055ace" data-ratio="1.33333333333333" src="//speakerdeck.com/assets/embed.js"></script-->

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/issre2014/gopinath2014mutations.pdf "paper")
[<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/issre2014/gopinath2014mutations.bib "reference")
[<em class="fa fa-database fa-lg" aria-hidden="true"></em>](https://dx.doi.org/10.17605/OSF.IO/ENZQK "data")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/mutations-how-close-are-they-to-real-faults "presentation")
