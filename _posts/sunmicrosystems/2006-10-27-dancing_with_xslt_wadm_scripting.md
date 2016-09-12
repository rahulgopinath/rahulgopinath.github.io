---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: (wadm IX) Dancing with XSLT
title: (wadm IX) Dancing with XSLT
---

Though generally wadm returns data as a tcl list that can be directly used, there are
multiple instances where more interesting data are made available as Xml. 

Eg:

{% raw %}
```
> get-stats-xml --config=test --node=agneyam
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE stats SYSTEM "sun-web-server-stats_7_0_0.dtd">
<stats versionMajor="1" versionMinor="2" enabled="1">
    <server id="https-test" versionServer="Sun Java System Web Server 7.0-Technology"  .... >
        <connection-queue id="cq1"/>
        <thread-pool id="thread-pool-0" name="NativePool"/>
        <thread-pool id="thread-pool-1" name="TestPool"/>
        <profile id="profile-0" name="all-requests" description="All requests"/>
        <profile id="profile-1" name="default-bucket" description="Default bucket"/>
        <profile id="profile-2" name="cache-bucket" description="Cached responses"/>
......
</stats>
```
{% endraw %}

Moreover the main configuraion file is also in xml.

{% raw %}
```
> get-config-file --config=test server.xml
<?xml version="1.0" encoding="UTF-8"?>
<server>
...
</server>
```
{% endraw %}

There may be times when the normal manipulation of configuration using wadm just dont
cut it and you may wish to manipulate the server.xml directly.


##### Asking TCL to help

Looking at the tcl syntax and the xml syntax again, we see that the xml looks pretty similar
infact An xml is nothing but a hierarchy of lists. (This is nothing new, and has been beaten to
death by the lisp folks -- the other language that uses lists as the mainstay.)

We can represent an xml like this

{% raw %}
```
            <thread mode="idle" timeStarted="1161917015" connection-queue="cq1">
                <request-bucket countRequests="0" countBytesReceived="0" countBytesTransmitted="0"/>
                <profile-bucket profile="profile-0" countCalls="0" />
                <profile-bucket profile="profile-1" countCalls="0" />
                ABCD
            </thread>
```
{% endraw %}

in tcl syntax as a list as below

{% raw %}
```
         thread { :mode "idle" :timestarted "1161917015" :connection-queue "cq1"
                  request-bucket { :countRequests "0" :countBytesReceived "0" :countBytesTransmitted "0"
                                           profile-bucket { :profile "profile-0" :countCalls "0"
                                          }
                                           profile-bucket {:profile "profile-1" :countCalls "0"
                                          }
                  }
                  % {ABCD}
         }
```
{% endraw %}


There are multiple packages available in tcl that can parse the xml ([this](http://wiki.tcl.tk/11020) being one of 
them), but it is not necessary for us to take that approach. When the language is xml,
it is needlessly complicated to parse the xml on our own, instead, It would be nice
if there is some tool that would allow us to just specify what we want and where, 
and convert the xml to that format. In short a macro expander.

There is a language that fits the bill. [XSLT](http://rahul.gopinath.org/sunblog/2006/10/27/dancing_with_xslt_wadm_scripting/www.w3.org/TR/xslt)

##### XSLT

Using XSLT we can transform the xml into tcl source. It allows all the necessary primitives

* Fetch the values of elements and attributes
* Recursively iterate over xml
* Compute results and process conditionaly when necessary.


##### First try.

Let us try and match all the elements.

{% raw %}
```
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" encoding="UTF-8"/>

    <xsl:template match="\*">
        <xsl:value-of select="name()"/>
        {
        <xsl:apply-templates select="\*"/>
        }
    </xsl:template>
</xsl:stylesheet>
```
{% endraw %}


##### The infrastructure.

transform.tcl

{% raw %}
```
namespace eval Transform {
    java::import javax.xml.parsers.SAXParserFactory
    java::import javax.xml.transform.Source
    java::import javax.xml.transform.TransformerFactory
    java::import javax.xml.transform.Transformer
    java::import javax.xml.transform.stream.StreamSource
    java::import javax.xml.transform.stream.StreamResult
    java::import javax.xml.transform.sax.SAXSource
    java::import org.xml.sax.XMLReader
    java::import java.io.File
    java::import java.io.ByteArrayOutputStream
    java::import java.io.ByteArrayInputStream

    set xsl {<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>
    <xsl:template match="\*">
        <xsl:value-of select="name()"/>
        {
        <xsl:apply-templates select="\*"/>
        }
    </xsl:template>
</xsl:stylesheet>
}

    proc get_source {reader arg} {
        set stream [java::new ByteArrayInputStream [[java::new String $arg] getBytes]]
        set source [java::new StreamSource $stream]
        return [java::new SAXSource $reader [java::call SAXSource sourceToInputSource $source]]
    }

    proc xslt {xml} {
        set  pfactory [java::call SAXParserFactory newInstance]
        $pfactory setValidating 0
        set reader [[$pfactory newSAXParser] getXMLReader]
        set trans [java::call TransformerFactory newInstance]
        set xsl_trans [$trans newTransformer [get_source $reader $Transform::xsl]]
        set bo [java::new ByteArrayOutputStream]
        $xsl_trans transform [get_source $reader $xml] [java::new StreamResult $bo]
        return [$bo toString]
    }
}
```
{% endraw %}

{% raw %}
```
> source xslt.tcl                                              
> Transform::xslt [get-stats-xml --config test --node agneyam]
ERROR:  'Content is not allowed in prolog.'
ERROR:  'com.sun.org.apache.xml.internal.utils.WrappedRuntimeException: Content is not allowed in prolog.'
javax.xml.transform.TransformerException: javax.xml.transform.TransformerException: com.sun.org.apache.xml.internal.utils.WrappedRuntimeException: Content is not allowed in prolog.
```
{% endraw %}

Now, this means that we wont be able to use the xml directly, We need to strip out the starting and
ending blank lines, the DocType tag (to avoid validation) etc.

Cleaning up the xml file,

{% raw %}
```
    proc clean_xml in {
        set out {}
        regsub {<!DOCTYPE [\^>]+>} $in {} _out
        foreach {line} [split $_out "\\n"] {
            switch -regexp -- $line {
                {\^$} {} ;#strip blanks.
                default { append out $line "\\n" }
            }
        }
        #some command return xml with in a list 
        #ugly but we dont have an option.
        if {[llength $out] == 1} {
            set out [lindex $out 0]
        }
        return $out
    }
```
{% endraw %}

{% raw %}
```
> source xslt.tcl                                             
> Transform::xslt [get-stats-xml --config test --node agneyam]
....
    cpu-info
        {
        }
    cpu-info
        {
        }
        }
        }
```
{% endraw %}

Seems to be working..
Checking if it is the syntax we are interested in,

{% raw %}
```
> array set stats_root [Transform::xslt [get-stats-xml --config test --node agneyam]]
> array names stats_root                                                             
stats
> array set stats $stats_root(stats)
> array names stats
server
> array set server $stats(server)
> array names server
auth-db audit-accesses connection-queue profile cpu-info http-listener access-log temp-path thread-pool log acl-file jvm default-auth-db-name process http cluster virtual-server mime-file user
```
{% endraw %}

The tcl list still needs more things to make it completely representative of the xml it parsed.
adding those to the xsl,

{% raw %}
```
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>

    <xsl:template match="@\*">
        :<xsl:value-of select="name()"/> "<xsl:value-of select="."/>"
    </xsl:template>
    <xsl:template match="\*">
        <xsl:value-of select="name()"/>
        {
        <xsl:apply-templates select="@\*"/>
        <xsl:apply-templates select="\*"/>
        <xsl:choose>
            <xsl:when test='string-length(translate(translate(text(),"&#10;","")," ","")) > 1'>
            % {<xsl:value-of select="translate(text(),'&#10;','')"/>}
            </xsl:when>
        </xsl:choose>
        }
    </xsl:template>
</xsl:stylesheet>
```
{% endraw %}

{% raw %}
```
> array set stats_root [Transform::xslt [get-stats-xml --config test --node agneyam]]
> array names stats_root                                                             
stats
> array set stats $stats_root(stats)                                                 
> array names stats                                                                  
:enabled :versionMajor server :versionMinor
> puts $stats(:enabled)
1
> array set names $stats(server)
> array names names
:secondsRunning connection-queue :load5MinuteAverage profile cpu-info :maxThreads 
:maxProcs thread-pool :rateBytesReceived :timeStarted :load15MinuteAverage 
process :load1MinuteAverage :id :rateBytesTransmitted :versionServer virtual-server 
:ticksPerSecond :flagProfilingEnabled
> puts $names(profile)
        :id "profile-2"
        :name "cache-bucket"
        :description "Cached responses"
```
{% endraw %}

While this seems to be fine, Accessing it through setting and accesssing arrays 
does not seem to be the friendliest or the most powerful approach,we should 
provide an API to access the values.


##### Creating an API.

What we need is an xpath like expression that allow arbitrary tcl statements to
be used for filtering. It should be some thing like below,

`{stats server {profile {~ \*1\* $id} }}`

where `stats/server/profile` is the node of the xml we are looking for, and 
`~ \*1\* $id` is the filter which will do a pattern match on the value of attribute 
with name id and return only those nodes that match what we provide.

{% raw %}
```
    #Filter returns true if either of following is satisfied.
    #1) the length of filter list is 0 (no filter)
    #the filter evaluates to true after setting the attributes
    #as variables
    proc filter {filter val} {
        if {![string length $filter]} {
            return 1
        } else {
            #transform ->:id "mexico"<- into ->set id "mexico"<-
            regsub -all {:([a-zA-Z0-9_-]+) } $val {set \\1 } val
            foreach {v} [split $val "\\n"] {
                eval $v
            }
            return [eval $filter]
        }
    }

    #collect all elements of name where filter evaluates to true
    proc fetch_alist {xml name {filter {}}} {
        set res {}
        foreach {n v} $xml {
            if [string match $n $name] {
                if [filter $filter $v] { lappend res $v }
            }
        }
        return $res
    }

    proc helper {lst res} {
        set rest [lrange $lst 1 end]
        if {![llength $rest]} {
            return $res
        } else {
            set out {}
            foreach {r} $res {
                set out [concat $out [get $r $rest]]
            }
            return $out
        }
    }

    proc get {xml lst} {
        set res $xml
        set element [lindex $lst 0]
        switch -exact -- [llength $element] {
            1 {
                #name alone. no filter
                #collect the corresponding lists from $xml
                set res [fetch_alist $res $element]
                return [helper $lst $res]
            }
            default {
                #use filter too.
                set res [fetch_alist $res [lindex $element 0] [lindex $element 1]]
                return [helper $lst $res]
            }
        }
    }
```
{% endraw %}



##### Using It,

(The regexp command is aliased to ~ and string match is aliased to ? -- see full implementation.)

{% raw %}
```
> set xml [Transform::xslt [get-stats-xml --config test --node agneyam]]
> Transform::get $xml {stats server {profile {~ 1 $id} }}
{
        :id "profile-1"
        :name "default-bucket"
        :description "Default bucket"
        }
> Transform::get $xml {stats server {profile {? \*1\* $id} }}
{
        :id "profile-1"
        :name "default-bucket"
        :description "Default bucket"
        }
> Transform::get $xml {stats server {profile {? \* $id} }}  
{
        :id "profile-0"
        :name "all-requests"
        :description "All requests"
        } {
        :id "profile-1"
        :name "default-bucket"
        :description "Default bucket"
        } {
        :id "profile-2"
        :name "cache-bucket"
        :description "Cached responses"
        }
```
{% endraw %}

The finished transform.tcl is available [here](./resources/sunmicrosystems/transform.tcl)
I will cover using Xpath to access the same data in a later post.
