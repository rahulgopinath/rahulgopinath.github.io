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


<h3> Notable Past Projects </h3>

[PIT](http://pitest.org): As part of my research in mutation analysis, I have
contributed newer operators and other fixes for Pit. My empirical studies
suggest that these added operators are sufficient to bring mutation operator
feature parity between Pit and other academic mutation analysis frameworks.

[Apache HTTPD](https://httpd.apache.org): I contributed patches to the Apache
Httpd project, which includes contributions for mod_proxy, and HTTPD core.
I have also implemented a small apache module [mod-scheme](https://github.com/vrthra/mod-scheme), a
Scheme language plugin for Apache HTTPD.


[Puppet](https://github.com/puppetlabs/puppet),[Factor](https://github.com/puppetlabs/facter):
As an intern at Puppet Labs, I contributed extensively towards Puppet and
Factor, and provided the first Solaris IPS package release for puppet
and Factor. I was also involved extensively with implementing native factor
functionalities for Solaris 10 and Solaris 11.

[Rubocop](http://batsov.com/rubocop/): Rubocop is a Ruby static code analyzer.
I contributed fixes to Rubocop as part of my internship, which included
studying the feasibility of applying Rubocop to the Puppet codebase.

[Syx](http://github.com/vrthra/syx) Syx was a command line smalltalk originally
hosted at [googlecode](http://code.google.com/p/syx).  I contributed the
XWindows API, and also a small window manager in smalltalk for Syx.

[openstack-mellanox-cookbook](https://github.com/osuosl-cookbooks/cookbook-openstack-mellanox): I was
one of the authors of the initial prototype of IBM Mellanox Chef Cookbook for OpenStack.



<h3>Other Notable but Small Projects </h3>

[v-language](https://github.com/vrthra/v-language) is a simple stack based
language that is very similar to Postscript and Forth. I wrote this to
understand concatenative programming. I later rewrote [V in Haskell](https://github.com/vrthra/v)

[bibprolog](https://github.com/vrthra/bibprolog) is a simple swi-prolog based
command line tool to query bibtex databases. It uses simple terminal based
colouring to indicate relevant parts of bibtex entries queried.

[tdlogic](https://github.com/vrthra/tdlogic) is another swi-prolog based
command line todo list manager. As with bibprolog, tdlogic also uses terminal
colouring to indicate priorities and tags.

[qbugs](https://github.com/vrthra/qbugs) is a simple command line interface
written in Java to query Bugster, which was used in Sun Microsystems. Bugster
was a Java swing application that had a horrible user interface. Qbugs had
auto-completion, filtering, piping, and other conveniences.

[trans](https://github.com/vrthra/trans) is a simple command line interface
written in Java to query Bugster, which was used in Sun Microsystems. Bugster
was a Java swing application that had a horrible user interface. Qbugs had
auto-completion, filtering, piping, and other conveniences.

I have also written a few small ruby daemons that are reasonably feature
complete in terms of the protocols they implement: [ircd](https://github.com/vrthra/ruby-ircd) [nntpd](https://github.com/vrthra/ruby-nntpd) [imapd](https://github.com/vrthra/ruby-imapd).
These were written to help with [ruby-hive](https://github.com/vrthra/ruby-hive) which I
wrote to orchestrate the testing process in multiple machines. It was
especially useful for testing the cache protocol implementations CARP, ICP, and
also SOCKS, and FTP proxies.

