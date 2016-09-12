---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 I) Scripting with servlets [jruby]
title: (SJSWS7.0 I) Scripting with servlets [jruby]
---

Writing Jruby servlets on Sun Java System WebServer 7.0. 

#### Prior work:

Jruby already has an [implementation](http://www.nabble.com/RubyServlet-t2915413.html) of servlets by <script>document.write('[');](http://rahul.gopinath.org/sunblog/2007/01/14/scripting_with_servlets_sun_java1/%5C%5C%22')[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[](http://blogs.sun.com/user/UserProfile.jtp?user=431520)[Marcin Mielżyński](http://www.nabble.com/user/UserProfile.jtp?user=431520)
It has these features:

* Loosely based on PyServlet (servlet implementation for jython)
* Mimics RailsControllers
* Offers three kinds of servlets
  * StatefullServlet that behaves like Rails controller (if instantiated every request)
  * StatelessServlet that behaves like standard stateless Java servlet
  * SessionServlet - is kept transparently in session (is its instance variables are not shared between sessions) 

 However it also has these features that I did not like 

* Too Rails oriented.         
  * Servlets in ruby should be preferably similar to java servlets rather than look like Rails

* Does too many things in java.
  * We should do only the basic framework in java and delegate the rest to the ruby world. This way a programmer who
is more comfortable in ruby will be able to implement any feature that he wants with out being impeded by 
the implementation of our servlet code in java. More over, the code in java generally becomes immutable once it 
gets compiled and added into a jar.

It would be much more nicer to delegate the responsibility of doing these things to the handler in ruby rather than to do it in java.
This would allow the possibility of allowing the programmer to construct different varieties of handler servlets in ruby itself during
the development with out touching the java code (compiling and jar-ing)

#### Our approach.

Making use of the ScriptServlet developed in the previous [entry](http://blogs.sun.com/blue/entry/scripting_with_servlets_sun_java), we create a simple class that provides necessary initialization
and evaluation primitives. 
 


```
package com.sun.servlet;

import javax.servlet.http.*;

import org.jruby.*;
import org.jruby.ast.Node;
import org.jruby.javasupport.JavaUtil;
import org.jruby.runtime.builtin.IRubyObject;

public class RubyServlet extends ScriptServlet {
    public static IRuby jr = Ruby.getDefaultInstance();

    public void initialize(String handler, Object code) throws Exception {
        jr.getLoadService().require("java");
        Node script = jr.parse((String)code, handler, jr.getCurrentContext().getCurrentScope());
        // The script file returns a single proc with arity 1
        ((RubyProc)jr.eval(script)).call(new IRubyObject[] {wrap(this)});
    }

    protected IRubyObject wrap(Object object) {
        IRubyObject result = JavaUtil.convertJavaToRuby(jr, object);
        return jr.getModule("JavaUtilities").callMethod(jr.getCurrentContext(), "wrap", result);
    }

    public void eval(Object fn, HttpServletRequest request,  HttpServletResponse response) {
        if (request == null)
            ((RubyProc)fn).call(new IRubyObject[0]);
        else
            ((RubyProc)fn).call(new IRubyObject[] {wrap(request), wrap(response)});
    }
}
```

 

Here we use the **initialize** method to read in the handler specified, and executes it. The handler (which is in ruby) is responsible
for specifying the behavior of our servlet. It specifies which HTTP methods are supported, and how the Request URI is interpreted.

The **eval** method provides a way for the scripts that are in place for HTTP method processing to be executed by the ScriptServlet.

### The Ruby Dimension

#### Jvm Bindings for jruby.

Jruby allows us to access the methods of a class or instance the same way as that of java, by using the 'dot' notation.
Thus to print something to the stdout, we can use the statement

 System.out.println 'my string'

 with the jruby correctly invoking System.out.println in java.

 Thus our handler can be written as below.

**docroot/WEB-INF/code/ruby.rb**



```
proc {|httpservlet|
    do_get = proc {|request,response|
        out = response.getWriter
        response.setContentType "text/html"

        begin
            spath = request.getServletPath
            filename = httpservlet.getServletConfig.getServletContext.getRealPath(spath)
            out.println eval(httpservlet.read(filename))
        rescue Exception => e
            out.println %{<html><body><b>Servlet Error (#{e.message})</b><xmp> 
                   #{e.backtrace}
                   </xmp></body></html>}
        end
    }
    httpservlet.add('get', do_get)
    httpservlet.add('post', do_get)
}
```

 

We return a proc object with an arity 1 to the evaluator. This is done to allow the servlet initializer to pass the
httpservlet object as an arguement. We could also have bound the httpservlet to a global variable.

Inside the larger anonymous proc, we define a second proc for do_get, and bind it to the 'get' and 'post' methods of httpservlet.
these procs take request and response as the arguments. They extract the name of the script and load and evaluate the script
referenced.  The script that gets evaluated has complete access to the variables request, response, out and httpservlet just like
a normal java servlet or a jsp page.Any exceptions are printed to the response output stream. 

A simple ruby script that may be loaded by this handler will look like this.

**/docroot/hello.rb** 



```
def myhello
     return %{<html>
<head><title>abc</title></head>
  <body>
   <h1> Hello at #{java.util.Date.new} from #{@request.getServletPath}</h1>
  </body>
 </html>}
end
myhello
```

#### Build  Steps.

          A complete webapp is provided [here](http://blogs.sun.com/blue/resource/servlets/jruby-webapp.tar.gz). You can download it and extract the contents to a
directory called 'jruby' inside your installation. In order for the build.xml to work, It should be in
the **samples/java/webapps/jruby** directory in your installation of webserver.

It also contains the jruby.jar in the WEB-INF/lib, which should be replaced with the latest
jruby.jar if necessary.

Your extracted directory will look like this.

```
> cd jruby
> find .
./docs
./docs/index.html
./src
./src/build.xml
./src/RubyServlet.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/jruby.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/code
./src/docroot/WEB-INF/code/ruby.rb
./src/docroot/index.html
./src/docroot/hello.rb
./src/ScriptServlet.java
./deploy.tcl
```


You can run 'ant' from inside the src directory which will create the jruby-webapp.war in the
jruby directory. This war file can be deployed on the webserver using the wadm.

```
wadm  -u admin -f deploy.tcl
```

Once the deployment goes through, you will be able to access the ruby file using the url

http://yourserver:port/jruby/hello.rb
