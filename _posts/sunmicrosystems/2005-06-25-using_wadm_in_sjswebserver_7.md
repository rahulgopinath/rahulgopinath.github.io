---
layout: post
categories : blog
tagline: "."
tags : [sunmicrosystems blog sun]
categories : sunblog
e: (wadm I) Using wadm in  Sun Java System Web Server 7.0
title: Using wadm in SJSWebServer 7
---

As you may have noticed, the Sun Java System Web Server 7.0 came out with a revamped command-line interface that incorporates a scripting
framework.
This scripting framework is based on JACL a java-vm implementation of the TCL language. During the start of 7.0 effort, multiple
languages were evaluated to provide the scripting solution that we wanted. The Application server even had their own home grown
solution called asadmin that provided a very skeletal interface to command invocation (I wouldn't call that a language yet.)
We were looking for the following features so as to make the use of our scripting interface painless for the users.

### Our needs...

* We needed to provide the same kind of interface both as stand-alone command line and also asexposed to scripting with in the language environment. This meant that the language needed to be as close to the shell scripting syntax as possible. This was high priority also because we recognized that most of our customers were sysadmins who will be more familiar with the shell scripting environment than with any other language.
* Most of our enterprise customers have home-grown solutions that rely on configuration files and shell scripts to achieve large scale clustering. Attention was paid to the mouldability of the language to emulate these systems so that the barrier of entry would be low for our scripting framework.
* We needed a powerful system that ran on top of JVM, (did not have the resources to create or adapt any new language to the jvm platform)
* A system that would allow us to hammer out simple scripts for simple tasks, and also keep its cool on complex tasks was felt to be the need of the hour (especially because our largest customers had to write very complex solutions to maintain their farms) We also wanted to support only a single language since having multiple languages would fragment the users and the community using the wadm. We evaluated the following based on these guiding principles.

### Languages we looked at

* scheme (jscheme)
* python (jython)
* ruby (jruby)
* perl
* shell (various _sh)
* asadmin
* groovy
* beanshell
* javascript (rhino)

The first one we looked at was **asadmin**, one because we had lots of in-house expertise on it, and second, it was already being used in
one of the sister products. Sadly it fell far short of most of the requirements.

The various shells like **bash,zsh,ksh,csh** started out as favorites because they had the shell syntax (well, they are the shells). but did not
make it due to the unavailability of a jvm implementation.

The same was true of **perl**.

**python** was a hot favorite of AppServer folks but did not make the grade because it made exchange of simple scripts needlessly difficult
(the indentations have a way of getting lost when you copy/paste your scripts to or from emails or web pages). Its strict philosophy was
also a slight turn off.

**groovy** was very interesting since it took the pain out of using the java libraries but that very same feature worked against it. While it may
be very comfortable to pick up for developers who are used to the java syntax and API, we were not very sure that the sysadmins were
going to do like it. If possible we wanted to hide the jvm underneath at least for common tasks.

The same was true of **beanshell** too.

The **javascript** offered a better perspective compared to the above two. It also had the advantage that we were associated with the
early javascript implementation (when it was the Mocha) and later we had even carried it as a server side scripting solution. It had a
'discover the features as you use' feel to it. It was obviously well suited for doing smaller scripts. Looking at its large scale features to
manage complexity,
 It had a very open prototype based inheritance which was much easier to use than many other languages, Allowed
all the features of dynamic languages including redefining the methods and classes at run time, It is very clean, and easy to maintain.
 It even allows continuations to be stored and used. JavaScript was in consideration until the last moment, and so was Ruby.

Looking at **ruby**, There are immediate benefits arising out of its support of open classes just like javascript, and interesting abstractions
like co-routines, interesting uses of objects and iterators, mixins etc.
 It also has a very clean and consistent syntax. Stitching up small languages for use in configurations and other server farm administration
tasks are also pretty easy in this ruby. ****

jscheme was also ruled out as it was markedly different from the shell/perl world that our end users are in currently.

Then we evaluated **jacl** (TCL), some of the things that we immediately attracted us were,

* It had the closest to the shell syntax that we can find on top of a jvm.
* Language with the fewest number of rules (right there with scheme) It has a simple primitive, the command. no special cases anywhere, and another simple data structure the list.
* Very high redesign capabilities (You can create your own language with it) Macros if you need them, create your own primitives, redefine syntax etc.
* Interesting and few primitives (even lower than scheme) means you can pick it up in half an hour.
* max late binding to be found anywhere.
* Availability of an existing vm based language so that we can utilize java api's in a pinch.
* an existing event driven model that may come in handy
* clean code with consistent interface.

While comparing with the rest of the finalist languages, Ruby and JavaScript, The negatives with TCL (as far as we were concerned) were:

* Richness of syntax.
Ruby has a much richer syntax than either JavaScript or TCL, though we were not sure if it should be considered a virtue for the audience we were targeting.
* No built in OO, but this could be rectified the same way it is done in CommonLisp/Scheme if necessary, since the language allows itself to be extended quite heavily (incrTcl being an example).
* Absence of interesting things like closures, continuations etc. (These cant be done in tcl even by extending it, while both ruby and javascript provided them)

Considering all the three, the main deficiency was 3, but considering other advantages, we decided to go for TCL
(or jacl - its jvm implementation.) the clinching argument was that the command lines would look exactly same in a stand alone
mode and within the jacl environment.
