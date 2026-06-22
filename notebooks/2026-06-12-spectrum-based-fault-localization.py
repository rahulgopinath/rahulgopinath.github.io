# ---
# published: true
# title: Spectrum-Based Fault Localization
# layout: post
# comments: true
# tags: debugging, fault-localization, sbfl, statistical-debugging
# categories: post
# ---
# 
# TLDR; This post is a complete implementation of Spectrum-Based Fault
# Localization (SBFL) in Python. Given a mix of passing and failing test runs,
# SBFL correlates per-line coverage with the pass/fail outcome to rank source
# lines by suspiciousness. We start with a binary search bug where all five
# metrics agree unanimously, then show a two-bug triangle classifier where
# Kulczynski and Ochiai/Dice/Jaccard give different rankings — and explain
# exactly why. The Python interpreter is embedded so that you can work through
# each step.
# 
# ## What is Spectrum-Based Fault Localization?
# 
# A failing test tells us _that_ something is wrong but not _where_. Fault
# localization is the problem of ranking source locations by their likelihood
# of being the fault site, so a developer can start their inspection at the
# top of the list rather than reading the entire codebase.
# 
# **Spectrum-Based Fault Localization (SBFL)** was introduced by Jones et al.
# at ICSE 2002 [^jones2002visualization] with the Tarantula tool. The central
# idea is simple: run the test suite, record which lines each test executes,
# and then score each line by how much more often it appears in failing runs
# than in passing runs. A line executed only in failing runs is maximally
# suspicious; a line executed equally in both is not.
# 
# The "spectrum" in SBFL refers to the coverage spectrum — the set of program
# elements (lines, branches, methods) touched by a run. SBFL needs only this
# binary hit/no-hit information per run; it does not need to understand
# program logic, read variable values, or modify the subject program.
# 
# ## Definitions
# 
# For this post, we use the following terms:
# 
# * A _subject program_ is the buggy function under investigation.
# 
# * A _reference program_ is a known-correct version of the same function,
#   used as the oracle: a run _passes_ when subject and reference agree on
#   the output, and _fails_ when they disagree.
# 
# * Treat "line $$\ell$$ was executed" as a _detector_ and "run fails" as the
#   _positive class_. The four counts for a line are then the standard
#   confusion-matrix cells:
# 
#   | | run fails | run passes |
#   |---|---|---|
#   | **$$\ell$$ executed** | $$f(\ell)$$ — true positives | $$s(\ell)$$ — false positives |
#   | **$$\ell$$ not executed** | $$F - f(\ell)$$ — false negatives | $$S - s(\ell)$$ — true negatives |
# 
#   $$F$$ is the total number of failing runs, $$S$$ the total number of
#   passing runs.
# 
# * From the table, **precision** and **recall** of the detector follow
#   directly:
#   $$ \text{Precision}(\ell) = \frac{f(\ell)}{f(\ell)+s(\ell)} \qquad
#      \text{Recall}(\ell) = \frac{f(\ell)}{F} $$
# 
# * **Ochiai** [^ochiai1957zoogeographic] is the _geometric mean_ of
#   precision and recall:
#   $$ \text{Ochiai}(\ell) = \sqrt{\text{Precision}(\ell) \times \text{Recall}(\ell)}
#      = \frac{f(\ell)}{\sqrt{(f(\ell)+s(\ell)) \cdot F}} $$
# 
# * **Dice** [^dice1945measures] is the _harmonic mean_ of precision and
#   recall, identical to the $$F_1$$ score:
#   $$ \text{Dice}(\ell) = \frac{2 \cdot f(\ell)}{2 \cdot f(\ell) + s(\ell) + (F - f(\ell))} $$
# 
# * **Kulczynski₂** [^kulczynski1928pflanzenassoziationen] is the _arithmetic
#   mean_ of precision and recall:
#   $$ \text{Kulczynski}_2(\ell) = \frac{\text{Precision}(\ell) + \text{Recall}(\ell)}{2} $$
# 
# * **Jaccard** [^jaccard1901etude] is a monotone transform of Dice —
#   ranking by Jaccard is equivalent to ranking by $$F_1$$:
#   $$ \text{Jaccard}(\ell) = \frac{f(\ell)}{f(\ell) + s(\ell) + (F - f(\ell))} $$
# 
# ## Prerequisites
# 
# SBFL uses only the Python standard library.

import sys
import math
import ast
import inspect
import textwrap

SCORE_DECIMALS = 2

# Since this notebook serves both as a web notebook and as a script that can
# be run on the command line, we redefine `__canvas__` if it is not already
# defined by the notebook environment.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print

# 
# ## The Subject Program
# 
# Our first subject is a binary search function with a subtle off-by-one bug.
# The correct behavior when the target is not found is to return `-1`; the
# buggy version returns `lo` instead. For searches that succeed, the two
# behave identically — the bug only manifests on _not-found_ inputs.
# 
# We store the source as a string and `exec` it once. This lets us extract
# `bsearch_start` from the code object without calling `inspect.getsource`,
# which raises `OSError` in Pyodide because there are no source files on
# disk in the browser sandbox.

bsearch_source = """\
def bsearch(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return lo"""

exec(bsearch_source, globals())
bsearch.__source__ = bsearch_source
bsearch_start = bsearch.__code__.co_firstlineno

# The reference returns `-1` for not-found, which is the standard contract.

def bsearch_correct(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# OK, let us do a quick check.
if __name__ == '__main__':
    result = bsearch_correct([1, 3, 5, 7, 9], 1)
    assert result == 0

# It would be good to check the lines that were covered by this test case. 
# So, let us define a simple coverage class next.
# 
# `FunctionCoverage` instruments a function with AST rewriting: it parses the
# function's source, injects `_tracker.covered.append(lineno)` before every
# statement, temporarily installs the patched version in the module globals,
# and restores the original on exit.  Calling `cov(...)` inside the `with`
# block invokes the instrumented version directly.
#
# `InjectCoverage` is the AST transformer that does the injection.
# `CoverageTracker` holds the accumulated line sequence.

class CoverageTracker:
    def __init__(self):
        self.covered = []

_tracker = CoverageTracker()

class InjectCoverage(ast.NodeTransformer):
    def visit_stmt(self, node):
        track = ast.Expr(ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(
                    value=ast.Name(id='_tracker', ctx=ast.Load()),
                    attr='covered', ctx=ast.Load()),
                attr='append', ctx=ast.Load()),
            args=[ast.Constant(value=node.lineno)],
            keywords=[]
        ))
        ast.copy_location(track, node)
        self.generic_visit(node)
        return [track, node]

    visit_Assign     = visit_stmt
    visit_AugAssign  = visit_stmt
    visit_Expr       = visit_stmt
    visit_Return     = visit_stmt
    visit_If         = visit_stmt
    visit_For        = visit_stmt
    visit_While      = visit_stmt

class FunctionCoverage:
    def __init__(self, fn):
        self._fn   = fn
        self._orig = None

    def __call__(self, *args, **kwargs):
        return self._fn.__globals__[self._fn.__name__](*args, **kwargs)

    def __enter__(self):
        global _tracker
        _tracker = CoverageTracker()
        raw  = getattr(self._fn, '__source__', None) or inspect.getsource(self._fn)
        src  = textwrap.dedent(raw)
        tree = InjectCoverage().visit(ast.parse(src))
        ast.increment_lineno(tree, self._fn.__code__.co_firstlineno - 1)
        ast.fix_missing_locations(tree)
        globs = self._fn.__globals__
        self._orig = globs.get(self._fn.__name__)
        globs['_tracker'] = _tracker
        exec(compile(tree, '<coverage>', 'exec'), globs)
        return self

    def __exit__(self, *args):
        if self._orig is not None:
            self._fn.__globals__[self._fn.__name__] = self._orig
        return False

    def coverage(self):
        return _tracker.covered

# We call the instrumented function via `cov(...)` so that the patched globals
# entry is used rather than the local reference to the original bytecode.

if __name__ == '__main__':
    with FunctionCoverage(bsearch) as cov:
        cov([1, 3, 5, 7, 9], 1)
    print(cov.coverage())

# Can we find a better way to display the coverage? We see how to do that next.
# 
# ## Gutter Annotations
#
# `GutterAnnotation` is the base class for all source-level annotations.
# `show` iterates the source lines and writes one marker per line.
# Covered lines (hit by at least one run) call `covered_marker`; untouched
# lines call `uncovered_marker`, which defaults to the same width as the
# covered marker so columns stay aligned.
# Subclasses override `covered_marker` (and optionally `header`) to add
# scoring columns; `F_total` (the number of failing runs) defaults to 0 and
# is only needed by scoring subclasses.

class GutterAnnotation:
    def __init__(self, source, start, hits, F_total=0):
        self.source = source
        self.start  = start
        self.hits   = hits
        self._F     = F_total

    def covered_marker(self, lineno, outcomes):
        return '|'

    def uncovered_marker(self):
        return ' ' * len(self.covered_marker(self.start, []))

    def header(self):
        return None

    def show(self):
        hdr = self.header()
        if hdr:
            print(hdr)
            print('-' * len(hdr))
        for i, line in enumerate(self.source.split('\n')):
            lineno   = self.start + i
            outcomes = self.hits.get(lineno, [])
            if outcomes: 
                m  = self.covered_marker(lineno, outcomes) 
            else:
                m = self.uncovered_marker()
            print(f'{m} {line}')

# We can now annotate the earlier `bsearch_correct` run using the `cov` we
# already collected.

if __name__ == '__main__':
    hits_one = {ln: ['pass'] for ln in set(cov.coverage())}
    GutterAnnotation(bsearch_source, bsearch_start, hits_one).show()

# ## The Oracle and Input Suite
# 
# A _reference-function oracle_ labels each run as passing when subject and
# reference agree on the output, and failing when they disagree. Searches
# that find the target return `mid` in both versions and always pass. Searches
# that fail to find the target return `lo` in the buggy version and `-1` in
# the reference, so they always fail.

if __name__ == '__main__':
    bs_passing = [
        ([1, 3, 5, 7, 9], 1),
        ([1, 3, 5, 7, 9], 3),
        ([1, 3, 5, 7, 9], 5),
        ([1, 3, 5, 7, 9], 7),
        ([1, 3, 5, 7, 9], 9),
        ([2, 4, 6, 8],    2),
        ([2, 4, 6, 8],    4),
        ([2, 4, 6, 8],    6),
        ([2, 4, 6, 8],    8),
    ]
    bs_failing = [
        ([1, 3, 5, 7, 9], 2),
        ([1, 3, 5, 7, 9], 4),
        ([1, 3, 5, 7, 9], 6),
        ([1, 3, 5, 7, 9], 8),
        ([2, 4, 6, 8],    1),
        ([2, 4, 6, 8],    3),
        ([2, 4, 6, 8],    5),
        ([2, 4, 6, 8],    7),
    ]
    for arr, t in bs_passing:
        assert bsearch(arr, t) == bsearch_correct(arr, t), f'expected pass: {arr}, {t}'
    for arr, t in bs_failing:
        assert bsearch(arr, t) != bsearch_correct(arr, t), f'expected fail: {arr}, {t}'
    print('bsearch oracle check ok')


# ## Scoring Functions
# 
# Before collecting any data, we define the four SBFL scoring functions. They
# all take $$f(\ell)$$, $$s(\ell)$$, $$F$$ (total failing runs), and $$S$$
# (total passing runs) and return a suspiciousness score in $$[0,1]$$.
# 
# **Ochiai** [^ochiai1957zoogeographic] is the geometric mean of precision
# and recall — equivalently, the cosine similarity between the failure vector
# and the line-hit vector:
# $$ \text{Ochiai}(\ell) = \frac{f(\ell)}{\sqrt{(f(\ell)+s(\ell)) \cdot F}} $$

def ochiai(fp, sp, F, S):
    denom = math.sqrt((fp + sp) * F)
    return fp / denom if denom > 0 else 0.0

# **Dice** [^dice1945measures] is the harmonic mean of precision and recall,
# identical to the $$F_1$$ score of the detector:
# $$ \text{Dice}(\ell) = \frac{2 \cdot f(\ell)}{2 \cdot f(\ell) + s(\ell) + (F - f(\ell))} $$

def dice(fp, sp, F, S):
    denom = 2 * fp + sp + (F - fp)
    return 2 * fp / denom if denom > 0 else 0.0

# **Kulczynski₂** [^kulczynski1928pflanzenassoziationen] is the arithmetic
# mean of precision and recall — the most lenient of the four because it
# weights the two components equally:
# $$ \text{Kulczynski}_2(\ell) = \frac{\text{Precision}(\ell) + \text{Recall}(\ell)}{2} $$

def kulczynski2(fp, sp, F, S):
    prec = fp / (fp + sp) if fp + sp > 0 else 0.0
    rec  = fp / F         if F > 0        else 0.0
    return (prec + rec) / 2

# **Jaccard** [^jaccard1901etude] is a monotone transform of Dice — ranking
# by Jaccard is equivalent to ranking by $$F_1$$:
# $$ \text{Jaccard}(\ell) = \frac{f(\ell)}{f(\ell) + s(\ell) + (F - f(\ell))} $$

def jaccard(fp, sp, F, S):
    denom = fp + sp + (F - fp)
    return fp / denom if denom > 0 else 0.0

# The inequality $$\text{Dice} \leq \text{Ochiai} \leq \text{Kulczynski}_2$$
# holds for every $$(f, s, F)$$ triple — harmonic $$\leq$$ geometric $$\leq$$
# arithmetic mean of precision and recall.

# Verify the four functions on a perfect predictor (fp=F, sp=0).

if __name__ == '__main__':
    assert ochiai(fp=10, sp=0, F=10, S=10) == 1.0
    assert dice(fp=10, sp=0, F=10, S=10) == 1.0
    assert kulczynski2(fp=10, sp=0, F=10, S=10) == 1.0
    assert jaccard(fp=10, sp=0, F=10, S=10) == 1.0
    j = jaccard(fp=5, sp=5, F=10, S=10)
    d = dice(fp=5, sp=5, F=10, S=10)
    assert abs(d - 2*j/(1+j)) < 1e-9
    print('scoring functions ok')

# `OchiaiAnnotation` extends `GutterAnnotation` with a per-line Ochiai score.

class OchiaiAnnotation(GutterAnnotation):
    def covered_marker(self, lineno, outcomes):
        fp    = sum(1 for o in outcomes if o == 'fail')
        sp    = sum(1 for o in outcomes if o == 'pass')
        w     = SCORE_DECIMALS + 2
        denom = math.sqrt((fp + sp) * self._F)
        score = fp / denom if denom > 0 else 0.0
        return f'{score:{w}.{SCORE_DECIMALS}f} |'

# `AllMetricsAnnotation` extends `GutterAnnotation` with columns for all four
# SBFL metrics plus the raw $$f(\ell)$$ and $$s(\ell)$$ counts.

class AllMetricsAnnotation(GutterAnnotation):
    def header(self):
        w = SCORE_DECIMALS + 2
        return (f'{"fp":>3} {"sp":>3} | '
                f'{"Och":>{w}} {"Dice":>{w}} {"Kul2":>{w}} {"Jac":>{w}} | code')

    def covered_marker(self, lineno, outcomes):
        fp  = sum(1 for o in outcomes if o == 'fail')
        sp  = sum(1 for o in outcomes if o == 'pass')
        w   = SCORE_DECIMALS + 2
        och = ochiai(fp, sp, self._F, 0)
        dic = dice(fp, sp, self._F, 0)
        kul = kulczynski2(fp, sp, self._F, 0)
        jac = jaccard(fp, sp, self._F, 0)
        return (f'{fp:>3} {sp:>3} | '
                f'{och:>{w}.{SCORE_DECIMALS}f} {dic:>{w}.{SCORE_DECIMALS}f} '
                f'{kul:>{w}.{SCORE_DECIMALS}f} {jac:>{w}.{SCORE_DECIMALS}f} |')

# `PrecRecAnnotation` extends `GutterAnnotation` with line numbers, precision,
# recall, and all four metrics — the full table used to explain metric
# disagreement.

class PrecRecAnnotation(GutterAnnotation):
    def header(self):
        w = SCORE_DECIMALS + 2
        return (f'{"ln":>4} | {"fp":>3} {"sp":>3} | '
                f'{"prec":>{w}} {"rec":>{w}} | '
                f'{"Och":>{w}} {"Dice":>{w}} {"Kul2":>{w}} {"Jac":>{w}} | code')

    def covered_marker(self, lineno, outcomes):
        fp  = sum(1 for o in outcomes if o == 'fail')
        sp  = sum(1 for o in outcomes if o == 'pass')
        w   = SCORE_DECIMALS + 2
        p   = fp / (fp + sp) if fp + sp else 0.0
        r   = fp / self._F   if self._F  else 0.0
        och = ochiai(fp, sp, self._F, 0)
        dic = dice(fp, sp, self._F, 0)
        kul = kulczynski2(fp, sp, self._F, 0)
        jac = jaccard(fp, sp, self._F, 0)
        return (f'{lineno:>4} | {fp:>3} {sp:>3} | '
                f'{p:>{w}.{SCORE_DECIMALS}f} {r:>{w}.{SCORE_DECIMALS}f} | '
                f'{och:>{w}.{SCORE_DECIMALS}f} {dic:>{w}.{SCORE_DECIMALS}f} '
                f'{kul:>{w}.{SCORE_DECIMALS}f} {jac:>{w}.{SCORE_DECIMALS}f} |')

#
# ## Spectrum-Based Fault Localization
# 
# SBFL treats each source line as a detector: "this line was executed."
# For each line $$\ell$$ we count $$f(\ell)$$ — the number of failing runs
# that touched it — and $$s(\ell)$$ — the number of passing runs that
# touched it — then score with any of the formulas above.
# 

# `collect_line_hits` uses `FunctionCoverage` to collect touched lines for
# each input. Each line is counted at most once per run — matching the
# standard SBFL coverage-hit definition.

def collect_line_hits(subject, reference, inputs, trace_fn):
    hits = {}
    for args in inputs:
        outcome = 'pass' if subject(*args) == reference(*args) else 'fail'
        with FunctionCoverage(trace_fn) as cov:
            subject.__globals__[subject.__name__](*args)
        for lineno in set(cov.coverage()):
            hits.setdefault(lineno, []).append(outcome)
    return hits

# We run bsearch on the full input suite and display each line annotated with
# its Ochiai score.

if __name__ == '__main__':
    bs_all  = bs_passing + bs_failing
    bs_hits = collect_line_hits(bsearch, bsearch_correct, bs_all, bsearch)
    bs_F    = len(bs_failing)
    OchiaiAnnotation(bsearch_source, bsearch_start, bs_hits, bs_F).show()

# The annotation tells the story at a glance. Every line in the loop body
# scores modestly — it is touched in both passing (found) and failing
# (not-found) runs. The final `return lo` scores 1.000 because it is only
# reachable when the loop exits without finding the target, which happens
# exclusively in failing runs. Its $$f(\ell)$$ equals the total failing-run
# count $$F$$, giving it perfect recall; and since no passing run ever
# reaches it, its precision is 1.0. Ochiai of a perfect detector is 1.0.
# 
# This is SBFL at its best: the buggy line lies on a code path that only
# failing runs take.
# 
# ## The Four Metrics on bsearch
# 
# SBFL offers more than one scoring formula. We defined four in the
# Definitions section. Let us compute all of them for `bsearch` and compare
# their rankings.

# Run the comparison on bsearch.

if __name__ == '__main__':
    AllMetricsAnnotation(bsearch_source, bsearch_start, bs_hits, bs_F).show()

# All four metrics agree: `return lo` is the most suspicious line by every
# measure. This is no coincidence. When a line has perfect precision
# ($$s(\ell) = 0$$) _and_ perfect recall ($$f(\ell) = F$$), all four
# similarity metrics return 1.0. When a line strictly dominates another —
# higher $$f$$ _and_ lower $$s$$ — every metric ranks it higher. Disagreement
# between metrics can only arise when one line has _higher precision_ but
# _lower recall_ than another. The bsearch example does not produce that
# situation, so the metrics are unanimous.
# 
# ## When the Metrics Disagree
# 
# Because the four similarity metrics are different means of the same
# (precision, recall) pair, they agree whenever one line strictly dominates
# another — higher $$f$$ _and_ lower $$s$$. Disagreement can only arise when
# one line has _higher precision but lower recall_ than a competing line.
# The arithmetic mean (Kulczynski₂) then favours the high-precision line more
# than the geometric mean (Ochiai) or harmonic mean (Dice), because arithmetic
# averaging is less sensitive to extreme imbalance between the two components.
# 
# We illustrate this with a small triangle classifier that has two bugs.

triangle_source = """\
def triangle(a, b, c):
    if a <= 0 or b <= 0 or c <= 0:
        return 'invalid'
    if a + b <= c or a + c <= b or b + c <= a:
        return 'invalid'
    if a == b and b == c and a % 2 == 0:
        return 'equilateral'
    if a == b or b == c:
        return 'isosceles'
    return 'scalene'"""

exec(triangle_source, globals())
triangle.__source__ = triangle_source

# **Bug A** (line 6): the equilateral check requires even side length
# (`a % 2 == 0`), so odd equilaterals like `(1,1,1)` slip through and are
# misclassified as isosceles.
# 
# **Bug B** (line 8): the isosceles check tests `a == b or b == c` but omits
# `a == c`, so triangles where only `a == c` holds — such as `(3,4,3)` — are
# misclassified as scalene.
# 
# The reference is the correct classifier.

def triangle_correct(a, b, c):
    if a <= 0 or b <= 0 or c <= 0:
        return 'invalid'
    if a + b <= c or a + c <= b or b + c <= a:
        return 'invalid'
    if a == b == c:
        return 'equilateral'
    if a == b or b == c or a == c:
        return 'isosceles'
    return 'scalene'

# We construct a test suite that exercises both bugs and deliberately biases
# coverage so that the two key lines end up with different precision/recall
# profiles. Many `a==b` and `b==c` passing tests inflate $$s(\ell)$$ on
# line 8 without affecting line 10, giving line 8 low precision but high
# recall. A single scalene passing test keeps $$s(\ell)$$ on line 10 at 1.

def collect_triangle_hits():
    bugA_failing = [
        (1,1,1),(3,3,3),(5,5,5),(7,7,7),(9,9,9),(11,11,11),(13,13,13),
    ]
    bugB_failing = [(3,4,3),(2,3,2),(4,5,4)]
    pass_ab      = [(n, n, n+1) for n in range(2, 20)]
    pass_bc      = [(n+1, n, n) for n in range(2, 20)]
    pass_even_eq = [(2,2,2),(4,4,4),(6,6,6)]
    pass_scalene  = [(3,4,5)]

    inputs = ([(a, 'fail') for a in bugA_failing + bugB_failing] +
              [(a, 'pass') for a in pass_ab + pass_bc + pass_even_eq + pass_scalene])

    hits = {}
    for args, _ in inputs:
        outcome = 'pass' if triangle(*args) == triangle_correct(*args) else 'fail'
        with FunctionCoverage(triangle) as cov:
            triangle.__globals__[triangle.__name__](*args)
        for ln in set(cov.coverage()):
            hits.setdefault(ln, []).append(outcome)
    F_total = sum(1 for _, expected in inputs if expected == 'fail')
    return hits, F_total

# Compute scores for all four metrics on every line of the triangle function.

if __name__ == '__main__':
    tri_hits, tri_F = collect_triangle_hits()
    tri_start = triangle.__code__.co_firstlineno
    print(f'F_total = {tri_F} failing runs\n')
    PrecRecAnnotation(triangle_source, tri_start, tri_hits, tri_F).show()

# The key contrast is between lines 8 and 10.
# 
# **Line 8** (`if a == b or b == c`) is reached by _all_ ten failing runs
# (both bug A and bug B pass through it) and also by the many `a==b` and
# `b==c` passing tests.  It has perfect recall but low precision.
# 
# **Line 10** (`return 'scalene'`) is reached only by the three bug-B failing
# runs (bug-A runs return early at line 9) and the single scalene passing
# test.  It has high precision but low recall.
# 
# | Line | f(ℓ) | s(ℓ) | Precision | Recall |
# |---|---|---|---|---|
# | 8  `if a == b or b == c` | 10 | 37 | 0.21 | 1.00 |
# | 10 `return 'scalene'`    |  3 |  1 | 0.75 | 0.30 |
# 
# | Metric | Line 8 | Line 10 | Winner |
# |---|---|---|---|
# | Ochiai  (geometric mean)      | 0.4613 | **0.4743** | Line 10 |
# | Dice    (harmonic mean)       | 0.3509 | **0.4286** | Line 10 |
# | Kulczynski₂ (arithmetic mean) | **0.6064** | 0.5250 | Line 8 |
# | Jaccard (monotone of Dice)    | 0.2128 | **0.2727** | Line 10 |
# 
# Ochiai, Dice, and Jaccard rank `return 'scalene'` first — the geometric and
# harmonic means penalise line 8's severe precision/recall imbalance enough
# that line 10's high precision wins out.  Kulczynski₂ ranks
# `if a == b or b == c` first — the arithmetic mean weights precision and
# recall equally, so line 8's perfect recall (1.0) overcomes its poor
# precision (0.21) relative to line 10's 0.75/0.30 split.
# 
# Both answers are useful to a developer: line 10 is _where_ bug B manifests;
# line 8 is _what condition_ should have caught it.  In practice, empirical
# studies (e.g., Abreu et al. 2007 [^abreu2007accuracy]) find Ochiai and Dice
# tend to outperform Kulczynski₂ on large benchmarks, likely because high
# recall — not missing the fault site — matters more than high precision when
# a developer is willing to inspect a few extra lines.
# 
# ## Conclusion
# 
# We have built a spectrum-based fault localizer from first principles using
# only the Python standard library. The core insight is the counting table:
# treat "line $$\ell$$ executed" as a detector and "run fails" as the positive
# class, then apply a similarity metric to the resulting precision and recall.
# 
# The four metrics are all means of the same (precision, recall) pair —
# harmonic (Dice), geometric (Ochiai), and arithmetic (Kulczynski₂) — so they
# agree when one line dominates another. They diverge only when the
# precision/recall trade-off differs between candidates, as the triangle
# example demonstrates. Empirical evidence favours Ochiai as a practical
# default.
# 
# The fundamental limit of SBFL is that its signal is the _coverage bit_: hit
# or not hit. When the bug lies on a line that both passing and failing runs
# execute, coverage carries no discriminating information. That limitation
# motivates the complementary technique of predicate-based analysis, explored
# in the [companion post on Predicate-Based Statistical Fault Localization](/post/2026/05/17/predicate-based-fault-localization/).

# ## References

# [^jones2002visualization]: James A. Jones, Mary Jean Harrold, and John Stasko. "Visualization of test information to assist fault localization." ICSE 2002.

# [^ochiai1957zoogeographic]: Akira Ochiai. "Zoogeographic studies on the soleoid fishes found in Japan and its neighbouring regions." Bulletin of the Japanese Society of Scientific Fisheries, 22(9), 1957.

# [^abreu2007accuracy]: Rui Abreu, Peter Zoeteweij, and Arjan J. C. van Gemund. "On the accuracy of spectrum-based fault localization." TAICPART 2007.

# [^dice1945measures]: Lee R. Dice. "Measures of the amount of ecologic association between species." Ecology, 26(3), 1945.

# [^kulczynski1928pflanzenassoziationen]: Stanisław Kulczyński. "Pflanzenassoziationen der Pieninen." Bulletin International de l'Académie Polonaise des Sciences et des Lettres, Classe des Sciences Mathématiques et Naturelles, Série B, 1928.

# [^jaccard1901etude]: Paul Jaccard. "Étude comparative de la distribution florale dans une portion des Alpes et des Jura." Bulletin de la Société Vaudoise des Sciences Naturelles, 37, 1901.
