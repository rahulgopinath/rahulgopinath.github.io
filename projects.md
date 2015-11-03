---
layout: page
title : Projects
header : Projects
group: navigation
weight: 3
menu: Publications
---
<h3> Current Projects </h3>

[MuCheck](https://hackage.haskell.org/package/MuCheck): MuCheck is a mutation
analysis framework for Haskell. We investigated the different fault patterns
that occur in Haskell, and implemented these as mutation operators. I was one
of the authors for MuCheck. MuCheck originally implemented only QuickCheck and
HUnit extensions. These were further extended by me to cover HUnit and SmallCheck.
I also implemented the distributed extensions to
MuCheck that takes advantage of Cloud-Haskell for parallelization.

[TreeT](https://hackage.haskell.org/package/TreeT),[LTree](https://hackage.haskell.org/package/LTree): These are small
monad transformers for simple tree data structures in Haskell, written
exclusively to check my understanding of monad transformers.
My complete list of Haskell projects including extensions to MuCheck is
available at [Hackage](https://hackage.haskell.org/user/RahulGopinath)

[XMutant](https://pypi.python.org/pypi/xmutant): XMutant is a simple mutation
analysis framework for Python that uses bytecode manipulation to mutate
programs. It implements a simple sampling based equivalent mutant analysis,
with some cleverness such as reservoir sampling to avoid having to generate the
entire set of mutants before sampling. This does not have other authors.


<h3> Notable Past Projects (Open Source) </h3>

[PIT](http://pitest.org): As part of my research in mutation analysis, I have
contributed newer operators and other fixes for Pit. My empirical studies
suggest that these added operators are sufficient to bring mutation operator
feature parity between Pit and other academic mutation analysis frameworks.

[Apache HTTPD](https://httpd.apache.org): I contributed patches to the Apache
Httpd project, which includes contributions for mod_proxy, and HTTPD core.
I have also implemented a small Apache module [mod-scheme](https://github.com/vrthra/mod-scheme), a
Scheme language plugin for Apache HTTPD.


[Puppet](https://github.com/puppetlabs/puppet),[Factor](https://github.com/puppetlabs/facter):
As an intern at Puppet Labs, I contributed extensively towards Puppet and
Factor, and provided the first Solaris IPS package release for puppet
and Factor. I was also involved extensively with implementing native factor
functionalities for Solaris 10 and Solaris 11.

[Rubocop](http://batsov.com/rubocop/): Rubocop is a Ruby static code analyzer.
I contributed fixes to Rubocop as part of my internship, which included
studying the feasibility of applying Rubocop to the Puppet codebase.

[Syx](http://github.com/vrthra/syx) Syx was a command line Smalltalk originally
hosted at [googlecode](http://code.google.com/p/syx).  I contributed the
XWindows API, and also a small window manager in Smalltalk for Syx.

[openstack-mellanox-cookbook](https://github.com/osuosl-cookbooks/cookbook-openstack-mellanox): I was
one of the authors of the initial prototype of IBM Mellanox Chef Cookbook for OpenStack.



<h3>Other Notable but Small Projects </h3>

[v-language](https://github.com/vrthra/v-language) is a simple stack based
language that is very similar to Postscript and Forth. I wrote this to
understand concatenative programming. Originally written in Java, it provides
a simple MOP and word invocation through pattern matches. The rewrite in C also
provides a simple reference counting GC. I later rewrote [V in Haskell](https://github.com/vrthra/v)

[bibprolog](https://github.com/vrthra/bibprolog) is a simple SWI-Prolog based
command line tool to query Bibtex databases. It uses simple terminal based
coloring to indicate relevant parts of Bibtex entries queried.

[tdlogic](https://github.com/vrthra/tdlogic) is another GNU-Prolog based
command line todo list manager. As with bibprolog, tdlogic also uses terminal
coloring to indicate priorities and tags.

[qbugs](https://github.com/vrthra/qbugs) is a simple command line interface
written in Java to query Bugster, which was used in Sun Microsystems. Bugster
was a Java swing application that had a horrible user interface. Qbugs had
auto-completion, filtering, piping, and other conveniences.

[trans](https://github.com/vrthra/trans) is a tiny little TCP proxy that can
be used to debug TCP connections. I wrote it to help me with my proxy work.

I have also written a few small ruby daemons that are reasonably feature
complete in terms of the protocols they implement: [ircd](https://github.com/vrthra/ruby-ircd) [nntpd](https://github.com/vrthra/ruby-nntpd) [imapd](https://github.com/vrthra/ruby-imapd).
These were written to help with [ruby-hive](https://github.com/vrthra/ruby-hive)
([docs](https://code.google.com/p/ruby-hive/)) which I
wrote to help with distributed testing.

[ruby-hive](https://code.google.com/p/ruby-hive/) A framework for machine orchestration
that I wrote to orchestrate the testing process in multiple machines. It was
especially useful for testing the cache protocol implementations CARP, ICP, and
also SOCKS, and FTP proxies.

[ps-fun](https://github.com/vrthra/trans) A concatenative and functional
library for the postscript language.

<h3>Interesting projects (Non Opensource)</h3>


<h4>2009 Sun Microsystems</h4>
Cat, Pat, Net, Hive: Implemented the testing frameworks affectionately called
Cat, Pat and Net for the iPlanet family web and proxy servers. The Cat
framework was written to test the wadm command line framework, which had two
modes: stand alone, and TCL (Jacl) scripting. Consequently Cat was implemented
in both Perl, and TCL (Jacl),
exposing similar functionalities. It allowed a testing engineer to specify the
particular command line, and the pattern of output expected as a regular
expression based on the parameters given in the corresponding command line.
Pat framework was written in Ruby, and was used to test the iPlanet proxy
server. It consisted of a program with two threads, one thread the server, and
the other client, and they communicated to each other through the proxy, and
verified that the responses from proxy, and the caching subsystem was as
specified in the HTTP 2616 RFC. The Net library was written in Perl, and was a
rewrite of CAT to allow it to test the protocol portion of the iPlanet
webserver itself using similar request-response style test cases. Finally,
since testing often involved specific machines due to licensing issues of GUI
testing tools, and also because of the different operating systems, and network
components such as webserver, proxy, and load balancers, I implemented
[Hive](https://github.com/vrthra/ruby-hive), an orchestration framework for
servers. It allowed IRC based co-ordination of different servers with automated
triggering of test runs corresponding to external events, reporting of test run
results etc.

[Webstack](https://bitbucket.org/webstack/) was the other very interesting project.
The aim was to develop a relocatable packaging of opensource projects (using IPS) such as
Apache, Squid, Ruby, Python, Perl etc. that a user could install in their home directory
and move the location around if required after installation. The entire set of projects
were pre-configured to work in specific ways. The interesting part was how to get the
components work from different directories than the developers assumed, and how to let
the programs find their configuration files and libraries. It involved figuring out the
linking and loading mechanisms of binaries, and figuring out how different opensource
projects managed their components and configurations. The other interesting part that
I was involved in was to actually create and maintain the packaging framework using
makefiles, managing dependencies and making sure that we can do parallel and distributed
builds of components.

[OpenSolaris](https://en.wikipedia.org/wiki/OpenSolaris): I was the maintainer of Apache
modules and Squid proxy server for OpenSolaris distribution, and it involved working with
the Architectural Review Committees to ensure that the opensource components followed
the Sun interface guidelines.

<h4>2005 Quark Media House</h4>
Administration Interface using JScheme: While at Quark, implemented a simple
administration interface for QWAF (Quark Web Application Framework) as
a personal project at learning Scheme language. It was sufficiently successful
to be included in the product release.

<h4>2002 Suntec Business Solutions</h4>
Rating Appliance using OSKit: While at Suntec, prototyped a simple rating
appliance using [OSKit](https://www.cs.utah.edu/flux/oskit). The OSKit provided
all the underlying libraries to build the appliance as a kernel, running
directly on the machine. While the project never went beyond the prototype
stage, it could boot up, accept rating requests over TCP, and do minimal processing.

