# ---
# published: true
# title: Simple Parser For Context Free Languages with Forking Stacks
# layout: post
# comments: true
# tags: combinators, parsing, cfg
# categories: post
# ---

# We [previously](/post/2020/03/02/combinatory-parsing/) saw how to parse simple context-free
# languages using combinatory parsers. In another [post](/post/2018/09/06/peg-parsing/), I had
# also detailed how one can do a simple PEG and even a context-free parser. However, these
# parsers are unsatisfying in some sense. They do not handle left recursion correctly.
# 
# The essential idea in those is to make use of the Python stack for recursive descent style 
# parsing. Using the language stack however comes with the restriction that one is restricted 
# to a depth first strategy. One cannot suspend an exploration when one feels like it, and 
# resume it later. How much does it take to implement left recursion? My [post](/post/2018/09/06/peg-parsing/)
# on CFG parses hints at a way. What we need to do is to handle the stack on our own, and do 
# a breadth first search search of the possible parses.
# 
# That is, we consider multiple parses at once (as multiple threads), and prioritize the most
# optimistic parsing scenarios so that they get examined first.
# 
# We use the following heuristic: The threads that are farthest along in parsing (in terms
# of number of characters parsed) gets the highest priority. Next, the threads where the
# first item is the shallowest gets the highest priority.
# 
# Here is a simple implementation. It takes the input chars (`lst`), the starting `key` and
# the `grammar`. Then, it extracts the most promising parse thread, *explores* its first element,
# which may produce a new set of threads that represent alternative parse directions.

import heapq as H
import math
import string

# Our grammars are

nl_grammar = {
        "<E>": [["<T>", "+", "<E>"],
                ["<T>"]],
        "<T>": [["1"],
               ["(", "<E>", ")"]]
        }
nl_start = "<E>"

# The match method assumes that our queue contains the threads of parsing.
# It extracts the top most (`current`) thread, and explores the possible
# threads that can result from it. If any of the threads result in a parse,
# we yield it. If not, we check if we can continue parsing with a given thread,
# and if we can, add the thread to the heap.

def match(lst, key, grammar):
    queue = [((len(lst), 0), [key])]
    while queue:
        current = H.heappop(queue)
        rlst = explore(current, lst, grammar)
        for item in rlst:
            (lst_rem, _depth), rule = item
            if lst_rem == 0:
                if not rule:
                    yield 'parsed: ' + str(len(lst))
                else:
                    # (check for epsilons)
                    H.heappush(queue, item)
            else:
                if not rule: # incomplete parse
                    continue
                else:
                    H.heappush(queue, item)

# The `explore()` method is fairly simple. It checks if the given element is a terminal or
# a nonterminal. If it is a terminal, it is checked for a match, and if matched, the current
# parsing point is updated, and returned. If not a match, the current thread is discarded.
# 
# If the gievn element is a nonterminal, then the parsing can proceed in any of the possible
# expansions of the nonterminal. So, the parsing thread is split into as many new threads, and
# the nonterminal is replaced with its particular expansion in each of the thread, and the
# new threads are returned.

def explore(current, lst, grammar):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    key = rule[0]

    if key not in grammar:
        if lst_rem == 0: return []
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), math.inf), rule[1:])]
    else:
        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = expansion + rule[1:]
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret

# The driver would be

def forking_parse(arg, grammar, start):
    for x in match(list(arg), start, grammar):
        print(x)

if __name__ == '__main__':
    forking_parse('1+1', nl_grammar, nl_start)


# While this can certainly handle left recursion, there is a new problem. The issue is that
# in the case of left recursion, and an incomplete prefix, the threads simply multiply, with
# out any means of actually parsing the input. 
# 
# That is, given the usual grammar:
# and the input `1+`, the `<E>` will keep getting expanded again and again generating
# new threads. So the parser will never terminate.
# 
# So, what we need is a way to discard invalid potential parses immediately. In our
# case, we can see that if you have reached the end of `1+` where there are no more characters
# to parse, we no longer can accept an expansion that has even a single terminal symbol that
# is non empty. We can make this restriction into code as below:

def get_rule_minlength(grammar, rule, seen):
    return sum([get_key_minlength(grammar, k, seen) for k in rule])

def get_key_minlength(grammar, key, seen):
    if key not in grammar: return len(key)
    if key in seen: return math.inf
    return min([get_rule_minlength(grammar, r, seen | {key}) for r in grammar[key]])

# we initialize the cost. This is a global variable for the purpose of this post.

grammar = {
        "<start>": [["<E>"]],
        "<E>": [
            ["<E>", "+", "<E>"],
            ["<E>", "-", "<E>"],
            ["(", "<E>", ")"],
            ["<digits>"],
            ],
        "<digits>": [["<digits>", "<digit>"], ["<digit>"]],
        "<digit>": [[str(i)] for i in string.digits]
        }
START = '<start>'

Cost = {}
for k in grammar:
    Cost[k] = get_key_minlength(grammar, k, set())

# That is, we find the minimum expansion length of each key and store it beforehand.
# Next, we update our `explore` so that if the minimum expansion length in any
# of the potential threads is larger than the characters remaining, that thread is not
# started.
# 
# There is an absolute limit to the number of recursions in a left recursion.
# We have say `m` nonterminals in the grammar. Even if at least one nonterminal
# consumes one token, and the remaining consumes none, there cannot be more than
# m repetitions of any key in the given stack, without consuming at least one
# token. Hence, the maximum limit of recursion is `m * (1+ |s|)` where `s` is
# the input length.


def explore(current, lst, grammar):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    key = rule[0]

    if key not in grammar:
        if lst_rem == 0: return []
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), depth + 1), rule[1:])]
    else:
        max_limit = len(list(grammar.keys())) * (1 + len(lst))
        if max_limit < depth: return [] # <- changed

        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = expansion + rule[1:]
            max_readable = sum([Cost.get(r, len(r)) for r in new_rule])
            if max_readable > lst_rem: continue # <- changed
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret

# With this, we are now ready to parse any context-free language. Using the driver above:

if __name__ == '__main__':
    forking_parse('1+1+', grammar, START)

# 

if __name__ == '__main__':
    forking_parse('1+1+1', grammar, START)

# As you can see, we can successfully use left recursive grammars. Note that this is still a
# recognizer. Turning it into a parser is not very difficult, and may be handled in a future post.
# 
# The complete code is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2020-03-14-simple-contextfree-parsing.py).
# 
# **Note:** 
# I implemented it to scratch an itch, without first checking the literature about similar parsing techniques. However, now that I have implemented it, this technique seems similar to [GLL](https://github.com/djspiewak/gll-combinators#theory)). While my implmentation is 
# inefficient, a few avenues of optimization such as the standard memoization (packrat) techniques, and GSS (fairly easy to implement in that it is about how to maintain the `rule` structure as a tree with common prefix) can help the situation.
