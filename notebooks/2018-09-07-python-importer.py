# ---
# published: true
# title: Importing Python Modules
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# In the [previous post](/post/2018/09/06/peg-parsing/) I discussed how to
# implement simple parsing expression grammar based parsing, and I mentioned
# that the notebook is available in [runnable source form](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2018-09-06-peg-parsing.py).
# This brings a question however. How do we make use of this notebook in later
# posts? A way forward is to hook into the Python import system.
#
# We start with our prerequisites

import sys, os, ast
import types
import importlib.abc
import importlib.machinery

# ## MetaPath
# 
# Python finds
# and imports modules using a two step process. In the first step, it searches
# through objects in `sys.meta_path`. These are `MetaPathFinder` objects that
# implement a single method `find_spec()` and will respond with a module spec
# if that object serves this particular module.
# Hence, we define our meta path finder, which if present in the system
# meta-path, will allow us to substitute our own module loaders.


class MetaPathFinderInWeb(importlib.abc.MetaPathFinder):
    def __init__(self, loaders): self._loaders = loaders

    def find_spec(self, fullname, path, target=None):
        for loader in self._loaders:
            if self._loaders[loader].has(fullname):
                return importlib.machinery.ModuleSpec(fullname, self._loaders[loader])
        return None

# ## Loaders
#
# Next we define our own loaders. A loader only needs to provide two functions
# `create_module(self, spec)` which returns an new module e.g. `types.ModuleType(m_name)`
# and `exec_module(self, module)` which executes the code of our module in the
# module object passed in as the parameter. While we can do this, there is a
# better way. Python provides a number of specialized implementations of this
# class that provides a lot of functionalities we need.
# `SourceLoader` class is one such. It needs us to implement `get_filename()`
# that takes the `module_name` and returns the file location of the module. Next
# is `get_data()` which takes that file location, and returns the source code.
# So, we implement a subclass that contains a few utility methods.
#
# ### MyLoader
#  
# Provides basic services for module loading. It requires another method to be
# defined. `fetch()` when given the module location, fetches the module source
# (if it can't find it, it returns `None`). If we have the `fetch()` method
# defined in a subclass, it is used to find which modules we can serve.
# For any module we can serve, we register ourselves and return `True` for `has()`.

class MyLoader(importlib.abc.SourceLoader):
    def __init__(self, sources):
        self.modules = {}
        self.locations = {}
        for m_loc in sources:
            src = self.fetch(m_loc)
            if src is None: continue
            m_name = self.load_src(src, m_loc)
            self.modules[m_name] = m_loc
            self.locations[m_loc] = src

    def load_src(self, src, m_loc):
        myast = ast.parse(src, filename=m_loc, mode='exec')
        if myast.body[-1].__class__ == ast.Assign and myast.body[-1].targets[0].id == '__MODULE_NAME__':
            return myast.body[-1].value.s
        return self.convert_to_name(m_loc)

    def convert_to_name(self, name):
        return name[len('notebooks/2018-09-06-'):-3].replace('-','').replace('_','')

    def get_data(self, m_loc):
        return self.locations[m_loc]

    def get_filename(self, fullname):
        return self.modules[fullname]

    def has(self, fullname):
        return fullname in self.modules

# ### LocalLoader
# The simplest loader. Checks for existence in the local file system.

class LocalLoader(MyLoader):
    def fetch(self, m_loc):
        if not os.path.exists(m_loc): return None
        with open(m_loc, encoding='utf-8') as f: return f.read()

# ### WebLoader
# The web loader checks for accessibility of the module through URL given.

class WebLoader(MyLoader):
    def fetch(self, m_loc):
        import urllib.request
        import urllib.error
        try:
            github_repo = 'https://raw.githubusercontent.com/'
            my_repo =  'rahulgopinath/rahulgopinath.github.io'
            m_loc = github_repo + my_repo + '/master/%s' % m_loc
            return urllib.request.urlopen(m_loc).read()
        except urllib.error.URLError as e:
            return None

# ### PyodideLoader
# The pyodide loader is active only if the environment is a browser.

class PyodideLoader(MyLoader):
    def fetch(self, m_loc):
        if "pyodide" not in sys.modules: return None
        import pyodide
        github_repo = 'https://raw.githubusercontent.com/'
        my_repo =  'rahulgopinath/rahulgopinath.github.io'
        m_loc = github_repo + my_repo + '/master/notebooks/%s' % m_loc
        return pyodide.open_url(m_loc).getvalue()

# ## Importer
# The imorter class holds everything together.

class Importer:
    def __init__(self, source_files):
        self._loader = {
                'local': LocalLoader(source_files),
                'web': WebLoader(source_files),
                'pyodide': PyodideLoader(source_files)}
        sys.meta_path.append(MetaPathFinderInWeb(self._loader))

# Testing it.

if __name__ == '__main__':
    importer = Importer(['notebooks/2018-09-06-peg-parsing.py'])
    import pegparsing
    print(pegparsing.term_grammar)

# As before the source code is available [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2018-09-07-python-importer.py).

