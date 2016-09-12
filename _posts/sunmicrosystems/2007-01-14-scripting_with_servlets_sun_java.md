---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 0) Scripting with servlets - prologue
title: (SJSWS7.0 0) Scripting with servlets - prologue
---

In this series I am going to try and see how easily the various scripting languages  
(jscheme, jacl, jruby, sleep, nice, jython, groovy, rhino .. to name a few) that currently runs over jvm  
can be used with the webcontainer as a servlet --  ie exposing the request, response and servlet  
environment to the scripting language.

(This can also be accomplished very easily using JSR223 in JDK6  
a detailed description of using JSR223 is available [here)](http://java.sun.com/developer/technicalArticles/J2SE/Desktop/scripting/)  
  

#### The Why's of it.

         Often the scripting languages are much faster to develop in than java. Most provide more powerful  
syntactic abstraction facilities. The code necessary to accomplish a given task can generally be cut down  
quite a bit using one of these languages. It may also be the case that the developers are more familiar with  
a particular scripting language than with java.

           In the general scenario, for web development, the option the developers have when they want  
to use one of the scripting languages is to go with the CGIs. Unfortunately the fact is that the  
servlets are generally faster than the CGIs even when using FastCGI.  

          The other option is to allow the scripting language to be loaded and executed by a small wrapper  
servlet. The advantage of this option is that It allows the full utilization of Webcontainer's jvm which will  
be optimized for serving web applications. Since a servlet is persistent over a large number of requests,  
we will also be able to cache often used resources inside the servlet.  

#### Writing the wrapper servlet.  

            We provide a base servlet called ScriptServlet which will do most of the work necessary to get a  
script to be loaded and executed. (leaving some work for a custom servlet to be able to optimize the script  
loading and execution when possible.) There is also provide a cache for the scripts that may be manipulated  
from the script if necessary.

 

 
```
package com.sun.servlet;  
  
import java.io.*;  
import java.util.*;  
import javax.servlet.*;  
import javax.servlet.http.*;  
  
public abstract class ScriptServlet extends GenericServlet {  
  
    private HashMap<String, Object> _sym = new HashMap<String, Object>();  
  
    public HashMap sym() {  
        return _sym;  
    }  
  
    public void add(String sym, Object fn) {  
        _sym.put(sym.toLowerCase(), fn);  
    }  
  
    public void init() throws ServletException {  
        ServletConfig config = getServletConfig();  
        if (config == null) return;  
        try {  
            String handler = config.getInitParameter("handler");  
            if (handler != null) {  
                ServletContext sc = config.getServletContext();  
                InputStream stream = sc.getResourceAsStream(handler);  
                initialize(handler, read(stream));  
                stream.close();  
            } else  
                System.out.println("No handler");  
        } catch (Exception e) {  
            System.out.println("During ScriptServlet.init(): ");  
            e.printStackTrace();  
        }  
    }  
  
    public abstract void initialize(String handler, Object code) throws Exception;  
  
    public abstract void eval(Object fn, HttpServletRequest request, HttpServletResponse response);  

    public void service(HttpServletRequest request,  HttpServletResponse response)  
        throws IOException, ServletException {  
        service((HttpServletRequest)request, (HttpServletResponse)response);  
    }  
  
    public void service(HttpServletRequest request,  HttpServletResponse response)  
        throws IOException, ServletException {  
        // do we have the named method?  
        if (sym().containsKey(request.getMethod().toLowerCase()))  
            eval(sym().get(request.getMethod().toLowerCase()), request, response);  
        // or are we atleast overriding the service?  
        if (sym().containsKey("service"))  
            eval(sym().get("service"), request, response);  
        else  
            super.service(request, response);  
    }  
  
    public void destroy() {  
        if (sym().containsKey("destroy"))  
            eval(sym().get("destroy"), null, null);  
        else  
            super.destroy();  
    }  
  
    // Library functions that may be faster(performance) to do in java  
    // than in our client languages.  
  
    private static Hashtable<String, Object> _cache = new Hashtable<String, Object>();  
    public static Hashtable<String, Object> cache() {  
        return _cache;  
    }  
    // read all in a file and return.  
    // If required, the client program can override this method to supply compiled  
    // code  
    public Object read(String name)  
        throws IOException {  
        if (_cache.containsKey(name))  
            return (String)_cache.get(name);  
        Object val = read(new FileInputStream(name));  
        _cache.put(name, val);  
        return val;  
    }  
  
    public Object read(InputStream in)  
        throws IOException {  
        StringBuffer sb = new StringBuffer();  
        String line = null;  
        DataInputStream ds = new DataInputStream(in);  
        while ((line = ds.readLine()) != null) {  
            sb.append(line);  
            sb.append("\\n");  
        }  
        return sb.toString();  
    }  
}  
  
```

 

The only portion that a language specific wrapper servlet that inherits from us  need to implement is the script evaluation.The  
custom servlet delegates the responsibility of actual implementation of HTTP method processors to the script that gets loaded.  
Which is responsible for adding the relevant entries to our symbol table. The HTTP methods are serviced only if they are  
present in our symbol table.  

An example language specific servlet for 'Foo' language:

 

```
package com.sun.servlet;  
  
import java.io.*;  
import javax.servlet.http.*;  
import foo.*;  
  
  
public class FooServlet extends ScriptServlet {  
  
    public static Foo foo = new Foo();  

    // the handler contains the script name, and the code contains the entire script as string  
    public void initialize(String handler, Object code)  
        throws Exception {  
        foo.eval(code, foo.bind("httpservlet", this));  
    }  
  
    public void eval(Object fn, HttpServletRequest request, HttpServletResponse response) {  
        try {  
            if (request == null)  
                foo.eval(fn);  
            else  
                foo.eval(fn, new Object[]{request, response});  
        } catch (Exception e) {  
            e.printStackTrace();  
        }  
    }  
}  
```
  

The meta info contained in web.xml and sun-web.xml will look like this  

**sun-web.xml**  
 

 

```
<?xml version="1.0" encoding="UTF-8"?>  
  
<!--  
 Copyright 2006 Sun Microsystems, Inc. All rights reserved.  
 Use is subject to license terms.  
-->  
  
  
<!DOCTYPE sun-web-app PUBLIC "-//Sun Microsystems, Inc.//DTD Application Server 8.1 Servlet 2.4//EN"  
"http://www.sun.com/software/sunone/appserver/dtds/sun-web-app_2_4-1.dtd">  
  
<sun-web-app>  
  <session-config>  
    <session-manager/>  
  </session-config>  
  <jsp-config/>  
</sun-web-app>  
```
  

 **web.xml**

 

```
<?xml version="1.0" encoding="ISO-8859-1"?>  
<!DOCTYPE web-app PUBLIC "-//Sun Microsystems, Inc.//DTD Web Application 2.3//EN" "http://java.sun.com/j2ee/dtds/web-app_2.3.dtd">  
<web-app>  
    <servlet>  
        <servlet-name>handler</servlet-name>  
        <servlet-class>com.sun.servlet.FooServlet</servlet-class>  
        <init-param><param-name>handler</param-name><param-value>/WEB-INF/code/foo.f</param-value></init-param>  
    </servlet>  
  
    <servlet-mapping>  
        <servlet-name>handler</servlet-name><url-pattern>*.f</url-pattern>  
    </servlet-mapping>  
</web-app>  
```
  
  
  

 

 

As you can see in the web.xml, we pass in the main servlet handling script to the custom servlet using the  
parameter **handler**. The custom servlet reads the handler code in and evaluates it. The handler script is  
responsible for registering the doGet and doPost methods in the ScriptServlet symbol table. The handler  
script will normally extract the script name that is referenced in the URI of the request, and will load and  
evaluate the particular script, returning the result to the browser through response.  

 A pseudo script for foo is given below.  

** docroot/WEB-INF/code/foo.f**

 

```
function doGet(request,response)  
    spath := request.getServletpath  
    fname := httpservlet.getServletConfig.getServletContext.getRealpath(spath)  
    body  := httpservlet.read(fname)  
    out   := response.getWriter  
    response.setContentType 'text/html'  
    out.prontln eval(body)  
end  
  
httpservlet.add 'get' doGet  
# use the same method for post  
httpservlet.add 'post' doGet  
```
  
  
  

**docroot/hello.f**

 

 

  
  
```
println 'This will come in the servlet error log'  
return 'and this will come in the browser window.'  
```
  

The URL for accessing the script will be http://yourserver:port/foo/hello.f assuming  
that you deployed the webapp to /foo URL.  

Follow this series for examples of real languages.
