---
published: true
title: Solaris 11 IPS Packages for Puppet Facter and Hiera
layout: post
tags: [puppet]
categories : post
---
Experimental Solaris 11 IPS packages for Puppet 
3.0.0-rc7, Facter 1.6.12 and Hiera 1.0.0 are available under 

http://downloads.puppetlabs.com/solaris 

They are: 

```
puppet@3.0.0,5.11-9211.p5p 
facter@1.6.12,5.11-819.p5p 
hiera@1.0.0,5.11-116.p5p 
```

The versioning scheme for Solaris is different from the default 
scheme.  The versioning scheme is 

```
<product>@<product-version>,<consolidation>-<build number> . 
```

Specifically the RC candidates and 
the Final version are distinguished only by their build number which 
is monotonic. 

To install these packages, download them from the above link and use 
IPS pkg command. E.g for puppet 

```
pkg install -g ./puppet@3.0.0,5.11-9211.p5p puppet 
```

Note that since this is experimental and each product is in its own 
repository archive, Hiera and Factor need to be installed first before 
Puppet is installed.

