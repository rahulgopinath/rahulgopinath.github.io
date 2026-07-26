---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd panlianglu 2025]
e:  Advancing Practical Automated Security Testing for Web Applications
---

#### Ph.D. Thesis

Advancing Practical Automated Security Testing for Web Applications

#### Abstract

Web applications are increasingly central to modern digital infrastructure, yet they
remain highly susceptible to security vulnerabilities. Automated testing offers a scalable
path toward improving web application robustness, but faces persistent challenges—
including the oracle problem, the lack of formal specifications, and the difficulty of
detecting subtle vulnerabilities like excessive data exposures.
This thesis advances practical automated security testing by rethinking how human in-
teraction artifacts—such as captured traffic and behavioral relationships—can be lever-
aged to reduce manual effort while maintaining high testing effectiveness. It introduces
EDEFuzz, a novel fuzzing tool for detecting Excessive Data Exposure (EDE) vulnerabil-
ities in web APIs. EDEFuzz applies metamorphic testing principles to compare related
web responses, enabling effective and scalable detection of sensitive data leaks without
requiring exhaustive manual specifications. A controlled user study demonstrates that
EDEFuzz improves both the accuracy and efficiency of EDE detection while reducing
user cognitive load.
The thesis also presents Trailblazer, an end-to-end fuzzing framework designed to un-
cover server-side crashes in undocumented or poorly documented APIs. Trailblazer
bootstraps its test generation process from real-world API traffic, autonomously identi-
fying endpoints and inferring payload structures without needing an API specification.
This black-box approach surfaces crash-inducing edge cases that are often missed by
existing tools, highlighting its applicability to complex, real-world web systems.
Together, these contributions demonstrate that reusing naturally generated human in-
teraction artifacts can enable practical, low-overhead, and scalable security testing. The
findings point toward new directions for building intelligent, human-informed testing
systems that better match the realities of modern web development.

[Link](https://rest.mars-prod.its.unimelb.edu.au/server/api/core/bitstreams/086995d8-4055-40af-8ddf-eef34b8cc9bd/content)
