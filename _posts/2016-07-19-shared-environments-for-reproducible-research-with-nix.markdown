---
published: false
title: Shared Environments for Reproducible Research with Nix
layout: post
tags: [nixos, reproducible-research]
---
*tl;dr* How to install Nix on a non `/nix` location, which can be shared across multiple users

*caveats* Very hacky.

As a researcher working on software empirical research, one of the *pain points* in my research is the creation and maintenance of an environment that can be reproduced easily. Ideally, I would like to switch environments easily, according to which project I am working on, and even experiment on new programs without affecting my old environments.

Further, one would also wish to collaborate with other researchers, and ideally share your resources with them. If you were able to set up and environment once in your machine, it is a waste of time and energy to try to do that again for another user. These are the constraints that led me to the [Nix](https://nixos.org/nix/) package manager in the first place.

Unfortunately, while we have little restriction in available space, or computational power, our systems are fairly locked down, with no chance of getting access to a folder like `/nix` in all the machines available. So a normal `/nix` install is completely out of question.