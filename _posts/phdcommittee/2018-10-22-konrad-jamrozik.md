---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd jamrozik 2018]
e: Mining Sandboxes
---

#### Dr. Eng. Thesis

Mining Sandboxes

#### Abstract

Modern software is ubiquitous, yet insecure. It has the potential to expose billions of humans to serious harm, up to and including losing fortunes and taking lives. Existing approaches for securing programs are either exceedingly hard and costly to apply, significantly decrease usability, or just don’t work well enough against a determined attacker.
In this thesis we propose a new solution that significantly increases application security yet it is cheap, easy to deploy, and has minimal usability impact.
We combine in a novel way the best of what existing techniques of test generation, dynamic program analysis and runtime enforcement have to offer: We introduce the concept of sandbox mining. First, in a phase called mining, we use automatic test generation to discover application behavior. Second, we apply a sandbox to limit any behavior during normal usage to the one discovered during mining. Users of an application running in a mined sandbox are thus protected from the application suddenly changing its behavior, as compared to the one observed during automatic test generation. As a consequence, backdoors, advanced persistent threats and other
kinds of attacks based on the passage of time become exceedingly hard to conduct covertly. They are either discovered in the secure mining phase, where they can do no damage, or are blocked altogether.
Mining is cheap because we leverage fully automated test generation to provide baseline behavior. Usability is not degraded: the sandbox runtime enforcement impact is negligible; the mined behavior is comprehensive and presented in a human readable format, thus any unexpected behavior changes are rare and easy to reason about. Our BOXMATE prototype for Android applications shows the approach is technically feasible, has an easy setup process, and is widely applicable to existing apps. Experiments conducted with BOXMATE show less than one hour is required to mine Android applications sandboxes, requiring few to no confirmations for frequently used functionality.

[Link](https://publikationen.sulb.uni-saarland.de/bitstream/20.500.11880/27191/1/KJamrozik_PhD_thesis_10_22_2018.pdf)
