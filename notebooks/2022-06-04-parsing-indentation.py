# ---
# published: true
# title: Parsing Indentation Sensitive Languages
# layout: post
# comments: true
# tags: combinators, parsing, cfg, indentation
# categories: post
# ---

# We have previously seen how to parse strings using both [context-free
# grammars](/post/2021/02/06/earley-parsing/), as well as usin [combinatory
# parsers](https://rahul.gopinath.org/post/2020/03/02/combinatory-parsing/).
# However, languages such as Python and Haskell cannot be directly parsed by
# these parsers. This is because they use indentation levels to indicate
# nested statement groups.
# 
# For example, given:
#
# ```
# if True:
#    x = 100
#    y = 200
# ```
# Python groups the `x = 100` and `y = 200` together, and is parsed equivalent
# to
#
# ```
# if True: {
#    x = 100;
#    y = 200;
# }
# ```
# in a `C` like language. This use of indentation is hard to capture in
# context-free grammars.
# 
# Interestingly, it turns out that there is an easy solution. We can simply
# keep track of the indentation and de-indentation for identifying groups.
#
# The idea here is to first use a lexical analyzer to translate the source code
# into tokens, and then post-process these tokens to insert *Indent* and
# *Dedent* tokens. Hence, we start by defining our lexical analyzer. Turns out,
# our combinatory parser is really good as a lexical analyzer.
# As before, we start by importing our prerequisite packages.

#@
# https://rahul.gopinath.org/py/combinatoryparser-0.0.1-py2.py3-none-any.whl

import combinatoryparser as C

# ## Tokens
# We start by defining a minimal set of tokens necessary to lex a simple
# language.

def to_val(name):
    return lambda v: [(name, ''.join([i for i in v]))]

# Numeric literals represent numbers.

numeric_literal = C.P(lambda:
        C.Apply(to_val('NumericLiteral'), lambda: C.Re('^[0-9][0-9_.]*')))

# 
if __name__ == '__main__':
    for to_parse, parsed in numeric_literal(list('123')):
        if to_parse: continue
        print(parsed)

# Quoted literals represent strings.

quoted_literal = C.P(lambda:
        C.Apply(to_val('QuotedLiteral'), lambda: C.Re('^"[^"]*"')))
# 
if __name__ == '__main__':
    for to_parse, parsed in quoted_literal(list('"abc def"')):
        if to_parse: continue
        print(parsed)


# Punctuation represent operators and other punctuation

punctuation = C.P(lambda:
        C.Apply(to_val('Punctuation'), lambda:
            C.Re('^[!#$%&()*+,-./:;<=>?@\[\]^`{|}~\\\\]+')))
# 
if __name__ == '__main__':
    for to_parse, parsed in punctuation(list('<=')):
        if to_parse: continue
        print(parsed)


# Name represents function and variable names, and other names in the program.

name = C.P(lambda: C.Apply(to_val('Name'), lambda: C.Re('^[a-zA-Z_]+')))

# We also need to represent new lines and whitespace.

nl = C.P(lambda: C.Apply(to_val('NL'), lambda: C.Lit('\n')))

ws = C.P(lambda: C.Apply(to_val('WS'), lambda: C.Re('^[ ]+')))

# With these, we can define our tokenizer as follows. A lexical token can
# anything that we previously defined.

lex = numeric_literal | quoted_literal | punctuation | name | nl | ws

# And the source string can contain any number of such tokens.

lexs =  C.P(lambda: lex | (lex >> lexs))

# ## Tokenize
# We can now define our tokenizer as follows.

def tokenize(mystring):
    for (rem,lexed) in lexs(list(mystring)):
        if rem: continue
        return lexed
    raise Exception('Unable to tokenize')

# 
if __name__ == '__main__':
    lex_tokens = tokenize('ab + cd < " xyz "')
    print(lex_tokens)


# ## Indents
# Next, we want to insert indentation and de-indentation. We do that by keeping
# a stack of seen indentation levels. If the new indentation level is greater
# than the current indentation level, we push the new indentation level into
# the stack. If the indentation level is smaller, the we pop the stack until we
# reach the correct indentation level.

def generate_indents(tokens):
    indents = [0]
    stream = []
    while tokens:
        token, *tokens  = tokens
        # did a nested block begin
        if token[0] == 'NL':
            if not tokens:
                stream.append(token)
                dedent(0, indents, stream)
                break
            elif tokens[0][0] == 'WS':
                indent = len(tokens[0][1])
                if indent > indents[-1]:
                    indents.append(indent)
                    stream.append(('Indent', indent))
                elif indent == indents[-1]:
                    stream.append(token)
                else:
                    stream.append(token)
                    dedent(indent, indents, stream)
                tokens = tokens[1:]
            else:
                stream.append(token)
                dedent(0, indents, stream)
        else:
            stream.append(token)
    assert len(indents) == 1
    return stream

def dedent(indent, indents, stream):
    while indent < indents[-1]:
        indents.pop()
        stream.append(('Dedent', indents[-1]))
    assert indent == indents[-1]
    return

# we can now extract the indentation based blocks as follows

example = """\
if foo:
    if bar:
        x = 42
        y = 100
else:
    print foo
"""

# 

if __name__ == '__main__':
    tokens = tokenize(example)
    res = generate_indents(tokens)
    current_indent = 0
    for k in res:
        if k[0] in 'Indent':
            current_indent = k[1]
            print()
            print(' ' * current_indent + '{')
            print(current_indent * ' ', end = '')
        elif k[0] in 'Dedent':
            print()
            print(current_indent * ' ' + '}')
            current_indent = k[1]
        elif k[0] in 'NL':
            print()
            print(current_indent * ' ', end = '')
        else:
            print(k[1], end = '')
    print()

# At this point, we can apply a standard context-free parser for parsing the
# produced tokens. We use a simple Combinatory parser for that.

# ## Combinatory parser
def NoParse():
    def parse(instr): return [(instr, [('Empty',)])]
    return parse

def Keyword(k):
    def parse(instr):
        if instr and instr[0] == ('Name', k):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Literal(k):
    def parse(instr):
        if instr and instr[0][0] == k:
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def NL():
    def parse(instr):
        if instr and instr[0][0] == 'NL':
            return [(instr[1:], [instr[0]])] 
        return []
    return parse

def WS():
    def parse(instr):
        if instr and instr[0][0] == 'WS':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Name():
    def parse(instr):
        if instr and instr[0][0] == 'Name':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Punct(c):
    def parse(instr):
        if instr and instr[0] == ('Punctuation', c):
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Indent():
    def parse(instr):
        if instr and instr[0][0] == 'Indent':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

def Dedent():
    def parse(instr):
        if instr and instr[0][0] == 'Dedent':
            return [(instr[1:], [instr[0]])]
        return []
    return parse

# 
example = """\
if False:
    if True:
        x = "ab cd"
        y = 100
z = 1
"""

# 
def to_valA(name):
    return lambda v: [(name, v)]

# Tokenizing
if __name__ == '__main__':
    tokens = tokenize(example)
    print(tokens)
    res = generate_indents(tokens)
    for k in res:
        print(k)

# Parsing
if __name__ == '__main__':

    ifkey = C.P(lambda: Keyword('if'))
    empty = C.P(lambda: NoParse())
    name = C.P(lambda: Name())
    expr = C.P(lambda:
            C.Apply(
                to_valA('Expr'),
                lambda: name | nlit | qlit)
            )
    ws = C.P(lambda: WS())
    nl = C.P(lambda: NL())
    spaces = C.P(lambda: (ws >> spaces) | empty)
    colon = C.P(lambda: Punct(':'))
    equals = C.P(lambda: Punct('='))
    nlit = C.P(lambda: Literal('NumericLiteral'))
    qlit = C.P(lambda: Literal('QuotedLiteral'))
    indent = C.P(lambda: Indent())
    dedent = C.P(lambda: Dedent())

    assignstmt = C.P(lambda:
            C.Apply(
                to_valA('Assignment'),
                lambda: name >> spaces >> equals >> spaces >> (nlit | qlit) >> nl)
            )
    ifstmt =  C.P(lambda:
            C.Apply(
                to_valA('If'),
                lambda: ifkey >> spaces >> expr >> spaces >> colon >> block)
            )

    block = C.P(lambda: (indent >> stmts >> dedent) | stmts)

    stmt = C.P(lambda:
            C.Apply(
                to_valA('Statement'),
                lambda: ifstmt | assignstmt)
            )

    stmts = C.P(lambda:
            C.Apply(
                to_valA('Stmts'),
                lambda: stmt| (stmt >> stmts))
            )

    for to_parse, parsed in stmts(res):
        if not to_parse:
            print(">", parsed)

