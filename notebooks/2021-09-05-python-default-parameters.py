# ---
# published: true
# title: Fixing Python Default Parameters
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# As the *The Hitchhiker’s Guide to Python!* [notes](https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments),
# The way Python default parameters work is a constant source of annoyance and
# bugs. For example,

def append_to(element, to=[]):
    to.append(element)
    return to

# Here we are using it

my_list = append_to(12)
print(my_list)

# again
my_other_list = append_to(42)
print(my_other_list)

# As you can see, the default arguments appear to be something other than what
# you would normally expect. That is, it seems that they maintain state. What
# actually happens here is that, these values are produced  when the function is
# *defined* rather than when the function is *invoked*. This makes them unusable
# for the intended purpose as actual default arguments.
#
# A common workaround is to define the argument value as `None` and check for
# that in code.

def append_to(element, to=None):
    to = to or []
    to.append(element)
    return to

# This pattern is however, unsatisfying, and really error prone. Even worse,
# it violates the principle of least surprise. 

# That is, the official [python tutorial](https://docs.python.org/3/tutorial/controlflow.html#default-argument-values)
# says:
#
# ### 4.7.1. Default Argument Values
# 
# The most useful form is to specify a default value for one or more arguments.
# This creates a function that can be called with fewer arguments than it is
# defined to allow.

# They have to add the caveat "**Important warning:** The default value is evaluated only once."
# which should have been a fairly large hint that this is not the expected
# behavior.
#
# For most part, the behavior is pretty sane, and you can often avoid the
# [insane parts](https://github.com/satwikkansal/wtfpython) by simply not using
# them. However, default arguments are too convenient to leave aside.
# So what should we do?
#
# Thankfully, the dynamic nature of Python means that even when the language
# implementation is insane, you can bring back sanity by monkey patching it.
# In our case, you can write a function decorator that inspects the default
# arguments, and provides the correct behavior. Here is an implementation.


import functools
import inspect
 
def fix_params(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        original_defaults = func.__defaults__
        func.__defaults__ = tuple([val()
            if callable(val) and not inspect.signature(val).parameters
            else val for val in func.__defaults__])
        rval = func(*args, **kwargs)
        func.__defaults__ = original_defaults
        return rval
 
    return wrapper

# What this does is to inspect the default arguments and if it is
# a `callable`, it calls that, and provides the result as the actual
# default value during invocation. It means that we can now do this.

@fix_params
def append_to(element, to=lambda: []):
    to.append(element)
    return to

# Here we are using it

my_list = append_to(12)
print(my_list)

# again
my_other_list = append_to(42)
print(my_other_list)

# A problem with this is that it messes with the function signature
# when using type hints. However, one can work around it
# by using a wrapper function.

def fix_params(**my_default_args):
    def _decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            specs = inspect.getfullargspec(func)
            defaults = dict(zip(specs.args[::-1], (specs.defaults or ())[::-1]))
            defaults.update(specs.kwonlydefaults or {})

            original_defaults = func.__defaults__
            func.__defaults__ = tuple([my_default_args[val]()
               if val in my_default_args else val
               for val in defaults])
            rval = func(*args, **kwargs)
            func.__defaults__ = original_defaults
            return rval
        return wrapper
    return _decorator

# Wit this, we provide default parameters to `@fix_params` instead with same
# name but wrapped in a lambda, which overwrites the provided default value.

@fix_params(to=lambda: [])
def append_to(element, to=None):
    to.append(element)
    return to

# using it.

my_list = append_to(12)
print(my_list)

# another.

my_other_list = append_to(42)
print(my_other_list)

#
# The full code is [here](https://github.com/rahulgopinath/rahulgopinath.github.io/blob/master/notebooks/2021-09-05-python-default-parameters.py).
