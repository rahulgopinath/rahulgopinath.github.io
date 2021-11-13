#!/usr/bin/env python
# USAGE: ./make_post.py notebooks/2021-02-21-python-pipes.py > _posts/2021-02-21-python-pipes.markdown
import sys
import itertools as I
from html import escape


def split_data(data):
    chunks = [list(g) for k,g in I.groupby(data, key=lambda line: line[0] == '#')]

    processed_data = []
    for chunk in chunks:
        if chunk[0][0] == '#': # comment chunk
            if chunk[0][1] == ' ':
                # remove extra newlines.
                comment = ''.join([line[2:] for line in chunk])
                processed_data.append(('comment', comment))
            elif chunk[0][1] == '@':
                wheels = [line[2:].strip() for line in chunk]
                processed_data.append(('wheel', [w for w in wheels if w.strip()]))
            elif chunk[0][1] == '^':
                wheels = [line[2:].strip() for line in chunk]
                processed_data.append(('sys_imports', [w for w in wheels if w.strip()]))
            else:
                assert False
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
                # find empty of first line
                e_l = 0
                for c in lines[0]:
                    if c == ' ': e_l += 1
                    else: break
                code = '\n'.join([l[e_l:] for l in lines])
                processed_data.append(('code', code))
    return processed_data


def print_data(processed_data):
    first_comment = True
    for kind, chunk in processed_data:
        if kind == 'comment':
            p(chunk)
            if first_comment:
                p('''
## Contents
{:.no_toc}

1. TOC
{:toc}

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
''')
            first_comment = False
        if kind == 'sys_imports':
            p('''
<details>
<summary> System Imports </summary>
<!--##### System Imports -->

These are available from Pyodide, but you may wish to make sure that they are
installed if you are attempting to run the program directly on the machine.

<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_sys_imports' name='python_edit'>
%s
</textarea>
</form>
</details>
''' % '\n'.join(['%s' % l for l in chunk]))

        if kind == 'wheel':
            p('''
<details>
<summary>Available Packages </summary>
<!--##### Available Packages-->

These are packages that refer either to my previous posts or to pure python
packages that I have compiled, and is available in the below locations. As
before, install them if you need to run the program directly on the machine.
<form name='python_run_form'>
<textarea cols="40" rows="4" id='python_pre_edit' name='python_edit'>
%s
</textarea>
</form>
</details>
''' % '\n'.join(['%s' % l for l in chunk]))
        elif kind == 'code':
            scraped_chunk = escape(chunk)
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
import os.path
from contextlib import redirect_stdout

def p(v):
    sys.stdout.buffer.write(v.encode('utf8'))

def main(args):
    fn =  args[0]
    if len(args) > 1:
        postname = args[1]
    else:
        postname = '_posts/%s.markdown' % os.path.splitext(os.path.basename(fn))[0]
    print('Writing to:', postname, file=sys.stderr)
    with open(fn, 'r', encoding='utf-8') as f:
        data = f.readlines()
    result = split_data(data)

    with open(postname, 'w+') as f:
        with redirect_stdout(f):
            print_data(result)
            p('''
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
''')

main(sys.argv[1:])
