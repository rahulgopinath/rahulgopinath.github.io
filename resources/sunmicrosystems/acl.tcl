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
        set Acl::acl($name) [list "acl \"$name\";\n"]
        set Acl::curacl $name
    }
    #|namespace eval Acl $acls
    #invalid command name "authenticate"

    proc authenticate {args} {
        set authargs [lindex $args 0]
        set rest [lrange $args 1 end]
        lappend Acl::acl($Acl::curacl) "authenticate $authargs $rest;\n\n"
    }

    proc ts {arg} {
        if {![regexp {(and|or) *$} $arg ]} {
            return ";\n"
        } else {
            return ""
        }
    }
    
    proc allow {args} {
        lappend Acl::acl($Acl::curacl) "allow $args\n"
    }
    
    proc deny {args} {
        lappend Acl::acl($Acl::curacl) "deny $args\n"
    }

    proc user {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur user $args[ts $args]\n"]
    }
    
    proc ip {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur ip $args[ts $args]\n"]
    }
    
    proc dns {args} {
        set cur [lindex $Acl::acl($Acl::curacl) end]
        set Acl::acl($Acl::curacl) [lreplace $Acl::acl($Acl::curacl) end end "$cur dns $args[ts $args]\n"]
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
        set new [lreplace $cur 0 0 "acl \"$new\";\n"]
        set cur $Acl::acl($old)
    }

    proc get {acl} {
        set cur $Acl::acl($acl)
        #set text "version 3.0;\n"
        set text ""
        foreach {cmd} $cur {
            set text "$text$cmd"
        }
        return $text
    }

    proc put {acl pos rule} {
        if {![regexp {; *$} $rule]} {
            error "End rule with a ';'"
        }
        if {!$pos} {
            puts "Cant change the name."
            return
        }
        set cur $Acl::acl($acl)
        set new [lreplace $cur $pos $pos "$rule\n"]
        set Acl::acl($acl) $new
    }

    proc add {acl rule} {
        if {![regexp {; *$} $rule]} {
            error "End rule with a ';'"
        }
        set cur $Acl::acl($acl)
        set new [lappend cur "$rule\n"]
        set Acl::acl($acl) $new
    }

    proc remove {acl pos} {
        set cur $Acl::acl($acl)
        set new [lreplace $cur $pos $pos]
        set Acl::acl($acl) $new
    }

    proc text {args} {
        set text "version 3.0;\n\n"
        if {[llength $args]} {
            set text "$text \n[Acl::get $args]"
        } else {
            foreach {name} [array names Acl::acl] {
                set text "$text \n[Acl::get $name]"
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
