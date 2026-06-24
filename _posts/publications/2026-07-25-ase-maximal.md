---
layout: post
categories : publications
tagline: "."
tags : publication
e:  Maximal Format-Free Data Repair
title: Maximal Format-Free Data Repair
authors: Zijian Luo, Xi Wu, Hong Jin Kang, Alan Fekete, Rahul Gopinath
venue: ACM/IEEE International Conference on Automated Software Engineering (ASE)
kind: conference
thesort: peerreviewed
peerreviewed: yes
---

Modern data-processing pipelines rely on input records conforming
to strict format specifications. In practice, however, data corruption
can occur at numerous stages including data-entry error, corruption
during input processing and retransmission, inconsistent formatting,
 and incompatible specifications. Such corrupted data can result
in loss of records, reducing the accuracy of processing.

Rather than discarding corrupted records and losing valuable information,
 one can attempt to repair the data. Data-repair solutions
such as regular expression based repair and error-correcting parsers
require a specification to perform structural repairs.

Specification-free techniques such as ddmax and εRepair are
limited in repair operations, repair location, and require specific
parser properties that are often unavailable.

To tackle this challenge, we introduce βMax, a novel format-free
data repair algorithm optimal with respect to the provided example
data, with maximal data-recovery and minimal parser constraints.

Despite requiring less information than εRepair, βMax repairs
83% of all corrupt records—1.77×the rate achieved by εRepair,
while using 27.7×fewer oracle calls.

[<em class="fa fa-book fa-lg" aria-hidden="true"></em>](/resources/ase2026/luo2026-maximal.pdf "paper")
<!-- [<em class="fa fa-bookmark-o fa-lg" aria-hidden="true"></em>](https://raw.githubusercontent.com/rahulgopinath/rahulgopinath.github.io/master/resources/ase2026/luo2026-maximal.bib "reference")
[<em class="fa fa-desktop" aria-hidden="true"></em>](https://speakerdeck.com/rahulgopinath/revisiting-the-relationship-between-fault-detection-test-adequacy-criteria-and-test-set-size "presentation") -->

