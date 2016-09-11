---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm VII) Halloween - dressing up as a filesystem
title: (wadm VII) Halloween - dressing up as a filesystem
---

In the previous installments, We have been implementing languages over wadm. this time
let us turn our attention to something different.

The Sun Java System Web Server 7.0 provides multiple commands that help us manipulate
the configuration. Though they are provided in a flat namespace, the parameters taken by 
each of the commands suggests that it is actualy a squashed up hierarchy.

let me illustrate what I mean.

type the below commands and tab once.

```
> list-config --
...nothing

> list-virtual-servers --
--config\*

> list-http-listeners --
--config\*

> list-webapps --
--config\*     --vs\*

> list-dav-collections --
--config\*     --vs\*

> list-ciphers --
--config\*          --http-listener\*
```

What we see above means that even though we see all the commands as a flat namespace
they are in reality members of a hierarchy as below. 

```
                     config
                       ||

  http-listeners         virtual-servers
         ||            ||                   ||
      ciphers dav-collections               webapps
```

and so forth

A filesystem is one of the better ways to represent hierarchical data. More so because users are 
familiar with filesystems.  To provide an fs view of our commands and data, this is what we will do.

1) Simplest case: We are at the root of hierarchy
      ls :           Show all the applicable list commands (commands that can be executed straight away with out 
                     any other required option)

     cd <dir>:  The dir will be the name of a command.that was listed in the ls. 
                      Save the dir in an internal variable $pwd.

2) We are one level up and the pwd now contains the name of a command.
      ls :           Show the results of executing that command.
      cd <dir>:  The dir will be the name of one of the result elements. that was listed in the ls.
                     Save the dir in the $pwd.

3) We are two levels up and the pwd now contains the name of a command and one element of its result
      ls :           Show all the applicable list commands (commands that can be executed straight away with out 
                     any other required option other than what is there in $pwd)

     cd <dir>:  The dir will be the name of a command.that was listed in the ls. 
                      Save the dir in an internal variable $pwd.

This an be continued for any levels with pwd contains alternate command names and one of its results.
eg: {list-configs test list-http-listeners http-listener-1 list-ciphers}


### Meta wadm.

In order for us to do this, We need some meta information:
The list commands supported, their required options, how the arguments map to the commands 

let us see if we can get wadm to describe itself..

```
> info commands list-\*
list-http-listeners list-jvm-profilers list-external-jndi-resources list-mail-resource-userprops ...
```

now to get them to describe themselves.
let us try executing one.

```
> list-http-listeners
Usage: list-http-listeners --help|-?
  or   list-http-listeners [--echo] [--no-prompt] [--verbose] [--all] --config=name
CLI014 config is a required option.

> list-jvm-profilers 
Usage: list-jvm-profilers --help|-?
  or   list-jvm-profilers [--echo] [--no-prompt] [--verbose] [--all] --config=name
CLI014 config is a required option.
```


This is pretty nice, the commands second line in the tcl error output gives us the information we need.
let us try and extract the info.

```
> foreach {l} [info commands list-\*] {
      if [catch $l err] {
            puts  [lindex [split $err "\\n"] 1]
      }
}
  or   list-http-listeners [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-jvm-profilers [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-external-jndi-resources [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-mail-resource-userprops [--echo] [--no-prompt] [--verbose] --config=name --jndi-name=name
  or   list-cgi-dirs [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-acls [--echo] [--no-prompt] [--verbose] [--all] [--vs=name] --config=name
  or   list-cgi-envvars [--echo] [--no-prompt] [--verbose] --config=name
  or   list-reverse-proxy-uris [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-url-redirects [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-document-dirs [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-lifecycle-module-userprops [--echo] [--no-prompt] [--verbose] [--verbose] --config=name --module=name
  or   list-mime-types [--echo] [--no-prompt] [--verbose] [--all] [--vs=name] [--category=type|enc|lang] --config=name
  or   list-certs [--echo] [--no-prompt] [--verbose] [--all] [--token=name] [--cert-type=(server | ca; default is 'server')] --config=name
  or   list-ciphers [--echo] [--no-prompt] [--verbose] [--cipher-type=ssl2/ssl3tls]  --config=name --http-listener=name
  or   list-error-pages [--echo] [--no-prompt] [--verbose] [--all] [--uri-pattern=pattern] --config=name --vs=name
  or   list-webapps [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-locks [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name --collection-uri=uri
  or   list-jdbc-resource-userprops [--echo] [--no-prompt] [--verbose] [--property-type=type]  --config=name --jndi-name=resourcename
  or   list-virtual-servers [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-mail-resources [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-soap-auth-provider-userprops [--echo] [--no-prompt] [--verbose] --config=name --provider=name
  or   list-external-jndi-resource-userprops [--echo] [--no-prompt] [--verbose] --config=name --jndi-name=resourcename
  or   list-tokens [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-jdbc-resources [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-users [--echo] [--no-prompt] [--verbose] [--all] ( [--uid=wildcardstr] | [--first-name=wildcardstr] | [--last-name=wildcardstr] | [--email=wildcardstr] ) [--vs=name] --config=name --authdb=name
  or   list-crls [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-org-units [--echo] [--no-prompt] [--verbose] [--all] [--vs=name] --config=name --authdb=name
  or   list-authdb-userprops [--echo] [--no-prompt] [--verbose] [--vs=name]  --config=name --authdb=name
  or   list-custom-resources [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-config-files [--echo] [--no-prompt] [--verbose] --config=name
  or   list-dav-collections [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-groups [--echo] [--no-prompt] [--verbose] [--all] [--name=filter] [--vs=name] --config=name --authdb=name
  or   list-group-members [--echo] [--no-prompt] [--verbose] [--all] [--org-unit=orgunit] [--vs=name] --config=name --authdb=name --group=group-id
  or   list-instances [--echo] [--no-prompt] [--verbose] [--all] (--config=name | --node=name)
  or   list-events [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-reverse-proxy-headers [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=vs-name --uri-prefix=uri
  or   list-authdbs [--echo] [--no-prompt] [--verbose] [--all] [--vs=name] --config=name
  or   list-lifecycle-modules [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-auth-realms [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-custom-resource-userprops [--echo] [--no-prompt] [--verbose] --config=name --jndi-name=resourcename
  or   list-soap-auth-providers [--echo] [--no-prompt] [--verbose] [--all] --config=name
  or   list-jvm-options [--echo] [--no-prompt] [--verbose] [--all] [--profiler=profiler-name] [--debug-options] --config=name
  or   list-uri-patterns [--echo] [--no-prompt] [--verbose] [--feature=feature] --config=name --vs=name
  or   list-search-collections [--echo] [--no-prompt] [--verbose] [--all] --config=name --vs=name
  or   list-auth-realm-userprops [--echo] [--no-prompt] [--verbose] --config=name --realm=name
```

yes it does seem to help. 
The things in [--xxx] are optional, so let us strip them away, also the starting 'or cmd-name' 
since we do not really have any need for those.

fs.tcl

```
namespace eval Fs {
    variable commands
    proc init {} {
        array set Fs::commands {}
        foreach {cmd} [info commands list-\*] {
            catch {$cmd} err
{% raw %}
            set line [replace [lindex [split $err "\\n"] 1] {{\^ +or +[a-z-]+} {\\[.+\\]} {=[a-z]+} {\^ +}}]
{% endraw %}
            #handle the either or.
            regsub -all -- {\\( \*([a-z=-]+) \*\\| \*([a-z=-]+) \*\\)} $line {\\1} line
            set Fs::commands($cmd) $line
        }
        show
    }

    proc replace {var lst} {
        foreach l $lst { regsub -all -- $l $var {} var }
        return $var
    }

    proc show {} {
        foreach {c} [array names Fs::commands] {
            puts "$c: $Fs::commands($c)"
        }
    }
}
```


#### Using it

```
> source fs.tcl                 
> Fs::init                      
list-jdbc-resource-userprops: --config --jndi-name
list-error-pages: --config --vs
list-crls: --config
list-lifecycle-modules: --config
list-locks: --config --vs --collection-uri
list-virtual-servers: --config
list-cgi-dirs: --config --vs
list-authdb-userprops: --config --authdb
list-configs: 
list-jvm-profilers: --config
list-ciphers: --config --http-listener
list-custom-resources: --config
list-external-jndi-resource-userprops: --config --jndi-name
list-soap-auth-provider-userprops: --config --provider
list-nodes: 
list-groups: --config --authdb
list-document-dirs: --config --vs
list-auth-realms: --config
list-lifecycle-module-userprops: --config --module
list-auth-realm-userprops: --config --realm
list-webapps: --config --vs
list-mime-types: --config
list-uri-patterns: --config --vs
list-events: --config
list-authdbs: --config
list-jvm-options: --config
list-http-listeners: --config
list-group-members: --config --authdb --group-id
list-mail-resource-userprops: --config --jndi-name
list-mail-resources: --config
list-reverse-proxy-headers: --config --vs-name --uri-prefix
list-users: --config --authdb
list-search-collections: --config --vs
list-certs: --config
list-tokens: --config
list-soap-auth-providers: --config
list-instances: --config
list-custom-resource-userprops: --config --jndi-name
list-config-files: --config
list-cgi-envvars: --config
list-reverse-proxy-uris: --config --vs
list-url-redirects: --config --vs
list-jdbc-resources: --config
list-org-units: --config --authdb
list-external-jndi-resources: --config
list-acls: --config
list-dav-collections: --config --vs
```

Now the next thing that remains is to figure out how we can extract the mandatory options 
(an oxymoron if there was one.) 
let us see how much we can do with wadm itself.


```
namespace eval Fs {
    variable commands
    variable options
    proc init {} {
        array set Fs::commands {}
        array set Fs::options {}
        foreach {cmd} [info commands list-\*] {
            catch {$cmd} err
{% raw %}
            set line [replace [lindex [split $err "\\n"] 1] {{\^ +or +[a-z-]+} {\\[.+\\]} {=[a-z-]+} {\^ +}}]
{% endraw %}
            regsub -all -- {\\( \*([a-z=-]+) \*\\| \*([a-z=-]+) \*\\)} $line {\\1} line
            set Fs::commands($cmd) $line
        }
        parseopt
        show
    }

    proc replace {var lst} {
        foreach l $lst { regsub -all -- $l $var {} var }
        return $var
    }

    proc default_opts {c} {
        #if the next statement does not throw, it is what we are looking for.
        set req $Fs::commands(list-[set c]s)
        set Fs::options($c) $c
    }

    proc parseopt {} {
        array set undefopt {}
        foreach {c} [array names Fs::commands] {
            set os [replace $Fs::commands($c) {--}]
            foreach {o} $os {
                set undefopt($o) $c
            }
        }
        foreach {c} [array names undefopt] {
            if [catch "default_opts $c" err] {
                puts "=> $err"
            }
        }
    }

    proc show {} {
        foreach o [array names Fs::options] {
            puts "$o => $Fs::options($o)"
        }
    }
}
```


#### Using It

```
> source fs.tcl            
> Fs::init                 
=> can't read "Fs::commands(list-modules)": no such element in array
=> can't read "Fs::commands(list-collection-uris)": no such element in array
=> can't read "Fs::commands(list-uri-prefixs)": no such element in array
=> can't read "Fs::commands(list-realms)": no such element in array
=> can't read "Fs::commands(list-jndi-names)": no such element in array
=> can't read "Fs::commands(list-providers)": no such element in array
=> can't read "Fs::commands(list-vss)": no such element in array
http-listener => http-listener
module => lifecycle-module
uri => reverse-proxy-uri
config => config
collection => dav-collection
realm => auth-realm
provider => soap-auth-provider
group => group
authdb => authdb
```

Looking at the  things that are not there, there seems to be a pattern,
if the option is xxxx, then there seems to be a command list-yyy-xxxxs.
that is if option is module, the command is list-lifecycle-modules. So adding 
that also to our script.

```
namespace eval Fs {
    variable commands
    variable options
    proc init {} {
        array set Fs::commands {}
        array set Fs::options {}
        foreach {cmd} [info commands list-\*] {
            catch {$cmd} err
{% raw %}
            set line [replace [lindex [split $err "\\n"] 1] {{\^ +or +[a-z-]+} {\\[.+\\]} {=[a-z-]+} {\^ +}}]
{% endraw %}
            regsub -all -- {\\( \*([a-z=-]+) \*\\| \*([a-z=-]+) \*\\)} $line {\\1} line
            set Fs::commands($cmd) $line
        }
        parseopt
        show
    }

    proc replace {var lst} {
        foreach l $lst { regsub -all -- $l $var {} var }
        return $var
    }

    proc default_opts {c cmd} {
        #if the next statement does not throw, it is what we are looking for.
        set req $Fs::commands(list-[set c]s)
        set Fs::options($c) $c
    }

    proc second_opts {c cmd} {
        #check if the following is true
        #if option is xxxx then command is list-yyyy-'xxxxs'$
        foreach {cmd} [info commands list-\*[set c]s] {
            if {![catch {set req $Fs::commands($cmd)} err]} {
{% raw %}
                set Fs::options($c) [replace $cmd {{list-} {s$}}]
{% endraw %}
                return
            }
        }
        error "$c does not match for $cmd."
    }

    proc final_opts {c cmd} {
        puts "$c does not match for $cmd."
    }

    proc parseopt {} {
        array set undefopt {}
        foreach {c} [array names Fs::commands] {
            set os [replace $Fs::commands($c) {--}]
            foreach {o} $os {
                set undefopt($o) $c
            }
        }
        foreach {c} [array names undefopt] {
            foreach {cmd} {default_opts second_opts final_opts} {
                if {![catch "$cmd $c $undefopt($c)" err]} {
                    break
                }
            }
        }
    }

    proc show {} {
        foreach o [array names Fs::options] {
            puts "$o => $Fs::options($o)"
        }
    }
}
```

Here We are trying to use three methods, default_opts second_ops, final_opts in an attempt
to match the options. The default_opts and second_opts tries to find a corresponding list command
while final_opts acts as a guard. If it reaches there, then our heuristics did not work. 

The reason for such a scheme is that it makes it easy to add new procedures.

#### Using It

```
> source fs.tcl
> Fs::init     
collection-uri does not match for list-locks.
uri-prefix does not match for list-reverse-proxy-headers.
jndi-name does not match for list-custom-resource-userprops.
vs does not match for list-dav-collections.
http-listener => http-listener
module => lifecycle-module
uri => reverse-proxy-uri
config => config
collection => dav-collection
realm => auth-realm
provider => soap-auth-provider
group => group
authdb => authdb
```

Of the four remaining, we notice more patterns,
if an option is of the form --firstword-secondword, then there is a good chance
that there is a list command of the form list-xxx-yyy-'firstword's
Including this heuristics again in our engine.

The modification to fs.tcl will be:

```
proc third_opts {c cmd} {
    #extract the first word eg: 
    #--uri-prefix # => uri and match it with uris$ =: list-reverse-proxy-uris
    #--collection-uri => collection and match with colections$ =: list-dav-collections
    second_opts [replace $c {-[a-z]+$}] cmd
}
proc parseopts {} {
 .....
      foreach {cmd} {default_opts second_opts third_opts final_opts} {
 ....
}
```


#### Using It.

```
> source fs.tcl
> Fs::init     
jndi-name does not match for list-custom-resource-userprops.
vs does not match for list-dav-collections.
http-listener => http-listener
module => lifecycle-module
uri => reverse-proxy-uri
config => config
collection => dav-collection
realm => auth-realm
provider => soap-auth-provider
group => group
authdb => authdb
```

Of the remaining the jndi-name can be included with one more rule.

```
> info commands list-\*jndi\*
list-external-jndi-resources list-external-jndi-resource-userprops
```

ie, if a command starts with list- and is not the same command that missed it,
and contains the first word of option and does not end in userprops, and the remaining
is just one then it is a good candidate. Adding this logic results in just one option left out.

```
--vs => list-virtual-servers
```

since there does not seem to be any connection between the option and the corresponding 
list, we will simply add an option to override the associated commands when needed, and
add this.

```
namespace eval Fs {
    variable commands
    variable options
    variable default_options
    proc init {} {
        array set Fs::commands {}
        array set Fs::options {}
        array set Fs::default_options {vs virtual-server}

        foreach {cmd} [info commands list-\*] {
            catch {$cmd} err
{% raw %}
            set line [replace [lindex [split $err "\\n"] 1] {{\^ +or +[a-z-]+} {\\[.+\\]} {=[a-z-]+} {\^ +}}]
{% endraw %}
            regsub -all -- {\\( \*([a-z=-]+) \*\\| \*([a-z=-]+) \*\\)} $line {\\1} line
            set Fs::commands($cmd) $line
        }
        parseopt
        #overriding the options.
        array set Fs::options [array get Fs::default_options]
        show
    }

    proc replace {var lst} {
        foreach l $lst { regsub -all -- $l $var {} var }
        return $var
    }

    proc default_opts {c cmd} {
        #if the next statement does not throw, it is what we are looking for.
        set req $Fs::commands(list-[set c]s)
        set Fs::options($c) $c
    }

    proc second_opts {c cmd} {
        #check if the following is true
        #if option is xxxx then command is list-yyyy-'xxxxs'$
        foreach {cm} [info commands list-\*[set c]s] {
{% raw %}
            set Fs::options($c) [replace $cm {{list-} {s$}}]
{% endraw %}
            return
        }
        error "$c does not match for $cmd."
    }

    proc third_opts {c cmd} {
        #extract the first word eg: 
        #--uri-prefix # => uri and match it with uris$ =: list-reverse-proxy-uris
        #--collection-uri => collection and match with colections$ =: list-dav-collections
        second_opts [replace $c {-[a-z]+$}] cmd
    }

    proc fourth_opts {c cmd} {
        #extract the first word.
        regexp {\^[a-z]+} $c first
        #if option is xxxx then command is list-yyyy-'xxxx'-zzzs$
        set opt {}
        foreach {cm} [info commands list-\*[set first]\*] {
            if {![string compare $cmd $cm]} {
                #we are the same command.
                continue
            }
            if [regexp {userprops$} $cm] {
                #ends with userprops
                continue
            }
            if {[string length $opt]} {
                error "$c:$cmd fourth opt bags more than one."
            }
{% raw %}
            set opt [replace $cmd {{list-} {s$}}]
{% endraw %}
        }
        if {![string length $opt]} {
            error "$c:$cmd not even one option"
        }
        set Fs::options($c) $opt
    }

    proc final_opts {c cmd} {
        if {![info exists Fs::default_options($c)]} {
            puts "$c does not match for $cmd."
        }
    }


    proc parseopt {} {
        array set undefopt {}
        foreach {c} [array names Fs::commands] {
            set os [replace $Fs::commands($c) {--}]
            foreach {o} $os {
                set undefopt($o) $c
            }
        }
        foreach {c} [array names undefopt] {
            foreach {cmd} {default_opts second_opts third_opts fourth_opts final_opts} {
                if {![catch "$cmd $c $undefopt($c)" err]} {
                    break
                }
            }
        }
    }

    proc show {} {
        foreach o [array names Fs::options] {
            puts "$o => $Fs::options($o)"
        }
    }
}
```


##### Using it

```
> source fs.tcl
> Fs::init     
http-listener => http-listener
module => lifecycle-module
uri => reverse-proxy-uri
config => config
collection => dav-collection
realm => auth-realm
jndi-name => custom-resource-userprop
provider => soap-auth-provider
group => group
authdb => authdb
vs => virtual-server
```


The hard work is mostly over, all we need to do now is to implement the commands
ls, pwd, cd
for a reasonable approximation of a filesystem.


#### The path representation.

We will use the following for path.

```
> <option-commandname>:<option-value>|<option-commandname>:option-value| etc....>
```

in EBNF, it will be
("|" <option-commandname> ":" <option-value> )\* ">"
For this, it is easier to just save the path as a list containing <optcmdname>, <value> multiple times
and convert to the representation when the need arises.


#### The pwd

```
proc pwd {} {
    set p ""
    foreach {c v} $Fs::pwd { set p "$p|$c:$v" }
    return $p
}
```

### The ls

We need to know if we are currently in an option or in a value.
option_folder will return true if we are on an option. ie
if pwd => {config} it will return true, but 
pwd => {config test} will return false
The in_current_folder is also important. It checks to see if the command really
belongs to this folder (if all the required options are defined, and also that 
the command really needs all the options defined now. if either of conditions is
false then it is not in current folder.)

```
proc in_current_folder {c} {
   set params $Fs::commands($c)
   foreach {opt -} $Fs::pwd {
        #=> config: :test vs: :mexico
        if {![regsub -all -- "--[get_opt $opt]" $params {} params]} { 
            #match failed, it is in one of parent/different folders.
            return 0
        }
    }
    return [expr [llength $params] == 0]
}

proc option_folder {} {
    return [expr [llength $Fs::pwd] % 2]
}

proc option_folder {} {
    return [expr [llength $Fs::pwd] % 2]
}

proc cmd_name cmd {
    return "list-[set cmd]s"
}

proc sane_cmd_name c {
    return [replace $c {\{\^list-} {s$}}]
}

proc get_opt opt {
    if [info exist Fs::options($opt)] {
        return $Fs::options($opt)
    } else {
        return $opt
    }
}

proc options {c} {
    set cmd $Fs::commands($c)
    foreach {opt val} $Fs::pwd {
        regsub -all -- "--[get_opt $opt]" $cmd "--[get_opt $opt]=$val" cmd
    }
    return $cmd
}

proc ls args {
    set out {}
    if [option_folder] {
        #show values for only this command.
        set c [cmd_name [lindex $Fs::pwd end]]
        set out [concat $out [lsort [eval "$c [options $c]"]]]
    } else {
        foreach {c} [array names Fs::commands] {
            if [in_current_folder $c] {
                lappend out [sane_cmd_name $c]
            }
        }
    }

    #output.
    foreach {l} [lsort $out] { puts $l }
}
```

We also need cd to check it out


##### The cd

```
proc cd {arg} {
    #config:test
    #config:mexico
    switch -regexp -- $arg {
        {\\.\\.} {
            pop_pwd
            unset_last_wadm_var
        }
        {\\.} {
            puts $Fs::pwd
        }
        default {
            push_pwd $arg
            set_wadm_var
       }
    }
    return
}
```


The complete implementation is available [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/fs.tcl)

##### Using It

```
> source fs.tcl
> Fs::init     
> interp alias {} cd {} Fs::cd 
cd
>interp alias {} ls {} Fs::ls
ls
>ls
config
node
>cd config
>
> config:>ls
apache-temp
emxico
security
test
> config:>cd test
> config:>ls
acl
auth-realm
authdb
cert
cgi-envvar
config-file
crl
custom-resource
event
external-jndi-resource
http-listener
instance
jdbc-resource
jvm-option
jvm-profiler
lifecycle-module
mail-resource
mime-type
soap-auth-provider
token
virtual-server
> config:test>cd http-listener
> config:test>ls
http-listener-1
newlist
> config:test|http-listener:>ls port=\*99
newlist
> config:test|http-listener:>info vars wadm_\*
wadm_histfile wadm_user wadm_config wadm_password wadm_savehist wadm_mode wadm_prompt
> config:test|http-listener:>cd ..
> config:test|http-listener:>
> config:test>cd ..
> config:test>
> config:>
```

As you can see you can even list by the properties (where get-xxx-prop is available for the option xxx
if it is not available you will get an error.)
More over it will also set and unset the corresponding wadm_xxx vars for each directory traversed.

the finished [fs.tcl](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/fs.tcl)
