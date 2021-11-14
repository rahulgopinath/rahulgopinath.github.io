import json
with open('pkgs.json') as f:
    VALS = json.load(fp=f)

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
        cp["../%s" % notebook, 'pkg/%s/post.py' % pkg]()
        tar["-cf", "%s.pkg.tar" % pkg, "pkg"]()
    with local.cwd("py/pkg"):
        make()
        res = make["install"]()
        v = res.strip().split("\n")
        print("Make Install>", v[-1])
    with local.cwd("py/"):
        cp["pkg/dist/{pkg_name}-{pkg_version}-py2.py3-none-any.whl".format(**data), "."]()

