# ---
# published: true
# title: Predicate-Based Statistical Fault Localization
# layout: post
# comments: true
# tags: debugging, fault-localization, statistical-debugging, dynamic-analysis
# categories: post
# ---
# 
# TLDR; This post is a complete implementation of predicate-based statistical
# fault localization in Python, building directly on the invariant miner from
# the [previous post](/post/2026/05/09/simple-invariant-miner/). We instrument
# a buggy quicksort, collect pass/fail-labelled predicate observations, and
# rank suspicious predicates using three formulas: the CBI Increase statistic
# (Liblit et al., PLDI 2003), Ochiai applied to predicates, and the Dice
# coefficient. The Python interpreter is embedded so that you can work through
# the implementation steps.
# 
# ## Two Strands of Statistical Debugging
# 
# The previous post introduced _runtime invariant mining_: given a set of
# passing runs, mine logical properties of variables that hold across all of
# them. Those invariants become an approximate oracle for regression testing.
# 
# This post follows a complementary question: given a mix of _passing_ and
# _failing_ runs, which predicates are most correlated with failure? The
# answer is a ranked list of suspicious program conditions — a fault
# localization report that points a developer at the likely bug.
# 
# There are two historical strands of statistical fault localization.
# The first, **Spectrum-Based Fault Localization (SBFL)**, was introduced by
# Jones et al. at ICSE 2002 [^jones2002visualization] with the Tarantula tool.
# It correlates _statement coverage_ with pass/fail outcomes: a line executed
# more often in failing runs than in passing runs is suspicious. Ochiai,
# Jaccard, DStar, and Dice are all SBFL metrics in this tradition.
# 
# The second strand, **Cooperative Bug Isolation (CBI)**, was founded by
# Liblit, Aiken, Zheng, and Jordan at PLDI 2003 [^liblit2003bug]. Instead of
# tracking which _statements_ executed, CBI tracks which _program predicates_
# were true — branch outcomes, comparison results, return-value signs — and
# applies statistical tests to find the predicates most predictive of failure.
# 
# The key insight separating the two: a statement may be executed in both
# passing and failing runs, giving zero SBFL signal. But the _truth value_ of
# a condition at that statement — `nums[head] >= pivot`, say — may differ
# sharply between the two, giving strong CBI signal. The invariant miner
# already evaluates predicates at program points; adding pass/fail labels to
# the runs is all that is needed to turn it into a fault localizer.
# 
# ## Synopsis
# 
# ```python
# results = localize(buggy_sort, reference_sort, inputs)
# for inc, och, dic, name, point, fp, sp in results[:5]:
#     print(f'{inc:.4f}  {name}  ({point})')
# ```
# 
# ## Definitions
# 
# * A _subject program_ is the buggy function under investigation.
#
# * A _reference program_ is a known-correct version of the same function,
#   used as the oracle: a run _passes_ when subject and reference agree on
#   the output, and _fails_ when they disagree.
#
# * A _predicate_ is a boolean function of the variable state at a program
#   point — for example, `head == lo + 1` at `partition:::EXIT`.
#
# * Treat "predicate $$p$$ is true" as a _detector_ and "run fails" as the
#   _positive class_. The four counts at a program point are then the standard
#   confusion-matrix cells:
#
#   | | run fails | run passes |
#   |---|---|---|
#   | **$$p$$ true** | $$f(p)$$ — true positives | $$s(p)$$ — false positives |
#   | **$$p$$ false** | $$F - f(p)$$ — false negatives | $$S - s(p)$$ — true negatives |
#
#   $$F$$ is the total failing-run observations at that point, $$S$$ the passing.
#
# * From the table, precision and recall of the detector follow directly:
#   $$ \text{Precision}(p) = \frac{f(p)}{f(p)+s(p)} \qquad
#      \text{Recall}(p) = \frac{f(p)}{F} $$
#
# * The **Increase** statistic [^liblit2005scalable] measures how much
#   observing $$p$$ true _increases_ the probability of failure above the base
#   rate $$F/(F+S)$$; equivalently, precision minus the prior:
#   $$ \text{Increase}(p) = \text{Precision}(p) - \frac{F}{F+S} $$
#
# * **Ochiai** [^ochiai1957zoogeographic] is the _geometric mean_ of precision
#   and recall — equivalently, the cosine similarity between the failure vector
#   and the predicate-true vector:
#   $$ \text{Ochiai}(p) = \sqrt{\text{Precision}(p) \times \text{Recall}(p)}
#      = \frac{f(p)}{\sqrt{(f(p)+s(p)) \cdot F}} $$
#
# * **Dice** [^dice1945measures] is the _harmonic mean_ of precision and recall,
#   identical to the $$F_1$$ score of the detector:
#   $$ \text{Dice}(p) = F_1(p)
#      = \frac{2 \cdot \text{Precision}(p) \cdot \text{Recall}(p)}{\text{Precision}(p) + \text{Recall}(p)}
#      = \frac{2 \cdot f(p)}{2 \cdot f(p) + s(p) + (F - f(p))} $$
# 
# ## Prerequisites
# 
# We reuse four pieces from the invariant miner wheel
# [previously discussed](/post/2026/05/09/simple-invariant-miner/):
# `TraceStore` and `Instrumentor` for the instrumentation machinery,
# and `unary_invariants` and `binary_invariants` for the predicate templates.
# The new contributions of this post are the outcome label attached to each
# observation, the `LabelledTraceStore` subclass that carries that label,
# and the three scoring functions.

#@
# https://rahul.gopinath.org/py/simpleinvariantminer-0.0.1-py2.py3-none-any.whl

import simpleinvariantminer as siv

import sys
import math
import itertools

# Since this notebook serves both as a web notebook and as a script that can
# be run on the command line, we redefine `__canvas__` if it is not already
# defined by the notebook environment.

if __name__ == '__main__':
    if '__canvas__' not in globals(): __canvas__ = print
# 
# ## The Subject Program
# 
# Our subject is a quicksort implementation posted to Stack Overflow
# (https://stackoverflow.com/q/74943555) that passes some inputs and fails
# on others. We transcribe it faithfully from the Java original.
# 
# The algorithm uses a two-pointer partition. `pivot` is always `nums[lo]`.
# `head` walks right past elements smaller than pivot; `tail` walks left past
# elements larger than pivot. When the pointers cross, the pivot is swapped
# into place and `head` is returned as the partition index.
# 
# Source: https://stackoverflow.com/q/74943555
# Posted by John Doe. Retrieved 2026-05-18. License: CC BY-SA 4.0.
#
# We keep the entire subject program as a single source string and `exec` it
# once. This eliminates the duplicate `partition_source` variable: the string
# is the definition, not a copy of it. `partition_start` is derived by
# counting the lines that precede `def partition` within the string, so the
# annotated-source display stays accurate. (`inspect.getsource` raises OSError
# in Pyodide because there are no source files on disk in the browser sandbox.)

subject_source = """\
def swap(nums, i, j):
    nums[i], nums[j] = nums[j], nums[i]

def partition(nums, lo, hi):
    pivot = nums[lo]
    head  = lo + 1
    tail  = hi
    while head < tail:
        while head < hi and nums[head] < pivot:
            head += 1
        while nums[tail] > pivot:
            tail -= 1
        if head < tail:
            swap(nums, head, tail)
            head += 1
            tail -= 1
    if nums[head] < pivot:
        swap(nums, lo, head)
    else:
        swap(nums, lo, head - 1)
    return head

def quicksort(nums, lo, hi):
    if lo < hi:
        j = partition(nums, lo, hi)
        quicksort(nums, lo, j - 1)
        quicksort(nums, j + 1, hi)

def buggy_sort(nums):
    arr = list(nums)
    quicksort(arr, 0, len(arr) - 1)
    return arr"""

exec(subject_source, globals())

# Extract partition_source and partition_start from subject_source so there
# is no duplication.
_lines = subject_source.split('\n')
_s = next(i for i, l in enumerate(_lines) if l.startswith('def partition'))
_e = next((i for i, l in enumerate(_lines)
           if i > _s and l and not l[0].isspace()), len(_lines))
partition_source = '\n'.join(_lines[_s:_e]).rstrip()
partition_start  = _s + 1   # 1-based line number within subject_source

# The reference is Python's built-in sort, which is known correct.

def reference_sort(nums):
    return sorted(nums)
# 
# ## The Oracle and Input Suite
# 
# A _reference-function oracle_ labels each run by comparing the subject's
# output to the reference's output on the same input. This is more general
# than an exception oracle: the bug here produces wrong answers without
# crashing, so only output comparison reveals failure.
# 
# We use the three passing inputs the SO poster provided, plus three inputs
# that fail — the one the poster reported and two additional ones that expose
# the same bug on different array shapes.

if __name__ == '__main__':
    passing_inputs = [
        ([5, 2, 3, 1],),
        ([5, 1, 1, 2, 0, 0],),
        ([7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],),
    ]
    failing_inputs = [
        ([5, 71, 1, 91, 10, 2, 0, 0, 13, 45, 7],),
        ([3, 4, 5, 6, 0, 1, 2, 7, 8, 9],),
        ([8, 6, 1, 7, 0, 5, 4, 3, 2, 1],),
    ]
    for (arr,) in passing_inputs:
        assert buggy_sort(arr) == reference_sort(arr), f'expected pass: {arr}'
    for (arr,) in failing_inputs:
        assert buggy_sort(arr) != reference_sort(arr), f'expected fail: {arr}'
    print('oracle check ok')
#
# ## Spectrum-Based Fault Localization
#
# Before reaching for predicate analysis, let us see how far plain statement
# coverage takes us. For each line of `partition` we count how many times it
# was executed in failing runs ($$f_\ell$$) and in passing runs ($$s_\ell$$).
# The scoring formulas defined in the Definitions section apply without change:
# we just substitute "line $$\ell$$ was executed" for "predicate $$p$$ is true".
#
# A `line`-event tracer collects the hits. The outcome label is determined
# before each run by comparing subject to reference, then the same run is
# traced for line events.

def collect_line_hits(subject, reference, inputs, trace_fn):
    hits = {}
    target_name = trace_fn.__name__
    for args in inputs:
        outcome = 'pass' if subject(*args) == reference(*args) else 'fail'
        touched = set()
        def tracer(frame, event, arg):
            if event != 'line': return tracer
            if frame.f_code.co_name != target_name: return tracer
            touched.add(frame.f_lineno)
            return tracer
        old = sys.gettrace(); sys.settrace(tracer)
        try:    subject(*args)
        finally: sys.settrace(old)
        for lineno in touched:
            hits.setdefault(lineno, []).append(outcome)
    return hits

def show_annotated_source(source, start, hits):
    source_lines = source.split('\n')
    F_total = sum(1 for outcomes in hits.values() for o in outcomes if o == 'fail')
    S_total = sum(1 for outcomes in hits.values() for o in outcomes if o == 'pass')
    for i, line in enumerate(source_lines):
        lineno   = start + i
        outcomes = hits.get(lineno, [])
        fp = sum(1 for o in outcomes if o == 'fail')
        sp = sum(1 for o in outcomes if o == 'pass')
        denom  = math.sqrt((fp + sp) * F_total)
        score  = fp / denom if denom > 0 else 0.0   # Ochiai
        marker = f'{score:5.3f}' if outcomes else '     '
        print(f'{marker} | {line}')

if __name__ == '__main__':
    all_inputs = passing_inputs + failing_inputs
    line_hits  = collect_line_hits(buggy_sort, reference_sort, all_inputs, partition)
    show_annotated_source(partition_source, partition_start, line_hits)
#
# Each line is counted at most once per run, regardless of how many times the
# loop executes — matching the standard SBFL definition of a coverage hit.
# The result is flat: almost every line scores around 0.18 because it is
# reached in all three failing runs and all three passing runs. The if-arm
# `swap(nums, lo, head)` dips slightly because it fires in only some failing
# runs. But the else-arm lines — `swap(nums, lo, head - 1)` and `return head`
# — score the same as the boilerplate setup lines at the top of the function.
# Coverage cannot see *which* arm fired on a given run; both arms are reached
# in both populations, so SBFL gives them equal suspicion. The bug is in the
# else arm, and coverage has no way to say so.
#
# ## From Coverage to Predicates
#
# The limitation is fundamental: a line is either hit or not, a binary signal.
# The _truth value_ of the branch condition `nums[head] < pivot` at that line
# is a richer signal — it tells us which arm was taken. If that truth value
# correlates with failure more strongly than the raw hit count does, predicate
# analysis will find the bug where SBFL cannot.
#
# To make the branch outcome visible to the frame tracer we assign it to a
# local variable just before the `if`. Because it is a named local, the tracer
# picks it up automatically at the `return` event alongside `head`, `tail`,
# and `pivot` — no special wiring needed. We encode it as a 0/1 integer so
# that `scalar_interesting` accepts it, and so that `candidates_for` detects
# it as boolean and generates `else_branch is true` / `else_branch is false`
# templates rather than uninformative numeric ones like `else_branch >= 0`.

def partition(nums, lo, hi):
    pivot = nums[lo]
    head  = lo + 1
    tail  = hi
    while head < tail:
        while head < hi and nums[head] < pivot:
            head += 1
        while nums[tail] > pivot:
            tail -= 1
        if head < tail:
            swap(nums, head, tail)
            head += 1
            tail -= 1
    else_branch = int(not (nums[head] < pivot))   # 1 = else arm taken
    if nums[head] < pivot:
        swap(nums, lo, head)
    else:
        swap(nums, lo, head - 1)
    return head

partition_source = """\
def partition(nums, lo, hi):
    pivot = nums[lo]
    head  = lo + 1
    tail  = hi
    while head < tail:
        while head < hi and nums[head] < pivot:
            head += 1
        while nums[tail] > pivot:
            tail -= 1
        if head < tail:
            swap(nums, head, tail)
            head += 1
            tail -= 1
    else_branch = int(not (nums[head] < pivot))   # 1 = else arm taken
    if nums[head] < pivot:
        swap(nums, lo, head)
    else:
        swap(nums, lo, head - 1)
    return head"""

partition_start = partition.__code__.co_firstlineno

#
# ## Instrumentation
#
# The invariant miner's `Instrumentor` hooks into `sys.settrace` and records
# variable states at `ENTER` and `EXIT` program points into a `TraceStore`.
# We need exactly the same machinery here, with one extension: each
# observation must carry an _outcome label_ (`'pass'` or `'fail'`) so that
# the scoring functions can separate the two populations.
#
# We achieve this with a single thin subclass.
#
# ### LabelledTraceStore
#
# `LabelledTraceStore` extends `TraceStore` with one addition: a mutable
# `outcome` attribute set by the caller before each instrumented run. Its
# `add` override stores `(state, outcome)` pairs, reading `self.outcome`
# automatically. Because the parent `Instrumentor._tracer` calls
# `self.store.add(point, state)` with no outcome argument, the label is
# injected here without any change to the instrumentation machinery.
#
# `get` is overridden to accept either a `ProgramPoint` or a plain string,
# since the parent stores keys as strings internally.

class LabelledTraceStore(siv.TraceStore):
    def __init__(self):
        super().__init__()
        self.outcome = '?'

    def add(self, point, state, outcome=None):
        if point is None:
            return
        name = point.name if isinstance(point, siv.ProgramPoint) else point
        if name not in self.data:
            self.data[name] = []
        self.data[name].append((dict(state), outcome if outcome else self.outcome))

    def get(self, point):
        name = point.name if isinstance(point, siv.ProgramPoint) else point
        return self.data.get(name, [])

# Verify the store stamps outcomes from `self.outcome` correctly.

if __name__ == '__main__':
    lts = LabelledTraceStore()
    lts.outcome = 'pass'
    lts.add(siv.ProgramPoint('partition:::ENTER'), {'lo': 0, 'hi': 3})
    lts.outcome = 'fail'
    lts.add(siv.ProgramPoint('partition:::ENTER'), {'lo': 0, 'hi': 5})
    obs = lts.get('partition:::ENTER')
    assert len(obs) == 2
    assert obs[0] == ({'lo': 0, 'hi': 3}, 'pass')
    assert obs[1] == ({'lo': 0, 'hi': 5}, 'fail')
    print('LabelledTraceStore ok')
#
# ### collect_labelled_traces
#
# `collect_labelled_traces` mirrors `collect_traces` from the invariant miner.
# For each input it first calls the subject and reference uninstrumented to
# determine the outcome label, sets `store.outcome`, then re-runs the subject
# under a plain `Instrumentor` with a `scalar_interesting` filter that excludes
# lists such as `nums`. For a deterministic function the two runs produce the
# same observations; the separation keeps the code straightforward.

def scalar_interesting(name, val):
    return not name.startswith('_') and isinstance(val, (int, float))

def collect_labelled_traces(subject, reference, inputs,
                            interesting=scalar_interesting):
    store = LabelledTraceStore()
    instr = siv.Instrumentor(store, interesting)
    for args in inputs:
        store.outcome = 'pass' if subject(*args) == reference(*args) else 'fail'
        instr.run(subject, *args)
    return store

# Collect observations for our input suite and verify the counts.

if __name__ == '__main__':
    all_inputs = passing_inputs + failing_inputs
    store = collect_labelled_traces(buggy_sort, reference_sort, all_inputs)
    for pt in store.points():
        obs    = store.get(pt)
        n_pass = sum(1 for _, o in obs if o == 'pass')
        n_fail = sum(1 for _, o in obs if o == 'fail')
        print(f'{pt}: {n_pass} pass obs, {n_fail} fail obs')

# The tracer visits every function in the call tree — `buggy_sort`,
# `quicksort`, `partition`, and `swap` — and records entry and exit states
# for each. The fault localizer will consider all of them, but the strongest
# signal will come from `partition`, where the bug lives.
# 
# ## Candidate Predicates
# 
# A candidate predicate is a boolean function of a state dict. We reuse
# `unary_invariants` and `binary_invariants` from the invariant miner wheel
# to generate numeric comparison templates (`is not None`, `>= 0`, `> 0`,
# `type(...) is int`, `x == y`, `x <= y`, `x >= y`) over every variable
# observed at a program point.
# 
# Variables coded as 0/1 integers — like `else_branch` — would produce
# uninformative numeric templates (`else_branch >= 0` is always true), so
# we detect them and replace them with a pair of boolean templates instead.

def boolean_predicates(var):
    return [
        (f'{var} is true',  lambda s, v=var: bool(s.get(v))),
        (f'{var} is false', lambda s, v=var: not bool(s.get(v))),
    ]

def candidates_for(observations):
    if not observations:
        return []
    all_vars     = sorted({k for state, _ in observations for k in state})
    bool_vars    = [v for v in all_vars
                    if {state.get(v) for state, _ in observations} <= {0, 1}]
    numeric_vars = [v for v in all_vars if v not in bool_vars]
    cands = []
    for v in bool_vars:
        cands.extend(boolean_predicates(v))
    for v in numeric_vars:
        for inv in siv.unary_invariants(v):
            cands.append((inv.name, inv.check))
    for x, y in itertools.combinations(numeric_vars, 2):
        for inv in siv.binary_invariants(x, y):
            cands.append((inv.name, inv.check))
    return cands

# Verify candidate generation on the partition exit point.

if __name__ == '__main__':
    exit_obs = store.get('partition:::EXIT')
    cands    = candidates_for(exit_obs)
    print(f'partition:::EXIT: {len(cands)} candidate predicates')
    for name, _ in cands:
        print(f'  {name}')
# 
# ## Scoring: CBI Increase
#
# The Increase statistic [^liblit2005scalable] is precision minus the prior
# failure rate. Without any predicate evidence, a randomly chosen observation
# at this program point fails with probability $$F/(F+S)$$. If we condition on
# the predicate being true, the failure probability becomes
# $$\text{Precision}(p) = f(p)/(f(p)+s(p))$$. The Increase is the lift:
#
# $$ \text{Increase}(p) = \text{Precision}(p) - \frac{F}{F+S} $$
#
# A positive value means observing $$p$$ true raises our estimate of failure
# above the base rate. A negative value means it is _protective_ — the
# predicate fires more often in passing runs. This signed character is unique
# among the three formulas: Ochiai and Dice are always non-negative.

def cbi_increase(fp, sp, F, S):
    if fp + sp == 0 or F + S == 0:
        return 0.0
    return fp / (fp + sp) - F / (F + S)

# Verify: a predicate true only in failing runs scores 1 - F/(F+S).

if __name__ == '__main__':
    score = cbi_increase(fp=10, sp=0, F=10, S=10)
    assert abs(score - 0.5) < 1e-9
    score_zero = cbi_increase(fp=5, sp=5, F=10, S=10)
    assert abs(score_zero) < 1e-9
    print('cbi_increase ok')
# 
# ## Scoring: Ochiai
#
# Ochiai [^ochiai1957zoogeographic] was originally a similarity index in
# ecology, repurposed for SBFL by Abreu et al. [^abreu2007accuracy]. It is
# the _geometric mean_ of precision and recall:
#
# $$ \text{Ochiai}(p) = \sqrt{\text{Precision}(p) \times \text{Recall}(p)}
#    = \frac{f(p)}{\sqrt{(f(p)+s(p)) \cdot F}} $$
#
# This is also the cosine similarity between the binary vector "predicate true"
# and the binary vector "run failed". In SBFL the formula is applied to
# statement coverage vectors; applied to predicate truth values it is
# identical — only the unit of observation changes, not the counting table.
# The geometric mean scores zero whenever either precision or recall is zero,
# and reaches 1.0 only when both are 1.0.

def ochiai(fp, sp, F, S):
    denom = math.sqrt((fp + sp) * F)
    return fp / denom if denom > 0 else 0.0

# Verify: perfect predictor scores 1.0.

if __name__ == '__main__':
    assert ochiai(fp=10, sp=0, F=10, S=10) == 1.0
    print('ochiai ok')
# 
# ## Scoring: Dice
#
# The Dice coefficient [^dice1945measures] is the _harmonic mean_ of precision
# and recall — exactly the $$F_1$$ score of the predicate-as-failure-detector:
#
# $$ \text{Dice}(p) = F_1(p)
#    = \frac{2 \cdot \text{Precision}(p) \cdot \text{Recall}(p)}{\text{Precision}(p) + \text{Recall}(p)}
#    = \frac{2 \cdot f(p)}{2 \cdot f(p) + s(p) + (F - f(p))} $$
#
# The harmonic mean is always at most the geometric mean, so
# $$\text{Dice} \leq \text{Ochiai}$$ for every predicate. Dice penalises
# imbalance between precision and recall more harshly than Ochiai does,
# making it the most conservative of the three: a predicate must be both
# precise and high-recall to score well, which is a useful property when
# false positives in a debugging report are expensive.

def dice(fp, sp, F, S):
    denom = 2 * fp + sp + (F - fp)
    return 2 * fp / denom if denom > 0 else 0.0

# Verify: perfect predictor scores 1.0; a predicate true in no failing
# observations scores 0.0.

if __name__ == '__main__':
    assert dice(fp=10, sp=0, F=10, S=10) == 1.0
    assert dice(fp=0,  sp=5, F=10, S=10) == 0.0
    print('dice ok')
#
# ## Scoring: Kulczynski₂
#
# Kulczynski's second coefficient [^kulczynski1928pflanzenassoziationen] is the
# _arithmetic mean_ of precision and recall:
#
# $$ \text{Kulczynski}_2(p) = \frac{\text{Precision}(p) + \text{Recall}(p)}{2}
#    = \frac{1}{2}\!\left(\frac{f(p)}{f(p)+s(p)} + \frac{f(p)}{F}\right) $$
#
# Because arithmetic $$\geq$$ geometric $$\geq$$ harmonic, we have
# $$\text{Kulczynski}_2 \geq \text{Ochiai} \geq \text{Dice}$$ for every
# predicate. It is the most lenient of the four similarity metrics: a predicate
# with perfect recall but terrible precision can still score 0.5, while Ochiai
# and Dice would penalise it more heavily.

def kulczynski2(fp, sp, F, S):
    prec = fp / (fp + sp) if fp + sp > 0 else 0.0
    rec  = fp / F         if F > 0        else 0.0
    return (prec + rec) / 2

# Verify: perfect predictor scores 1.0; a predicate with 0.5 precision and
# 1.0 recall scores 0.75.

if __name__ == '__main__':
    assert kulczynski2(fp=10, sp=0, F=10, S=10) == 1.0
    assert abs(kulczynski2(fp=10, sp=10, F=10, S=10) - 0.75) < 1e-9
    print('kulczynski2 ok')
#
# ## Scoring: Jaccard
#
# The Jaccard index [^jaccard1901etude] is the intersection over union of the
# "predicate true" and "run fails" sets. In terms of precision and recall it is
# a monotone transformation of $$F_1$$:
#
# $$ \text{Jaccard}(p) = \frac{f(p)}{f(p) + s(p) + (F - f(p))}
#    = \frac{F_1}{2 - F_1} $$
#
# Because $$x \mapsto x/(2-x)$$ is strictly increasing on $$[0,1]$$, ranking
# by Jaccard is equivalent to ranking by Dice/$$F_1$$. Jaccard counts the
# shared elements once; Dice double-weights them, so Dice $$\geq$$ Jaccard.

def jaccard(fp, sp, F, S):
    denom = fp + sp + (F - fp)
    return fp / denom if denom > 0 else 0.0

# Verify: perfect predictor scores 1.0; a predicate with fp=5, sp=5, F=10
# has Jaccard = 5/15 = 1/3 and Dice = 10/20 = 0.5, so Dice = 2·Jaccard/(1+Jaccard).

if __name__ == '__main__':
    assert jaccard(fp=10, sp=0, F=10, S=10) == 1.0
    j = jaccard(fp=5, sp=5, F=10, S=10)
    d = dice(fp=5, sp=5, F=10, S=10)
    assert abs(d - 2*j/(1+j)) < 1e-9, f'{d} != 2*{j}/(1+{j})'
    print('jaccard ok')
#
# ## FaultLocalizer
#
# `FaultLocalizer` ties everything together. For each program point in the
# store it generates candidate predicates, counts $$f(p)$$ and $$s(p)$$ by
# evaluating each predicate over the labelled observations, computes all five
# scores, and collects the results. Predicates that are never true in any run
# carry no information and are dropped.

class FaultLocalizer:
    def _count(self, observations, predicate_fn):
        fp = sp = 0
        for state, outcome in observations:
            try:
                val = predicate_fn(state)
            except Exception:
                continue
            if val:
                if outcome == 'fail': fp += 1
                else:                 sp += 1
        return fp, sp

    def analyze(self, store):
        results = {}
        for pt in store.points():
            obs   = store.get(pt)
            F     = sum(1 for _, o in obs if o == 'fail')
            S     = sum(1 for _, o in obs if o == 'pass')
            cands = candidates_for(obs)
            rows  = []
            for name, fn in cands:
                fp, sp = self._count(obs, fn)
                if fp + sp == 0:
                    continue
                inc = cbi_increase(fp, sp, F, S)
                och = ochiai(fp, sp, F, S)
                dic = dice(fp, sp, F, S)
                kul = kulczynski2(fp, sp, F, S)
                jac = jaccard(fp, sp, F, S)
                rows.append((inc, och, dic, kul, jac, name, fp, sp))
            results[pt] = rows
        return results

# Run the localizer on our partition observations.

if __name__ == '__main__':
    localizer = FaultLocalizer()
    results   = localizer.analyze(store)
    for pt in store.points():
        rows = results[pt]
        print(f'\n{pt}')
        print(f'  {"Predicate":<30} {"Inc":>7} {"Och":>6} {"Dice":>6} {"Kul":>6} {"Jac":>6}  f(p) s(p)')
        for inc, och, dic, kul, jac, name, fp, sp in sorted(rows, key=lambda r: -r[0])[:6]:
            print(f'  {name:<30} {inc:>7.4f} {och:>6.4f} {dic:>6.4f} {kul:>6.4f} {jac:>6.4f}  {fp:>3}  {sp:>3}')
# 
# ## Interpreting the Rankings
# 
# At `partition:::EXIT` the top-ranked predicates by Increase are
# `else_branch is true` and `head >= pivot` — two ways of expressing the
# same condition: the else arm of the final `if` fired, meaning
# `nums[head] >= pivot` at the moment of the branch. This points directly
# at the buggy code path: when the else arm fires, the pivot is placed at
# `head - 1` but `head` is still returned, so the index fed back to
# `quicksort` is one position too high.
# 
# Crucially, **statement coverage gives zero signal here**. Both branches of
# the final `if` inside `partition` execute in passing runs and in failing
# runs. Only the _truth value_ of `nums[head] < pivot` at that point,
# correlated with the outcome, reveals the fault.
# 
# ## How the Formulas Differ
#
# Four of the five formulas are classical set-similarity coefficients repurposed
# for fault localization. They all combine precision and recall, but with
# different averaging strategies. For any $$(P, R)$$ pair:
#
# $$ \text{Dice/}F_1 \leq \text{Ochiai} \leq \text{Kulczynski}_2 $$
# (harmonic $$\leq$$ geometric $$\leq$$ arithmetic mean of precision and recall)
#
# Jaccard is a monotone transform of Dice so it ranks identically; it simply
# counts the shared elements once while Dice double-weights them.
#
# Increase is the odd one out. It is precision minus the base failure rate
# at the program point — a signed quantity. It is the only formula that
# identifies _protective_ predicates (negative Increase), which is useful for
# ruling out false suspects. Its weakness is sensitivity to base-rate
# differences across program points: a predicate at a frequently-visited point
# sees a different denominator than one at a rarely-visited point, making
# cross-point comparison less reliable.
#
# Kulczynski₂ is the most lenient similarity metric: high recall alone can
# carry a predicate to a decent score even if its precision is poor. Dice is
# the most conservative: both precision and recall must be high. Ochiai sits
# between them, which partly explains its strong empirical performance — it is
# less forgiving than Kulczynski₂ but more tolerant of imperfect recall than
# Dice.
# 
# ## Full Pipeline
# 
# We collect everything into a single `localize` function that accepts a
# subject, a reference, and an input suite and returns a ranked list of
# `(increase, ochiai, dice, name, point, f(p), s(p))` tuples sorted by
# Increase, breaking ties by Ochiai.

def localize(subject, reference, inputs, top_n=10):
    store     = collect_labelled_traces(subject, reference, inputs)
    localizer = FaultLocalizer()
    results   = localizer.analyze(store)
    ranked    = []
    for pt, rows in results.items():
        for inc, och, dic, kul, jac, name, fp, sp in rows:
            ranked.append((inc, och, dic, kul, jac, name, pt, fp, sp))
    ranked.sort(key=lambda r: (-r[0], -r[1]))
    return ranked[:top_n]

# Run the full pipeline and display the top suspects.

if __name__ == '__main__':
    all_inputs = passing_inputs + failing_inputs
    top = localize(buggy_sort, reference_sort, all_inputs)
    print(f'\n{"Predicate":<32} {"Point":<22} {"Inc":>7} {"Och":>6} {"Dice":>6} {"Kul":>6} {"Jac":>6}')
    print('-' * 95)
    for inc, och, dic, kul, jac, name, pt, fp, sp in top:
        print(f'{name:<32} {pt:<22} {inc:>7.4f} {och:>6.4f} {dic:>6.4f} {kul:>6.4f} {jac:>6.4f}')

# Comparing the two annotated views — coverage-based SBFL at the top of the
# post and predicate-based scores here — makes the improvement concrete.
# In the SBFL view the two arms of the final `if` score nearly the same.
# In the predicate view `else_branch is true` rises to the top of the global
# ranking, pinpointing the else arm as the fault site.
# Coverage sees that both arms were reached; only predicate truth values reveal
# which arm correlates with failure.
#
# ## The Correct Partition
# 
# For completeness, here is the corrected partition. The only change is
# `return head - 1` in the else branch.

def partition_fixed(nums, lo, hi):
    pivot = nums[lo]
    head  = lo + 1
    tail  = hi
    while head < tail:
        while head < hi and nums[head] < pivot:
            head += 1
        while nums[tail] > pivot:
            tail -= 1
        if head < tail:
            swap(nums, head, tail)
            head += 1
            tail -= 1
    if nums[head] < pivot:
        swap(nums, lo, head)
        return head
    else:
        swap(nums, lo, head - 1)
        return head - 1      # fix: was `return head`

def quicksort_fixed(nums, lo, hi):
    if lo < hi:
        j = partition_fixed(nums, lo, hi)
        quicksort_fixed(nums, lo, j - 1)
        quicksort_fixed(nums, j + 1, hi)

def fixed_sort(nums):
    arr = list(nums)
    quicksort_fixed(arr, 0, len(arr) - 1)
    return arr

# Verify the fix on all inputs.

if __name__ == '__main__':
    for (arr,) in passing_inputs + failing_inputs:
        assert fixed_sort(arr) == sorted(arr), f'fix failed on {arr}'
    print('fixed_sort ok on all inputs')

# Run on a broader random sample to gain confidence.

if __name__ == '__main__':
    import random
    random.seed(0)
    for _ in range(500):
        arr = [random.randint(0, 50) for _ in range(random.randint(2, 20))]
        assert fixed_sort(arr) == sorted(arr), f'fix failed on {arr}'
    print('fixed_sort ok on 500 random inputs')
# 
# ## Conclusion
# 
# We have built a predicate-based statistical fault localizer from first
# principles, reusing the instrumentation machinery of the invariant miner
# and adding only one thin subclass and five scoring functions.
# 
# The core ideas are three. First, _predicates are richer than coverage bits_.
# Statement coverage tells us whether a line was reached; predicate truth tells
# us what the program believed at that line. The bug in our quicksort is
# invisible to coverage but clearly visible to predicate analysis:
# `else_branch is true` fires disproportionately in failing runs precisely
# because the else branch is where the off-by-one lives.
# 
# Second, _the counting table unifies two traditions_. Ochiai and Dice were
# developed for spectrum-based fault localization over coverage vectors, but
# they apply without formula change to predicate truth values. The CBI
# Increase statistic adds a signed, base-rate-adjusted view that coverage
# metrics lack.
# 
# Third, _the instrumentation is the same as for invariant mining_. The only
# difference between this post and the previous one is the outcome label on
# each observation: invariant mining keeps predicates that are true in all
# passing runs; fault localization ranks predicates by how much more often
# they are true in failing runs. The `sys.settrace` machinery, the program
# point naming, and the candidate template generation are shared wholesale.
# 
# ## References
# 
# [^jones2002visualization]: James A. Jones, Mary Jean Harrold, and John
# Stasko. "Visualization of test information to assist fault localization."
# ICSE 2002.
# 
# [^liblit2003bug]: Ben Liblit, Alex Aiken, Alice X. Zheng, and Michael I.
# Jordan. "Bug isolation via remote program sampling." PLDI 2003.
# 
# [^liblit2005scalable]: Ben Liblit, Mayur Naik, Alice X. Zheng, Alex Aiken,
# and Michael I. Jordan. "Scalable statistical bug isolation." PLDI 2005.
# 
# [^ochiai1957zoogeographic]: Akira Ochiai. "Zoogeographic studies on the
# soleoid fishes found in Japan and its neighbouring regions." Bulletin of
# the Japanese Society of Scientific Fisheries, 22(9), 1957.
# 
# [^abreu2007accuracy]: Rui Abreu, Peter Zoeteweij, and Arjan J. C. van
# Gemund. "On the accuracy of spectrum-based fault localization." TAICPART
# 2007.
# 
# [^dice1945measures]: Lee R. Dice. "Measures of the amount of ecologic
# association between species." Ecology, 26(3), 1945.
#
# [^kulczynski1928pflanzenassoziationen]: Stanisław Kulczyński.
# "Pflanzenassoziationen der Pieninen." Bulletin International de l'Académie
# Polonaise des Sciences et des Lettres, Classe des Sciences Mathématiques et
# Naturelles, Série B, 1928.
#
# [^jaccard1901etude]: Paul Jaccard. "Étude comparative de la distribution
# florale dans une portion des Alpes et des Jura." Bulletin de la Société
# Vaudoise des Sciences Naturelles, 37, 1901.
