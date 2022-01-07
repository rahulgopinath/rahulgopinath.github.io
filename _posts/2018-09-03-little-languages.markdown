---
published: true
title: A tale of two little languages -- an engineering story
layout: post
comments: true
tags: sun
categories: post
---

This particular post was prompted by reading two papers. One, [a programming Perl by Bentley](http://staff.um.edu.mt/afra1/seminar/little-languages.pdf) which recommends writing independent programs that accept their own little languages, and another by [Shivers](https://3e8.org/pub/scheme/doc/Universal%20Scripting%20Framework%20(Lambda%20as%20little%20language).pdf) which suggests that independent little languages are flawed, and one should instead go for embedding them in a larger general purpose language. What follows is my experience in designing and developing two different languages, in different styles.

## CAT

In an earlier incarnation, I was an engineer at Sun Microsystems (before the Oracle takeover). I worked on the [iPlanet](https://en.wikipedia.org/wiki/IPlanet) line of web and proxy servers, and among other things, I implemented the command line administration environment for these servers called [wadm](https://docs.oracle.com/cd/E19146-01/821-1837/help-1/index.html).

This was a customized _TCL_ environment based on [Jacl](http://tcljava.sourceforge.net/docs/website/index.html). We chose Jacl as the base after [careful study](/sunblog/blog/2005/06/25/using_wadm_in_sjswebserver_7/), which looked at both where it was going to be used most (as an interactive shell environment), as well as its ease of extension. I prefer to think of _wadm_ as its own little language above _TCL_ because it had a small set of rules beyond _TCL_ such as the ability to infer right options based on the current environment that made life a bit more simpler for administrators.

At [Sun](https://en.wikipedia.org/wiki/Sun_Microsystems), we had a very strong culture of testing, with a dedicated QA team that we worked closely with. Their expertise was in the domain of web and proxy servers more than programming. For testing _wadm_, I worked with the QA engineers to capture their knowledge as test cases (and to convert existing ad-hoc tests).

When I looked at existing shell scripts, it struck me that most of the testing was simply invoke a command line and verify the output. Written out as a shell script, these may look ugly for a programmer because the scripts are often flat, with little loops or other abstractions. However, I have since come to regard them as a better style for the domain they are in. Unlike in general programming, for testing, one needs to make the tests as simple as possible, and loops and subroutines often make simple stuff more complicated than it is. Further, tests once written are almost never reused (as in, as part of a larger test case), but only rerun. Further, what we needed was a simple way to verify the output of commands based on some patterns, the return codes, and simple behavior such as response to specific requests, and contents of a few administration files. So, we created a testing tool called _CAT_ (command line automation tool) that essentially provided a simple way to run a command line and verify its result. This was very similar to [expect](https://core.tcl.tk/expect/index). It looked like this

```bash
wadm> list-webapps --user=admin --port=[ADMIN_PORT] --password-file=admin.passwd --no-ssl
/web-admin/
/localhost/
=0

wadm> add-webapp --user=admin --port=[ADMIN_PORT] --password-file=admin.passwd --config=[HOSTNAME] --vs=[VIRTUAL_SERVER] --uri=[URI_PATH]
=0
```

Each line that started with `wadm>` represented a command invocation, with the given parameters. The square brackets on command invocation such as `[HOSTNAME]` represented variables that were passed in from the command line. This was the same format we used in our documentation system. The next lines specified how to match the output of the command. If a line was `=<number>`, then the `<number>` was taken to be the return value, which was [designed](https://docs.oracle.com/cd/E19146-01/821-1837/help-1/index.html#Exit%20Codes) to provide maximum information to the user about any error without having to parse the output. If a matching line started and ended with slashes (`/.../`) it was treated as a regular expression match, and a line wrapped in quotes (`"..."`) meant exact string match.
Wadm had two modes – standalone, and as a script (other than the REPL). For the script mode, the file containing wadm commands was simply interpreted as a _TCL_ script by _wadm_ interpreter when passed as a file input to the _wadm_ command. For standalone mode, the _wadm_ command accepted a sub-command of the form `wadm list-webapps --user=admin ...`. which can be executed directly on the _UNIX shell_. The return codes (=0) are present only in stand alone mode, and do not exist in TCL mode where exceptions were used.

With the test cases written in _CAT_, we could make it spit out either a _TCL_ script containing the _wadm_ commands, or a shell-script containing standalone commands -- It could also directly interpret the language which was its most common mode of operation. The advantage of doing it this way was that it provided the QA engineers with domain knowledge an easy environment to function. The _CAT_ scripts were simple to read and maintain. They were static, and eschewed complexities such as loops, changing variable values, etc, and could handle about 80% of the testing scenarios we looked at. For the 80% of the remaining 20%, we provided simple loops and loop variables as a pre-processor step. If the features of _CAT_ were insufficient, engineers were welcome to write their test cases in any of Perl, TCL, or UNIX shell. The scripts spat out by _CAT_ were easy to check and were often used as recipes for accomplishing particular tasks by other engineers. All this was designed and implemented in consultation with QA Engineers with their active input on what was important, and what was confusing.

I would say that we had these stages in the end:

* The preprocessor that provides loops and loop variables.
* _CAT_ that provided command invocation and verification.
* _wadm_ that provided a custom TCL+ environment.
* wadm used the JMX framework to call into the webserver admin instance. The admin instance also exposed a web interface for administration.

We could instead have done the entire testing of web server by just implementing the whole testing in _Java_. While it may have been possible, I believe that splitting it out to stages, each with its own little language was better than such a step. Further, I think that keeping the little language _cat_ simple (without subroutines, scopes etc) helped in keeping the scripts simple and understandable with little cognitive overhead by its intended users.

Of course, each stage had existence on its own, and had independent consumers. But I would say that the consumers at each stage could chosen to have used any of the more expressive languages above them, and chose not to.

## PAT

I also implemented several functionalities in the iPlanet HTTP proxy server, and needed a way to verify the proxy server functionalities, especially its caching features (which also included distributed caching protocols -- ICP and CARP). Taking inspiration from the success of _CAT_, I wrote another tool called _PAT_ (proxy automation) which I used to add test cases for proxy server features. Unlike with _CAT_, I decided to write the tool in _Ruby_ as a DSL embedded in ruby. The test suites looked like this

### Driver

```
#connect.pat

cr 0
title 'generic connect' 

info 'Connect method tests starting'

server.start 

send %q[
CONNECT #{@options.server_host_port} HTTP/1.0 

] 
match line=/^\r\n$/, %q[ 
HTTP/1.1 200 OK 
Server: Sun-Java-System-Web-Proxy-Server/4.0 
/Date: .*/ 
Connection: close 

] 
#now upgrade to ssl 
info "Upgrading to SSL" 
take SSLProxyClientConn,conn 

send %q[ 
GET /index.html HTTP/1.0 

] 

#it is being sent by us so no CRLF 
match line=/^$/, %q[ 
HTTP/1.0 200 OK 
Server: PAT/1.0 
Content-type: text/html 

] 

match line=/^$/, strict=true, seq=true, %q[
<html> 
     <head> 
          <title>Phoenix</title> 
     </head> 
     <body>
         Hello
     </body>
</html> 
] 

server.stop 
match %q[ 
/success/ 
]
```

### Server

```
#server/connect.pat

cr 0
title 'generic connect'
info "binding on: #{opt.server_port}"
take SSLServerConn,opt.server_port

match line=/^$/, [
/GET \/index\.html HTTP\/1.0/

]

send %q[
HTTP/1.0 200 OK
Server: PAT/1.0
Content-type: text/html

<html> 
     <head> 
          <title>Phoenix</title> 
     </head> 
     <body>
         Hello
     </body>
</html>

]

```

This is a tiny script to test the "CONNECT" method. I think that the API has enough conveniences over Ruby to qualify as a DSL. The run was started by executing the driver part. Each driver script started with declaring what ticket number it was supposed to test, and what the test was about. Then it started up the corresponding server script that bound to a specified socket. Once the server started up, the driver sent it requests through the proxy server, and verified the behavior at both server and driver.

As you can see, the script is just another ruby script, and the host language is always at hand.

The unfortunate problem here was that, it required enormous discipline to stick to the DSL. There was always the temptation to refactor, or identify common strings or common procedures. In the end, people just wrote ruby scripts rather than use the DSL, and these scripts were too complex unlike the _CAT_ scripts, and the tool did not survive for long.

To summarize, my experience has been that the most underappreciated aspect of little languages has been the discipline that they impose -- _what they will not let you do_. It also lets you focus on particular layers of the problem without getting distracted. When the little language used is sufficiently independent of the remaining layers, the results have been useful and very much maintainable. On the other hand, when the separation imposed from other layers was insufficient, the results were not very worthwhile.

Hence, my experience has been that, programs written in the fashion prescribed by Shivers often end up much less readable than little languages with pipe line stages approach.
