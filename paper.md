---
layout: page
header: Paper
title : Writing a paper with me
header : Writing a paper with me
group: navigation
exclude: true
---

## Writing a paper with me

(Adapted from recommendations of [Andreas Zeller](https://andreas-zeller.info/2013/04/05/my-top-ten-presentation-issues-in.html))

### General structure.

 * Follow the recommendations by [Arie van Deursen](https://avandeursen.com/2013/07/10/research-paper-writing-recommendations/)
 * Most important: One section per contribution, one contribution per section.

### Files.  

* I typically work on several papers at once, so make your paper name unique.
* One single LaTeX file, named `<venue>-<keyword>.tex`, say `fse2019-ddmax.tex`.
* No `\includes`, no other .tex files unless coming from a third party or program.
* Bibliography goes into `<venue>-<keyword>.bib`.
* Pictures go into `PICS/`. include sources.

### Math mode and numbers.  

* Use math mode only for formula.  Numbers need not go into math mode.  The year is `2019`, not `$2019$`.
* Numbers 2–12 are typeset as words, unless they reference something.  It is the next three sections, not the next 3 (and not the next `$3$` either).
* Multi-letter identifiers in math mode go into `\textit`.  `$foo$` is `$f \times o \times o$`.  You probably want `$\textit{foo}$`.

### Line breaks.

* Use tildes (`~`) to tie numbers to text.  It’s `Line~2`, `Rules 3~to~4`, and the next `42~seconds`,

### Hyphen, double hyphen (en dash), and tripple hyphen (em dash)
* Use hyphens `-` for word joining; but for those who are not native speakers. It is a *high-quality* product, but this product is high quality.
* Use double hyphens to indicate ranges. `pages 5--10` and `experiments 1-10`.
* Use tripple hyphens for parenthetical interruptions. `Use of context-free grammars---grammars that contain recursive rules---are encouraged`.

### Bibliography.

* In the bibliography, handle caps properly.  It’s {CISPA} work on {Android}, {C++}, and {Java}.
* In the bibliography use the following format for keys:
  authorlastnameYYYYfirstword For ``Learning Input Tokens for Effective Fuzzing'' by Bjoern Mathis, Rahul Gopinath and Andreas Zeller, the bib key is *mathis2020learning*.
* Cleanup the bibliography. Do not leave the abstract and other extra tags which come when copying from other sources. Indent it properly.

### Indentation.

* Do not indent regular text.

### Tables

* Columns of numbers should be right justified, and text should be left justified.
* Stick with a standard number of decimal places. I advocate for one or two decimal places
* If in the column, at least one cell has a decimal place, all cells should have that many places in decimal. An exception is the overall statistics line.
* Provide overall statistics when possible. If you have a column of numbers, provide mean and standard deviation/confidence intervals as a row at the end.

### Threats to Validity

Try to have a threats to validity section. It is an excercise that makes you think what impact circumstances beyond your control can have on your results. Be honest. It is OK to just acknowledge the threat and move on. However, I would also advocate for adding a line of mitigation where you have some mitigation in place. The standard sections in threats to validity are the following:

#### Internal Validity
Internal validity concerns the impact of systemic errors. A familiar example is the impact of bugs, in implementation, data processing, and aggregation. Another is selection bias. Does your choice of tool have an impact? What about the load on the machine your experiment is run? Think carefully about what other uncontrolled factors can have an impact.

#### External Validity
External validity is about the generality of your findings. Are your subjects constrained in any way (due to them being impelemnted in a particular language, due to the data coming from a single source etc.)

#### Construct Validity
Construct validity is about whether you are measuring the thing you are trying to measure. In software engineering, we often have to rely on proxies. For example, measuring the coverage/mutation score achieved as a proxy for the effectiveness of a fuzzer.

### References.

* Use the `cleveref` package and `\Cref{<label>}` to make cross-references.
* Prefix labels with sec:, fig:, tab:, alg:, line:.  No subsec: or subsubsec:.

### Todos.

* Have a `\todo{}` command such that I can leave hints. The following is the
  latex code for doing so. It adds a footnote with an editor mark in the page
  border.

```
\newcounter{todocounter}
\newcommand{\todo}[1]{\marginpar{$|$}\textcolor{red}{\stepcounter{todocounter}\footnote[\thetodocounter]{\textcolor{red}{\textbf{TODO }}\textit{#1}}}}
\newcommand{\done}[1]{\marginpar{$*$}\textcolor{green}{\stepcounter{todocounter}\footnote[\thetodocounter]{\textcolor{black}{\textbf{DONE }}\textit{#1}}}}

% Hide TODOs for final version if needed
\IfFileExists{SUBMIT}{ % Requires creating a file named SUBMIT
\renewcommand{\todo}[1]{}
\renewcommand{\done}[1]{}
}{}
```

