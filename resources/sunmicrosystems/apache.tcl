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
        regsub -all {\">} $text {\" >} text

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
        set popd [lindex  $Apache::stack end]
        set Apache::stack [lrange $Apache::stack 0 end-1]
        return $popd
    }

    proc invoke arg {
        set word [lindex $arg 0]
        switch -regexp $word {
            {^ *</.*} {
                if {[regexp {^ *< */([^ ]+) *> *$} $arg all one]} {
                    set p [pop_stack]
                    invoke_proc $p -exit
                }
                return
            }

            {^ *<.*} {
                if {[regexp {^ *<([^ ]+) *(.*)> *$} $arg all one rest]} {
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
    #       The Engine
    #==================================================

    proc IfModule args {
        set arg [lindex $args 0]
        switch -- [lindex $arg 0] {
            {-init} {
                set cur [lindex $arg 1]
                #check if it is of type !xxxx , if it is take the reverse.
               if {[regexp {^ *!([^ ]+)$} $cur all one] } {
                    | "if {!\[info exist Apache::module($one)\]}  {" ;#}
                } else {
                    | "if \[info exist Apache::module($cur)\]  {" ;#}
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
        | set-virtual-server-prop --config $Apache::info(config) --vs $Apache::info(default_vs) \
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
        | enable-htaccess --config $Apache::info(config) --vs $Apache::info(default_vs) \
            --config-file $af
    }

    proc AddType args {
        set type [lindex $args 0]
        set ext [join [lrange $args 1 end] ","]
        regsub -all {\.} $ext {} ext
        | create-mime-type --config $Apache::info(config) --extensions $ext $type
    }

    proc DefaultType args {
        #this does not have an equivalent in sjswebsrever.
    }

    proc Alias args {
        set alias [lindex $args 0]
        set fs [lindex $args 1]
        | create-document-dir --config $Apache::info(config) --uri-prefix $alias \
            --directory $fs --vs $Apache::info(default_vs)
    }

    proc CgiAlias args {
        set alias [lindex $args 0]
        set fs [lindex $args 1]
        | create-cgi-dir --config $Apache::info(config) --uri-prefix $alias \
            --directory $fs --vs $Apache::info(default_vs)
    }

    proc TypesConfig args {
        set mf [lindex $args 0]
        | set-config-prop --config $Apache::info(config) mime-file=$mf
    }

    proc LoadModule args {
        set Apache::module([lindex $args 0]) [lrange $args 1 end]
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
            eval "| create-http-listener --config $Apache::info(config) \
                     --listener-port $port $ipprop \
                    --server-name $Apache::info(server_name) \
                    --default-virtual-server-name $Apache::info(default_vs) \
                    $ipprop $lst"

            set Apache::info(http-listener-cur) $lst
        } else {
            set ipprop ""
            if [string length $ip] {
                set ipprop "ip=$ip"
            }
            eval "| set-http-listener-prop --config $Apache::info(config) \
                    --http-listener $lst port=$port $ipprop"
        }
    }


}
