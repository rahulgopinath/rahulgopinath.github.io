---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 III) Scripting with servlets [rhino]
title: (SJSWS7.0 III) Scripting with servlets [rhino]
---

Writing Javascript servlets using [Rhino ](http://www.mozilla.org/rhino/)on Sun Java System WebServer 7.0.

#### About the language

Javascript is one of the few languages that are exceptionally neat in the specification. The syntax
is very simple and there are are very few exceptions to the rules. It provides a prototype based
inheritance model and supports all the higher order constructs like closures, objects, exceptions
etc.. 

Since I had already discussed the complete sequence of instructions to get the servlets up and
running using other languages, I will stick to a somewhat brief outline here.

If you are using JDK6, then you already have access to scripting APIs in java, using which you
can load the language dynamically. It is simple to modify our parent ScriptServlet to do this (based
on a parameter passed in init, you can decide on the language loaded. I will treat that in a later entry.)

#### RhinoServlet

The ScriptServlet developed in the previous [entry](http://rahul.gopinath.org/sunblog/2007/01/blue/entry/scripting_with_servlets_sun_java) is used here as the parent class. 
 


```
package com.sun.servlet;

import javax.servlet.http.*;
import org.mozilla.javascript.*;
import org.mozilla.javascript.tools.shell.Global;

public class RhinoServlet extends ScriptServlet {
    public Context jm = Context.enter();
    protected final Global global = new Global();

    protected void finalize() throws Throwable {
        Context.exit();
    }

    public void initialize(String handler, Object code) throws Exception {
        global.init(jm);
        Function funct = jm.compileFunction(global, (String)code, handler, 1, null);
        funct.call(jm, global, funct, new Object[] {jm.javaToJS(this, global)});
    }

    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {
        ((Function)fn).call(jm, global, (Function)fn, new Object[] {
            jm.javaToJS(request, global), 
            jm.javaToJS(response, global)});
    }
}
```

 

### Providing the javascript handler

#### Jvm Bindings.

The bindings are just like pure java, ie Use the 'dot' notation to access methods in objects.
(check out the nice [entry](http://blogs.sun.com/sundararajan/entry/java_integration_javascript_groovy_and) by Sundararajan that compares the java bindings of various jvm languages
if you would like to know more.)

**docroot/WEB-INF/code/rhino.js**



```
function (httpservlet) {
    do_get = function (request,response) {
        response.setContentType("text/html");
        this.out = response.getWriter();

        this.request = request;
        this.response = response;
        this.httpservlet = httpservlet;

        try {
            spath = request.getServletPath();
            filename = httpservlet.getServletConfig().getServletContext().getRealPath(spath);
            body = httpservlet.read(filename) + ""; // convert body to javascript string.
            this.out.println(eval(body));
        } catch (e) {
            this.out.println("<html><body><b>Servlet Error ("
                    + e.name + ")</b><xmp>" + e.message + "</xmp></body></html>");
        }
    }
    httpservlet.add('get', do_get);
    httpservlet.add('post', do_get);
}
```



As usual, we return a proc object with an arity 1 using which we get the current instance of  ScriptServlet. then we proceed
to set the 'get' and 'post' symbols

An example js script that can get executed:

**/docroot/hello.js** 



```
"<html> <head><title>abc</title></head> <body> <h1> Hello at "
    + new Date() + " from " + request.getServletPath() 
    + " </h1> </body> </html>"
```

#### Build  Steps.

          The complete rhino-webapp is provided [here](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/servlets/rhino-webapp.tar.gz). You can download it and extract the contents to a
directory called 'rhino' inside your installation. It should be in the **samples/java/webapps/rhino** directory
in your installation of webserver as it refers to the common.xml for building.

Update the js.jar if required. 

Your extracted directory will look like this.

```
> cd rhino
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/RhinoServlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/js.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/rhino.js
./src/docroot/index.html
./src/docroot/hello.js
./src/ScriptServlet.java
./deploy.tcl
```


You can run 'ant' from inside the src directory which will create the rhino-webapp.war in the
rhino directory. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

 Once the deployment goes through, you will be able to access the js file using the url

http://yourserver:port/rhino/hello.js

  
