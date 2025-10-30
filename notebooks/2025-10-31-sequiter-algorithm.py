# ---
# published: true
# title: Inferring Hierarchical Structure with Sequitur
# layout: post
# comments: true
# tags: grammars inference
# categories: post
# ---
#
# TLDR; This tutorial is a complete implementation of Sequitur algorithm
# which infers a hierarchical structure (in the form of a grammar) from a
# sequence of symbols. Such grammars are one way to achieve data
# compression of a long string.
# The Python interpreter is embedded so that you
# can work through the implementation steps.
#
# Sequitur was introduced by Craig Nevill-Manning and Ian H. Witten in 1997
# [^manning1997]. It inferrs a hierarchical structure from a sequence of
# input symbols by replacing repeated symbol sequences with nonterminal symbols
# recursively.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

# #### Prerequisites
# 
# We need the fuzzer to generate inputs to parse and also to provide some
# utilities such as conversion of regular expression to grammars, random
# sampling from grammars etc. Hence, we import all that.


# # Structure Inference

class Sequitur:
    def __init__(self):
        self.sequence = []
        self.diagrams = {}
        self.grammar = {}
        self.next_rule_id = 1
        self.grammar["<0>"] = self.sequence

# Processes the next symbol and add it to the sequence. We check for new
# diagrams when a new symbol is added.

class Sequitur(Sequitur):
    def handle_new_symbol(self, symbol):
        self.sequence.append(symbol)
        if len(self.sequence) < 2: return
        self.check_diagram(len(self.sequence) - 2)

# create a new rule
class Sequitur(Sequitur):
    def create_new_rule(self, diagram, index1, index2):
        new_rule_id = '<%s>' % self.next_rule_id
        self.next_rule_id += 1
        self.grammar[new_rule_id] = [diagram[0], diagram[1]]

        # update both locations
        self.sequence[index2:index2+2] = [new_rule_id]
        self.sequence[index1:index1+2] = [new_rule_id]
        del self.diagrams[diagram]


# Check and replace the diagram starting at the given index
class Sequitur(Sequitur):
    def check_diagram(self, index):
        if index < 0 or index +1 >= len(self.sequence): return

        diagram = (self.sequence[index], self.sequence[index+1])
        if diagram not in self.diagrams:
            self.diagrams[diagram] = index
            return
        first_occurrence_index = self.diagrams[diagram]
        # if first_occurrence_index is just one token away, e.g. aaa
        # then we can't replace.
        assert index - first_occurrence_index != 1
        self.create_new_rule(diagram, first_occurrence_index, index)
        # now check from the first occurrence again
        if first_occurrence_index > 0:
            self.check_diagram(first_occurrence_index-1)
        self.check_diagram(first_occurrence_index)
        if index > 0:
            self.check_diagram(index-1)
        self.check_diagram(index)



class Sequitur(Sequitur):
    def process(self, input_string):
        for i,c in enumerate(input_string):
            self.handle_new_symbol(c)
        self.grammar["<0>"] = self.sequence
        return self.grammar

def collapse(grammar, start):
    rule = grammar[start]
    res = []
    for k in rule:
        if (k[0],k[-1]) == ('<', '>'):
            r = collapse(grammar, k)
            res.extend(r)
        else:
            res.append(k)
    return ''.join(res)


if __name__ == '__main__':
     input_strings = [
             'abracadabra',
             "abab",
             "aaaa",
             "aaaaa",
             "x",
             "abcdef",
             "abcxabcyabc",
             "abcabcabcabc",
             "xyxyx"

     ]
     for input_string in input_strings:
         print(input_string)
         sequitur_processor = Sequitur()
         g = sequitur_processor.process(input_string)
         for k in g:
             print(k)
             print("\t", g[k])
         s = collapse(g, '<0>')
         assert input_string == s

# ## Complexity and Limitations
# 
# Time Complexity: The Sequitur algorithm is $$ O(n) $$ where n is the size of input data.
# 
# 
# ---
# [^manning1997]: Craig Nevill-Manning, Ian H. Witten, Identifying Hierarchical Structure in Sequences: A linear-time algorithm, 1997
