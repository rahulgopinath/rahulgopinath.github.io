namespace eval Transform {
    variable self
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
    interp alias {} ~ {} regexp
    interp alias {} ? {} string match

    set xsl {<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>

    <xsl:template match="@*">
        :<xsl:value-of select="name()"/> "<xsl:value-of select="."/>"
    </xsl:template>
    <xsl:template match="*">
        <xsl:value-of select="name()"/>
        {
        <xsl:apply-templates select="@*"/>
        <xsl:apply-templates select="*"/>
        <xsl:choose>
            <xsl:when test='string-length(translate(translate(text(),"&#10;","")," ","")) &gt; 1'>
            % {<xsl:value-of select="translate(text(),'&#10;','')"/>}
            </xsl:when>
        </xsl:choose>
        }
    </xsl:template>
</xsl:stylesheet>
}

    proc get_source {reader arg} {
        set stream [java::new ByteArrayInputStream [[java::new String $arg] getBytes]]
        set source [java::new StreamSource $stream]
        return [java::new SAXSource $reader [java::call SAXSource sourceToInputSource $source]]
    }
    proc clean_xml in {
        set out {}
        regsub {<!DOCTYPE [^>]+>} $in {} _out
        foreach {line} [split $_out "\n"] {
            switch -regexp -- $line {
                {^$} {} ;#strip blanks.
                default { append out $line "\n" }
            }
        }
        #some command return xml with in a list 
        #ugly but we dont have an option.
        if {[llength $out] == 1} {
            set out [lindex $out 0]
        }
        return $out
    }


    proc xslt {xml} {
        set  pfactory [java::call SAXParserFactory newInstance]
        $pfactory setValidating 0
        set reader [[$pfactory newSAXParser] getXMLReader]
        set trans [java::call TransformerFactory newInstance]
        set xsl_trans [$trans newTransformer [get_source $reader $Transform::xsl]]
        set bo [java::new ByteArrayOutputStream]
        $xsl_trans transform [get_source $reader [clean_xml $xml]] [java::new StreamResult $bo]
        return [$bo toString]
    }

    proc filter {filter val} {
        if {![string length $filter]} {
            return 1
        } else {
            regsub -all {:([a-zA-Z0-9_-]+) } $val {set \1 } val
            foreach {v} [split $val "\n"] {
                eval $v
            }
            return [eval $filter]
        }
    }

    #see if filter evaluates to true.
    proc fetch_alist {xml name {filter {}}} {
        set res {}
        foreach {n v} $xml {
            if [string match $n $name] {
                if [filter $filter $v] {
                    lappend res $v
                }
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
}
