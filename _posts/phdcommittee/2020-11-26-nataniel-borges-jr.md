---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd felixklein 2020]
e: Synthesizing Stream Control
---

#### Ph.D. Thesis

Learning the Language of Apps

#### Abstract

To explore the functionality of an app, automated test generators systematically identify and interact with its user interface (UI) elements. A key challenge is to synthesize inputs which effectively and efficiently cover app behavior.
To do so, a test generator has to choose which elements to interact with but, which interactions to do on each element and which input values to type. In summary, to better test apps, a test generator should know the app's language , that is, the language of its graphical interactions and the language of its textual inputs. In this work,
we show how a test generator can learn the language of apps and how this knowledge is modeled to create tests. We demonstrate how to learn the language of the graphical input prior to testing by combining machine learning and static analysis, and how to refine this knowledge during testing using reinforcement learning. In our experiments, statically learned models resulted in 50% less ineffective actions an average increase in test (code) coverage of 19%, while refining these through reinforcement learning resulted in an additional test (code) coverage of up to 20% . We learn the language of textual inputs, by identifying the semantics of input fields in the UI and querying the web for real-world values. In our experiments, real-world values increase test (code) coverage by ≈ 10%;
Finally, we show how to use context-free grammars to integrate both languages into a single representation (UI grammar), giving back control to the user. This representation can then be: mined from existing tests, associated to the app source code, and used to produce new tests. 82% test cases produced by fuzzing our UI grammar can reach a UI element within the app and 70% of them can reach a specific code location.

[Link](-)
