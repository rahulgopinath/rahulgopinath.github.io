---
published: false
title: Control Flow Graph from Python Bytecode
layout: post
comments: true
tags: cfg, bytecode, python
categories: post
---

We previous [discussed](/post/2019/12/08/python-controlflow/) how to extract the control flow graph
from the Python AST. However, the Python AST can change from version to version, with the introduction
of new control flow structures. The byte code, in comparison, stays relatively stable. Hence, we can
use the bytecode to recover the control flow graph too.

First, we need the following imports. The `dis` package gives us access to the Python disassembly, and
pygraphviz lets us draw.
```python
import sys
import dis
import pygraphviz
```
Next, we define the node in the graph.
```python
class CFGNode:
    def __init__(self, i, bid):
        self.i = i
        self.bid = bid
        self.children = []
        self.props = {}
    def add_child(self, n):
        self.children.append(n)
```
Now, we come to the main class
```python
class CFG:
    def __init__(self, myfn):
        self.myfn = myfn
```
A small helper
```python
class CFG(CFG):
    def lstadd(self, hmap, key, val):
        if key not in hmap:
            hmap[key] = [val]
        else:
            hmap[key].append(val)   
```
We define an entry point for the graph
```python
class CFG(CFG):
    def entry(self):
        return CFGNode(dis.Instruction('NOP', opcode=dis.opmap['NOP'],
                                        arg=0, argval=0, argrepr=0,
                                        offset=0,starts_line=0, is_jump_target=False), 0)
```
Next, the meat of generation. We look handle the jump instructions specifically. Everything else is a simple block.
```python
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
```
We need to fix the jumps now.
```python
class CFG(CFG):
    def fix_jumps(self):
        for byte in self.opcodes:
            if  byte in self.jump_to:
                node = self.opcodes[byte]
                assert node.i.is_jump_target
                for b in self.jump_to[byte]:
                    b.add_child(node)
```
Making the graph to be displayed.
```python
class CFG(CFG):
    def to_graph(self):
        self.gen()
        self.fix_jumps()
        G = pygraphviz.AGraph(directed=True)
        for nid, cnode in self.opcodes.items():
            G.add_node(cnode.bid)
            n = G.get_node(cnode.bid)
            n.attr['label'] = "%d: %s" % (nid, cnode.i.opname)
            for cn in cnode.children:
                G.add_edge(cnode.bid, cn.bid)
        return G
```
This finishes our implementation.
We need a simple test program
```python
def gcd(a, b):
    if a<b:
        c = a
        a = b
        b = c

    while b != 0 :
        c = a
        a = b
        b = c % b
    return a
```
The CFG can be extracted as follows
```python
from IPython.display import Image
v = CFG(gcd)
g = v.to_graph()
Image(g.draw(format='png', prog='dot'))
```
<svg width="336pt" height="1916pt"
 viewBox="0.00 0.00 335.77 1916.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 1912)">
<polygon fill="#ffffff" stroke="transparent" points="-4,4 -4,-1912 331.7695,-1912 331.7695,4 -4,4"/>
<!-- 0 -->
<g id="node1" class="node">
<title>0</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1890" rx="69.3053" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1885.8" font-family="Times,serif" font-size="14.00" fill="#000000">0: LOAD_FAST</text>
</g>
<!-- 2 -->
<g id="node2" class="node">
<title>2</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1818" rx="69.3053" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1813.8" font-family="Times,serif" font-size="14.00" fill="#000000">2: LOAD_FAST</text>
</g>
<!-- 0&#45;&gt;2 -->
<g id="edge1" class="edge">
<title>0&#45;&gt;2</title>
<path fill="none" stroke="#000000" d="M222.2371,-1871.8314C222.2371,-1864.131 222.2371,-1854.9743 222.2371,-1846.4166"/>
<polygon fill="#000000" stroke="#000000" points="225.7372,-1846.4132 222.2371,-1836.4133 218.7372,-1846.4133 225.7372,-1846.4132"/>
</g>
<!-- 4 -->
<g id="node3" class="node">
<title>4</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1746" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1741.8" font-family="Times,serif" font-size="14.00" fill="#000000">4: COMPARE_OP</text>
</g>
<!-- 2&#45;&gt;4 -->
<g id="edge2" class="edge">
<title>2&#45;&gt;4</title>
<path fill="none" stroke="#000000" d="M222.2371,-1799.8314C222.2371,-1792.131 222.2371,-1782.9743 222.2371,-1774.4166"/>
<polygon fill="#000000" stroke="#000000" points="225.7372,-1774.4132 222.2371,-1764.4133 218.7372,-1774.4133 225.7372,-1774.4132"/>
</g>
<!-- 6 -->
<g id="node4" class="node">
<title>6</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1674" rx="105.565" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1669.8" font-family="Times,serif" font-size="14.00" fill="#000000">6: POP_JUMP_IF_FALSE</text>
</g>
<!-- 4&#45;&gt;6 -->
<g id="edge3" class="edge">
<title>4&#45;&gt;6</title>
<path fill="none" stroke="#000000" d="M222.2371,-1727.8314C222.2371,-1720.131 222.2371,-1710.9743 222.2371,-1702.4166"/>
<polygon fill="#000000" stroke="#000000" points="225.7372,-1702.4132 222.2371,-1692.4133 218.7372,-1702.4133 225.7372,-1702.4132"/>
</g>
<!-- 8 -->
<g id="node5" class="node">
<title>8</title>
<ellipse fill="none" stroke="#000000" cx="174.2371" cy="-1602" rx="69.3053" ry="18"/>
<text text-anchor="middle" x="174.2371" y="-1597.8" font-family="Times,serif" font-size="14.00" fill="#000000">8: LOAD_FAST</text>
</g>
<!-- 6&#45;&gt;8 -->
<g id="edge4" class="edge">
<title>6&#45;&gt;8</title>
<path fill="none" stroke="#000000" d="M210.1246,-1655.8314C204.5684,-1647.497 197.8749,-1637.4567 191.7812,-1628.3162"/>
<polygon fill="#000000" stroke="#000000" points="194.6386,-1626.2925 186.1793,-1619.9134 188.8142,-1630.1754 194.6386,-1626.2925"/>
</g>
<!-- 20 -->
<g id="node6" class="node">
<title>20</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1170" rx="78.3204" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1165.8" font-family="Times,serif" font-size="14.00" fill="#000000">20: SETUP_LOOP</text>
</g>
<!-- 6&#45;&gt;20 -->
<g id="edge5" class="edge">
<title>6&#45;&gt;20</title>
<path fill="none" stroke="#000000" d="M233.7373,-1655.6962C249.325,-1629.088 275.2371,-1577.6848 275.2371,-1530 275.2371,-1530 275.2371,-1530 275.2371,-1314 275.2371,-1273.1184 271.5901,-1261.8892 256.2371,-1224 252.4081,-1214.5506 246.938,-1204.9164 241.5016,-1196.4515"/>
<polygon fill="#000000" stroke="#000000" points="244.3896,-1194.4738 235.9188,-1188.1102 238.5724,-1198.3674 244.3896,-1194.4738"/>
</g>
<!-- 10 -->
<g id="node7" class="node">
<title>10</title>
<ellipse fill="none" stroke="#000000" cx="170.2371" cy="-1530" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="170.2371" y="-1525.8" font-family="Times,serif" font-size="14.00" fill="#000000">10: STORE_FAST</text>
</g>
<!-- 8&#45;&gt;10 -->
<g id="edge6" class="edge">
<title>8&#45;&gt;10</title>
<path fill="none" stroke="#000000" d="M173.2277,-1583.8314C172.7999,-1576.131 172.2912,-1566.9743 171.8158,-1558.4166"/>
<polygon fill="#000000" stroke="#000000" points="175.3094,-1558.2037 171.26,-1548.4133 168.3202,-1558.592 175.3094,-1558.2037"/>
</g>
<!-- 22 -->
<g id="node8" class="node">
<title>22</title>
<ellipse fill="none" stroke="#000000" cx="222.2371" cy="-1098" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="222.2371" y="-1093.8" font-family="Times,serif" font-size="14.00" fill="#000000">22: LOAD_FAST</text>
</g>
<!-- 20&#45;&gt;22 -->
<g id="edge7" class="edge">
<title>20&#45;&gt;22</title>
<path fill="none" stroke="#000000" d="M222.2371,-1151.8314C222.2371,-1144.131 222.2371,-1134.9743 222.2371,-1126.4166"/>
<polygon fill="#000000" stroke="#000000" points="225.7372,-1126.4132 222.2371,-1116.4133 218.7372,-1126.4133 225.7372,-1126.4132"/>
</g>
<!-- 12 -->
<g id="node9" class="node">
<title>12</title>
<ellipse fill="none" stroke="#000000" cx="170.2371" cy="-1458" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="170.2371" y="-1453.8" font-family="Times,serif" font-size="14.00" fill="#000000">12: LOAD_FAST</text>
</g>
<!-- 10&#45;&gt;12 -->
<g id="edge8" class="edge">
<title>10&#45;&gt;12</title>
<path fill="none" stroke="#000000" d="M170.2371,-1511.8314C170.2371,-1504.131 170.2371,-1494.9743 170.2371,-1486.4166"/>
<polygon fill="#000000" stroke="#000000" points="173.7372,-1486.4132 170.2371,-1476.4133 166.7372,-1486.4133 173.7372,-1486.4132"/>
</g>
<!-- 24 -->
<g id="node13" class="node">
<title>24</title>
<ellipse fill="none" stroke="#000000" cx="167.2371" cy="-1026" rx="81.686" ry="18"/>
<text text-anchor="middle" x="167.2371" y="-1021.8" font-family="Times,serif" font-size="14.00" fill="#000000">24: LOAD_CONST</text>
</g>
<!-- 22&#45;&gt;24 -->
<g id="edge13" class="edge">
<title>22&#45;&gt;24</title>
<path fill="none" stroke="#000000" d="M208.6415,-1080.2022C202.1631,-1071.7214 194.2875,-1061.4115 187.1513,-1052.0696"/>
<polygon fill="#000000" stroke="#000000" points="189.7186,-1049.6646 180.8668,-1043.8425 184.1559,-1053.9139 189.7186,-1049.6646"/>
</g>
<!-- 14 -->
<g id="node10" class="node">
<title>14</title>
<ellipse fill="none" stroke="#000000" cx="170.2371" cy="-1386" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="170.2371" y="-1381.8" font-family="Times,serif" font-size="14.00" fill="#000000">14: STORE_FAST</text>
</g>
<!-- 12&#45;&gt;14 -->
<g id="edge9" class="edge">
<title>12&#45;&gt;14</title>
<path fill="none" stroke="#000000" d="M170.2371,-1439.8314C170.2371,-1432.131 170.2371,-1422.9743 170.2371,-1414.4166"/>
<polygon fill="#000000" stroke="#000000" points="173.7372,-1414.4132 170.2371,-1404.4133 166.7372,-1414.4133 173.7372,-1414.4132"/>
</g>
<!-- 16 -->
<g id="node11" class="node">
<title>16</title>
<ellipse fill="none" stroke="#000000" cx="170.2371" cy="-1314" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="170.2371" y="-1309.8" font-family="Times,serif" font-size="14.00" fill="#000000">16: LOAD_FAST</text>
</g>
<!-- 14&#45;&gt;16 -->
<g id="edge10" class="edge">
<title>14&#45;&gt;16</title>
<path fill="none" stroke="#000000" d="M170.2371,-1367.8314C170.2371,-1360.131 170.2371,-1350.9743 170.2371,-1342.4166"/>
<polygon fill="#000000" stroke="#000000" points="173.7372,-1342.4132 170.2371,-1332.4133 166.7372,-1342.4133 173.7372,-1342.4132"/>
</g>
<!-- 18 -->
<g id="node12" class="node">
<title>18</title>
<ellipse fill="none" stroke="#000000" cx="170.2371" cy="-1242" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="170.2371" y="-1237.8" font-family="Times,serif" font-size="14.00" fill="#000000">18: STORE_FAST</text>
</g>
<!-- 16&#45;&gt;18 -->
<g id="edge11" class="edge">
<title>16&#45;&gt;18</title>
<path fill="none" stroke="#000000" d="M170.2371,-1295.8314C170.2371,-1288.131 170.2371,-1278.9743 170.2371,-1270.4166"/>
<polygon fill="#000000" stroke="#000000" points="173.7372,-1270.4132 170.2371,-1260.4133 166.7372,-1270.4133 173.7372,-1270.4132"/>
</g>
<!-- 18&#45;&gt;20 -->
<g id="edge12" class="edge">
<title>18&#45;&gt;20</title>
<path fill="none" stroke="#000000" d="M183.091,-1224.2022C189.2161,-1215.7214 196.6621,-1205.4115 203.409,-1196.0696"/>
<polygon fill="#000000" stroke="#000000" points="206.3332,-1197.9986 209.3508,-1187.8425 200.6584,-1193.9001 206.3332,-1197.9986"/>
</g>
<!-- 26 -->
<g id="node14" class="node">
<title>26</title>
<ellipse fill="none" stroke="#000000" cx="160.2371" cy="-954" rx="81.0733" ry="18"/>
<text text-anchor="middle" x="160.2371" y="-949.8" font-family="Times,serif" font-size="14.00" fill="#000000">26: COMPARE_OP</text>
</g>
<!-- 24&#45;&gt;26 -->
<g id="edge14" class="edge">
<title>24&#45;&gt;26</title>
<path fill="none" stroke="#000000" d="M165.4707,-1007.8314C164.722,-1000.131 163.8318,-990.9743 162.9998,-982.4166"/>
<polygon fill="#000000" stroke="#000000" points="166.4786,-982.0276 162.0272,-972.4133 159.5114,-982.7051 166.4786,-982.0276"/>
</g>
<!-- 28 -->
<g id="node15" class="node">
<title>28</title>
<ellipse fill="none" stroke="#000000" cx="146.2371" cy="-882" rx="109.9085" ry="18"/>
<text text-anchor="middle" x="146.2371" y="-877.8" font-family="Times,serif" font-size="14.00" fill="#000000">28: POP_JUMP_IF_FALSE</text>
</g>
<!-- 26&#45;&gt;28 -->
<g id="edge15" class="edge">
<title>26&#45;&gt;28</title>
<path fill="none" stroke="#000000" d="M156.7043,-935.8314C155.207,-928.131 153.4265,-918.9743 151.7625,-910.4166"/>
<polygon fill="#000000" stroke="#000000" points="155.1618,-909.5614 149.8174,-900.4133 148.2905,-910.8975 155.1618,-909.5614"/>
</g>
<!-- 30 -->
<g id="node16" class="node">
<title>30</title>
<ellipse fill="none" stroke="#000000" cx="147.2371" cy="-810" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="147.2371" y="-805.8" font-family="Times,serif" font-size="14.00" fill="#000000">30: LOAD_FAST</text>
</g>
<!-- 28&#45;&gt;30 -->
<g id="edge16" class="edge">
<title>28&#45;&gt;30</title>
<path fill="none" stroke="#000000" d="M146.4894,-863.8314C146.5963,-856.131 146.7235,-846.9743 146.8424,-838.4166"/>
<polygon fill="#000000" stroke="#000000" points="150.342,-838.4609 146.9813,-828.4133 143.3427,-838.3637 150.342,-838.4609"/>
</g>
<!-- 48 -->
<g id="node17" class="node">
<title>48</title>
<ellipse fill="none" stroke="#000000" cx="92.2371" cy="-162" rx="74.4706" ry="18"/>
<text text-anchor="middle" x="92.2371" y="-157.8" font-family="Times,serif" font-size="14.00" fill="#000000">48: POP_BLOCK</text>
</g>
<!-- 28&#45;&gt;48 -->
<g id="edge17" class="edge">
<title>28&#45;&gt;48</title>
<path fill="none" stroke="#000000" d="M110.7052,-864.9589C94.7474,-855.8428 76.7389,-843.3192 64.2371,-828 36.9982,-794.6227 28.2371,-781.0813 28.2371,-738 28.2371,-738 28.2371,-738 28.2371,-306 28.2371,-264.8223 32.3116,-253.0713 50.2371,-216 55.0954,-205.9525 62.0461,-196.0053 68.8984,-187.4387"/>
<polygon fill="#000000" stroke="#000000" points="71.6452,-189.6099 75.3665,-179.6901 66.2713,-185.1241 71.6452,-189.6099"/>
</g>
<!-- 32 -->
<g id="node18" class="node">
<title>32</title>
<ellipse fill="none" stroke="#000000" cx="148.2371" cy="-738" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="148.2371" y="-733.8" font-family="Times,serif" font-size="14.00" fill="#000000">32: STORE_FAST</text>
</g>
<!-- 30&#45;&gt;32 -->
<g id="edge18" class="edge">
<title>30&#45;&gt;32</title>
<path fill="none" stroke="#000000" d="M147.4894,-791.8314C147.5963,-784.131 147.7235,-774.9743 147.8424,-766.4166"/>
<polygon fill="#000000" stroke="#000000" points="151.342,-766.4609 147.9813,-756.4133 144.3427,-766.3637 151.342,-766.4609"/>
</g>
<!-- 50 -->
<g id="node19" class="node">
<title>50</title>
<ellipse fill="none" stroke="#000000" cx="92.2371" cy="-90" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="92.2371" y="-85.8" font-family="Times,serif" font-size="14.00" fill="#000000">50: LOAD_FAST</text>
</g>
<!-- 48&#45;&gt;50 -->
<g id="edge19" class="edge">
<title>48&#45;&gt;50</title>
<path fill="none" stroke="#000000" d="M92.2371,-143.8314C92.2371,-136.131 92.2371,-126.9743 92.2371,-118.4166"/>
<polygon fill="#000000" stroke="#000000" points="95.7372,-118.4132 92.2371,-108.4133 88.7372,-118.4133 95.7372,-118.4132"/>
</g>
<!-- 34 -->
<g id="node20" class="node">
<title>34</title>
<ellipse fill="none" stroke="#000000" cx="148.2371" cy="-666" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="148.2371" y="-661.8" font-family="Times,serif" font-size="14.00" fill="#000000">34: LOAD_FAST</text>
</g>
<!-- 32&#45;&gt;34 -->
<g id="edge20" class="edge">
<title>32&#45;&gt;34</title>
<path fill="none" stroke="#000000" d="M148.2371,-719.8314C148.2371,-712.131 148.2371,-702.9743 148.2371,-694.4166"/>
<polygon fill="#000000" stroke="#000000" points="151.7372,-694.4132 148.2371,-684.4133 144.7372,-694.4133 151.7372,-694.4132"/>
</g>
<!-- 52 -->
<g id="node27" class="node">
<title>52</title>
<ellipse fill="none" stroke="#000000" cx="92.2371" cy="-18" rx="92.4747" ry="18"/>
<text text-anchor="middle" x="92.2371" y="-13.8" font-family="Times,serif" font-size="14.00" fill="#000000">52: RETURN_VALUE</text>
</g>
<!-- 50&#45;&gt;52 -->
<g id="edge29" class="edge">
<title>50&#45;&gt;52</title>
<path fill="none" stroke="#000000" d="M92.2371,-71.8314C92.2371,-64.131 92.2371,-54.9743 92.2371,-46.4166"/>
<polygon fill="#000000" stroke="#000000" points="95.7372,-46.4132 92.2371,-36.4133 88.7372,-46.4133 95.7372,-46.4132"/>
</g>
<!-- 36 -->
<g id="node21" class="node">
<title>36</title>
<ellipse fill="none" stroke="#000000" cx="150.2371" cy="-594" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="150.2371" y="-589.8" font-family="Times,serif" font-size="14.00" fill="#000000">36: STORE_FAST</text>
</g>
<!-- 34&#45;&gt;36 -->
<g id="edge21" class="edge">
<title>34&#45;&gt;36</title>
<path fill="none" stroke="#000000" d="M148.7417,-647.8314C148.9556,-640.131 149.21,-630.9743 149.4477,-622.4166"/>
<polygon fill="#000000" stroke="#000000" points="152.9465,-622.5066 149.7256,-612.4133 145.9492,-622.3122 152.9465,-622.5066"/>
</g>
<!-- 38 -->
<g id="node22" class="node">
<title>38</title>
<ellipse fill="none" stroke="#000000" cx="150.2371" cy="-522" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="150.2371" y="-517.8" font-family="Times,serif" font-size="14.00" fill="#000000">38: LOAD_FAST</text>
</g>
<!-- 36&#45;&gt;38 -->
<g id="edge22" class="edge">
<title>36&#45;&gt;38</title>
<path fill="none" stroke="#000000" d="M150.2371,-575.8314C150.2371,-568.131 150.2371,-558.9743 150.2371,-550.4166"/>
<polygon fill="#000000" stroke="#000000" points="153.7372,-550.4132 150.2371,-540.4133 146.7372,-550.4133 153.7372,-550.4132"/>
</g>
<!-- 40 -->
<g id="node23" class="node">
<title>40</title>
<ellipse fill="none" stroke="#000000" cx="155.2371" cy="-450" rx="73.6485" ry="18"/>
<text text-anchor="middle" x="155.2371" y="-445.8" font-family="Times,serif" font-size="14.00" fill="#000000">40: LOAD_FAST</text>
</g>
<!-- 38&#45;&gt;40 -->
<g id="edge23" class="edge">
<title>38&#45;&gt;40</title>
<path fill="none" stroke="#000000" d="M151.4988,-503.8314C152.0335,-496.131 152.6694,-486.9743 153.2637,-478.4166"/>
<polygon fill="#000000" stroke="#000000" points="156.7571,-478.6317 153.9584,-468.4133 149.7739,-478.1467 156.7571,-478.6317"/>
</g>
<!-- 42 -->
<g id="node24" class="node">
<title>42</title>
<ellipse fill="none" stroke="#000000" cx="156.2371" cy="-378" rx="100.038" ry="18"/>
<text text-anchor="middle" x="156.2371" y="-373.8" font-family="Times,serif" font-size="14.00" fill="#000000">42: BINARY_MODULO</text>
</g>
<!-- 40&#45;&gt;42 -->
<g id="edge24" class="edge">
<title>40&#45;&gt;42</title>
<path fill="none" stroke="#000000" d="M155.4894,-431.8314C155.5963,-424.131 155.7235,-414.9743 155.8424,-406.4166"/>
<polygon fill="#000000" stroke="#000000" points="159.342,-406.4609 155.9813,-396.4133 152.3427,-406.3637 159.342,-406.4609"/>
</g>
<!-- 44 -->
<g id="node25" class="node">
<title>44</title>
<ellipse fill="none" stroke="#000000" cx="156.2371" cy="-306" rx="76.7295" ry="18"/>
<text text-anchor="middle" x="156.2371" y="-301.8" font-family="Times,serif" font-size="14.00" fill="#000000">44: STORE_FAST</text>
</g>
<!-- 42&#45;&gt;44 -->
<g id="edge25" class="edge">
<title>42&#45;&gt;44</title>
<path fill="none" stroke="#000000" d="M156.2371,-359.8314C156.2371,-352.131 156.2371,-342.9743 156.2371,-334.4166"/>
<polygon fill="#000000" stroke="#000000" points="159.7372,-334.4132 156.2371,-324.4133 152.7372,-334.4133 159.7372,-334.4132"/>
</g>
<!-- 46 -->
<g id="node26" class="node">
<title>46</title>
<ellipse fill="none" stroke="#000000" cx="156.2371" cy="-234" rx="96.6633" ry="18"/>
<text text-anchor="middle" x="156.2371" y="-229.8" font-family="Times,serif" font-size="14.00" fill="#000000">46: JUMP_ABSOLUTE</text>
</g>
<!-- 44&#45;&gt;46 -->
<g id="edge26" class="edge">
<title>44&#45;&gt;46</title>
<path fill="none" stroke="#000000" d="M156.2371,-287.8314C156.2371,-280.131 156.2371,-270.9743 156.2371,-262.4166"/>
<polygon fill="#000000" stroke="#000000" points="159.7372,-262.4132 156.2371,-252.4133 152.7372,-262.4133 159.7372,-262.4132"/>
</g>
<!-- 46&#45;&gt;22 -->
<g id="edge27" class="edge">
<title>46&#45;&gt;22</title>
<path fill="none" stroke="#000000" d="M192.6908,-250.797C209.447,-259.9303 228.5838,-272.5384 242.2371,-288 271.4547,-321.0874 284.2371,-333.8588 284.2371,-378 284.2371,-954 284.2371,-954 284.2371,-954 284.2371,-995.6357 275.7683,-1006.2351 258.2371,-1044 253.8708,-1053.4054 247.9913,-1063.0273 242.2509,-1071.4944"/>
<polygon fill="#000000" stroke="#000000" points="239.2711,-1069.6474 236.3883,-1079.8425 244.9996,-1073.6704 239.2711,-1069.6474"/>
</g>
<!-- 46&#45;&gt;48 -->
<g id="edge28" class="edge">
<title>46&#45;&gt;48</title>
<path fill="none" stroke="#000000" d="M140.4168,-216.2022C132.7244,-207.5483 123.3393,-196.99 114.9027,-187.4988"/>
<polygon fill="#000000" stroke="#000000" points="117.3567,-184.9914 108.0971,-179.8425 112.1248,-189.6419 117.3567,-184.9914"/>
</g>
</g>
</svg>
