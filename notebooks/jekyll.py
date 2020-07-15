# modification of config created here: https://gist.github.com/cscorley/9144544
from urllib.parse import quote  # Py 3
import os
import sys

f = None
for arg in sys.argv:
    if arg.endswith('.ipynb'):
        f = arg.split('.ipynb')[0]
        break

c = get_config()
c.NbConvertApp.export_format = 'markdown'
c.MarkdownExporter.template_path = ['./'] # point this to your jekyll template file
c.MarkdownExporter.template_file = 'jekyll'
c.Application.verbose_crash=True

# modify this function to point your images to a custom path
# by default this saves all images to a directory 'images' in the root of the blog directory
def path2support(path):
    """Turn a file path into a URL"""
    # resources/posts/
    return '{{ BASE_PATH }}/resources/posts/' + os.path.splitext(os.path.basename(f))[0] + '/' + os.path.basename(path)

c.MarkdownExporter.filters = {'path2support': path2support}

if f:
    c.NbConvertApp.output_base = 'notebook' #f.lower().replace(' ', '-')
    c.FilesWriter.build_directory = './build' # point this to your build directory
