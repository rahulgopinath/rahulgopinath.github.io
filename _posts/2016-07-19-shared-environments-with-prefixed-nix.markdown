---
published: true
title: Shared Environments with Prefixed Nix
layout: post
comments: true
tags: nixos
categories: post
---
*tl;dr*: Recipe for Nix installation on a non */nix* location, which can be shared across multiple users

*caveats*: Very hacky

*requirements*: Every one in your group should at least be a member of the same UNIX group.

As a researcher working on software empirical research, one of the *pain points* in my research is the creation and maintenance of an environment that can be reproduced easily. I would like to be able to switch environments according to which project I am working on, and even experiment on new programs without affecting my old environments.

Further, I would also wish to collaborate with other researchers, and share my resources with them. If I were to set up an environment once in my machine, it is a waste of time and energy to try to do that again on another system or for another user in the same system. These are the constraints that led me to the [Nix](https://nixos.org/nix/) package manager in the first place. The promises of [Nix](https://nixos.org/nix/) are an easily reproducible declarative environment, and purity in the environment thus produced.

Unfortunately, while we have little restriction in available space, or computational power, our systems are fairly locked down. There is no chance of getting access to a folder like */nix* in all the machines available (i.e. no chance of _root_ access). So a normal */nix* install is completely out of question. These systems are also fairly minimal in their installed packages, and gets updated rather infrequently. Hence the set of packages required to make Nix work is larger than what is required for most Nix installations. Hence, my recipe includes more packages than may be strictly necessary at your environment.

There are still some pieces missing, such as *sssd* support. These are implemented using rather gross hacks. While there does not seem to be any insurmountable reasons for any of the missing pieces, one may be cautioned that it may not be a priority for the Nix developers at this point of time. Also, be warned that when the corresponding bugs get fixed, some of these hacks might break.

Our environment at [Oregon State](http://eecs.oregonstate.edu/) consists of two separate groups of machines. The first ones consists of our personal desktops (fairly week, 4G RAM, and 40G space), and about 15 machines with about 512G RAM in each, and 1000G space under */scratch* (No common NFS share). The second ones consist of about 1000 machines in a [Univa cluster](http://engineering.oregonstate.edu/computing/cluster/using.html) with varying capabilities. We also have an NFS mount accessible from each machine in the cluster. So I had to build my recipe to be applicable in both kinds of machines. Each user gets a home environment mounted using NFS, that is accessible in both groups of machines.

While Nix wiki [details](https://nixos.org/wiki/How_to_install_nix_in_home_%28on_another_distribution%29) multiple ways to install Nix on non */nix* locations, most of them did not work for me. For example, *PRoot* does not work in the cluster machines, and where it works, it is too slow. The *chroot* also had problems on cluster. The manual install only works with the below changes. Finally, LDAP is a *must have* for almost everyone in an academic setting, since we usually have to login to multiple machines. So we really need the *glibc* hack if we are to use Nix.

## Recipe

* Fork [nix-prefix](https://github.com/vrthra/nix-prefix), change any variables you want in [Makefile](https://github.com/vrthra/nix-prefix/blob/master/Makefile) and checkout to a location of your choice (I assume */scratch*).

```bash
$ export base=/scratch
$ git clone https://github.com/vrthra/nix-prefix $base/nix-prefix
```

* Especially verify that you require all packages that are specified in the checked out [Makefile](https://github.com/vrthra/nix-prefix/blob/master/Makefile). You can change which packages get installed by modifying the *$src* variable. By default, these packages are built
*src=nix bzip2 curl sqlite dbi dbd wwwcurl bison flex gcc coreutils*. See the *#@ * lines for where they are fetched from.

* Change to the UNIX group that you share with other team members (I assume that *myteam* is the UNIX group).

```bash
$ newgrp myteam
```

* Initiate *make* (If you have not changed the Makefile, please provide a reasonable value for *base* while making). Nix will be installed at *$base/nix*

```bash
$ make -f etc/Makefile.nix link
$ make
```

* Note that due to [512](https://github.com/NixOS/nix/issues/512) we have to modify the Nix packages slightly. We need a non-released version of Nix (see [here](https://github.com/vrthra/nix-prefix/blob/master/etc/non-nix.patch)), which is fetched automatically.

* You will also require to create/update your *~/.nixpkgs/config.nix*. If you don't have one, it can be created automatically by using *nixpkgs* target. Remember to use *base=* argument here if you have not changed it in the Makefile. Update your profile *~/.nix-profile* and the Nix Packages checkout link at *~/.nix-defexpr/nixpkgs*.

```bash
$ make nixpkgs nixprofile nixconfig
```

* At the end of these steps, you should have the nix installation under *$base/nix*, *~/.nix-profile* linked to *$base/nix/var/nix/profiles/default*, and *~/.nixpkgs/config.nix* containing entries from *nix-prefix/etc/config.nix* with BASE replaced with $base.

* Make sure that you can access your nix commands by executing *./bin/nix.sh* You should get a prompt `nix>`.

```bash
$ ./bin/nix.sh
nix> nix-env -q
nix-1.12.x
```
* Remember to garbage collect, if you would like some space back.

```bash
nix> nix-collect-garbage -d
nix> nix-collect-garbage -d
```

* Exit out of the `nix>` prompt, and you may now safely cleanup

```bash
$ make clean
```

* We are almost there. Unfortunately due to [554](https://github.com/NixOS/nix/issues/554), LDAP will not work right now. You can check you need to hack to make it work by

```bash
$ ./bin/check-nss.py
```

If it throws an exception, execute the next command, if not, skip it.

* It does not work: we hack it temporarily by installing *sssd*, which is in [PR 14697](https://github.com/NixOS/nixpkgs/pull/14697) right now, and copying over *libnss_sss* to the *glibc plugins* folder. WARNING: GROSS HACK  _If you are a Nix purist, please hold your nose (or help me fix)_.

```bash
$ ./bin/update-glibc-hack.sh
```

* A final issue is that of sharing with others. Due to [324](https://github.com/NixOS/nix/issues/324), one cant yet share an installation with the members in the same group. A hack is to update the permissions under *$base/nix* so that any file that has user write becomes group write. This can be done by below. Remember to do this each time any of the members have added a new package.

```bash
$ ./bin/update-perms.sh
```

* Once you have built *$base/nix*, you can compress it and transport it to other machines with same operating system. After a GC, the size is really small.

```bash
nix> nix-collect-garbage -d
nix> nix-collect-garbage -d
```
For some reason, I have to do `nix-collect-garbage -d` two times to actually delete all garbage.

Now, Exit out of the shell, and check the size of installation.

```bash
$ cd $base
$ tar -cf nix.tar nix
$ gzip nix.tar
$ du -ksh nix.tar.gz
36M     nix.tar.gz
```

The *nix.tar.gz* can now be copied to other machines to get a base nix package installation. Once you have the `nix>` prompt in another machine, you could use `copy-closure` to copy packages back and forth.

* For another user who wants to use the same *$base/nix* installation in the same machine, login as that user, and cd to directory where you checked out *nix-prefix*, and invoke targets *nixpkgs* and *nixprofile*. These will create the necessary links in their home directory.

```bash
$ cd $base/nix-prefix
$ make nixprofile nixpkgs nixconfig
```

* Remember that you need at least these environment variables

```bash
$ export PATH=$HOME/.nix-profile/bin:$PATH
$ export NIXDIR=$HOME/.nix-defexpr
$ export NIXPKGS=$NIXDIR/nixpkgs/
$ export NIX_PATH=$NIXPKGS:nixpkgs=$NIXPKGS
```

* Also, switch to the correct group as the second user before touching *nix*.

```bash
$ newgrp myteam
```

* Finally, if you update *nix* as any user, always run update permissions.

```bash
$ ./bin/update-perms.sh
```


* The *default.nix* in the [nix-prefix](https://github.com/vrthra/nix-prefix) should get you started for an academic research paper using basic *IEEE* latex style, and *R* using *ggplot* and a number of other packages. You can instantiate it using

```bash
$ mkdir -p .gcroots
$ nix-instantiate . --indirect --add-root $.gcroots/default.drv
$ nix-shell . --pure --indirect --add-root .gcroots/dep
```

Which will land you in a *nix-shell* containing the required tools. The `add-root` incantations ensure that your environment will not be garbage collected on `nix-collect-garbage` invocations. The first `nix-instantiate ... --add-root ...` creates a reference to the derivation of *default.nix*, and the second `nix-shell ... --add-root ...` creates references to all the build dependencies.

With this recipe, you should have a shared prefixed nix installation suitable for academic environments under *$base/nix*. Ping me if you face any troubles, and I will see if I can help.

## Still to be solved.

Because we have multiple kinds of environments, all of which mounts the same *$HOME*, we don't have a way to switch the directories *~/.nixpkgs/config.nix* and *~/.nix-defexpr*. There is this issue [817](https://github.com/NixOS/nix/issues/817) still open about it, and it seems there was a *NIXPKGS_CONFIG* variable at one point of time, but seems to have been removed. See [829](https://github.com/NixOS/nix/issues/829).

This can be worked around by using some shell scripting to switch the variables. However, it is very error-prone, and does not let you use different environments simultaneously.
