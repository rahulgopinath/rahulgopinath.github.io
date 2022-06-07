# ---
# published: false
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

# ## PEG
import sys, string
e_grammar = {
    '<start>': [['<expr>']],
    '<expr>': [
        ['<term>', '<add_op>', '<expr>'],
        ['<term>']],
    '<term>': [
        ['<digits>'],
        ['(','<expr>',')']],
    '<digits>': [
        ['<digit>','<digits>'],
        ['<digit>']],
    '<digit>': [[str(i)] for i in list(range(10))],
    '<add_op>': [['+'], ['-']],
}
i_grammar = {
    '<start>': [['<stmts>']],
    '<stmts>': [
        ['<stmt>', '<$nl>', '<stmts>'],
        ['<stmt>']],
    '<stmt>': [['<assignstmt>'], ['<ifstmt>']],
    '<assignstmt>': [['<letter>', '=','<letter>']],
    '<letter>': [['a'],['b'], ['c'], ['d']],
    '<ifstmt>': [['if ', '<letter>', ':', '<$nl>', '<block>']],
    '<expr>': [['<letter>', '=', '<letter>']],
    '<block>': [['<$indent>','<stmts>', '<$dedent>']]
}


my_text = '1+2'

# ### Text
class Text:
    def __init__(self, text, at):
        self.text, self.at = text, at

    def match(self, t): return self.text[self.at:self.at+len(t)] == t

    def advance(self, t):
        if self.match(t):
            return Text(self.text, self.at + len(t))
        else:
            return None

    def __repr__(self):
        return repr(self.text[:self.at]+ '|' +self.text[self.at:])

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
    v, res = peg_parser(e_grammar).parse('<start>', my_text)
    print(len(my_text), '<>', v.at)
    F.display_tree(res)

# ## IPEG
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


    def match(self, t):
        if self.buffer: return self.buffer[0] == t
        return self.text[self.at:self.at+len(t)] == t

    def advance(self, t):
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

def read_indent(text):
    indent = 0
    while True:
        text_ = text.advance(' ')
        if text_ is None: return indent, text
        indent += 1
        text = text_
    assert False

# Using it
if __name__ == '__main__':
    print(read_indent(IText('  abc', 0)))

# ## handle_newline
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

    def handle_newline(self, text):
        indent, text_ = read_indent(text)
        assert indent is not None
        if indent > text_.get_indent():
            text_ = text_.insert('<$indent>')
            text_ = text_.push_indent(indent)
            text_ = text_.insert('<$nl>') # unify_nl
        elif indent == text_.get_indent():
            text_ = text_.insert('<$nl>') # unify_nl
        elif indent < text_.get_indent():
            while indent < text_.get_indent():
                text_ = text_.pop_indent()
                text_ = text_.insert('<$dedent>')
            text_ = text_.insert('<$nl>') # unify_nl
            #text_ = text_.push_indent(indent)
        return text_

    def unify_nl(self, key, text, _indent):
        text_ = text.advance('\n')
        if text_ is None:
            return (text, None)
        # this should add a $nl to stream buffer and the right $indent if any
        text_ = self.handle_newline(text_)
        text_ = text_.advance('<$nl>')
        assert text_ is not None
        return (text_, ('<$nl>', []))

    def unify_key(self, key, text, _indent):
        if key == '<$nl>':
            return self.unify_nl(key, text, _indent)
        elif key not in self.grammar:
            v = text.advance(key) # also for ['<$indent>', '<$dedent>']:
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
    v, res = ipeg_parser_log(g1, log=False).unify_key('<start>', IText(my_text, 0), 0)
    assert(len(my_text) == v.at)
    print(my_text)
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
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text, 0), 0)
    assert(len(my_text) == v.at)
    print(my_text)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text1 = """\
if a:
    a
"""
# Using
if __name__ == '__main__':
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text1, 0), 0)
    assert(len(my_text1) == v.at)
    print(my_text)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text2 = """\
if a:
    a
    a
"""
# Using
if __name__ == '__main__':
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text2, 0), 0)
    assert(len(my_text2) == v.at)
    print(my_text2)
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
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text3, 0), 0)
    assert(len(my_text3) == v.at)
    print(my_text3)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text4 = """\
a
a
"""
# Using
if __name__ == '__main__':
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text4, 0), 0)
    assert(len(my_text4) == v.at)
    print(my_text4)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)

my_text5 = """\
if a:
    if a:
        a
"""
# Using
if __name__ == '__main__':
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text5, 0), 0)
    assert(len(my_text5) == v.at)
    print(my_text5)
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
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text6, 0), 0)
    assert(len(my_text6) == v.at)
    print(my_text6)
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
    v, res = ipeg_parser_log(g2, log=False).unify_key('<start>', IText(my_text7, 0), 0)
    assert(len(my_text7) == v.at)
    print(my_text7)
    #for k in v._tokens: print(repr(k))
    F.display_tree(res, get_children=get_children)


