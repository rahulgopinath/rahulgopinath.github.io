---
layout: post
tagline: "."
tags : [sunmicrosystems blog sun]
categories : sunblog
e: The Proxy side
title: The Proxy side
---

There is a lot of debate happening in the proxy server community over which features are a must have in a Proxy Server. Quite a lot of [bad blood](http://seankelly.tv/blog/blogentry.2007-03-02.4768602564) seems to be because of a misunderstanding. The common naming used to denote Servers that address radically different segments of the internet architecture is the culprit.

The various segments that lay claim to the proxy in their name are Reverse Proxies, Forward Proxies, and Personal Proxies, (and Filtering Proxies). While most proxies can function as any of the above, They specialize in only one because of the trade offs and choices involved (explained below).  

Another confusion that is around is that a proxy is same as a **Firewall**. This is incorrect. A firewall usually operates below the network actively refusing connections. A proxy server is just one of the applications that are allowed communication with the outside world. Some vendors bundle a proxy server by default with a firewall and call it a single product, but that does not make a firewall a proxy server or vice versa.

While Forward and Personal Proxies are commonly used to filter content reaching the internal sites, it is done only because a proxy is generally one of the points of entry for outside content (The others being Mail protocols, VPN etc). Filtering is not the primary purpose of a Forward Proxy, but is commonly used for this purpose. (if it was, then SOCKS and SSL connections does not make much sense, nor does the HTTP RFC 2616 talk about filtering)  Filtering Proxies can be considered a sub-domain of the forward and personal proxies.  

The  Reverse Proxies and Forward Proxies are fundamentally different in their approaches towards most of the things. They operate near different ends of connection and their requirements are different. To avoid the confusion further, I will use the term **Load Balancer** for Reverse Proxies and **Proxy Server** for a Forward Proxy from here on. (edit: RFC 3040 uses the term surrogates for an server that acts like an origin server thus a Load Balancer is a **surrogate**.)  
  

## The trade offs and choices involved between the main segments

- Concurrent Connections 

A **Load balancer** is generally the single entry point to a cluster of Web Servers and as such is the server which has to handle the maximum number of concurrent requests.  
For a **Proxy Server**, the number of simultaneous connections are not that important. If the users are going through a switch, (usually) there will be separate intercepting proxies for different switches. It means that the maximum number of connections will be restricted to the number of machines served by that switch. Even in the case of large organizations which employs Proxy Servers to allow traffic outside, Things like [ProxyAutoConfig](http://wp.netscape.com/eng/mozilla/2.0/relnotes/demo/proxy-live.html) files are used to distribute the connections among various proxies. The users are also provided with a pool of Proxy Servers to choose from in places where the user has to manually set the Proxy in their browsers.  
  

### Caching Cache management and object eviction 

For a **Proxy Server**, caching is the most important functionality. It means that persistent cache (to disk) is mandatory and has to obey the HTTP RFC while doing so.  
For a **Load Balancer**, a persistent cache only makes sense if reading the cache from disk is faster than getting it over the network This may not be the case since Load balancers generally have high speed high bandwidth connections with the back end servers. The Load Balancers usually get away with caching in the RAM. The load balancer can even have understandings with the back end servers as to what kind of things it would cache. This need not even obey the RFC since this interaction is restricted to the small number of captive servers which are not exposed to the world.  

To put it simply, for a Load Balancer, **access times** are the highest priority and hence caching in the RAM is a must, with persistent cache coming as a bonus. And for a Proxy Server, **optimization of consumed bandwidth** is the primary concern, - Persistent cache is a must, with caching in the RAM serving as a bonus.  

For a **Load Balancer**, the important things about cache management is that it should be able to selectively cache responses from specific servers. It should also be able to ignore responses from others irrespective of content. (think of dynamic content application servers that may produce graphs and static look and feel servers serving GIFs and CSS). Generally the time an object is in cache is not important for load balancers. This is because the static contents in the cache are useful as long as the website retains the general look and feel. The administrator also takes an active control of the cache when the static contents change.  

A Proxy  Server on the other hand, needs management of size of cache, the number of cached objects, and more macro level adjustment on the amount of time particular content types are allowed to remain in the persistent cache.  

### Errant Servers and Heuristics  

An interesting aspect of  the **Proxy Servers** is that when they act as gateways for external servers like FTP, they often have to employ heuristics to figure out the type of server in question (as most servers vary in their implementation of FTP). So Proxy Servers start with a the most general notion and fall back to less common ones when the general ones fail. This is unacceptable for a **Load Balancer** due to the overhead involved in heuristics. As they only have to deal with a restricted set of servers, they can use user input in configuration files to figure the type of back end server. Passive change in strategy is not useful since it introduces additional overhead in serving the requests.

### Cache Hierarchies 

Persistent caching is the life blood of Forward Proxies, they implement most of the caching protocols like ICP, CARP, WCCP, Digests etc, while these are generally not present or not given enough importance in the Load Balancers. Many of them use custom facilities to monitor and update the content with the latest in their server pool  

### Security 

For a Proxy Server, the main clients are the ones who are connecting to its HTTP Server side. Thus the anonymity of these connections to the outside world is of paramount importance. Usually no information other than the bare minimum is passed outside. The Load Balancers sees it in a different light. The main clients of a Load Balancer are its the servers its HTTP Client connects to. So they generally pass on all information from the browsers to these servers but keep the information coming out from these servers to a bare minimum (Mostly only those information that has been configured to be visible).  

### Protocol 

Lastly, here are the differences in terms of the protocol.

Feature | Load Balancer | Proxy Server
--------|---------------|--------------
Request | GET /path.html HTTP/1.1 <br/> Host:server.domain:port | GET http://server.domain:port/path.html HTTP/1.0
ipv6    | Generally used to provide ipv6 front end to servers  which are not ipv6 capable | not applicable  
ssl     | Generally used to provide an SSL enabled interface to servers that does not provide one | not applicable  
Auth    | HTTP Auth/Form based Auth | Proxy Auth (Form based Auth not possible)

## Summary  

### Load Balancer (Surrogate)

- Load Balancing and Clustering with fail over (May also implement heart beat.)
- High amount of concurrent connections
- Figure out type of back end through configuration
- Fine grained cache management but most caching in RAM  
- Generally cache hierarchies protocols are not implemented
- Anonymity and Security as services in the Server side, with maximum permissiveness on the other side.  

### Proxy Servers (Forward Proxies)

- Large number of cache hierarchy protocols
- Generally smaller number of concurrent connections
- Origin server types are figured out through heuristics and testing.
- Macro management of Cache, with Persistent caching
- Anonymity and Security as services in the Client side, with maximum permissiveness on the other side.

### Personal Proxy Servers

- Filtering based on rules is important
- Prefetching is important for pages being viewed (spurt in connections with large idle time in between)
- Very small number of concurrent connections
- Restricted connections (may even have facility to block connections from systems other than localhost)
- Administration of individual users is important.  

 

## Different Proxies classified according to their specialization.

### Proxy Servers 

- [Squid](http://www.squid-cache.org/)
- [Sun Java System Web Proxy Server](http://www.sun.com/software/products/web_proxy/home_web_proxy.xml)
- [Microsoft ISA Server ](http://www.microsoft.com/isaserver/default.mspx)

### Load Balancers (Surrogates)

- [Varnish](http://varnish.projects.linpro.no/)
- [Apache mod_proxy](http://httpd.apache.org/docs/2.0/mod/mod_proxy.html)   
- [LightHTTPD mod_proxy_core](http://trac.lighttpd.net/trac/wiki/Docs:ModProxyCore)
- [Nginx](http://nginx.net/)
- [GlassFish load balancer](https://glassfish.dev.java.net/javaee5/lb-admin/)
- [Sun Java System Web Server RPP plugin](http://www.sun.com/software/products/web_srvr/home_web_srvr.xml)

### Personal Proxies

- [MouseHole](http://code.whytheluckystiff.net/mouseHole/)
- [Privoxy](http://www.privoxy.org/)
