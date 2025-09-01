# ---
# published: true
# title: A Tiny Prolog in Python
# layout: post
# comments: true
# tags: prolog unification
# categories: post
# ---

# TLDR; This tutorial is an implementation of a toy prolog interpreter
# in Python. It is based on an earlier implementation [here](http://www.okisoft.co.jp/esc/prolog/in-python.html)
# that has since disappeared.

# ## Definitions
# For this post, we use the following terms:
#
# * A _fact_ is a statement that is unconditionally true. For example,
#   `man(adam).` asserts that Adam is a man.
#
# * A _rule_ is a conditional statement that defines when something holds.
#   For example, `father(P, C) :- man(P), parent(P, C).` states that `P` is a
#   father of `C` if `P` is a man and `P` is a parent of `C`.
#
# * A _query_ (or goal sequence) is a question posed to the system, asking for
#   values of variables that make a statement true. For example, `?- father(X, Y).`
#   asks for all pairs `(X, Y)` that satisfy the relation.
#
# * A _variable_ is a placeholder for an unknown value. During execution,
#   variables can be bound to constants or other variables.
#
# * A _constant_ is a literal value such as a number or string (e.g., `"adam"`, `42`).
#
# * A _predicate_ is a named relation, such as `man/1` or `parent/2`. Applying
#   a predicate to arguments produces a goal.
#
# * A _goal_ (or predicate term) is an instance of a predicate applied to
#   arguments, such as `man(adam)`. Prolog execution is the process of trying to
#   satisfy goals.
#
# * A _clause_ is a definition consisting of a head and a body. The head is a
#   goal, and the body is a sequence of subgoals that must hold for the head
#   to be true.
#
# * An _environment_ is a mapping from variables to values (or other variables)
#   that records substitutions created during unification.
#
# * _Unification_ is the process of making two terms equal by finding
#   consistent bindings for variables. For example, unifying `X` with `"adam"`
#   binds `X` to `"adam"`.
#
# * _Dereferencing_ means following variable bindings in the environment until
#   reaching either a concrete value or an unbound variable.
#
# * _Resolution_ is the inference mechanism of Prolog: repeatedly trying to
#   satisfy goals by unifying them with predicate definitions and recursively
#   solving subgoals.
#
# * _Backtracking_ is the process of undoing variable bindings and trying
#   alternative clauses when a goal cannot be satisfied.


# # Building a Tiny Prolog in Python
#
# This implementation is based on an earlier implementation in Python2
# [here](http://www.okisoft.co.jp/esc/prolog/in-python.html).
# The effort here is to update it for Python3, and to serve as a reference for future.
# The explanations are partial, and will be completed at a later point.
# 
# Prolog is a language designed around **first-order predicate logic** [^prolog]. Instead
# of writing explicit algorithms, you declare **facts** and **rules**, and Prolog
# automatically searches for values that satisfy them.
#
# For example:
# 
# ```
# man(adam).
# parent(adam, cain).
# father(P, C) :- man(P), parent(P, C).
# ```
# 
# means that Adam is a man, Adam is the parent of Cain, and anyone who is both a
# man and a parent is a father.
#
# We will next build a very small Prolog engine in Python. Note that our
# implementation is very simple, and does not implement advanced concepts
# such as CUT or the WAM virtual machine. We next start with implementing
# the basic prolog concepts in Python.
# 
# ## Variables
# 
# In Prolog, variables stand for unknown values that the system will try to
# assign during computation. For example, one may query for `man(X)`, and the
# `X` is represented by `Var`.

class Var:
    def __init__(self, name): self.name = name

    def __str__(self): return '$' + self.name

    def __hash__(self): return hash(self.name)

    def __repr__(self): return str(self)

    def __eq__(self, other): return self.name == other.name

# Using it
if __name__ == '__main__':
    A = Var('A')
    print(A)

# ## Predicates
# 
# A **predicate** represents a relation, such as `man(X)` or `parent(X,Y)`.
# A predicate has a name and may have definitions (facts or rules).
# We model this using the `Pred` class.

class Pred:
    def __init__(self, name): self.name, self.defs = name, []

    def __str__(self): return self.name

    def __repr__(self): return str(self)

    def __call__(self, *args): return Goal(self, to_list(args))

# Due to limitations of adapting Prolog semantics to Python's semantics,
# we need to declare a predicate before we can attach any definitions to it.
# This is how we can delcare a predicate

if __name__ == '__main__':
    man = Pred('man')
    print(man)

# ## Goals
#  
# A **goal** is a predicate applied to arguments, e.g., `man(adam)` or `parent(X,Y)`.
# Goals can also be used to define clauses by associating them with other goals.
# The essential idea is that given a predicate goal, the prolog interpreter tries
# to find the subgoals that when solved, will make the current goal succeed. We
# will see this later in `unify()`.
# 
# **Note:** Here, we represent clauses with `<<`. That is,
# 
# ```
# man('adam') << ()
# ```

class Goal:
    def __init__(self, pred, args): self.pred, self.args = pred, args

    def __lshift__(self, rhs): self.pred.defs.append((self, to_list(rhs)))

    def __str__(self): return "%s%s" % (str(self.pred), str(self.args))

    def __repr__(self): return str(self)

# This is how we define a goal. We leave the testing until we have defined `Cons`.
if __name__ == '__main__':
    gman = Goal(Pred('man'), [])
    print(gman)


# ## Lists
#  
# Prolog programs often use list-like structures. Here we represent them
# with a Lisp-style `Cons` cell. 

class Cons:
    def __init__(self, car, cdr): self.car, self.cdr = car, cdr

    def __str__(self):
       def lst_repr(x):
          if x.cdr is None: return [str(x.car)]
          elif type(x.cdr) is Cons: return [str(x.car)] + lst_repr(x.cdr)
          else: return [str(x.car), '.', str(x.cdr)]
       return '(' + ' '.join(lst_repr(self)) + ')'

    def __repr__(self): return str(self)

    def pair(self): return (self.car, self.cdr)

    def __getitem__(self, i): return self.pair()[i]

# Let us test it out
if __name__ == '__main__':
    c = Cons(1, None)
    print(c)
    d = Cons(2, c)
    print(d)

# We update our Var with `**` to stand in for list construction by appending
# a term to the beginning of the list That is, `cons(term, list)` same as `:` in other languages.
class Var(Var):
    def __pow__(self, other):
        return Cons(self, other)


# Let us test it out
if __name__ == '__main__':
    e = Var('E')
    print(e ** d)

# The helper `to_list` converts Python sequences into this linked-list form.
def to_list(x, y=None):
    for e in reversed(x):
        if type(e) is list: y = Cons(to_list(e), y)
        elif type(e) is Cons: y = e
        else: y = Cons(e, y)
    return y

# Let us test the complete functionality.
if __name__ == '__main__':
    man = Pred('man')
    X = Var('X')
    g = man(X)
    g << []
    print(g)

# ## Environment
# Prolog variables don’t store values directly. Instead, an **environment**
# keeps track of bindings. Each variable may be associated with a term and
# the environment where it was bound. This allows variables to reference
# other variables until eventually grounded.

class Env:
    def __init__(self): self.table = {}

    def put(self, x, pair): self.table[x] = pair

    def get(self, x): return self.table.get(x)

    def clear(self): self.table = {}

    def __repr__(self): return "env:" + str(self.table)

    def delete(self, x): del self.table[x]

    def __str__(self): return "env:" + str(self.table)

    def dereference(self, t):
        env = self
        while type(t) is Var:
            p = env.get(t)
            if p is None: break
            t, env = p
        return [t, env]

    def __getitem__(self, t):
        t, env = self.dereference(t)
        tt = type(t)
        if tt is Goal: return Goal(t.pred, env[t.args])
        if tt is Cons: return Cons(env[t.car], env[t.cdr])
        if tt is list: return [env[e] for e in t]
        return t
# Let us test the complete functionality.
if __name__ == '__main__':
    env = Env()
    env.put('A', Cons(1, Cons(2, None)))
    env.put('B', to_list([3, 4]))
    print(env.get('A'))
    print(env.get('B'))
    print(env)
    env.clear()
    A,B,C = Var('A'), Var('B'), Var('C')
    env.put(A, Cons(B, env))
    env.put(B, Cons(C, env))
    env.put(C, Cons(1, env))
    print(env.dereference(A))

# ## Unification
# The heart of Prolog is **unification**, which tries to make two terms equal
# by binding variables as necessary. The `unify` function handles different
# cases: variable-variable, variable-term, and term-term.

def unify(x, x_env, y, y_env, trail, tmp_env):
    while True:
        if type(x) is Var:
           xp = x_env.get(x)
           if xp is None:
              yp = y_env.dereference(y)
              if (x, x_env) != yp:
                  x_env.put(x, yp)
                  if x_env != tmp_env: trail.append((x, x_env))
              return True
           else:
              x, x_env = xp
              x, x_env = x_env.dereference(x)
        elif type(y) is Var: x, x_env, y, y_env = y, y_env, x, x_env
        else: break
    if type(x) is Goal and type(y) is Goal:
       if x.pred != y.pred: return False
       x, y = x.args, y.args
    if not (type(x) is Cons and type(y) is Cons): return x == y
    return all(unify(a, x_env, b, y_env, trail, tmp_env) for (a,b) in zip(x, y))

# ## Resolution
# Finally, we need to **solve queries**. Resolution works by trying to match
# goals against predicate definitions, applying unification, and recursively
# resolving subgoals. Python’s generators make it natural to model
# Prolog’s backtracking search.

def resolve_body(body, env):
    if body is None: yield None # yield whenever no more goals remain
    else:
       goal, rest = body.car, body.cdr
       for d_head, d_body in goal.pred.defs:
          d_env, trail = Env(), []
          if unify(goal, env, d_head, d_env, trail, d_env):
             if d_body and callable(d_body.car):
                 if d_body.car(CallbackEnv(d_env, trail)):
                     yield from resolve_body(rest, env)
             else:
                for _i in resolve_body(d_body, d_env):
                    yield from resolve_body(rest, env)
          for x, x_env in trail: x_env.delete(x)

def resolve(goals):
    env = Env()
    for _ in resolve_body(to_list(goals), env): # not an error.
        yield env

# We also define a `CallbackEnv` to allow us to to make simple
# function calls.
class CallbackEnv:
    def __init__(self, env, trail): self.env, self.trail = env, trail

    def __getitem__(self, t): return self.env[t]

    def unify(self, t, u): return unify(t, self.env, u, self.env, self.trail, self.env)

# We also define a convenience method `query` that resovles the goals.
def query(*goals):
   goals = list(goals)
   return [env[goals] for env in resolve(goals)]

# variables, which allow us to define Vars
def variables(symbols):
    for s in symbols: globals()[s] = Var(s)

# and predicates, which allow us to define predicates
def predicates(predicates):
    for s in predicates: globals()[s] = Pred(s)

# Now, let us test all these out. We first define a few variables and predicates,
# which are needed to ensure that we can add clauses to predicates.
if __name__ == '__main__':
    variables([chr(x) for x in range(ord('A'),ord('Z')+1)])
    predicates(['eq', 'noteq', 'gt', 'gteq', 'lt', 'lteq', 'write', 'writenl', 'nl'])

# Next, we construct a simple library. Let us define our predicates.
if __name__ == '__main__':
    eq(X, Y) << [lambda env: env.unify(env[X], env[Y])]
    noteq(X, Y) << [lambda env: env[X] != env[Y]]
    gt(X, Y) << [lambda env: env[X] > env[Y]]
    gteq(X, Y) << [lambda env: env[X] >= env[Y]]
    lt(X, Y) << [lambda env: env[X] < env[Y]]
    lteq(X, Y) << [lambda env: env[X] <= env[Y]]

# Predicates for writing.
if __name__ == '__main__':
    write(X) << [lambda env: (print(env[X], end=''),)]
    writenl(X) << [lambda env: (print(env[X]),)]
    nl() << [lambda env: (print(),)]


# A few more predicates for list operations.
if __name__ == '__main__':
    predicates(['car', 'cdr', 'cons', 'member', 'append', 'reverse', 'takeout', 'perm', 'subset'])
     
    car([X**Y],X) << []
    cdr([X**Y],Y) << []
     
    cons(X,R,[X**R]) << []
     
    member(X,[X**R]) << []
    member(X,[Y**R]) << [member(X,R)]
     
    append([],X,X) << []
    append([X**Y],Z,[X**W]) << [append(Y,Z,W)]
     
    reverse([X**Y],Z,W) << [reverse(Y,[X**Z],W)]
    reverse([],X,X) << []
    reverse(A,R) << [reverse(A,[],R)]
     
    takeout(X,[X**R],R) << []
    takeout(X,[F**R],[F**S]) << [takeout(X,R,S)]

    subset([X**R],S) << [member(X,S), subset(R,S)]
    subset([],X) << []

# Let us try writing a merge sort.
if __name__ == '__main__':
    predicates(['mergesort', 'split', 'merge'])

    mergesort([],[]) << []
    mergesort([A],[A]) << []
    mergesort([A**B**R],S) << [
      split([A**B**R],P,T),
      mergesort(P,Q),
      mergesort(T,U),
      merge(Q,U,S)]

    split([],[],[]) << []
    split([A],[A],[]) << []
    split([A**B**R],[A**X],[B**Y]) << [split(R,X,Y)]

    merge(A,[],A) << []
    merge([],B,B) << []
    merge([A**X],[B**Y],[A**M]) << [lteq(A,B), merge(X,[B**Y],M)]
    merge([A**X],[B**Y],[B**M]) << [gt(A,B),  merge([A**X],Y,M)]

# Let us test it out.
if __name__ == '__main__':
    print("mergesort[")
    print(query(mergesort([4,3,6,5,9,1,7],S)))
    print("]")

# A few more tests. First membership.
if __name__ == '__main__':
    print("membership[")
    print(query(member(1,[1,2,3])))
    print(query(member(3,[1,2,3])))
    print(query(member(10,[1,2,3])))
    print("]")

# Appending to a list
if __name__ == '__main__':
    print("append[")
    print(query(append([],[1,2],A)))
    print(query(append([1,2,3],[4],B)))
    print(query(append([1,2,3],[4,5],[1,2,3,4,5])))
    print(query(append([1,2,3],W,[1,2,3,4,5])))
    print("]")

# Reversing a list
if __name__ == '__main__':
    print("reverse[")
    print(query(reverse([1,2,3,4,5],X)))
    print("]")

# Takeout
if __name__ == '__main__':
    print("takeout[")
    print(query(takeout(X,[1,2,3],L)))
    print("]")

    # perm([X**Y],Z) << [perm(Y,W), takeout(X,Z,W)]
    # perm([],[]) << []
    # print(query(perm(P,[1,2])))

# Subset
if __name__ == '__main__':
    print("subset[")
    print(query(subset([4,3],[2,3,5,4])))
    print(query(subset([A],[2,3,5,4])))
    print("]")

# A few more predicates. We also define our digits.
if __name__ == '__main__':
    predicates(['expr', 'num', 'number', 'digit', 'plus', 'minus'])
    digit('1') << []
    digit('2') << []
    digit('3') << []
    digit('4') << []
    digit('5') << []
    digit('6') << []
    digit('7') << []
    digit('8') << []
    digit('9') << []
    digit('0') << []
    plus('+') << []
    minus('-') << []
    
    variables(['Rest','Remain', 'L1', 'L2'])
    number([D]) << [digit(D)]
    number([D**Rest]) << [digit(D), number(Rest)]
    print(query(number(list('12'))))
    
    print("expr[")
    expr(L, A) << [num(L), eq(L, A)]
    expr(L, A) << [append(L1, [P**L2], L), plus(P), num(L1), expr(L2,B), eq(plus(L1,B), A)]
    expr(L, A) << [append(L1, [P**L2], L), minus(P), num(L1), expr(L2,B), eq(minus(L1,B), A)]
    num(D) << [number(D)]
    
    val = query(expr(list('1+2-3'),A))
    print(query(expr(list('1+2-3'),A)))
    print("]")
    
# Using definite clause grammars.
if __name__ == '__main__':
    print("dcg[")
    predicates(['dcgexpr', 'dcgnum', 'rcons', 'dcgexprcomplete'])
    dcgexpr(L, Remain) << [dcgnum(L, Remain)]
    dcgexpr(L, Remain) << [dcgnum(L, L1), rcons(L1, '+', L2), dcgexpr(L2, Remain)]
    dcgexpr(L, Remain) << [dcgnum(L, L1), rcons(L1, '-', L2), dcgexpr(L2, Remain)]
    dcgnum([D**Remain], Remain) << [digit(D)]
    rcons([X**L], X, L) << []
    dcgexprcomplete(L) << [dcgexpr(L, list(''))]
    print(query(dcgnum(list('123'), A)))
    print(query(rcons(list('+123'), '+', L)))
    print(query(dcgexpr(list('1+2-3'), A)))
    print(query(dcgexprcomplete(list('1-2+3'))))
    print("]")
   
# Another way to use query.
if __name__ == '__main__':
    for e in query(member(X, [1,2,3])):
        print(e[0])



# # References
# [^prolog]:  Colmerauer, A. and Roussel, P., 1996. The birth of Prolog. In History of programming languages
