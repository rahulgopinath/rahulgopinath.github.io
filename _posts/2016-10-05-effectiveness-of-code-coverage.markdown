---
published: true
title: Is Code Coverage Effective in Preventing Bugs?
layout: post
comments: true
tags: [coverage]
categories: post
---

I had [previously written about](/post/2015/10/01/should-we-use-mutation-score/)
the utility of code coverage when compared to mutation score. While I
suggested that coverage is indeed useful since it explains a larger amount
of variation of mutation score than test suite alone, it is questionable
if mutation score is the final arbiter when it comes to test suite
effectiveness.

Indeed, one could make the point that even mutation analysis has not
been whetted thoroughly notwithstanding the result of Just et al. ([Just 2014](/references#just2014are))
because the results depend on a only a few bug fixes.

We wanted to validate the effectiveness of code coverage in detecting
bugs. One of the best ways to do that is to look at the incidence of
bugs in covered code, and compare it with code that is uncovered.

This is what we investigated in our latest research ([FSE 2016](/publications/#ahmed2016can)).

What we did is to select 49 programs from Github, and selected a point
in time as the *epoch*. Next, we looked at all commits from that epoch,
and classified them as bugfixes or feature fix. Now, for a given line, we
looked at the total number of bugfix commits after epoch until the first
feature fix.

Next, we compared the difference in number of bugfixes between the
covered lines at epoch and uncovered lines. We found that for statement
coverage, a covered line has about 0.68 bugfix, while
for a non-covered line, the number of bugfixes were about 1.2. That is,
a non-covered line is about twice as likely to be buggy as that of a
line covered by a test case.

Our results suggest that code coverage is indeed useful, and can serve
to reduce the incidence of bugs if one heeds the results.
