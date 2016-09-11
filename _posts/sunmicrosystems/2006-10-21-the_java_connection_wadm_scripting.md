---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm V) The java nature
title: (wadm V) The java nature
---

In this section we will try to explore the way java objects are accessible from wadm, and how to get the framework to do our bidding.  
  
### Our tools

log into wadm and type  

```
> java::  
ambiguous command name "java::": ::java::autolock ::java::autolock_create_instance ::java::autolock_destroy_instance ::java::bind ::java::call ::java::cast ::java::defineclass ::java::event ::java::field ::java::getinterp ::java::import ::java::info ::java::instanceof ::java::isnull ::java::load ::java::lock ::java::new ::java::null ::java::prop ::java::throw ::java::try ::java::unlock  
```
  
  
These commands are explained [here(external)](http://tcljava.sourceforge.net/docs/TclJava/contents.html)  

#### Exploring wadm.

```
> java::call java.lang.Thread dumpStack  
java.lang.Exception: Stack trace  
        at java.lang.Thread.dumpStack(Thread.java:1158)  
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)  
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:39)  
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:25)  
        at java.lang.reflect.Method.invoke(Method.java:585)  
        at tcl.lang.reflect.PkgInvoker.invokeMethod(PkgInvoker.java:125)  
        at tcl.lang.JavaInvoke.call(JavaInvoke.java:263)  
        at tcl.lang.JavaInvoke.callStaticMethod(JavaInvoke.java:176)  
        at tcl.lang.JavaCallCmd.cmdProc(JavaCallCmd.java:74)  
        at tcl.lang.AutoloadStub.cmdProc(Extension.java:144)  
        at tcl.lang.Parser.evalObjv(Parser.java:818)  
        at tcl.lang.Parser.eval2(Parser.java:1221)  
        at tcl.lang.Interp.eval(Interp.java:2222)  
        at tcl.lang.Interp.eval(Interp.java:2306)  
        at tcl.lang.Interp.recordAndEval(Interp.java:2361)  
        at tcl.lang.ConsoleThread$1.processEvent(JaclShell.java:428)  
        at tcl.lang.Notifier.serviceEvent(Notifier.java:444)  
        at tcl.lang.Notifier.doOneEvent(Notifier.java:585)  
        at tcl.lang.JaclShell.invoke(JaclShell.java:193)  
        at com.sun.web.admin.cli.shelladapter.WSadminShell.invokeJaclShell(WSadminShell.java:122)  
        at com.sun.web.admin.cli.shelladapter.WSadminShell.main(WSadminShell.java:104)  
```
  
The java::call is used to call a static method in the provided class. In this instance we call dumpStack static method in Thread class.  
  
The last few lines are pretty interesting, It tells us that there is a class called WSadminShell that has invoked the class called JaclShell.  
Let us explore these two classes.  
  
reflect.tcl

```
namespace eval Reflect {  
    namespace export get_class for_each_el  
  
    proc get_class {cl} {  
        return [java::field $cl class]  
    }  
    proc get_name {i} {  
        return [[$i getClass] getName]  
    }  
    proc for_each_el {arr cmd} {  
        set size [$arr length]  
        set result {}  
        for {set i 0} {$i &lt; $size} {incr i} {  
            set e [$arr get $i]  
            java::lock $e  
            lappend result [eval $cmd]  
        }  
        return $result  
    }  
}  
```

```
> source reflect.tcl  
> namespace import Reflect::\*  
```
  
The above commands will import all the methods defined in the reflect namespace to the global.  
  
```
> set shelladapter "com.sun.web.admin.cli.shelladapter"  
> set methods [[get_class $shelladapter.WSadminShell] getDeclaredMethods]  
> for_each_el $methods {  puts [$e getName] }
main  
invokeJaclShell  
exitIfNotShell  
handleError  
handleError  
handleError  
invokeFramework  
getArg  
getBooleanArg  
getRCFile  
getScriptFileName  
getScriptFilePosition  
invokeConnectCommand  
isConnectOpt  
printVersionAndExit  
printCommandLine  
```
  
As you would have doubtless noticed, the for_each_el is a control structure that we have just defined. It is a powerful faciilty that can be combined  
with upvar and upeval to emulate almost any kind of features in other languages.  

```
> for_each_el $methods {puts "[$e getName] - [[$e getParameterTypes] length]"}  
main - 1  
invokeJaclShell - 1  
exitIfNotShell - 2  
handleError - 1  
handleError - 1  
handleError - 1  
invokeFramework - 1  
getArg - 3  
getBooleanArg - 3  
getRCFile - 1  
getScriptFileName - 1  
getScriptFilePosition - 1  
invokeConnectCommand - 1  
isConnectOpt - 1  
printVersionAndExit - 0  
printCommandLine - 1  
```
  
The number of arguments taken by each method.  
Some of the interesting methods that seem to exist are (purely based on method names)  
  
```
invokeJaclShell - 1  
invokeFramework - 1  
invokeConnectCommand - 1  
```
  
let us try the same with JaclShell, the other interesting class  
  
```
> set methods [[get_class tcl.lang.JaclShell] getDeclaredMethods]       
> for_each_el $methods {puts "[$e getName] - [[$e getParameterTypes] length]"}  
invoke - 1  
evalRC - 0  
loadWadm - 0  
reader - 0  
fetchCommands - 0  
getTclshrcContent - 0  
```
  
This is slightly more interesting than the other one.  
the interesting ones here seems to be   
`reader` , `fetchCommands`
  
Let us take the first one, reader and see what it can tell us  

```
> java::info class [java::call tcl.lang.JaclShell reader]  
jline.ConsoleReader  
```
  
  
This is pretty interesting. More so because it does not belong to either com.sun.xxxx or tcl.lang.xxx which   
we are expecting. There is a high chance that this is from a different product. Let us ask google.  
The source for this particular class seems to be accessible [here](http://sourceware.org/frysk/javadoc/public/jline/ConsoleReader-source.html).  
  
[Jline](http://jline.sourceforge.net/) is a package that gives you history, keboard shortcuts and auto completion according to their website.  
Since the wadm does have all these, it stands to reason that wadm is using jline to implement these.  
  
Let us see if we can add a simple completion command to it.  
looking at the fields of jline.ConsoleReader  
  
```
> set f_console [[java::field jline.ConsoleReader class] getDeclaredFields]  
> java::lock $f_console  
> for_each_el $f_console {puts "$i - [$e getName]" }  
0 - prompt  
1 - useHistory  
2 - CR  
3 - KEYMAP_NAMES  
4 - keybindings  
5 - bellEnabled  
6 - mask  
7 - NULL_MASK  
8 - autoprintThreshhold  
9 - terminal  
10 - completionHandler  
11 - in  
12 - out  
13 - buf  
14 - debugger  
15 - history  
16 - completors  
17 - echoCharacter  
18 - class$jline$ConsoleReader  
```

Of these, according to the jline source, the 'completors' holds the current completion classes.  
let us define another procedure for easy access of fields  


```
proc get_fields {cl method} {  
    set arr [[java::field $cl class] $method]  
    set result {}  
    foreach {l} [for_each_el $arr {list [$e getName] $e}] {  
        set result [concat $result $l]  
    }  
    return $result  
}  

```

You can use it as  


```
> array set c_fields [get_fields jline.ConsoleReader getDeclaredFields]  
> puts [$c_fields(completors) getName]  
```
  
circumvent private access.  

```
> $c_fields(completors) setAccessible true  
> $c_fields(completors) get [java::call tcl.lang.JaclShell reader]  
> get_name [$c_fields(completors) get [java::call tcl.lang.JaclShell reader]]  
java.util.LinkedList  
```
  
so let us go and get one of items out.  

```
> [$c_fields(completors) get [java::call tcl.lang.JaclShell reader]] get 0               
no accessible method "get" in class java.lang.Object  
```
  
So we have to cast it to get this things out

```
> set completor [[java::cast java.util.List [$c_fields(completors) get [java::call tcl.lang.JaclShell reader]]] get 0]  
java0x188  
```

save for later

```
> java::lock $completor  
```

```
> get_name $completor  
jline.ArgumentCompletor  
```

So, we got the ArgumentCompletor instance in wadm which is used for completion of arguments. looking at it,  


```
> get_fields jline.ArgumentCompletor getDeclaredFields  
completors java0x191 delim java0x192 strict java0x193  
```
  
From [here(external)](http://sourceware.org/frysk/javadoc/public/jline/ArgumentCompletor-source.html) it looks like completors are the ones we need.  

```
> array set a_completor [get_fields jline.ArgumentCompletor getDeclaredFields]  
> $a_completor(completors) setAccessible true  
```

Using the earlier set variable completor  
  
```
> $a_completor(completors) get $completor      
java0x1aa  
> get_name [$a_completor(completors) get $completor]  
[Ljline.Completor;  
```
  
It is an array (the L syntax in java is for array)  
so we use reflection to get to the array elements.  
  
```
> set clist [$a_completor(completors) get $completor]   
```
  
save for later  

```
> java::lock $clist  
```
  
```
> java::call java.lang.reflect.Array get $clist 0  
java0x1b1  
```

  
```
> get_name [java::call java.lang.reflect.Array get $clist 0]  
jline.SimpleCompletor  
```
  
save for later  

```
> set s_completor [java::call java.lang.reflect.Array get $clist 0]  
> java::lock $s_completor  
```
  
```
> get_fields jline.SimpleCompletor getDeclaredFields  
candidates java0x1ba delimiter java0x1bb filter java0x1bc  
```
  
The candidats seem an interesting option.  

```
> array set s_fields [get_fields jline.SimpleCompletor getDeclaredFields]  
> puts $s_fields(candidates)  
java0x1c4  
```
  
```
> $s_fields(candidates) setAccessible true  
> get_name [$s_fields(candidates) get $s_completor]  
java.util.TreeSet  
```
  
```
> [java::cast java.util.TreeSet [$s_fields(candidates) get $s_completor ]] add "true-blue"  
```
  
There. we have added a new auto completion to the wadm.  
You can test it by trying this in the wadm prompt.  


```
> true-[TAB]   
```

and it should complete itself to  

```
> true-blue   
```
  
the complete reflect.tcl  

```
namespace eval Reflect {  
    namespace export get_class for_each_el get_fields get_name  
  
    proc get_class {cl} {  
        return [java::field $cl class]  
    }  
  
    proc get_name {i} {  
        return [[$i getClass] getName]  
    }  
  
    #get_fields jline.ConsoleReader getDeclaredFields  
    proc get_fields {cl method} {  
        set arr [[java::field $cl class] $method]  
        set result {}  
        foreach {l} [for_each_el $arr {list [$e getName] $e}] {  
            set result [concat $result $l]  
        }  
        return $result  
    }  
  
    proc for_each_el {arr cmd} {  
        set size [$arr length]  
        set result {}  
        for {set i 0} {$i &lt; $size} {incr i} {  
            set e [$arr get $i]  
            java::lock $e  
            lappend result [eval $cmd]  
        }  
        return $result  
    }  
}  
```

  
You can load this in your wadm to get the customized auto completions in your wadm shell.  
  
Please be ware that we are modifying the private interfaces of the jline and wadm   
and these may change in further releases. Do not use this for serious work.  
  
We will explore adding options to the command completion at a later time.
