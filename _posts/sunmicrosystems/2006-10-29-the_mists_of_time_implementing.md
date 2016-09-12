---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm X) The mists of time - implementing cron
title: (wadm X) The mists of time - implementing cron
---

There are many times when you would want to do some sequence of actions periodically. Such as renewing your certificates, rotating the logs bring up and bringing down instances and virtual servers based on day and time etc.

Most people run the Webserver in some kind of unix which means  that they already have and are familiar with a utility that will help them do just that, the crontab.

The Sun Java System Web Server 7.0 also ships with an event scheduler that will help you set up these actions that will be  repeated in the time frame that you specify. One of the reasons for the  scheduler getting integrated into the Webserver was that we wanted to provide an administrative interface to the scheduling facility. 

Since sometimes the Webserver administrators may not be the sysadmins for the machine in which the server runs on, and also because the setting up of cron in unix required access to the machine itself, It was better to  provide a scheduler that was different from the machine cron that was  specific to the Webserver alone. 

Though the current Scheduler in Webserver does have an administrative remote interface now, a small short coming is that inorder to allow any kind of complex action (Any thing that requires a condition or a dependecy) you still need access to the machine in which the Webserver runs (over and  above administrative access to the Webserver). This is because the only  way you can do such things is to write it in shell script and then schedule
that shell script to run.

While it would have been a great idea to provide callbacks from the  Scheduler to the wadm, it is not there currently (Unfortunately). 

Moreover, you can not schedule events across the cluster but are restricted to a particular configuration for each event.

{% raw %}
```
> create-event __Usage: create-event --help|-?
  or create-event [--echo] [--no-prompt] [--verbose] [--no-enabled] --config=name
  --command=restart|reconfig|rotate-log|rotate-access-log|update-crl|commandline
  ( (--time=hh:mm [--month=1-12] [--day-of-week=sun/mon/tue/wed/thu/fri/sat]
  [--day-of-month=1-31]) | --interval=60-86400(seconds) )
  CLI014 config is a required option.
```
{% endraw %}

Because it is running on the webserverd, it also means that it is machine specific
(ie) the command line specified would run once in each machine. while it is desirable
in some cases, it is not so in others where you just want to execute a command cluster 
wide.

let us see how much wadm will be able to help us in this matter.


##### Deciding on the API

We will try and have some similarity with the crontab, also it will be nice to make the
API look like a procedure that gets executed on time.


{% raw %}
```
on name "\* \* \* \* \* \*" {
         if {certs-expired} {
                 renew-selfsigned-cert
         }
         rotate-logs
         cleanup
}
```
{% endraw %}

Implementation

{% raw %}
```
namespace eval Cron {
    variable units
    variable schedule
    proc on {name time script} {
        array set schedule [parse_time $time]
        set schedule(script) $script
        set Cron::schedule($name) [array get schedule]
        persist
        return {}
    }

    proc init {} {
        set Cron::units {second minute hour day_of_month month day_of_week}
    }

    proc parse_time time {
        array set parsed {}
        set time [validate $time]
        foreach unit $Cron::units value $time {
            set parsed($unit) $value
        }
        return [array get parsed]
    }
    proc persist {} {
    }
    proc validate {time} {
        return $time
    }
}
```
{% endraw %}


{% raw %}
```
> source cron.tcl                      
> Cron::on mexico "\* \* \* \*" { puts blue }
> Cron::init                           
second minute hour day_of_month month day_of_week
> Cron::on blue "\* \* \* \*" { puts true}
> puts $Cron::schedule(blue)
hour \* script { puts true } day_of_week {} second \* day_of_month \* month {} minute \*
```
{% endraw %}

We have set aside the validation and persistance for later. They are not 
strictly needed for simple operations.


##### Scheduling

Now we need to find a way to get these to be invoked periodicaly, and Tcl provides
just what we want in the form of after command.

{% raw %}
```
> after
wrong # args: should be "after option ?arg arg ...?"
```
{% endraw %}

The arguments of the after are the number of milliseconds to wait and the procedure
to run after that wait. so adding the after command to our script,


{% raw %}
```
variable id
proc start {} {
    run [clock seconds]
    catch {after cancel $Cron::id} err
    set Cron::id [after 1000 Cron::start]
}

proc run {now} {
    foreach id [array names Cron::schedule] {
        puts "$id $now"
    }
}
```
{% endraw %}

Here we print each scheduled entry with 1 second periodicity.
all it remains to do is to change the puts to invocation after determining
if the schdedule matches to the current time.

Checking it out.

{% raw %}
```
> source cron.tcl                      
> Cron::init                           
second minute hour day_of_month month day_of_week
> Cron::on blue "\* \* \* \*" { puts true}
> Cron::start                          
blue 1162126366
blue 1162126367
blue 1162126368
```
{% endraw %}

Matching the time.
Now we need to match the scheduled time for each id, and invoke
it if the time matches the current.


##### A bug

Unfortunately due to a bug in jacl implementation of tcl, the list entered directly
in the console which contains new lines is used with the newlines stripped out,
ie:

{% raw %}
```
> puts {
a
b
c
}
abc
```
{% endraw %}

while in tclsh

{% raw %}
```
tclsh>puts {
a
b
c
}
a
b
c
```
{% endraw %}

Due to this reason, when you enter scripts, you will have to terminate each line by a ';'


##### Minimal Cron


{% raw %}
```
namespace eval Cron {
    variable units
    variable schedule
    variable id
    variable fmt

    set Cron::units {second minute hour day_of_month month day_of_week}
    set Cron::fmt {%S %M %H %d %m %w}

    foreach u $Cron::units f $Cron::fmt {
        eval "proc $u {time} { clock format \\$time -format $f }"
    }

    proc on {name time script} {
        set Cron::schedule($name) [concat [parse_time $time] "script {$script}"]
        return {}
    }

    proc parse_time time {
        array set parsed {}
        foreach unit $Cron::units value $time {
            if [llength $value] {
                set parsed($unit) $value
            } else {
                set parsed($unit) \*
            }
        }
        return [array get parsed]
    }

    proc start {} {
        run [clock seconds]
        catch {after cancel $Cron::id} err
        set Cron::id [after 1000 Cron::start]
    }

    proc run {now} {
        foreach id [array names Cron::schedule] {
            runone $id $now
        }
    }

    proc runone {id now} {
        array set time $Cron::schedule($id)
        foreach unit $Cron::units {
            if {![includes $time($unit) [$unit $now]]} { 
                return 
            }
        }
        if [catch {eval $time(script)} err] {
            puts "Error($id):$err"
        }
    }

    proc includes {lst var} {
        regsub {\^0+(.+)$} $var {\\1} var
        foreach p $lst {
            if {[lsearch -glob $var $p] > -1} {
                return 1
            }
        }
        return 0
    }
}
```
{% endraw %}

#### Some shortcuts.

##### You may have noticed this line

{% raw %}
```
foreach u $Cron::units f $Cron::fmt {
    eval "proc $u {time} { clock format \\$time -format $f }"
}
```
{% endraw %}

where I am making use of the tcl's dynamic evaluation capabilities
to create similar procedures in a loop. It allows us to abstract further
and reduce duplication of code.


##### Using it

{% raw %}
```
> source cron.tcl           
> Cron::on blue \* {         
:puts one;
:puts two;
:puts three;
:}
> Cron::start
one
two
three
one
two
three
```
{% endraw %}

As noted above, please insert the ';' to terminate each lines.,


##### Persistance

Because we are dealing with tcl, the data always has a string representaion
that can be used to recreate the data. so all it takes us to implement persistance 
is

{% raw %}
```
proc persist {} {
    set f [open $Cron::ifile w]
    puts $f [array get Cron::schedule]
    close $f
}
proc init {} {
   catch {
        set f [open $Cron::ifile r]
        array set Cron::schedule [read -nonewline $f]
        close $f
    } err 
    start
    return {}
}
```
{% endraw %}

We just write the Cron::schedule to a file '.cron.wadm' and
read it back when we startup.

The completed cron with validation and listing is available [here](http://rahul.gopinath.org/sunblog/2006/10/blue/resource/cron.tcl)
I have removed the seconds part from the cron since it is not very useful 
except during debugging.

##### Using It


{% raw %}
```
> source cron.tcl  
> Cron::init
> Cron::on blue \* {
:puts 1
:}
1
1
1
1
> Cron::stop
> Cron::ls
blue
> Cron::ls -l
blue => hour \* day_of_week \* second \* day_of_month \* month \* minute \* script {puts 1}
> Cron::on newblue {{0 1} 1} {
:puts mex;                 
:puts mee;
:}
> Cron::rm blue
> Cron::ls -l               
newblue => hour \* day_of_week \* second {0 1} day_of_month \* month \* minute \* script {puts mex;puts mee;}
....
mex
mee
mex
mee
```
{% endraw %}

I have removed the seconds part from the cron since it is not very useful 
except during debugging.

{% raw %}
```
> source cron.tcl  
> Cron::init       
> Cron::on blue \* {
:puts here;
:}
> Cron::ls -l
blue => hour \* day_of_week \* day_of_month \* month \* minute \* script {puts here;}
here
here
```
{% endraw %}

The completed cron is available [here](/resources/sunmicrosystems/cron.tcl)
