---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (SJSWS7.0 VII) Scripting with servlets [php - using quercus]
title: (SJSWS7.0 VII) Scripting with servlets [php - using quercus]
---

**Hack Warning**

     The steps described below are plainly a simple hack to get the Quercus implementation of 
php working with Sun's WebServer 7.0. This will get you started and gives only the base language.
I have not tested any of the libraries and do not expect any of them to work. The hack involves
removing the dependency of Resin server from the distributed open-sourced Quercus codebase.

#### More info: 

For a detailed treatment of running the **Native** php on Sun Java System see Joe's [article](http://developers.sun.com/prodtech/webserver/reference/techart/php2.html). The difference
here is that we use the [Quercus](http://www.caucho.com/resin-3.0/quercus/) implementation of php over jvm provided by [Caucho](http://www.caucho.com/).
We use Quercus implementation distributed with the Resin 3.0 which was opensourced by Caucho.

Unlike the previous installments of this series, This entry does not make use of the ScriptingServlet or the Scripting
interface of jdk6. I have tried to make use of the servlet (slightly modified) that allows Quercus to run on Resin, and
have modified it slightly to run on Sun Java System WebServer 7.0.

More over, I have added the diffs required to get Quercus to work in Sun Java System WebServer [here](http://blogs.sun.com/blue/resource/servlets/resin.patch). It should
help any one else who are interested. (note that all the lines that states 'Only in' are the directories that were removed
from the original Caucho distribution)

#### About the language

The php is a powerful server-side templating language. It is widely used and is an alternative to technologies
like ASP, JSP etc. The strength of php is that it is easy to use and its syntax is closely related to Perl and C.

Steps involved for the Users.

1. Download the [quercus-webapp.tar.gz](http://blogs.sun.com/blue/resource/servlets/quercus-webapp.tar.gz)
2. Extract it to the **samples/java/webapps/quercus** directory in your installation. (same as previous entries)
3. Download the below jars and put them inside **samples/java/webapps/quercus/docroot/WEB-INF/lib**

* [amber-resin.jar](http://blogs.sun.com/blue/resource/php-jars/amber-resin.jar)  
* [ejb-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/ejb-resin.jar) 
* [javax-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/javax-resin.jar) 
* [lib-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/lib-resin.jar) 
* [main-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/main-resin.jar) 
* [parser-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/parser-resin.jar) 
* [server-resin.jar](http://rahul.gopinath.org/sunblog/2007/01/blue/resource/php-jars/server-resin.jar) 

Compile the PhpServlet by invoking Ant from your quercus/src directory. 

- (This will create quercus-webapp.war in your quercus directory)

Deploy it by invoking the deploy.tcl in your quercus directory.

```bash
wadm  -u admin -f deploy.tcl
```

The directory should look like the following after the jars are downloaded.


```bash
> cd quercus
> find .
.
./docs
./docs/index.html
./src
./src/build.xml
./src/HelloModule.java
./src/docroot
./src/docroot/WEB-INF
./src/docroot/WEB-INF/lib
./src/docroot/WEB-INF/lib/aopalliance.jar
./src/docroot/WEB-INF/lib/amber-resin.jar
./src/docroot/WEB-INF/lib/ejb-resin.jar
./src/docroot/WEB-INF/lib/javax-resin.jar
./src/docroot/WEB-INF/lib/lib-resin.jar
./src/docroot/WEB-INF/lib/main-resin.jar
./src/docroot/WEB-INF/lib/parser-resin.jar
./src/docroot/WEB-INF/lib/server-resin.jar
./src/docroot/WEB-INF/web.xml
./src/docroot/WEB-INF/sun-web.xml
./src/docroot/WEB-INF/classes
./src/docroot/WEB-INF/classes/META-INF
./src/docroot/WEB-INF/classes/META-INF/services
./src/docroot/WEB-INF/classes/META-INF/services/com.caucho.quercus.QuercusModule
./src/docroot/index.html
./src/docroot/hello.php
./src/PhpServlet.java
./resin.patch
./deploy.tcl
```

(There are multiple jar files only because the blogs.sun.com does not permit me to upload files more
than 3.0 MB at once.)

#### Callbacks to Java Land

 You might have noticed two interesting files in the previous listing..
`HelloModule.java` and `com.caucho.quercus.QuercusModule`

 

The **HelloModule.java** contains a simple implementation of a php function. hello_test. (The class name does not matter.)

```java
package example;
import com.caucho.quercus.module.AbstractQuercusModule;

public class HelloModule extends AbstractQuercusModule {
    public String hello_test(String name) {
        return "at, " + (new java.util.Date()).toString() + " for " + name;
    }
}
```

And the **com.caucho.quercus.QuercusModule** contains a single string that tells the Quercus what class to load **example.HelloModule**

The **hello.php** file below invokes the php function we have thus defined.


```xml
<html>
<body>
<?php echo "Hello, "; ?>
<br/>
<?php echo hello_test("World"); ?>
<br/>
</body>
</html>
```

You will be able to invoke your application as http://yourserver:port/quercus/hello.php  once you have deployed the webapp.
