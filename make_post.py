#!/usr/bin/env python
import sys
import itertools as I
from html import escape

def split_data(data):
    chunks = [list(g) for k,g in I.groupby(data, key=lambda line: line[0] == '#')]

    processed_data = []
    for chunk in chunks:
        if chunk[0][0] == '#': # comment chunk
            assert chunk[0][1] == ' '
            comment = ''.join([line[2:] for line in chunk])
            processed_data.append(('comment', comment))
        else:
            code = ''.join([line for line in chunk])
            processed_data.append(('code', code))
    return processed_data


def print_data(processed_data):
    for kind, chunk in processed_data:
        if kind == 'comment':
            sys.stdout.buffer.write(chunk.encode('utf8'))
        elif kind == 'code':
            scraped_chunk = escape(chunk)
            print('''\
<!--
############
%s
############
-->''' % chunk)
            print('''\
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>''')
            print(scraped_chunk)
            print('''\
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>''')

def main(args):
    fn =  args[0]
    with open(fn, 'r', encoding='utf-8') as f:
        data = f.readlines()
    result = split_data(data)
    print('''\
---
published: true
title: 
layout: post
comments: true
tags: 
categories: post
---
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
</form>''')

    print_data(result)
    print('''\
<form name='python_run_form'>
<button type="button" name="python_run_all">Run all</button>
</form>
''')

main(sys.argv[1:])
