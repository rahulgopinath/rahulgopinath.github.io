---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm IV) Log Analyzer
title: (wadm IV) Log Analyzer
---

In the earlier section, we looked at how to create a parser by defining a little language that understood what   
we were trying to parse, here we will try an create a little language that _we_ can use to look at the data in a   
more comprehensive way.  
  
One of the more interesting things that the Web Server provides is the access logs that tells us who are visiting   
our site, how many pages they visited, who are all referring to us, and how many (if any) pages have broken   
links (ie how many 404 we have.)  
  
Interesting info also includes the type of UserAgents, the pages that seem to get hit the largest, and our entry   
points, (The pages that a unique ip will have accessed first,) our exit points (The page which the unique ips   
accessed last) etc.  
  
### The commands that wadm provides for logs:

```
> info commands \*log\*  
get-log enable-access-log set-log-prop get-access-log get-access-log-prop get-log-prop   
set-access-log-buffer-prop rotate-log get-access-log-buffer-prop disable-access-log  
```

While the wadm does provide a means for us to get the access log as a whole, they are not meant to be   
used directly. (ie they just dump the whole information as a chunk with out any way to filter the information to   
what is relevant for us)  
  
But this is not a very serious handicap as long as we have the scripting ability. Infact it provides us freedom   
to define the interface that we like to to access the data which we are interested in.  
  

### Substructure: Access Log from wadm  

```
> get-access-log --config=test agneyam  
format=%Ses->client.ip% - %Req->vars.auth-user% [%SYSDATE%] "%Req->reqpb.clf-request%"   
%Req->srvhdrs.clf-status% %Req->srvhdrs.content-length%  
webcache.sun.com - - [20/Oct/2006:06:27:57 -0700] "GET / HTTP/1.1" 200 355  
webcache.sun.com - - [20/Oct/2006:06:27:58 -0700] "GET /favicon.ico HTTP/1.1" 200 3574  
webcache.sun.com - - [20/Oct/2006:06:28:03 -0700] "POST /cgi-bin/test-cgi HTTP/1.1" 200 596  
varunam.sun.com - - [20/Oct/2006:06:28:22 -0700] "GET / HTTP/1.1" 200 355  
varunam.sun.com - - [20/Oct/2006:06:28:22 -0700] "GET /favicon.ico HTTP/1.1" 200 3574  
varunam.sun.com - - [20/Oct/2006:06:28:24 -0700] "POST /cgi-bin/test-cgi HTTP/1.1" 200 602  
varunam.sun.com - - [20/Oct/2006:06:28:48 -0700] "GET /cgi-bin/test-cgi?myvar=new HTTP/1.1" 200 573  
varunam.sun.com - - [20/Oct/2006:06:29:06 -0700] "GET /whoami.html HTTP/1.1" 404 292  
hokus-pokus.sun.com - - [20/Oct/2006:23:09:15 +0530] "GET / HTTP/1.1" 200 355  
```
  
(You can also modify the settings of access log by using the following CLIs)  

```
> get-access-log-prop  --config=test  
enabled=true  
file=../logs/access  
format=%Ses->client.ip% - %Req->vars.auth-user% [%SYSDATE%] "%Req->reqpb.clf-request%"   
%Req->srvhdrs.clf-status% %Req->srvhdrs.content-length%  
```

Assuming your new custom format is in the variable $myformat  

```
> set-access-log-prop --config=test format=$myformat  
``` 

### Choosing a superstructure

The access log is a matrix that is arranged cronologically. The SQL (Structured Query Language) is generally   
useful in mining data out of these matrices. More so because the users will be able to transpose at least a part   
of their familiarity with SQL to our API.  
  
While it is useful to stick close to SQL, I am changing it slightly so as to make it easier to parse. In general   
this is what I am going to do:  

### Syntax

```
select {select list} from {from list} where {where list} group by {id}  
```

The where part and later are optional.  
Each of the key words are followed by a list which specifies the list associated with it. The list will contain   
the variables that will be extracted from the logs.  

### Some UseCases

```
# Avoiding this common use case for now to make the code a little more simpler  
# select {\*} from machine1 
# The reason for choosing $xxx is that we will be able to replace them with the corresponding  
# values just by evaluating them. This will make it much simpler to construct the result.  
  
select {$ip,$request,$response} from machine1  
select {$ip,$request,$response} from {machine1,machine2}  
select {$ip,$request,$response} from machine1 where {$response == 404}  
select {$ip [:sum $size] } from machine1 where {$response == 404} group by {$ip}  
``` 

#### More assumptions and short cuts (In the interest of simplicity)  

While it is easy to parse the format line from `get-access-log-prop`
`format=%Ses->client.ip% - %Req->vars.auth-user% [%SYSDATE%] "%Req->reqpb.clf-request%" %Req->srvhdrs.clf-status% %Req->srvhdrs.content-length%`
We wont be parsing that, Instead we will use fixed positions for now.  
  
ie: from the above  

```
$ip : 0  
#dummy field -  
$auth : 2  
$date : 3  
#you can always massage the data to remove the _"_ from request and you will get the $method, $uri, $http from the $request.  
$request : 5  
$response : 6  
$size : 7  
```

### Implementing the Language

As always it is a good idea to start with a namespace.  
  
#### db.tcl

```
namespace eval Logs {  
    namespace export {select}  
    proc select args {  
            puts ">$args"  
    }  
}  
```
  
Remember what we discussed last section? The args is the variable args mechanism for tcl.   
so any tcl statement that takes args as a parameter will take any number of parameters. With   
that in mind, the proc select will be able to slurp the entire query that we will throw at it.  
  
The namespace export marks for export the procedures that we want others to be able to   
use natively. ie by using  
  
```
> namespace import Logs::select  
```
  
from global namespace, the user will be able to make use of our language with out polluting his   
namespace with our local procedurs.  

##### The select statement.

```
proc select args {  
    set select {}  
    set from {}  
    set where {}  
    set group {}  
    set group_by {}  
    set lastword select  
    foreach word $args {  
        #look for our delimiters  
        switch $word {  
            from {  
                set lastword from  
            }  
            where {  
                set lastword where  
            }  
            group {  
                set lastword group  
            }  
            by {  
                set lastword group_by  
            }  
            default {  
                lappend $lastword $word  
            }  
        }     
    }     
    exec_select [join $select { }] [join $from { }] [join $where { }] [join $group_by {}]  
}  
```

What we are doing here, is to take an easy way.  We are just looking for the keywords 'from' 'where'   
and 'group' to extract the lists following them, we use the tcl's dynamic nature to just change the variable   
being appended to.   
  
You would have under stood the reason whey we went for a {$ip $response} model rather than simply   
$ip $response in the select statement,...     
          The reason is that if we had gone for $ip $response model, tcl would have evaluated them in the   
execution local context rather than wait for us to supply them. the braces {} provides us a convenient   
bubble to protect against evaluation before time.  
  
check it out with the exec_select  

```
proc exec_select {select from where group} {  
     puts "-------------"  
     puts "select>"  
     puts $select  
     puts "from>"  
     puts $from  
     puts "where>"  
     puts $where  
     puts "group_by>"  
     puts $group  
     puts "-------------"  
}  
```

```
> select {$ip -> $response} from agneyam where {$response == 404}  
-------------  
select>  
$ip -> $response  
from>  
agneyam  
where>  
$response == 404  
group_by>  
```
  
Using the $select list as an output formater, and $where as the condition.  
Here is what the exec select would look like.  
  
```
proc exec_select {select from where group} {  
    set collect 0  
    # check if we have grouping statements in select (:sum)  
    #  
    # if there are, then we use the current select statement as a template for two types of statements  
    # one to keep adding to an accumulator each variable that is grouped, and the other template to  
    # fetch all the data at the end of the loop from the accumulator and construct the result.  
    # if there are none, then we just have one template which will contain the variables that will be  
    # expanded inline at the end of each iteration.  

    #use_select and collect_select are the two templates. use_select sends data to accumulator and  
    #collect_select retrieves them.  

    if {[regexp {:[a-zA-Z]+} $select]} then {  
        set collect 1  
        regsub -nocase -all {:([a-zA-Z]+) } $select {use_\\1 [incr use_id]:$id } use_select  
        regsub -nocase -all {:([a-zA-Z]+) } $select {collect_\\1 [incr use_id]:$id } collect_select  
    } else {  
         set use_select $select  
    }  

    #process the from here.   
    #interleave-logs will collect all the logs from the list of machines supplied and splat it into a list.  
    set cmd {[interleave-logs $from]}  
    set all_logs [subst $cmd]  
    foreach line $all_logs {  
        set use_id 0  
        set id [subst_in_context $line $group]  
        if {[expr [string length $where] > 0]} {  
            if [expr $where] {  
                eval_select $line $use_select  
            }  
        } else {  
            eval_select $line $use_select  
        }  

    }  
    if $collect {  
        foreach id [array names Logs::context] {  
            set line $Logs::context($id)  
            set use_id 0  
            puts [subst_in_context $line $collect_select]  
            unset Logs::context($id)  
        }  
    }  
}  
```
  
Interleave logs is a tiny procedure that mixes the logs from multiple machines.  
  
```
proc interleave-logs {args} {  
    set fmt [Date::GetFormat]  
    Date::SetFormat {\\[DD/MMM/YYYY:T24S}  
    set logs {}  
    foreach machine $args {  
        set log [get-log $machine]  
        set logs [concat $logs $log]  
    }  
    set sorted [lsort -command compare-dates $logs]  
    Date::SetFormat $fmt  
    return $sorted  
}  
```
  
The accumulator is pretty simple.  

```
proc use_sum {_id val} {  
    upvar 1 ip ip  
    upvar 1 auth auth  
    upvar 1 date date  
    upvar 1 request request  
    upvar 1 response response  
    set id [subst $_id]  
    if [info exists Logs::results($id)] {  
        array set Logs::results [list $id "$Logs::results($id) $val"]  
    } else {  
        array set Logs::results [list $id "$val"]  
    }  
    return $val  
}  
proc collect_sum {_id val} {  
    upvar 1 ip ip  
    upvar 1 auth auth  
    upvar 1 date date  
    upvar 1 request request  
    upvar 1 response response  
    upvar 1 size size   
    set id [subst $_id]  
    set lst $Logs::results($id)  
    set sum 0  
    foreach l $lst {  
        set sum [expr $sum + $l]  
    }  
    set Logs::results($id) {}  
    return $sum  
}  
```
  
To define any new [:xxx ] procedure that you want to apply in select procedure, you just have to   
copy the previous procedures, define the use_xx and collect_xxx, and change the list processing in   
collect_xxx accourdingly (as given below.)  

```
    set sum  
    foreach l $lst {  
        set sum [your_func $sum $l]  
    }  
```

As you would have noticed there is some redundancy which can be eliminated. but this form is   
easier to understand than after eliminating the common portion.  
  
The complete db.tcl is available [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/db.tcl).

#### Using it

1) Make sure that the date.tcl from the below section is in your current directory along with db.tcl  

```
> source db.tcl  
> select {$ip, $request, $response } from agneyam  
webcache.sun.com, GET /favicon.ico HTTP/1.1, 200   
webcache.sun.com, POST /cgi-bin/test-cgi HTTP/1.1, 200   
varunam.sun.com, GET /favicon.ico HTTP/1.1, 200    
varunam.sun.com, GET / HTTP/1.1, 200    
varunam.sun.com, POST /cgi-bin/test-cgi HTTP/1.1, 200    
varunam.sun.com, GET /cgi-bin/test-cgi?myvar=new HTTP/1.1, 200    
varunam.sun.com, GET /whoami.html HTTP/1.1, 404    
varunam.sun.com, GET /mexico.html HTTP/1.1, 404    
hokus-pokus.sun.com, GET / HTTP/1.1, 200  
  
> select {$ip, $request, $response } from agneyam where {$response == 404}  
varunam.sun.com, GET /whoami.html HTTP/1.1, 404   
varunam.sun.com, GET /mexico.html HTTP/1.1, 404   
  
> select {$ip [:sum $size] } from agneyam group by {$ip}  
hokus-pokus.sun.com 355   
varunam.sun.com 5688   
webcache.sun.com 4170   
  
> select {$response [:sum $size] } from agneyam group by {$response}  
404 584   
200  9629   
  
> select {$ip [:sum 1] } from agneyam group by {$ip}                     
hokus-pokus.sun.com 1   
varunam.sun.com 6   
webcache.sun.com 2   
                                                                        
> select {$response [:sum 1] } from agneyam group by {$response}  
404 2   
200 7   
```

#### required utilities:

date.tcl from [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/date.tcl) or [here(external)](http://web.uvic.ca/~erempel/tcl/DatePkg/DatePkg.html)  
Download the sourcefile and save it as date.tcl. Use the below command to use it before you source the db.tcl (It is already sourced in db.tcl)  

```
> source date.tcl  
```

The complete db.tcl is available [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/db.tcl).
