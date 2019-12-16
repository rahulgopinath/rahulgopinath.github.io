---
published: true
title: The simplest grammar fuzzer in the world
layout: post
comments: true
tags: fuzzing
---

Fuzzing is one of the key tools in a security reseracher's tool box. It is simple
to write a [random fuzzer](https://www.fuzzingbook.org/html/Fuzzer.html#A-Simple-Fuzzer).

```python
def fuzzer(max_length=100, chars=[chr(i) for i in range(32, 64)]):
    return ''.join([random.choice(chars) for i in range(random.randint(0,max_length))])

for i in range(10):
    print(fuzzer())
```
This results in the following output, which can be used to fuzz programs.
```
59*6!8/>-9),4:"%01=?1,;5!2 6/? :,)(+>'6-55&#-(>'=:&8)")9,537
5:4&,;=,,.>1;8 %8=1 <"8!$, /#4&:346>%%<*</!3(602%+:$+5#(!##26=#+7";0'/)!#'%( !;;:&62=#&%-'>;
9#&/>/$ .>1&/84( .%(>&3+%$&="1 &'+6%,06<4<
/>:#"%9 ((&)#!+:/*-90=(#='.8(*-$#$$>91%93'?*9/7 ,>=",*/= ""4=&0&4,7" )?).
+"(:67-/-4.#".:>+*)/<%>5+"*:'?-2&58!48/ 49>:$4%=,%/'2#<7;%4/. 0$<=$,$!3).2?:1/!&0!4)3+$%$?&*0
:7;. $%9'?)7& "><#':$ +6<%$:41?16&,0 054>),2'$02 $#&'3>*9;%9-4>,:882,$4,$$(>6$-3#%8?>#"9";">=126
1'  ' 4': $9+0(-$*+$:=)"#"
.67&84,69;=
8:=%
!6=$+'89;59$)4.<<!7<7!9$!0"/%/$&")?&6',7.;>84<*,$1=-)-75<35%--68!>=;*0:-/51&4:7
```

Unfortunately, random fuzzing is not very effective for programs that accept complex
input languages such as those that expect JSON or any other structure in their input.
For these programs, the fuzzing can be much more effective if one has a model of their
input structure. A number of such tools exist
([1](https://github.com/renatahodovan/grammarinator), [2](https://www.fuzzingbook.org/html/GrammarFuzzer.html), [3](https://github.com/MozillaSecurity/dharma), [4](https://github.com/googleprojectzero/domato)).
But how difficult is it to write your own grammar based fuzzer?

The interesting thing is that, a grammar fuzzer is essentially a parser turned inside
out. Rather than consuming, we simply output what gets compared. With that idea in mind,
let us use one of the simplest parsers -- ([A PEG parser](http://rahul.gopinath.org/2018/09/06/peg-parsing/)).

```python
import random
def unify_key(grammar, key):
   return unify_rule(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule(grammar, rule):
    return sum([unify_key(grammar, token) for token in rule], [])
```
Now, all one needs is a grammar.

```python
grammar = {
        '<start>': [['<json>']],
        '<json>': [['<element>']],
        '<element>': [['<ws>', '<value>', '<ws>']],
        '<value>': [
           ['<object>'], ['<array>'], ['<string>'], ['<number>'],
           ['true'], ['false'], ['null']],
        '<object>': [['{', '<ws>', '}'], ['{', '<members>', '}']],
        '<members>': [['<member>', '<symbol-2>']],
        '<member>': [['<ws>', '<string>', '<ws>', ':', '<element>']],
        '<array>': [['[', '<ws>', ']'], ['[', '<elements>', ']']],
        '<elements>': [['<element>', '<symbol-1-1>']],
        '<string>': [['"', '<characters>', '"']],
        '<characters>': [['<character-1>']],
        '<character>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['g'], ['h'], ['i'], ['j'],
            ['k'], ['l'], ['m'], ['n'], ['o'], ['p'], ['q'], ['r'], ['s'], ['t'],
            ['u'], ['v'], ['w'], ['x'], ['y'], ['z'], ['A'], ['B'], ['C'], ['D'],
            ['E'], ['F'], ['G'], ['H'], ['I'], ['J'], ['K'], ['L'], ['M'], ['N'],
            ['O'], ['P'], ['Q'], ['R'], ['S'], ['T'], ['U'], ['V'], ['W'], ['X'],
            ['Y'], ['Z'], ['!'], ['#'], ['$'], ['%'], ['&'], ["'"], ['('], [')'],
            ['*'], ['+'], [','], ['-'], ['.'], ['/'], [':'], [';'], ['<'], ['='],
            ['>'], ['?'], ['@'], ['['], [']'], ['^'], ['_'], ['`'], ['{'], ['|'],
            ['}'], ['~'], [' '], ['\\"'], ['\\\\'], ['\\/'], ['<unicode>'], ['<escaped>']],
        '<number>': [['<int>', '<frac>', '<exp>']],
        '<int>': [
           ['<digit>'], ['<onenine>', '<digits>'],
           ['-', '<digits>'], ['-', '<onenine>', '<digits>']],
        '<digits>': [['<digit-1>']],
        '<digit>': [['0'], ['<onenine>']],
        '<onenine>': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9']],
        '<frac>': [[], ['.', '<digits>']],
        '<exp>': [[], ['E', '<sign>', '<digits>'], ['e', '<sign>', '<digits>']],
        '<sign>': [[], ['+'], ['-']],
        '<ws>': [['<sp1>', '<ws>'], []],
        '<sp1>': [[' ']], ##[['\n'], ['\r'], ['\t'], ['\x08'], ['\x0c']],
        '<symbol>': [[',', '<members>']],
        '<symbol-1>': [[',', '<elements>']],
        '<symbol-2>': [[], ['<symbol>', '<symbol-2>']],
        '<symbol-1-1>': [[], ['<symbol-1>', '<symbol-1-1>']],
        '<character-1>': [[], ['<character>', '<character-1>']],
        '<digit-1>': [['<digit>'], ['<digit>', '<digit-1>']],
        '<escaped>': [['\\u', '<hex>', '<hex>', '<hex>', '<hex>']],
        '<hex>': [
            ['0'], ['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'],
            ['a'], ['b'], ['c'], ['d'], ['e'], ['f'], ['A'], ['B'], ['C'], ['D'], ['E'], ['F']]
        }
```

The driver is as follows:

```python
i = 0
while True:
    try:
        print(repr(''.join(unify_key('<start>'))))
        i += 1
        if i == 10: break
    except:
        pass
```

It results in the following output

```json
' {  "" :105.27E0 } '
' [ -8e+3700 ]    '
'null   '
'  [     false  ,null,"l",     {   "$x":false ,  "=":true , "" :  null} ,""] '
'false '
'[  ] '
' -40e+21'
'true'
'[]  '
'  [  []   ,null  , 60E-3,{"":{}  ,""  :true, ""  :   false },true  ]  '
```

This grammar fuzzer can be implemented in pretty much any programming language that supports basic data structures.

What if you want the derivation tree instead? The following modified fuzzer will get you the derivation tree which
can be used with `fuzzingbook.GrammarFuzzer.tree_to_string`

```python
def unify_key(g, key):
   return (key, unify_rule(g, random.choice(g[key]))) if key in g else (key, [])

def unify_rule(g, rule):
    return [unify_key(g, token) for token in rule]
```

Using it

```python
from fuzzingbook.GrammarFuzzer import tree_to_string

res = unify_key(g, '<start>')
print(res)
print(repr(tree_to_string(res)))

```
