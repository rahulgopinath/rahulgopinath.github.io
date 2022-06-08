# ---
# published: true
# title: Incorporating Indentation Parsing in Standard Parsers -- PEG
# layout: post
# comments: true
# tags: peg, parsing, cfg, indentation
# categories: post
# ---

# We previously [saw](/post/2022/06/04/parsing-indentation/) how to incorporate
# indentation sensitive parsing to combinatory parsers. There were two things
# that made that solution somewhat unsatisfactory. The first is that we had to
# use a lexer first, and generate lexical tokens before we could actually
# parse. This is unsatisfactory because it forces us to deal with two different
# kinds of grammars -- the lexical grammar of tokens and the parsing grammar.
# Given that we have reasonable complete grammar parsers such as
# [PEG parser](/post/2018/09/06/peg-parsing/) and the [Earley
# parser](/post/2021/02/06/earley-parsing/), it would be nicer if we can reuse
# these parsers somehow. The second problem is that
# combinatory parsers can be difficult to debug.
# 
# So, can we incorporate the indentation sensitive parsing to more standard
# parsers? Turns out, it is fairly simple to retrofit Python like parsing to
# standard grammar parsers. In this post we will see how to do that for
# [PEG parsers](/post/2018/09/06/peg-parsing/). (The
# [PEG parser post](/post/2018/09/06/peg-parsing/) post contains the background
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
# z = 300;
# ```
# in a `C` like language.
# As before, we start by importing our prerequisite packages.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl

import simplefuzzer as F

# ## Delimited Parser
# We first define our grammar.
import string
e_grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', ';', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letters>', '=','<expr>']],
    '<letter>': [[c] for c in string.ascii_letters],
    '<digit>': [[c] for c in string.digits],
    '<letters>': [
        ['<letter>', '<letters>'],
        ['<letter>']],
    '<digits>': [
        ['<digit>', '<digits>'],
        ['<digit>']],
    '<ifstmt>': [['if', '<expr>', '<block>']],
    '<expr>': [
        ['(', '<expr>', '==', '<expr>', ')'],
        ['(', '<expr>', '!=', '<expr>', ')'],
        ['<digits>'],
        ['<letters>']
        ],
    '<block>': [['{','<stmts>', '}']]
}

# ### Text
# We want a stream of text that we can manipulate where needed. This stream
# will allow us to control our parsing.

class Text:
    def __init__(self, text, at=0):
        self.text, self.at = text, at

    def _match(self, t):
        return self.text[self.at:self.at+len(t)] == t

    def advance(self, t):
        if self._match(t):
            return Text(self.text, self.at + len(t))
        else:
            return None

    def __repr__(self):
        return repr(self.text[:self.at]+ '|' +self.text[self.at:])

# Next, we modify our PEG parser so that we can use the text stream instead of
# the array.
# 
# ### PEG
class peg_parser:
    def __init__(self, grammar):
        self.grammar = grammar

    def parse(self, key, text):
        return self.unify_key(key, Text(text))

    def unify_key(self, key, text):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return v, (key, [])
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text):
        results = []
        for part in parts:
            text, res = self.unify_key(part, text)
            if res is None: return text, None
            results.append(res)
        return text, results

# Using
if __name__ == '__main__':
    my_text = 'if(a==1){x=10}'
    v, res = peg_parser(e_grammar).parse('<start>', my_text)
    print(len(my_text), '<>', v.at)
    F.display_tree(res)

# It is often useful to understand the parser actions. Hence, we also define
# a parse visualizer as follows.

class peg_parser_visual(peg_parser):
    def __init__(self, grammar, loginit=False, logfalse=False):
        self.grammar = grammar
        self.loginit = loginit
        self.logfalse = logfalse

    def log(self, depth, *args):
        print(' '*depth, *args)

    def unify_key(self, key, text, _stackdepth=0):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return (v, (key, []))
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, _stackdepth+1)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text, _stackdepth):
        results = []
        text_ = text
        for part in parts:
            if self.loginit:
                self.log(_stackdepth,' ', part, '=>', repr(text))
            text_, res = self.unify_key(part, text_, _stackdepth)
            if res is not None:
                self.log(_stackdepth, part, '#', '=>', repr(text_))
            elif self.logfalse:
                self.log(_stackdepth, part, '_', '=>', repr(text_))
            if res is None: return text, None
            results.append(res)
        return text_, results

    def parse(self, key, text):
        return self.unify_key(key, Text(text), 0)

# Using
if __name__ == '__main__':
    my_text = '(12==a)'
    v, res = peg_parser_visual(e_grammar).parse('<expr>', my_text)
    print(len(my_text), '<>', v.at)
    F.display_tree(res)

    my_text = '12'
    v, res = peg_parser_visual(e_grammar,
            loginit=True,logfalse=True).parse('<digits>', my_text)
    print(len(my_text), '<>', v.at)
    F.display_tree(res)


# ## Indentation Based Parser
# For indentation based parsing, we modify our string stream slightly. The idea
# is that when the parser is expecting a new line that corresponds to a new
# block (indentation) or a delimiter, then it will specifically ask for `<$nl>`
# token from the text stream. The text stream will first try to satisfy the
# new line request. If the request can be satisfied, it will also try to
# identify the new indentation level. If the new indentation level is
# more than the current indentation level, it will insert a new `<$indent>`
# token into the text stream. If on the other hand, the new indentation level
# is less than the current level, it will generate as many `<$dedent>` tokens
# as required that will match the new indentation level. 

# ### IText
class IText(Text):
    def __init__(self, text, at=0, buf=None, indent=None):
        self.text, self.at = text, at
        self.buffer = [] if buf is None else buf
        self._indent = [0] if indent is None else indent

    def advance(self, t):
        if t == '<$nl>': return self._advance_nl()
        else: return self._advance(t)

    def _advance(self, t):
        if self.buffer:
            if self.buffer[0] != t: return None
            return IText(self.text, self.at, self.buffer[1:], self._indent)
        elif self.text[self.at:self.at+len(t)] != t:
            return None
        return IText(self.text, self.at + len(t), self.buffer, self._indent)

    def _read_indent(self, at):
        indent = 0
        while self.text[at+indent:at+indent+1] == ' ':
            indent += 1
        return indent, at+indent

    def _advance_nl(self):
        if self.buffer: return None
        if self.text[self.at] != '\n': return None
        my_indent, my_buf = self._indent, self.buffer
        i, at = self._read_indent(self.at+1)
        if i > my_indent[-1]:
            my_indent, my_buf = my_indent + [i], ['<$indent>'] + my_buf
        else:
            while i < my_indent[-1]:
                my_indent, my_buf = my_indent[:-1], ['<$dedent>'] + my_buf
        return IText(self.text, at, my_buf, my_indent)

    def __repr__(self):
        return (repr(self.text[:self.at])+ '|' + ''.join(self.buffer) + '|'  +
                repr(self.text[self.at:]))

# We will first define a small grammar to test it out.
g1 = {
    '<start>': [['<ifstmt>']],
    '<stmt>': [['<assignstmt>']],
    '<assignstmt>': [['<letter>', '<$nl>']],
    '<letter>': [['a']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<block>': [['<$indent>','<stmt>', '<$dedent>']]
}
# Here is our text that corresponds to the g1 grammar.
my_text = """\
if a:
    a
"""

# We can now use the same parser with the text stream.

if __name__ == '__main__':
    v, res = peg_parser(g1).unify_key('<start>', IText(my_text))
    assert(len(my_text) == v.at)
    F.display_tree(res)

# Here is a slightly more complex grammar and corresponding text

g2 = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<ifstmt>'], ['<assignstmt>']],
    '<assignstmt>': [['<letter>', '<$nl>']],
    '<letter>': [['a']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}
my_text = """\
a
a
"""

# Checking if the text is parsable.
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text))
    assert(len(my_text) == v.at)
    F.display_tree(res)

# Another test
my_text1 = """\
if a:
    a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text1))
    assert(len(my_text1) == v.at)
    F.display_tree(res)

# Another
my_text2 = """\
if a:
    a
    a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text2))
    assert(len(my_text2) == v.at)
    F.display_tree(res)

# Another
my_text3 = """\
if a:
    a
    a
a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text3))
    assert(len(my_text3) == v.at)
    F.display_tree(res)
# Another
my_text4 = """\
a
a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text4))
    assert(len(my_text4) == v.at)
    F.display_tree(res)
# Another
my_text5 = """\
if a:
    if a:
        a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text5))
    assert(len(my_text5) == v.at)
    F.display_tree(res)
# Another
my_text6 = """\
if a:
    if a:
        a
a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text6))
    assert(len(my_text6) == v.at)
    F.display_tree(res)
# Another
my_text7 = """\
if a:
    if a:
        a
        a
a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text7))
    assert(len(my_text7) == v.at)
    F.display_tree(res)
# Another
my_text8 = """\
if a:
    if a:
        a
        a
    if a:
        a
a
"""
# Using
if __name__ == '__main__':
    v, res = peg_parser(g2).unify_key('<start>', IText(my_text8))
    assert(len(my_text8) == v.at)
    F.display_tree(res)

# Let us make a much larger grammar
e_grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letters>', '=','<expr>', '<$nl>']],
    '<letter>': [[c] for c in string.ascii_letters],
    '<digit>': [[c] for c in string.digits],
    '<letters>': [
        ['<letter>', '<letters>'],
        ['<letter>']],
    '<digits>': [
        ['<digit>', '<digits>'],
        ['<digit>']],
    '<ifstmt>': [['if', '<expr>', ':', '<$nl>', '<block>']],
    '<expr>': [
        ['(', '<expr>', '==', '<expr>', ')'],
        ['(', '<expr>', '!=', '<expr>', ')'],
        ['<digits>'],
        ['<letters>']
        ],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}
my_text9 = '''\
if(a==1):
    x=10
'''
# Using
if __name__ == '__main__':
    v, res = peg_parser(e_grammar).unify_key('<start>', IText(my_text9))
    assert(len(my_text9) == v.at)
    F.display_tree(res)

# As can be seen, we require no changes to the standard PEG parser for
# incorporating indentation sensitive (layout sensitive) parsing. The situation
# is same for other parsers such as Earley parsing.
