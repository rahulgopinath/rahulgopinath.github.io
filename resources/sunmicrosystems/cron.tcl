namespace eval Cron {
    variable units
    variable validrange
    variable months
    variable weeks
    variable fmt

    variable schedule
    variable id
    variable ifile

    set Cron::units {minute hour day_of_month month day_of_week}
    set Cron::validrange {v_60 v_hours_in_day v_days_in_month v_month v_week}
    set Cron::fmt {%M %H %d %m %w}

    set Cron::months {jan feb mar apr may jun jul aug sep oct nov dec}
    set Cron::weeks {mon tue wed thu fri sat sun}

    set Cron::ifile .cron.wadm


    foreach u $Cron::units f $Cron::fmt {
        eval "proc $u {time} { clock format \$time -format $f }"
    }

    proc on {name time script} {
        set Cron::schedule($name) [concat [parse_time $time] "script {$script}"]
        return {}
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

    proc ls args {
        foreach id [array names Cron::schedule] {
            expr {[llength $args] ? [puts "$id => $Cron::schedule($id)"] : [puts $id]}
        }
    }

    proc rm {name} {
        unset Cron::schedule($name)
    }

    proc persist {} {
        set f [open $Cron::ifile w]
        puts $f [array get Cron::schedule]
        close $f
    }

    proc stop {} {
        after cancel $Cron::id
    }

    proc parse_time time {
        validate $time
        array set parsed {}
        foreach unit $Cron::units value $time {
            if [llength $value] {
                set parsed($unit) $value
            } else {
                set parsed($unit) *
            }
        }
        return [array get parsed]
    }

    proc start {} {
        run [clock seconds]
        catch {after cancel $Cron::id} err
        set Cron::id [after 60000 Cron::start]
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
        regsub {^0+(.+)$} $var {\1} var
        foreach p $lst {
            if {[lsearch -glob $var $p] > -1} {
                return 1
            }
        }
        return 0
    }

    proc v_week val {
        if {![catch {vpos $Cron::weeks $val} err]} {
            return $err
        }
        if {![catch {v_num 1 7 $val} err]} {
            return $err
        }
        error "Out of range $Cron::weeks !~ $val"
    }

    proc v_month val {
        if {![catch {vpos $Cron::months $val} err]} {
            return $err
        }
        if {![catch {v_num 1 12 $val} err]} {
            return $err
        }
        error "Out of range $Cron::months !~ $val"
    }

    proc v_60 val {
        return [v_num 0 59 $val]
    }

    proc v_days_in_month val {
        return [v_num 1 31 $val]
    }

    proc v_hours_in_day val {
        return [v_num 0 23 $val]
    }

    proc v_num {a b val} {
        if [expr $val > $b] { error "Out of range $b < $val" }
        if [expr $val < $a] { error "Out of range $a > $val" }
        return $val
    }

    proc validate {time} {
        foreach {val} $time {func} $Cron::validrange  {
            switch -exact -- $val {
                {*} {}
                {} {}
                default {foreach v $val {$func $v}}
            }
        }
        return {}
    }

}

