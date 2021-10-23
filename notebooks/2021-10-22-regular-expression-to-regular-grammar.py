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

import sys, imp, pprint, string

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
        with open(module_loc, encoding='utf8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

# We import the following modules

earleyparser = import_file('earleyparser', '2021-02-06-earley-parsing.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')

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


REGEX_GRAMMAR = {
    '<start>' : [
        ['<regex>']
    ],
    '<regex>' : [
        ['<cex>', '|', '<regex>'],
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
    '<alpha>' : [[c] for c in string.printable if c not in '[]()*+.'],
    '<char>' : [[c] for c in string.printable if c not in '[]\\'],
}
REGEX_START = '<start>'

# Let us see if we can parse a small regular expression.

if __name__ == '__main__':
    my_input = '(a|b)+(c)*'
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
    fuzzer.display_tree(parsed_expr)

# While a regular expression parse tree is technically sufficient to produce
# a generator, there is a better solution. We know how to build very good
# fuzzers with grammars. Hence, it is better to convert the regular expression
# to a grammar first, and use one of our fuzzers.
#
# ## Regular expression to context-free grammar

class RegexToGrammar:
    def __init__(self):
        self.parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
        self.counter = 0

    def parse(self, inex):
        parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
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
        grammar = {}
        start = self.convert_regex(children[0], grammar)
        return start, grammar

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
    def convert_unitexp(self, node, grammar):
        _key, children = node
        key = children[0][0]
        if key == '<alpha>':
            return self.convert_alpha(children[0], grammar)
        elif key == '<bracket>':
            return self.convert_bracket(children[0], grammar)
        elif key == '<dot>':
            return self.convert_dot(children[0], grammar)
        elif key == '<parenexp>':
            return self.convert_regexparen(children[0], grammar)
        else:
            assert False
        return key

# The most basic regular expression is the character itself. We convert
# it to a nonterminal that defines the single character

class RegexToGrammar(RegexToGrammar):
    def convert_alpha(self, node, grammar):
        key, children = node
        assert key == '<alpha>'
        nkey = self.new_key()
        grammar[nkey] = [[children[0][0]]]
        return nkey

# Using it

if __name__ == '__main__':
    my_input = 'a'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g = {}
    s = RegexToGrammar().convert_unitexp(parsed_expr, g)
    gatleast.display_grammar(g, s)

# The next basic regular expression is the brackets, which matches any
# character inside the brackets `[...]`. We convert
# it to a nonterminal that defines the single character
# ```
#   <bracket> ::= `[` <singlechars> `]`
#   <singlechars>::= <singlechar><singlechars>
#                  | <singlechar>
#   <singlechar> ::= <char>
#                  | `\` <escbkt>
#   <escbkt>     ::= `[`
#                  | `]`
#                  | `\`

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

    def convert_bracket(self, node, grammar):
        key, children = node
        assert key == '<bracket>'
        assert len(children) == 3
        nkey = self.new_key()
        chars = self.extract_singlechars(children[1])
        grammar[nkey] = [[c] for c in  chars]
        return nkey

# Using it

if __name__ == '__main__':
    my_input = '[abc\\\\d\\[e\\].]'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g = {}
    s = RegexToGrammar().convert_unitexp(parsed_expr, g)
    gatleast.display_grammar(g, s)

# Next, we define the `<dot>`

class RegexToGrammar(RegexToGrammar):
    def convert_dot(self, node, grammar):
        key, children = node
        assert key == '<dot>'
        assert children[0][0] == '.'
        if '<dot>' not in grammar:
            grammar['<dot>'] = [[c] for c in string.printable]
        return '<dot>'

# Using it

if __name__ == '__main__':
    my_input = '.'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, '<unitexp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g = {}
    s = RegexToGrammar().convert_unitexp(parsed_expr, g)
    gatleast.display_grammar(g, s)

# ## <exp>
#   <exp>   ::=  <unitexp>
#             |  <regexstar>
#             |  <regexplus>
# 
# Next, we define the `<exp>`

class RegexToGrammar(RegexToGrammar):
    def convert_exp(self, node, grammar):
        _key, children = node
        key = children[0][0]
        if key == '<unitexp>':
            return self.convert_unitexp(children[0], grammar)
        elif key == '<regexstar>':
            return self.convert_regexstar(children[0], grammar)
        elif key == '<regexplus>':
            return self.convert_regexplus(children[0], grammar)
        else:
            assert False
        return key

#    <regexstar> ::= <unitexp> `*`
#    <regexplus> ::= <unitexp> `+`

class RegexToGrammar(RegexToGrammar):
    def convert_regexstar(self, node, grammar):
        key, children = node
        assert len(children) == 2
        key = self.convert_unitexp(children[0], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key, nkey], []]
        return nkey

    def convert_regexplus(self, node, grammar):
        key, children = node
        assert len(children) == 2
        key = self.convert_unitexp(children[0], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key, nkey], [key]]
        return nkey

# Using it.

if __name__ == '__main__':
    my_input = '.+'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, '<exp>'))[0]
    fuzzer.display_tree(parsed_expr)
    g = {}
    s = RegexToGrammar().convert_exp(parsed_expr, g)
    gatleast.display_grammar(g, s)

# ## <cex>
# One basic operation of regular expressions is concatenation. It matches
# two patterns in sequence. We convert
# concatenation to a rule containing two corresponding nonterminals.
#   <cex>   ::= <exp>
#             | <exp> <cex>

class RegexToGrammar(RegexToGrammar):
    def convert_cex(self, node, grammar):
        key, children = node
        child, *children = children
        key = self.convert_exp(child, grammar)
        rule = [key]
        if children:
            assert len(children) == 1
            key2 = self.convert_cex(children[0], grammar)
            rule.append(key2)
        nkey = self.new_key()
        grammar[nkey] = [rule]
        return nkey

# Using it
if __name__ == '__main__':
    my_input = '[ab].'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, '<cex>'))[0]
    fuzzer.display_tree(parsed_expr)
    g = {}
    s = RegexToGrammar().convert_cex(parsed_expr, g)
    gatleast.display_grammar(g, s)

# Next, we define our top level converter.
# ```
#   <regex> ::= <cex>
#             | <cex> `|` <regex>
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_regex(self, node, grammar):
        key, children = node
        child, *children = children
        key = self.convert_cex(child, grammar)
        rules = [[key]]
        if children:
            assert len(children) == 2
            key2 = self.convert_regex(children[1], grammar)
            rules.append([key2])
        nkey = self.new_key()
        grammar[nkey] = rules
        return nkey

# Using it
if __name__ == '__main__':
    my_input = 'ab|c'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
    fuzzer.display_tree(parsed_expr)
    s, g = RegexToGrammar().to_grammar(my_input)
    gatleast.display_grammar(g, s)

# Next, we define our <parenexp>
# A parenthesis is simply a grouping construct that groups all
# elements inside it as one.
# ```
# <parenexp> ::= `(` <regex> `)`
# ```

class RegexToGrammar(RegexToGrammar):
    def convert_regexparen(self, node, grammar):
        key, children = node
        assert len(children) == 3
        key = self.convert_regex(children[1], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key]]
        return nkey

# Using it

if __name__ == '__main__':
    my_input = '(abc)'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
    fuzzer.display_tree(parsed_expr)
    s, g = RegexToGrammar().to_grammar(my_input)
    gatleast.display_grammar(g, s)

