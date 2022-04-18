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
# `copy.deepcopy()` makes use of recursion.

if __name__ == '__main__':
    root = []
    my_arr = root
    for i in range(1000):
        my_arr.append([])
        my_arr = my_arr[0]

# This will blow the stack on copy

if __name__ == '__main__':
    import copy
    try:
        new_arr = copy.deepcopy(root)
    except RecursionError as e:
        print(e)

# The trouble is that `copy()` is implemented as a recursive procedure. For
# example, For exmple `copy_array()` may be defined as follows:

def copy_arr(arr):
    if not isinstance(arr, list): return arr
    dup_arr = []
    for item in arr:
        dup_arr.append(copy_arr(item))
    return dup_arr

# This is used as follows:

if __name__ == '__main__':
    my_arr = [1,2,[3, [0]]]
    new_arr = copy_arr(my_arr)
    print(repr(new_arr))

# As before, it easily blows the stack when given a deeply nested data
# structure.

if __name__ == '__main__':
    try:
        new_arr = copy_arr(root)
    except RecursionError as e:
        print(e)

# Here is a simple recipe that lets you duplicate or serialize deeply nested
# data structures. The traditional way to duplicate such a data structure is to
# simply turn the recursive implementation to an iterative solution as follows:


def copy_arr_iter(arr):
    root = []
    stack = [(arr, root)]
    while stack:
        (o, d), *stack = stack
        assert isinstance(o, list)
        for i in o:
            if isinstance(i, list):
                p = (i, [])
                d.append(p[1])
                stack.append(p)
            else:
                d.append(i)
    return root

# It is used as follows:

if __name__ == '__main__':
    my_arr = [1,2,[3, [4], 5], 6]
    new_arr = copy_arr_iter(my_arr)
    print(repr(new_arr))

# As expected, it does not result in stack exhaustion.

if __name__ == '__main__':
    new_arr = copy_arr_iter(root)

# Another way is to use a stack. For example, we can serialize a nested array by
# using the following function.
# We make use of a stack: `to_expand` contains a stack of items that
# still needs to be processed. Our results are stored in `expanded`.

def iter_arr_to_str(arr):
    expanded = []
    to_expand = [arr]
    while to_expand:
        item, *to_expand = to_expand
        if isinstance(item, list):
            to_expand = ['['] + item + [']'] + to_expand
        else:
            if not expanded:
                expanded.append(str(item))
            elif expanded[-1] == '[':
                expanded.append(str(item))
            elif item == ']':
                expanded.append(str(item))
            else:
                expanded.append(', ')
                expanded.append(str(item))
    return ''.join(expanded)

# You can use it as follows:

if __name__ == '__main__':
    my_arr = [1,2,[3, [4], 5], 6]
    new_arr = iter_arr_to_str(my_arr)
    print(repr(new_arr))

# If you do not care about human readability of the generated instructions, you
# can also go for a variant of the tag-length-value (TLV) format used for binary
# serialization.
#
# ### TLV Serialize
#
# Next, we define how to serialize a deep data structure.  Here is our subject.

if __name__ == '__main__':
    example = [{'a':10, 'b':20, 'c': 30}, ['c', ('d', 'e', 1)]]

# The TLV format serializes a data structure by storing the type (tag) of the
# data structure followed by the number of its child elements, finally followed
# by the child elements themselves. That is, (from right to left)
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

def to_tlv(ds):
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

if __name__ == '__main__':
    print(my_stk := to_tlv(example))

# ### TLV Deserialize
# To deserialize, we do the opposite.

def get_children(result_stk):
    l = result_stk.pop()
    return [result_stk.pop() for i in range(l)]

def from_tlv(stk):
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

if __name__ == '__main__':
    print(my_ds := from_tlv(my_stk))

# # Cyclic data structures
# How do we serialize a cyclic data structure or a data structure where
# a single item is present as a child of multiple items?
#
# For example, in the below fragment, `b` contains two links to `a`.

if __name__ == '__main__':
    a = [1, 2]
    b = [a, a]

# To handle such data structures, we need to introduce *naming*. Let us
# consider the below example.

if __name__ == '__main__':
    dex = {'a':10, 'b':20, 'c': 30}
    gexample = [dex, 40, 50]
    dex['e'] = gexample
    print('repr', repr(gexample))

# To handle this we first need a data structure for references.

class Ref__:
    def __init__(self, ds): self._id = id(ds)
    def __str__(self): return str('$'+ str(self._id))
    def __repr__(self): return str('$'+str(self._id))

# ## Serialize
# Next we define how to convert a data structure to a format that preserves
# links.

def to_tlvx(ds):
    expanded = []
    to_expand = [ds]
    seen = set()
    while to_expand:
        ds, *to_expand = to_expand
        if id(ds) in seen:
            expanded.append(Ref__(ds))
        elif type(ds) in {list, set, tuple}:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            to_expand = list(ds) + to_expand
            seen.add(id(ds))
        elif type(ds) in {tuple}:
            assert False, 'tuples not supported'
        elif type(ds) in {dict}:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(len(ds))
            seen.add(id(ds))
            to_expand = [[i,j] for i,j in ds.items()] + to_expand
        elif hasattr(ds, '__dict__'):
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            # to_expand = children(ds) + to_expand <- we stop at any custom
            seen.add(id(ds))
        else:
            expanded.append(Ref__(ds))
            expanded.append('def')
            expanded.append(Ref__(ds))
            expanded.append(type(ds))
            expanded.append(ds)
            seen.add(id(ds))
    return list(reversed(expanded))

# Here is how the definition looks like. As you can see,
# all the nesting is eliminated using naming of data structures.

if __name__ == '__main__':
    print('expanded', my_g := to_tlvx(gexample))

# ## Deserialize
# Next, to recreate the structure

def from_tlvx(stk):
    i = 0
    result_stk = []
    defs = {}
    while stk:
        item, *stk = stk
        if item == 'def':
            iid = result_stk.pop()._id
            kind = result_stk.pop()
            if kind == list:
                ds = get_children(result_stk)
                defs[iid] = list(ds)
            elif kind == set:
                ds = get_children(result_stk)
                defs[iid] = set(ds)
            elif kind == tuple:
                ds = get_children(result_stk)
                assert False, 'tuples not supported'
            elif kind == dict:
                ds = get_children(result_stk)
                defs[iid] = {i:None for i in ds}
            else:
                ds = result_stk.pop()
                defs[iid] = ds
        else:
            result_stk.append(item)
    assert len(result_stk) == 1
    return result_stk[0], defs

# Using it.

if __name__ == '__main__':
    my_gds, defs = from_tlvx(my_g)
    print(my_gds)
    for k in defs:
        print(k)
        print("   ", defs[k])

# ## Reconstruct
# This structure still contains references. So, we need to reconstruct the
# actual data

def reconstruct_tlvx(defs, root):
    for k in defs:
        ds = defs[k]
        if type(ds) in {list, set}: # container
            for i,kx in enumerate(ds):
                if type(kx) == Ref__: # Ref
                    ds[i] = defs[kx._id]
                else:
                    ds[i] = kx

        elif type(ds) in {dict}: # container
            keys = list(ds.keys())
            ds.clear()
            for i,kx in enumerate(keys):
                if type(kx) == Ref__: # Ref
                    k,v = defs[kx._id]
                    if type(v) == Ref__:
                        ds[k] = defs[v._id]
                    else:
                        ds[k] = v
                else:
                    assert False
                    ds[kx] = kx
        else:
            pass
    return defs[root]

# Using it.
if __name__ == '__main__':
    v = reconstruct_tlvx(defs, my_gds._id)
    print(v)

# # Generators for recursion
# This i not the end of the story however. It is remarkably easy to make a
# Python function to allocate its stack frames on the heap so that you
# are not restricted to the arbitrary cut off of recursion limit. The answer
# is [generators](https://speakerdeck.com/dabeaz/generators-the-final-frontier?slide=163).
# Here is how it is done

def cpstrampoline(gen):
    stack = [gen]
    ret = None
    while stack:
        try:
            value, ret = ret, None
            res = stack[-1].send(value)
            stack.append(res)
        except StopIteration as e:
            stack.pop()
            ret = e.value
    return ret

# With this, we can transform any of our recursive functions as below. The idea
# is to change any function call to `yield`

def copy_arr_gen(arr):
    if not isinstance(arr, list): return arr
    dup_arr = []
    for item in arr:
        val = (yield copy_arr_gen(item))
        dup_arr.append(val)
    return dup_arr

# Once we have this, we can use the `cpstrampoline()` to execute this function.

if __name__ == '__main__':
    root = []
    my_arr = root
    for i in range(1000):
        my_arr.append([])
        my_arr = my_arr[0]

# Testing

if __name__ == '__main__':
    new_arr = cpstrampoline(copy_arr_gen(root))
    print(iter_arr_to_str(new_arr))

