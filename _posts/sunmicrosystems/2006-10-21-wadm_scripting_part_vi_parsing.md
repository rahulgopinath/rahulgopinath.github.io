---
layout: post
tagline: "."
tags : [sunmicrosystems blog sun]
categories : sunblog
e: (wadm VI) Walking with the unknown - parsing Apache httpd.conf
title: (wadm VI) Walking with the unknown - parsing Apache httpd.conf
---

I have already shown you how to implement a ACL parser using wadm tcl. In this section, I will try to 
take you along as I try to implement a simple parser for Apache httpd.conf and use it to implement a
similar configuration in Sun Java System WebServer.


#### Looking at the apache httpd.conf

The httpd.conf looks like this:

httpd.conf

{% raw %}
```
# This is the main Apache HTTP server configuration file.  It contains the
# configuration directives that give the server its instructions.
ServerRoot "/usr/local/apache2"
Listen 800
LoadModule authn_file_module modules/mod_authn_file.so
LoadModule mime_module modules/mod_mime.so
..snipped..
LoadModule rewrite_module modules/mod_rewrite.so
..snipped..
ServerAdmin me@sun.com
ServerName www.example.com:80
DocumentRoot "/usr/local/www"
<Directory />
    Options FollowSymLinks
    AllowOverride All
</Directory>
ScriptAlias /codestriker/  /space/codestriker/codestriker-1.9.2-alpha-5/cgi-bin/
Alias /codestrikerhtml/  /space/codestriker/codestriker-1.9.2-alpha-5/html/
<IfModule dir_module>
    DirectoryIndex index.html
</IfModule>
<FilesMatch "\^\\.ht">
    Order allow,deny
    Deny from all
</FilesMatch>
ErrorLog logs/error_log
LogLevel warn

<IfModule log_config_module>
    LogFormat "%h %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-Agent}i\\"" combined
    LogFormat "%h %l %u %t \\"%r\\" %>s %b" common
    <IfModule logio_module>
      LogFormat "%h %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-Agent}i\\" %I %O" combinedio
    </IfModule>
    CustomLog logs/access_log common
</IfModule>
DefaultType text/plain
<IfModule mime_module>
    TypesConfig conf/mime.types
    AddType application/x-compress .Z
    AddType application/x-gzip .gz .tgz
    AddOutputFilter INCLUDES .shtml
</IfModule>
MIMEMagicFile conf/magic
```
{% endraw %}


The files look like tcl except for the <tag> </tag> stuff. Well it is possible to make tcl understand
that too. But other wise our strategy of defining procedures that are undefined until all the procedures
are defined holds good here too.

Since we are looking at a slightly more complex parsing than the acls, we will take a similar but slightly 
different route.


### The Parsing.

First let us see if we can capture the pattern that we noticed above.
here is our temporary conf file

temp.conf

{% raw %}
```
ServerName agneyam
<Directory />
    Options FollowSymLinks
    AllowOverride All
</Directory>
```
{% endraw %}


Here is the parser that we want to run on it.

apache.tcl

{% raw %}
```
namespace eval Apache {

    proc parse {file} {
        set text [read_file $file]
        eval $text
    }

    proc read_file {file} {
        set f [open $file r]
        set res [read -nonewline $f]
        close $f
        return $res
    }
}   
```
{% endraw %}

As you can see, We are just trying to apply the strategy previously described in ACL parsing.

{% raw %}
```
> source apache.tcl
> Apache::parse temp.conf
invalid command name "ServerName"
```
{% endraw %}

Ok so we implement the ServerName

{% raw %}
```
    proc ServerName args {
    }
```
{% endraw %}

{% raw %}
```
> source apache.tcl
> Apache::parse temp.conf
invalid command name "<Directory"
```
{% endraw %}

While it is easy for us to define two more commands <Directory and </Directory,
it seems that there should be a better way, What we can do is ask the tcl parser to
call us when it sees things of this sort. Tcl provides a convenient way for us to do 
that .


### The Unknown.

Tcl calls a procedure called unknown when ever it finds a command or procedure
that was not previously defined. We will take advantage of that to get the <tags> 
parsed.

What we will do is to redefine the unknown and make it into our own procedure.

apache.tcl

{% raw %}
```
namespace eval Apache {
    variable stack

    proc parse {file} {
        set text [read_file $file]
        init_parse
        if [catch {eval $text} err] {
            puts "Eval:$err"
        }
        exit_parse
    }

    proc read_file {file} {
        set f [open $file r]
        set res [read -nonewline $f]
        close $f
        return $res
    }

    proc init_parse {} {
        rename ::unknown _unknown
        proc ::unknown args {
            Apache::invoke $args
        }
        set Apache::stack {}
    }

    proc exit_parse {} {
        rename ::unknown ""
        rename _unknown ::unknown
    }

    proc invoke arg {
        puts ": $arg"
    }
}
```
{% endraw %}


Trying it

{% raw %}
```
> source apache.tcl
> Apache::parse temp.conf
: ServerName agneyam
: <Directory />
: Options FollowSymLinks
: AllowOverride All
: </Directory>
```
{% endraw %}

As you can see, We redefined and saved the current unknown to Apache::_unknown 
before parsing, evaluated the file and after that changed the Apache::_unknown to the 
global unknown.

Inside our parser, we redefined the unknown to call the Apache::invoke instead. so that
we get to interpret the procedures instead of tcl evaluator.

Now, we need to handle these tags better.


#### Handling the tags

Our aim is to just define procedures for all the normal directives (Those that are \*not\* of the
form <tag> or </tag>) and leave the <tag></tag> for invoke. In the process we also will keep
track of any un-implemented procedures.


apache.tcl

{% raw %}
```
namespace eval Apache {
    variable stack
    variable not_impl
    set not_impl {}

    proc parse {file} {
        set text [read_file $file]
        init_parse
        if [catch {eval $text} err] {
            puts "Eval:$err"
        }
        exit_parse
    }

    proc show {} {
        puts "Not Implemented:"
        puts "________________"
        foreach {i} $Apache::not_impl {
            puts $i
        }
    }

    proc read_file {file} {
        set f [open $file r]
        set res [read -nonewline $f]
        close $f
        return $res
    }

    proc init_parse {} {
        rename ::unknown _unknown
        proc ::unknown args {
            Apache::invoke $args
        }
        set Apache::stack {}
    }

    proc exit_parse {} {
        rename ::unknown ""
        rename _unknown ::unknown
    }

    proc push_stack arg {
        set Apache::stack [concat $Apache::stack $arg]
    }
    proc pop_stack {} {
        set popd [lindex  $Apache::stack end]
        set Apache::stack [lrange $Apache::stack 0 end-1]
        return $popd
    }

    proc invoke arg {
        set word [lindex $arg 0]
        switch -regexp $word {
            {\^ \*</.\*} {
                if {[regexp {\^ \*< \*/([\^ ]+) \*> \*$} $arg all one]} {
                    set p [pop_stack]
                    invoke_proc $p -exit
                }
                return
            }

            {\^ \*<.\*} {
                if {[regexp {\^ \*<([\^ ]+) \*(.\*)> \*$} $arg all one rest]} {
                    push_stack $one
                    invoke_proc $one -init $rest
                }
                return
            }

            default {
                #the only directives that come here must be those that are not done.
                notimpl $word
            }
       }
    }
    proc invoke_proc {p args} {
        if [llength [info proc $p]] {
            $p $args
        } else {
            notimpl $p
        }
    }

    proc notimpl arg {
        set Apache::not_impl [concat $Apache::not_impl $arg]
    }
}
```
{% endraw %}


As you can see, when we find a tag of sort <Directory> or <IfModule> we call
the corresponding procedure - eg: 'Directory' with the argument -init along with
the rest of arguments we got in the declaration. 
When we get the end of tag (</Directory>) we simply call Directory -exit.

Using it

{% raw %}
```
> source apache.tcl      
> Apache::parse temp.conf
> Apache::show           
Not Implemented:
________________
ServerName
Directory
Options
AllowOverride
```
{% endraw %}

Let us add something more to the apache httpd.conf

temp.conf

{% raw %}
```
ServerName agneyam
<IfModule log_config_module>
    LogFormat "%h %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-Agent}i\\"" combined
    LogFormat "%h %l %u %t \\"%r\\" %>s %b" common
    <IfModule logio_module>
      LogFormat "%h %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-Agent}i\\" %I %O" combinedio
    </IfModule>
    CustomLog logs/access_log common
</IfModule>
<Directory />
    Options FollowSymLinks
    AllowOverride All
</Directory>
```
{% endraw %}


#### Implementing the IfModule

There are two ways we can handle the IfModule,
* Do it statically, That is evaluate the IfModule with what is available in the current LoadedModules array (Assume such an array is constructed and is available.)
* Do it dynamically, Instead of Evaluating the IfModule during parsing state, add the condition to the script that will get evaluated when the script is run.

We will go for the second option since that is more powerful.

apache.tcl

{% raw %}
```
namespace eval Apache {
    variable stack
    variable not_impl

    #commands to be evaluated
    variable text

    proc parse {file} {
        set text [read_file $file]
        regsub -all {\\">} $text {\\" >} text
        pre_conf
        init_parse
        if [catch {eval $text} err] {
            puts "Eval:$err"
        }
        exit_parse
    }

    proc pre_conf {} {
        set Apache::stack {}
        set Apache::not_impl {}
        set Apache::text {}
        array set Apache::info {}
        array set Apache::module {}
    }

    proc show {} {
        puts "Not Implemented:"
        puts "________________"
        foreach {i} [lsort [uniq $Apache::not_impl]] { puts $i }
        puts "________________"
        foreach {i} $Apache::text { puts $i }
    }

    proc uniq {l} {
        if { $l == {} } { return {} }
        array set arr {}
        foreach element $l { set arr($element) "" }
        set result [array names arr]
        return $result
    }

    proc read_file {file} {
        set f [open $file r]
        set res [read -nonewline $f]
        close $f
        return $res
    }

    proc | args {
        lappend Apache::text [join $arg " "]
    }

    proc init_parse {} {
        rename ::unknown _unknown
        proc ::unknown args {
            Apache::invoke $args
        }
    }

    proc exit_parse {} {
        rename ::unknown ""
        rename _unknown ::unknown
    }

    proc push_stack arg {
        set Apache::stack [concat $Apache::stack $arg]
    }

    proc pop_stack {} {
        set popd [lindex  $Apache::stack end]
        set Apache::stack [lrange $Apache::stack 0 end-1]
        return $popd
    }

    proc invoke arg {
        set word [lindex $arg 0]
        switch -regexp $word {
            {\^ \*</.\*} {
                if {[regexp {\^ \*< \*/([\^ ]+) \*> \*$} $arg all one]} {
                    set p [pop_stack]
                    invoke_proc $p -exit
                }
                return
            }

            {\^ \*<.\*} {
                if {[regexp {\^ \*<([\^ ]+) \*(.\*)> \*$} $arg all one rest]} {
                    push_stack $one
                    invoke_proc $one -init $rest
                }
                return
            }

            default {
                #the only directives that come here must be those that are not done.
                notimpl $word $arg
            }
       }
    }
    proc invoke_proc {p args} {
        if [llength [info proc $p]] {
            $p $args
        } else {
            notimpl $p $args
        }
    }

    proc notimpl {p arg} {
        #Uncomment the next line to get the not implenented procedures
        #in their context.
        | "#NI ($p) $arg"
        set Apache::not_impl [concat $Apache::not_impl $p]
    }

    #==================================================
    #       The Engine
    #==================================================

    proc IfModule args {
        set arg [lindex $args 0]
        switch -- [lindex $arg 0] {
            {-init} {
                set cur [lindex $arg 1]
                #check if it is of type !xxxx , if it is take the reverse.
               if {[regexp {\^ \*!([\^ ]+)$} $cur all one] } {
                    | "if {!\\[info exist Apache::module($one)\\]}  {" ;#}
                } else {
                    | "if \\[info exist Apache::module($cur)\\]  {" ;#}
                }
            }
            {-exit} {
                #;{
                | "}"
            }
        }
    }
}
```
{% endraw %}



##### Using it,

{% raw %}
```
> source apache.tcl      
> Apache::parse temp.conf
> Apache::show           
Not Implemented:
________________
AllowOverride
CustomLog
Directory
LogFormat
Options
ServerName
________________
#NI (ServerName) ServerName agneyam
if [info exist Apache::module(log_config_module)]  {
#NI (LogFormat) LogFormat {%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"} combined
#NI (LogFormat) LogFormat {%h %l %u %t "%r" %>s %b} common
if [info exist Apache::module(logio_module)]  {
#NI (LogFormat) LogFormat {%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i" %I %O} combinedio
}
#NI (CustomLog) CustomLog logs/access_log common
}
#NI (Directory) -init /
#NI (Options) Options FollowSymLinks
#NI (AllowOverride) AllowOverride All
#NI (Directory) -exit
```
{% endraw %}

As you can see, the IfModule adds if condition to the script produced at the end. Now let us 
turn our attension to the engine.

#### The Engine

The Engine is very simple. You have to define a procedure for each directive you want to 
translate. You will be given the arguments via the $args list. After figuring out what commands to call,
just call them using the '|' procedure. (as demonstrated in the IfModule.)

Handling the tags are also simple as shown in the IfModule, each such procedure (say Directory)
will take a list whose first element will be '-init' when it enters the tag, and '-exit' when it exits the tag.
You will also get the rest of arguments to tag entry along with -init.

(Look for the comment with #Engine to see the engine starting.)

apache.tcl

{% raw %}
```
namespace eval Apache {
    variable stack
    variable not_impl
    variable info
    variable module

    #commands to be evaluated
    variable text

    proc parse {file} {
        set text [read_file $file]
        #massage it gently.
        regsub -all {\\">} $text {\\" >} text

        pre_conf
        init_parse
        if [catch {eval $text} err] {
            puts "Eval:$err"
        }
        exit_parse
    }

    proc pre_conf {} {
        set Apache::stack {}
        set Apache::not_impl {}
        set Apache::text {}
        array set Apache::info {}
        array set Apache::module {}
        #--------------------------------
        set Apache::info(config) apache
        set Apache::info(config_port) 10000
        set Apache::info(server_name) apache_mig
        set Apache::info(default_vs) $Apache::info(config)
        | create-config --http-port $Apache::info(config_port) --server-name $Apache::info(server_name) $Apache::info(config)
 
    }

    proc show {} {
        puts "Not Implemented:"
        puts "________________"
        foreach {i} [lsort [uniq $Apache::not_impl]] { puts $i }
        puts "________________"
        foreach {i} $Apache::text { puts $i }
    }

    proc uniq {l} {
        if { $l == {} } { return {} }
        array set arr {}
        foreach element $l { set arr($element) "" }
        set result [array names arr]
        return $result
    }


    proc read_file {file} {
        set f [open $file r]
        set res [read -nonewline $f]
        close $f
        return $res
    }

    proc | args {
        lappend Apache::text [join $args " "]
    }

    proc init_parse {} {
        rename ::unknown _unknown
        proc ::unknown args {
            Apache::invoke $args
        }
    }

    proc exit_parse {} {
        rename ::unknown ""
        rename _unknown ::unknown
    }

    proc push_stack arg {
        set Apache::stack [concat $Apache::stack $arg]
    }

    proc pop_stack {} {
        set popd [lindex  $Apache::stack end]
        set Apache::stack [lrange $Apache::stack 0 end-1]
        return $popd
    }

    proc invoke arg {
        set word [lindex $arg 0]
        switch -regexp $word {
            {\^ \*</.\*} {
                if {[regexp {\^ \*< \*/([\^ ]+) \*> \*$} $arg all one]} {
                    set p [pop_stack]
                    invoke_proc $p -exit
                }
                return
            }

            {\^ \*<.\*} {
                if {[regexp {\^ \*<([\^ ]+) \*(.\*)> \*$} $arg all one rest]} {
                    push_stack $one
                    invoke_proc $one -init $rest
                }
                return
            }

            default {
                #the only directives that come here must be those that are not done.
                notimpl $word $arg
            }
       }
    }
    proc invoke_proc {p args} {
        if [llength [info proc $p]] {
            $p $args
        } else {
            notimpl $p $args
        }
    }

    proc notimpl {p arg} {
        #Uncomment the next line to get the not implenented procedures
        #in their context.
        #| "#NI ($p) $arg"
        set Apache::not_impl [concat $Apache::not_impl $p]
    }

    #==================================================
    #       The Engine
    #==================================================

    proc IfModule args {
        set arg [lindex $args 0]
        switch -- [lindex $arg 0] {
            {-init} {
                set cur [lindex $arg 1]
                #check if it is of type !xxxx , if it is take the reverse.
               if {[regexp {\^ \*!([\^ ]+)$} $cur all one] } {
                    | "if {!\\[info exist Apache::module($one)\\]}  {" ;#}
                } else {
                    | "if \\[info exist Apache::module($cur)\\]  {" ;#}
                }
            }
            {-exit} {
                #;{
                | "}"
            }
        }
    }

    proc ServerRoot args {
        set Apache::info(server_root) $args
    }

    proc ServerAdmin args {
        set Apache::info(server_admin) [lindex $args 0]
    }

    proc ServerName args {
        set Apache::info(server_name) [lindex $args 0]
    }

    proc DocumentRoot args {
        set droot [lindex $args 0]
        | set-virtual-server-prop --config $Apache::info(config) --vs $Apache::info(default_vs) \\
            document-root=$droot
    }

    proc LogLevel args {
        set arg [lindex $args 0]
        set log warning
        #emerg System is unstable
        #alert Immediate action required
        #crit Critical error
        #error Non-critical error
        #warn Warning
        #notice Normal but significant
        #info Informational
        #debug Debug level

        #finest
        #finer
        #fine
        #info
        #warning
        #failure
        #config
        #security
        #catastrophe

        switch $arg -- {
            emerg {
                set log catastrophe
            }
            alert {
                set log failure
            }
            crit {
                set log failure
            }
            errof {
                set log warning
            }
            warn {
                set log warning
            }
            notice {
                set log info
            }
            info {
                set log fine
            }
            debug {
                set log finest
            }
        }

        | set-log-prop --config $Apache::info(config) log-level=$log
    }

    proc ErrorLog args {
        set log [lindex $args 0]
        | set-log-prop --config $Apache::info(config) log-file=$log
    }

    proc AccessFileName args {
        set af [lindex $args 0]
        | enable-htaccess --config $Apache::info(config) --vs $Apache::info(default_vs) \\
            --config-file $af
    }

    proc AddType args {
        set type [lindex $args 0]
        set ext [join [lrange $args 1 end] ","]
        regsub -all {\\.} $ext {} ext
        | create-mime-type --config $Apache::info(config) --extensions $ext $type
    }

    proc DefaultType args {
        #this does not have an equivalent in sjswebsrever.
    }

    proc Alias args {
        set alias [lindex $args 0]
        set fs [lindex $args 1]
        | create-document-dir --config $Apache::info(config) --uri-prefix $alias \\
            --directory $fs --vs $Apache::info(default_vs)
    }

    proc CgiAlias args {
        set alias [lindex $args 0]
        set fs [lindex $args 1]
        | create-cgi-dir --config $Apache::info(config) --uri-prefix $alias \\
            --directory $fs --vs $Apache::info(default_vs)
    }

    proc TypesConfig args {
        set mf [lindex $args 0]
        | set-config-prop --config $Apache::info(config) mime-file=$mf
    }

    proc LoadModule args {
        | "set Apache::module([lindex $args 0]) [lrange $args 1 end]"
    }

    proc Listen args {
        #listen could come in two forms:
        #8000
        #192.168.1.1:8000
        set port 0
        set ip {}

        set arg [lindex $args 0]
        switch -regexp -- $arg {
            {:} {
                regexp {(.+):(.+)} $arg all ip port
            }
            default {
                set port $arg
            }
        }

        #The listen could happen multiple times. when it does, we need to change the http-listener name
        set lst http-listener-1
        if [info exists Apache::info(http-listener-cur)] {
            set lst "$Apache::info(http-listener-cur)-1"
            set ipprop ""
            if [string length $ip] {
                set ipprop "--ip $ip"
            }
            eval "| create-http-listener --config $Apache::info(config) \\
                     --listener-port $port $ipprop \\
                    --server-name $Apache::info(server_name) \\
                    --default-virtual-server-name $Apache::info(default_vs) \\
                    $ipprop $lst"

            set Apache::info(http-listener-cur) $lst
        } else {
            set ipprop ""
            if [string length $ip] {
                set ipprop "ip=$ip"
            }
            eval "| set-http-listener-prop --config $Apache::info(config) \\
                    --http-listener $lst port=$port $ipprop"
        }
    }
}
```
{% endraw %}


##### Using It

{% raw %}
```
> source apache.tcl       
> Apache::parse httpd.conf
> Apache::show            
Not Implemented:
________________
Allow
AllowOverride
CustomLog
Deny
Directory
DirectoryIndex
FilesMatch
Group
LogFormat
Options
Order
SSLRandomSeed
ScriptAlias
SetHandler
User
________________
create-config --http-port 10000 --server-name apache_mig apache
set-http-listener-prop --config apache --http-listener http-listener-1 port=800
if {![info exist Apache::module(mpm_winnt_module)]}  {
if {![info exist Apache::module(mpm_netware_module)]}  {
}
}
set-virtual-server-prop --config apache --vs apache document-root=/usr/local/www
create-document-dir --config apache --uri-prefix /codestrikerhtml/ --directory /space/codestriker/codestriker-1.9.2-alpha-5/html/ --vs apache
create-document-dir --config apache --uri-prefix /lxr_scratch --directory /usr/local/lxr_scratch --vs apache
create-document-dir --config apache --uri-prefix /lxr_40rtm --directory /usr/local/lxr_40rtm --vs apache
create-document-dir --config apache --uri-prefix /lxr_36rtm --directory /usr/local/lxr_36rtm --vs apache
create-document-dir --config apache --uri-prefix /lxr_nspr --directory /usr/local/lxr_nspr --vs apache
create-document-dir --config apache --uri-prefix /lxr_nss --directory /usr/local/lxr_nss --vs apache
create-document-dir --config apache --uri-prefix /lxr_squid --directory /usr/local/lxr_squid --vs apache
create-document-dir --config apache --uri-prefix /lxr_ws70 --directory /usr/local/lxr_ws70 --vs apache
if [info exist Apache::module(dir_module)]  {
}
enable-htaccess --config apache --vs apache --config-file .htaccess
set-log-prop --config apache log-file=logs/error_log
set-log-prop --config apache log-level=warning
if [info exist Apache::module(log_config_module)]  {
if [info exist Apache::module(logio_module)]  {
}
}
if [info exist Apache::module(alias_module)]  {
}
if [info exist Apache::module(cgid_module)]  {
}
if [info exist Apache::module(mime_module)]  {
set-config-prop --config apache mime-file=conf/mime.types
create-mime-type --config apache --extensions Z application/x-compress
create-mime-type --config apache --extensions gz,tgz application/x-gzip
}
if [info exist Apache::module(ssl_module)]  {
}
```
{% endraw %}

The current apache.tcl is available [here](./resources/sunmicrosystems/apache.tcl)
