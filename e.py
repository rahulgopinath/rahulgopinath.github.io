#!/usr/bin/env python3
import sys
from html import escape
clean_html = sys.stdin.read().strip()
if clean_html[0:4] == '```': clean_html = clean_html[4:]
if clean_html[-3:] == '```': clean_html = clean_html[:-3]
scraped_html = escape(clean_html)
print('''
<!--
############
%s
############
-->
''' % clean_html)
print('''
<form name='python_run_form'>
<textarea cols="40" rows="4" name='python_edit'>''')
print(scraped_html)
print('''\
</textarea><br />
<pre class='Output' name='python_output'></pre>
<div name='python_canvas'></div>
</form>
''')
