#!/usr/bin/env python
import sys
import itertools as I
from html import escape

def p(v): sys.stdout.buffer.write(v.encode('utf8'))

def split_data(data):
    chunks = [list(g) for k,g in I.groupby(data, key=lambda line: line[0] == '#')]

    processed_data = []
    for chunk in chunks:
        if chunk[0][0] == '#': # comment chunk
            assert chunk[0][1] == ' '
            # remove extra newlines.
            comment = ''.join([line[2:] for line in chunk])
            processed_data.append(('comment', comment))
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
                if lines[0] == "if __name__ == '__main__':": lines = lines[1:]
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
                p('''\
<script type="text/javascript">window.languagePluginUrl='/resources/pyodide/full/3.8/';</script>
<script src="/resources/pyodide/full/3.8/pyodide.js"></script>
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
            p(scraped_chunk)
            p('''
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
''')

def main(args):
    fn =  args[0]
    with open(fn, 'r', encoding='utf-8') as f:
        data = f.readlines()
    result = split_data(data)

    print_data(result)
    p('''
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
''')

main(sys.argv[1:])
