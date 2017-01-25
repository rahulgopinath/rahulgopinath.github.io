---
published: true
title: Have we gotten better at writing code?
layout: post
comments: true
tags: bugs
---

An analysis of Linux kernel vulnerabilities with partial data from
[kees dataset](https://outflux.net/blog/archives/2016/10/20/cve-2016-5195/).

![Linux kernel vulnerabilities over the years](/resources/posts/2017/vulnerabilities-lifetime.png)

The impact is 4 for critical, 3 for high, 2 for medium, and 1 for low. The blue
regression line is the line we should expect if the regression formula was
`Introduced = Found * LOC`. The dark red regression line is for the regression
formula `Introduced = Found` The regression line that does not contain `LOC`
has an R^2 of `0.2564`, while adding the `LOC` changes the R^2 to `0.9893`

(post still in progress)
