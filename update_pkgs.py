VALS = {
"notebooks/2018-09-06-peg-parsing.py":                              ["pegparser", "Recursive descent parsing with Parsing Expression (PEG) and Context Free (CFG) Grammars", "0.0.1"],
"notebooks/2019-05-28-simplefuzzer-01.py":                          ["simplefuzzer", "The simplest grammar fuzzer in the world", "0.0.1"],
"notebooks/2019-12-04-hdd.py":                                      ["hdd", "Hierarchical Delta Debugging", "0.0.1"],
"notebooks/2019-12-07-python-mci.py":                               ["metacircularinterpreter", "Python Meta Circular Interpreter", "0.0.1"],
"notebooks/2020-08-03-simple-ddset.py":                             ["ddset", "Simple DDSet", "0.0.1"],
"notebooks/2021-02-06-earley-parsing.py":                           ["earleyparser", "Earley Parser", "0.0.1"],
"notebooks/2021-07-27-random-sampling-from-context-free-grammar.py":["cfgrandomsample", "Uniform Random Sampling of Strings from Context-Free Grammar", "0.0.1"],
"notebooks/2021-09-09-fault-inducing-grammar.py":                   ["gatleastsinglefault", "Specializing Context-Free Grammars for Inducing Faults", "0.0.1"],
"notebooks/2021-09-10-multiple-fault-grammars.py":                  ["gmultiplefaults", "Specializing Context-Free Grammars for Inducing Multiple Faults", "0.0.1"],
"notebooks/2021-09-11-fault-expressions.py":                        ["gfaultexpressions", "Fault Expressions for Specializing Context-Free Grammars", "0.0.1"],
"notebooks/2021-09-12-negated-fault-grammars.py":                   ["gnegatedfaults", "Specializing Context-Free Grammars for Not Inducing A Fault", "0.0.1"],
"notebooks/2021-09-29-remove-epsilons.py":                          ["cfgremoveepsilon", "Remove Empty (Epsilon) Rules From a Context-Free Grammar.", "0.0.1"],
"notebooks/2021-10-22-fuzzing-with-regular-expressions.py":         ["rxfuzzer", "iFuzzing With Regular Expressions", "0.0.1"],
"notebooks/2021-10-23-regular-expression-to-regular-grammar.py":    ["rxregular", "Regular Expression to Regular Grammar", "0.0.1"],
"notebooks/2021-10-24-canonical-regular-grammar.py":                ["rxcanonical", "Converting a Regular Expression to DFA using Regular Grammar", "0.0.1"],
"notebooks/2021-10-26-regular-grammar-expressions.py":              ["rxexpressions", "Conjunction, Disjunction, and Complement of Regular Grammars", "0.0.1"],
}

import plumbum
from plumbum import local
tar = local["tar"]
rm = local["rm"]
cat = local["cat"]
grep = local["grep"]
mkdir = local["mkdir"]
make = local["make"]
cp = local["cp"]

def to_url(notebook):
    name = notebook[len('notebooks/'):]
    date = name[0:len('2021-10-26-')]
    rest = name[len('2021-10-26-'):]
    assert rest[-3:] == '.py'
    return 'https://rahul.gopinath.org/post/' + date.replace('-', '/') + rest[:-3] + "/"

def replace_url(pkg, url):
    with open('pkg/setup.py') as f:
        data = f.readlines()
    my_data = []
    for d in data:
        if d.strip().startswith('url='): # ends with comma.
            assert d.strip()[-1] == ','
            spaces = len(d) - len(d.lstrip())
            d_ = d[:spaces] + 'url="' + url + '",' + '\n'
            my_data.append(d_)
        else:
            my_data.append(d)
    new_src = ''.join(my_data)
    with open('pkg/setup.py', 'w+') as f:
        f.write(new_src)

Makefile = """
wheel:
	python3 setup.py check
	python setup.py sdist
	python setup.py bdist_wheel --universal

# P
# |-- LICENSE
# |-- P
# |   +-- __init__.py
# |   +-- post.py
# |-- README.rst
# +-- setup.py

prereq:
	python3 -m pip install setuptools
	python3 -m pip install wheel


install:
	python3 -m pip install .

clean:
	rm -rf dist build rm -rf *.egg-info
	find . -name __pycache__ | xargs rm -rf
"""
        
setup_py = """
from setuptools import setup

setup(
    name='{pkg_name}',
    version='{pkg_version}',
    description='{pkg_desc}',
    url='{pkg_url}',
    author='Rahul Gopinath',
    author_email='rahul@gopinath.org',
    license='Fuzzingbook',
    packages=['{pkg_name}'],
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
)
"""
init_py = '''

"""
{pkg_name}.

{pkg_desc}
"""
__version__ = '{pkg_version}'
__author__ = 'Rahul Gopinath'
__url__ = '{pkg_url}'

from .post import *
'''

for notebook in VALS:
    pkg, desc, version = VALS[notebook]
    url = to_url(notebook)
    print(pkg, url)
    data = {
        'pkg_name': pkg,
        'pkg_version': version,
        'pkg_desc': desc,
        'pkg_url': url
    }
    with local.cwd("py/"):
        rm["-rf", "pkg"]()
        mkdir["pkg"]()
        mkdir["pkg/%s" % pkg]()
        # setup.py
        with open('pkg/Makefile', 'w+') as f:
            f.write(Makefile)
        with open('pkg/setup.py', 'w+') as f:
            my_setup_py = setup_py.format(**data)
            f.write(my_setup_py)
        with open('pkg/%s/__init__.py' % pkg, 'w+') as f:
            my_init_py = init_py.format(**data)
            f.write(my_init_py)
        cp["../%s" % notebook, 'pkg/%s/post.py' % pkg]
        tar["-cf", "%s.pkg.tar" % pkg, "pkg"]()
    with local.cwd("py/pkg"):
        make()
        res = make["install"]()
        v = res.strip().split("\n")
        print("Make Install>", v[-1])
    with local.cwd("py/"):
        cp["pkg/dist/{pkg_name}-{pkg_version}-py2.py3-none-any.whl".format(**data), "."]()

