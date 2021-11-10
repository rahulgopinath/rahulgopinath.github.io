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
