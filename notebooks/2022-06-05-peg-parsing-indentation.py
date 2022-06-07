# ---
# published: false
# title: Incorporating Indentation Parsing in PEG
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
    def __init__(self, text, at):
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
        return self.unify_key(key, Text(text, 0))

    def unify_key(self, key, text):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return v, (key, [])
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text)
            if res is not None: return l, (key, res)
        return (0, None)

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

# ## Indentation Based Parser
# For indentation based parsing, we modify our string stream slightly.
# ### IText
class IText(Text):
    def __init__(self, text, at, buf=None, indent=None, tokens=None):
        self.text, self.at = text, at
        if buf is None: self.buffer = []
        else: self.buffer = buf
        if indent is None: self._indent = [0]
        else: self._indent = indent
        if tokens is None: self._tokens = []
        else: self._tokens = tokens

    def insert(self, t):
        return IText(self.text, self.at, [t] + self.buffer, self._indent,
                self._tokens)

    def pop_indent(self):
        return IText(self.text, self.at, self.buffer, self._indent[:-1],
                self._tokens)

    def push_indent(self, indent):
        return IText(self.text, self.at, self.buffer, self._indent + [indent],
                self._tokens)

    def get_indent(self):
        return self._indent[-1]

    def _match(self, t):
        if self.buffer: return self.buffer[0] == t
        return self.text[self.at:self.at+len(t)] == t

    def _advance(self, t):
        if self.buffer:
            if self.buffer[0] == t:
                return IText(self.text, self.at, self.buffer[1:],
                        self._indent, self._tokens + [t])
            else:
                return None
        elif self.text[self.at:self.at+len(t)] == t:
            return IText(self.text, self.at + len(t), self.buffer,
                    self._indent, self._tokens + [t])
        else:
            return None

    def advance(self, t):
        if t == '<$nl>': return self.advance_nl()
        else: return self._advance(t)

    def read_indent(self):
        indent = 0
        text = self
        while True:
            text_ = text._advance(' ')
            if text_ is None: return indent, text
            indent += 1
            text = text_
        assert False

    def advance_nl(self):
        text_ = self._advance('\n')
        if text_ is None: return None
        indent, text_ = text_.read_indent()
        if indent > text_.get_indent():
            text_ = text_.insert('<$indent>').push_indent(indent)
        else:
            while indent < text_.get_indent():
                text_ = text_.pop_indent().insert('<$dedent>')
        return text_.insert('<$nl>')._advance('<$nl>')


    def __repr__(self):
        return repr(self.text[:self.at])+ '|' + ''.join(self.buffer) + '|'  + repr(self.text[self.at:])

# Using
if __name__ == '__main__':
    v, res = peg_parser(e_grammar).unify_key('<start>', IText(my_text, 0))
    print(len(my_text), '<>', v.at)
    F.display_tree(res)

# ## read_indent
# When given a line, we find the number of spaces occurring before a non-space
# character is found.

# Using it
if __name__ == '__main__':
    print(IText('  abc', 0).read_indent())

# ## advance_nl
# Next, we define how to parse a nonterminal symbol. This is the area
# where we hook indentation parsing. When unifying `<$indent>`,
# we expect the text to contain a new line,
# and we also expect an increase in indentation.
# ## unify_nl
# If the current key is `<$nl>`, then we
# expect the current text to contain a new line. Furthermore, there may also be
# a reduction in indentation.
# With this, we are ready to define the main PEG parser.
# The rest of the implementation is very similar to
# [PEG parser](/post/2018/09/06/peg-parsing/) that we discussed before.


# display
def get_children(node):
    if node[0] in ['<$indent>', '<$dedent>', '<$nl>']: return []
    return F.get_children(node)

class ipeg_parser_log(peg_parser):
    def __init__(self, grammar, log):
        self.grammar, self.indent, self._log = grammar, [0], log

    def unify_key(self, key, text, _indent):
        if key not in self.grammar:
            v = text.advance(key)
            if v is not None: return (v, (key, []))
            else: return (text, None)
        rules = self.grammar[key]
        for rule in rules:
            l, res = self.unify_rule(rule, text, _indent+1)
            if res is not None: return l, (key, res)
        return (text, None)

    def unify_rule(self, parts, text, _indent):
        results = []
        text_ = text
        for part in parts:
            if self._log:
                print(' '*_indent, part, '=>', repr(text))
            text_, res = self.unify_key(part, text_, _indent)
            if self._log:
                print(' '*_indent, part, '=>', repr(text_), res is not None)
            if res is None: return text, None
            results.append(res)
        return text_, results

    def parse(self, key, text):
        return self.unify_key(key, IText(text, 0), 0)


g1 = {
    '<start>': [['<ifstmt>']],
    '<stmt>': [['<assignstmt>']],
    '<assignstmt>': [['<letter>', '<$nl>']],
    '<letter>': [['a']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<block>': [['<$indent>','<stmt>', '<$dedent>']]
}

my_text = """\
if a:
    a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text)
    v, res = ipeg_parser_log(g1, log=False).unify_key('<start>', IText(my_text, 0), 0)
    assert(len(my_text) == v.at)
    #for k in v._tokens: print(repr(k))
    #F.display_tree(res, get_children=get_children)
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
# Using
if __name__ == '__main__':
    print('---')
    print(my_text)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text, 0), 0)
    assert(len(my_text) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text1 = """\
if a:
    a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text1)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text1, 0), 0)
    assert(len(my_text1) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text2 = """\
if a:
    a
    a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text2)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text2, 0), 0)
    assert(len(my_text2) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text3 = """\
if a:
    a
    a
a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text3)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text3, 0), 0)
    assert(len(my_text3) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text4 = """\
a
a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text4)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text4, 0), 0)
    assert(len(my_text4) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text5 = """\
if a:
    if a:
        a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text5)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text5, 0), 0)
    assert(len(my_text5) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text6 = """\
if a:
    if a:
        a
a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text6)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text6, 0), 0)
    assert(len(my_text6) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text7 = """\
if a:
    if a:
        a
        a
a
"""
# Using
if __name__ == '__main__':
    print('---')
    print(my_text7)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text7, 0), 0)
    assert(len(my_text7) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

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
    print('---')
    print(my_text8)
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text8, 0), 0)
    assert(len(my_text8) == v.at)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)


