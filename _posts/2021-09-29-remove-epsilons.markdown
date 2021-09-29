---
published: true
title: Remove Empty (Epsilon) Rules From a Context-Free Grammar.
layout: post
comments: true
tags: python
categories: post
---
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.9/';</script>
<script src="/resources/pyodide/full/3.9/pyodide.js"></script>
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/codemirror.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/solarized.css">
<link rel="stylesheet" type="text/css" media="all" href="/resources/skulpt/css/env/editor.css">

<script src="/resources/skulpt/js/codemirrorepl.js" type="text/javascript"></script>
<script src="/resources/skulpt/js/python.js" type="text/javascript"></script>
<script src="/resources/pyodide/js/env/editor.js" type="text/javascript"></script>

**Important:** [Pyodide](https://pyodide.readthedocs.io/en/latest/) takes time to initialize.
Initialization completion is indicated by a red border around *Run all* button.
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
In the previous post about [uniform random sampling from grammars](https://rahul.gopinath.org/post/2021/07/27/random-sampling-from-context-free-grammar/),
I mentioned that the algorithm expects an *epsilon-free* grammar. That is,
the grammar should contain no empty rules. Unfortunately, empty rules are
quite useful for describing languages. For example, to specify that we need
zero or more white space characters, the following definition of `<spaceZ>`
is the ideal representation.

<!--
############
grammar = {
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        []
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ]
}

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
grammar = {
    &quot;&lt;spaceZ&gt;&quot;: [
        [ &quot;&lt;space&gt;&quot;, &quot;&lt;spaceZ&gt;&quot; ],
        []
    ],
    &quot;&lt;space&gt;&quot;: [
        [&#x27; &#x27;],
        [&#x27;\t&#x27;],
        [&#x27;\n&#x27;]
    ]
}
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
So, what can we do? In fact, it is possible to transform the grammar such that
it no longer contain epsilon rules. The idea is that any rule that references
a nonterminal that can be empty can be represented by skipping in a duplicate
rule. When there are multiple such empty-able nonterminals, you need to
produce every combination of skipping them.
But first, let us tackle an easier task. We want to remove those nonterminals
that exclusively represent an empty string. E.g.

<!--
############
emptyG = {
    "<start>": [
        ["<spaceZ>"]
            ],
    "<spaceZ>": [
        [ "<space>", "<spaceZ>" ],
        ['<empty>']
    ],
    "<space>": [
        [' '],
        ['\t'],
        ['\n']
    ],
    '<empty>': [[]]
}
emptyS = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
emptyG = {
    &quot;&lt;start&gt;&quot;: [
        [&quot;&lt;spaceZ&gt;&quot;]
            ],
    &quot;&lt;spaceZ&gt;&quot;: [
        [ &quot;&lt;space&gt;&quot;, &quot;&lt;spaceZ&gt;&quot; ],
        [&#x27;&lt;empty&gt;&#x27;]
    ],
    &quot;&lt;space&gt;&quot;: [
        [&#x27; &#x27;],
        [&#x27;\t&#x27;],
        [&#x27;\n&#x27;]
    ],
    &#x27;&lt;empty&gt;&#x27;: [[]]
}
emptyS = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We also load a few prerequisites

<!--
############
import sys, imp
import itertools as I
import random

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
        with open(module_loc, encoding='utf-8') as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
import sys, imp
import itertools as I
import random

def make_module(modulesource, sourcestr, modname):
    codeobj = compile(modulesource, sourcestr, &#x27;exec&#x27;)
    newmodule = imp.new_module(modname)
    exec(codeobj, newmodule.__dict__)
    return newmodule

def import_file(name, location):
    if &quot;pyodide&quot; in sys.modules:
        import pyodide
        github_repo = &#x27;https://raw.githubusercontent.com/&#x27;
        my_repo =  &#x27;rahulgopinath/rahulgopinath.github.io&#x27;
        module_loc = github_repo + my_repo + &#x27;/master/notebooks/%s&#x27; % location
        module_str = pyodide.open_url(module_loc).getvalue()
    else:
        module_loc = &#x27;./notebooks/%s&#x27; % location
        with open(module_loc, encoding=&#x27;utf-8&#x27;) as f:
            module_str = f.read()
    return make_module(module_str, module_loc, name)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We import the following modules

<!--
############
fuzzer = import_file('fuzzer', '2019-05-28-simplefuzzer-01.py')
gatleast = import_file('gatleast', '2021-09-09-fault-inducing-grammar.py')
grandom = import_file('grandom', '2021-07-27-random-sampling-from-context-free-grammar.py')

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
fuzzer = import_file(&#x27;fuzzer&#x27;, &#x27;2019-05-28-simplefuzzer-01.py&#x27;)
gatleast = import_file(&#x27;gatleast&#x27;, &#x27;2021-09-09-fault-inducing-grammar.py&#x27;)
grandom = import_file(&#x27;grandom&#x27;, &#x27;2021-07-27-random-sampling-from-context-free-grammar.py&#x27;)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Note that we still need an empty expansion inside the definition. i.e `[[]]`.
Leaving `<empty>` without an expansion, i.e. `[]` means that `<empty>` can't
be expanded, and hence we will have an invalid grammar.
## Remove empty keys

<!--
############
class GrammarShrinker:
    def __init__(self, grammar, start):
        self.grammar, self.start = grammar, start
        self.processed = set()

    def remove_empty_rule_keys(self):
        while True:
            keys_to_delete = []
            for key in self.grammar:
                if key == self.start: continue
                if self.grammar[key] == [[]]:
                    keys_to_delete.append(key)
            if not keys_to_delete: break
            self.grammar = {k:[[t for t in r if t not in keys_to_delete]
                for r in self.grammar[k]]
                    for k in self.grammar if k not in keys_to_delete}
        return self.grammar

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker:
    def __init__(self, grammar, start):
        self.grammar, self.start = grammar, start
        self.processed = set()

    def remove_empty_rule_keys(self):
        while True:
            keys_to_delete = []
            for key in self.grammar:
                if key == self.start: continue
                if self.grammar[key] == [[]]:
                    keys_to_delete.append(key)
            if not keys_to_delete: break
            self.grammar = {k:[[t for t in r if t not in keys_to_delete]
                for r in self.grammar[k]]
                    for k in self.grammar if k not in keys_to_delete}
        return self.grammar
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gatleast.display_grammar(emptyG, emptyS)
gs = GrammarShrinker(emptyG, emptyS)
newG, newS = gs.remove_empty_rule_keys(), emptyS
gatleast.display_grammar(newG, newS)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gatleast.display_grammar(emptyG, emptyS)
gs = GrammarShrinker(emptyG, emptyS)
newG, newS = gs.remove_empty_rule_keys(), emptyS
gatleast.display_grammar(newG, newS)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now we are ready to tackle the more complex part: That of removing epsilon
rules. First, we need to identify such rules that are empty.
## Finding empty (epsilon) rules

<!--
############
class GrammarShrinker(GrammarShrinker):
    def find_epsilon_rules(self):
        e_rules = []
        for key in self.grammar:
            if key == self.start: continue
            rules = self.grammar[key]
            for i, r in enumerate(rules):
                if not r:
                    e_rules.append((key, i))
        return e_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker(GrammarShrinker):
    def find_epsilon_rules(self):
        e_rules = []
        for key in self.grammar:
            if key == self.start: continue
            rules = self.grammar[key]
            for i, r in enumerate(rules):
                if not r:
                    e_rules.append((key, i))
        return e_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gs = GrammarShrinker(newG, newS)
erules = gs.find_epsilon_rules()
print('Empty rules:')
for key,rule in erules:
    print('',key,rule)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(newG, newS)
erules = gs.find_epsilon_rules()
print(&#x27;Empty rules:&#x27;)
for key,rule in erules:
    print(&#x27;&#x27;,key,rule)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Now that we can find epsilon rules, we need generate all combinations of
the corresponding keys, so that we can generate corresponding rules.

<!--
############
class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys, cur_key):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        if (cur_key, tuple(rule)) in self.processed: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            for a in I.combinations(positions, n):
                if a or cur_key not in self.processed:
                    combinations.append(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            new_rules.append(new_rule)
        self.processed.add((cur_key, tuple(rule)))
        return new_rules

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker(GrammarShrinker):
    def rule_combinations(self, rule, keys, cur_key):
        positions = [i for i,t in enumerate(rule) if t in keys]
        if not positions: return [rule]
        if (cur_key, tuple(rule)) in self.processed: return [rule]
        combinations = []
        for n in range(len(rule)+1):
            for a in I.combinations(positions, n):
                if a or cur_key not in self.processed:
                    combinations.append(a)
        new_rules = []
        for combination in combinations:
            new_rule = [t for i,t in enumerate(rule) if i not in combination]
            new_rules.append(new_rule)
        self.processed.add((cur_key, tuple(rule)))
        return new_rules
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can use it thus:

<!--
############
gs = GrammarShrinker(newG, newS)
zrule = newG['<spaceZ>'][0]
print('Rule to produce combinations:', zrule)
erules = gs.find_epsilon_rules()
comb = gs.rule_combinations(zrule, [k for k,rule in erules], '<spaceZ>')
for c in comb:
    print('', c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(newG, newS)
zrule = newG[&#x27;&lt;spaceZ&gt;&#x27;][0]
print(&#x27;Rule to produce combinations:&#x27;, zrule)
erules = gs.find_epsilon_rules()
comb = gs.rule_combinations(zrule, [k for k,rule in erules], &#x27;&lt;spaceZ&gt;&#x27;)
for c in comb:
    print(&#x27;&#x27;, c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Let us try a larger grammar. This is the JSON grammar.

<!--
############
jsonG = {
    "<start>": [["<json>"]],
    "<json>": [["<element>"]],
    "<element>": [["<ws>", "<value>", "<ws>"]],
    "<value>": [["<object>"], ["<array>"], ["<string>"], ["<number>"],
                ["true"], ["false"],
                ["null"]],
    "<object>": [["{", "<ws>", "}"], ["{", "<members>", "}"]],
    "<members>": [["<member>", "<symbol-2>"]],
    "<member>": [["<ws>", "<string>", "<ws>", ":", "<element>"]],
    "<array>": [["[", "<ws>", "]"], ["[", "<elements>", "]"]],
    "<elements>": [["<element>", "<symbol-1-1>"]],
    "<string>": [["\"", "<characters>", "\""]],
    "<characters>": [["<character-1>"]],
    "<character>": [["0"], ["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"],
                    ["8"], ["9"], ["a"], ["b"], ["c"], ["d"], ["e"], ["f"],
                    ["g"], ["h"], ["i"], ["j"], ["k"], ["l"], ["m"], ["n"],
                    ["o"], ["p"], ["q"], ["r"], ["s"], ["t"], ["u"], ["v"],
                    ["w"], ["x"], ["y"], ["z"], ["A"], ["B"], ["C"], ["D"],
                    ["E"], ["F"], ["G"], ["H"], ["I"], ["J"], ["K"], ["L"],
                    ["M"], ["N"], ["O"], ["P"], ["Q"], ["R"], ["S"], ["T"],
                    ["U"], ["V"], ["W"], ["X"], ["Y"], ["Z"], ["!"], ["#"],
                    ["$"], ["%"], ["&"], ["\""], ["("], [")"], ["*"], ["+"],
                    [","], ["-"], ["."], ["/"], [":"], [";"], ["<"], ["="],
                    [">"], ["?"], ["@"], ["["], ["]"], ["^"], ["_"], ["`"],
                    ["{"], ["|"], ["}"], ["~"], [" "], ["<esc>"]],
    "<esc>": [["\\","<escc>"]],
    "<escc>": [["\\"],["b"],["f"], ["n"], ["r"],["t"],["\""]],
    "<number>": [["<int>", "<frac>", "<exp>"]],
    "<int>": [["<digit>"], ["<onenine>", "<digits>"], ["-", "<digits>"],
              ["-", "<onenine>", "<digits>"]],
    "<digits>": [["<digit-1>"]],
    "<digit>": [["0"], ["<onenine>"]],
    "<onenine>": [["1"], ["2"], ["3"], ["4"], ["5"], ["6"], ["7"], ["8"],
                  ["9"]],
    "<frac>": [[], [".", "<digits>"]],
    "<exp>": [[], ["E", "<sign>", "<digits>"], ["e", "<sign>", "<digits>"]],
    "<sign>": [[], ["+"], ["-"]],
    "<ws>": [["<sp1>", "<ws>"], []],
    "<sp1>": [[" "],["\n"],["\t"],["\r"]],
    "<symbol>": [[",", "<members>"]],
    "<symbol-1>": [[",", "<elements>"]],
    "<symbol-2>": [[], ["<symbol>", "<symbol-2>"]],
    "<symbol-1-1>": [[], ["<symbol-1>", "<symbol-1-1>"]],
    "<character-1>": [[], ["<character>", "<character-1>"]],
    "<digit-1>": [["<digit>"], ["<digit>", "<digit-1>"]]
}
jsonS = '<start>'

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
jsonG = {
    &quot;&lt;start&gt;&quot;: [[&quot;&lt;json&gt;&quot;]],
    &quot;&lt;json&gt;&quot;: [[&quot;&lt;element&gt;&quot;]],
    &quot;&lt;element&gt;&quot;: [[&quot;&lt;ws&gt;&quot;, &quot;&lt;value&gt;&quot;, &quot;&lt;ws&gt;&quot;]],
    &quot;&lt;value&gt;&quot;: [[&quot;&lt;object&gt;&quot;], [&quot;&lt;array&gt;&quot;], [&quot;&lt;string&gt;&quot;], [&quot;&lt;number&gt;&quot;],
                [&quot;true&quot;], [&quot;false&quot;],
                [&quot;null&quot;]],
    &quot;&lt;object&gt;&quot;: [[&quot;{&quot;, &quot;&lt;ws&gt;&quot;, &quot;}&quot;], [&quot;{&quot;, &quot;&lt;members&gt;&quot;, &quot;}&quot;]],
    &quot;&lt;members&gt;&quot;: [[&quot;&lt;member&gt;&quot;, &quot;&lt;symbol-2&gt;&quot;]],
    &quot;&lt;member&gt;&quot;: [[&quot;&lt;ws&gt;&quot;, &quot;&lt;string&gt;&quot;, &quot;&lt;ws&gt;&quot;, &quot;:&quot;, &quot;&lt;element&gt;&quot;]],
    &quot;&lt;array&gt;&quot;: [[&quot;[&quot;, &quot;&lt;ws&gt;&quot;, &quot;]&quot;], [&quot;[&quot;, &quot;&lt;elements&gt;&quot;, &quot;]&quot;]],
    &quot;&lt;elements&gt;&quot;: [[&quot;&lt;element&gt;&quot;, &quot;&lt;symbol-1-1&gt;&quot;]],
    &quot;&lt;string&gt;&quot;: [[&quot;\&quot;&quot;, &quot;&lt;characters&gt;&quot;, &quot;\&quot;&quot;]],
    &quot;&lt;characters&gt;&quot;: [[&quot;&lt;character-1&gt;&quot;]],
    &quot;&lt;character&gt;&quot;: [[&quot;0&quot;], [&quot;1&quot;], [&quot;2&quot;], [&quot;3&quot;], [&quot;4&quot;], [&quot;5&quot;], [&quot;6&quot;], [&quot;7&quot;],
                    [&quot;8&quot;], [&quot;9&quot;], [&quot;a&quot;], [&quot;b&quot;], [&quot;c&quot;], [&quot;d&quot;], [&quot;e&quot;], [&quot;f&quot;],
                    [&quot;g&quot;], [&quot;h&quot;], [&quot;i&quot;], [&quot;j&quot;], [&quot;k&quot;], [&quot;l&quot;], [&quot;m&quot;], [&quot;n&quot;],
                    [&quot;o&quot;], [&quot;p&quot;], [&quot;q&quot;], [&quot;r&quot;], [&quot;s&quot;], [&quot;t&quot;], [&quot;u&quot;], [&quot;v&quot;],
                    [&quot;w&quot;], [&quot;x&quot;], [&quot;y&quot;], [&quot;z&quot;], [&quot;A&quot;], [&quot;B&quot;], [&quot;C&quot;], [&quot;D&quot;],
                    [&quot;E&quot;], [&quot;F&quot;], [&quot;G&quot;], [&quot;H&quot;], [&quot;I&quot;], [&quot;J&quot;], [&quot;K&quot;], [&quot;L&quot;],
                    [&quot;M&quot;], [&quot;N&quot;], [&quot;O&quot;], [&quot;P&quot;], [&quot;Q&quot;], [&quot;R&quot;], [&quot;S&quot;], [&quot;T&quot;],
                    [&quot;U&quot;], [&quot;V&quot;], [&quot;W&quot;], [&quot;X&quot;], [&quot;Y&quot;], [&quot;Z&quot;], [&quot;!&quot;], [&quot;#&quot;],
                    [&quot;$&quot;], [&quot;%&quot;], [&quot;&amp;&quot;], [&quot;\&quot;&quot;], [&quot;(&quot;], [&quot;)&quot;], [&quot;*&quot;], [&quot;+&quot;],
                    [&quot;,&quot;], [&quot;-&quot;], [&quot;.&quot;], [&quot;/&quot;], [&quot;:&quot;], [&quot;;&quot;], [&quot;&lt;&quot;], [&quot;=&quot;],
                    [&quot;&gt;&quot;], [&quot;?&quot;], [&quot;@&quot;], [&quot;[&quot;], [&quot;]&quot;], [&quot;^&quot;], [&quot;_&quot;], [&quot;`&quot;],
                    [&quot;{&quot;], [&quot;|&quot;], [&quot;}&quot;], [&quot;~&quot;], [&quot; &quot;], [&quot;&lt;esc&gt;&quot;]],
    &quot;&lt;esc&gt;&quot;: [[&quot;\\&quot;,&quot;&lt;escc&gt;&quot;]],
    &quot;&lt;escc&gt;&quot;: [[&quot;\\&quot;],[&quot;b&quot;],[&quot;f&quot;], [&quot;n&quot;], [&quot;r&quot;],[&quot;t&quot;],[&quot;\&quot;&quot;]],
    &quot;&lt;number&gt;&quot;: [[&quot;&lt;int&gt;&quot;, &quot;&lt;frac&gt;&quot;, &quot;&lt;exp&gt;&quot;]],
    &quot;&lt;int&gt;&quot;: [[&quot;&lt;digit&gt;&quot;], [&quot;&lt;onenine&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;-&quot;, &quot;&lt;digits&gt;&quot;],
              [&quot;-&quot;, &quot;&lt;onenine&gt;&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;digits&gt;&quot;: [[&quot;&lt;digit-1&gt;&quot;]],
    &quot;&lt;digit&gt;&quot;: [[&quot;0&quot;], [&quot;&lt;onenine&gt;&quot;]],
    &quot;&lt;onenine&gt;&quot;: [[&quot;1&quot;], [&quot;2&quot;], [&quot;3&quot;], [&quot;4&quot;], [&quot;5&quot;], [&quot;6&quot;], [&quot;7&quot;], [&quot;8&quot;],
                  [&quot;9&quot;]],
    &quot;&lt;frac&gt;&quot;: [[], [&quot;.&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;exp&gt;&quot;: [[], [&quot;E&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;], [&quot;e&quot;, &quot;&lt;sign&gt;&quot;, &quot;&lt;digits&gt;&quot;]],
    &quot;&lt;sign&gt;&quot;: [[], [&quot;+&quot;], [&quot;-&quot;]],
    &quot;&lt;ws&gt;&quot;: [[&quot;&lt;sp1&gt;&quot;, &quot;&lt;ws&gt;&quot;], []],
    &quot;&lt;sp1&gt;&quot;: [[&quot; &quot;],[&quot;\n&quot;],[&quot;\t&quot;],[&quot;\r&quot;]],
    &quot;&lt;symbol&gt;&quot;: [[&quot;,&quot;, &quot;&lt;members&gt;&quot;]],
    &quot;&lt;symbol-1&gt;&quot;: [[&quot;,&quot;, &quot;&lt;elements&gt;&quot;]],
    &quot;&lt;symbol-2&gt;&quot;: [[], [&quot;&lt;symbol&gt;&quot;, &quot;&lt;symbol-2&gt;&quot;]],
    &quot;&lt;symbol-1-1&gt;&quot;: [[], [&quot;&lt;symbol-1&gt;&quot;, &quot;&lt;symbol-1-1&gt;&quot;]],
    &quot;&lt;character-1&gt;&quot;: [[], [&quot;&lt;character&gt;&quot;, &quot;&lt;character-1&gt;&quot;]],
    &quot;&lt;digit-1&gt;&quot;: [[&quot;&lt;digit&gt;&quot;], [&quot;&lt;digit&gt;&quot;, &quot;&lt;digit-1&gt;&quot;]]
}
jsonS = &#x27;&lt;start&gt;&#x27;
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Extract combinations.

<!--
############
gs = GrammarShrinker(jsonG, jsonS)
zrule = jsonG['<member>'][0]
erules = gs.find_epsilon_rules()
print('Rule to produce combinations:', zrule)
comb = gs.rule_combinations(zrule, [k for k,rule in erules], '<member>')
for c in comb:
    print('', c)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(jsonG, jsonS)
zrule = jsonG[&#x27;&lt;member&gt;&#x27;][0]
erules = gs.find_epsilon_rules()
print(&#x27;Rule to produce combinations:&#x27;, zrule)
comb = gs.rule_combinations(zrule, [k for k,rule in erules], &#x27;&lt;member&gt;&#x27;)
for c in comb:
    print(&#x27;&#x27;, c)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Here comes the last part, which stitches all these together.

<!--
############
class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        while True:
            self.remove_empty_rule_keys()
            e_rules = self.find_epsilon_rules()
            if not e_rules: break
            for e_key, index in e_rules:
                del self.grammar[e_key][index]
                assert self.grammar[e_key]
                self.processed.add(e_key)

            for key in self.grammar:
                rules_hash = {}
                for rule in self.grammar[key]:
                    # find e_key positions.
                    combs = self.rule_combinations(rule, [k for k,i in e_rules], key)
                    for nrule in combs:
                        rules_hash[str(nrule)] = nrule
                self.grammar[key] = [rules_hash[k] for k in rules_hash]


############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
class GrammarShrinker(GrammarShrinker):
    def remove_epsilon_rules(self):
        while True:
            self.remove_empty_rule_keys()
            e_rules = self.find_epsilon_rules()
            if not e_rules: break
            for e_key, index in e_rules:
                del self.grammar[e_key][index]
                assert self.grammar[e_key]
                self.processed.add(e_key)

            for key in self.grammar:
                rules_hash = {}
                for rule in self.grammar[key]:
                    # find e_key positions.
                    combs = self.rule_combinations(rule, [k for k,i in e_rules], key)
                    for nrule in combs:
                        rules_hash[str(nrule)] = nrule
                self.grammar[key] = [rules_hash[k] for k in rules_hash]
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
Using the complete epsilon remover.

<!--
############
gs = GrammarShrinker(jsonG, jsonS)
gs.remove_epsilon_rules()
gatleast.display_grammar(gs.grammar, gs.start)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
gs = GrammarShrinker(jsonG, jsonS)
gs.remove_epsilon_rules()
gatleast.display_grammar(gs.grammar, gs.start)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
We can now count the strings produced by the epsilon free grammar

<!--
############
rscfg = grandom.RandomSampleCFG(gs.grammar)
max_len = 5
rscfg.produce_shared_forest(gs.start, max_len)
for i in range(10):
    v, tree = rscfg.random_sample(gs.start, 5)
    string = fuzzer.tree_to_string(tree)
    print("mystring:", repr(string), "at:", v)

############
-->
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
rscfg = grandom.RandomSampleCFG(gs.grammar)
max_len = 5
rscfg.produce_shared_forest(gs.start, max_len)
for i in range(10):
    v, tree = rscfg.random_sample(gs.start, 5)
    string = fuzzer.tree_to_string(tree)
    print(&quot;mystring:&quot;, repr(string), &quot;at:&quot;, v)
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
As before, the runnable source of this notebook is [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-29-remove-epsilons.py).

<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
