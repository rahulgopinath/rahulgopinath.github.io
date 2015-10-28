# date.tcl
# Date 2.9 package
#

# SetDateFormat must be called to tell the package what format
# the dates are in.
#    Date::SetFormat   DateFormat 
#    Date::Compare     Date1       Date2
#    Date::Adjust      Date        Adjustment
#    Date::Today       ?relative?
#    Date::Now
#    Date::WeekDay     Date        S|L|N
#    Date::Day         Date        S|L
#    Date::Month       Date        S|L|N
#    Date::Year        Date        L|S
#    Date::Convert     Date        Format
#    Date::Apart       Date1       Date1
#    Date::Seconds     DateApart
#    Date::Parse       DateString
#    Date::GetFormat

package provide DatePkg 2.9

namespace eval Date {
  namespace export SetFormat GetFormat Compare Adjust Now Today Convert Apart Seconds Parse
  namespace export WeekDay Month Year

  set TheFormat ""
  set InFormat ""
  set OutFormat ""
  set Result ""

  array set WeekDays [list sunday 0 monday 1 tuesday 2 wednesday 3 thursday 4 friday 5 saturday 6]

# ----------------------------------------------- DateSetFormat ----
proc SetFormat { DateFormat } {
  variable InFormat
  variable OutFormat
  variable Result
  variable TheFormat

  # specify a date time format with the following denominators
  # YYYY - year with century
  #   YY - year without century
  #  MMM - Shortform of month
  #   MM - Month as digit
  #   DD - Day of month
  #  DDD - Short day of week
  # DDDD - long day of week
  #  T24 - 24 hour clock
  # T24S - 24 hour clock with seconds
  #  T12 - 12 hour clock
  # T12S - 12 hour clock with seconds
  #    m - meridian (AM/PM) indicator

  # create the input format string for grep substring matching
  set InFmt $DateFormat
  regsub MMM $InFmt {([a-zA-Z]+)} InFmt
  regsub MM $InFmt {([0-9]?[0-9])} InFmt
  regsub DDDD $InFmt {([a-zA-Z]+)} InFmt
  regsub DDD $InFmt {([a-zA-Z]+)} InFmt
  regsub DD $InFmt {([0-9]?[0-9])} InFmt
  regsub YYYY $InFmt {([0-9][0-9][0-9][0-9])} InFmt
  regsub YY $InFmt {([0-9][0-9])} InFmt
  regsub T24S $InFmt {([0-2][0-9]:[0-5][0-9]:[0-5][0-9])} InFmt
  regsub T24 $InFmt {([0-2][0-9]:[0-5][0-9])} InFmt
  regsub T12S $InFmt {([0-1][0-9]:[0-5][0-9]:[0-5][0-9])} InFmt
  regsub T12 $InFmt {([0-1][0-9]:[0-5][0-9])} InFmt
  regsub m $InFmt {([aApP][Mm])} InFmt
  set InFormat "$InFmt.*"

  # need to be able to break up each part
  set tempFmt $DateFormat
  regsub m $tempFmt {(m)} tempFmt

  regsub MMM $tempFmt {(mmm)} tempFmt
  regsub MM $tempFmt {(MM)} tempFmt
  regsub {\(mmm\)} $tempFmt {(MMM)} tempFmt

  regsub DDDD $tempFmt {(dddd)} tempFmt
  regsub DDD $tempFmt {(ddd)} tempFmt
  regsub DD $tempFmt {(DD)} tempFmt
  regsub {\(dddd\)} $tempFmt {(DDDD)} tempFmt
  regsub {\(ddd\)} $tempFmt {(DDD)} tempFmt

  regsub YYYY $tempFmt {(yyyy)} tempFmt
  regsub YY $tempFmt {(YY)} tempFmt
  regsub {\(yyyy\)} $tempFmt {(YYYY)} tempFmt

  regsub T24S $tempFmt {(t24s)} tempFmt
  regsub T24 $tempFmt {(T24)} tempFmt
  regsub {\(t24s\)} $tempFmt {(T24S)} tempFmt

  regsub T12S $tempFmt {(t12s)} tempFmt
  regsub T12 $tempFmt {(T12)} tempFmt
  regsub {\(t12s\)} $tempFmt {(T12S)} tempFmt

  # create the format for tcl clock scanning
  set temp "none"
  regsub $tempFmt $DateFormat {\1 \2 \3 \4 \5 \6 \7 \8 \9} temp
  set Month [lsearch $temp "MMM"]
  incr Month
  if {$Month == 0} then {
    set Month [lsearch $temp "MM"]
    incr Month
    set MonthName 0
  } else {
    set MonthName 1
  }
  set Day [lsearch $temp "DD"]
  incr Day
  set Year [lsearch $temp "YYYY"]
  incr Year
  if {$Year == 0} then {
    set Year [lsearch $temp "YY"]
    incr Year
  }
  set Time [lsearch $temp "T24S"]
  incr Time
  if {$Time == 0} then {
    set Time [lsearch $temp "T24"]
    incr Time
  }
  if {$Time == 0} then {
    set Time [lsearch $temp "T12S"]
    incr Time
  }
  if {$Time == 0} then {
    set Time [lsearch $temp "T12"]
    incr Time
  }
  if {$Time == 0} then {
    set Time ""
   }
  set TimeAMPM [lsearch $temp "m"]
  incr TimeAMPM
  if {$TimeAMPM == 0} then {
    set TimeAMPM ""
  }
  if {$Time != ""} then {
    set Time "\\$Time"
  }
  if {$TimeAMPM != ""} then {
    set TimeAMPM "\\$TimeAMPM"
  }
# need different formats if numerical month or word month
  if {$MonthName == 1} then {
    set Result [string trim "\\$Month \\$Day, \\$Year $Time$TimeAMPM"]
  } else {
    set Result [string trim "\\$Month/\\$Day/\\$Year $Time$TimeAMPM"]
  }

  # create the display format string using tcl clock paramaters
  set OutFmt $DateFormat
  regsub m $OutFmt {%p} OutFmt
  regsub MMM $OutFmt {%b} OutFmt
  regsub MM $OutFmt {%m} OutFmt
  regsub DDDD $OutFmt {%A} OutFmt
  regsub DDD $OutFmt {%a} OutFmt
  regsub DD $OutFmt {%d} OutFmt
  regsub YYYY $OutFmt {%Y} OutFmt
  regsub YY $OutFmt {%y} OutFmt
  regsub T24S $OutFmt {%H:%M:%S} OutFmt
  regsub T24 $OutFmt {%H:%M} OutFmt
  regsub T12S $OutFmt {%I:%M:%S} OutFmt
  regsub T12 $OutFmt {%I:%M} OutFmt
  set OutFormat $OutFmt

  set TheFormat $DateFormat

  return ""
}

# --------------------------------------------------- GetFormat ----
proc GetFormat { } {
  variable TheFormat
  return $TheFormat
}

# ------------------------------------------------- DateCompare ----
proc Compare { Date1 Date2 } {
# Input:   Date1 and Date2 in Date Format specified by DateSetFormat
# Output:  -1  Date1 < Date2
#           0  Date1 = Date2
#           1  Date1 > Date2

  variable InFormat
  variable Result

# convert the date string to MMM DD, YYYY (TTTT)? format
  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  regsub -nocase "$InFormat" "$Date2" "$Result" Da2

# convert the dates to numbers
  set D1 [clock scan "$Da1"]
  set D2 [clock scan "$Da2"]

# return the result
  return [expr ($D1 > $D2) - ($D1 < $D2)]
}

# ------------------------------------------------- DateAdjust ----
proc Adjust { DateIn Modifier } {
# Input:  DateIn    - a starting date in the format specified by
#                     DateSetFormat
#         Modifier  - a string to adjust the date/time.
#                     adjustments are performed accurate to the
#                     second, but the DateSetFormat specified may
#                     result in this accuracy being discarded.
#                     i.e. If you adjust by 2 hours, but only show
#                     the dates, then the hours are lost.

  variable InFormat
  variable OutFormat
  variable Result
  variable WeekDays

# strip out the days and weeks. they need to be adjusted GMT
  set Mods [string tolower $Modifier]
  set Ago ""
  regexp -nocase  "(.*)(ago)" [string trim $Modifier] dummy Mods Ago

  set GMTMods ""
  set LocalMods ""

  # create the Local Time Zone mods
  foreach unitname [list second hours month year] {
     if {[regexp "(-?\[0-9]+) +(${unitname}s?)" $Mods dummy num unit]} then {
       append LocalMods " $num $unit"
     }
  }
  # create the GMT Time Zone mods
  foreach unitname [list minute day week] {
     if {[regexp "(-?\[0-9]+) +(${unitname}s?)" $Mods dummy num unit]} then {
       append GMTMods " $num $unit"
     }
  }
  if {[string length [string trim $LocalMods]] > 0} then {
    append LocalMods " $Ago"
  }
  if {[string length [string trim $GMTMods]] > 0} then {
    append GMTMods " $Ago"
  }

  set Date1 $DateIn
  # days of week mods wich are also GMT mods
  foreach unitname [list sunday monday tuesday wednesday thursday friday saturday] {
    if {[regexp "($unitname)" $Mods dummyAll day]} then {
      regsub -nocase "$InFormat" "$Date1" "$Result" Da1
      set AdjDay [expr $WeekDays($unitname) - [clock format [clock scan "$Da1"] -format "%w"]]
      if {$AdjDay >= 0} then {
        set NewTime [clock scan "$Da1 $AdjDay days" -gmt 1]
      } elseif {$AdjDay < 0} then {
        set NewTime [clock scan "$Da1 [expr abs($AdjDay)] days ago" -gmt 1]
      }
      set Date1 [clock format $NewTime -format "$OutFormat" -gmt 1]
    }
  }

# convert the date string to MMM DD, YYYY (TTTT)? format
  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  set NewTime [clock scan "$Da1 $GMTMods" -gmt 1]
  set NewSTR [clock format $NewTime -format "$OutFormat" -gmt 1]
  regsub -nocase "$InFormat" "$NewSTR" "$Result" Da1
  set NewTime [clock scan "$Da1 $LocalMods"]
  return [clock format $NewTime -format "$OutFormat"]
}

# ------------------------------------------------- DateToday ----
proc Today { args } {
# return the current data/time accurate to the format specified by
#   DateSetFormat
  
  variable InFormat
  variable OutFormat
  variable Result

  set theArg [lindex $args 0]
  if {$theArg == ""} then { set theArg 0 }
  return [clock format [clock scan "$theArg" -base [clock seconds]] -format "$OutFormat"]
}

# ------------------------------------------------- DateNow ----
proc Now { } {
# return the current data/time accurate to the format specified by
#   DateSetFormat
  
  variable InFormat
  variable OutFormat
  variable Result

  return [clock format [clock seconds] -format "$OutFormat"]

}
# ------------------------------------------------ WeekDay ----
proc WeekDay { Date1 args } {
# returns the day of the week. If the argument is included
# it specifies the format
#   s  - short 3 character (default)
#   l  - long  full name
#   n  - numeric

  variable InFormat
  variable Result

  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  set NewTime [clock scan "$Da1"]
  if {[llength $args] > 0} then {
    switch -- [string tolower [string range [lindex $args 0] 0 0]] {
      l { set RetStr [clock format $NewTime -format "%A"] }
      n { set RetStr [clock format $NewTime -format "%w"] }
      s -
      default { set RetStr [clock format $NewTime -format "%a"] }
    }
  } else {
    set RetStr [clock format $NewTime -format "%a"]
  }
  return $RetStr
}

# ------------------------------------------------------ Day ----
proc Day { Date1 args } {
# returns the day of the month. If the argument is included
# it specifies the format
#   s  - no leading 0 (default)
#   l  - 2 digit number

  variable InFormat
  variable Result

  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  set NewTime [clock scan "$Da1"]
  if {[llength $args] > 0} then {
    switch -- [string tolower [string range [lindex $args 0] 0 0]] {
      l { set RetStr [clock format $NewTime -format "%d"] }
      s -
      default { set RetStr [string trimleft [clock format $NewTime -format "%d"] "0 "]}
    }
  } else {
    set RetStr [string trimleft [clock format $NewTime -format "%d"] "0 "]
  }
  return $RetStr
}


# ---------------------------------------------------- Month ----
proc Month { Date1 args } {
# returns the month of the year. If the argument is included
# it specifies the format
#   s  - short 3 character (default)
#   l  - long  full name
#   n  - numeric

  variable InFormat
  variable Result

  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  set NewTime [clock scan "$Da1"]
  if {[llength $args] > 0} then {
    switch -- [string tolower [string range [lindex $args 0] 0 0]] {
      l { set RetStr [clock format $NewTime -format "%B"] }
      n { set RetStr [clock format $NewTime -format "%m"] }
      s -
      default { set RetStr [clock format $NewTime -format "%b"] }
    }
  } else {
    set RetStr [clock format $NewTime -format "%b"]
  }
  return $RetStr
}

# ---------------------------------------------------- Year ----
proc Year { Date1 args } {
# returns the year. If the argument is included
# it specifies the format
#   s  - short 2 digit year
#   l  - long  4 digit year (default)

  variable InFormat
  variable Result

  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  set NewTime [clock scan "$Da1"]
  if {[llength $args] > 0} then {
    switch -- [string tolower [string range [lindex $args 0] 0 0]] {
      s { set RetStr [clock format $NewTime -format "%y"] }
      l -
      default { set RetStr [clock format $NewTime -format "%Y"] }
    }
  } else {
    set RetStr [clock format $NewTime -format "%Y"]
  }
  return $RetStr
}

# ------------------------------------------------- DateConvert ----
proc Convert { Date1 FormatOut } {
# return the data/time currently in format specified by DateSetFormat
# as FormatOut
  
  variable InFormat
  variable OutFormat
  variable Result

# save the current format information
  set TempFormat [GetFormat]

# convert the date string to MMM DD, YYYY (TTTT)? format
  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  
  set D1 [clock scan "$Da1"]
  SetFormat "$FormatOut"
  set NewTime [clock format $D1 -format "$OutFormat"]
  
# restore the current format information
  SetFormat "$TempFormat"

  return "$NewTime"
}

# ------------------------------------------------- DateApart ----
proc Apart { Date1 Date2 } {
# return the the amount of time in
#  x days y hours z minuts s seconds
#  depending on the accuracy specified in DateSetFormat
  
  variable InFormat
  variable OutFormat
  variable Result

# convert the date string to MMM DD, YYYY (TTTT)? format
  regsub -nocase "$InFormat" "$Date1" "$Result" Da1
  regsub -nocase "$InFormat" "$Date2" "$Result" Da2

# convert the dates to numbers
  set D1 [clock scan "$Da1" -gmt 1]
  set D2 [clock scan "$Da2" -gmt 1]

  set TimeSign ""
  set Apart [expr $D2 - $D1]
  if {$Apart < 0} then {
    set TimeSign "ago"
    set Apart [expr abs($Apart)]
  }
# number of seconds in a day
  set Days [expr $Apart / 86400]
  set Apart [expr $Apart % 86400]
# number of seconds in an hour
  set Hours [expr $Apart / 3600]
  set Apart [expr $Apart % 3600]
# number of seconds in a minute
  set Minutes [expr $Apart / 60]
  set Seconds [expr $Apart % 60]

# assign expressions in the form null, 1 day, x days for each
  set Days [expr {$Days?[expr $Days==1?"$Days day":"$Days days"]:""}]
  set Hours [expr {$Hours?[expr $Hours==1?"$Hours hour":"$Hours hours"]:""}]
  set Minutes [expr {$Minutes?[expr $Minutes==1?"$Minutes minute":"$Minutes minutes"]:""}]
  set Seconds [expr {$Seconds?[expr $Seconds==1?"$Seconds second":"$Seconds seconds"]:""}]
# put it all together
  set WholeThing [string trim [join "$Days $Hours $Minutes $Seconds $TimeSign" " "]]
  if {"$WholeThing" == ""} then {
    return "0 seconds"
  } else {
    return $WholeThing
  }
}

# ------------------------------------------------- DateSeconds ----
# Given a date difference as returned by DateApart, convert it to
# total seconds
proc Seconds { Diff } {
  return [clock scan "[clock format 0 -format {%b %d, %Y %H:%M:%S}] $Diff"]
}

# ------------------------------------------------- DateParse ----
# Parse the date only string and generate a new one in the form
# of the DateFormat setting. If datestring is an invalid date, return a null.
proc Parse { datestring } {
  variable OutFormat

  regsub -all {[^A-Za-z0-9:]} $datestring " " newstring
  set newstring [string tolower [string trim $newstring]]
  set date(day) -1
  set date(month) -1
  set date(year) -1
  set date(monthDay) -1
  set date(monthWord) 0

# break apart adjacent items
  set datelist ""
  set Remainder $newstring
  while {[string length $Remainder] > 0} {
    set Item ""
    regexp {^ *([A-Za-z]+) *(.*)$} $Remainder dummy Item Remainder
    if {$Item == ""} then {
      regexp {^ *([0-9.:]+) *(.*)$} $Remainder dummy Item Remainder
    }
    lappend datelist $Item
  }

# remove the time element if it is present
  set timeIndex [lsearch -regexp $datelist ":"]
  if {$timeIndex == -1 } then {
    set TimeString ""
  } else {
    if { [regexp -nocase {^[ap]m$} [lindex $datelist [expr $timeIndex + 1]]]} then {
      set TimeString [lrange $datelist $timeIndex [expr $timeIndex + 1]]
      set datelist [lreplace $datelist $timeIndex [expr $timeIndex + 1] ]
    } else {
      set TimeString [lindex $datelist $timeIndex]
      set datelist [lreplace $datelist $timeIndex $timeIndex]
    }
  }

# go through each element
  set Max [llength $datelist]
  for {set count 0} { $count < $Max } {incr count} {
    if {[regexp {^[a-zA-Z]+$} [lindex $datelist $count] dummy]} then {
      # skip processing of week days
      if {[string match "*([string range "[lindex $datelist $count]" 0 2])*" "(jan)(feb)(mar)(apr)(may)(jun)(jul)(aug)(sep)(oct)(nov)(dec)"]} then {
        set date(month) $count
        set date(monthWord) 1
      }
    } elseif { [lindex $datelist $count] > 31 } then {
      set date(year) $count
    } elseif { [lindex $datelist $count] > 12 } then {
      set date(day) $count
    } elseif { $date(month) != -1 } then {
      set date(day) $count 
    } else {
      set date(monthDay) $count
    }
  }

# if either of month or day can be determined, the other must be the
# monthday value
  if {$date(monthDay) != -1} then {
    if {$date(month) != -1} then {
      set date(day) $date(monthDay)
    } elseif {$date(day) != -1} then {
      set date(month) $date(monthDay)
    }
  }

# if we can not be sure of the format, default to formats of
#    yyyy/mm/dd or mm/dd/yyyy all others have month as word.
  if {($date(month) == -1) || ($date(day) == -1)} then {
    if { $date(year) == 2 } then {
      set date(day) 1
      set date(month) 0
    } elseif {$date(year) == 0} then {
      set date(day) 2
      set date(month) 1
    } else {
      set date(day) 0
      set date(month) 2
    }
  }

  if {$date(monthWord) == 1} then {
    set myerror [catch {set theDate [clock scan "[lindex $datelist $date(month)] [lindex $datelist $date(day)], [lindex $datelist $date(year)] $TimeString"]}]
  } else {
    set myerror [catch {set theDate [clock scan "[lindex $datelist $date(month)]/[lindex $datelist $date(day)]/[lindex $datelist $date(year)] $TimeString"]}]
  }

  if {$myerror == 0} then {
    return [clock format $theDate -format "$OutFormat"]
  } else {
    return ""
  }
}

}
