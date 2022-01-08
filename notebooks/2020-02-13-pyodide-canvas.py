# ---
# published: true
# title: Pyodide Canvas
# layout: post
# comments: true
# tags: pyodide
# categories: post
# ---

#^
# matplotlib
# networkx

# others

#@
# https://rahul.gopinath.org/py/pyparsing-2.4.7-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/graphviz-0.16-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/pydot-1.4.1-py2.py3-none-any.whl

# define the picture

dotFormat = """
digraph G {
    node [shape=rect];

    subgraph cluster_0 {
        style=filled;
        color=lightgrey;
        node [style=filled,color=white];
        a0 -> a1 -> a2 -> a3;
        label = "Hello";
    }

    subgraph cluster_1 {
        node [style=filled];
        b0 -> b1 -> b2 -> b3;
        label = "World";
        color=blue
    }

    start -> a0;
    start -> b0;
    a1 -> b3;
    b2 -> a3;
    a3 -> a0;
    a3 -> end;
    b3 -> end;

    start [shape=Mdiamond];
    end [shape=Msquare];
}
"""

# draw

__canvas__(dotFormt)

# derivation tree

derivation_tree = ("<start>",
                   [("<expr>",
                     [("<expr>", None),
                      (" + ", []),
                         ("<term>", None)]
                     )])

# program

from graphviz import Digraph

import re
def dot_escape(s):
    """Return s in a form suitable for dot"""
    s = re.sub(r'([^a-zA-Z0-9" ])', r"\\\1", s)
    return s


def extract_node(node, id):
    symbol, children, *annotation = node
    return symbol, children, ''.join(str(a) for a in annotation)



def default_node_attr(dot, nid, symbol, ann):
    dot.node(repr(nid), dot_escape(symbol))

def default_edge_attr(dot, start_node, stop_node):
    dot.edge(repr(start_node), repr(stop_node))
def default_graph_attr(dot):
    dot.attr('node', shape='plain')
def display_tree(derivation_tree,
                 log=False,
                 extract_node=extract_node,
                 node_attr=default_node_attr,
                 edge_attr=default_edge_attr,
                 graph_attr=default_graph_attr):
    
    # If we import display_tree, we also have to import its functions
    from graphviz import Digraph

    counter = 0
    labels = {}

    def traverse_tree(dot, tree, id=0):
        (symbol, children, annotation) = extract_node(tree, id)
        labels[str(id)] = symbol
        node_attr(dot, id, symbol, annotation)

        if children:
            for child in children:
                nonlocal counter
                counter += 1
                child_id = counter
                edge_attr(dot, id, child_id)
                traverse_tree(dot, child, child_id)

    dot = Digraph(comment="Derivation Tree")
    graph_attr(dot)
    traverse_tree(dot, derivation_tree)
    if log:
        print(dot)
    return dot, labels

# display

v, labels = display_tree(derivation_tree)
print(str(v))
print(labels)

# pydot

import pydot
dotFormat = str(v)
__canvas__(dotFormat)

# hierarchy

def hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter):
    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)
        if len(children)!=0:
            dx = width/len(children)
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap,
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

# show

plt.clf()
pos = hierarchy_pos(g,'0', width=1, vert_loc=0, vert_gap=0.006, xcenter=0)


nx.draw(g, pos=pos, with_labels=True, labels=labels,node_size=1000,font_size=8, node_color='#ffffff')

plt.axis('off')
plt.show()
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_str = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
print(len(img_str))

# canvas

__canvas__(img_str)

