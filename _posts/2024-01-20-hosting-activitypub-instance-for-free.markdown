---
published: true
title: Hosting your own ActivityPub instance for free
layout: post
comments: true
tags: activitypub, mastodon
categories: post
---

# Hosting your own ActivityPub instance for free

Note: You can view this post in the hosted activitypub instance [here](https://gopinath.org/2022-11-11-hosting-ktistec-on-oracle-cloud)

For those who are impatient, here is the quick and dirty procedure:

## DNS

0. You need a domain name for this to work. You have two choices
(a) Head over to any of the domain registrars like domains.google and  buy a domain name-- say mydomain.org, or
(b) use a free dynamic dns service like freemyip which will get you something like mydomain.freemyip.com. If you use a dynamic dns, you will have to use Let Us Encrypt to handle your own  certificate. If you own the domain, you can use Cloudflare to https-front-end your server. If using the freemyip, make sure to save your token securely.

In the steps below, I will mark (a) or (b) based on the solution you chose.

## Ktistec

Ktistec is a server that supports the ActivityPub protocol. That is, in simple terms, it can collaborate with Mastodon and other servers that support ActivityPub. One trouble we have is that Ktistec does not distribute binaries yet, so we have to build it on our own. Unfortunately the Oracle free tier does not have sufficient computing power to build it. So you will have to build it in a local machine. I use an Ubuntu 22.04 vagrant image to build it (I used the Ubuntu 22.04 image because that is what is available in Oracle free tier box).

1. Within the vagrant box, checkout Ktistec

```
git clone https://github.com/toddsundsted/ktistec; cd ktistec
```

2. Use the provided docker to build an image. 

```
docker build -t "ktistec:latest" .
```

3. Export the docker image

```
docker  save ktistec:latest | gzip > ktistec.tgz
```

## Oracle Cloud

Next, we host the Ktistec instance in the oracle cloud. We have to do three things; Create and prepare a free compute box, start the server, and open ports so that it is accessible over the public internet.

5. Head over to the oracle cloud, create a free compute box instance with the Ubuntu 22.04 image. Prepare the image so that it can run docker.  Digital ocean has a reasonable tutorial. Make sure to create your own ssh keypair and upload the public key when creating the compute box. We need to connect to the machine using SSH. Also, make sure that you have a public IP when you create the compute box. Copy the public IP once the machine is created. (You can delete and recreate machines easily, so if you make a mistake, start over)

6. Next, we copy ktistec.tgz to this machine,

```
scp ktistec.tgz my_public_ip:~/
```

7. Connect to your machine

```
ssh my_public_ip
```

7.  Load the docker image within your newly created machine.

```
docker image load -i ~/ktistec.tgz
```

8. Check it has loaded

```
docker image ls
REPOSITORY   TAG         IMAGE ID       CREATED        SIZE
ktistec       latest      22d6ac8c8cd5   2 days ago     37.1MB
```

9. Start the machine. You have two options here. 
    (a) The first is if you own the domain name.

```
mkdir -p ktistec/db ktistec/uploads; cd ktistec;
docker run -p 80:3000 \
   -v `pwd`/db:/db -v `pwd`/uploads:/uploads ktistec:latest
```

 (b) If you are using the freemyip subdomain, then you need a separate nginx reverse proxy to front end your system. In that case run this instead.

```
mkdir -p ktistec/db ktistec/uploads; cd ktistec
docker run -p 3000:3000 \
   -v `pwd`/db:/db -v `pwd`/uploads:/uploads ktistec:latest
```

Note that the db and uploads contain the data from your instance. Back them up periodically.

Next, we open the ports in Oracle cloud so that browsers outside can connect to port 80 if you are using a custom domain and cloudflare, and port 443 if you are going with freemyip and letusencrypt.

6.  In cloud.oracle.com, click on [Instance Information] -> [Primary VNIC: Subnet]

7. Click on default security list, click on [Add Ingress Rules]

(a) domain+cloudflare  --- Stateless, Source CIDR is 0.0.0.0/0 IP Protocol is TCP, Destination port range is 80
(b) freemyip+letusencrypyt  --- Stateless, Source CIDR is 0.0.0.0/0 IP Protocol is TCP, Destination port range is 443 create another rule for 80 also. You will need it for testing, but you can turn it off later.

 
9. HTTPS Frontend. 

(a) If using cloud flare, head over to CloudFlare, add site (your sitename), choose the free plan. Add DNS Records, create a [A] record with [@] or the full name for your site, content is the public ip of the oracle instance you just created, and mark proxied.

 At this point, you are done, and your Ktistec instance will be available at https://mydomain.org. You will need to immediately open the instance in a browser and set the primary username password, and other site configuration details.

(b) if using freemyip+letusencrypt then you have to be a little careful. The usual method of creating a certificate requires you to add a TXT record to DNS or use nginx directly. I have not been able to get this to work. Instead, follow these steps to generate a letusencrypt certificate.

i) Install nginx on the system. Make sure that you can reach the nginx installation from outside by connecting to it over the http://<publicip>:80
sudo apt install nginx
If it does not work, flush your iptables so that it can connect from outside (not sure how better to do this, but if you are familiar with iptables, add a rule to connect instead. Flush worked for me.)

```
iptables -F
```

Try http://-publicip-:80 again. It should show the welcome page.

ii) To generate a certificate with letusencrypt, you need to first install certbot.

```
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

ii) Next, generate the certificate manually with http (I could not get DNS to work. It requires adding a TXT record to freemyip subdomain. While it is mentioned in the webpage of freemyip, the TXT record never gets added). 

```
sudo certbot -d <mydomain>.freemyip.com \
    --manual --preferred-challenges http certonly
```

iii) Provide <mydomain>.freemyip.com as the domain name if asked. It will ask you to place a file <filename> inside the root directory of nginx followed by .well-known/acme-challenge/ with a value <the value>.  The root directory is typically at /var/www/html. So, you have to create the directory, and place the file.

```
mkdir -p /var/www/html.well-known/acme-challenge/
echo <the value> \
     > /var/www/html.well-known/acme-challenge/<filename>  
```

iv) Make sure to check the file first

```
wget http://<mydomain>.freemyip.com/.well-known/acme-challenge/<filename> 
```

If no errors, then press enter in the console for certbot and continue. You will see something like

```
Successfully received certificate.
 
Certificate is saved at: /etc/letsencrypt/live/<mydomain>.freemyip.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/<mydomain>.freemyip.com/privkey.pem
This certificate expires on 2023-02-09.
These files will be updated when the certificate renews.    
```

v) Make it available on nginx by adding the following in the following file.

```
sudo touch /etc/nginx/sites-available/<mydomain>.freemyip.com
sudo ln -s /etc/nginx/sites-available/<mydomain>.freemyip.com \
           /etc/nginx/sites-enabled/
```

vi) Then edit /etc/nginx/sites-available/<mydomain>.freemyip.com and add the following.

```
server {
    listen *:80;
    listen [::]:80;
    server_name _;
    listen 443 ssl;
    # RSA certificate
    ssl_certificate /etc/letsencrypt/live/<mydomain>.freemyip.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<mydomain>.freemyip.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    # reverse proxy
    location / {
         proxy_pass http://localhost:3000;
         include proxy_params;
    }
    # Redirect non-https traffic to https
    if ($scheme != "https") {
       return 301 https://$host$request_uri;
    }
}
```

vii) Restart nginx

```
sudo systemctl restart nginx
```

At this point, your site should be available  as https://mydomain.freemyip.com.  You will need to immediately open the instance in a browser and set the primary username password, and other site configuration details.

Once this is done, you can remove the port 80 from the Ingress rules in oracle cloud.

## More

If you find that the docker is taking up too much memory, you can also compile ktistec externally, and copy it over to the server. You will need to ensure the following files are available in the directory.  The server is the ktistec executable. The ktistec.db is your ktistec database. The following are the files I have. You will have to copy over these files into the directory, either from the docker image or from elsewhere.

First, check the docker image

```
$ docker ps
CONTAINER ID   IMAGE           COMMAND ...
0e9882260f65   social:latest   "/bin/server"   ... 
$ docker export 0e9882260f65 > s.tar
```

Now, you can check the files in the docker:

```
$ tar -tvpf s.tar | grep app
```

These are the same files you require, so copy these over.

```
$ tar -xvpf s.tar app/
```

Next,  copy over the kitstec executable.

```
$ cp ~/ktistec.bin app/server
```

Next, copy over your ktistec.db to the same directory

```
$ cp ~/ktistec.db app/
```

The finished directory should look like this

```
$  pwd
/home/user/ktistec/app
$ ls
etc ktistec.db public server
$  find etc
etc
etc/rules
etc/rules/content.rules
etc/database
etc/database/schema.sql
etc/contexts
etc/contexts/w3id.org
etc/contexts/w3id.org/security
etc/contexts/w3id.org/security/v1
etc/contexts/w3id.org/security/v1/context.jsonld
etc/contexts/litepub.social
etc/contexts/litepub.social/context.jsonld
etc/contexts/www.w3.org
etc/contexts/www.w3.org/ns
etc/contexts/www.w3.org/ns/activitystreams
etc/contexts/www.w3.org/ns/activitystreams/context.jsonld

$ find public/
public/
public/mstile-150x150.png
public/android-chrome-192x192.png
public/favicon.ico
public/browserconfig.xml
public/dist
public/dist/site.bundle.js.LICENSE.txt
public/dist/597.bundle.js
public/dist/64b800aa30714fd916dc.woff2
public/dist/fcba57cdb89652f9bb54.gif
public/dist/747d038541bfc6bb8ea9.ttf
public/dist/09cd8e9be7081f216644.svg
public/dist/597.bundle.js.LICENSE.txt
public/dist/356a0e9cb064c7a196c6.woff
public/dist/site.bundle.js
public/dist/settings.bundle.js
public/dist/settings.bundle.js.LICENSE.txt
public/android-chrome-512x512.png
public/apple-touch-icon.png
public/logo.png
public/safari-pinned-tab.svg
public/mstile-70x70.png
public/mstile-144x144.png
public/mstile-310x150.png
public/mstile-310x310.png
public/3rd
public/3rd/themes
public/3rd/themes/default
public/3rd/themes/default/assets
public/3rd/themes/default/assets/fonts
public/3rd/themes/default/assets/fonts/Lato-Italic.woff2
public/3rd/themes/default/assets/fonts/brand-icons.woff2
public/3rd/themes/default/assets/fonts/Lato-Bold.woff2
public/3rd/themes/default/assets/fonts/outline-icons.woff2
public/3rd/themes/default/assets/fonts/Lato-BoldItalic.woff2
public/3rd/themes/default/assets/fonts/Lato-Regular.woff2
public/3rd/themes/default/assets/fonts/icons.woff2
public/3rd/themes/default/assets/images
public/3rd/themes/default/assets/images/flags.png
public/3rd/semantic-2.4.1.min.css
public/site.webmanifest
public/favicon-32x32.png
public/favicon-16x16.png
```

If you had any uploads, copy that directory over

```
$ cp -r ~/uploads/* public/uploads/
```

Finally, you can start the server

```
$  cd /home/user/ktistec/app; LOG_LEVEL=INFO ./server
```

