---
layout: post
categories : sunblog
tagline: "."
tags : [sunmicrosystems blog sun]
e: sun hpc clustertools for openmpi
title: Sun HPC clustertools for OpenMPI
---

Having migrated originally from Civil Engineering, I have always been interested in parallel programming. Quite a few (almost all?) problems in that domain are what can be called embarrassingly parallel - be it Structural Mechanics, Fluid dynamics, or Virtual Modeling.  

Recently I got interested in parallel programming again as part of my studies. While the [university](http://www.cs.iit.edu/%7Escs/home/home.html)
has a cluster setup, it is almost always in use, and is dead slow because of the number of users. So I tried setting up a simple OpenMP cluster locally for Ubuntu and Solaris,  

Setting up OpenMP on Ubuntu is treated in quite a few places in the web, so I am not listing the steps for that. How ever I found that using the [cluster tools](
http://www.sun.com/software/products/clustertools/) from Sun was much more easy than messing with the MPICH distribution in Ubuntu.

Here are my notes on getting it to work.

Prerequisites

* You need some machines with the same OS and ARCH, NM
* A common NFS exported directory (mounted on the same path) on each machine. I used /home/myname as the NFS mount  
* Ensure that you have password less login either using ssh or rsh.  
* You also need to install the cluster tools on each.

You can get the cluster tools from [here](http://www.sun.com/software/products/clustertools/get_it.jsp). Ungzip it to directory and execute the ctinstall binary

```
$ cat sun-hpc-ct-8.1-SunOS-sparc.tar.gz |gzip -dc | tar -xvpf -  
$ sun-hpc-ct-8.1-SunOS-sparc/Product/Install_Utilities/bin/ctinstall -l  
$ ...
```

This will install the necessary packages. You might need to check the default parameters and verify that they are to your satisfaction.  

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/ompi_info --param all all
```

In my setup, I wanted to use rsh while ssh is the default for clustertools  

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/ompi_info --param all all | grep ssh
     MCA plm: parameter "plm_rsh_agent" (current value: "ssh : rsh", data source: default value, synonyms: pls_rsh_agent)  
              The command used to launch executables on remote nodes (typically either "ssh" or "rsh")  
     MCA filem: parameter "filem_rsh_rsh" (current value: "ssh", data source: default value)  
$ echo 'plm_rsh_agent = rsh' >> /opt/SUNWhpc/HPC8.1/sun/etc/openmpi-mca-params.conf
```

Once this is done, create your machines file (my machine names are host1 host2 host3 and host4)  

```
$ cat > machines.lst  
host1  
host2  
host3  
host4  
^D 
```

Now you are ready to verify that stuff works. Try   

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/mpirun -np 4 -machinefile ./machines.lst hostname
host1  
host2  
host3  
host4  
```

This should also work  

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/mpirun -np 4 -host host1,host2,host3,host4 hostname
host1  
host2  
host3  
host4  
```

If you get similar output, then you have successfully completed the initial configuration.   
If you are unable to modify the `/opt/SUNWhpc/HPC8.1/sun/etc/openmpi-mca-params.conf` file, then you could try the below  

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/mpirun -mca pls_rsh_agent rsh -np 4 -machinefile ./machines.lst hostname
host1  
host2  
host3  
host4  
```

Try an example,

```
$ cat hello.c
#include <stdio.h>  
#include <mpi.h>  
int main(int argc, char **argv) {  
     int my_rank;  
     MPI_Init( &argc, &argv);  
     MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);  
     printf("Hello world[%d] ", my_rank);  
     MPI_Finalize();  
     return 0;  
}  
```

Try compiling and running  

```
$ /opt/SUNWhpc/HPC8.1/sun/bin/mpicc -o hello hello.c  
$ /opt/SUNWhpc/HPC8.1/sun/bin/mpirun -np 4 -machinefile ./machines.lst ./hello
  Hello world[2]  
  Hello world[3]  
  Hello world[0]  
  Hello world[1]
```

Now you are ready to try something larger. You can try with a simple scatter and gather of a matrix that is [attached](/blue/resource/scattermatrix.c).

(Many thanks to the Sun HPC team for making this setup so easy.)
