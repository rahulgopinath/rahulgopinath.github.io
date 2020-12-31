---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd felixklein 2020]
e: Synthesizing Stream Control
---

#### Ph.D. Thesis

Synthesizing Stream Control

#### Abstract

For the management of reactive systems, controllers must coordinate time,data 
streams, and data transformations, all joint by the high level perspective of 
their control flow. This control flow is required to drive the system 
correctly and continuously, which turns the development into a challenge. The 
process is error-prone, time consuming, unintuitive, and costly. An attractive 
alter-native is to synthesize the system instead, where the developer only 
needs to specify the desired behavior. The synthesis engine then automatically 
takes care of all the technical details. However, while current algorithms for 
the synthesis of reactive systems are well-suited to handle control, they fail 
on complex data transformations due to the complexity of the comparably 
large data space. Thus, to overcome the challenge of explicitly handling the 
data we must separate data and control.

We introduce Temporal Stream Logic(TSL), a 
logic which exclusively argues about the control of the controller, while 
treating data and functional transformations as interchangeable black-boxes. In 
TSL it is possible to specify control flow properties independently of the 
complexity of the handled data. Furthermore, with TSL at hand a synthesis engine
can check for realizability, even without a concrete implementation of the 
data transformations.We present a modular development framework that first uses 
synthesis to identify the high level control flow of a program. If successful, 
the created control flow then is extended with concrete data transformations in 
order to be compiled into a final executable.

Our results also show that the 
current synthesis approaches cannot re-place existing manual development work 
flows immediately. During the development of a reactive system, the developer 
still may use incomplete or faulty specifications at first, that need the be 
refined after a subsequent inspection. In the worst case, constraints are 
contradictory or miss important assumptions, which leads to unrealizable 
specifications. In both scenarios, the developer needs additional feedback from 
the synthesis engine to debug errors for finally improving the system 
specification. To this end, we explore two further possible improvements. On the
one hand, we consider output sensitive synthesis metrics, which allow to 
synthesize simple and well structured solutions that help the developer to 
understand and verify the underlying behavior quickly. On the other hand, we 
consider the extension of delay, whose requirement is a frequent reason for 
unrealizability. With both methods at hand, we resolve the aforementioned 
problems and therefore help the developer in the development phase with the 
effective creation of a safe and correct reactive system.


[Link](https://www.react.uni-saarland.de/publications/diss-klein.pdf)
