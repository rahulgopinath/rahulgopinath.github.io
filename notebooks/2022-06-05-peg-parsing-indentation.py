# ---
# published: true
# title: Incorporating Indentation Parsing in PEG
# layout: post
# comments: true
# tags: peg, parsing, cfg, indentation
# categories: post
# ---

# We previously [saw](/post/2022/06/04/parsing-indentation/) how to incorporate
# indentation sensitive parsing to combinatory parsers. One of the problems
# with combinatory parsers is that they can be difficult to debug. So, can we
# incorporate the indentation sensitive parsing to more standard parsers? Turns
# out, it is fairly simple to retrofit Python like parsing to
# [PEG parsers](/post/2018/09/06/peg-parsing/). (The
# [PEG parser](/post/2018/09/06/peg-parsing/) post contains the background
# information on PEG parsers.)
#
# That is, given
#
# ```
# if True:
#    if False:
#       x = 100
#       y = 200
# z = 300
# ```
# We want to parse it similar to
#
# ```
# if True: {
#    if False: {
#       x = 100;
#       y = 200;
#    }
# }
# ```
# in a `C` like language.
# As before, we start by importing our prerequisite packages.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

import simplefuzzer as F

# ## Example.
# 
# Here is the text we want to parse.
my_text = '''\
if a=b:
    if c=d:
        a=b
    c=d
c=b
'''


# ## Grammar
# We first define our grammar. Within our grammar, we use `<$indent>` and
# `<$dedent>` to wrap lines with similar indentation. We also use `<$nl>` as
# delimiters when lines have similar indentation.

grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<$nl>', '<stmts>'],
        ['<stmt>', '<$nl>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letter>', '=','<letter>']],
    '<letter>': [['a'],['b'], ['c'], ['d']],
    '<ifstmt>': [['if ', '<expr>', ':', '<block>']],
    '<expr>': [['<letter>', '=', '<letter>']],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}

# ## ipeg_parse
# Our class is initialized with the grammar. We also initialize a stack of
# indentations.

class ipeg_parse:
    def __init__(self, grammar):
        self.grammar, self.indent = grammar, [0]

# ## read_indent
# When given a line, we find the number of spaces occurring before a non-space
# character is found.

def read_indent(text, at):
    indent = 0
    while text[at:at+1] == ' ':
        indent += 1
        at += 1
    return indent, at

# Using it
if __name__ == '__main__':
    print(read_indent('  abc', 0))

# ## unify_indent
# Next, we define how to parse a nonterminal symbol. This is the area
# where we hook indentation parsing. When unifying `<$indent>`,
# we expect the text to contain a new line,
# and we also expect an increase in indentation.

class ipeg_parse(ipeg_parse):
    def unify_indent(self, text, at):
        if text[at:at+1] != '\n': return (at, None)
        indent, at_ = read_indent(text, at+1)
        if indent <= self.indent[-1]: return (at, None)
        self.indent.append(indent)
        return (at_, ('<$indent>', []))

# ## unify_dedent
# To unify a `<$dedent>` key, we simply have to pop off the current
# indentation.
class ipeg_parse(ipeg_parse):
    def unify_dedent(self, text, at):
        self.indent.pop()
        return (at, ('<$dedent>', []))
# ## unify_nl
# If the current key is `<$nl>`, then we
# expect the current text to contain a new line. Furthermore, there may also be
# a reduction in indentation.

class ipeg_parse(ipeg_parse):
    def unify_nl(self, text, at):
        if text[at:at+1] != '\n': return (at, None)
        indent, at_ = read_indent(text, at+1)
        assert indent <= self.indent[-1]
        return (at_, ('<$nl>', []))

# ## unify_key
# With this, we are ready to define the main PEG parser.
# The rest of the implementation is very similar to
# [PEG parser](/post/2018/09/06/peg-parsing/) that we discussed before.

class ipeg_parse(ipeg_parse):
    def unify_key(self, key, text, at=0):
        if key == '<$nl>': return self.unify_nl(text, at)
        elif key == '<$indent>': return self.unify_indent(text, at)
        elif key == '<$dedent>': return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at)
            if res is not None: return l, (key, res)
        return (0, None)

# ## unify_rule
# We add some logging to unify_rule to see how the matching takes place.
# Otherwise it is exactly same as the original PEG parser.
class ipeg_parse(ipeg_parse):
    def unify_rule(self, parts, text, tfrom):
        results = []
        for part in parts:
            tfrom, res = self.unify_key(part, text, tfrom)
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

# display

def get_children(node):
    if node[0] in ['<$indent>', '<$dedent>', '<$nl>']: return []
    return F.get_children(node)

# We can now test it out
if __name__ == '__main__':
    v, res = ipeg_parse(grammar).unify_key('<start>', my_text)
    print(len(my_text), '<>', v)
    F.display_tree(res, get_children=get_children)

# ## Visualization
# Visualization can be of use when trying to debug grammars. So, here we add a
# bit more log output.

class ipeg_parse_log(ipeg_parse):
    def __init__(self, grammar, log):
        self.grammar, self.indent, self._log = grammar, [0], log

    def unify_rule(self, parts, text, tfrom, _indent):
        results = []
        for part in parts:
            if self._log:
                print(' '*_indent, part, '=>', repr(text[tfrom:]))
            tfrom_, res = self.unify_key(part, text, tfrom, _indent+1)
            if self._log:
                print(' '*_indent, part, '=>', repr(text[tfrom:tfrom_]), "|",
                        repr(text[tfrom:]), res is not None)
            tfrom = tfrom_
            if res is None: return tfrom, None
            results.append(res)
        return tfrom, results

    def unify_key(self, key, text, at=0, _indent=0):
        if key == '<$nl>': return self.unify_nl(text, at)
        elif key == '<$indent>': return self.unify_indent(text, at)
        elif key == '<$dedent>': return self.unify_dedent(text, at)
        if key not in self.grammar:
            return (at + len(key), (key, [])) if text[at:].startswith(key) else (at, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, at, _indent)
            if res is not None: return l, (key, res)
        return (0, None)

# test with visualization
my_text = """
if a=b:
    a=b
c=d
"""
# Using
if __name__ == '__main__':
    v, res = ipeg_parse_log(grammar, log=True).unify_key('<start>', my_text)
    print(len(my_text), '<>', v)

