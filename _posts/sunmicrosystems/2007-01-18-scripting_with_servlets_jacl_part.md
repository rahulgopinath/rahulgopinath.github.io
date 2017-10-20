---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 V) Scripting with servlets [jacl]
title: (SJSWS7.0 V) Scripting with servlets [jacl]
---

#### About the language

[TclJava](http://tcljava.sourceforge.net/docs/website/index.html) [Jacl](http://tcljava.sourceforge.net/docs/website/index.html) is the implementation of TCL over jvm. It supports interaction with the java objects
using the same command notation. While originally a procedural language, extensions like
incrTcl can be used provide object orientation to the language.


#### JaclServlet

The ScriptServlet developed in the previous [entry](http://rahul.gopinath.org/sunblog/2007/01/blue/entry/scripting_with_servlets_sun_java) is used here as the parent class. 
 


```
package com.sun.servlet;

import java.io.*;
import java.util.*;
import tcl.lang.*;

import javax.servlet.http.*;

public class JaclServlet extends ScriptServlet {

    public static Interp jt = new Interp();

    public void initialize(String handler, Object code) throws Exception {
        jt.setVar("httpservlet",ReflectObject.newInstance(jt, JaclServlet.class, this),
              TCL.GLOBAL_ONLY);
        jt.eval((String)code);
    }

    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {
        try {
            jt.setVar("request",ReflectObject.newInstance(jt, HttpServletRequest.class, request),
                  TCL.NAMESPACE_ONLY);
            jt.setVar("response",ReflectObject.newInstance(jt, HttpServletResponse.class, response),
                  TCL.NAMESPACE_ONLY);
            jt.eval((String)fn);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

 

### Providing the handler

#### Jvm Bindings.

The Java objects are treated as commands with in jacl, allowing to interact with them by
using parameters instead of method names. It also provides convenience commands to access
fields, create new objects, calling static methods etc.

ie:  System.out.println("mystring") is written as [java::field System out] println "Mystring"

**docroot/WEB-INF/code/jacl.tcl**



```tcl
package require java

set do_get {
    set out [$response getWriter]
    $response setContentType {text/html}
    set spath [$request getServletPath]
    set filename [[[$httpservlet getServletConfig] getServletContext] getRealPath $spath]
    set e [catch {eval [[$httpservlet read $filename] toString]} o]
    if {$e == 1} {
        $out println "<html><body><h1> ServletError ($o)</h1><xmp>"
        $out println $errorInfo
        $out println {</xmp><body></html>}
    } else {
        $out println $o
    }
}

$httpservlet add get $do_get
$httpservlet add post $do_get
```



The current instance of ScriptServlet is available as the variable 'httpservlet' inside the script. Since jacl
does not have the concept of lexical closures, we are stuck with binding to a variable of our choice, rather than
allow the end user to specify it in jacl.
Due tothe same reason, rather than setting the symbols 'get' and 'post' to executable functions, we associate
them with just strings containing scripts to execute.


An example js script that can get executed:

**/docroot/hello.tcl** 



```
set at [[java::new java.util.Date] toString]
set from [$request getServletPath]
return "<html> <head><title>abc</title></head> <body> <h1> Hello at $at from $from </h1> </body> </html>"
```

#### Build  Steps.

          The complete jacl-webapp can be downloaded [here](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/servlets/jacl-webapp.tar.gz). Extract the contents to a directory called 'jacl'
inside samples in your installation (**samples/java/webapps/jacl**). It has to be in that directory to make use
of the common.xml during ant build.

Update the js.jar if required. 

Your extracted directory will look like this.

```
> cd jacl
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/JaclServlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/jacl.jar
./src/docroot/WEB-INF/lib/tcljava.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/jacl.tcl
./src/docroot/index.html
./src/docroot/hello.tcl
./src/ScriptServlet.java
./deploy.tcl
```

Please note that the jacl used here is 1.3.3 which is superseeded by Jacl 1.4. If you are using Jacl 1.4, then the number of jars
are more. Make sure that you have all the jars from the Jacl 1.4 distribution in your lib directory.

The jacl-webapp.war will be created in the jacl directory when you run ant from inside
the src. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

 Once the deployment goes through, you will be able to access the js file using the url

http://yourserver:port/jacl/hello.tcl 
