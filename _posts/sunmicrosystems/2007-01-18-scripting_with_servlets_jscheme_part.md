---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 II) Scripting with servlets [jscheme]
title: (SJSWS7.0 II) Scripting with servlets [jscheme]
---

#### Prior work:

Jscheme already has a good servlet [implementation](http://jscheme.sourceforge.net/jscheme/src/jschemeweb/SchemeServlet.java) distributed along with jscheme.jar. The ScriptServlet.java
that we use is very similar (Infact it was the inspiration for ScriptServlet.java) but the amount is some what
reduced. We also make use of their jscheme (modified) scripts to load the freestanding scripts. 

#### SchemeServlet

The ScriptServlet developed in the previous [entry](http://rahul.gopinath.org/sunblog/2007/01/blue/entry/scripting_with_servlets_sun_java) is used here as the parent class.
 


```
package com.sun.servlet;

import javax.servlet.http.*;
import jscheme.*;

public class SchemeServlet extends ScriptServlet {

    public static JScheme js = new JScheme();

    public void initialize(String handler, Object code)
        throws Exception {
        js.apply((jsint.Procedure)js.eval((String)code),js.list(this));
    }

    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {
        if (request == null)
            js.apply((jsint.Procedure)fn, js.list());
        else
            js.apply((jsint.Procedure)fn, js.list(request, response));
    }
}
```

 

### Providing the scheme handler

#### Jscheme Jvm Bindings.

The jscheme allows java access in a very 'schemish' notation. ie a call like the below

`servlet.getServletConfig( ).getServletContext().getRealPath(new File(file));`
in java is transformed into
`(.getRealPath (.getServletContext (.getServletConfig servlet)) (File. file))`
in jscheme. As you can see the constructor new File(file) looks like (File. file) when
it is called in Jscheme

Using this notation in our handler

**docroot/WEB-INF/code/scheme.scm**



```
;; scheme.scm
;; slightly modified from the version in jscheme distribution.

(lambda (httpservlet)

  (define (doGet request response)
    (define (getRealPath servlet file)
      (.getRealPath (.getServletContext (.getServletConfig servlet)) file))
    (define filename (getRealPath httpservlet (.getServletPath request)))
    (define body (string->expr (.read httpservlet filename)))
    (define proc `(lambda(request response httpservlet out)
                    (let ((b ,body))
                      (if (not (equal? #null b)) (.println out b)))))

    (let ((out (.getWriter response)))
      (.setContentType response "text/html")
      (jsint.Procedure.tryCatch
        (lambda()
          ((eval proc)
           request response httpservlet out))
        (lambda(e)
          (display "
                   <html><body><b>Servlet Error</b><xmp> 
                   [(.printStackTrace e out)]
                   </xmp></body></html>
                   " out)))))

  ;; store scheme procedures into the httpservlet
  (.add httpservlet "get" doGet)
  (.add httpservlet "post" doGet))
```

 

As in the jruby, we return a proc object with an arity 1 on evaluation of this. The argument is used by the evaluator to pass in
the current instance of httpservlet (or rather the ScriptServlet). This larger closure contains the function that defines doGet,
and is added to the symbol table of the ScriptServlet by the line below on execution by **initialize**

```
(.add httpservlet "get" doGet) 
```

An example scheme script is given below. (The scheme handler can execute scripts like this.)

**/docroot/hello.scm** 



```
{<html>
  <head><title>abc</title></head>
  <body>
   <h1> Hello at [(Date.)] from [(.getServletPath request)]</h1>
  </body>
 </html>}
```

#### Build  Steps.

          The complete jschem-webapp is provided [here](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/servlets/jscheme-webapp.tar.gz). You can download it and extract the contents to a
directory called 'jscheme' inside your installation. It should be in the **samples/java/webapps/jscheme** directory
in your installation of webserver as it refers to the common.xml for building.

It also contains the jscheme.jar in the WEB-INF/lib, which may not be latest.

Your extracted directory will look like this.

```
> cd jscheme
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/SchemeServlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/jscheme.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/scheme.scm
./src/docroot/index.html
./src/docroot/hello.scm
./src/ScriptServlet.java
./deploy.tcl
```


You can run 'ant' from inside the src directory which will create the jscheme-webapp.war in the
jscheme directory. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

 Once the deployment goes through, you will be able to access the scheme file using the url

http://yourserver:port/jscheme/hello.scm

  
