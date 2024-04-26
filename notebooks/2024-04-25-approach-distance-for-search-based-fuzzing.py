# ---
# published: true
# title: Approach Distance for Search Based Fuzzing
# layout: post
# comments: true
# tags: search fuzzing
# categories: post
# ---
#  
# TLDR; 
# 
# 
# ## Definitions
#
# For this post, we use the following terms as we have defiend  previously:
#
# * The _alphabet_ is the set all of symbols in the input language. For example,
#   in this post, we use all ASCII characters as alphabet.

#@
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pycfg-0.0.1-py2.py3-none-any.whl 
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/metacircularinterpreter-0.0.1-py2.py3-none-any.whl

import importlib.util
import sys

def load_module(file_name, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


import math
import random
import simplefuzzer as fuzzer
#import pycfg
#import 
pycfg = load_module('notebooks/2019-12-08-python-controlflow.py', 'pycfg')

# The idea behind approach level is that, we start with a path, and then find
# how many critical branches are there

def triangle(a, b, c):
    if a == b:
        if b == c:
            return 'Equilateral'
        else:
            return 'Isosceless'
    else:
        if b == c:
            return "Isosceles"
        else:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"

def compute_dominator(cfg, start = 0, key='parents'):
    #v = [(l, n) for (l,n) in cfg if n == start] # there should be only one nid
    #start = v[0]
    dominator = {}
    dominator[start] = {start}
    all_nodes = set(cfg.keys())
    rem_nodes = all_nodes - {start}
    for n in rem_nodes:
        dominator[n] = all_nodes

    c = True
    while c:
        c = False
        for n in rem_nodes:
            pred_n = cfg[n][key]
            doms = [dominator[p] for p in pred_n]
            i = set.intersection(*doms) if doms else set()
            v = {n} | i
            if dominator[n] != v:
                c = True
            dominator[n] = v
    return dominator



class PathFitness:
    def __init__(self, cfg, dom, postdom):
        self.cfg = cfg
        self.dom = dom
        self.postdom = postdom

    # def compute_fitness(self, path):
    #     def normalized(x): return x / (x + 1.0)
    #     self.path = path
    #     al = self.approach_level()
    #     bd = self.branch_distance()
    #     if bd == math.inf: return al
    #     return (al + normalized(bd))



def successors(cfg, a, key='children'):
    seen = set()
    successors = list(cfg[a][key])
    to_process = list(successors)
    while to_process:
        nodeid, *to_process = to_process
        seen.add(nodeid)
        new_children = [c for c in cfg[nodeid][key] if c not in seen]
        successors.extend(new_children)
        to_process.extend(new_children)
    return set(successors)


def a_control_dependent_on_b(cfg, dom, postdom, a, b):
    # B has at least 2 successors in CFG
    if len(cfg[b]['children']) < 2: return False

    b_successors = successors(cfg, b)
    # B dominates A
    v1 = b in dom[a]
    # B is not post dominated by A
    v2 = a not in postdom[b]
    # there exist a successor for B that is post dominated by A
    v3 = any(a in postdom[s] for s in b_successors)
    return v1 and v2 and v3

def _approach_level(cfg, dom, postdom, target, path):
    if not path: return 0
    # find the node
    nxt_target = None
    while path:
        n, *path = path
        if a_control_dependent_on_b(cfg, dom, postdom, target, n):
            nxt_target = n
            break
    cost = 1 if nxt_target is not None else 0
    return cost + _approach_level(cfg, dom, postdom, nxt_target, path)

def approach_level(cfg, dom, postdom, path):
    hd, *tl = reversed(path)
    return _approach_level(cfg, dom, postdom, hd, tl)


def get_cfg(src):
    cfg = pycfg.PyCFGExtractor()
    cfg.eval(src)
    cache = cfg.gstate.registry
    g = {}
    for k,v in cache.items():
        j = v.to_json()
        at_key = 'at' # id
        at = j[at_key]
        parents_at = [cache[p].to_json()[at_key] for p in j['parents']]
        children_at = [cache[c].to_json()[at_key] for c in j['children']]
        if at not in g:
            g[at] = {'parents':set(), 'children':set()}
        # remove dummy nodes
        ps = set([p for p in parents_at if p != at])
        cs = set([c for c in children_at if c != at])
        g[at]['parents'] |= ps
        g[at]['children'] |= cs 
        if v.calls:
            g[at]['calls'] = v.calls
        assert v.lineno() in cfg.functions_node
        g[at]['function'] = cfg.functions_node[v.lineno()]
    #return (g, cfg.founder.ast_node.lineno, cfg.last_node.ast_node.lineno)
    return (g, cfg.founder.rid, cfg.last_node.rid)


if __name__ == '__main__':
    import inspect
    cfg, first, last= get_cfg(inspect.getsource(triangle))
    dom = compute_dominator(cfg, start=first)
    postdom = compute_dominator(cfg, start=last, key='children')
    ffn = PathFitness(cfg, dom, postdom)
    #path = [3, 4, 10, 13, 16]
    path = [1, 2, 8, 11, 14]
    #nodepath = []
    #for elt in path:
    #    e = [(l,n) for (l,n) in cfg if l == elt][0]
    #    nodepath.append(e)
    # 3 is triangle, 4 is first if, 10 is else, first if
    # 13 is else else if
    # 16 is return scalene -- should be 14
    print('Approach Level %d' % approach_level(cfg, dom, postdom, path))


# 
# [^havricov2019]: Havrikov, Nikolas, and Andreas Zeller. "Systematically covering input structure." 2019 IEEE/ACM international conference on Automated Software Engineering (ASE). IEEE, 2019.
# [^purdom1972]: Paul Purdom. "A Sentence Generator for Testing Parsers." BIT Numerical Mathematics, 1972
