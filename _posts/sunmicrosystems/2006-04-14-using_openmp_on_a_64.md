---
layout: post
tagline: "."
tags : [sunmicrosystems blog sun]
categories : sunblog
e: using openmp on a 64 threads system
title: Using OpenMP on a 64 Threads System
---

What do you do when you get a [64 threads machine](http://www.sun.com/servers/coolthreads/t5120/)? I mean other than trying to find the hidden messages in
[Pi](http://en.wikipedia.org/wiki/Contact_%28novel%29%20)?
Our group recently acquired a T5120 behemoth for builds, and I wanted to see what it was capable of.  

```
$ uname -a  
SunOS hypernova 5.10 Generic_127127-11 sun4v sparc SUNW,SPARC-Enterprise-T5120
$ psrinfo | wc -l
64  
```

In my case I settled a slightly less ambitious endeavor. I recently had to implement Gaussian elimination as part of a university course work, I converted it to use the [OpenMP](http://openmp.org/wp/) and compiled with [SunStudio](http://developers.sun.com/solaris/articles/studio_openmp.html).

```
$ cat Makefile
gauss: gauss.omp.c  
       /opt/SUNWspro/bin/cc -xopenmp=parallel gauss.omp.c -o gauss  
$ diff -u gauss.single.c gauss.omp.c
\--- gauss.single.c      Tue Apr 14 14:32:57 2009  
+++ gauss.omp.c Tue Apr 14 14:44:48 2009  
@@ -7,6 +7,7 @@  
 #include <sys times.h="">  
 #include <sys time.h="">  
 #include <limits.h>  
+#include <omp.h>
 
 #define MAXN 10000  /* Max value of N */  
 int N;  /* Matrix size */  
@@ -35,7 +36,7 @@  
     char uid[L_cuserid + 2]; /*User name */

     seed = time_seed();  
-    procs = 1;  
+    procs = omp_get_num_threads();

     /* Read command-line arguments */  
     switch(argc) {  
@@ -63,7 +64,7 @@  
                 exit(0);  
             }  
     }  
-  
+    omp_set_num_threads(procs);  
     srand(seed);  /* Randomize */  
     /* Print parameters */  
     printf("Matrix dimension N = %i. ", N);  
@@ -170,6 +171,7 @@

 }

+#define CHUNKSIZE 5  
 void gauss() {  
     int row, col;  /* Normalization row, and zeroing  
                     * element row and col */  
@@ -178,7 +180,9 @@

     /* Gaussian elimination */  
     for (norm = 0; norm &lt; N - 1; norm++) {  
+        #pragma omp parallel shared(A,B) private(multiplier,col, row)  
         {  
+            #pragma omp for schedule(dynamic, CHUNKSIZE)  
             for (row = norm + 1; row &lt; N; row++) {  
                 multiplier = A[row][norm] / A[norm][norm];  
                 for (col = norm; col &lt; N; col++) {  

```


As you can see, the changes are very simple, and requires very little modification to the code. Below was my result running it in a single thread and next using all 64 threads.

 First the single threaded version.  

```
$ time ./gauss 10000 1 4
Random seed = 4  
Matrix dimension N = 10000.  
Number of processors = 1.  
Initializing...  
Starting clock.  
Stopped clock.  
Elapsed time = 1.11523e+07 ms.  
(CPU times are accurate to the nearest 10 ms)  
My total CPU time for parent = 1.11523e+07 ms.  
My system CPU time for parent = 1080 ms.  
My total CPU time for child processes = 0 ms.  
\--------------------------------------------  
./gauss 10000 1 4  11163.06s user 1.64s system **99**% cpu 3:06:04.96 total  
```

And now using all threads.  

```
$ time ./gauss 10000 64 4
Random seed = 4  
Matrix dimension N = 10000.  
Number of processors = 64.  
Initializing...  
Starting clock.  
Stopped clock.  
Elapsed time = 254993 ms.  
(CPU times are accurate to the nearest 10 ms)  
My total CPU time for parent = 1.53976e+07 ms.  
My system CPU time for parent = 37960 ms.  
My total CPU time for child processes = 0 ms.  
\--------------------------------------------  
./gauss 10000 64 4  15371.53s user 38.51s system **5757**% cpu 4:27.65 total  
```

Now I am all set to look for my name in [Pi](http://www.cs.berkeley.edu/~ejr/GSI/2000-spring/cs267/assignments/assignment1-results/flab/). :)

The gaussian elimination source is [here](/blue/resource/gauss.omp.c)
