---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 IV) Scripting with servlets [sleep]
title: (SJSWS7.0 IV) Scripting with servlets [sleep]
---

Using sleep (A perl like language over JVM) as servlet on Sun Java System WebServer 7.0.

About the language
Sleep is a language inspired by perl. Most of the syntax is same as that of the perl (with some
differences). This is the closest there is to perl on jvm and that makes this language worth
a better look (IMO). The language does offer higher order programming primitives like closures
but other stuff like exception handling feels somewhat primitive. The closures are invoked using
a syntax reminiscent of Objective C (with named parameters), and the Java Objects are treated
the same as closures.

SleepServlet
The ScriptServlet developed in the previous entry is used here as the parent class.

```
package com.sun.servlet;

import javax.servlet.http.*;
import java.util.*;
import sleep.interfaces.Evaluation;
import sleep.runtime.*;
import sleep.engine.*;
import sleep.bridges.*;
import sleep.error.*;

public class SleepServlet extends ScriptServlet {

    ScriptLoader loader = new ScriptLoader();
    ScriptInstance js = null;

    public StringBuffer err = new StringBuffer();

    public void initialize(String handler, Object code) throws Exception {
        js = loader.loadScript(handler, (String)code, new Hashtable());
        js.addWarningWatcher(new RuntimeWarningWatcher() {
            public void processScriptWarning(ScriptWarning w) {
                String message = w.getMessage();
                int lineNo  = w.getLineNumber();
                String script = w.getNameShort();
                err.append(message + " at " + script + ":" + lineNo + "\\n");
            }
        });

        Block blk = js.getRunnableBlock();
        SleepClosure sc = new SleepClosure(js, blk);

        Stack stk = new Stack();
        stk.push(SleepUtils.getScalar(this));
        sc.callClosure("&main", js, stk);
    }

    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {
        Stack stk = new Stack();
        stk.push(SleepUtils.getScalar(response));
        stk.push(SleepUtils.getScalar(request));
        ((SleepClosure)fn).callClosure("&closure", js, stk);
    }
}
```



Providing the handler
Jvm Bindings.

The  Java objects are treated as closures as mentioned above. The syntax of accessing an object is
very reminiscent of Objective C.

ie:  System.out.println("mystring") is written as [[$System out] println: "mystring"]

(see the ':' after println.)

docroot/WEB-INF/code/sleep.sl

```
($httpservlet) = @_;
$do_get = {
    ($request,$response) = @_;
    $out = [$response getWriter];
    [$response setContentType: "text/html"];

    $spath = [$request getServletPath];
    $filename = [[[$httpservlet getServletConfig] getServletContext] getRealPath: $spath];
    $body = [$httpservlet read: $filename];
    $result = &eval($body);
    if (checkError($error)) {
        [$out println: "<html><h1>Servlet Error</h1><body><xmp>"];
        [$out println: $error];
        [$out println: "</xmp></body></html>"];
    } else {
        if (!&strlen($result)) {
            [$out println: "<html><h1>Servlet Error</h1><body><xmp>"];
            [$out println: [$httpservlet err]];
            [$out println: "</xmp></body></html>"];
        } else {
            [$out println: $result];
        }
    }
};
[$httpservlet add: "get", $do_get];
[$httpservlet add: "post", $do_get];
```



The current instance of ScriptServlet is available as an argument in the local stack for the main closure. The 'get' and 'post'
symbols are also set to the '$do_get' closure so that both doGet and doPost gets redirected to $do_get.


An example js script that can get executed:

/docroot/hello.sl

```
$date = [new java.util.Date];
$script = [$request getServletPath];
return "<html> <head><title>abc</title></head> <body> <h1> Hello at $date from $script";
```

Build  Steps.

The complete sleep-webapp can be downloaded here. Extract the contents to a directory called 'rhino'
inside samples in your installation (samples/java/webapps/rhino). It has to be in that directory to make use
of the common.xml during ant build.

Update the js.jar if required.

Your extracted directory will look like this.

```
> cd sleep
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/SleepServlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/sleep.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/sleep.sl
./src/docroot/index.html
./src/docroot/hello.sl
./src/ScriptServlet.java
./deploy.tcl
```

The sleep-webapp.war will be created in the sleep directory when you run ant from inside
the src. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

 Once the deployment goes through, you will be able to access the js file using the url

http://yourserver:port/sleep/hello.sl



