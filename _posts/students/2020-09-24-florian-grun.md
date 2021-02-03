---
layout: post
categories : student
tagline: "."
tags : [student floriangrun 2020]
e: ARM Processor Fuzzing via QEMU
---

#### Bachelors Thesis

ARM Processor Fuzzing via QEMU

#### Abstract


Each processor manufacturer hands out documentation of all usable processor
instructions for their specific processor architectures. However, not all
possible sequences of instructions are well-defined in those documentations;
hence, their execution is undefined. This bachelor thesis describes the
implementation of a tool capable of testing a QEMU-emulated ARM architecture.
It is used to investigate if there appears any recognizable misbehavior
when trying to execute undefined sequences of instructions.
To do so, the grammar-based F1 prototype fuzzer, combined with a self-written
instruction grammar manually derived from an instruction set description,
is used. Being able to create a massive amount of instruction inputs,
they are executed on the emulated ARM processor architecture. The target of this
fuzzing campaign is a QEMU-emulated ARM Cortex-A9 processor, and it is tested in
user as well as in supervisor execution mode.
