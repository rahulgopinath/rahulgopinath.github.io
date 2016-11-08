---
published: true
title: Version Control Systems
layout: post
comments: true
tag: [vcs]
categories : post
---
## Introduction

The need for managing revisions and variants in software arose with the advent of software itself. Products go through various releases in their life cycle, and the feature sets differ based on platform capabilities and customer requirements. Thus the developers often have to support differing revisions and variants at the same time, which implies an ability to recreate the specific variant running at the customer site, and tracking changes that may have introduced an error. Another factor that led to the sophistication of version management tools was the explosion in the size and complexity of software projects. While manual synchronization of updates may have been an option with smaller teams, projects with multiple components and geographically distributed teams necessitated a shift in strategy. The teams had to work in parallel, and the updates from each needed to be synchronized to a common database, so that the latest updates were available to all.

Version control systems were introduced in the later half of 1960 to fill this need. The first version control system - PATCHY[16] was developed at CERN to manage updates to a deck of punched cards. This system maintained the history of changes at the start of a module via correction decks. However, the creation of these decks were a manual process, and neither was there a way of recovering a previous revision automatically. The correction decks served as a means to distribute updates to copies of the program running in other sites. Thus these decks were forerunners of the later operation based version management systems employing changesets.

Automatic version management was introduced in 1968 for IBM Clear/Caster[6] - a change management system for mainframes. This system stored a database of program specifications using deltas. However the deltas still had to be produced manually. SCCS[25] was the first version management system to introduce auto- matic management of deltas and revision management, and a data structure for fast retrieval of versions called interleaved deltas or the weave. This data structure later proved to be well suited for efficient merges and conflict resolution[27]. The next major innovation was by RCS[29] which introduced branches for parallel develop- ment of related programs. SCCS along with RCS are considered to be ancestors of all modern version control systems.

The introduction of networking which enabled concurrent development crossing machine boundaries was the next major milestone. This necessitated the introduction of early client-server version management systems. The first of these systems was CVS[12] which also marked a change from the earlier pessimistic concurrency with lock-modify-unlock work flow to an optimistic concurrency model with copy- modify-merge work flow.

Development of Version Control Systems from this point on are characterized by different solutions to move away from a centralized architecture to a more distributed approach. The rise of Internet and the popularity of large open source projects which involved coordination between geographically separated individuals with different requirements of features and stability was a major contributor to this change. A obvious approach is represented by systems such as ClearCase[2] and Code Co-Op[21] which make use of distributed commit protocols to provide the feeling of a central system to the user and maintain sequential consistency while still providing benefits of a distributed architecture such as division of labour across machines. Another direction is represented by distributed version control systems such as Mercurial[22] and Git[28] guaranteeing only eventual consistency. They do not synchronize between distant repositories automatically, instead opting to let the degree and frequency of synchronization be decided by the user. Another line of research is using peer to peer network overlays exemplified by PastWatch[33] which uses distributed hash table as the underlying network. Semantics aware version control systems like Monticello[31] and Envy[23] represent a new dimension of research, which are capable of tracking changes to classes, modules methods and variables, thus providing more intelligent merge facilities.

Table 1: Comparison of Version Control Systems

| VCS             | Conflict Resolution        | History Model  | Unit of Change   |
|-----------------|----------------------------|----------------|------------------|
| SCCS            | Lock - Modify - Unlock     | File           | File             |
| RCS             | Lock - Modify - Unlock     | File           | File             |
| CVS             | Modify - Merge - Commit    | Changeset      | File             |
| Subversion      | Modify - Merge - Commit    | Changeset      | Tree             |
| Clearcase       | Lock - Modify - Unlock     | Changeset      | File             |
| Code Co-Op      | Lock - Modify - Unlock     | Changeset      | Tree             |
| PastWatch       | Lock - Modify - Unlock     | Snapshot       | File             |
| Teamware        | Modify - Commit - Merge    | Changeset      | File             |
| Bitkeeper       | Modify - Commit - Merge    | Changeset      | Tree             |
| Arch            | Modify - Merge - Commit    | Changeset      | Tree             |
| Git             | Modify - Commit - Merge    | Snapshot       | Tree             |
| Mercurial       | Modify - Merge - Commit    | Changeset      | Tree             |
| Darcs           | Modify - Merge - Commit    | Patches        | Tree             |
| Monticello      | Modify - Merge - Commit    | Changeset      | Semantic elements|


## Early Version Control Systems

The initial version control systems were developed for the strongly centralized architecture in time sharing systems characterized by local storage and no access across machine boundaries. Due to the environment in which they developed, these systems did not feature the ability to network, nor did they support concurrent development. We look at two of these systems - SCCS and RCS that can be considered representatives of this era. They also illustrate a major design decision in the development of version control systems. That is, how the changes are stored. The SCCS system uses a technique called interleaved deltas where all the versions of a document are interleaved together along with a few control structures detailing which version uses what. This means that the time for look up of any version is same and is proportional to the length of document. On the other hand RCS uses reverse deltas from the latest version to store the entire history. This lets the access of the last version to be fast, but access of earlier versions becomes progressively harder. Both systems are analyzed in detail next.

### Source Code Control System

SCCS[25] was originally created for IBM 370 and PDP 11. These systems were time sharing systems which meant that the clients were expected to execute within the same system. Thus there was no expectation of networking in the system design. The main innovation of SCCS was the creation and management of version histories automatically. However the versioning was limited to individual artifacts rather than the complete repository. Another important contribution of SCCS was in its storage of deltas. It used a technique called interleaved deltas which interleaved all the versions of a document in the same file. This is a very space optimal technique that also allowed a single pass reconstruction of any revision that was required. This data-structure is called the weave data structure. This data structure is now considered foundational to merging and conflict resolution. However, SCCS did not feature automatic merging and conflict resolution.

The SCCS work flow only allowed one user at a time, where the user would lock a file before modification. This meant that only one user could have write access to a file at a time. This is different from the later systems which allowed multiple users to modify the files at the same time. This also meant that SCCS could provide a stronger guarantee of eventual consistency with respect to other systems which only provide an eventual consistency guarantee. SCCS also featured a very rudimentary mechanism for branches called optional deltas which were marked with an optional keyword. The deltas thus marked could be included or excluded later using another kind of deltas called include and exclude deltas. A user could simulate branching to some extant by the use of optional deltas. SCCS served as the foundation for the later distributed version control systems TeamWare and Bitkeeper.

### Revision Control System

The RCS[29] made its appearance in 1982. While the basic characteristics were similar to SCCS, the innovation of RCS was in introduction of genuine branches. This allowed its users to pursue parallel developmental lines. The concept of automatic merging of two related branches was also first introduced in RCS. One major diversion of RCS from SCCS was its use of delta encoding for version storage. This made RCS faster than SCCS in the retrieval of immediate ancestors while increasing the time taken for earlier ancestors. Like SCCS, RCS was also meant to manage individual files rather than complete directories. It was also similar to SCCS in terms of the lack of concurrency and networking support, and the strong sequential consistency thus provided. RCS spawned the later systems CVS, SVN and was influential in other version control systems in terms of the branching support and the delta encoding used as storage mechanism.

## Centralized Version Control Systems

Early version control systems were strongly centralized due to the assumption of a single machine. In this section, the second generation systems that grew out of these systems incorporating networking and concurrency are examined. An important feature in these systems is the recognition that the project as a whole needed to be versioned rather than individual artifacts. The requirement of concurrent access also necessitated a change from the pessimistic concurrency of early systems to optimistic concurrency in these systems. The two representatives of this era, CVS and SVN are examined in detail.

### Concurrent Versions System

CVS[12] started life as a set of scripts operating on top of RCS. It was created in order to make concurrent development easy. To this end, it goes further than both SCCS and RCS in allowing concurrent modification of artifacts. The concurrency model that is offered by CVS is optimistic concurrency control[8] where the changes to artifacts that are not in conflict are merged automatically and those in conflict are deferred for manual intervention and conflict resolution.

A major improvement in CVS with respect to SCCS came in the form of support for networking which along with the relaxed concurrency model encouraged parallel development. The users checked out versions of source code over the network, and at the end of modification, changes were committed back to the repository. CVS also allowed grouping of artifacts together using tags which allowed configurations to be reproduced later. This work flow can be described as follows. Different users check out an artifact to work on, and after modification, the first user checks in the changes made. When the next user tries to check in, the system informs the user that the repository version has updated, and is asked to merge the changes to the new version in the repository. The user merges the new version to the working directory and issues a commit. This in turn creates a new version in the repository after that of the first user. For the merge procedure, any non conflicting changes are automatically merged, and conflicts are marked for manual resolution.

The major shortcomings of CVS are that, versions are tracked for individual files rather than a repository as a whole. This ignores the dependency of certain files to others which makes it hard to identify changes that should be bundled together. This can be alleviated to some extant using tagging which allows a tag to be attached to the current version of all files in the repository. Another problem is that commits of groups of files are not atomic. That is, changes to one file can be accepted while others can be refused. This leads to inconsistent repository states. CVS also does not track file renames. Moreover, it treats addition and deletion of files and directories outside the transaction, which again causes problems for the consistency of the repository. CVS also needs to be told which files are binary and which are text files. This is so because it tries to be platform independent and hence replaces the end of line markers in the text files checked in depending on the platform of the client.

### Subversion

SVN[24] was created to rectify the major shortcomings of CVS. It has the same client server architecture as CVS. However, versioning is done per directories rather than on a file basis. Moreover, the commits are on directory level rather than per file. This preserves the atomicity of commits. SVN is also preserve the history of files across copy and rename. However, it still requires modifications and renames to be done as separate steps to be able to track a file across renaming. The branching operation is different from CVS in that, the operation creates a shallow copy of the specified version in the outermost folder. The tagging operation in SVN is also similar in that a new folder with the specified versions are created when a tag is made.

## Distributed Version Control Systems - Replicated

Replicated version control systems are a natural evolution of the centralized version control systems. In these systems, each replica are in synchronization with each other, and the membership in the peer to peer group is determined in advance. They typically use a distributed commit protocol to maintain consistency between replicas. The mechanism of replication is hidden from the user from whose perspective, there is no difference between a replicated version control system and a centralized version control system. Some of the replicated version control systems partition the repository such that the some replica is assigned the job of maintaining particular parts of the repository. The major representatives of this mode of operation are ClearCase, Code Co-Op and PastWatch. We analyze each in detail next.

### ClearCase

ClearCase[2] and ClearCase Multisite[1] are tools from IBM. The ClearCase Multi- site is an add-on to the main product. ClearCase is implemented as a file system that tracks every fine-grained change made to the file system. The equivalent of a commit is the operation baseline which tags all the current versions of the files in the repository to a single identifier. The Versioned Object Base containing all the versions of artifacts in a directory is typically accessible over the network and mounted in the user’s machine using Multi Version File System. This layer is called a view. There can be multiple branches for each elements corresponding to different versions. The versions of objects shown in a view is selected by a ConfigSpec which contains the rules to choose specific versions of elements. ClearCase allows derived artifacts in one view to be synchronized to another view which requires the same object thereby avoiding repetitive builds.ClearCase is an example of a centralized versioning system, and the multisite add-on adds the capability of partitioning the Versioned Object Base to different machines so that the particular portion of source tree being worked on can be moved closest to the team requiring it. A repository partitioned this way maintains active objects only in its specific domain. The passive objects which are from the portion not worked on, are synchronized periodically. This enables it to work even in places where there is no live connectivity to the central server, and hence it is best described as a distributed client server architecture. An intriguing feature of ClearCase is that a view can refer to any number of branches. Hence a user can work with the union of specified branches in a single view. Conflicts can be avoided completely by locking individual files by individual developers if necessary.

### Code Co-Op

Code Co-Op[21] is another replicated version control system that takes a distributed commit approach to the global repository. The two phase distributed commit protocol is used to keep the replicas in sync, which enables it to create an illusion of a single up-to-date trunk while the repositories are distributed in a peer to peer architecture.

### PastWatch

The PastWatch[33] version control system is built over a peer to peer architecture using Distributed Hash Tables, and uses a data structure called revtree to keep track of concurrent changes and relationship between chanegs. The revisions are stored as key value pairs, and synchronization is simply moving the final image to a union of revisions from all users. The conflicts are resolved by one of the users if required.

The revtree data structure ensures that the replicas converge to identical images after sufficient synchronization. This too uses a two phase commit that keeps the replicas in sync with each other. It uses a distributed hash table to manage the peer to peer architecture.

## Distributed Version Control Systems : Open Systems

An open system is characterized by a relaxation of consistency requirement to eventual consistency, and a heavy reliance on branching and merging. Each copy of the repository is effectively a fork compared to the identical images in replicated systems. Like replicated systems there is no master repository. However, unlike the replicated systems the membership in the peer to peer grouping is dynamic, and new peers can freely join without applying for access to a central server.

### TeamWare

TeamWare[32] was the first distributed version control system, which was imple- mented as a layer over SCCS. It utilises the Network File System for access to peer repositories rather than a separate network protocol. The TeamWare defines operations bringover and putback which are used for synchronization between peer repositories. Unlike other distributed version control systems such as Git and Mercurial, TeamWare can bring over specific directories of the parent rather than particular changesets. This allow a finer grained control over the synchronization operation.

### Bitkeeper

Bitkeeper[13] is a reimplementation of TeamWare. However, unlike TeamWare, the changes are managed by chanegsets rather than SCCS deltas for individual files. It also has better support for file and directory renames than TeamWare. Another important addition to Bitkeeper is the ability to keep track of merged deltas so that merges are not attempted twice. This history awareness reduces the need for manual conflict resolution[14].

### Git

Git[28] is a decentralized version control system that has a massive user base. It is used as the version control for the Linux kernel[30] and GHC[18], and uses state based history model. Performance was the major concern for git and hence it is optimized heavily in this direction. While any repository is a branch for a distributed version control system, Git provides another mechanism called light weight branches which allow developers to work on parallel lines in the same repository. These are just reference tags to specific commits in the repository that are not exported by default to other repositories. A new commit to a light weight branch moves the tag to the latest commit. The history of the branch can be reconstructed by following back the parent commits of the commit pointed to by the tag. The state based history model allows git to be very flexible in managing relationships between commits, which can be changed at will by the operation rebase. The users can also modify the commit record using amend operation. Git adds the concept of a staging area which is the only area from which commits are done irrespective of the contents in the working directory. Submodules is another feature in Git that deserves attention. This feature allows Git to manage commits in external repositories that correspond to specific commits in the local repository. Git also allows users to save their work for later in a temporary branch by the operation stash. Other interesting operations include cherry pick, which allows only a particular set of commits to be extracted from the repository, the operation bisect which can be used to find a specific checkin that introduced a change in behavior, and reflog which is a trace of operations done on that repository.

### Mercurial

Mercurial[22] is another version control system very similar to Git, but based on operation based history model. Even though both Git and Mercurial started out with very different features, they have incorporated each others features to a large extant. For example, Mercurial supports the notion of relation ship editing through rebase extension, and the concept of stashing through shelve. The mq extension provides a temporary stack of changesets that can be applied to a repository in order without committing any of the changesets first. Mercurial also has the concept of sub-repositories equivalent to git sub-modules that enables it to track the state of project dependencies along with the project. One difference that Mercurial has in relation with Git is that it treats branches as a complete part of the repository data to be shared by default. Thus cloning a project with a branch will make the branch available to the new repository. The branching in Mercurial is provided by heavy branches which are separate repositories, or light weight branches called heads that can be tracked by using bookmarks, or a third way called long lived branches. These are visible to any repository to which the changes are pushed. Mercurial is extended heavily by its extensions. For example, the acl extension allows Mercurialto control access to parts of the repository, while bookmarks provides Gitlike light weight branches, transplant provides cherry picking, and share extension allows the history to be shared between multiple repositories. Mercurial can also actively exclude specific patches using ban, and provide a meta repository using nested extension.

### Darcs Advanced Revision Control System

Darcs[26] is another distributed version control system that takes a changeset oriented view of the repository, that resembles other changeset oriented systems like GNU Arch and Bazaar. An important feature of Darcs is that it is much more history aware in that it keeps track of which changesets have been merged before. Thus it provides better merging than other version control systems. An important aspect of Darcs is its underlying elegant theory of patches which enables it to make sure that its operations does not lead to loss of data. Another important difference in Darcs is that it maintains no chronological history. Instead, it maintains a more fine grained order on texual changes that can be called patch dependencies. This enables automatic merges so long as there is no patch conflict.

## Syntax Aware Version Control Systems

Syntax aware Version Control Systems are those systems that understand the structure of the documents being stored under them, and are thus able to make intelligent decisions regarding conflicts and merges. While this seems to be the natural progression for Version Control Systems, so far, I was able to identify only Smalltalk oriented Version Control Systems like Monticello and Envy which follow this route.

### Monticello

Monticello[7] is a version control system that is focused on Smalltalk language, and understands the elements in the Smalltalk such as Classes, Methods, Class comments, Instance variables, Class variables, Class instance variables, and Pool Imports. That is, the meta model that is kept by the version control system is same as the meta model of the language. It keeps a version history of each of these elements, along with its properties. For example, it keeps the name of the super class as a property of the class element. Each of the elements have different properties that are tracked along with the source code. A version in this context is just a variant of the properties for a particular element[4]. Another interesting feature is the concept of slices which aggregates groups of elements and makes tracking of such groups easier. Snapshots capture the state of a slice. These are advantageous in multiple aspects. For example, Monticello is able to keep track of renaming and moving around of variables, imports etc. , And is able to provide a better picture of change history. The second advantage is that, merges become much more intelligent, and conflict free.


## References

[1] L. Allen, G. Fernandez, K. Kane, D. Leblang, D. Minard, and J. Posner. Clearcase multisite: Supporting geographically-distributed software development. Software Configuration Management, pages 194–214, 1995.

[2] U. Asklund and B. Magnusson. A case-study of configuration management with clearcase in an industrial environment. Software Configuration Manage- ment, pages 201–221, 1997.

[3] A. Bieniusa, P. Thiemann, and S. Wehr. The relation of version control to concurrent programming. In Computer Science and Software Engineering, 2008 International Conference on, volume 3, pages 461–464. IEEE, 2008.

[4] Andrew Black, Ste ́phane Ducasse, Oscar Nierstrasz, Damien Pollet, Damien Cassou, and Marcus Denker. Pharo by Example. Square Bracket Associates, 2009.

[5] P. Bo ̈rjesson and A. Karlsson. Focal project a conflict free version control system. Unpublished, 2008.

[6] H.B Brown. The clear/caster system. In The clear/caster system., 1970.

[7] Avi Bryant, Damien Cassou, Julian Fitzell, and Colin Putney. Monticello.

[8] Henrik B. Christensen. Configuration Management. Flexible, Reliable Soft- ware: Using Patterns and Agile Development. Boca Raton, FL: Chapman & Hall/CRC, 2010.

[9] A. Cicchetti, D. Di Ruscio, and A. Pierantonio. A metamodel independent approach to difference representation. Technology, 6(9):165–185, 2007.

[10] Darcs exponential merge.

[11] M. Erwig. A language for software variation research. In Proceedings of the ninth international conference on Generative programming and component engineering, pages 3–12. ACM, 2010.

[12] Dick Grune. Concurrent versions system, a method for independent coopera- tion. Technical report, IR 113, Vrije Universiteit, 1986.

[13] V. Henson and J. Garzik. Bitkeeper for kernel developers. In Ottawa Linux Symposium, pages 197–212. Citeseer, 2002.

[14] V. Henson and J. Garzik. Bitkeeper for kernel developers. In Ottawa Linux Symposium, pages 197–212. Citeseer, 2002.

[15] Liyang Hu and Graham Hutton. Towards a Verified Implementation of Soft- ware Transactional Memory. In Peter Achten, Pieter Koopman, and Marco Morazan, editors, Trends in Functional Programming volume 9. Intellect, july 2009. Selected papers from the Ninth Symposium on Trends in Functional Programming, Nijmegen, The Netherlands, May 2008.

[16] V. Innocente, C. Onions, and T. P. shah. Code management systems. ECFA Large Hadron Collider (LHC) Workshop: Physics and Instrumentation, Aachen, Germany, 1990.

[17] J. Jacobson. A formalization of darcs patch theory using inverse semigroups. Technical report, Technical Report CAM report 09-83, UCLA, 2009.

[18] Simon Peyton Jones. GHC Repository.

[19] A. Lo ̈h, W. Swierstra, and D. Leijen. A principled approach to version control.
Relation, 10(1.39):8342, 2008.

[20] I. Lynagh. Camp patch theory. Available from http://projects.haskell.org/camp/files/theory.pdf, 2009.

[21] B. Milewski. Distributed source control system. Software Configuration Management, pages 98–107, 1997.

[22] B. OSullivan. Distributed revision control with mercurial. Mercurial project, 2007.

[23] J. Pelrine, A. Knight, and A. Cho. Mastering ENVY/Developer, volume 22. Cambridge Univ Pr, 2001.

[24] C. Michael Pilato, Ben Collins-Sussman, and Brian W. Fitzpatrick. Version Control With Subversion. O’Reilly & Associates, Inc., Sebastopol, CA, USA, 2 edition, 2008.

[25] Marc J. Rochkind. The source code control system. IEEE Trans. Software Eng., 1(4):364–370, 1975.

[26] David Roundy. Darcs: distributed version management in haskell. In Proceed- ings of the 2005 ACM SIGPLAN workshop on Haskell, Haskell ’05, pages 1–4, New York, NY, USA, 2005. ACM.

[27] N.B. Ruparelia. The history of version control. ACM SIGSOFT Software Engineering Notes, 35(1):5–9, 2010.

[28] T. Swicegood. Pragmatic version control using Git. Pragmatic Bookshelf, 2008.

[29] Walter F. Tichy and Walter F. Tichy. Rcs: a system for version control. SoftwarePractice & Experience, 1985.

[30] Linus Torvalds. Linux Kernel Repository.

[31] Vero ́nica Uquillas-Gomez, Ste ́phane Ducasse, and Theo D’Hondt. Meta- models and Infrastructure for Smalltalk Omnipresent History. In Smalltalks’2010, Buenos Ares, Argentine, November 2010.

[32] T. Users’Guide. Sunpro manual set. Sun Micro Systems, Mountain View, 1994.

[33] Alexander Yip, Benjie Chen, and Robert Morris. Pastwatch: A Distributed Version Control System. In Pastwatch: A Distributed Version Control System, pages 381–394, 2006.
