---
published: true
title: Simple Parser For Context Free Languages with Forking Stacks
layout: post
comments: true
tags: combinators, parsing, cfg
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.8/';</script>
<script src="/resources/pyodide/full/3.8/pyodide.js"></script>
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/pyodide/js/env/editor.js" type="text/javascript"></script>

**Important:** [Pyodide](https://pyodide.readthedocs.io/en/latest/) takes time to initialize.
Initialization completion is indicated by a red border around *Run all* button.
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
We [previously](/post/2020/03/02/combinatory-parsing/) saw how to parse simple context-free
languages using combinatory parsers. In another [post](/post/2018/09/06/peg-parsing/), I had
also detailed how one can do a simple PEG and even a context-free parser. However, these
parsers are unsatisfying in some sense. They do not handle left recursion correctly.

The essential idea in those is to make use of the Python stack for recursive descent style 
parsing. Using the language stack however comes with the restriction that one is restricted 
to a depth first strategy. One cannot suspend an exploration when one feels like it, and 
resume it later. How much does it take to implement left recursion? My [post](/post/2018/09/06/peg-parsing/)
on CFG parses hints at a way. What we need to do is to handle the stack on our own, and do 
a breadth first search search of the possible parses.

That is, we consider multiple parses at once (as multiple threads), and prioritize the most
optimistic parsing scenarios so that they get examined first.

We use the following heuristic: The threads that are farthest along in parsing (in terms
of number of characters parsed) gets the highest priority. Next, the threads where the
first item is the shallowest gets the highest priority.

Here is a simple implementation. It takes the input chars (`lst`), the starting `key` and
the `grammar`. Then, it extracts the most promising parse thread, *explores* its first element,
which may produce a new set of threads that represent alternative parse directions.

<!--
############
import heapq as H
import math
import string

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import heapq as H
import math
import string
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Our grammar is

<!--
############
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

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
        &quot;&lt;start&gt;&quot;: [[&quot;&lt;E&gt;&quot;]],
        &quot;&lt;E&gt;&quot;: [
            [&quot;&lt;E&gt;&quot;, &quot;+&quot;, &quot;&lt;E&gt;&quot;],
            [&quot;&lt;E&gt;&quot;, &quot;-&quot;, &quot;&lt;E&gt;&quot;],
            [&quot;(&quot;, &quot;&lt;E&gt;&quot;, &quot;)&quot;],
            [&quot;&lt;digits&gt;&quot;],
            ],
        &quot;&lt;digits&gt;&quot;: [[&quot;&lt;digits&gt;&quot;, &quot;&lt;digit&gt;&quot;], [&quot;&lt;digit&gt;&quot;]],
        &quot;&lt;digit&gt;&quot;: [[str(i)] for i in string.digits]
        }
START = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
def match(lst, key, grammar):
    queue = [((len(lst), 0), [(0, key)])]
    while queue:
        current = H.heappop(queue)
        rlst = explore(current, lst)
        for item in rlst:
            (lst_rem, _depth), rule = item
            lst_idx = len(lst) - lst_rem
            if lst_idx == len(lst):
                if not rule:
                    yield 'parsed: ' + str(lst_idx)
                else:
                    # (check for epsilons)
                    H.heappush(queue, item)
            else:
                if not rule: # incomplete parse
                    continue
                else:
                    H.heappush(queue, item)
############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def match(lst, key, grammar):
    queue = [((len(lst), 0), [(0, key)])]
    while queue:
        current = H.heappop(queue)
        rlst = explore(current, lst)
        for item in rlst:
            (lst_rem, _depth), rule = item
            lst_idx = len(lst) - lst_rem
            if lst_idx == len(lst):
                if not rule:
                    yield &#x27;parsed: &#x27; + str(lst_idx)
                else:
                    # (check for epsilons)
                    H.heappush(queue, item)
            else:
                if not rule: # incomplete parse
                    continue
                else:
                    H.heappush(queue, item)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The `explore()` method is fairly simple. It checks if the given element is a terminal or
a nonterminal. If it is a terminal, it is checked for a match, and if matched, the current
parsing point is updated, and returned. If not a match, the current thread is discarded.

If the gievn element is a nonterminal, then the parsing can proceed in any of the possible
expansions of the nonterminal. So, the parsing thread is split into as many new threads, and
the nonterminal is replaced with its particular expansion in each of the thread, and the
new threads are returned.

<!--
############
def explore(current, lst):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    depth, key = rule[0]

    if key not in grammar:
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), math.inf), rule[1:])]
    else:
        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = [(depth + 1, e) for e in expansion] + rule[1:]
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def explore(current, lst):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    depth, key = rule[0]

    if key not in grammar:
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), math.inf), rule[1:])]
    else:
        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = [(depth + 1, e) for e in expansion] + rule[1:]
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
The driver would be

<!--
############
def forking_parse(arg, grammar, start):
    for x in match(list(arg), start, grammar):
        print(x)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def forking_parse(arg, grammar, start):
    for x in match(list(arg), start, grammar):
        print(x)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
While this can certainly handle left recursion, there is a new problem. The issue is that
in the case of left recursion, and an incomplete prefix, the threads simply multiply, with
out any means of actually parsing the input. 

That is, given the usual grammar:
and the input `1+`, the `<E>` will keep getting expanded again and again generating
new threads. So the parser will never terminate.

So, what we need is a way to discard invalid potential parses immediately. In our
case, we can see that if you have reached the end of `1+` where there are no more characters
to parse, we no longer can accept an expansion that has even a single terminal symbol that
is non empty. We can make this restriction into code as below:

<!--
############
def get_rule_minlength(grammar, rule, seen):
    return sum([get_key_minlength(grammar, k, seen) for k in rule])

def get_key_minlength(grammar, key, seen):
    if key not in grammar: return len(key)
    if key in seen: return math.inf
    return min([get_rule_minlength(grammar, r, seen | {key}) for r in grammar[key]])

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def get_rule_minlength(grammar, rule, seen):
    return sum([get_key_minlength(grammar, k, seen) for k in rule])

def get_key_minlength(grammar, key, seen):
    if key not in grammar: return len(key)
    if key in seen: return math.inf
    return min([get_rule_minlength(grammar, r, seen | {key}) for r in grammar[key]])
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
we initialize the cost. This is a global variable for the purpose of this post.

<!--
############
cost = {}
for k in grammar:
    cost[k] = get_key_minlength(grammar, k, set())

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
cost = {}
for k in grammar:
    cost[k] = get_key_minlength(grammar, k, set())
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
That is, we find the minimum expansion length of each key and store it beforehand.
Next, we update our `explore` so that if the minimum expansion length in any
of the potential threads is larger than the characters remaining, that thread is not
started.

<!--
############
def explore(current, lst):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    depth, key = rule[0]

    if key not in grammar:
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), math.inf), rule[1:])]
    else:
        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = [(depth + 1, e) for e in expansion] + rule[1:]
            if sum([cost.get(r, len(r)) for d,r in new_rule]) > lst_rem: continue # <-- changed
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
def explore(current, lst):
    (lst_rem, depth), rule = current
    lst_idx = len(lst) - lst_rem
    depth, key = rule[0]

    if key not in grammar:
        if key != lst[lst_idx]:
            return []
        else:
            return [((lst_rem - len(key), math.inf), rule[1:])]
    else:
        expansions = grammar[key]
        ret = []
        for expansion in expansions:
            new_rule = [(depth + 1, e) for e in expansion] + rule[1:]
            if sum([cost.get(r, len(r)) for d,r in new_rule]) &gt; lst_rem: continue # &lt;-- changed
            ret.append(((lst_rem, depth + 1), new_rule))
        return ret
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
With this, we are now ready to parse any context-free language. Using the driver above:

<!--
############
forking_parse('1+1+', grammar, START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
forking_parse(&#x27;1+1+&#x27;, grammar, START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>


<!--
############
forking_parse('1+1+1', grammar, START)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
forking_parse(&#x27;1+1+1&#x27;, grammar, START)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As you can see, we can successfully use left recursive grammars. Note that this is still a
recognizer. Turning it into a parser is not very difficult, and may be handled in a future post.

The complete code is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2020-03-14-simple-contextfree-parsing.py).

**Note:** 
I implemented it to scratch an itch, without first checking the literature about similar parsing techniques. However, now that I have implemented it, this technique seems similar to [GLL](https://github.com/djspiewak/gll-combinators#theory)). While my implmentation is 
inefficient, a few avenues of optimization such as the standard memoization (packrat) techniques, and GSS (fairly easy to implement in that it is about how to maintain the `rule` structure as a tree with common prefix) can help the situation.

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
