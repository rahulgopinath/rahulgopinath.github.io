#!/usr/bin/env python
# USAGE: ./make_post.py notebooks/2021-02-21-python-pipes.py > _posts/2021-02-21-python-pipes.markdown
import sys
import os
import json
import itertools as I
from html import escape

# versioned packages
PKGVS = {}
PKGS = {}
VALS = {}

def load_notebooks(my_pkgs):
    global PKGVS
    global PKGS
    global VALS

    with open(my_pkgs) as f:
        VALS=json.load(fp=f)

    for notebook in VALS:
        pkg, desc, ver = VALS[notebook]
        name = "%s-%s" % (pkg, ver)
        assert name not in PKGVS
        assert pkg not in PKGS
        PKGVS[name] = [pkg, ver, desc, notebook]
        PKGS[pkg] = [desc, notebook, ver]

load_notebooks('pkgs.json')

def notebook_to_post(notebook):
    "notebooks/2018-09-06-peg-parsing.py"
    '/post/2019/12/08/python-controlflow/'
    post_str = notebook[len('notebooks/'):-3]
    year,month,date = post_str.split('-')[:3]
    post_val = '-'.join(post_str.split('-')[3:])
    return '/post/%s/%s/%s/%s/' % (year, month, date, post_val)


def get_post_name(pkg):
    if pkg in PKGS:
        desc, notebook, ver = PKGS[pkg]
        return ' from "<a href="%s">%s</a>".' % (notebook_to_post(notebook), PKGS[pkg][0])
    else: return ''

def _scan_triple_state(line, state):
    """Walk one line updating triple-quote string state ('', \"\"\" or None=outside)."""
    i = 0
    while i < len(line):
        if state is None:
            if line[i:i+3] in ("'''", '"""'):
                state = line[i:i+3]
                i += 3
            else:
                i += 1
        else:
            if line[i:i+3] == state:
                state = None
                i += 3
            else:
                i += 1
    return state

def split_data(data):
    # Group lines into comment/code runs, but never split inside a triple-quoted string.
    triple_state = None
    raw_chunks = []          # list of (is_comment, [lines])
    cur_lines = []
    cur_is_comment = None

    for line in data:
        is_comment = (triple_state is None) and len(line) > 0 and line[0] == '#'
        triple_state = _scan_triple_state(line, triple_state)

        if cur_is_comment is None:
            cur_is_comment = is_comment
        if is_comment != cur_is_comment:
            raw_chunks.append((cur_is_comment, cur_lines))
            cur_lines = []
            cur_is_comment = is_comment
        cur_lines.append(line)

    if cur_lines:
        raw_chunks.append((cur_is_comment, cur_lines))

    processed_data = []
    for is_comment, chunk in raw_chunks:
        if is_comment:
            if chunk[0][1] == ' ':
                comment = ''.join([line[2:] for line in chunk])
                processed_data.append(('comment', comment))
            elif chunk[0][1] == '@':
                wheels = [line[2:].strip() for line in chunk]
                processed_data.append(('wheel', [w for w in wheels if w.strip()]))
            elif chunk[0][1] == '^':
                wheels = [line[2:].strip() for line in chunk]
                processed_data.append(('sys_imports', [w for w in wheels if w.strip()]))
            elif chunk[0][1] == '\n':
                comment = ''.join([line[2:] for line in chunk])
                processed_data.append(('comment', comment))
            else:
                assert False, repr(chunk[0])
        else:
            skip_empty = True
            lines = []
            for line in chunk:
                if line.strip() == '' and skip_empty:
                    pass
                else:
                    skip_empty = False
                    lines.append(line.rstrip())
            if lines:
                if lines[0] == "if __name__ == '__main__':":
                    lines = lines[1:]
                import textwrap as _textwrap
                code = _textwrap.dedent('\n'.join(lines))
                processed_data.append(('code', code))
    return processed_data

# Grammar blocks that exceed this line count are folded into a <details> element.
FOLD_LINES = 15
import re as _re
# Matches a fuzzingbook-style grammar dict entry: '<nonterminal>': [
_GRAMMAR_DICT = _re.compile(r"'<[A-Za-z0-9_-]+>':\s*\[|\"<[A-Za-z0-9_-]+>\":\s*\[")

def _should_fold(code):
    """Return True for large blocks that are grammar data definitions."""
    lines = [l for l in code.split('\n') if l.strip()]
    if len(lines) < FOLD_LINES:
        return False
    # Never fold function/class definitions — they're core content
    if lines and _re.match(r'\s*(def |class )', lines[0]):
        return False
    # Only fold blocks that contain grammar dict entries like '<nt>': [...]
    return bool(_GRAMMAR_DICT.search(code))

def process_pkg_name(name):
    baselen = len('https://rahul.gopinath.org/py/')
    if os.getenv('LOCAL'):
        return '/py/%s' %  name[baselen:]
    else:
        return name

def get_pkg_desc(name):
    # , VALS[fn][1], notebook_to_post(fn) See the post "[%s](%s)" for further information.
    # https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
    baselen = len('https://rahul.gopinath.org/py/')
    wheel_name = name[baselen:]
    pkg_name, *rest = wheel_name.split('-')
    post_name = get_post_name(pkg_name)
    # we don't want to do this because students may run the page from somewhere else.
    # return '<li><a href="%s">%s</a>%s</li>' % (name[len('https://rahul.gopinath.org'):], wheel_name, post_name)
    if os.getenv('LOCAL'):
        return '<li><a href="/py/%s">%s</a>%s</li>' %  (name[baselen:] , wheel_name, post_name)
    else:
        return '<li><a href="%s">%s</a>%s</li>' % (name, wheel_name, post_name)

def print_data(processed_data):
    first_comment = True
    for kind, chunk in processed_data:
        if kind == 'comment':
            # Escape Liquid-special sequences so Jekyll doesn't misparse prose
            chunk = chunk.replace('{{', '{{ "{{" }}').replace('{%', '{{ "{%" }}')
            p(chunk)
            if first_comment:
                p('''
## Contents
{:.no_toc}

1. TOC
{:toc}

<script src="/resources/js/graphviz/index.min.js"></script>
<script>
// From https://github.com/hpcc-systems/hpcc-js-wasm
// Hosted for teaching.
var hpccWasm = window["@hpcc-js/wasm"];
function display_dot(dot_txt, div) {
    hpccWasm.graphviz.layout(dot_txt, "svg", "dot").then(svg => {
        div.innerHTML = svg;
    });
}
window.display_dot = display_dot
// from js import display_dot
</script>

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
''')
            first_comment = False
        if kind == 'sys_imports':
            p('''
<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<ol>
%s
</ol>
<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
%s
</textarea>
</form>
</div>
</details>
''' % ('\n'.join(['<li>%s</li>' % l for l in chunk]),'\n'.join(['%s' % l for l in chunk])))

        if kind == 'wheel':
            items = [get_pkg_desc(l) for l in chunk]
            pkg_desc = '\n'.join(items)
            pkg_names = '\n'.join(['%s' % process_pkg_name(l) for l in chunk])
            p('''
<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
To install, simply download the wheel file (`pkg.whl`) and install using
`pip install pkg.whl`.

<ol>
%s
</ol>

<div style='display:none'>
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
%s
</textarea>
</form>
</div>
</details>
''' % ( pkg_desc, pkg_names))
        elif kind == 'code':
            scraped_chunk = escape(chunk)
            fold = _should_fold(chunk)
            if fold:
                first_line = chunk.split('\n')[0][:60]
                nlines = len([l for l in chunk.split('\n') if l.strip()])
                p('<details><summary><code>%s</code> &nbsp;(%d lines)</summary>\n'
                  % (escape(first_line), nlines))
            p('''
<!--
############
%s
############
-->
''' % chunk)
            p('''\
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
''')
            p(scraped_chunk.strip())
            p('''
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
''')
            if fold:
                p('</details>\n')
import os.path
from contextlib import redirect_stdout

def p(v):
    sys.stdout.buffer.write(v.encode('utf8'))

def main(args):
    fn =  args[0]
    #assert fn in VALS
    if len(args) > 1:
        postname = args[1]
    else:
        postname = '_posts/%s.markdown' % os.path.splitext(os.path.basename(fn))[0]
    print('Writing to:', postname, file=sys.stderr)
    with open(fn, 'r', encoding='utf-8') as f:
        data = f.readlines()
    result = split_data(data)
    runnable_code = """\

## Artifacts

The runnable Python source for this notebook is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/%s).
""" % fn
    if fn in VALS:
        wheel = """
The installable python wheel `%s` is available [here](%s).
""" % (VALS[fn][0], '/py/%s-%s-py2.py3-none-any.whl' % (VALS[fn][0], VALS[fn][2]))
    else:
        wheel = ""

    with open(postname, 'w+') as f:
        with redirect_stdout(f):
            print_data(result)
            p('''
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
''')
            print(runnable_code)
            print(wheel)

main(sys.argv[1:])
