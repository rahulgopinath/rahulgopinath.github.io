# ---
# published: true
# title: Delta Debugging
# layout: post
# comments: true
# tags: reducing
# categories: post
# ---
 
# Note: This is based on the *ddmin* in [the fuzzingbook](https://www.fuzzingbook.org/html/Reducer.html#Delta-Debugging).

# ### About Delta Debugging
# 
# Delta Debugging is a method to reduce failure inducing inputs to their
# smallest required size that still induces the same failure. It was
# first formally introduced in the paper
# [*Simplifying and Isolating Failure-Inducing Input*](https://www.st.cs.uni-saarland.de/papers/tse2002/tse2002.pdf)
# by Zeller and Hildebrandt.
# 
# The idea of delta debugging is fairly simple. We start by partitioning
# the given input string, starting with two partitions -- which have a
# given partition length. Then, we check if any of these parts can be
# removed without removing the observed failure. If any of these can be
# removed, we remove all such parts of the given length. Once no such
# parts of the given length can be removed, we reduce the partition
# length by two, and do the same process again. This obtains us the
# *1-minimal* failure causing string where removal of even a single
# character will remove the observed failure.
# 
# Given a causal function as below,

def test(s):
    v = re.match("<SELECT.*>", s)
    print("%s  %s %d" % (('+' if v else '.'),  s, len(s)))
    return v

# Here is an example run:
# 
# ```shell
# $ python ddmin.py '<SELECT NAME="priority" MULTIPLE SIZE=7>'
# .  ty" MULTIPLE SIZE=7> 20
# .  <SELECT NAME="priori 20
# .  ME="priority" MULTIPLE SIZE=7> 30
# +  <SELECT NAty" MULTIPLE SIZE=7> 30
# +  <SELECT NALE SIZE=7> 20
# .  <SELECT NA 10
# .  CT NALE SIZE=7> 15
# .  <SELELE SIZE=7> 15
# +  <SELECT NAZE=7> 15
# .  <SELECT NA 10
# .  ELECT NAZE=7> 13
# .  <SECT NAZE=7> 13
# .  <SELT NAZE=7> 13
# .  <SELECNAZE=7> 13
# +  <SELECT ZE=7> 13
# +  <SELECT =7> 11
# +  <SELECT > 9
# .  <SELECT  8
# .  SELECT > 8
# .  <ELECT > 8
# .  <SLECT > 8
# .  <SEECT > 8
# .  <SELCT > 8
# .  <SELET > 8
# .  <SELEC > 8
# +  <SELECT> 8
# .  <SELECT 7
# <SELECT>
# ```

# ## Implementation
# 
# How do we implement this?
# 
# First, the prerequisites:

import random
import string

# ### remove_check_each_fragment()

# Given a partition length, we want to split the string into
# that many partitions, remove each partition one at a time from the
# string, and check if for any of them, the `causal()` succeeds. If it
# succeeds for any, then we can skip that section of the string.
 
def remove_check_each_fragment(instr, part_len, causal):
    pre = ''
    for i in range(0, len(instr), part_len):
        removed, remaining = instr[i:i+part_len], instr[i+part_len:]
        if not causal(pre+remaining):
             pre = pre + removed
    return pre

# There is a reason this function is split from the main function unlike in the
# original implementation of `ddmin`. The function `remove_check_each_fragment`
# obeys the contract that any string returned by it obeys the contract represented
# by the `causal` function. This means that any test case that is produced by
# `remove_check_each_fragment` will reproduce the specified behavior, and can be
# used for other computations. For example, one may use it for evaluating test
# reduction slippage, or for finding other reductions.
# 
# 
# ### ddmin()
# 
# The main function. We start by the smallest number of partitions -- 2.
# Then, we check by removing each fragment for success. If removing one
# fragment succeeds, we change the current string to the string without that
# fragment. So, we remove all fragments that can be removed in that partition
# size.
# <!--If none of the fragments could be removed, then we reduce the partition length
# by half. -->
# Next, we reduce the partition length by half and try again.
# If the partition cannot be halved again (i.e, the last partition length was
# one) or the string has become empty, we stop the iteration.

def ddmin(cur_str, causal_fn):
    part_len = len(cur_str) // 2
    while part_len and cur_str:
        cur_str = remove_check_each_fragment(cur_str, part_len, causal_fn)
        part_len = part_len // 2
    return cur_str

# The driver.

def test(s):
    print("%s %d" % (s, len(s)))
    return set('()') <= set(s)

# 

if __name__ == '__main__':
    inputstring = ''.join(random.choices(string.digits +
                          string.ascii_letters +
                          string.punctuation, k=1024))
    print(inputstring)

# 

if __name__ == '__main__':
    assert test(inputstring)
    solution = ddmin(inputstring, test)
    print(solution)

# The nice thing is that, if you invoke the driver, you can see the reduction in
# input length in action. Note that our driver is essentially a best case
# scenario. In the worst case, the complexity is $$O(n^2)$$. The worst case is
# when tests can result in _unresolved_ status, and the last change always fails.
# 
# ## Recursive
# 
# That was of course illuminating. However, is that the only way to implement this?
# *delta-debug* at its heart, is a divide and conquer algorithm. Can we implement it
# recursively? This is the direct translation of ddmin from the paper's
# formalization, which is recursive.

def ddrmin(cur_str, causal_fn, n=2):
    if len(cur_str) == 1:
        return cur_str

    chunk = len(cur_str) // n
    split_idxs = [i for i in range(0, len(cur_str), chunk)]

    # Try complements
    for index in split_idxs:
        complement = cur_str[:index] + cur_str[index + chunk:]  # Remove it
        if causal_fn(complement):
            return ddrmin(complement, causal_fn, 2)  # Reset n to 2

    # Try subsets
    for index in split_idxs:
        s = cur_str[index:index+chunk]
        if causal_fn(s):
            return ddrmin(s, causal_fn, 2)  # Reset n to 2

    # Increase granularity
    if n < len(cur_str):
        return ddrmin(cur_str, causal_fn, min(2 * n, len(cur_str)))

    return cur_str
 
# ## Recursive2
# But, is all that work necessary?
# The basic idea is that given a string, we can split it into parts, and check if either
# part reproduces the failure. If either one does, then call `ddrmin()` on the part that
# reproduced the failure.
# 
# If neither one did, then it means that there is some part in the first partition that
# is required for failure, and there is some part in the second partition too that is required
# for failure. All that we need to do now, is to isolate these parts. How should we do that?
# 
# Call `ddrmin()` but with an updated check. For example, for the first part, rather than
# checking if some portion of the first part alone produces the failure, check if some part of
# first, when combined with the second will cause the failure.
# 
# All we have left to do, is to define the base case. In our case, a character of length one
# can not be partitioned to strictly smaller parts. Further, we already know that any string
# passed into `ddrmin()` was required for reproducing the failure. So, we do not have to
# worry about empty string. Hence, we can return it as is.
# 
# Here is the implementation.
# 
# ### ddrmin()

def ddrmin(cur_str, causal_fn, pre='', post=''):
    if len(cur_str) == 1: return cur_str
    
    part_i = len(cur_str) // 2
    string1, string2 = cur_str[:part_i], cur_str[part_i:]
    if causal_fn(pre + string1 + post):
        return ddrmin(string1, causal_fn, pre, post)
    elif causal_fn(pre + string2 + post):
        return ddrmin(string2, causal_fn, pre, post)
    s1 = ddrmin(string1, causal_fn, pre, string2 + post)
    s2 = ddrmin(string2, causal_fn, pre + s1, post)
    return s1 + s2

# Let us redefine our ddmin

if __name__ == '__main__':
    ddmin = ddrmin

# Given that it is a recursive procedure, one may worry about stack exhaustion, especially
# in languages such as Python which allocates just the bare minimum stack by default. Here
# is the direct conversion to iteration with own stack management.

def ddmin_loop(cur_str, causal_fn, pre='', post=''):
    stack = [('process', cur_str, pre, post)]
    result_stack = []

    while stack:
        frame = stack.pop()
        action = frame[0]
        if action == 'process':
            _, cur_str, pre, post = frame

            if len(cur_str) == 1:
                result_stack.append(cur_str)
                continue

            part_i = len(cur_str) // 2
            string1, string2 = cur_str[:part_i], cur_str[part_i:]

            if causal_fn(pre + string1 + post):
                stack.append(('process', string1, pre, post))
            elif causal_fn(pre + string2 + post):
                stack.append(('process', string2, pre, post))
            else:
                # we need to process string1 first, then combine
                # results of that to process string2
                stack.append(('combine', string2, pre, post))
                stack.append(('process', string1, pre, string2 + post))

        elif action == 'combine':
            _, string2, pre, post = frame
            stack.append(('finalize',))
            # s1 was just computed and is on result_stack
            s1 = result_stack[-1]
            # Now process string2 with updated pre (pre + s1)
            stack.append(('process', string2, pre + s1, post))

        elif action == 'finalize':
            s2 = result_stack.pop()
            s1 = result_stack.pop()
            result_stack.append(s1 + s2)

    return result_stack[0]

# 
if __name__ == '__main__':
    assert test(inputstring)
    solution = ddmin_loop(inputstring, test)
    print(solution)


 
# Note: This Zeller provides a similar algorithm in Zeller[^zeller1999] (1) described below,
# translated to Python,

def dd(cur_str, causal_fn):
    return ddz(cur_str, [], causal_fn)

def ddz(cur_str, remainder, causal_fn):
    if len(cur_str) == 1: return cur_str

    part_i = len(cur_str) // 2
    string1 = cur_str[:part_i]
    string2 = cur_str[part_i:]

    if causal_fn(string1 + remainder):
        return ddz(string1, remainder, causal_fn)

    elif causal_fn(string2 + remainder):
        return ddz(string2, remainder, causal_fn)

    s1 = ddz(string1, string2 + remainder, causal_fn)
    s2 = ddz(string2, string1 + remainder, causal_fn)
    return s1 + s2

# The difference is that adding remainder does not preserve the order unlike in
# the previous formulation I provided. However, note that Zeller [^zeller1999]
# is talking about sets of changes, which are order independent. Secondly, see
# the generation of s1 and s2. s1 is not used in producing s2. That is, there
# could be an element each in string1 and string2, of which only one is
# necessary, and the above would remove it because string2 would contain it
# when testing ddz(string1) and string1 would contain itwhen testing ddz(string2)
# 
# [^zeller1999]: Yesterday, my program worked.Today, it does not. Why? Zeller, 1999.
# 


