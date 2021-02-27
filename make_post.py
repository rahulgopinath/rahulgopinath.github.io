#!/usr/bin/env python
import sys
import itertools as I
from html import escape

def split_data(data):
    chunks = [i for i in I.groupby(data, key=lambda line: line[0] == '#')]

    processed_data = []
    for chunk in chunks:
        if chunk[0][0] == '#': # comment chunk
            comment = ''.join([line[1:] for line in chunk])
            processed_data.append(('comment', comment))
        else:
            code = ''.join([line for line in chunk])
            processed_data.append(('code', code))
    return processed_data


def print_data(processed_data):
    for kind, chunk in processed_data:
        if kind == 'comment':
            print(chunk)
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
    with open(fn) as f:
        data = f.readlines()
    result = split_data(data)
    print_data(result)

main(sys.argv[1:])
