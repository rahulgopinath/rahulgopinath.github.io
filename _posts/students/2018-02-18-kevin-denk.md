---
layout: post
category : student
tagline: "."
tags : [student kevindenk 2018]
e: Evaluating the Robustness of Ethereum Virtual Machines
---

### Advised Masters Students

Kevin Denk<br/>

#### Thesis

Evaluating the Robustness of Ethereum Virtual Machines

#### Abstract

Ethereum is a blockchain-based verifiable distributed computing platform that is used for implementation of smart contracts. It consists of a network of nodes each running an Ethereum Virtual Machine capable of executing and verifying transactions in the network. The network can be used to execute smart contracts consisting of several transactions. These smart contracts, in turn, provide a way to formalize agreements between multiple real-world entities. The entities involved in a smart contract rely on the correct and verifiable execution of EVMs in the network. Hence, the robustness of EVMs is a key concern for Ethereum users. While previous research has focused on the formal verification of smart contracts and their vulnerabilities, little research has been done on whether the EVM implementations themselves are subject to vulnerabilities.
In this work, we evaluate the robustness of EVMs applying grammar-based fuzzing and a technique called parser-directed test generation. We show with substantial coverage results that we reach deep execution paths in the EVMs. With our evaluation, we found that the implementations Geth-EVM and Parity-EVM are robust regarding their smart contract execution. Along with grammar-based fuzzing, we applied differential testing which revealed three divergences in the behavior of Geth-EVM and Parity-EVM. With our parser- directed test generation algorithm, we were able to generate exclusively valid inputs which were accepted by all EVMs.
