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


<h3> Past Projects </h3>

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
and Factor.

[Rubocop](http://batsov.com/rubocop/): Rubocop is a Ruby static code analyzer.
I contributed fixes to Rubocop as part of my internship, which included
studying the feasibility of applying Rubocop to the Puppet codebase.

Author of [openstack-mellanox-cookbook](https://github.com/osuosl-cookbooks/cookbook-openstack-mellanox) (prototype) - IBM Mellanox Chef Cookbook for OpenStack

I have also written a few small ruby daemons that are reasonably feature
complete in terms of the protocols they implement [ircd](https://github.com/vrthra/ruby-ircd) [nntpd](https://github.com/vrthra/ruby-nntpd) [imapd](https://github.com/vrthra/ruby-imapd).

