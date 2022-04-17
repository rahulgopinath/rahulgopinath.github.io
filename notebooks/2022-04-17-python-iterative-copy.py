# ---
# published: true
# title: Iterative deep copy of Python data structures
# layout: post
# comments: true
# tags: deepcopy
# categories: post
# ---

# One of the problems when working with Python is that, even though many
# libraries use data structures making use of recursion, the recursion stack in
# Python is limited. Python starts with a recursion budget of 1000 function
# calls which is easy to exhaust. Such data structures include
# `JSON` and `pickle`. Even simple deep copy of a Python data structure from
# `copy.deepcopy()` makes use of recursion. Here is a simple recipe that lets
# you serialize and duplicate deep data structures.
# 
# The idea is to turn any data structure into a series of instructions in a
# [concatenative language](https://en.wikipedia.org/wiki/Concatenative_programming_language)
# that recreates the data structure. A concatenative language is defined by a
# sequence of instructions that is Turing complete. Hence, it is suitable for
# what we want to do.

# ## To concatenative instructions

# ### Serialize
# Next, we define how to serialize a deep data structure.  Here is our subject.

example = [{'a':10, 'b':20, 'c': 30}, ['c', ('d', 'e', 1)]]

# To turn this to a linear sequence of instructions, we make use of two stacks.
# The `to_expand` contains a stack of items that still needs to be processed,
# and `expanded` is a stack of concatenative instructions to build the data
# structure that was input. The idea is that the following stack
# 
# ```
# 'a' 'b' 'c' 'd' 2 <set> 3 <list>
# ```
# represents
#
# ```
# 'a' 'b' {'c', 'd'} 3 <list>
# ```
# which in turn represents the following Python data structure.
# ```
# ['a', 'b', {'c', 'd'}]
# ```

def to_stack(ds):
    expanded = []
    to_expand = [ds]
    while to_expand:
        ds, *to_expand = to_expand
        if type(ds) in {list, set, tuple}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
        elif type(ds) in {dict}:
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds.items()) + to_expand
        else:
            expanded.append(ds)
    return list(reversed(expanded))

# Let us see how it works

(my_stk := to_stack(example))

# ### Deserialize
# To deserialize, we do the opposite.

def get_children(result_stk):
    l = result_stk.pop()
    return [result_stk.pop() for i in range(l)]

def from_stack(stk):
    i = 0
    result_stk = []
    while stk:
        item, *stk = stk
        if item == list:
            ds = get_children(result_stk)
            result_stk.append(ds)
        elif item == set:
            ds = get_children(result_stk)
            result_stk.append(set(ds))
        elif item == tuple:
            ds = get_children(result_stk)
            result_stk.append(tuple(ds))
        elif item == dict:
            ds = get_children(result_stk)
            result_stk.append({i[0]:i[1]for i in ds})
        else:
            result_stk.append(item)
    return result_stk[0]

# Let us see how it works

(my_ds := from_stack(my_stk))

