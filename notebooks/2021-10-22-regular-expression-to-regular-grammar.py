# ---
# published: true
# title: Converting a Regular Expression to Regular Grammar
# layout: post
# comments: true
# tags: python
# categories: post
# ---

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

REGEX_GRAMMAR = {
    '<start>' : [
        ['<regex>']
        ],
    '<regex>' : [
        ['<regexstar>'],
        ['<regexplus>'],
        ['<regexparen>'],
        ['<regexconcat>'],
        ['<regexalts>'],
        ['<alpha>'],
        ['<bracket>'],
        ],
    '<regexstar>': [
        ['<regexparen>', '*'],
        ['<alpha>', '*'],
        ['<braket>', '*'],
    ],
    '<regexplus>': [
        ['<regexparen>', '+'],
        ['<alpha>', '+'],
        ['<braket>', '+'],
    ],
    '<regexparen>': [
        ['(', '<regex>', ')'],
    ],
    '<regexconcat>': [
        ['<regex>', '<regex>'],
    ],
    '<regexalts>' : [
        ['<regex>', '|', '<regex>']
    ],
    '<bracket>' : [
        ['[','<singlechar>', ']'],
        ['[','\\','<escbkt>', ']'],
    ],
    '<alpha>' : [[c] for c in string.printable if c not in '[]()*+'],
    '<singlechar>' : [[c] for c in string.printable if c not in '[]'],
    '<escbkt>' : [['['], [']']],
}

REGEX_START = '<start>'


#if __name__ == '__main__':
    #my_input = '(a|b)+(c)*'
    #regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    #parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
    #fuzzer.display_tree(parsed_expr)


class RegexToGrammar:
    def __init__(self):
        self.parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
        self.counter = 0

    def parse(self, inex):
        parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
        return parsed_expr

    def convert(self, node, grammar):
        key, children = node
        assert key == '<regex>'
        assert len(children) == 1
        key, _ = children[0]
        if key == '<regexparen>':
            return self.convert_paren(children[0], grammar)
        elif key == '<regexstar>':
            return self.convert_star(children[0], grammar)
        elif key == '<regexplus>':
            return self.convert_plus(children[0], grammar)
        elif key == '<regexconcat>':
            return self.convert_concat(children[0], grammar)
        elif key == '<regexalts>':
            return self.convert_alts(children[0], grammar)
        elif key == '<alpha>':
            return self.convert_alpha(children[0], grammar)
        elif key == '<bracket>':
            assert False
        else:
            assert False
        return key

    def new_key(self):
        k = self.counter
        self.counter += 1
        return '<%d>' % k

    def convert_paren(self, node, grammar):
        key, children = node
        assert len(children) == 3
        key = self.convert(children[1], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key]]
        return nkey

    def convert_alts(self, node, grammar):
        key, children = node
        key1 = self.convert(children[0], grammar)
        # |
        key2 = self.convert(children[2], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key1], [key2]]
        return nkey

    def convert_concat(self, node, grammar):
        key, children = node
        key1 = self.convert(children[0], grammar)
        key2 = self.convert(children[1], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key1, key2]]
        return nkey

    def convert_star(self, node, grammar):
        key, children = node
        assert len(children) == 2
        key, children = children[0] # the 1 is *
        # could be one of paren, alpha and bracket
        if key == '<regexparen>':
            assert len(children) == 3 # (<expr>)
            key = self.convert(children[1], grammar)
            nkey = self.new_key()
            grammar[nkey] = [[key, nkey]]
            return nkey
        elif key == '<alpha>':
            nkey = self.new_key()
            grammar[nkey] = [[children[0][0], nkey], []]
            return nkey
        elif key == '<bracket>':
            assert False
        key = self.convert(children[0], grammar)
        nkey = self.new_key()
        grammar[nkey] = [[key, nkey]]
        return nkey

    def convert_alpha(self, node, grammar):
        key, children = node
        assert key == '<alpha>'
        nkey = self.new_key()
        grammar[nkey] = [[children[0][0]]]
        return nkey

    def to_grammar(self, inex):
        parsed = self.parse(inex)
        key, children = parsed
        assert key == '<start>'
        assert len(children) == 1
        grammar = {}
        start = self.convert(children[0], grammar)
        return start, grammar

if __name__ == '__main__':
    my_input = '(a|b)c*'
    print(my_input)
    regex_parser = earleyparser.EarleyParser(REGEX_GRAMMAR)
    parsed_expr = list(regex_parser.parse_on(my_input, REGEX_START))[0]
    #parsed_expr = list(regex_parser.parse_on(my_input, '<regexparen>'))[0]
    fuzzer.display_tree(parsed_expr)
    s, g = RegexToGrammar().to_grammar(my_input)
    gatleast.display_grammar(g, s)
