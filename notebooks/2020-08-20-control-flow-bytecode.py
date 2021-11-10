# ---
# published: true
# title: Control Flow Graph from Python Bytecode
# layout: post
# comments: true
# tags: cfg, bytecode, python
# categories: post
# ---


# We previous [discussed](/post/2019/12/08/python-controlflow/) how to extract the control flow graph
# from the Python AST. However, the Python AST can change from version to version, with the introduction
# of new control flow structures. The byte code, in comparison, stays relatively stable. Hence, we can
# use the bytecode to recover the control flow graph too.
# 
# First, we need the following imports. The `dis` package gives us access to the Python disassembly, and
# networkx and matplotlib lets us draw.

#^
# matplotlib
# networkx
# pydot

import sys
import dis
import networkx as nx
import matplotlib.pyplot as plt
import pydot
import textwrap

# Let us start by defining a few functions that we want to extract the control-flow graphs of.

def gcd(a, b):
    if a<b:
        c = a
        a = b
        b = c

    while b != 0:
        c = a
        a = b
        b = c % b
    return a

# Next, we define the node in the graph.

class CFGNode:
    def __init__(self, i, bid):
        self.i = i
        self.bid = bid
        self.children = []
        self.props = {}

    def add_child(self, n):
        self.children.append(n)

# Now, we come to the main class

class CFG:
    def __init__(self, myfn):
        self.myfn = myfn

# A small helper

class CFG(CFG):
    def lstadd(self, hmap, key, val):
        if key not in hmap:
            hmap[key] = [val]
        else:
            hmap[key].append(val)

# We define an entry point for the graph

class CFG(CFG):
    def entry(self):
        return CFGNode(dis.Instruction('NOP', opcode=dis.opmap['NOP'],
                                        arg=0, argval=0, argrepr=0,
                                        offset=0,starts_line=0, is_jump_target=False), 0)

# Next, the meat of generation. We look handle the jump instructions specifically. Everything else is a simple block.

class CFG(CFG):
    def gen(self):
        enter = self.entry()
        last = enter
        self.jump_to = {}
        self.opcodes = {}
        for i,ins in enumerate(dis.get_instructions(self.myfn)):
            byte = i * 2
            node = CFGNode(ins, byte)
            self.opcodes[byte] = node
            #print(i,ins)
            if ins.opname in ['LOAD_CONST',
                              'LOAD_FAST',
                              'STORE_FAST',
                              'COMPARE_OP',
                              'INPLACE_ADD',
                              'INPLACE_SUBTRACT',
                              'RETURN_VALUE',
                              'BINARY_MODULO',
                              'STORE_NAME',
                              'MAKE_FUNCTION',
                              'POP_BLOCK']:
                last.add_child(node)
                last = node
            elif ins.opname == 'POP_JUMP_IF_FALSE':
                #print("will jump to", ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props['jmp'] = True
                last.add_child(node)
                last = node
            elif ins.opname == 'JUMP_FORWARD':
                node.props['jmp'] = True
                self.lstadd(self.jump_to, (i+1)*2 + ins.arg, node)
                #print("will jump to", (i+1)*2 + ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == 'SETUP_LOOP':
                #print("setuploop: ", byte , ins.arg)
                last.add_child(node)
                last = node
            elif ins.opname == 'JUMP_ABSOLUTE':
                #print("will jump to", ins.arg)
                self.lstadd(self.jump_to, ins.arg, node)
                node.props['jmp'] = True
                last.add_child(node)
                last = node
            else:
                assert False

# We need to fix the jumps now.

class CFG(CFG):
    def fix_jumps(self):
        for byte in self.opcodes:
            if  byte in self.jump_to:
                node = self.opcodes[byte]
                assert node.i.is_jump_target
                for b in self.jump_to[byte]:
                    b.add_child(node)

# Making the graph to be displayed.

class CFG(CFG):
    def to_graph(self):
        self.gen()
        self.fix_jumps()
        G = pydot.Dot("my_graph", graph_type="digraph")
        for nid, cnode in self.opcodes.items():
            G.add_node(pydot.Node(str(cnode.bid)))
            ns = G.get_node(str(cnode.bid))
            ns[0].set_label("%d: %s" % (nid, cnode.i.opname))
            for cn in cnode.children:
                G.add_edge(pydot.Edge(str(cnode.bid), str(cn.bid)))
        return G

# This finishes our implementation.

if __name__== '__main__':
    v = CFG(gcd)
    g = v.to_graph()
    print(g)

# Show the image

if __name__== '__main__':
    nxg = nx.nx_pydot.from_pydot(g)
    plt.clf()
    nx.draw(nxg, with_labels=True)
    plt.axis('off')
    plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
    print(len(img_str))

# 

if __name__== '__main__':
    __canvas__(img_str)

