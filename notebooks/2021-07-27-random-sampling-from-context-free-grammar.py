# ---
# published: true
# title: Random Sampling of Strings from Context-Free Grammar
# layout: post
# comments: true
# tags: pipes, python
# categories: post
# ---
# 
# In the previous [post](/post/2019/05/28/simplefuzzer-01/) I talked about
# how to generate input strings from any given context-free grammar. While that
# algorithm is quite useful for fuzzing, one of the problems with that algorithm
# is that the strings produced from that grammar is skewed toward shallow strings.
# 
# For example, consider this grammar:

G = {
    "<start>" : [["<digits>"]],
    "<digits>" : [["<digit>", "<digits>"],
        ["<digit>"]],
    "<digit>" : [[str(i)] for i in range(10)]
}

# To generate inputs, let us load the limit fuzzer from the previous post.

import sys, imp

def make_module(modulesource, sourcestr, modname):
    codeobj = compile(modulesource, sourcestr, 'exec')
    newmodule = imp.new_module(modname)
    exec(codeobj, newmodule.__dict__)
    return newmodule

def import_file(name, location):
    if "pyodide" in sys.modules:
        import pyodide
        github_repo = 'https://raw.githubusercontent.com/'
        my_repo =  'rahulgopinath/rahulgopinath.github.io'
        module_loc = github_repo + my_repo + '/master/notebooks/%s' % location
        module_str = pyodide.open_url(module_loc).getvalue()
    else:
        module_loc = './notebooks/%s' % location
        with open(module_loc) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# ## The Fuzzer

fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')

# The generated strings (which generate random integers) are as follows

if __name__ == '__main__':
    gf = fuzzer.LimitFuzzer(G)
    for i in range(10):
        print(gf.fuzz('<start>'))

# As you can see, there are more single digits in the output than
# longer integers. Almost half of the generated strings are single character.
# If we modify our grammar as below

G2 = {
    "<start>" : [["<digits>"]],
    "<digits>" : [["<digit>", "<digits>"],
                  ["<digit>"],
                  ["<threedigits>"],
                  ],
    "<digit>" : [[str(i)] for i in range(10)],
    "<threedigits>" : [[str(i) + str(j) + str(k)] for i in range(2) for j in range(2) for k in range(2)]
}

# and run it again

if __name__ == '__main__':
    gf = fuzzer.LimitFuzzer(G2)
    for i in range(10):
        print(gf.fuzz('<start>'))

# you will notice a lot more three digit wide binary numbers are produced. In
# fact, now, more than one third of the generated strings are likely to be three
# digits. This is because of the way the grammar is written. That is, there are
# three possible expansions of the `<digits>` nonterminal, and our fuzzer
# chooses one of the expansions with equal probability. This leads to the skew
# in the inputs we see above.
#
# This is interesting, but why is it a problem for practitioners? Consider these
# two grammars.
E1 = {
 '<start>': [['<E>']],
 '<E>': [['<F>', '*', '<E>'],
         ['<F>', '/', '<E>'],
         ['<F>']],
 '<F>': [['<T>', '+', '<F>'],
         ['<T>', '-', '<F>'],
         ['<T>']],
 '<T>': [['(', '<E>', ')'],
         ['<D>']],
 '<D>': [['0'], ['1']]
}
E2 = {
 '<start>': [['<E>']],
 '<E>': [['<T>', '+', '<E>'],
            ['<T>', '-', '<E>'],
            ['<T>']],
 '<T>': [['<F>', '*', '<T>'],
            ['<F>', '/', '<T>'],
            ['<F>']],
 '<F>': [['(', '<E>', ')'],
         ['<D>']],
 '<D>': [['0'], ['1']]
} 

# Now, let us look at the generated strings. The first:
if __name__ == '__main__':
    print("E1")
    e1f = fuzzer.LimitFuzzer(E1)
    for i in range(10):
        print(e1f.fuzz('<start>', max_depth=1))

# And the second:

if __name__ == '__main__':
    print("E2")
    e2f = fuzzer.LimitFuzzer(E2)
    for i in range(10):
        print(e2f.fuzz('<start>', max_depth=1))

# Notice that both grammars describe exactly the same language, but the
# first one has a higher proportion of multiplications and divisions while the
# second one has a higher proportion of additions and subtractions. This means
# that the effectiveness of our fuzzers is determined to a large extent by the
# way the context-free grammar is written. 
#
# Another case is when one wants to compare the agreement between two grammars.
# I talked about this [before](/post/2021/01/28/grammar-inference/).
# As you can see from the above cases, the same language can be described by
# different grammars, and it is undecidable in general whether two context-free
# grammars describe the same language [^barhilel1961on]. So, we will have to
# go for statistical means.

# To start with, we need to be able to randomly sample from the strings that can
# be produced from the grammar. So, the minimal requirement is as follows:
# 
# * We need to be able to randomly sample a string that can be generated from
#   the grammar.
#
# To make this happen, let us split this into two simpler requirements:
# 
# * We can find the number of strings of a given size that can be produced from
#   the grammar.
# 
# * We can enumerate the strings that can be produced from the grammar, and
#   pick a specific string given its index in the enumeration.
#
# Once we have both these abilities, then we can combine them to provide random
# sampling of derived strings. So, let us see how to achieve that.
#
# ## A Naive Implementation.
# 
# ### Counting the number of strings
# 
# Let us first implement a way to count the number of strings that can be
# possibly generated.
# 
# We first implement `key_get_num_strings()` to
# count the number of strings of a given size `l_str` generated by a token.
# For finding the number we first check if the given token is a `terminal`
# symbol. If it is, then there is only one choice. That symbol is the string.
# The constraint is that the length of the string should be as given by `l_str`.
# if not, the total number of strings that can be generated from this token is
# the total number of strings we can generated from each individual expansion.

def key_get_num_strings(key, grammar, l_str):
    if not fuzzer.is_nonterminal(key):
        return 1 if l_str == len(key) else 0
    s = 0
    rules = grammar[key]
    for rule in rules:
        s += rule_get_num_strings(rule, grammar, l_str) 
    return s

# Next, we implement `rule_get_num_strings()` which counts the number of strings
# of given size `l_str` that can be generated by a rule (an expansion of a nonterminal).
# Here, we treat each rule as a head followed by a tail. The token is the first
# symbol in the rule. The idea is that, the total number of strings that can be
# generated from a rule is the multiplication of the number of strings that can
# be generated from the head by the total strings that can be generated by the
# tail.
# 
# The complication is that we want to generate a specific size string. So, we
# split that size (`l_str`) between the head and tail and count strings
# generated by each possible split.

def rule_get_num_strings(rule, grammar, l_str):
    if not rule: return 0

    token, *tail = rule
    if not tail:
        return key_get_num_strings(token, grammar, l_str)

    sum_rule = 0
    for l_str_x in range(1, l_str+1): # inclusive
        s_ = key_get_num_strings(token, grammar, l_str_x)
        if s_ == 0: continue

        rem = rule_get_num_strings(tail, grammar, l_str - l_str_x)
        sum_rule += s_ * rem
    return sum_rule

# Using it.

if __name__ == '__main__':
    count = key_get_num_strings('<start>', G, 2)
    print("len:", count)

# ### Generation of strings
# 
# Let us next implement a way to generate all strings of a given
# size. Here, in `get_strings_of_length_in_definition()`, we pass in the key,
# the grammar and the length of the string expected.
# 
# For generating a string from a key, we first check if it is a `terminal`
# symbol. If it is, then there is only one choice. That symbol is the string.
# The constraint is that the length of the string should be as given by `l_str`.
# if not, then we find all the expansion rules of the corresponding definition
# and generate strings from each expansion of the given size `l_str`; the
# concatenation of which is the required string list.

def get_strings_of_length_in_definition(key, grammar, l_str):
    if not fuzzer.is_nonterminal(key):
        if l_str == len(key):
            return [key]
        else:
            return []
    # number strings in definition = sum of number of strings in rules
    rules = grammar[key]
    s = []
    for rule in rules:
        s_ = get_strings_of_length_in_rule(rule, grammar, l_str)
        s.extend(s_)
    return s

# Next, we come to the rule implementation given by `get_strings_of_length_in_rule()`
# Here, we treat each rule as a head followed by a tail. The token is the first
# symbol in the rule. The idea is that, the strings that are generated from this
# rule will have one of the strings generated from the token followed by one of
# the strings generated from the rest of the rule. This also provides us with the
# base case. If the rule is empty, we are done.
# if it is not the base case, then we first extract the strings from the token
# head, then extract the strings from the tail, and concatenate them pairwise.
# 
# The complication here is the number of characters expected in the string. We
# can divide the number of characters --- `l_str` between the head and the tail.
# That is, if the string from head takes up `x` characters, then we can only
# have `l_str - x` characters in the tail. To handle this, we produce a loop
# with all possible splits between head and tail. Of course not all possible
# splits may be satisfiable. Whenever we detect an impossible split --- by
# noticing that `s_` is empty, we skip the loop.

def get_strings_of_length_in_rule(rule, grammar, l_str):
    if not rule: return []

    token, *tail = rule
    if not tail:
        return get_strings_of_length_in_definition(token, grammar, l_str)

    sum_rule = []
    for l_str_x in range(1,l_str+1): # inclusive
        s_ = get_strings_of_length_in_definition(token, grammar, l_str_x)
        if not s_: continue

        rem = get_strings_of_length_in_rule(tail, grammar, l_str - l_str_x)
        for s1 in s_:
            for sr in rem:
                sum_rule.append(s1 + sr)
    return sum_rule

# Using it.

if __name__ == '__main__':
    strings = get_strings_of_length_in_definition('<start>', G, 2)
    print("len:", len(strings))
    print(strings)

# The problem with these implementations is tht it is horribly naive. Each call
# recomputes the wohle set of strings or the count again and again. However,
# many nonterminals are reused again and again, which means that we should be
# sharing the results. Let us see how we can memoize the resuls of these calls.
# 
# ## A Memoized Implementation.
# 
# ### Counting the number of strings
#
# We first define a data structure to keep the key nodes. Such nodes help us to
# identify the corresponding rules of the given key that generates strings of
# `l_str` size.

class KeyNode:
    def __init__(self, token, l_str, count, rules):
        self.token = token
        self.l_str = l_str
        self.count = count
        self.rules = rules

    def __str__(self):
        return "key: %s <%d> count:%d" % (repr(self.token), self.l_str, self.count)

    def __repr__(self):
        return "key: %s <%d> count:%d" % (repr(self.token), self.l_str, self.count)

# We also define a data structure to keep the rule nodes. Such rules contain
# both the head `token` as well as the `tail`, the `l_str` as well as the count

class RuleNode:
    def __init__(self, key, tail, l_str, count):
        self.key = key
        self.tail = tail
        self.l_str = l_str
        self.count = count
        assert count

    def __str__(self):
        return "head: %s tail: (%s) <%d> count:%d" % (repr(self.key.token), repr(self.tail), self.l_str, self.count)

    def __repr__(self):
        return "head: %s tail: (%s) <%d> count:%d" % (repr(self.key.token), repr(self.tail), self.l_str, self.count)

# globals

rule_strs = { }

key_strs = { }

EmptyKey = KeyNode(token=None, l_str=None, count=0, rules = None)

# ### Populating the linked data structure.
# 
# This follows the same skeleton as our previous functions. Firt the keys

def key_get_def(key, grammar, l_str):
    if (key, l_str) in key_strs: return key_strs[(key, l_str)]

    if key not in grammar:
        if l_str == len(key):
            key_strs[(key, l_str)] = KeyNode(token=key, l_str=l_str, count=1, rules = [])
            return key_strs[(key, l_str)]
        else:
            key_strs[(key, l_str)] = EmptyKey
            return key_strs[(key, l_str)]
    # number strings in definition = sum of number of strings in rules
    rules = grammar[key]
    s = []
    count = 0
    for rule in rules:
        s_s = rules_get_def(rule, grammar, l_str) # returns RuleNode (should it return array?)
        for s_ in s_s:
            assert s_.count
            count += s_.count
            s.append(s_)
    key_strs[(key, l_str)] = KeyNode(token=key, l_str=l_str, count=count, rules = s)
    return key_strs[(key, l_str)]

# Now the rules.

def rules_get_def(rule_, grammar, l_str):
    rule = tuple(rule_)
    if not rule: return []
    if (rule, l_str) in rule_strs: return rule_strs[(rule, l_str)]

    token, *tail = rule
    if not tail:
        s_ = key_get_def(token, grammar, l_str)
        if not s_.count: return []
        return [RuleNode(key=s_, tail=[], l_str=l_str, count=s_.count)]

    sum_rule = []
    count = 0
    for l_str_x in range(1, l_str+1):
        s_ = key_get_def(token, grammar, l_str_x)
        if not s_.count: continue

        rem = rules_get_def(tail, grammar, l_str - l_str_x)
        count_ = 0
        for r in rem:
            count_ += s_.count * r.count

        if count_:
            count += count_
            rn = RuleNode(key=s_, tail=rem, l_str=l_str_x, count=count_)
            sum_rule.append(rn)
    rule_strs[(rule, l_str)] = sum_rule
    return rule_strs[(rule, l_str)]

# Using it.

if __name__ == '__main__':
    key_node = key_get_def('<start>', G, 2)
    print("len:", key_node.count)

# We can ofcourse extract the same things from this data structure
# 
# ### Count

def key_get_count(key_node):
    if not key_node.rules: return 1
    slen = 0
    for rule in key_node.rules:
        s = rule_get_count(rule)
        slen += s
    return slen

def rule_get_count(rule_node):
    slen = 0
    s_k = key_get_count(rule_node.key)
    for rule in rule_node.tail:
        s_t = rule_get_count(rule)
        slen = s_k * s_t
    if not rule_node.tail:
        slen += s_k
    return slen

# Using it.

if __name__ == '__main__':
    count = key_get_count(key_node)
    print("len:", count)

# ### Strings

def key_extract_strings(key_node):
    # key node has a set of rules
    if not key_node.rules: return [key_node.token]
    strings = []
    for rule in key_node.rules:
        s = rule_extract_strings(rule)
        if s:
            strings.extend(s)
    return strings

def rule_extract_strings(rule_node):
    strings = []
    s_k = key_extract_strings(rule_node.key)
    for rule in rule_node.tail:
        s_t = rule_extract_strings(rule)
        for s1 in s_k:
            for s2 in s_t:
                strings.append(s1 + s2)
    if not rule_node.tail:
        strings.extend(s_k)
    return strings

# Using it.

if __name__ == '__main__':
    strings = key_extract_strings(key_node)
    print("len:", len(strings))

# ### Random Access
# 
# But more usefully, we can now use it to randomly access any particular string

def key_get_string_at(key_node, at):
    assert at < key_node.count
    if not key_node.rules: return key_node.token
    at_ = 0
    for rule in key_node.rules:
        if at < (at_ + rule.count):
            return rule_get_string_at(rule, at - at_)
        else:
            at_ += rule.count
    return None

def rule_get_string_at(rule_node, at):
    assert at < rule_node.count
    if not rule_node.tail:
        s_k = key_get_string_at(rule_node.key, at)
        return s_k

    len_s_k = rule_node.key.count
    at_ = 0
    for rule in rule_node.tail:
        for i in range(len_s_k):
            if at < (at_ + rule.count):
                s_k = key_get_string_at(rule_node.key, i)
                return s_k + rule_get_string_at(rule, at - at_)
            else:
                at_ += rule.count
    return None

# Using it.

if __name__ == '__main__':
    at = 3
    strings = key_extract_strings(key_node)
    print("strting[%d]" % at, repr(strings[at]))

    string = key_get_string_at(key_node, at)
    print(repr(string))

# ### Random Sampling
# 
# Once we have random access of a given string, we can turn it to random
# sampling. 

import random

# 

if __name__ == '__main__':
    key_node_g = key_get_def('<start>', E1, 5)
    print(key_node_g.count)
    at = random.randint(0,key_node_g.count)
    print('at:', at)
    strings = key_extract_strings(key_node_g)
    print("strting[%d]" % at, repr(strings[at]))
    string = key_get_string_at(key_node_g, at)
    print(repr(string))

# This is random sampling from restricted set --- the set of derivation strings 
# of a given length. How do we extend this to lengths up to a given length?
# The idea is that for generating strings of length up to `n`, we produce and
# use nonterminals that generate strings of length up to `n-x` where `x` is the
# length of first terminals in expansions. This means that we can build the
# `key_node` data structures recursively from 1 to `n`, and most of the parts
# will be shared between the `key_node` data structures of different lengths.

class RandomSampleCFG:
    def __init__(self, grammar):
        self.grammar = grammar
        self.rule_strs = { }
        self.key_strs = { }
        self.EmptyKey = KeyNode(token=None, l_str=None, count=0, rules = None)
        self.ds = {}

    def key_get_def(self, key, l_str):
        if (key, l_str) in self.key_strs: return self.key_strs[(key, l_str)]

        if key not in self.grammar:
            if l_str == len(key):
                self.key_strs[(key, l_str)] = KeyNode(token=key, l_str=l_str, count=1, rules = [])
                return self.key_strs[(key, l_str)]
            else:
                self.key_strs[(key, l_str)] = EmptyKey
                return self.key_strs[(key, l_str)]
        # number strings in definition = sum of number of strings in rules
        rules = self.grammar[key]
        s = []
        count = 0
        for rule in rules:
            s_s = self.rules_get_def(rule, l_str) # returns RuleNode (should it return array?)
            for s_ in s_s:
                assert s_.count
                count += s_.count
                s.append(s_)
        self.key_strs[(key, l_str)] = KeyNode(token=key, l_str=l_str, count=count, rules = s)
        return self.key_strs[(key, l_str)]

    # Now the rules.

    def rules_get_def(self, rule_, l_str):
        rule = tuple(rule_)
        if not rule: return []
        if (rule, l_str) in rule_strs: return rule_strs[(rule, l_str)]

        token, *tail = rule
        if not tail:
            s_ = self.key_get_def(token, l_str)
            if not s_.count: return []
            return [RuleNode(key=s_, tail=[], l_str=l_str, count=s_.count)]

        sum_rule = []
        count = 0
        for l_str_x in range(1, l_str+1):
            s_ = self.key_get_def(token, l_str_x)
            if not s_.count: continue

            rem = self.rules_get_def(tail, l_str - l_str_x)
            count_ = 0
            for r in rem:
                count_ += s_.count * r.count

            if count_:
                count += count_
                rn = RuleNode(key=s_, tail=rem, l_str=l_str_x, count=count_)
                sum_rule.append(rn)
        rule_strs[(rule, l_str)] = sum_rule
        return rule_strs[(rule, l_str)]

    def key_get_string_at(self, key_node, at):
        assert at < key_node.count
        if not key_node.rules: return key_node.token
        at_ = 0
        for rule in key_node.rules:
            if at < (at_ + rule.count):
                return self.rule_get_string_at(rule, at - at_)
            else:
                at_ += rule.count
        assert False

    def rule_get_string_at(self, rule_node, at):
        assert at < rule_node.count
        if not rule_node.tail:
            s_k = self.key_get_string_at(rule_node.key, at)
            return s_k

        len_s_k = rule_node.key.count
        at_ = 0
        for rule in rule_node.tail:
            for i in range(len_s_k):
                if at < (at_ + rule.count):
                    s_k = self.key_get_string_at(rule_node.key, i)
                    return s_k + self.rule_get_string_at(rule, at - at_)
                else:
                    at_ += rule.count
        assert False

    # produce a shared key forest.
    def produce_shared_forest(self, start, upto):
        for length in range(1, upto+1):
            if length in self.ds: continue
            key_node_g = self.key_get_def(start, length)
            count = key_node_g.count
            self.ds[length] = key_node_g
        return self.ds

    # randomly sample from 1 up to `n` length.
    def random_sample(self, start, n):
        assert n > 0
        if n not in self.ds:
            self.produce_shared_forest(start, n)
        total_count = sum([self.ds[l].count for l in self.ds if l <= n])
        choice = random.randint(0, total_count-1)
        my_choice = choice
        for i in range(1, n+1):
            c = self.ds[i].count
            if my_choice >= c:
                my_choice -= c
            else:
                return choice, self.key_get_string_at(self.ds[i], my_choice)
        assert False

# Using it.

if __name__ == '__main__':
    rscfg = RandomSampleCFG(E1)
    max_len = 10
    rscfg.produce_shared_forest('<start>', max_len)
    for i in range(10):
        at = random.randint(1, max_len) # at least 1 length
        v, string = rscfg.random_sample('<start>', at)
        print("mystring:", repr(string), "at:", v, "upto:", at)

# There are a few limitations to this algorithm. The first is that it does
# not take into account epsilons -- that is empty derivations. It can be
# argued that it is not that big of a concern since any context-free grammar
# can be made epsilon free. The next limitation is bigger. This implementation
# does not take into account ambiguity in grammar where multiple derivation
# trees can result in the same string. This means that such strings will be
# more likely to appear than other strings.
# While there are a number of papers [^madhavan2015automating] [^mckenzie1997the] [^mckenzie1997generating] [^mairson1994generating] [^hickey1983uniform] that tackle
# the issue of statistical sampling, with better runtime and space
# characteristics, we are not aware of any that fixes both issues
# (Gore et al.[^gore1997a] is notable for showing an _almost uniform random
# sampling_ result).
# Bertoni et al. shows[^bertoni1991the] shows that for some inherrently
# ambiguous languages, the problem becomes intractable.
# 
# The code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-07-27-random-sampling-from-context-free-grammar.py).

# # References
# 
# [^barhilel1961on]: Bar-Hillel, Yehoshua, Micha Perles, and Eli Shamir. "On formal properties of simple phrase structure grammars." STUF-Language Typology and Universals 14.1-4 (1961): 143-172.
#
# [^madhavan2015automating]: Madhavan, Ravichandhran, et al. "Automating grammar comparison." Proceedings of the 2015 ACM SIGPLAN International Conference on Object-Oriented Programming, Systems, Languages, and Applications. 2015.
# 
# [^bertoni1991the]: Bertoni, Alberto, Massimiliano Goldwurm, and Nicoletta Sabadini. "The complexity of computing the number of strings of given length in context-free languages." Theoretical Computer Science 86.2 (1991): 325-342.
#
# [^mckenzie1997the]: McKenzie, Bruce. "The Generation of Strings from a CFG using a Functional Language." (1997).
#
# [^mckenzie1997generating]: McKenzie, Bruce. "Generating strings at random from a context free grammar." (1997).
# 
# [^hickey1983uniform]: Hickey, Timothy, and Jacques Cohen. "Uniform random generation of strings in a context-free language." SIAM Journal on Computing 12.4 (1983): 645-655.
#
# [^mairson1994generating]: Harry G. Mairson. Generating words in a context-free language uniformly at random. Information Processing Letters, 49(2):95{99, 28 January 1994
#
# [^gore1997a]: Gore, Vivek, et al. "A quasi-polynomial-time algorithm for sampling words from a context-free language." Information and Computation 134.1 (1997): 59-74.
