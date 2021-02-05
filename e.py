#!/usr/bin/env python3
import sys
from html import escape
clean_html = sys.stdin.read()
scraped_html = escape(clean_html)
print('''
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>
''')
print(scraped_html)
print('''
</textarea><br />
<button type="button" name="python_run">Run</button>
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
''')
