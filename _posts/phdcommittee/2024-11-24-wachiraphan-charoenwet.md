---
layout: post
categories : phdcommittee
tagline: "."
tags : [phdcommittee phd wachirapancharoenwet 2025]
e:  Complementing Secure Code Review with Automated Program Analysis
---

#### Ph.D. Thesis

Complementing Secure Code Review with Automated Program Analysis

#### Abstract

Code review is a software quality assurance practice that allows developers to provide feedback on proposed code changes with the goal of improving code quality and identifying defects before code integration. Despite its manual nature, the flexibility and low process overhead of code review have contributed to its widespread adoption in modern software development. Nevertheless, security bugs and vulnerabilities continue to be reported and exploited in production systems. These incidents raise concerns about the effectiveness of current secure code review practices and suggest that security bugs may slip through the review process due to factors such as limited reviewer resources, cognitive overload, or lack of security expertise.

Prior research has suggested automated program analysis techniques as potential support mechanisms for code review. However, most existing tools are designed for system-level analysis and have not been thoroughly examined in the context of incremental and localized code changes typical in code reviews. Reviewers, often constrained by limited time and context, face difficulties in understanding proposed changes while relying on automated outputs that may not align with review-specific needs. As a result, it remains unclear how these techniques can effectively assist secure code review in practice. Moreover, prior research on secure code review has largely focused on reviewer behavior and the prevalence of security issues, leaving open questions about the practical effectiveness of the review process itself and how automated techniques can be meaningfully integrated to help detect security-relevant concerns.

The goal of this thesis is to advance automation in secure code review by leveraging program analysis techniques to effectively support developers and enhance the overall secure code review process. To achieve this, we conducted three individual studies.
The first is an empirical study that investigated how secure code reviews are realistically performed in practice. The second and third studies examined how static and dynamic analysis techniques—specifically static application security testing (SAST) and fuzzing—can support reviewers in identifying potential vulnerabilities within the context of code changes.

In the first empirical study, we investigated how secure code review practices address software weaknesses that may lead to security issues. We conducted a case study on two large open-source projects, OpenSSL and PHP, analyzing code review discussions to examine the types of security concerns raised by reviewers and how those concerns were handled. The study shows that reviewers can identify a diverse range of software weaknesses during code review. However, some weakness categories associated with past vulnerabilities received relatively limited attention, and a number of identified concerns were left unresolved or insufficiently addressed, highlighting practical gaps in current secure code review practices.


In the second study, we evaluated the practical effectiveness of static application security testing (SAST) tools in supporting secure code review. Using real-world vulnerability-contributing commits from C/C++ projects, we examined how effectively SAST warnings align with vulnerable code changes and whether they can assist in prioritizing review effort. Our findings indicate that SAST tools can help highlight potentially risky code regions and improve prioritization during review. However, the results also reveal limitations in coverage and warning relevance, suggesting that existing SAST tools alone are insufficient for reliable secure code review support.

In the third study, we investigated how dynamic analysis techniques can support reviewers by identifying behavioral differences between program versions. We developed a framework that leverages likely invariants derived from non-crashing fuzzing inputs to detect behavioral changes associated with code modifications. The results demonstrate that behavioral differences inferred from fuzzing inputs can help expose subtle bugs and regressions that may evade conventional fuzzing campaigns and static analysis tools. The study further highlights the potential of behavioral signals to complement existing review support techniques at a finer granularity of code changes.

The three studies in this thesis reveal key issues in current secure code review practices and the potential of automated program analysis to offer meaningful support. 
While human reviewers can identify a wide range of weakness types, certain critical categories—particularly those linked to severe past vulnerabilities—remain under-discussed or unresolved. Static analysis tools like SAST help prioritize code changes and detect issues at the function level in many cases, but often produce irrelevant warnings and miss others. Complementary dynamic analysis based on likely invariants from non-crashing fuzzing inputs shows strong potential in uncovering subtle behavioral bugs, which evade both reviewers and SAST, at the code block level. These findings highlight the need for integrated approaches that combine human judgment with insights from both static and dynamic analysis.

[Link](https://minerva-access.unimelb.edu.au/items/9aa4092f-dd6b-47df-9d28-9e1d9b1fcbee)
