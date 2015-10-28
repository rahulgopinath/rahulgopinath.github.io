namespace eval Fs {
    variable commands
    variable default_options
    variable options
    variable pwd
    variable verbose

    proc init {} {
        array set Fs::commands {}
        array set Fs::options {}
        array set Fs::default_options {vs virtual-server}
        set Fs::pwd {}
        set Fs::verbose 0

        foreach {cmd} [info commands list-*] {
            catch {$cmd} err
            set line [replace [lindex [split $err "\n"] 1] {{^ +or +[a-z-]+} {\[.+\]} {=[a-z-]+} {^ +}}]
            regsub -all -- {\( *([a-z=-]+) *\| *([a-z=-]+) *\)} $line {\1} line
            set Fs::commands($cmd) $line
        }
        parseopt
        #overriding the options.
        array set Fs::options [array get Fs::default_options]

        set ::tcl_prompt1 {Fs::prompt}
        return
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
        foreach {cm} [info commands list-*[set c]s] {
            set Fs::options($c) [replace $cm {{list-} {s$}}]
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
        regexp {^[a-z]+} $c first
        #if option is xxxx then command is list-yyyy-'xxxx'-zzzs$
        set opt {}
        foreach {cm} [info commands list-*[set first]*] {
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
            set opt [replace $cmd {{list-} {s$}}]
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

    proc pwd {} {
        set p ""
        foreach {c v} $Fs::pwd { set p "$p|$c:$v" }
        return $p
    }

    proc option_folder {} {
        return [expr [llength $Fs::pwd] % 2]
    }

    proc cmd_name cmd {
        return "list-[set cmd]s"
    }

    proc sane_cmd_name c {
        return [replace $c {{^list-} {s$}}]
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

    #Given a command c, it checks if the command belongs in the current pwd
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

    proc cmd_filter {opt elem} {
        return "get-[replace $opt {{^list-} {s$}}]-prop --[get_opt [current_folder]] $elem [options $opt]"
    }

    proc fill_pat var {
        if {![string length $var]} { 
            return "*" 
        } else { 
            return $var 
        }
    }
    proc v {num var} {
        if {$Fs::verbose >= $num} {
            puts $var
        }
    }

    proc v+ {} {
        incr Fs::verbose
    }

    proc v- {} {
        set Fs::verbose [expr $Fs::verbose - 1]
    }

    proc filter_cmd {cmd filter} {
        if {![string length $filter]} {
            return 1
        }
        regexp {^([^=]+)=(.+)$} $filter all fname fval
        foreach {prop} [eval $cmd] {
            set name [lindex $prop 0]
            set value [lindex $prop 1]
            v 2 "[lindex $cmd end] => $name:$value"
            if [expr [string match -nocase [fill_pat $fname] $name]] {
                if [string match -nocase [fill_pat $fval] $value] {
                    v 1 "Match: [lindex $cmd end] => $name:$value"
                    return 1
                } else {
                    return 0
                }
            }
        }
        return 0
    }

    proc filter_by_property {c filter} {
        set out {}
        foreach {r} [lsort [eval "$c [options $c]"]] {
            if [filter_cmd [cmd_filter $c $r] $filter] {
                lappend out $r
            }
        }
        return $out
    }


    proc ls args {
        set filter [lindex $args 0]
        set out {}
        if [option_folder] {
            #show values for only this command.
            set c [cmd_name [lindex $Fs::pwd end]]
            set out [filter_by_property $c $filter]
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

    proc pop_pwd {} {
        set Fs::pwd [lrange $Fs::pwd 0 end-1]
    }
    
    proc push_pwd {arg} {
        lappend Fs::pwd $arg
    }

    proc current_folder {} {
        return [lindex $Fs::pwd end]
    }

    proc to_wadm_var {v} {
        regsub -all -- {-} $v {_} var
        return wadm_$var
    }

    proc set_wadm_var {} {
        #check if we are even. If we are, then define the wadm_vars.
        if {![option_folder]} {
            foreach {var val} $Fs::pwd {
                set ::[to_wadm_var $var] $val
            }
        }
    }

    proc unset_last_wadm_var {} {
        #unset the last wadm_xx variable if we are even.
        regsub -all -- {-} [current_folder] {_} var
        if [option_folder] { catch {unset ::[to_wadm_var [current_folder]]} err }
    }

    proc cd {arg} {
        #config:test
        #config:mexico
        switch -regexp -- $arg {
            {\.\.} {
                pop_pwd
                unset_last_wadm_var
            }
            {\.} {
                puts $Fs::pwd
            }
            default {
                push_pwd $arg
                set_wadm_var
           }
        }
        return
    }

    proc prompt {} {
        return "[pwd]>"
    }
}
