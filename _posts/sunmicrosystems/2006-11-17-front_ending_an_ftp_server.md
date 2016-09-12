---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: Front ending an ftp server - Using SJS Web Proxy Server to boost Ftp Server performance.
title: Front ending an ftp server - Using SJS Web Proxy Server to boost Ftp Server performance.
---

Ftp is the storage protocol of the web.
by that statement I mean that when ever there is content to be served that is large enough (say more than a 100 MB), Ftp is the protocol of choice in serving it. The reason has to do with the very little amount of configuration you have to do to get a secure Ftp server up and running, and with the fact that the navigation is very easy and intuitive since it mirrors a filesystem. (Some times I tend to think that FTP took over the functions that the Gopher protocol was meant for.). Since the commands provided by Ftp are very restrictive, securing it does not take much effort either.

But this is a protocol with significant communication overhead. Given below is the normal path you have to go through inorder to fetch a file or to list the contents of a directory.

```
<[
220 agneyam.india.sun.com FTP server (Version wu-2.6.2+Sun) ready.
]
>[
USER myuser
]
<[
331 Password required for myuser.
]
>[
PASS xxxxxxx
]
<[
230 User myuser logged in.
]
>[
SYST
]
<[
215 UNIX Type: L8 Version: SUNOS
]
>[
PWD
]
<[
257 "/home/myuser" is current directory.
]
>[
EPSV
]
<[
229 Entering Extended Passive Mode (|||58605|)
]
>[
RETR myfile
]
<[
200 PORT command successful.
]
<[
150 Opening BINARY mode data connection for 'myfile' (3 bytes).
]
<[
226 Transfer complete.
]
```

 As you can see, it took 6 commands to actualy transfer a 3 byts long file. This introduces a large overhead when there are a large number of users. For this reason most Ftp servers limit the number of simultaneous users to a small number. (You might be familiar with the 'You are user 101 or 100 users allowed. Please wait a little time and try again' message when there is a new OS release).

 Ftp has another trouble, it requires two connections to operate on, the Contol connection and the Data connection. This is different from the way Http operates. This also introduces some hinderance for users who are behind firewalls.

 Here is where the webproxy server comes into picture. The webproxy server acts as a gateway between the ftp and the http. ie, it can be configured in such a fashion that the http requests that comes to it are translated to ftp requests by it, and the result of this ftp request is translated back into the http protocol.

Here is how it will operate.

```
->request from client to the proxy:

>[GET / HTTP/1.0
]
```

* From proxy to ftp server

```
Login with username/passwd (anonymous)
send sys and retrieve system type
setup data connection
retrieve the LIST for directory '/'
encode the result of LIST in html
```

```
<-response from proxy to client.,
<[
file1
file2
]
```

What you will gain out of this setup,
1)  The SunJavaSystem WebproxyServer is multi threaded rather than multi process, which allows it to reuse a single ftp connection for multiple HTTP requests. Which means that this is how the communication will be.

```
->client1 request for /file1

[proxy logs into ftpserver,

sends & retrieves sys,

changes to correct directory

sets up the data connection

retrieves the file1.

 ]

<-response to client1  with /file1

===================================

->client2 request for /file1

<-response to client2 with cached /file1 (note that there is no ftp connection involved.)

===================================

->client3 request for /file2

[use the previous connection

retrieves file2

]

<-response to client3 with /file2

===================================

->client4 request for /dir1/file2

[use the previous connection

change to directory dir1

retrieves file2

]

<-response to client3 with /file2

 ===================================
```

 As you can see, there is significant saving in doing this. The number of messages have been cut down drastically.

Configuring your WebProxy Server:

* Download the SunJavaSystem Web Proxy Server
* Install the server in a directory you wish to,
* Edit the obj.conf and add this entry:

(Add only the entry in bold letters. the rest of the entries are there just to show you where to add this.)

(change agneyam.india.sun.com to the name of your 'ftpserver')

```
<Object name="default">
AuthTrans fn="match-browser" browser=".\*MSIE.\*" ssl-unclean-shutdown="true"
NameTrans fn="map" from="/" to="ftp://agneyam.india.sun.com" rewrite-host="true"
PathCheck fn="url-check"
Service fn="deny-service"
AddLog fn="flex-log" name="access"
</Object>
```

* startup the server.
* Access the server from your browser and make sure that everything is alright.
ie, in the browser address bar, type (substitute myproxy for your own server name)
http://myproxy.sun.com

and make sure that you get the listing if anonymous user is supported in your ftp server. If anonymous listing is not supported, you should get a password prompt as a dialog.

With this configuration, the proxy at myproxy.india.sun.com will act as a front end for the ftpserver that you have configured in obj.conf. (From a user point of view the http://myproxy.sun.com will look like a webserver.)


