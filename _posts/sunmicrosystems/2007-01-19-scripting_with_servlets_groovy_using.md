---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 VI) Scripting with servlets [groovy - using jsr223]
title: (SJSWS7.0 VI) Scripting with servlets [groovy - using jsr223]
---

#### About the language

[groovy](http://groovy.codehaus.org/) is a language much like ruby, except that it's only implementation is over jvm. Its claim to
fame is that it integrates tightly with the jvm and the java libraries. (It does not provide any libraries
other than what the java itself provides in its standard libraries). However the language itself is quite
powerful and supports most of the higher order programming constructs.

(From a moderate hight, the languages like Groovy, Ruby, Javascript, Jython, Sleep all look
very similar. You can take what you have learned in one language and expect almost similar tools and
syntactical constructs to be available in the other languages too.  If you are interested in languages that
really have a very different look and feel, go for either Functional languages -- like Haskell  or for things
really different, go for Concatenative languages like [Joy](http://en.wikipedia.org/wiki/Joy_%28programming_language%29). Unfortunately for us while Haskell has a jvm
implementation called [Jaskell](http://jaskell.codehaus.org/), The language Joy does not seem to have one. Some others like [Factor](http://factorcode.org/)
did have a jvm implementation but it seems to have moved to native land now.)

##### Existing Implementations

Groovy has [groovlets](http://groovy.codehaus.org/Groovlets)

 

In this entry, the discussion is on creating a generic JSR223 compatible servlet that is able to load any
scripting api - (jsr223) aware language. To that end Our servlet will either try to figure out the language
used from the scripting language handler extension, or will rely on the user supplying a 'language' as an
initialization parameter.

We will try to make use of the '**Invocable' **interface if it is provided by the language implementation
to invoke the individual method handlers. However if the language does not provide the Invocable
interface will fall back to just evaluating the scripts with relevant variables bound to the context.

One more detail here is that, unlike the other entries, Closures are not used for binding the variables
instead, We evaluate the script handler first with the 'httpservlet' variable bound to instance of our
java servlet, and let it define the function names that can be called later as the entries in our symbol table.

The printEngines() method is provided for debugging support. In case the you find that the scripts does not
evaluate, call the printEngines() and monitor the stdout. Perhaps the engine is not getting registered properly.

 You can make use of the JSR223Servlet implemented here with any of the other languages that support the
java scripting API. The only need is to implement the servlet handler part in the language of your choice and
make sure that you redirect the requests to the servlet initialized with the correct 'language' parameter.

#### External Components

We make use of the Groovy Scripting libraries implemented by [Sundararajan](http://blogs.sun.com/sundararajan/) and Mike available [here](https://scripting.dev.java.net/) 
They have quite a few languages already made aware of the scripting interface now.
 

#### JSR223Servlet

The ScriptServlet developed in the previous [entry](http://rahul.gopinath.org/sunblog/2007/01/blue/entry/scripting_with_servlets_sun_java) is used here as the parent class. 
 


```
package com.sun.servlet;

import java.io.*;
import java.util.*;
import java.util.regex.*;

import javax.servlet.*;
import javax.servlet.http.*;

import javax.script.*;

public class JSR223Servlet extends ScriptServlet {

    private static Pattern FILENAME = Pattern.compile("\^(.*).([\^.]+)$");
    protected ScriptEngineManager _sem = new ScriptEngineManager();
    protected ScriptEngine _eng = null;

    protected ScriptEngine getScriptEngine(String filename)
        throws Exception {
        // see if the user has some preference?
        String lang = getServletConfig().getInitParameter("language");
        if (lang != null) {
            ScriptEngine se = _sem.getEngineByName(lang);
            if (se!= null)
                return se;
        }

        // or figure out the engine to use by extension.
        Matcher m = FILENAME.matcher(filename);
        if (m.matches()) {
            String ext = m.group(1);
            ScriptEngine se = _sem.getEngineByExtension(ext);
            if (se != null)
                return se;
        }

        // we failed miserably. :(
        throw new Exception("Unable to figure out a script engine to use.");
    }

    public void initialize(String handler, Object code)
        throws Exception {
        List<ScriptEngineFactory> list = _sem.getEngineFactories(); // seems needed for init.
        _eng = getScriptEngine(handler);
        // we want to bind the variable httpservlet for initialization rather than
        // call a method.
        _eng.getContext().setAttribute("httpservlet", this, ScriptContext.ENGINE_SCOPE);
        _eng.eval((String)code);
    }

    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {
        try {
            if (_eng instanceof Invocable) {
                Invocable inv = (Invocable)_eng;
                inv.invokeFunction((String)fn, this, request, response);
            } else {
                _eng.getContext().setAttribute("httpservlet", this, ScriptContext.ENGINE_SCOPE);
                _eng.getContext().setAttribute("request", request, ScriptContext.ENGINE_SCOPE);
                _eng.getContext().setAttribute("response", response, ScriptContext.ENGINE_SCOPE);
                _eng.eval((String)fn);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void printEngines() {
        List<ScriptEngineFactory> list = _sem.getEngineFactories();
        System.out.println("Supported Script Engines");
        for (ScriptEngineFactory factory: list) {
            // Obtains the full name of the ScriptEngine.
            String name = factory.getEngineName();
            String version = factory.getEngineVersion();
            // Returns the name of the scripting language
            // supported by this ScriptEngine
            String language = factory.getLanguageName();
            String languageVersion = factory.getLanguageVersion();
            System.out.printf("Name: %s (%s) : Language: %s v. %s \\n",
                    name, version, language, languageVersion);
            // Get a list of aliases
            List<String> engNames = factory.getNames();
            for(String e: engNames) {
                System.out.printf("\\tEngine Alias: %s\\n", e);
            }
        }
    }

```


 

### Providing the handler

#### Jvm Bindings.

The java objects are accessed in the same way as that of native java in groovy. 

ie:  System.out.println("mystring") is written as System.out.println "mystring" - with or with out the parens.

**docroot/WEB-INF/code/groovy.groovy**



```
def do_service (httpservlet, request, response) {
    out = response.getWriter()
    response.setContentType("text/html")
    try {
        spath = request.getServletPath()
        filename = httpservlet.getServletConfig().getServletContext().getRealPath(spath)
        GroovyShell shell = new GroovyShell()
        shell.setVariable("request", request);
        shell.setVariable("response", response);
        shell.setVariable("httpservlet", httpservlet);
        out.println shell.evaluate(httpservlet.read(filename).toString(), filename)
    } catch (e) {
        out.println "<html><body><b>Servlet Error ( "+ e.getMessage() + "</b><xmp> "
        e.printStackTrace(out);
        out.println " </xmp></body></html>"
    }
}

httpservlet.add('get', "do_service")
httpservlet.add('post', "do_service")
```




Here we are taking another route than the previous entries. We define do_service as a function that takes
two arguments, and set the function name in the symbol table (rather than the closures that we used in previous
entries or the entire script as was the case in jacl.) Since the httpservlet is defined when the complete
script is evaluated the first time, this variable is available for the function too.

The JSR223Servlet takes care of calling the functions with necessary arguments.

An example groovy script that can get executed:

**/docroot/hello.groovy**



```
pre = "<html> <head><title>abc</title></head> <body> <h1> Hello at "
date = new Date()
from = " from "
path = request.getServletPath()
post = "</h1>  </body> </html>"
pre + date + from + path + post
```

#### Build  Steps.

          The complete groovy-webapp can be downloaded [here](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/servlets/groovy-webapp.tar.gz). Extract the contents to a directory called 'groovy'
inside samples in your installation (**samples/java/webapps/groovy**). It has to be in that directory to make use
of the common.xml during ant build.

#### Important 

This will work only with JDK6. So make sure that when you install your Sun Java System WebServer, you choose
to install it with a pre-installed JDK6 rather than the bundled JDK. Even if you have installed your
Sun Java System WebServer with bundled JDK(5), you can still change the **java.home** variable to point to jdk6
in **server.xml **and use this sample.

Your extracted directory will look like this.

```
> cd groovy
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/JSR223Servlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/groovy-1.0.jar
./src/docroot/WEB-INF/lib/groovy-engine.jar
./src/docroot/WEB-INF/lib/asm-2.2.jar
./src/docroot/WEB-INF/lib/asm-analysis-2.2.jar
./src/docroot/WEB-INF/lib/asm-attrs-2.2.jar
./src/docroot/WEB-INF/lib/asm-tree-2.2.jar
./src/docroot/WEB-INF/lib/asm-util-2.2.jar
./src/docroot/WEB-INF/lib/antlr-2.7.5.jar
./src/docroot/WEB-INF/lib/LICENSE.TXT
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/groovy.groovy
./src/docroot/index.html
./src/docroot/hello.groovy
./src/ScriptServlet.java
./deploy.tcl
```

Please note that there are a number of jar files required for this to work. You need the groovy-engine
supplied by https://scripting.dev.java.net/ , the asm antlr and groovy jars supplied by the groovy project.

The groovy-webapp.war will be created in the groovy directory when you run ant from inside
the src. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

Once the deployment goes through, you will be able to access the js file using the url

http://yourserver:port/groovy/hello.groovy 
