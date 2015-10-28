#select { $ip ,$response , $request } from {agneyam}
#select { $ip ,$response , $request ,$agent  } from {agneyam vaishnavam} where {$response == 200}
#select { $ip , [:sum {1}] , $request } from agneyam where {$response == 200}
#select { $ip , [:sum $size], [:sum {1}] , $request } from agneyam where {$response == 200} group by {$ip}

source date.tcl
namespace eval Logs {
    namespace export {select}
    variable fmt
    array set fmt {}
    set fmt(ip) 0
    set fmt(auth) 2
    set fmt(date) 3
    set fmt(request) 5
    set fmt(response) 6
    set fmt(size) 7

    variable results
    variable context

    proc use_sum {_id val} {
        upvar 1 ip ip
        upvar 1 auth auth
        upvar 1 date date
        upvar 1 request request
        upvar 1 response response
        set id [subst $_id]
        if [info exists Logs::results($id)] {
            set Logs::results($id) "$Logs::results($id) $val"
        } else {
            set Logs::results($id) $val
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

    proc exec_select {select from where group} {
        set collect 0
        #check if we have grouping statements in select (:sum)
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
            regsub -nocase -all {:([a-zA-Z]+) } $select {use_\1 [incr use_id]:$id } use_select
            regsub -nocase -all {:([a-zA-Z]+) } $select {collect_\1 [incr use_id]:$id } collect_select
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

    proc eval_select {line select} {
        upvar 1 use_id use_id
        upvar 1 collect collect
        upvar 1 group group
        upvar 1 id id
        set result [subst_in_context $line $select]
        if {$collect == 0} {
            puts $result
        } else {
            #save context
            set Logs::context($id) $line
        }
    }

    proc subst_in_context {line statement} {
        upvar 1 use_id use_id
        upvar 1 id id
        upvar 1 group group
        set ip [lindex $line $Logs::fmt(ip)]
        set auth [lindex $line $Logs::fmt(auth)]
        set date [lindex $line $Logs::fmt(date)]
        set request [lindex $line $Logs::fmt(request)]
        set response [lindex $line $Logs::fmt(response)]
        set size [lindex $line $Logs::fmt(size)]
        return [subst $statement]
    }

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
    #=============================================================
    # collate access logs across instances of a config


    proc compare-dates {line1 line2} {
        return [Date::Compare [lindex $line1 $Logs::fmt(date)] [lindex $line2 $Logs::fmt(date)]]
    }

    proc get-log {machine} {
        return [get-no-first [get-access-log --config test $machine]]
    }

    proc get-no-first {log} {
        return [lrange $log 2 end]
    }

    #requirements - Date::SetFormat is set correctly,
    #All the logs have same header format

    proc interleave-logs {args} {
        set fmt [Date::GetFormat]
        Date::SetFormat {\[DD/MMM/YYYY:T24S}
        set logs {}
        foreach machine $args {
            set log [get-log $machine]
            set logs [concat $logs $log]
        }
        set sorted [lsort -command compare-dates $logs]
        Date::SetFormat $fmt
        return $sorted
    }

}

