# ---
# published: true
# title: Fuzzing With Regular Expressions
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# For fuzzing, we often need to generate inputs that have a particular pattern,
# and this pattern could be easier to specify using a regular expression than
# using a context free grammar. For example, the URL can be described as:
# ```
# (https|http|ftp)://[a-zA-Z0-9.]+(:[0-9]+|)(/[a-zA-Z0-9-/]+|)
# ```
# Can we use such regular expressions as producers? As before, we start with
# our prerequisites.

# We import the following modules

#^
# sympy

#@
# https://rahul.gopinath.org/py/simplefuzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl

# The imported modules

import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import itertools as I

import earleyparser
import sympy

# Since we want to convert a regular expression to a generator, it is necessary
# to parse it first. The following describes the grammar of regular expressions.
#
# A regular expression is basically a set of alternatives separated by `|`
#
# ```
#   <regex> ::= <cex>
#             | <cex> `|` <regex>
# ```
#
# Each alternative is an expression that is a sequence of more basic expressions
#
# ```
#   <cex>   ::= <exp>
#             | <exp> <cex>
# ```
#
# The basic regular expression unit is a single character, standing for itself.
# One may also have a bracket expression `[...]` which matches the list of
# characters inside the brackets, or a single `.` which matches any character.
#
# However, one can also have more complex units such as a parenthesized regex
# `(...)`, a basic expression followed by Kleene star `*` which stands for any
# number of matches including none, and a basic expression followed by `+` which
# stands for at least one match of the preceding basic expression.
#
# ```
#   <exp>   ::=  <unitexp>
#             |  <regexstar>
#             |  <regexplus>
#
#   <unitexp>::= <alpha>
#             |  <bracket>
#             |  <dot>
#             |  <parenexp>
# ```

import string

REGEX_GRAMMAR = {
    '<start>' : [
        ['<regex>']
    ],
    '<regex>' : [
        ['<cex>', '|', '<regex>'],
        ['<cex>', '|'],
        ['<cex>']
    ],
    '<cex>' : [
        ['<exp>', '<cex>'],
        ['<exp>']
    ],
    '<exp>': [
        ['<unitexp>'],
        ['<regexstar>'],
        ['<regexplus>'],
    ],
    '<unitexp>': [
        ['<alpha>'],
        ['<bracket>'],
        ['<dot>'],
        ['<parenexp>'],
    ],
    '<parenexp>': [
        ['(', '<regex>', ')'],
    ],
    '<regexstar>': [
        ['<unitexp>', '*'],
    ],
    '<regexplus>': [
        ['<unitexp>', '+'],
    ],
    '<bracket>' : [
        ['[','<singlechars>', ']'],
    ],
    '<singlechars>': [
        ['<singlechar>', '<singlechars>'],
        ['<singlechar>'],
    ],
    '<singlechar>': [
        ['<char>'],
        ['\\','<escbkt>'],
    ],
    '<escbkt>' : [['['], [']'], ['\\']],
    '<dot>': [
        ['.'],
    ],
    '<alpha>' : [[c] for c in string.printable if c not in '[]()*+.|'],
    '<char>' : [[c] for c in string.printable if c not in '[]\\'],
}
REGEX_START = '<start>'

# Let us see if we can parse a small regular expression.

if __name__ == '__main__':
    my_re = '(https|http|ftp)://[a-zA-Z0-9.]+(/[a-zA-Z0-9-/]+|)'
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, REGEX_START))[0]
    fuzzer.display_tree(parsed_expr)

# While a regular expression parse tree is technically sufficient to produce
# a generator, there is a better solution. We know how to build very good
# fuzzers with grammars. Hence, it is better to convert the regular expression
# to a grammar first, and use one of our fuzzers.
#
# ## Regular expression to context-free grammar

TERMINAL_SYMBOLS = list(string.digits + string.ascii_lowercase + string.ascii_uppercase)

class RegexToGrammar:
    def __init__(self, all_terminal_symbols=TERMINAL_SYMBOLS):
        self.parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
        self.counter = 0
        self.all_terminal_symbols = all_terminal_symbols

    def parse(self, inex):
        parsed_expr = list(self.parser.parse_on(inex, REGEX_START))[0]
        return parsed_expr

    def new_key(self):
        k = self.counter
        self.counter += 1
        return '<%d>' % k

    def to_grammar(self, inex):
        parsed = self.parse(inex)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        grammar, start = self.convert_regex(children[0])
        return grammar, start

# ## <unitexp>
# We first define our basic unit. The exp converter, which delegates to other
# converters
# ```
#   <unitexp>::= <alpha>
#             |  <bracket>
#             |  <dot>
#             |  <parenexp>
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_unitexp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<alpha>':
            return self.convert_alpha(children[0])
        elif key == '<bracket>':
            return self.convert_bracket(children[0])
        elif key == '<dot>':
            return self.convert_dot(children[0])
        elif key == '<parenexp>':
            return self.convert_regexparen(children[0])
        else:
            assert False
        assert False

# The most basic regular expression is the character itself. We convert
# it to a nonterminal that defines the single character. That is,
# `a` gets translated to
# ```
# <X> ::= `a`
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_alpha(self, node):
        key, children = node
        assert key == '<alpha>'
        nkey = self.new_key()
        return {nkey: [[children[0][0]]]}, nkey

# Using it

if __name__ == '__main__':
    my_re = 'a'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().convert_unitexp(parsed_expr)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# The next basic regular expression is the brackets, which matches any
# character inside the brackets `[...]`. We convert
# it to a nonterminal that defines the single character. The following
# is the regex grammar.
# ```
#   <bracket> ::= `[` <singlechars> `]`
#   <singlechars>::= <singlechar><singlechars>
#                  | <singlechar>
#   <singlechar> ::= <char>
#                  | `\` <escbkt>
#   <escbkt>     ::= `[`
#                  | `]`
#                  | `\`
# ```
# Given the regex `[abc]`, this regex is converted to the following grammar
# ```
# <X> ::= `a` | `b` | `c`
# ```

class RegexToGrammar(RegexToGrammar):
    def extract_char(self, node):
        key, children = node
        if len(children) == 1:
            key, children = children[0]
            assert key == '<char>'
            return children[0][0]
        else:
            key, children = children[1]
            assert key == '<escbkt>'
            return children[0][0]

    def extract_singlechars(self, node):
        key, children = node
        child, *children = children
        char = self.extract_char(child)
        if children:
            assert len(children) == 1
            return [char] + self.extract_singlechars(children[0])
        else:
            return [char]

    def convert_bracket(self, node):
        key, children = node
        assert key == '<bracket>'
        assert len(children) == 3
        nkey = self.new_key()
        chars = self.extract_singlechars(children[1])
        return {nkey: [[c] for c in  chars]}, nkey

# Using it

if __name__ == '__main__':
    my_re = '[abc\\\\d\\[e\\].]'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().convert_unitexp(parsed_expr)
    gatleast.display_grammar(g, s)
    # check it has worked
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v


# Next, we define the `<dot>`. A dot matches any character. That is, terminal
# symbol.
#
# ```
#   <dot>   ::=  a | b | ...
# ```


class RegexToGrammar(RegexToGrammar):
    def convert_dot(self, node):
        key, children = node
        assert key == '<dot>'
        assert children[0][0] == '.'
        return {'<dot>':[[c] for c in self.all_terminal_symbols]}, '<dot>'

# Using it

if __name__ == '__main__':
    my_re = '.'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().convert_unitexp(parsed_expr)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# ## <exp>
# Next, we define the `<exp>`
# ```
#   <exp>   ::=  <unitexp>
#             |  <regexstar>
#             |  <regexplus>
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_exp(self, node):
        _key, children = node
        key = children[0][0]
        if key == '<unitexp>':
            return self.convert_unitexp(children[0])
        elif key == '<regexstar>':
            return self.convert_regexstar(children[0])
        elif key == '<regexplus>':
            return self.convert_regexplus(children[0])
        else:
            assert False
        assert False

# For `<regexstar>` the regular expression grammar is
# ```
#    <regexstar> ::= <unitexp> `*`
# ```
# Given a regular expression `a*`, this gets translated to
# ```
# <X> ::= a <X>
#       |
# ```
# For `<regexplus>` the regular expression grammar is
# ```
#    <regexplus> ::= <unitexp> `+`
# ```
# Given a regular expression `a+`, this gets translated to
# ```
# <X> ::= a <X>
#       | a
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_regexstar(self, node):
        key, children = node
        assert len(children) == 2
        key, g = self.convert_unitexp(children[0])
        nkey = self.new_key()
        return {**g, **{nkey: [[key, nkey], []]}}, nkey

    def convert_regexplus(self, node):
        key, children = node
        assert len(children) == 2
        g, key = self.convert_unitexp(children[0])
        nkey = self.new_key()
        return {**g, **{nkey: [[key, nkey], [key]]}}, nkey

# Using it.

if __name__ == '__main__':
    my_re = '.+'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<exp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().convert_exp(parsed_expr)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# ## <cex>
# One basic operation of regular expressions is concatenation. It matches
# two patterns in sequence. We convert
# concatenation to a rule containing two corresponding nonterminals.
# The regular expression grammar is
# ```
#   <cex>   ::= <exp>
#             | <exp> <cex>
# ```
# Given a regular expression `ab`, this gets converted into
# ```
# <X> := a
# <Y> := b
# <Z> := <X> <Y>
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_cex(self, node):
        key, children = node
        child, *children = children
        g, key = self.convert_exp(child)
        rule = [key]
        if children:
            assert len(children) == 1
            g2, key2 = self.convert_cex(children[0])
            rule.append(key2)
            g = {**g, **g2}
        nkey = self.new_key()
        return {**g, **{nkey: [rule]}}, nkey

# Using it
if __name__ == '__main__':
    my_re = '[ab].'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, '<cex>'))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().convert_cex(parsed_expr)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# Next, we define our top level converter.
# ```
#   <regex> ::= <cex>
#             | <cex> `|` <regex>
# ```
# Given a regular expression `a|b`, this gets converted into
# ```
# <X> := a
# <Y> := b
# <Z> := <X>
#      | <Y>
# ```


class RegexToGrammar(RegexToGrammar):
    def convert_regex(self, node):
        key, children = node
        child, *children = children
        g, key = self.convert_cex(child)
        rules = [[key]]
        if children:
            if len(children) == 2:
                g2, key2 = self.convert_regex(children[1])
                rules.append([key2])
                g = {**g, **g2}
            elif len(children) == 1:
                rules.append([])
            else:
                assert False
        nkey = self.new_key()
        return {**g, **{nkey: rules}}, nkey

# Using it
if __name__ == '__main__':
    my_re = 'ab|c'
    print(my_re)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_re, REGEX_START))[0]
    fuzzer.display_tree(parsed_expr)
    g, s = RegexToGrammar().to_grammar(my_re)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# Next, we define our <parenexp>
# A parenthesis is simply a grouping construct that groups all
# elements inside it as one.
# ```
# <parenexp> ::= `(` <regex> `)`
# ```
# Given a parenthesis expression `(a)`, this gets translated to
# ```
# <X> = a
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_regexparen(self, node):
        key, children = node
        assert len(children) == 3
        return self.convert_regex(children[1])

# Using it

if __name__ == '__main__':
    my_re = '(abc)'
    print(my_re)
    g, s = RegexToGrammar().to_grammar(my_re)
    gatleast.display_grammar(g, s)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

# At this point, we have our full grammar, and we can use it to generate inputs
# as below

if __name__ == '__main__':
    my_re = '(ab|c)[.][de]+.'
    print(my_re)
    g, s = RegexToGrammar().to_grammar(my_re)
    # check it has worked
    import re
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        assert re.match(my_re, v), v

    # Let us try the original regex
    my_re = '(https|http|ftp)://[abcdABCD01234567899.]+(:[01234567899]+|)(/[abcdzABCDZ0123456789/-]+|)'
    print(my_re)
    g, s = RegexToGrammar().to_grammar(my_re)
    rgf = fuzzer.LimitFuzzer(g)
    for i in range(10):
        v = rgf.fuzz(s)
        print(repr(v))
        assert re.match(my_re, v), v

# The runnable code for this post is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-10-22-fuzzing-with-regular-expressions.py)
