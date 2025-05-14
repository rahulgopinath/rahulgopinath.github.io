## Writing a paper with me

(Adapted from recommendations of Andreas Zeller)

### General structure.

 * Follow the recommendations by Arie van Deursen: https://avandeursen.com/2013/07/10/research-paper-writing-recommendations/
 * Most important: One section per contribution, one contribution per section.

### Files.  

* I typically work on several papers at once, so make your paper name unique.
* One single LaTeX file, named <venue>-<keyword>.tex, say “fse2019-ddmax.tex”.
* No \includes, no other .tex files unless coming from a third party or program.
* Bibliography goes into <venue>-<keyword>.bib.
* Pictures go into PICS/.  include sources.

### Math mode and numbers.  

* Use math mode only for formula.  Numbers need not go into math mode.  The year is 2019, not $2019$.
* Numbers 2–12 are typeset as words, unless they reference something.  It is the next three sections, not the next 3 (and not the next $3$ either).
* Multi-letter identifiers in math mode go into \textit.  $foo$ is $f \times o \times o$.  You probably want $\textit{foo}$.

### Line breaks.

* Use tildes (~) to tie numbers to text.  It’s Line~2, Rules 3~to~4, and the next 42~seconds,  

### Bibliography.

* In the bibliography, handle caps properly.  It’s {CISPA} work on {Android}, {C++}, and {Java}.
* In the bibliography use the following format for keys:
  authorlastnameYYYYfirstword For ``Learning Input Tokens for Effective Fuzzing'' by Bjoern Mathis, Rahul Gopinath and Andreas Zeller, the bib key is *mathis2020learning*.

### Indentation.

* Do not indent regular text.

### References.

* Use the `cleveref` package and \Cref{<label>} to make cross-references.
* Prefix labels with sec:, fig:, tab:, alg:, line:.  No subsec: or subsubsec:.

### Todos.

* Have a \todo{} command such that I can leave hints. The following is the
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

