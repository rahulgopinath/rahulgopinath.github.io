---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm III) ACL, Parse thyself
title: (wadm III) ACL, Parse thyself
---

The  Sun Java System Web Server contains a small language called ACL which defines the Access rules for each resource. (Access Control Lists). While very powerful, It is not very easy to manipulate the ACLS using the CLI in the raw form.

The only support that we have from CLI are these commands:

```
> info commands \*acl\*
set-acl list-acls delete-acl get-acl set-acl-cache-prop get-acl-cache-prop
```

Of which set-acl, list-acls, delete-acl, get-acl are the only commands that actualy work on ACL. As below.

```
> list-acls --config=test
default
es-internal
mexico

> get-acl --config=test
# File automatically written
version 3.0;

acl "default";
authenticate (user,group) {
        prompt = "Sun Java System Web Server";
};
allow (read,execute,info) 
    user = "anyone";
allow (list,write,delete) 
    user = "all";

acl "es-internal";
allow (read,execute,info) 
    user = "anyone";
deny (list,write,delete) 
    user = "anyone";

acl "mexico";
authenticate (user,group) {
        database = "default";
        method = "basic";
        prompt = "Hi there..";
};
deny (all) 
    user = "anyone";
allow (read,write,execute,delete,list,info) 
    user = "rahul" and
    ip = "129.158.223.\*,129.158.224.\*" or
    dns = "varunam,vayavyam,vaishnavam";
```

Now, the only command provided to change the acl is

```
> set-acl --config=test
Usage: set-acl --help|-?
  or   set-acl [--echo] [--no-prompt] [--verbose] [--vs=name] --config=name --aclfile=file
CLI014 aclfile is a required option.
```

While quite powerful, is hardly friendly.

It would be nice to have an option to fetch the acl, do the required changes using a friendlier API, and update it back.
But before getting to an API, we need to parse the ACL syntax.

## Parsing the ACL

We have multiple options when it comes to Parsing, Some are,

- Read in the complete as a text file, tokenize it and use rules to parse it.
- Notice that the language is simple and has only a few rules, so use regular expressions to extract the relevant data in each line.
- Massage the text a little bit so that it looks a little more like Tcl, and use Tcl to parse it.

Now all the above are equally valid, and you can do this in almost any other language. Languages like c++ or java usually take the first two approaches, 
since they do not have the option of using the language parser to do their bidding.

But dynamic laugnages like perl, ruby, python, scheme or factor allows you to make use of the language machinery to get the work done.
It is a more easier approach since the parsing is mainly done by the language, and the only thing you have to do is to slightly change the data so that it is 
parsable.

Tcl being Tcl, It allows us one more entertaining option:
*Massage the Tcl so that it looks a bit more like the ACL syntax* :)

### ACL Syntax (from a Tcl point of view)

In order to get the Tcl to parse ACL, we should be able to do this.

```
> set acls [get-acl --config=test]
> eval $acls
```

ie, the content of the variable $acls should be valid Tcl syntax.
Generally inorder to pull something like this off we would need to redefine the unknown procedure which
is called by tcl when it finds some thing it does not know about. But in this case, the syntax of the ACL does not
seem to be in need of any such gymnastics.

One of the interesting things that helps us here is that, the tcl is word oriented in that unless quoted by braces - {}
or by doubble quotes -"" any other tokens are interpreted as valid individual strings.. The quoted ones are interpreted as one single string.
ie:
`mycmd abc def ghi`
is interpreted as the command `mycmd` having three strings as arguments ie `"abc"` `"def"` `"ghi"`

Taking that a bit more,
`mycmd (abc, def, ghi)`
is interpreted as command mycmd taking 3 string arguments `"(abc"` `"def"` `"ghi)"`.
Notice how the brackets are interpreted as part of the string. This is very useful because we can define
`mycmd` as 

```
proc mycmd {args} {
       #process args as a list
       process $args
}
```

and inside the `mycmd` we can extract the original args from the list passed in.

#### Varargs

Notice the args paramenter, It is the way in which we can pass multiple arguments in tcl (like varargs in c/c++)
Tcl collects all arguments to the procedure in a list and places it in the '$args' variable if args is defined as the paramenter to the procedure.

#### Quotes

As you saw above, tcl does not really care about the string being unquoted, this gives us considerable freedom to mould the calling syntax as we wish.

#### Semicolons

Tcl uses ';' to specify command termination too.

#### Back to parsing

Now, it is not a very good idea to pollute the global namespace with all the Acl specific procedures that we are going to write, so let us create a namespace
of our own (open a file acl.tcl and copy the below in it,)

```tcl
namespace eval Acl {
}
```

and our aim becomes

```
> source acl.tcl
> namespace eval Acl $acls
```

ie, the acls are valid tcl inside the namespace of Acl.

```
> namespace eval Acl $acls
invalid command name "version"
```

We can start implementing each commands that the namespace eval complains about.
just define dummy procedures. We are not bothered about parsing any thing at this point of time.

acl.tcl:

```tcl
namespace eval Acl {
    proc version {ver} {}
    proc acl {name} {}
    proc authenticate {args}{}
    proc allow {args} {}
    proc deny {args} {}
    proc user {args} {}
    proc ip {args} {}
    proc dns {args} {}
}
```

```
> namespace eval Acl $acls
```

Well, that did it, The Acl is now valid TCL, though it does not really does not do any thing.


### First Parsing Procedures

```tcl
namespace eval Acl {
    variable ver {1.0}
    variable acl 
    variable curacl
    array set Acl::acl {}

    proc version {ver} {
        set Acl::ver $ver
    }

    proc acl {name} {
        set Acl::acl($name) ""
        set Acl::curacl $name
    }
   #snipped the rest of procedures.
}
```

As you can see, I used variable to declare that it is a part of the namespace. It is outside the scope of the procedures, and I can refer to them as
$namespace::variable.

#### version

eg: 

```
> version 3.0;
```

```tcl
proc version {ver} {
    set Acl::ver $ver
}
```

As soon as the version entry in acl is evaluated, it invokes the `version` command,
and we set the version inside the namespace scope. the semicolon is discarded by the tcl as it is a statement terminator.

#### acl

eg:

```
> acl "mexico";
```

```
proc acl {name} {
     set Acl::acl($name) [list "acl \\"$name\\";\\n"]
     set Acl::curacl $name
}
```

Next comes the Acl entry. It has just one string after it, which is interpreted as the argument, so we set the Acl being processed in the curacl variable.
We have also set the Acl::acl array value here to be a one element list. We will be appending to it in the coming procedures.

#### authenticate

eg:

```
> authenticate (user,group) {
    database = "default"
    method = "basic"
    prompt = "Hi There."
}
```

```tcl
proc authenticate {args} {
    set authargs [lindex $args 0]
    set rest [lrange $args 1 end]
    lappend Acl::acl($Acl::curacl) "authenticate $authargs $rest;\\n\\n"
}
```

As explained above, Tcl sees the statement (user,group) as one single string "(user,group)" and the one that comes after it is with in
the braces - {} which means that it is again a *single* string for Tcl. 
Had it not been this case, we would have had to write procedures for database, prompt and method, but as it is we are saved from that
effort.
`lindex` lets you extract a positional element from a list, and lrange does the same but returns a range.
`lappend` appends the given element to a list

#### allow

eg:

```
> allow (read,write)
```

```tcl
proc allow {args} {
    lappend Acl::acl($Acl::curacl) "allow $args\\n"
}
```

While the grammar of ACL does not put any restriction on the filter part of the allow and deny statement, we can take advantage of the fact
that while returning through wadm, it always separates out the allow, user, ip and dns into neatly separated lines.

#### deny

eg:

```
> deny (all)
```

```tcl
proc deny {args} {
    lappend Acl::acl($Acl::curacl) "deny $args\\n"
}
```

We could have abstracted out the above two procedures into one, but the pay offs are not that huge in this case.

#### user,ip and dns

eg:

```
user = "rahul" and
ip = "129.158.223.\*,129.158.224.\*" or
dns = "machine1,machine2,machine3";
```

```tcl
proc user {args} {
  set cur [lindex $Acl::acl($Acl::curacl) end]
  set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur user $args[ts $args]\\n"]
}

proc ip {args} {
  set cur [lindex $Acl::acl($Acl::curacl) end]
  set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur ip $args[ts $args]\\n"]
}

proc dns {args} {
  set cur [lindex $Acl::acl($Acl::curacl) end]
  set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur dns $args[ts $args]\\n"]
}
```

We dont really care about what they have as the arguemnts any way.


#### Sanity Check

Now that we have implemented these, let us run the eval and see the results in the `Acl::acl` array.

```
> source acl.tcl
> namespace eval Acl $acls
> puts [array names Acl::acl]
default mexico es-internal
```

Things seem to be working ok, Let us take one of them and see what it contains

```
> puts Acl::acl(mexico)
{acl "mexico";
} {authenticate (user,group) {
        database = "default";
        method = "basic";
        prompt = "Hi there..";
};
} {deny (all)
 user = anyone;
} {allow (read,write,execute,delete,list,info)
 user = rahul and
 ip = 129.158.223.\*,129.158.224.\* or
 dns = machine1,machine2,machine3;
}
```

Well, things seem nice enough. Now that we have parsed it, we need to access it, change it, and get the result back as a nice clean ACL.
Here is a skeleton of such an API along with the complete script. You can modify it to have an interface that you like.

acl.tcl:

```tcl
namespace eval Acl {
    variable ver {1.0}
    variable acl
    variable config
    variable curacl
    variable text
    array set Acl::acl {}

    proc version {ver} {
        set Acl::ver $ver
    }

    proc reset {} {
        array set Acl::acl {}
        set Acl::curacl {}
    }

    proc init {config} {
        set acls [get-acl --config $config]
        set Acl::config $config
        eval $acls
    }

    #puts [array names Acl::acl]
    proc acl {name} {
        set Acl::acl($name) [list "acl \\"$name\\";\\n"]
        set Acl::curacl $name
    }
    #> namespace eval Acl $acls
    #invalid command name "authenticate"

    proc authenticate {args} {
        set authargs [lindex $args 0]
        set rest [lrange $args 1 end]
        lappend Acl::acl($Acl::curacl) "authenticate $authargs $rest;\\n\\n"
    }

    proc ts {arg} {
        if {![regexp {(and|or) \*$} $arg ]} {
            return ";\\n"
        } else {
            return ""
        }
    }
    
    proc allow {args} {
        lappend Acl::acl($Acl::curacl) "allow $args\\n"
    }
    
    proc deny {args} {
        lappend Acl::acl($Acl::curacl) "deny $args\\n"
    }

    proc user {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur user $args[ts $args]\\n"]
    }
    
    proc ip {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur ip $args[ts $args]\\n"]
    }
    
    proc dns {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur dns $args[ts $args]\\n"]
    }

    proc show {acl} {
        set cur $Acl::acl($acl)
        set pos 0
        foreach cmd $cur {
            if {$pos} {
                puts "=========$pos============"
                puts $cmd
            }
            incr pos
        }
    }

    proc clone {old new} {
        set cur $Acl::acl($old)
        set new [lreplace $cur 0 0 "acl \\"$new\\";\\n"]
        set cur $Acl::acl($old)
    }

    proc get {acl} {
        set cur $Acl::acl($acl)
        #set text "version 3.0;\\n"
        set text ""
        foreach {cmd} $cur {
            set text "$text$cmd"
        }
        return $text
    }

    proc put {acl pos rule} {
        if {![regexp {; \*$} $rule]} {
            error "End rule with a ';'"
        }
        if {!$pos} {
            puts "Cant change the name."
            return
        }
        set cur $Acl::acl($acl)
        set new [lreplace $cur $pos $pos "$rule\\n"]
        set Acl::acl($acl) $new
    }

    proc add {acl rule} {
        if {![regexp {; \*$} $rule]} {
            error "End rule with a ';'"
        }
        set cur $Acl::acl($acl)
        set new [lappend cur "$rule\\n"]
        set Acl::acl($acl) $new
    }

    proc remove {acl pos} {
        set cur $Acl::acl($acl)
        set new [lreplace $cur $pos $pos]
        set Acl::acl($acl) $new
    }

    proc text {args} {
        set text "version 3.0;\\n\\n"
        if {[llength $args]} {
            set text "$text \\n[Acl::get $args]"
        } else {
            foreach {name} [array names Acl::acl] {
                set text "$text \\n[Acl::get $name]"
            }
        }
        return $text
    }
    proc save {args} {
        set txt "[text $args]"
        set fn "tmp.acl"
        set f [open $fn "w"]
        puts -nonewline $f $txt
        close $f
        set ret [set-acl --config $Acl::config --aclfile $fn ]
        file delete -force $fn
        return $ret
    }
}
```

### Using it:

Here, `#test` is the name of config. The evaulation is done by the `Acl::init` internaly.

```
> Acl::init test
> Acl::show mexico
=========1============
authenticate (user,group) {
        database = "default";
        method = "basic";
        prompt = "Hi there..";
};
=========2============
deny (all)
 user = anyone;
=========3============
allow (read,write,execute,delete,list,info)
 user = rahul and
 ip = 129.158.223.\*,129.158.224.\* or
 dns = varunam,vayavyam,vaishnavam;
```

The show prints out the numbers for use by later procedures.

Change the 3rd rule to allow (all) user = all;

```
> Acl::put mexico 3 {allow (all) user = all;}
> Acl::show mexico                           
=========1============
authenticate (user,group) {
        database = "default";
        method = "basic";
        prompt = "Hi there..";
};
=========2============
deny (all)
 user = anyone;
=========3============
allow (all) user = all;
```

Get the complete text

```
> Acl::text       
version 3.0;
 
acl "mexico";
authenticate (user,group) {
        database = "default";
        method = "basic";
        prompt = "Hi there..";
};

deny (all)
 user = anyone;

allow (all) user = all;
 
acl "default";
authenticate (user,group) {
        prompt = "Sun Java System Web Server";
};

allow (read,execute,info)
 user = anyone;

allow (list,write,delete)
 user = all;
 
acl "es-internal";
allow (read,execute,info)
 user = anyone;

deny (list,write,delete)
 user = anyone;
```

You can also make it specific to one acl.

```
> Acl::text default
version 3.0;
 
acl "default";
authenticate (user,group) {
        prompt = "Sun Java System Web Server";
};

allow (read,execute,info)
 user = anyone;

allow (list,write,delete)
 user = all;
```

Now, we need to set this back into a file and use that file name as an argument for `set-acl`. 

```
> Acl::save default
CLI201 Command 'set-acl' ran successfully
```

You can also do it with out the argument, in which case it will save the entire text in back to server.

```
> Acl::save
CLI201 Command 'set-acl' ran successfully
```

The finished acl.tcl is available [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/acl.tcl)
