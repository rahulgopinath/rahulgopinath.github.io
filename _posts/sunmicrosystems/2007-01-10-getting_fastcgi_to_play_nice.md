---
layout: post
tagline: "."
tags : [sunmicrosystems blog sun]
categories : sunblog
e: Getting FastCGI to play nice with ruby  (Sun Java System Web Server 7.0 )
title: Getting FastCGI to play nice with ruby  (Sun Java System Web Server 7.0 )
---

I have been trying to get the FastCGI to run ruby using the Sun Java System Web Server 7.0. Since
there are some steps involved (albeit simple) I am documenting them here.

There are two options that you have:

* Very minimal with very few packages and minimum configuration. (Pure ruby FastCGI server)
* More faster and industrial strength with more packages. (FastCGI with Native component)

If you are just interested in getting the FastCGI for ruby to work go with the First option, Incase
what you need is more than just that (due to performance considerations) then the Second option
is a better choice.

### Option I (minimal configurations)  

#### Prerequesites:

[fcgi](http://www.fastcgi.com/dist/fcgi.tar.gz) [ruby-fcgi](http://raa.ruby-lang.org/project/fcgi/) (0.8.7)
[Sun Java System Web Server](http://www.sun.com/download/products.xml?id=446518d5) 

#### Installation: 

Install the ruby-fcgi (You can also do a gem install of ruby-fcgi)

```
$ gzcat ruby-fcgi-0.8.7.tar.gz | tar -xvpf -;cd ruby-fcgi-0.8.7;ruby install.rb config&&ruby install.rb setup&&sudo ruby install.rb install**
```

If you are doing a gem install, then this is the command line:

```
gem install ruby-fcgi-0.8.7.gem**
```

#### Configuring our webserver.

Enable fastcgi. 

(Editing config files by hand -- you can also do this by using the wadm console.)
These files are found under https-xxx/config in the webserver installation directory.

Open the **magnus.conf** and add

```
Init fn="load-modules" shlib="libfastcgi.so" shlib_flags="(global|now)"
```


Open **mime.types** and add this line to the end (If it is not already present).

 

```
type=application/ruby                            exts=rb
```


Open **obj.conf** and add this line to the default object (Assuming /space/store/fcgi contains
your dispatcher.rb script)

```
<Object name="default">
...
Service fn="responder-fastcgi" type="application/ruby" app-path="/usr/local/bin/ruby" app-args="/space/store/fcgi/dispatcher.rb"
</Object> 
```


**dispatcher.rb**

```
#!/usr/local/bin/ruby
require "fcgi"

def getBinding(cgi,env)
  return binding
end

FCGI.each_cgi do |cgi|
    begin
        script = cgi.env_table['PATH_TRANSLATED']
        eval File.open(script).read, getBinding(cgi,cgi.env_table)
    rescue Exception => e
        puts "Content-type: text/plain\\r\\n\\r\\n"
        puts e.message
        puts e.backtrace
    end
end
```

Now, once you have done all this, start your webserver, and access 

http://yourwebserver.com:port/hello.rb

You should see this error. Do not worry. this is expected.

```
No such file or directory - /space/store/https-agneyam/docs/hello.rb
/space/store/fcgi/dispatcher.rb:11:in `initialize'
/space/store/fcgi/dispatcher.rb:11
/usr/local/lib/ruby/site_ruby/1.9/fcgi.rb:612:in `each_cgi'
/usr/local/lib/ruby/site_ruby/1.9/fcgi.rb:609:in `each_cgi'
/space/store/fcgi/dispatcher.rb:8
```


Now provide the hello.rb in the directory indicated. (The docroot of the installed
instance)

**hello.rb**

```
puts "Content-type: text/plain\\r\\n\\r\\n"
puts "Hi from ruby."
```

Now access the same url

http://yourwebserver.com:port/hello.rb

This should give you

Hi from ruby.

http://yourwebserver.com:port/hello.rb


As you may be already aware, the FastCGI is persistant across requests. So you can
set and access persistant ruby global variables. Which also means that you should be
careful in doing so as they can lead to unplesent side effects.

In case your script had any errors they are logged in the webserver temp directory.
For unix systems, it is usually in /tmp/http-yourserver-randomchars/FastCgiStub.log

 

### Option II (Industrial Strength) 

#### Prerequesites:

[fcgi](http://www.fastcgi.com/dist/fcgi.tar.gz) (2.4.0)   (You dont need to install this if you just want to run pure ruby fcgi)
[ruby-fcgi](http://raa.ruby-lang.org/project/fcgi/) (0.8.7)
[ruby-mmap](http://raa.ruby-lang.org/project/mmap) (0.26)

[Sun Java System Web Server ](http://www.sun.com/download/products.xml?id=446518d5)

#### Installation: 

Install the fcgi to your system. (I used Solaris 10.)-- optional.

```
$ gzcat fcgi.tar.gz | tar -xvpf -
cd fcgi-2.4.0
./configure
make
sudo make install
```

Install the ruby-mmap (You can also do a gem install of ruby-mmap)

```
$ gzcat mmap.tar.gz | tar -xvpf -;cd mmap-0.2.6;ruby extconf.rb && make && sudo make install
```

Install the ruby-fcgi (You can also do a gem install of ruby-fcgi)

```
$ gzcat ruby-fcgi-0.8.7.tar.gz | tar -xvpf -;cd ruby-fcgi-0.8.7;ruby install.rb config&&ruby install.rb setup&&sudo ruby install.rb install
```


Also download the ruby fastcgi dispatcher written by http://pallas.telperion.info/ruby-cgi/ (Available [here ](http://blogs.sun.com/blue/resource/ruby-cgi)too.)

#### Configuring our webserver.

Enable fastcgi. 

(Editing config files by hand -- you can also do this by using the wadm console.) 
Open the magnus.conf and add

```
Init fn="load-modules" shlib="libfastcgi.so" shlib_flags="(global|now)"
```

Open obj.conf and add this line to the default object

(Assuming /space/store/fcgi is the place where you are going to store your scripts)

You can also do it the way I demonstrated earlier (by adding a mimetype of type application/ruby and using
Nametrans fn="assign-name". The only change from the above will be in the value of app-args. Ie it should
change from **dispatcher.rb** to the **ruby-cgi** used here.)

```
<Object name="default">
...
NameTrans fn="pfx2dir" from="/fcgi" dir="/space/store/fcgi" name="ruby"
</Object> 
```

Provide the fastcgi object as below. (Assuming /space/store/fcgi contains the ruby fastcgi dispatcher ruby-cgi.)

```
<Object name="ruby">
Service fn="responder-fastcgi" app-path="/usr/local/bin/ruby" app-args="/space/store/fcgi/ruby-cgi"
</Object>
```

Now, edit the ruby-cgi dispatcher, and change the line

```
script = cgi.env_table['SCRIPT_FILENAME']
```

to read 

```
script = cgi.env_table['PATH_TRANSLATED'] 
```

Be sure to place an example script in the same directory
ie hello.rb

```
puts "Content-type: text/plain\\r\\n\\r\\n"
puts "Hello there...\\n" 
```

Be sure to give execute permissions to ruby-cgi and hello.rb

```
$ chmod 755 ruby-cgi
$ chmod 755 hello.rb 
```

Now, once you have done all this, start your webserver, and access 

http://yourwebserver.com:port/fcgi/hello.rb

You should see

```
Hello there...
```

In case your script had any errors they are logged in the webserver temp directory.
For unix systems, it is usually in /tmp/http-yourserver-randomchars/FastCgiStub.log
