---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm VIII) Through the looking glass - implement extensions
title: (wadm VIII) Through the looking glass - implement extensions
---

In one of the last sections, We explored the java commands that were available 
from the wadm but that is not all. 
If necessary we can interface java to wadm by making available the java libraries
as commands. In this section I will take you through implementing an extension 
command for wadm (jacl).

We need to implement two classes. 

* The extension that will create the command(s) when it is loaded,
* The command class itself.


### First Try

```
package blue;
import tcl.lang.Interp;
import tcl.lang.Extension;

public class MyExtension extends Extension {
    public void init(Interp interp) {
        interp.createCommand(MyCmd.name, new MyCmd());
    }
}
```

```
package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd"
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        try {
            System.out.println(name + ":Here I am");
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}
```

Compiling it,

```
$ export CLASSPATH=$CLASSPATH:&lt;wsroot&gt;/lib/wadmcli.jar
$ export CLASSPATH=$CLASSPATH:&lt;wsroot&gt;/lib/jacl.jar
$ export CLASSPATH=$CLASSPATH:&lt;wsroot&gt;/lib/tcljava.jar
$ export CLASSPATH=$CLASSPATH:&lt;wsroot&gt;/lib/cli-framework.jar
$ javac -d *.java
$ jar -cf blue.jar blue
```

Let us startup wadm and check them out.
(Assuming that you are starting wadm from the current directory. Other wise change the -classpath to point to blue.jar)

```
$ java::load -classpath blue.jar blue.MyExtension
$ my-cmd
my-cmd :Here I am
```


So we will be able to make a simple wadm shell command, but compared to
other wadm commands it has two major defects.

* It does not have auto completion.:  I am not going to explain it here since it is not one of the published interfaces but as a hint..

We are using the [glassfish](http://www.glassfishwiki.org/gfwiki/attach/GlassFishAdminReferences/s1as8_cli_framework_cookbook.html) for the command ,option parsing and Using a file similar to CLI Descriptor can be found in the jars. The auto completion is also  done using the same file. So you can extract the the file from jar, put your  commands in (as described in the above link) and repackage it, and autocomplete for command and its options should work fine.

* It does not work in stand alone mode

The above hint works here too. You can define your own command by deriving it
from the [Command](http://appserver.sfbay.sun.com/apollo/cli/api/framework/) and you can add it to our descriptor file. If you are going this
way, then you can change the wadm[sh|bat] to load your jar file too.


Well that seems to have worked. Let us add a little more, say argument processing and see.


#### Argument Processing

The jacl gives us all the arguments in the 'TclObject argv[]' variable that is passed in
the format of the argv is similar to java :argv[0] = command name and argv[&gt;0] the rest of arguments. 

```
package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd";
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        StringBuffer sb = new StringBuffer();
        try {
            for (Object o: argv) {
                sb.append(":"+o);
            }
            System.out.println(name + sb);
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}
```

#### Using It

```
$ java::load -classpath blue.jar blue.MyExtension
$ my-cmd abc def g
my-cmd:my-cmd:abc:def:g
```

To avoid the manual loading every time, let it add it to .wadmrc

```
catch {
package require java
java::load -classpath "blue.jar" blue.MyExtension
} err
puts $err
```

When dealing with java and especially in .wadmrc, it is always a nice thing to wrap 
your loading in catch block. Other wise the only sign of an error or an exception will
be 'Invalid RC File' printed on your console when you invoke the wadm.


#### Strings and Lists

Your commands can take both Strings and lists. 
(The strings are same as lists in tcl, a multivalue list is nothing but a string with spaces in 
them which also means that a word is a single value list.)

It depends on the command to distinguish as to what was passed in was a String, a List 
or a number(int/real). You can get the string representation of the argument by just doing
a argv[xxx].toString. If a list was passed in, then you will get the list in tcl representation
ie:

```
> my-cmd a b c    
my-cmd:my-cmd:a:b:c
> my-cmd {a b c}
my-cmd:my-cmd:a b c
> my-cmd {a b c} {d e f}
my-cmd:my-cmd:a b c:d e f
> my-cmd {a {b c}} {d e f}
my-cmd:my-cmd:a {b c}:d e f
```

The strings that get passed in can be any thing..

```
> my-cmd --name mexico -p 8080 newmexico
my-cmd:my-cmd:--name:mexico:-p:8080:newmexico
```

You can use a library like getopt to parse these. (Or make use of the bundled glassfish 
cli-framework to do it for you.)


#### Returning Values

    Often times you are interested in the return values of the command you ran. Let us
see how our newly implemented command fares

```
> set out [my-cmd --name mexico -p 8080 newmexico]
my-cmd:my-cmd:--name:mexico:-p:8080:newmexico
> puts $out
>

```
Unfortunately it does not work. In order for the tcl to receive a value, it has to be 
passed in another fashion. There are different ways for things that contain just one
element and things that return multi element lists.

##### Strings

For strings we just set the result string into the interpretor as shown below,

```
package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd";
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        StringBuffer sb = new StringBuffer();
        try {
            for (Object o: argv) {
                sb.append(":"+o);
            }
            interp.setResult(name + sb);
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}
```


```
> set out [my-cmd --name mexico -p 8080 newmexico]
my-cmd:my-cmd:--name:mexico:-p:8080:newmexico
> puts $out
my-cmd:my-cmd:--name:mexico:-p:8080:newmexico
```


##### Lists

For producing tcl lists, you have to instanciate TclList instance and keep appending
the elements to it, then return its stirng representation in the interp.

```
package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd";
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        TclObject obj =  TclList.newInstance();
        try {
            for (Object o: argv) {
                TclList.append(interp, obj, 
                    TclString.newInstance(o.toString()));
            }
            interp.setResult(obj.toString());
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}
```

```
> set out [my-cmd --name mexico -p 8080 newmexico]      
my-cmd --name mexico -p 8080 newmexico
> puts $out
my-cmd --name mexico -p 8080 newmexico

> set out [my-cmd --name "My mexico" -p 8080 newmexico]
my-cmd --name {My mexico} -p 8080 newmexico
> puts $out                                            
my-cmd --name {My mexico} -p 8080 newmexico
```

You can see the difference here.

##### Handling Errors

         For robust implementations, you also need to let the tcl know about
any errors in the execution (That includes validation errors and process errors)
In wadm, you can do that by throwing a TclException when you encounter 
such a problem,

```
package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd";
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        if (argv.length == 1)
            throw new TclException(interp,"Need at least 1 argument");
        TclObject obj =  TclList.newInstance();
        try {
            for (Object o: argv) {
                TclList.append(interp, obj,
                    TclString.newInstance(o.toString()));
            }
            interp.setResult(obj.toString());
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}
```

```
> my-cmd   
Need at least 1 argument
> if [catch {my-cmd} err] {
      puts "-- $err"
}
-- Need at least 1 argument
>       
> if [catch {my-cmd -one} err] {
      puts "-- $err"
}
```

As you see no error was thrown when passing an option. The error is
caught by tcl when the problematic statement or script is enclosed in a
`catch {....} err`  block

You can use these as a template for your work.
[MyCmd.java](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/MyCmd.java)
[MyExtension.java](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/MyExtension.java)

--removing auto completion since that is not a published interface.
but a hint, We are using the [glassfish](http://www.glassfishwiki.org/gfwiki/attach/GlassFishAdminReferences/s1as8_cli_framework_cookbook.html) for the command ,option parsing and Using a file
similar to CLI Descriptor can be found in the jars. The auto completion is also done using
the same file.
