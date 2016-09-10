---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm II) More wadm
title: wadm in  Sun Java System Web Server 7.0 (part II)
---
### Log in to your wadm shell

The rest of the tutorial assumes that you are on the wadm shell.

## Global Variables

The wadm shell behaves differently depending on the values of a few wadm variables.
(They all start with **wadm_** by the way)

### A little exploring with tcl

Try typing these into the wadm shell

```
> info vars wadm_\*
wadm_histfile wadm_script wadm_debug wadm_savehist wadm_mode wadm_prompt
```

These are the variables that are defined by default when you enter the wadm. Let us see the values of each,

#### first try:

```
> foreach i [info vars wadm_\*] {puts $i}
wadm_histfile
wadm_script
wadm_debug
wadm_savehist
wadm_mode
wadm_prompt
```

This gave you the variables in a pretty printed format. Now to get the values..

```
> foreach i [info vars wadm_\*] { puts $i=[set $i] }
wadm_histfile=/home/myhome/.wadm_history
wadm_script=false
wadm_debug=false
wadm_savehist=false
wadm_mode=shell
wadm_prompt=true
```

We wont bother with the debug, here. but here are the explanations for rest of variables.

`wadm_script` allows you to return tcl lists from the administration commands (By default they do not return any thing). So it is a good habit to set this to true before you do any thing. We will deal with setting up a good rc file later, where you can set it to true by default. Now for the purposes of this tutorial, set it to true like this:

```
> set wadm_script true
```

`wadm_histfile` tells us where the history file will be stored and under what name.

`wadm_savehist` controlls whether the history will be saved at all. This is also disabled by default due to security considerations. But if you are not logging in to the wadm shell from a public terminal, it is better to leave it on.

```
> set wadm_savehist true
```

`wadm_mode` is a variable that tells us a little about how we were invoked. It can have these values: *(single | file | shell)*
When a wadm command is invoked directly with out using the shell the mode is set to single.
ie: 

```
$ wadm create-config --config=test1
```

It is set to file when we invoke the script using the -f option to wadm 
ie: 

```
$ wadm -f create-mime.tcl newspiffymime mime.ext
```

(assuming create-mime.tcl is a script file that you have written, and it is present in the current directory.)


It is set to shell mode, when we are on the wadm shell (as we are on now.)

`wadm_prompt` is used by some of the commands to decide if the user should be prompted for any confirmation. You will find this info in the help for those commands.

### Setting up the `.wadmrc` file with some nice entries

Since we are on with it, let us do that through wadm.
The file name is `.wadmrc`, and it is to be placed in your home directory. The wadm knows about the home directory as much as you do. It is stored in an array variable called env. Try:

```
> array names env
```

This will give you all the environmental variables that wadm knows about. To get the value of home, try

```
> puts $env(HOME)
/home/myhome
```

Now to open your .wadmrc file:

```
> set file [open "$env(HOME)/.wadmrc" w]
```

Here you are asking the jacl to open the .wadmrc file in 'w' mode (which is 'write') and assign the result to a variable called file.

Now to write some thing to it:

```
> puts $file "set wadm_script true"</span>
> puts $file "set wadm_savehist true"
```

As you can see, the $file contains the file object (channel in tcl land), on to which we are writing our strings.

I also like to set the user, password and the port to which I will connect to.

```
> puts $file "set wadm_user admin"
> puts $file "set wadm_password adminadmin"
```

Yes you noticed it correctly, there is no need to use a password file so long as you are inside the wadm shell, it will take the `wadm_password` as a `wadm_*` variable. This is one of the few brownie points you get when using wadm shell.

```
> puts $file "set wadm_port 1893"
```

It is nice to have a default config on which all commands are run. (That way I dont have to specify the --config option)

```
> puts $file "set wadm_config myconfig"
```

And ofcource, no shell is complete with out some ability to customize the prompt!

first a tiny procedure to get the prompt string dynamically.

```
> puts $file {proc var {var} {return $var}}
> puts $file {set tcl_prompt1 "var |"}
> puts $file {set tcl_prompt2 "var :"}
```

As you can see, using '{}' is another way of quoting a string, which is in effect telling the jacl to leave the contents alone.

We are mostly set. so let us release the file (channel)

```
> close $file
```

Just to verify we have done it correctly, (assuming you are on a unix system,) let us ask the system to print it out.

```
$ cat $env(HOME)/.wadmrc
set wadm_script true
set wadm_savehist true
set wadm_user admin
set wadm_password adminadmin
set wadm_port 1893
set wadm_config myconfig
proc var {var} {return $var}
set tcl_prompt1 "var |"
set tcl_prompt2 "var :"
```

As you can see, tcl allows you to execute the system commands also from with in.

But we can also go about it in a slightly different fashion:

```
> set f [open $env(HOME)/.wadmrc r]
> read -nonewline $f
set wadm_script true
set wadm_savehist true
set wadm_user admin
set wadm_password adminadmin
set wadm_port 1893
set wadm_config myconfig
proc var {var} {return $var}
set tcl_prompt1 "var |"
set tcl_prompt2 "var :"
> close $f
```

This should have printed your current .wadmrc to the screen.

If you want, you can make this into a procedure and place it inside your .wadmrc

```
proc wcat {fname} {
    set f [open $fname "r"]
    set data [read -nonewline $f]
    close $f
  return $data
}
```

which can be invoked as 
```
> wcat $env(HOME)/.wadmrc</span>
```

## Looking at what else is available

the info command comes to our help again.
try this:

```
> info help
bad option "help": must be args, body, cmdcount, commands, complete, default, exists, globals, hostname, level, library, loaded, locals, nameofexecutable, patchlevel, procs, script, sharedlibextension, tclversion, or vars
```

There is no subcommand named help for info, but it does print what are the allowed subcommands.
We are interested in the 'commands' right now, so let us see what it contains.

```
> info commands
```

There! it gives us all the commands that the wadm supports. This is useful in many ways. Suppose you want to do an operation related to mime, here is how you find what operations are supported with mime.

```
> info commands \*mime\*
delete-mime-type create-mime-type list-mime-types
```

You can explore further to see what else the info command will give you.

## Implementing a filter for mimes.

The mime operations that are provided are pretty nice, but there is a small functionality missing, There is no direct way for the user to see if the particular mime alone that he is interested in. But since we have the wadm in our hands, we can always add this on our own.

Open a file called filtermime.tcl and add this.

```
proc filter-mime {filter config vs} {
  #incantation to the wadm deity.
  set ::wadm_script true
  #get the list of mimes
  set mimes [list-mime-types --config $config --vs $vs]
  #the actual engine. Iterate the list $mimes, with each mime in $mime.
  #The $mime variable is a list that contains two parts. The first part
  #has the mime definition, and the second part has extension.
  #eg {application/pdf pdf}
  #eg {application/postscript ai,eps,ps}
  #so we extract just the first portion alone with the [lindex $mime 0]
  #and match that against the $filter using the regexp command.
  foreach mime $mimes {
    if {[regexp $filter [lindex $mime 0]]} {
      puts $mime
    }
  }
}
```

You can load it into the current environment like this:

```
> source filtermime.tcl
```

and invoke it this way:

```
> filter-mime "text" myconfig myvs
```

with the myconfig and myvs replaced with appropriate values, you should be seeing a list of all mimes that has 'text' in them.


### Default options

wadm shell supports setting options in variables which gets used by default.
ie,
type this on the wadm shell, ('tab' for completion)

```
> create-virtual-server --document-root=/ myvs
Usage: create-virtual-server ... --config=name --document-root=path virtual-server-name
CLI014 config is a required option.
```

now, try doing this.

```
> set wadm_config test
```

and try again

```
> create-virtual-server --document-root=/ myvs
CLI201 Command 'create-virtual-server' ran successfully
```

As you can see, the `wadm_config` corresponds to `--config`. It is the same with all the options passed to the wadm commands. You can convert an option to its corresponding wadm variable by appending `wadm_` to it and changing any hyphens (-) to underscores (_).

This should have given you an idea about what can be done with wadm. 
I will explore more advanced topics next time.

