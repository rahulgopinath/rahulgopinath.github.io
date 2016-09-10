---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: A simple extension to the hg (mercurial) forest (fdiff fcommit and fimport)
title: A simple extension to the hg (mercurial) forest (fdiff fcommit and fimport)
---

For Sun WebStack, I have been working with multiple repositories (apache2, squid, mysql5, lighttpd etc). I often have to do the same or related changes in each of these repositories.The standard commands that I had to use to work with these repos are,

* Fetch the sources for all repos [ `for i in $mylist; do hg clone ssh://webstack-root/$i ; done `]
* Fix some stuff and verify by doing a diff [ `for i in *; do [ -d $i/.hg ] && (cd $i && hg diff ); done`]
* Commit the fixes [ `for i in * ; do [ -d $i/.hg ] && (cd $i && hg commit -m "my message" ) ; done`]
* And push the same way. [ `for i in * ; do [ -d $i/.hg ] && (cd $i && hg push) ; done`]

Quite recently I found the [forest](http://www.selenic.com/mercurial/wiki/index.cgi/ForestExtension) extension which allowed me to do  

On top dir in the server  

```
$ hg init  
```

On the client systems, clone, push and pull  

```
$ hg fclone ssh://webstack-root  
$ hg fpull  
$ hg up
$ hg fpush  
```

These were very helpful, but I also wanted to review the diffs (and to request for review) and to commit related changes with the same aggregated commit message, Unfortunately the forest extension does not yet have commands for these.

I have modified the forest extension slightly to provide for new commands `fdiff`, `fcommit` and `fimport`. The source is [here](/blue/resource/forest.py). In case you have the same need, drop this into your hgext directory (replace the forest.py if it exists) or set the extension path in your `.hgrc`

*Beware that this is nothing more than a hack though.*

