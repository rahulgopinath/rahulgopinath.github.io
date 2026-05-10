# ---
# published: true
# title: A simple Daikon-style runtime invariant miner
# layout: post
# comments: true
# tags: invariants, dynamic-analysis, mining
# categories: post
# ---
#
# TLDR; This post is a complete implementation of a Daikon-style runtime
# invariant miner in Python, including instrumentation, trace collection,
# candidate invariant checking, and implication-based suppression.
#
# The concept of _runtime invariant mining_ is as follows. Given a program
# and a set of inputs, we run the program under a tracer that records the
# values of all variables at key points in the execution — function entry,
# function exit, and so on. We then generate a large set of candidate
# invariants (e.g. `x >= 0`, `x == y`, `len(a) == n`) and check each one
# against every recorded state. A candidate that survives all observations
# is reported as a likely invariant.
#
# This idea was introduced by Ernst et al. in the Daikon system
# [^ernst2001daikon]. Daikon has been used to find real bugs, generate
# test oracles, and document program behaviour automatically.
#
# This post follows the same structure as our
# [grammar miner](/post/2019/05/28/simplefuzzer-01/) post: we hook into
# `sys.settrace`, collect observations, and mine structure from them. The
# difference is that instead of recovering a grammar we recover logical
# properties of the program's variables.

# ## Synopsis
#
# ```python
# import daikonminer as D
#
# def my_fn(x, y):
#     return x + y
#
# results = D.mine_invariants(my_fn, [(1, 2), (3, 4), (0, 0)])
# for point, invs in results.items():
#     print(point)
#     for inv in invs:
#         print('  ', inv)
# ```

# ## Definitions
#
# * A _program point_ is a named location in a program's execution at
#   which variable values are observed. Typical program points are function
#   entry (`ENTER`) and function exit (`EXIT`).
#
# * A _trace_ is a sequence of (program point, variable state) pairs
#   collected during a single run of the program on one input.
#
# * A _variable state_ is a snapshot of all in-scope variable bindings at
#   a given program point. For an `EXIT` point this also includes the
#   return value bound to the key `'return'`.
#
# * A _candidate invariant_ is a predicate over a variable state that we
#   wish to check. For example, `x >= 0` or `x == y`.
#
# * An invariant _survives_ a state if the predicate holds for that state.
#   An invariant is _falsified_ the first time it fails on any observed
#   state, and is discarded thereafter.
#
# * A _likely invariant_ is a candidate that survived every observed state
#   at its program point. It is called "likely" because we have only
#   checked a finite set of inputs.
#
# * _Suppression_ is the process of removing redundant invariants. If
#   `x == y` holds, then `x <= y` and `x >= y` are both implied by it and
#   need not be reported separately.

# ## Prerequisites
#
# We only need the standard library for this post.

import sys
import itertools
from collections import defaultdict
from dataclasses import dataclass, field

# We will use the following simple functions as running examples throughout
# the post. They are small enough that we can predict their invariants by
# inspection, which lets us verify that the miner is working correctly.

def triangle(a, b, c):
    """Classify a triangle by its sides."""
    if a == b == c:
        return 'equilateral'
    elif a == b or b == c or a == c:
        return 'isosceles'
    else:
        return 'scalene'

def sum_list(lst):
    """Return the sum of a list of numbers."""
    total = 0
    for x in lst:
        total += x
    return total

# ## Program Points
#
# Daikon's most important design decision is that invariants are attached
# to _program points_, not to functions globally. This means that
# `x >= 0` at `foo:::ENTER` and `x >= 0` at `foo:::EXIT` are two
# separate invariants. The distinction matters: a variable may satisfy
# a property on entry but not on exit, or vice versa.
#
# We represent a program point simply as a named string. By convention
# the name is `function_name:::POINT_TYPE`.

@dataclass(frozen=True)
class ProgramPoint:
    name: str    # e.g. "triangle:::ENTER" or "triangle:::EXIT"

    def __str__(self):
        return self.name

# ### TraceStore
#
# The trace store collects all observed variable states, grouped by
# program point. Each entry in `data` is a list of state dicts, one
# per observation.

@dataclass
class TraceStore:
    data: dict = field(default_factory=lambda: defaultdict(list))

    def add(self, point, state):
        self.data[point.name].append(dict(state))

    def get(self, point):
        return self.data[point.name]

    def points(self):
        return list(self.data.keys())

# Let us verify the basic structure.

if __name__ == '__main__':
    store = TraceStore()
    p = ProgramPoint('foo:::ENTER')
    store.add(p, {'x': 1, 'y': 2})
    store.add(p, {'x': 3, 'y': 4})
    assert len(store.get(p)) == 2
    assert store.get(p)[0] == {'x': 1, 'y': 2}
    print('TraceStore ok')

# ## Instrumentation
#
# To collect traces we hook into Python's `sys.settrace` mechanism. The
# tracer is called on every `call` and `return` event. On `call` we
# record the function's local variables as an `ENTER` state. On `return`
# we record them again as an `EXIT` state, adding the return value under
# the key `'return'`.
#
# We filter out variables whose names start with `_` to avoid cluttering
# the trace with Python internals.

class Instrumentor:
    def __init__(self, store):
        self.store = store
        self._target = None

    def _is_interesting(self, val):
        return isinstance(val, (int, float, str, list, tuple, bool))

# ### The tracer callback
#
# The tracer is registered with `sys.settrace`. Python calls it on every
# `call`, `return`, `line`, and `exception` event. We respond only to
# `call` and `return` to keep overhead low.

class Instrumentor(Instrumentor):
    def tracer(self, frame, event, arg):
        if event not in ('call', 'return'):
            return self.tracer
        fn = frame.f_code.co_name
        if fn.startswith('_'):
            return self.tracer

        point_type = 'ENTER' if event == 'call' else 'EXIT'
        point = ProgramPoint('%s:::%s' % (fn, point_type))

        state = {k: v for k, v in frame.f_locals.items()
                 if not k.startswith('_') and self._is_interesting(v)}
        if event == 'return' and self._is_interesting(arg):
            state['return'] = arg

        self.store.add(point, state)
        return self.tracer

# ### Running a function under the tracer

class Instrumentor(Instrumentor):
    def run(self, fn, *args, **kwargs):
        sys.settrace(self.tracer)
        try:
            result = fn(*args, **kwargs)
        finally:
            sys.settrace(None)
        return result

# Let us test the instrumentor on our running example.

if __name__ == '__main__':
    store = TraceStore()
    instr = Instrumentor(store)
    instr.run(triangle, 3, 3, 3)
    assert 'triangle:::ENTER' in store.points()
    assert 'triangle:::EXIT'  in store.points()
    enter_state = store.get(ProgramPoint('triangle:::ENTER'))[0]
    assert enter_state == {'a': 3, 'b': 3, 'c': 3}
    exit_state = store.get(ProgramPoint('triangle:::EXIT'))[0]
    assert exit_state['return'] == 'equilateral'
    print('Instrumentor ok')

# ### Collecting traces over multiple inputs
#
# We run the function once per input and accumulate all observations in
# the same store.

def collect_traces(fn, inputs, store=None):
    if store is None:
        store = TraceStore()
    instr = Instrumentor(store)
    for args in inputs:
        if isinstance(args, tuple):
            instr.run(fn, *args)
        else:
            instr.run(fn, args)
    return store

# Let us collect traces for a range of triangle inputs.

if __name__ == '__main__':
    triangle_inputs = [
        (3, 3, 3),
        (3, 3, 4),
        (3, 4, 5),
        (5, 5, 5),
        (1, 2, 3),
    ]
    store = collect_traces(triangle, triangle_inputs)
    print('program points:', store.points())
    print('ENTER observations:', len(store.get(ProgramPoint('triangle:::ENTER'))))

# ## Candidate Invariants
#
# An _Invariant_ object wraps a predicate and tracks whether it has been
# falsified. Once falsified it stays dead — we never resurrect it.

class Invariant:
    def __init__(self, name, check):
        self.name  = name
        self.check = check
        self.alive = True

    def test(self, state):
        if not self.alive:
            return
        try:
            if not self.check(state):
                self.alive = False
        except Exception:
            self.alive = False

    def __repr__(self):
        return self.name

# ### Unary templates
#
# Unary invariants involve a single variable. We generate a small fixed
# set of templates for every numeric and string variable we see.

def unary_invariants(var):
    return [
        Invariant('%s is not None' % var,
                  lambda s, v=var: s.get(v) is not None),
        Invariant('%s >= 0' % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] >= 0),
        Invariant('%s > 0' % var,
                  lambda s, v=var: isinstance(s.get(v), (int, float))
                                   and s[v] > 0),
        Invariant('type(%s) is int' % var,
                  lambda s, v=var: isinstance(s.get(v), int)),
        Invariant('type(%s) is str' % var,
                  lambda s, v=var: isinstance(s.get(v), str)),
    ]

# Let us verify a single invariant against a state.

if __name__ == '__main__':
    invs = unary_invariants('x')
    state_ok  = {'x': 5}
    state_bad = {'x': -1}
    for inv in invs:
        inv.test(state_ok)
    assert all(inv.alive for inv in invs)
    invs[1].test(state_bad)          # x >= 0 should die
    assert not invs[1].alive
    assert invs[0].alive             # x is not None should survive
    print('unary invariants ok')

# ### Binary templates
#
# Binary invariants involve two variables. We generate templates for
# every pair of variables that appear together in at least one state.

def binary_invariants(x, y):
    return [
        Invariant('%s == %s' % (x, y),
                  lambda s, a=x, b=y: s.get(a) == s.get(b)),
        Invariant('%s <= %s' % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] <= s[b]),
        Invariant('%s >= %s' % (x, y),
                  lambda s, a=x, b=y:
                      isinstance(s.get(a), (int, float)) and
                      isinstance(s.get(b), (int, float)) and
                      s[a] >= s[b]),
    ]

# Let us verify binary invariants.

if __name__ == '__main__':
    invs = binary_invariants('x', 'y')
    for state in [{'x': 2, 'y': 2}, {'x': 2, 'y': 2}]:
        for inv in invs: inv.test(state)
    assert invs[0].alive    # x == y survived
    for inv in invs: inv.test({'x': 1, 'y': 2})
    assert not invs[0].alive   # x == y falsified
    assert invs[1].alive       # x <= y survived
    print('binary invariants ok')

# ## Invariant Engine
#
# The engine takes a `TraceStore`, generates candidate invariants for each
# program point, and checks them against all observations at that point.
#
# ### Generating candidates for a point
#
# We first collect all variable names that appear in any state at the
# point, then generate all unary and binary candidates over those names.

class InvariantEngine:
    def candidates_for(self, observations):
        all_vars = set()
        for state in observations:
            all_vars.update(state.keys())
        all_vars = sorted(all_vars)

        candidates = []
        for v in all_vars:
            candidates.extend(unary_invariants(v))
        for x, y in itertools.combinations(all_vars, 2):
            candidates.extend(binary_invariants(x, y))
        return candidates

# Let us verify candidate generation.

if __name__ == '__main__':
    engine = InvariantEngine()
    obs = [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]
    cands = engine.candidates_for(obs)
    names = [c.name for c in cands]
    assert 'x >= 0' in names
    assert 'x == y' in names
    print('candidate generation ok, %d candidates' % len(cands))

# ### Checking candidates against observations
#
# We test every candidate against every observed state. Candidates that
# remain alive after all observations are the likely invariants.

class InvariantEngine(InvariantEngine):
    def check(self, candidates, observations):
        for state in observations:
            for inv in candidates:
                inv.test(state)
        return [inv for inv in candidates if inv.alive]

# ### Running the full analysis

class InvariantEngine(InvariantEngine):
    def analyze(self, store):
        results = {}
        for point_name in store.points():
            observations = store.data[point_name]
            if not observations:
                continue
            candidates = self.candidates_for(observations)
            results[point_name] = self.check(candidates, observations)
        return results

# Let us run the engine on our triangle traces.

if __name__ == '__main__':
    store = collect_traces(triangle, triangle_inputs)
    engine = InvariantEngine()
    results = engine.analyze(store)
    for point, invs in results.items():
        print(point)
        for inv in invs:
            print('  ', inv)
    print()

# Notice that at `triangle:::ENTER` we expect to see `a >= 0`, `b >= 0`,
# and `c >= 0` because all our inputs used positive side lengths. We also
# expect `type(a) is int` and similar. At `triangle:::EXIT` we expect
# `type(return) is str`.

# ## Suppression
#
# The engine produces many redundant invariants. If `x == y` holds, then
# both `x <= y` and `x >= y` also hold but add no information. The
# suppression step removes weaker invariants that are implied by stronger
# ones.
#
# We maintain a simple implication table: if an invariant whose name
# contains the _strong_ pattern is alive, we remove any co-surviving
# invariant whose name contains the _weak_ pattern and shares the same
# variable names.

class SuppressionLattice:
    # Each entry is (strong_marker, weak_marker). If an invariant
    # matching strong_marker is alive for a given variable pair, we
    # suppress any co-surviving invariant matching weak_marker for the
    # same pair.
    IMPLIES = [
        ('==', '<='),
        ('==', '>='),
    ]

# ### Extracting variable names from an invariant name
#
# We need to compare two invariants to decide whether they share the
# same variables. We extract the tokens that look like variable names
# (no spaces, not operators).

class SuppressionLattice(SuppressionLattice):
    def _vars(self, inv_name):
        tokens = inv_name.replace('(', ' ').replace(')', ' ').split()
        return frozenset(t for t in tokens
                         if t.isidentifier() and t not in ('type', 'is',
                                                            'not', 'None',
                                                            'int', 'str',
                                                            'float'))

# ### Applying suppression to a list of invariants

class SuppressionLattice(SuppressionLattice):
    def suppress(self, invariants):
        alive = list(invariants)
        to_remove = set()
        for strong, weak in self.IMPLIES:
            strong_invs = [i for i in alive if strong in i.name]
            weak_invs   = [i for i in alive if weak   in i.name
                           and strong not in i.name]
            for s_inv in strong_invs:
                s_vars = self._vars(s_inv.name)
                for w_inv in weak_invs:
                    if self._vars(w_inv.name) == s_vars:
                        to_remove.add(id(w_inv))
        return [i for i in alive if id(i) not in to_remove]

# Let us verify suppression.

if __name__ == '__main__':
    lattice = SuppressionLattice()
    eq_inv  = Invariant('x == y', lambda s: s['x'] == s['y'])
    le_inv  = Invariant('x <= y', lambda s: s['x'] <= s['y'])
    ge_inv  = Invariant('x >= y', lambda s: s['x'] >= s['y'])
    result  = lattice.suppress([eq_inv, le_inv, ge_inv])
    assert len(result) == 1
    assert result[0].name == 'x == y'
    print('suppression ok')

# ## Full Pipeline
#
# We now combine all the pieces into a single `mine_invariants` function.

def mine_invariants(fn, inputs):
    store   = collect_traces(fn, inputs)
    engine  = InvariantEngine()
    raw     = engine.analyze(store)
    lattice = SuppressionLattice()
    return {point: lattice.suppress(invs) for point, invs in raw.items()}

# Let us run the full pipeline on our triangle function.

if __name__ == '__main__':
    results = mine_invariants(triangle, triangle_inputs)
    for point, invs in results.items():
        print(point)
        for inv in invs:
            print('  ', inv)
    print()

# And on `sum_list`.

if __name__ == '__main__':
    sum_inputs = [[1, 2, 3], [0], [10, 20], [1, 1, 1, 1]]
    results = mine_invariants(sum_list, sum_inputs)
    for point, invs in results.items():
        print(point)
        for inv in invs:
            print('  ', inv)
    print()

# ## Utilities

def format_results(results):
    lines = []
    for point in sorted(results.keys()):
        lines.append(point)
        for inv in results[point]:
            lines.append('    ' + str(inv))
    return '\n'.join(lines)

# Using it.

if __name__ == '__main__':
    results = mine_invariants(triangle, triangle_inputs)
    print(format_results(results))

# ## References
#
# [^ernst2001daikon]: Michael D. Ernst, Jake Cockrell, William G. Griswold,
# David Notkin. "Dynamically Discovering Likely Program Invariants to
# Support Program Evolution." IEEE Transactions on Software Engineering,
# 27(2):99–123, 2001.
#
# [^ernst2007daikon]: Michael D. Ernst et al. "The Daikon system for
# dynamic detection of likely invariants." Science of Computer
# Programming, 69(1–3):35–45, 2007.
